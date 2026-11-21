"""Aux rails from VBAT (15-21 V). Every converter runs at <= 1/3 of its rated current (3:1 rule).

Bus protection (P-24 / X-3 TVS coordination, P-39 UVLO, C-17 isolation, design-rules 2.7 PG):
  The VBAT TVS (SMBJ24A) clamps at up to 38.9 V, above the TPS62933 VIN abs max of 32 V (DS 8.1). All 32 V-class bucks
  therefore sit behind one of two TPS26631 eFuses used as OV cut-off / UVLO / current-limit switches:
    VBAT -> JP -> TPS26631 (AUXA) -> VPROT_A : V3V3, V3V3_ETH, V5_PD, V5_AUX, V5_ETH       (<= 1.80 A at 12.5 V in)
    VBAT -> JP -> TPS26631 (AUXB) -> VPROT_B : V5_QI, V12_RTR, V0V95_SW                    (<= 1.93 A at 12.5 V in)
  Divider 178k / 7.5k / 10k: OV = 1.2 x 195.5/10 = 23.5 V (22.8-24.2 V over the 1.176-1.224 V threshold and 1 % parts),
  above BATOVP max 21.8 V (BQ25756 DS: 105.5 % x 20.66 V); UV = 1.2 x 195.5/17.5 = 13.4 V rising, 12.5 V falling
  (pack UV 5 x 2.9 V = 14.5 V), which is the bucks' input UVLO (P-39). OVP turn-off 8.5-14 us (TPS2663 DS 6.6).
  I_LIM 7.5k = 2.4 A (18/R). Load per eFuse <= 1.93 A -> 6 A rated / 1.93 = 3.1:1. ~SHDN open = always enabled
  (V3V3 must come up without firmware). MODE = GND auto-retry.

TPS62933P (3 A, FB 0.8 V, 500 kHz with RT floating; datasheet Table 10-2 LC values):
  V3V3      main logic, always on          load <= 1.0 A  (ESP32 0.5 A peak, PD ctrls, mux, RTC, NFC, LoRa)
  V3V3_ETH  NICs/switch/PHY 3.3 V, gated    load <= 1.0 A
  V5_PD     VCONN for 4 ports               load <= 0.8 A  (P-38: VCONN must be capped at 200 mA/port in the PD config)
  V5_AUX    amp, fan, glow, level shift     load <= 1.0 A RMS
  V5_ETH    0.95 V NIC/PHY bucks, gated     load <= 0.7 A
  V12_RTR   router module 12 V, gated       load <= 0.92 A
TPS56A37 (10 A, FB 0.6 V - datasheet not in docs/, VERIFY):
  V5_QI     Qi transmitter 5 V, gated       load <= 1.45 A (IP6826 5 W BPP at 5 V in, >= 70 % eff.) -> 6.9:1
            (was V12_QI on a TPS62933: at 12 V the IP6826 negotiates up to 15 W - P-29/X-25. "5 V input for 5 W output",
             IP6826 DS features; 1.45 A on a 3 A TPS62933 would be 2.1:1, so a 10 A part is used.)
  V0V95_SW  switch+PHY core, gated          load <= 2.5 A
TPS22965 load switches (6 A): V3V3_LORA (<0.2 A), V5_GLOW (<0.4 A)
"""
from blocks.power_input import efuse

RAILS = [
    # name, rtop, l_sym, l_rated, l_isat, load, en_net, cout_key, feed, note
    ("V3V3", "31.6k", "MAPM0630F-4R7M-LF", 5.0, 10.0, 1.0, None, "C_22u_10V", "VPROT_A", "3.33 V"),
    ("V3V3_ETH", "31.6k", "MAPM0630F-4R7M-LF", 5.0, 10.0, 1.0, "EXP_EN_ETH", "C_22u_10V", "VPROT_A", "3.33 V, gated"),
    ("V5_PD", "52.3k", "MSA75-6R8M", 5.0, 5.0, 0.8, None, "C_22u_10V", "VPROT_A", "4.98 V VCONN"),
    ("V5_AUX", "52.3k", "MSA75-6R8M", 5.0, 5.0, 1.0, None, "C_22u_10V", "VPROT_A", "4.98 V"),
    ("V5_ETH", "52.3k", "MSA75-6R8M", 5.0, 5.0, 0.7, "EXP_EN_ETH", "C_22u_10V", "VPROT_A", "4.98 V, gated; feeds the 1.2 MHz FCCM 0.95 V NIC/PHY bucks (H-10)"),
    ("V12_RTR", "140k", "FNR8040S120MT", 3.0, 4.0, 0.92, "EXP_EN_RTR", "C_22u_25V", "VPROT_B", "12.0 V, gated"),
]

# eFuse groups: tag, output, worst-case input current at the 12.5 V UV-falling point (85 % converter efficiency)
#   A: (3.33 + 3.33 + 4.0 + 5.0 + 3.5) W / 0.85 / 12.5 V = 1.80 A
#   B: (7.1 [5 W Qi / 0.70] + 11.0 + 2.4) W / 0.85 / 12.5 V = 1.93 A
GROUPS = [("AUXA", "VPROT_A", 1.80), ("AUXB", "VPROT_B", 1.93)]


