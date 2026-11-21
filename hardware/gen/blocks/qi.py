"""Qi wireless pad: Injoinic IP6826 (WPC 1.2.4 TX SoC, integrated full bridge) on V5_QI -> hardware-limited to 5 W.

IP6826 datasheet (LCSC C2921390, V1.1) facts used:
  Features: "5V input for 5W output application; 9V input for 5W, 7.5W, 10W; 12V input for 5W ... 15W" -> a 5 V supply
  is the only input that caps the TX at 5 W BPP (P-29 / X-25 / C-24). VIN recommended 4.5-12 V, abs max 16 V.
  DPM below 4.3 V input. VCC 2.2 uF close to pin 4. EPAD/PGND to the high side of the 20 mOhm shunt.
  NC pins 25/31 float. NTC pin sources 20 uA; stop < 0.5 V, resume > 0.72 V; "100K@25C B=3950, R_SetPoint1 = 0 ->
  60 C". LOSS_THR 50-130k, default 100k (dynamic FOD). VDET: default 2.2 nF to ground (static FOD).
  Reference BOM (single coil): D1 1N5819; C10-C12 3x 15 nF; C5 2.2 nF; C4/C6/C8 100 nF; C7 2.2 uF; R26 100k; R25 133k;
  R22 3.3k; R20/R27 100k; R23/R24 1k; R21 10k; C1 10 uF; C2/C3 22 uF; R16 20 mOhm; coil 10 uH + 250 nF. No crystal.
  The demodulation TOPOLOGY (Fig. 4 voltage ASK, Fig. 5 current ASK, p.11-12 schematic) is only in the PDF figures:
  the wiring below uses exactly the BOM values but its topology is a reconstruction -> VERIFY against the PDF.
Layout (DS 8): Kelvin ISENSE/IGND leads from both shunt ends; VIN caps return to PGND with minimum loop; V_DECODE/VDET
  guarded, away from the coil and resonant caps.
"""


