"""Review round 1 - H-10: clean 0.95 V supplies for the Realtek parts.
RTL8221B DS 9.2: AVDD09 <= 15 mVpp, switcher in PWM/CCM above 1 MHz. Impossible from 21 V (t_on_min 70 ns), so:
  VBAT -> V5_ETH (TPS62933P, gated by EXP_EN_ETH) -> per-NIC and PHY TPS62933F (FCCM) at 1.2 MHz (RT = GND).
  5 V -> 0.95 V at 1.2 MHz: t_on = 0.19 / 1.2 MHz = 158 ns > 70 ns.
Switch core stays on TPS56A37 (10 A) with the ferrite + bulk post-filter on its analog group (MODE strap VERIFY FCCM)."""
import os

GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "gen")


def sub(rel, old, new):
    path = os.path.join(GEN, rel)
    t = open(path, encoding="utf-8").read()
    assert old in t, (rel, old[:90])
    open(path, "w", encoding="utf-8").write(t.replace(old, new, 1))


U = "blocks/usbc_port.py"
sub(U, '''    D.IC(sh, "TPS62933PDRLR", {"RT": n("BRT"), "EN": n("EXTSWR"), "VIN": "VBAT", "GND": G, "SW": n("BSW"),
                                "BST": n("BBST"), "PG": n("V09PG"), "FB": n("BFB")},
         fields={"Op_I": 0.65, "Rated_I": 3.0, "Note": "0.65 A max NIC core (datasheet) vs 3 A -> 4.6:1"})
    D.v(n("BSW"), 21.0)
    D.R(sh, "71.5k", n("BRT"), G, fields={"Note": "310 kHz (datasheet table)"})''',
    '''    D.IC(sh, "TPS62933FDRLR", {"RT": G, "EN": n("EXTSWR"), "VIN": "V5_ETH", "GND": G, "SW": n("BSW"),
                                "BST": n("BBST"), "SS": n("BSS"), "FB": n("BFB")},
         fields={"Op_I": 0.65, "Rated_I": 3.0,
                 "Note": "H-10: FCCM variant at 1.2 MHz (RT=GND) from V5_ETH; 0.65 A NIC core vs 3 A -> 4.6:1"})
    D.v(n("BSW"), 5.5)
    D.C(sh, "C_33n_50V", n("BSS"), G, fields={"Note": "soft start ~5 ms"})''')
sub(U, '''    D.L(sh, "MAPM0630F-4R7M-LF", n("BSW"), V09, rated_i=5.0, isat=10.0, irms=0.65, ipk=1.0, value="4.7uH 5A")''',
    '''    D.L(sh, "FNR6045S2R2MT", n("BSW"), V09, rated_i=5.0, isat=7.4, irms=0.65, ipk=0.8, value="2.2uH 5A")''')
sub(U, '''    D.C(sh, "C_10u_50V", "VBAT", G)
    D.C(sh, "C_100n_50V", "VBAT", G)
    D.C(sh, "C_22u_6V3", V09, G)
    D.R(sh, "10k", n("V09PG"), "V3V3_ETH")
    D.TP(sh, V09)
    D.TP(sh, n("V09PG"), small=True)''',
    '''    D.C(sh, "C_10u_16V", "V5_ETH", G)
    D.C(sh, "C_100n_16V", "V5_ETH", G)
    D.C(sh, "C_22u_6V3", V09, G)
    D.TP(sh, V09)''')

A = "blocks/aux_power.py"
sub(A, '''    ("V5_AUX", "52.3k", "MSA75-6R8M", 5.0, 5.0, 1.0, None, "C_22u_10V", "4.98 V"),''',
    '''    ("V5_AUX", "52.3k", "MSA75-6R8M", 5.0, 5.0, 1.0, None, "C_22u_10V", "4.98 V"),
    ("V5_ETH", "52.3k", "MSA75-6R8M", 5.0, 5.0, 0.7, "EXP_EN_ETH", "C_22u_10V", "4.98 V, gated; feeds the 1.2 MHz FCCM 0.95 V NIC/PHY bucks (H-10)"),''')