def _feed(D, sh, feed, t, i_op):
    """design-rules 2.2: each converter fed through its own solder jumper; returns the converter VIN net."""
    vin = D.v(f"{t}_VIN", 21.0)
    D.JP(sh, feed, vin, i_op=i_op, note=f"{t} isolate")
    D.C(sh, "C_10u_50V", vin, "GND")
    D.C(sh, "C_100n_50V", vin, "GND")
    return vin


def _rail_led(D, sh, name, t):
    D.JP(sh, name, f"{t}_LEDJ", note="LED cut")
    D.R(sh, "10k" if "12" in name else "2.2k", f"{t}_LEDJ", f"{t}_LEDA", pkg="0402")
    D.IC(sh, "KT-0603R", {"A": f"{t}_LEDA", "K": "GND"}, prefix="D", value=f"{name} LED")


def build(D):
    sh = D.sheet("aux_power", "Aux rails: 3.3 V / 5 V / 12 V / 0.95 V (each converter <= 1/3 of rating)")
    sh.note("TPS62933P values from datasheet Table 10-2 (500 kHz): 3.3 V 31.3k/10k 4.7 uH; 5 V 52.5k/10k 6.8 uH; 12 V 140k/10k 12 uH.")
    sh.note("All 32 V-class bucks are behind TPS26631 OV cut-off (23.5 V) / UV (13.4 V) eFuses: VPROT_A / VPROT_B (P-24, P-39).")
    sh.note("V12_QI replaced by V5_QI (TPS56A37, 5.0 V): the IP6826 is hardware-limited to 5 W BPP at a 5 V input (P-29, X-25).")
    for tag, out, iop in GROUPS:
        D.v(out, 21.0)
        efuse(D, sh, "VBAT", out, tag, ilim_r="7.5k", ov_div=("178k", "7.5k", "10k"), shdn="open", vin_max=21.0,
              vout_max=21.0, pgth=("100k", "10k"), blocking=False, i_op=iop,
              note="Aux sub-bus OV cut-off / UVLO (protects the 32 V bucks from the 38.9 V TVS clamp).")
        D.C(sh, "C_10u_50V", out, "GND")
        D.TP(sh, out)

    for name, rtop, lsym, lr, ls, load, en, cout, feed, note in RAILS:
        t = name
        sw, bst, fb, pg = f"{t}_SW", f"{t}_BST", f"{t}_FB", f"{t}_PG"
        D.v(sw, 21.0)
        vin = _feed(D, sh, feed, t, load)
        conns = {"RT": f"{t}_RT", "EN": en or f"{t}_ENP", "VIN": vin, "GND": "GND", "SW": sw, "BST": bst, "PG": pg, "FB": fb}
        u = D.IC(sh, "TPS62933PDRLR", conns, fields={"Op_I": load, "Rated_I": 3.0, "Note": f"{note}; load {load} A"})
        u.nc = set()
        # RT floating = 500 kHz: give the pin an explicit no-connect
        u.conns.pop("RT")
        u.nc.add("RT")
        if en is None:
            u.conns.pop("EN")   # C-2: EN abs-max 6 V; floating enables via the internal pull-up current (datasheet)
            u.nc.add("EN")
        else:
            D.R(sh, "100k", en, "GND", fields={"Note": "default off until the expander enables it"})
        D.C(sh, "C_100n_16V", bst, sw, fields={"V_across": 5.5})
        D.L(sh, lsym, sw, name, rated_i=lr, isat=ls, irms=load, ipk=load + 0.6)
        D.R(sh, rtop, name, fb)
        D.R(sh, "10k", fb, "GND")
        D.C(sh, cout, name, "GND")
        D.C(sh, cout, name, "GND")
        D.C(sh, "C_100n_16V" if "12" not in name else "C_100n_50V", name, "GND")
        D.R(sh, "10k", pg, "V3V3")
        D.TP(sh, name)
        D.TP(sh, pg, small=True)
        _rail_led(D, sh, name, t)

    # Qi 5 V: TPS56A37 10 A (V12_QI -> V5_QI, P-29 / X-25)
    D.v("V5_QI", 5.5)
    D.v("V5_QI_SW", 21.0)
    vin = _feed(D, sh, "VPROT_B", "V5_QI", 1.45)
    D.C(sh, "C_10u_50V", vin, "GND")
    D.IC(sh, "TPS56A37RPAR", {"EN": "EXP_EN_QI", "FB": "V5QI_FB", "AGND": "GND", "PG": "V5_QI_PG", "SS": "V5QI_SS",
                              "SW": "V5_QI_SW", "BOOT": "V5QI_BST", "VIN": vin, "PGND": "GND", "MODE": "V5QI_MODE"},
         fields={"Op_I": 1.45, "Rated_I": 10.0,
                 "Note": "Qi 5 V: IP6826 5 W at 5 V in -> <= 1.45 A. FB 0.6 V, MODE and EN levels VERIFY (TPS56A37 datasheet not in docs/)."})
    D.R(sh, "100k", "EXP_EN_QI", "GND", fields={"Note": "default off until the expander enables it"})
    D.R(sh, "49.9k", "V5_QI", "V5QI_FB", fields={"Note": "0.6 x (1 + 49.9/6.8) = 5.00 V (IP6826 VIN 4.5-12 V; DPM below 4.3 V)"})
    D.R(sh, "6.8k", "V5QI_FB", "GND")
    D.C(sh, "C_22n_50V", "V5QI_SS", "GND")
    D.R(sh, "52.3k", "V5QI_MODE", "GND", fields={"Note": "MODE strap 52.3k to AGND per X-23 (same mode as V0V95_SW). VERIFY TI MODE table"})
    D.C(sh, "C_100n_16V", "V5QI_BST", "V5_QI_SW", fields={"V_across": 5.5})
    D.L(sh, "MSA75-6R8M", "V5_QI_SW", "V5_QI", rated_i=5.0, isat=5.0, irms=1.45, ipk=2.0,
        value="6.8uH 5A")  # ripple 16 V x 0.24 / (6.8 uH x 500 kHz) = 1.1 A p-p -> 2.0 A peak (VERIFY f_sw)
    for _ in range(2):
        D.C(sh, "C_22u_10V", "V5_QI", "GND")
    D.C(sh, "C_100n_16V", "V5_QI", "GND")
    D.R(sh, "10k", "V5_QI_PG", "V3V3")
    D.TP(sh, "V5_QI")
    D.TP(sh, "V5_QI_PG", small=True)
    _rail_led(D, sh, "V5_QI", "V5_QI")

    # switch + PHY core: TPS56A37 10 A
    D.v("V0V95_SW_SW", 21.0)
    vin = _feed(D, sh, "VPROT_B", "V0V95_SW", 0.25)
    D.C(sh, "C_10u_50V", vin, "GND")
    D.IC(sh, "TPS56A37RPAR", {"EN": "EXP_EN_ETH", "FB": "V09SW_FB", "AGND": "GND", "PG": "V0V95_SW_PG", "SS": "V09SW_SS",
                              "SW": "V0V95_SW_SW", "BOOT": "V09SW_BST", "VIN": vin, "PGND": "GND", "MODE": "V09SW_MODE"},
         fields={"Op_I": 2.5, "Rated_I": 10.0, "Note": "RTL8372N core only (PHY now separate). FB 0.6 V VERIFY (TPS56A37 datasheet not yet downloaded)."})
    D.R(sh, "4.7k", "V0V95_SW", "V09SW_FBT", fields={"Note": "X-23: 4.7k + 1.2k = 5.9k top"})
    D.R(sh, "1.2k", "V09SW_FBT", "V09SW_FB")
    D.R(sh, "10k", "V09SW_FB", "GND", fields={"Note": "0.6 x (1 + 5.9/10) = 0.954 V; high corner 0.609 V x 1.602 = 0.976 V <= 0.98 V. "
                                                     "X-23 asks for 0.1 % parts (no passives key yet)"})
    D.C(sh, "C_22n_50V", "V09SW_SS", "GND")
    D.R(sh, "52.3k", "V09SW_MODE", "GND", fields={"Note": "X-23: MODE 52.3k to AGND (was 0 ohm). VERIFY against the TI MODE table"})
    D.C(sh, "C_100n_16V", "V09SW_BST", "V0V95_SW_SW", fields={"V_across": 5.5})
    D.L(sh, "IHLP4040DZER2R2M01", "V0V95_SW_SW", "V0V95_SW", rated_i=12.0, isat=25.6, irms=2.9, ipk=3.8, value="2.2uH 12A")
    for _ in range(4):
        D.C(sh, "C_22u_6V3", "V0V95_SW", "GND")
    D.R(sh, "10k", "V0V95_SW_PG", "V3V3")
    D.TP(sh, "V0V95_SW")
    D.TP(sh, "V0V95_SW_PG", small=True)

    # load switches
    for out, vin, en, load in [("V3V3_LORA", "V3V3", "EXP_EN_LORA", 0.2), ("V5_GLOW", "V5_AUX", "EXP_EN_GLOW", 0.4)]:
        D.IC(sh, "TPS22965DSGR", {"VIN": vin, "ON": en, "VBIAS": "V5_AUX", "GND": "GND", "CT": f"{out}_CT", "VOUT": out, "EP": "GND"},
             fields={"Op_I": load, "Rated_I": 6.0})
        D.C(sh, "C_1n_50V", f"{out}_CT", "GND")
        D.C(sh, "C_1u_16V", vin, "GND")
        D.C(sh, "C_1u_16V", out, "GND")
        D.R(sh, "100k", en, "GND")
        D.TP(sh, out)
    return sh
