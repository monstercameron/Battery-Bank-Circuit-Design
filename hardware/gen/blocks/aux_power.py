"""Aux rails from VBAT (15-21 V). Every converter runs at <= 1/3 of its rated current (3:1 rule).

TPS62933P (3 A, FB 0.8 V, 500 kHz with RT floating; datasheet Table 10-2 LC values):
  V3V3      main logic, always on          load <= 1.0 A  (ESP32 0.5 A peak, PD ctrls, mux, RTC, NFC, LoRa)
  V3V3_ETH  NICs/switch/PHY 3.3 V, gated    load <= 1.0 A
  V5_PD     VCONN for 4 ports               load <= 0.8 A
  V5_AUX    amp, fan, glow, level shift     load <= 1.0 A RMS
  V12_QI    Qi transmitter, gated           load <= 0.6 A
  V12_RTR   router module 12 V, gated       load <= 0.92 A
TPS56A37 (10 A, FB 0.6 V): V0V95_SW switch+PHY core, gated, load <= 2.9 A
TPS22965 load switches (6 A): V3V3_LORA (<0.2 A), V5_GLOW (<0.4 A)
"""

RAILS = [
    # name, rtop, l_sym, l_rated, l_isat, load, en_net, cout_key, note
    ("V3V3", "31.6k", "MAPM0630F-4R7M-LF", 5.0, 10.0, 1.0, None, "C_22u_10V", "3.33 V"),
    ("V3V3_ETH", "31.6k", "MAPM0630F-4R7M-LF", 5.0, 10.0, 1.0, "EXP_EN_ETH", "C_22u_10V", "3.33 V, gated"),
    ("V5_PD", "52.3k", "MSA75-6R8M", 5.0, 5.0, 0.8, None, "C_22u_10V", "4.98 V VCONN"),
    ("V5_AUX", "52.3k", "MSA75-6R8M", 5.0, 5.0, 1.0, None, "C_22u_10V", "4.98 V"),
    ("V12_QI", "140k", "FNR8040S120MT", 3.0, 4.0, 0.6, "EXP_EN_QI", "C_22u_25V", "12.0 V, gated"),
    ("V12_RTR", "140k", "FNR8040S120MT", 3.0, 4.0, 0.92, "EXP_EN_RTR", "C_22u_25V", "12.0 V, gated"),
]


def build(D):
    sh = D.sheet("aux_power", "Aux rails: 3.3 V / 5 V / 12 V / 0.95 V (each converter <= 1/3 of rating)")
    sh.note("TPS62933P values from datasheet Table 10-2 (500 kHz): 3.3 V 31.3k/10k 4.7 uH; 5 V 52.5k/10k 6.8 uH; 12 V 140k/10k 12 uH.")
    for name, rtop, lsym, lr, ls, load, en, cout, note in RAILS:
        t = name
        sw, bst, fb, pg = f"{t}_SW", f"{t}_BST", f"{t}_FB", f"{t}_PG"
        D.v(sw, 21.0)
        conns = {"RT": f"{t}_RT", "EN": en or f"{t}_ENP", "VIN": "VBAT", "GND": "GND", "SW": sw, "BST": bst, "PG": pg, "FB": fb}
        u = D.IC(sh, "TPS62933PDRLR", conns, fields={"Op_I": load, "Rated_I": 3.0, "Note": f"{note}; load {load} A"})
        u.nc = set()
        # RT floating = 500 kHz: give the pin an explicit no-connect
        u.conns.pop("RT")
        u.nc.add("RT")
        if en is None:
            D.R(sh, "100k", f"{t}_ENP", "VBAT", pkg="0603", fields={"Note": "always on (EN pull-up; floating also enables)"})
        else:
            D.R(sh, "100k", en, "GND", fields={"Note": "default off until the expander enables it"})
        D.C(sh, "C_100n_16V", bst, sw, fields={"V_across": 5.5})
        D.L(sh, lsym, sw, name, rated_i=lr, isat=ls, irms=load, ipk=load + 0.6)
        D.R(sh, rtop, name, fb)
        D.R(sh, "10k", fb, "GND")
        D.C(sh, "C_10u_50V", "VBAT", "GND")
        D.C(sh, "C_100n_50V", "VBAT", "GND")
        D.C(sh, cout, name, "GND")
        D.C(sh, cout, name, "GND")
        D.C(sh, "C_100n_16V" if "12" not in name else "C_100n_50V", name, "GND")
        D.R(sh, "10k", pg, "V3V3")
        D.TP(sh, name)
        D.TP(sh, pg, small=True)
        # rail LED behind a cut jumper (debug)
        D.JP(sh, name, f"{t}_LEDJ", note="LED cut")
        D.R(sh, "10k" if "12" in name else "2.2k", f"{t}_LEDJ", f"{t}_LEDA", pkg="0402")
        D.IC(sh, "KT-0603R", {"A": f"{t}_LEDA", "K": "GND"}, prefix="D", value=f"{name} LED")

    # switch + PHY core: TPS56A37 10 A
    D.v("V0V95_SW_SW", 21.0)
    D.IC(sh, "TPS56A37RPAR", {"EN": "EXP_EN_ETH", "FB": "V09SW_FB", "AGND": "GND", "PG": "V0V95_SW_PG", "SS": "V09SW_SS",
                              "SW": "V0V95_SW_SW", "BOOT": "V09SW_BST", "VIN": "VBAT", "PGND": "GND", "MODE": "V09SW_MODE"},
         fields={"Op_I": 2.9, "Rated_I": 10.0, "Note": "FB 0.6 V assumed (VERIFY datasheet). MODE resistor selects freq/FCCM (VERIFY)."})
    D.R(sh, "6.04k", "V0V95_SW", "V09SW_FB", fields={"Note": "0.6 x (1 + 6.04/10) = 0.962 V (in 0.92-0.98 V window)"})
    D.R(sh, "10k", "V09SW_FB", "GND")
    D.C(sh, "C_22n_50V", "V09SW_SS", "GND")
    D.R(sh, "0", "V09SW_MODE", "GND", fields={"Note": "MODE strap placeholder VERIFY"})
    D.C(sh, "C_100n_16V", "V09SW_BST", "V0V95_SW_SW", fields={"V_across": 5.5})
    D.L(sh, "IHLP4040DZER2R2M01", "V0V95_SW_SW", "V0V95_SW", rated_i=12.0, isat=25.6, irms=2.9, ipk=3.8, value="2.2uH 12A")
    for _ in range(2):
        D.C(sh, "C_10u_50V", "VBAT", "GND")
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