sub(A, '''    # load switches''', '''    # RTL8221B core: TPS62933F FCCM 1.2 MHz from V5_ETH (H-10: <=15 mVpp, PWM > 1 MHz)
    D.v("V0V95_PHY_SW", 5.5)
    D.IC(sh, "TPS62933FDRLR", {"RT": "GND", "EN": "EXP_EN_ETH", "VIN": "V5_ETH", "GND": "GND", "SW": "V0V95_PHY_SW",
                               "BST": "V09PHY_BST", "SS": "V09PHY_SS", "FB": "V09PHY_FB"},
         fields={"Op_I": 0.5, "Rated_I": 3.0, "Note": "RTL8221B 0.95 V (DVDD09/AVDD09/EVDD09)"})
    D.C(sh, "C_33n_50V", "V09PHY_SS", "GND")
    D.C(sh, "C_100n_16V", "V09PHY_BST", "V0V95_PHY_SW", fields={"V_across": 5.5})
    D.L(sh, "FNR6045S2R2MT", "V0V95_PHY_SW", "V0V95_PHY", rated_i=5.0, isat=7.4, irms=0.5, ipk=0.7, value="2.2uH 5A")
    D.R(sh, "1.87k", "V0V95_PHY", "V09PHY_FB", fields={"Note": "0.950 V"})
    D.R(sh, "10k", "V09PHY_FB", "GND")
    D.C(sh, "C_10u_16V", "V5_ETH", "GND")
    D.C(sh, "C_22u_6V3", "V0V95_PHY", "GND")
    D.C(sh, "C_22u_6V3", "V0V95_PHY", "GND")
    D.TP(sh, "V0V95_PHY")

    # load switches''')
sub(A, '''         fields={"Op_I": 2.9, "Rated_I": 10.0, "Note": "FB 0.6 V assumed (VERIFY datasheet). MODE resistor selects freq/FCCM (VERIFY)."})''',
    '''         fields={"Op_I": 2.5, "Rated_I": 10.0, "Note": "RTL8372N core only (PHY now separate). FB 0.6 V and MODE->FCCM strap VERIFY (TPS56A37 datasheet not yet downloaded)."})''')

E = "blocks/ethernet.py"
sub(E, '''"PHYRSTB": "EXP_PHY_RST_N", "MDC": "ETH_MDC", "MDIO": "ETH_MDIO", "DVDD09": V09, "DVDD3318": V33,''',
    '''"PHYRSTB": "EXP_PHY_RST_N", "MDC": "ETH_MDC", "MDIO": "ETH_MDIO", "DVDD09": "V0V95_PHY", "DVDD3318": V33,''')
sub(E, '''"CKXTAL1": "ETH_PHY_XI", "AVDD09": "V0V95_SWA",''', '''"CKXTAL1": "ETH_PHY_XI", "AVDD09": "V0V95_PHY",''')
sub(E, '''"EVDD09": "V0V95_SWA", "HSON":''', '''"EVDD09": "V0V95_PHY", "HSON":''')
sub(E, '''    for _ in range(6):
        D.C(sh, "C_100n_16V", "V0V95_SWA", G)
    for _ in range(5):
        D.C(sh, "C_100n_16V", "V3V3_ETHA", G)''', '''    for _ in range(7):
        D.C(sh, "C_100n_16V", "V0V95_PHY", G)
    for _ in range(5):
        D.C(sh, "C_100n_16V", "V3V3_ETHA", G)''')

B = "build.py"
sub(B, '"V5_AUX": 5.5, "V5_GLOW": 5.5,', '"V5_AUX": 5.5, "V5_GLOW": 5.5, "V5_ETH": 5.5, "V0V95_PHY": 1.0, "V5_FAN": 5.5,')
print("H-10 core-supply patch applied")
