"""Qi wireless pad: Injoinic IP6826 (15 W WPC 1.2.4 TX SoC, integrated full bridge) on V12_QI, limited to 5 W (3:1).
Datasheet notes: VIN 4.5-12 V; VCC 2.2 uF; EPAD (PGND) to the high side of the 20 mOhm shunt; NC pins 25/31 must float;
NTC unused -> 100k to GND; LOSS_THR 50-130k (FOD). Coil A11 (6.3 uH) with series resonant C0G caps.
Crystal frequency and the V_DECODE/VDET demodulation network are NOT in the extracted text: VERIFY with the datasheet PDF.
"""


def build(D):
    sh = D.sheet("qi", "Qi transmitter (5 W limited) under the non-metal top window")
    G = "GND"
    D.IC(sh, "IP6826QFN32", {
        "GND": G, "AGND": G, "IGND": G, "ISENSE": "QI_PGND", "PGND": "QI_PGND", "EP": "QI_PGND", "VCC": "QI_VCC",
        "HOSCI": "QI_XI", "HOSCO": "QI_XO", "NTC": "QI_NTC", "LOSS_THR": "QI_FOD", "LED1": "QI_LED1", "LED2": "QI_LED2",
        "LED3": "QI_LED3", "V_DECODE": "QI_VDEC", "VDET": "QI_VDET", "BST1": "QI_BST1", "LX1": "QI_LX1", "LX2": "QI_LX2",
        "BST2": "QI_BST2", "VIN": "V12_QI"},
        nc=["CC1", "CC2", "DEBUG", "IO4", "IO7", "NC", "DM", "DP"],
        fields={"Op_P": 5.0, "Rated_P": 15.0, "Note": "Needs factory firmware burn (JLCPCB listing). CC/DP/DM unused (fixed 12 V input)."})
    D.IC(sh, "LR1206-21R020F4", {"1": "QI_PGND", "2": G}, prefix="R", value="20m 1W", fields={"Op_P": 0.05, "Rated_P": 1.0})
    D.v("QI_VCC", 5.5)
    for n_ in ("QI_NTC", "QI_FOD", "QI_LED1", "QI_LED2", "QI_LED3", "QI_XI", "QI_XO", "QI_VDET"):
        D.v(n_, 5.5)
    D.C(sh, "C_2u2_16V", "QI_VCC", G)
    for _ in range(2):
        D.C(sh, "C_10u_25V", "V12_QI", G)
    D.C(sh, "C_100n_50V", "V12_QI", G)
    D.R(sh, "100k", "QI_NTC", G, fields={"Note": "NTC unused (datasheet)"})
    D.R(sh, "100k", "QI_FOD", G, fields={"Note": "LOSS_THR 50-130k: start at 100k, tune FOD on the bench"})
    D.C(sh, "C_100n_50V", "QI_BST1", "QI_LX1", fields={"V_across": 5.5})
    D.C(sh, "C_100n_50V", "QI_BST2", "QI_LX2", fields={"V_across": 5.5})
    D.IC(sh, "NX3225SA-24MHZ-EXS00A-CS08583", {"1": "QI_XI", "3": "QI_XO", "GND": G}, prefix="Y", value="24MHz VERIFY",
         fields={"LCSC": "C2762192", "Note": "frequency not confirmed from the datasheet text - VERIFY before ordering"}, dnp=True) \
        if False else D.CONN(sh, "QI_XTAL_TBD", ["XI", "XO"], {"XI": "QI_XI", "XO": "QI_XO"}, footprint="", prefix="Y",
                             fields={"Note": "IP6826 crystal: frequency/load TBD from datasheet PDF"}, dnp=True)
    # resonant tank: 4x 100 nF C0G 100 V in parallel (~400 nF) in series with the A11 coil
    for _ in range(4):
        D.IC(sh, "C1206N104J101T", {"1": "QI_LX1", "2": "QI_RES"}, prefix="C", value="100nF 100V C0G",
             fields={"Rated_V": 100.0, "Note": "resonant cap, C0G only. Coil voltage peak TBD on bench (VERIFY <= 50 V)"})
    D.v("QI_RES", 50.0)
    D.v("QI_LX1", 12.4)
    D.v("QI_LX2", 12.4)
    D.CONN(sh, "QI_COIL", ["A", "B"], {"A": "QI_RES", "B": "QI_LX2"}, footprint="", prefix="L",
           fields={"LCSC": "C3003211", "Note": "CND-tek A11 6.3 uH coil + ferrite, wired to pads under the PC/glass window"})
    # demodulation network placeholders (VERIFY values against the IP6826 reference design)
    D.R(sh, "100k", "QI_RES", "QI_VDET", fields={"Note": "VDET divider top VERIFY"})
    D.R(sh, "10k", "QI_VDET", G)
    D.R(sh, "100k", "QI_RES", "QI_VDEC", fields={"Note": "V_DECODE network VERIFY"})
    D.C(sh, "C_10n_50V", "QI_VDEC", G)
    for i in (1, 2, 3):
        D.TP(sh, f"QI_LED{i}", small=True)
    D.TP(sh, "V12_QI")
    return sh
