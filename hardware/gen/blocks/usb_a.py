"""USB-A fast-charge output: Injoinic IP6525S_EN single-chip buck (5.2-32 V in; BC1.2/QC2/QC3/FCP/SCP/AFC/...).
Limited to 1.5 A by policy (2 A connector -> documented exception; 3:1 on the 22.5 W IC -> 7.5 W).
VOOC is not offered (needs 4-6.5 A receptacles). Pin 4 is HLED/PS/EN multi-function: VERIFY strap/enable behaviour.
"""


def build(D):
    sh = D.sheet("usb_a", "USB-A output (QC/FCP/SCP/AFC), 1.5 A max")
    G = "GND"
    D.IC(sh, "IP6525S_EN", {"GND": G, "SW": "USBA_SW", "BST": "USBA_BST", "HLED/PS/EN": "EXP_EN_USBA", "DM": "USBA_DM",
                            "DP": "USBA_DP", "VIN": "VBAT", "VOUT": "USBA_VBUS", "PGND": G},
         fields={"Op_P": 7.5, "Rated_P": 22.5, "Note": "Firmware/IC limit 1.5 A. EN via expander (default off by pull-down)."})
    D.v("USBA_SW", 21.0)
    D.C(sh, "C_100n_16V", "USBA_BST", "USBA_SW", fields={"V_across": 5.5})
    D.IC(sh, "MSA75-6R8M", {"1": "USBA_SW", "2": "USBA_VBUS"}, prefix="L", value="6.8uH 5A",
         fields={"Rated_I": 5.0, "Isat": 5.0, "Op_Irms": 1.5, "Op_Ipk": 2.0, "Note": "inductor value per IP6525S app note VERIFY"})
    D.C(sh, "C_10u_50V", "VBAT", G)
    D.C(sh, "C_10u_50V", "VBAT", G)
    D.C(sh, "C_100n_50V", "VBAT", G)
    for _ in range(3):
        D.C(sh, "C_10u_50V", "USBA_VBUS", G)
    D.IC(sh, "TPD4E05U06DQAR_C138714", {"D1+": "USBA_DP", "D1-": "USBA_DM", "GND": G}, nc=["NC", "D2+", "D2-"], prefix="U")
    D.IC(sh, "HC-A-002-4P-DIP10-2A-27", {"1": "USBA_VBUS", "2": "USBA_DM", "3": "USBA_DP", "4": G, "5": G, "6": G}, prefix="J",
         value="USB-A", fields={"Op_I": 1.5, "Rated_I": 2.0, "Derating_Exception": "USB-A 2 A connector, docs/design-rules.md 1.4",
                               "Note": "pin map 1 VBUS 2 D- 3 D+ 4 GND 5/6 shell - VERIFY against footprint"})
    D.TP(sh, "USBA_VBUS")
    return sh