def build(D):
    sh = D.sheet("qi", "Qi transmitter (5 W, 5 V input) under the non-metal top window", board="B")
    sh.note("5 V input -> IP6826 can only run the 5 W BPP profile (DS features). V5_QI from a TPS56A37 on aux_power.")
    sh.note("Demod network values = reference BOM; topology reconstructed from the BOM, VERIFY vs datasheet Fig. 4/5 and p.12 schematic.")
    G = "GND"
    D.JP(sh, "V5_QI", "QI_VIN", i_op=1.45, note="Qi isolate")
    D.IC(sh, "IP6826QFN32", {
        "GND": G, "AGND": G, "IGND": "QI_IGND", "ISENSE": "QI_ISNS", "PGND": "QI_PGND", "EP": "QI_PGND", "VCC": "QI_VCC",
        "NTC": "QI_NTC", "LOSS_THR": "QI_FOD", "LED1": "QI_LED1", "LED2": "QI_LED2",
        "LED3": "QI_LED3", "V_DECODE": "QI_VDEC", "VDET": "QI_VDET", "BST1": "QI_BST1", "LX1": "QI_LX1", "LX2": "QI_LX2",
        "BST2": "QI_BST2", "VIN": "QI_VIN", "DEBUG": "QI_DEBUG_TX"},
        nc=["CC1", "CC2", "IO4", "IO7", "NC", "DM", "DP", "HOSCI", "HOSCO"],
        fields={"Op_P": 5.0, "Rated_P": 15.0,
                "Note": "C-16: order PRE-PROGRAMMED (Injoinic 5 W firmware). 5 V input -> 5 W BPP only. CC/DP/DM unused. "
                        "HOSCI/HOSCO NC: reference BOM has no crystal (C-25, VERIFY with Injoinic)."})
    D.TP(sh, "QI_DEBUG_TX", small=True)
    for n_, v in [("QI_VIN", 5.5), ("QI_VCC", 5.5), ("QI_LX1", 5.5), ("QI_LX2", 5.5), ("QI_RES", 50.0), ("QI_PGND", 0.1),
                  ("QI_ISNS", 0.1), ("QI_IGND", 0.1)]:
        D.v(n_, v)
    for n_ in ("QI_NTC", "QI_FOD", "QI_LED1", "QI_LED2", "QI_LED3", "QI_VDET", "QI_VDEC", "QI_VDIV", "QI_VPK", "QI_DEBUG_TX"):
        D.v(n_, 5.5)
    # supply: VIN bypass returns to the bridge ground QI_PGND (X-25; DS layout note 2), shunt to system GND
    D.C(sh, "C_10u_25V", "QI_VIN", "QI_PGND", fields={"Note": "C1 10 uF (reference) VIN-PGND, minimum loop"})
    for _ in range(2):
        D.C(sh, "C_22u_10V", "QI_VIN", "QI_PGND", fields={"Note": "C2/C3 22 uF (reference) VIN-PGND"})
    D.C(sh, "C_100n_16V", "QI_VIN", "QI_PGND", fields={"Note": "C4 100 nF (reference)"})
    D.IC(sh, "LR1206-21R020F4", {"1": "QI_PGND", "2": G}, prefix="R", value="20m 1W",
         fields={"Op_P": 0.05, "Rated_P": 1.0, "Note": "R16 20 mOhm shunt: 1.45^2 x 0.02 = 0.04 W"})
    D.C(sh, "C_2u2_16V", "QI_VCC", G, fields={"Note": "C7 2.2 uF at pin 4, ground to pin 1"})
    D.C(sh, "C_100n_50V", "QI_BST1", "QI_LX1", fields={"V_across": 5.5, "Note": "C6 (must not be omitted)"})
    D.C(sh, "C_100n_50V", "QI_BST2", "QI_LX2", fields={"V_across": 5.5, "Note": "C8 (must not be omitted)"})
    # FOD / NTC
    D.R(sh, "100k", "QI_FOD", G, fields={"Note": "R26 LOSS_THR default 100k (50-130k): tune dynamic FOD on the bench"})
    D.IC(sh, "NCP15WF104F03RC", {"1": "QI_NTC", "2": G}, prefix="TH", value="100k NTC B4250",
         fields={"Note": "X-25: real coil NTC (glue to the coil). 20 uA x 25k = 0.5 V stop -> 57 C with B4250 "
                         "(DS example 60 C uses B3950); resume at 36k = 48 C. R_SetPoint1 = 0, R_SetPoint2 NC."})
    # resonant tank: 4x 100 nF C0G 100 V in parallel (~400 nF) in series with the A11 6.3 uH coil
    for _ in range(4):
        D.IC(sh, "C1206N104J101T", {"1": "QI_LX1", "2": "QI_RES"}, prefix="C", value="100nF 100V C0G",
             fields={"Rated_V": 100.0, "Note": "resonant cap, C0G only. A11 coil 6.3 uH + 400 nF (DS lists 10 uH/250 nF, 13 uH/150 nF; "
                                               "A11 support stated) VERIFY. Coil voltage peak <= 50 V at 5 V in (bench)"})
    D.CONN(sh, "QI_COIL", ["A", "B"], {"A": "QI_RES", "B": "QI_LX2"}, footprint="", prefix="L",
           fields={"LCSC": "C3003211", "Note": "CND-tek A11 6.3 uH coil + ferrite, wired to pads under the PC/glass window"})
    # voltage ASK / static-FOD sense (reference values; topology VERIFY Fig. 4)
    D.R(sh, "120k", "QI_RES", "QI_VDIV_T", fields={"V_across": 45.0, "Note": "R25 133k (reference) = 120k + 12k"})
    D.R(sh, "12k", "QI_VDIV_T", "QI_VDIV", fields={"V_across": 5.0})
    D.v("QI_VDIV_T", 50.0)
    D.R(sh, "3.3k", "QI_VDIV", G, fields={"Note": "R22 3.3k: 133k/3.3k divides the coil node ~41:1"})
    D.IC(sh, "B5819W_C8598", {"+": "QI_VDIV", "-": "QI_VPK"}, prefix="D", value="B5819W",
         fields={"Note": "D1 1N5819 class (reference): envelope detector after the divider"})
    D.C(sh, "C_10n_50V", "QI_VPK", G, fields={"Note": "C10 15 nF = 10n + 4.7n"})
    D.C(sh, "C_4n7_50V", "QI_VPK", G)
    D.R(sh, "100k", "QI_VPK", G, fields={"Note": "R20 100k envelope discharge"})
    D.R(sh, "10k", "QI_VPK", "QI_VDET", fields={"Note": "R21 10k"})
    D.C(sh, "C_2n2_50V", "QI_VDET", G, fields={"Note": "C5 2.2 nF static-FOD default (DS FOD section)"})
    D.C(sh, "C_10n_50V", "QI_VPK", "QI_VDEC", fields={"Note": "C11 15 nF DC block = 10n + 4.7n"})
    D.C(sh, "C_4n7_50V", "QI_VPK", "QI_VDEC")
    D.R(sh, "100k", "QI_VDEC", G, fields={"Note": "R27 100k V_DECODE bias"})
    # current ASK (Fig. 5): Kelvin leads from both shunt ends, RC low-pass (topology VERIFY)
    D.R(sh, "1k", "QI_PGND", "QI_ISNS", fields={"Note": "R23 1k Kelvin from the shunt high side"})
    D.R(sh, "1k", G, "QI_IGND", fields={"Note": "R24 1k Kelvin from the shunt low side (separate trace, DS layout note 3)"})
    D.C(sh, "C_10n_50V", "QI_ISNS", "QI_IGND", fields={"Note": "C12 15 nF = 10n + 4.7n: LPF ~5 kHz with 2x 1k"})
    D.C(sh, "C_4n7_50V", "QI_ISNS", "QI_IGND")
    # status LED (C-25): LED1 through a series resistor, behind a cut jumper
    D.JP(sh, "QI_LED1", "QI_LED1J", note="LED cut")
    D.R(sh, "1k", "QI_LED1J", "QI_LED1A", fields={"Note": "LED1 series resistor (DS: drive LEDs through a current-limit resistor)"})
    D.LED(sh, "G", "QI_LED1A", G)
    for i in (2, 3):
        D.TP(sh, f"QI_LED{i}", small=True)
    D.TP(sh, "QI_VIN")
    return sh
