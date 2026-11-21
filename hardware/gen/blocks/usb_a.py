"""USB-A output, 5 V / 1.5 A (7.5 W) hardware-limited: Injoinic IP6525S_EN buck (5.2-32 V in) + TPS26631 eFuse.

P-28 / X-24: the IP6525S has no current or protocol programming (DS: 5 V/3.4 A, 9 V/2 A, 12 V/1.5 A, SCP 5 V/4.5 A,
4.5 V/5 A, all negotiated autonomously over DP/DM). Hardware enforcement of the 1.5 A / 7.5 W policy (design-rules 1.2:
3:1 on the 22.5 W IC -> 7.5 W; 1.4: 2 A receptacle -> 1.5 A):
  1. No fast-charge handshake: the receptacle D+/D- are shorted together (BC1.2 DCP, <= 1.5 A class) and the
     IP6525S DP/DM pins are NOT connected to the receptacle (tied to each other only), so no QC/FCP/SCP/AFC request can
     reach the IC and it stays at its 5 V default. VERIFY on the bench that the IP6525S idles at 5 V with DP/DM tied.
  2. TPS26631 eFuse between the IC and the receptacle: I_LIM 13k = 1.38 A nominal, 1.50 A max (+8 %, TPS2663 DS),
     OV cut-off 6.35 V (6.2-6.5 V) as a backstop if the IC ever leaves 5 V; UV 4.56 V (>= 4.5 V IN_SYS minimum).
  Inductor 22 uH / 6 A: 1.5 A -> 4:1; ripple at 21 V in 1.73 A p-p -> 2.4 A peak vs 12 A Isat.
Pin 4 is HLED/PS/EN: only a pull-LOW disables the DC-DC (DS 9.4) -> open-drain AO3400A, gate pulled up = default off (C-14).
"""
from blocks.power_input import efuse, polymer


def build(D):
    sh = D.sheet("usb_a", "USB-A output 5 V / 1.5 A (hardware-limited)")
    sh.note("P-28/X-24: receptacle D+/D- shorted (DCP); IP6525S DP/DM not routed out -> 5 V only. TPS26631 limits to 1.38 A nom / 1.5 A max.")
    G = "GND"
    D.JP(sh, "VBAT", "USBA_VIN", i_op=0.6, note="USB-A isolate")
    D.v("USBA_VIN", 21.0)
    D.IC(sh, "IP6525S_EN", {"GND": G, "SW": "USBA_SW", "BST": "USBA_BST", "HLED/PS/EN": "USBA_EN_OD", "DM": "USBA_IC_D",
                            "DP": "USBA_IC_D", "VIN": "USBA_VIN", "VOUT": "USBA_VOUT", "PGND": G},
         fields={"Op_P": 7.5, "Rated_P": 22.5,
                 "Note": "5 V only (no handshake path), 1.5 A max by the downstream eFuse -> 7.5 W = 3:1. EN via EXP_USBA_DIS (default off)."})
    D.TP(sh, "USBA_IC_D", small=True)
    D.v("USBA_SW", 21.0)
    D.C(sh, "C_100n_16V", "USBA_BST", "USBA_SW", fields={"V_across": 5.5})
    D.IC(sh, "SLO1365H220MTT", {"1": "USBA_SW", "2": "USBA_VOUT"}, prefix="L", value="22uH 6A",
         fields={"Rated_I": 6.0, "Isat": 12.0, "Op_Irms": 1.5, "Op_Ipk": 2.4,
                 "Note": "C-3: 22 uH per IP6525S reference (100 kHz); 1.73 A p-p at 21 V in; load capped at 1.5 A by the eFuse"})
    D.R(sh, "2.2", "USBA_SW", "USBA_SNB", pkg="0603", p_op=0.03, fields={"Note": "C-13: SW snubber ~2 ohm + 1 nF (reference design)"})
    D.C(sh, "C_1n_50V", "USBA_SNB", G)
    D.v("USBA_SNB", 21.0)
    D.IC(sh, "JBLM2101M025C058RTM100UF25V", {"1": "USBA_VOUT", "2": G}, prefix="C", value="100uF 25V polymer",
         fields={"Rated_V": 25, "Note": "C-13: solid output cap (~50 mOhm) per reference; pin 1 = + VERIFY"})
    D.IC(sh, "AO3400A", {"D": "USBA_EN_OD", "G": "EXP_USBA_DIS", "S": G}, prefix="Q",
         fields={"Note": "C-14: open-drain disable (pin 4 acts only when pulled low). Gate pulled up by default -> USB-A off"})
    D.v("USBA_EN_OD", 5.5)
    D.C(sh, "C_10u_50V", "USBA_VIN", G)
    D.C(sh, "C_10u_50V", "USBA_VIN", G)
    D.C(sh, "C_100n_50V", "USBA_VIN", G)
    polymer(D, sh, "USBA_VIN", 21.0, note="C-13: input bulk (reference: 100 uF / 35 V electrolytic or solid)")
    for _ in range(3):
        D.C(sh, "C_10u_50V", "USBA_VOUT", G)
    # hardware current / voltage limiter (P-28, X-24)
    efuse(D, sh, "USBA_VOUT", "USBA_VBUS", "USBAF", ilim_r="13k", ov_div=("39k", "3.92k", "10k"), shdn="open",
          vin_max=12.6, vout_max=12.6, pgth=("27k", "10k"), blocking=False, jp=False, i_op=1.5, imon=False,
          note="USB-A limiter: 1.38 A nom / 1.50 A max, OV 6.35 V backstop, PGOOD at 4.4 V.")
    D.TP(sh, "USBA_VOUT")
    D.C(sh, "C_10u_50V", "USBA_VBUS", G)
    D.IC(sh, "TPD4E05U06DQAR_C138714", {"D1+": "USBA_DCP", "D1-": "USBA_DCP", "GND": G}, nc=["NC", "D2+", "D2-"], prefix="U",
         fields={"Note": "ESD on the shorted D+/D- (DCP) pair"})
    D.v("USBA_DCP", 3.6)
    D.IC(sh, "HC-A-002-4P-DIP10-2A-27", {"1": "USBA_VBUS", "2": "USBA_DCP", "3": "USBA_DCP", "4": G, "5": G, "6": G}, prefix="J",
         value="USB-A", fields={"Op_I": 1.5, "Rated_I": 2.0, "Derating_Exception": "USB-A 2 A connector, docs/design-rules.md 1.4",
                               "Note": "D+ shorted to D- (BC1.2 DCP). pin map 1 VBUS 2 D- 3 D+ 4 GND 5/6 shell - VERIFY against footprint"})
    D.TP(sh, "USBA_VBUS")
    return sh
