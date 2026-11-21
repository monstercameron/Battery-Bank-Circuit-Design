"""USB-C port k (1..4): connector, ESD, TPD4S480, TPS26750 + EEPROM, BQ25756 bidirectional
100 W stage, HD3SS3212 SS mux, RTL8156BG 2.5GbE with its own 0.95 V buck.

Datasheet values used (docs/datasheets/text/*.txt):
  BQ25756  VFB = 1.536 V; R_TOP 249k (TI example); K_ICHG = 50 A*kOhm @5 mOhm; K_ILIM = 50 A*kOhm @2 mOhm
           (-> 20 A*kOhm @5 mOhm); RT1 5.24k / RT2 30.31k for 103AT; R_FSW: 80k = 350 kHz.
  TPS26750 ADCIN SafeMode straps (Table 7-6): #1 (7,0) #2 (0,0) #3 (6,0) #4 (5,7); EEPROM >= 36 KB @0x50;
           C_VIN3V3 10u, C_LDO3V3 10u, C_LDO1V5 >=4.5u, C_VBUS 4.7u, C_CC 200-480 pF.
  TPD4S480 VBIAS 0.1 uF >=63 V (100 V recommended), VPWR 1 uF, VBUS_LV 0.1 uF, RPD_Gx->C_CCx for dead battery.
  TPS62933 FB 0.8 V; RT = 71.5k -> 310 kHz (t_on_min 70 ns at 21 V -> 0.95 V needs <= ~640 kHz).
"""

ADCIN = {  # port -> (ADCIN1 source, ADCIN2 source); "DIV6" = divider to 0.806 of LDO_3V3
    1: ("LDO3", "GND"), 2: ("GND", "GND"), 3: ("DIV6", "GND"), 4: ("LDO15", "LDO3"),
}


def build(D, k):
    sh = D.sheet(f"usbc_port_{k}", f"USB-C port {k}: 100 W bidirectional PD 3.x EPR + 2.5GbE")
    n = lambda s: f"{s}_C{k}"  # noqa: E731
    G = "GND"
    VBUS, VIN, VOUT, SW1, SW2 = n("VBUS"), n("VIN"), n("VOUT"), n("SW1"), n("SW2")
    for net, v in [(VBUS, 28.0), (VIN, 28.0), (VOUT, 21.0), (SW1, 28.0), (SW2, 21.0), (n("VBUSLV"), 22.0)]:
        D.v(net, v)
    sh.note("Port power: 100 W max (20 V/5 A or 28 V EPR/3.57 A). Stage sized 3:1 on current (inductor 22 A rated vs 7 A RMS).")
    sh.note("Data role: TPS26750 configured to swap to UFP (DR_Swap) so the host sees the RTL8156BG as a USB NIC. VERIFY on EVM.")

    # ---------------------------------------------------------------- connector + ESD
    J = D.IC(sh, "HC-TYPE-C-24P-MM0.8-5A-01", {
        "A4": VBUS, "A9": VBUS, "B4": VBUS, "B9": VBUS,
        "A1": G, "B1": G, "A12": G, "B12": G, "25": G, "26": G, "27": G, "28": G,
        "A5": n("CONN_CC1"), "B5": n("CONN_CC2"),
        "A6": n("DPC"), "B6": n("DPC"), "A7": n("DNC"), "B7": n("DNC"),
        "A2": n("SSTX1P"), "A3": n("SSTX1N"), "B11": n("SSRX1P"), "B10": n("SSRX1N"),
        "B2": n("SSTX2P"), "B3": n("SSTX2N"), "A11": n("SSRX2P"), "A10": n("SSRX2N"),
    }, nc=["A8", "B8"], prefix="J", fields={"Op_I": 5.0, "Rated_I": 5.0, "Derating_Exception": "USB-C 5 A contact rating, docs/design-rules.md 1.4"})
    D.IC(sh, "SMBJ33A", {"K": VBUS, "A": G}, prefix="D", fields={"Note": "VBUS TVS: standoff 33 V >= 28 V x1.1"})
    for side in (1, 2):
        D.IC(sh, "TPD4E05U06DQAR_C138714", {"D1+": n(f"SSTX{side}P"), "D1-": n(f"SSTX{side}N"),
                                             "D2+": n(f"SSRX{side}P"), "D2-": n(f"SSRX{side}N"), "GND": G},
             nc=["NC"], prefix="U")

    # ---------------------------------------------------------------- TPD4S480 CC/D+/D- protection
    D.IC(sh, "TPD4S480RUKR_C43131250", {
        "C_SBU1": n("DPC"), "C_SBU2": n("DNC"), "VBIAS": n("VBIAS"), "C_CC1": n("CONN_CC1"), "C_CC2": n("CONN_CC2"),
        "RPD_G1": n("CONN_CC1"), "RPD_G2": n("CONN_CC2"), "GND": G, "~{FLT}": n("TPDFLT"), "VPWR": "V3V3",
        "CC1": n("CC1"), "CC2": n("CC2"), "SBU1": n("U2DP"), "SBU2": n("U2DN"), "EPR_EN": n("EPREN"),
        "VBUS_LV": n("VBUSLV"), "VBUS": VBUS, "EP": G}, nc=["EPR_BLK_G"],
        fields={"Note": "SBU channels used to protect USB2 D+/D- (datasheet pin note). VERIFY USB2 HS signal integrity."})
    D.C(sh, "C_100n_100V", n("VBIAS"), G, fields={"Note": "VBIAS cap: >=63 V required, 100 V recommended"})
    D.C(sh, "C_1u_16V", "V3V3", G)
    D.R(sh, "10k", n("TPDFLT"), "V3V3")
    D.R(sh, "100k", n("EPREN"), G)

    # ---------------------------------------------------------------- TPS26750 PD controller
    a1, a2 = ADCIN[k]
    src = {"LDO3": n("LDO3V3"), "LDO15": n("LDO1V5"), "GND": G}
    adc1 = n("ADCIN1") if a1 == "DIV6" else src[a1]
    adc2 = src[a2]
    D.IC(sh, "TPS26750SRSMR_C42166327", {
        "LDO_3V3": n("LDO3V3"), "ADCIN1": adc1, "ADCIN2": adc2, "LDO_1V5": n("LDO1V5"),
        "GPIO0": n("MUXSEL"), "GPIO1": n("EPREN"), "GPIO2": n("TPDFLT"),
        "I2Ct_SDA": "I2C_SDA", "I2Ct_SCL": "I2C_SCL", "~{I2Ct_IRQ}": "PD_INT_N", "GND": G,
        "I2Cc_SDA": n("PDE_SDA"), "I2Cc_SCL": n("PDE_SCL"), "~{I2Cc_IRQ}": n("PDE_IRQ"),
        "CC1": n("CC1"), "CC2": n("CC2"), "VBUS": n("VBUSLV"), "PP5V": "V5_PD", "VIN_3V3": "V3V3"},
        nc=["GPIO11", "GPIO3", "POWER_PATH_EN", "NC", "GPIO4/USB_P/LD1", "GPIO5/USB_N/LD2", "GPIO7", "GPIO6"],
        fields={"Note": f"I2C target 0x{0x20 + k - 1:02X} (ADCIN SafeMode strap #{k}); config + patch from EEPROM 0x50"})
    if a1 == "DIV6":
        D.R(sh, "24k", n("LDO3V3"), n("ADCIN1"))
        D.R(sh, "100k", n("ADCIN1"), G)
    D.C(sh, "C_10u_16V", n("LDO3V3"), G)
    D.C(sh, "C_10u_16V", n("LDO1V5"), G)
    D.C(sh, "C_10u_16V", "V3V3", G)
    D.C(sh, "C_4u7_50V", n("VBUSLV"), G, fields={"Note": "C_VBUS 4.7 uF (TPS26750) on divided VBUS_LV"})
    D.C(sh, "C_22u_10V", "V5_PD", G, fields={"Note": "PP5V (VCONN only). Datasheet lists 120 uF when sourcing 3 A from PP5V - not used here. VERIFY"})
    D.C(sh, "C_330p_50V", n("CC1"), G)
    D.C(sh, "C_330p_50V", n("CC2"), G)
    for net in (n("PDE_SDA"), n("PDE_SCL"), n("PDE_IRQ")):
        D.R(sh, "4.7k", net, "V3V3")
    D.IC(sh, "M24512-RMN6TP", {"E0": G, "E1": G, "E2": G, "VSS": G, "SDA": n("PDE_SDA"), "SCL": n("PDE_SCL"),
                                "~{WC}": G, "VCC": "V3V3"}, fields={"Note": "64 KB (>= 36 KB required) PD config/patch EEPROM @0x50"})
    D.C(sh, "C_100n_16V", "V3V3", G)
    D.TP(sh, n("PDE_SDA"), small=True)
    D.TP(sh, n("PDE_SCL"), small=True)

    # ---------------------------------------------------------------- BQ25756 100 W stage
    ch = k - 1  # mux channel
    sda, scl = f"I2C{ch}_SDA", f"I2C{ch}_SCL"
    D.IC(sh, "BQ25756RRVR", {
        "SCL": scl, "SDA": sda, "~{INT}": "CHG_INT_N", "STAT1": n("STAT1"), "STAT2": n("STAT2"), "~{PG}": n("PG"),
        "~{CE}": n("CE"), "TS": n("TS"), "ICHG": n("ICHG"), "ILIM_HIZ": n("ILIM"), "FBG": n("FBG"), "FB": n("FB"),
        "SRN": "VBAT", "SRP": VOUT, "PGND": G, "SW2": SW2, "HIDRV2": n("HD2"), "BTST2": n("BT2"), "LODRV2": n("LD2"),
        "DRV_SUP": n("REGN"), "REGN": n("REGN"), "LODRV1": n("LD1"), "BTST1": n("BT1"), "HIDRV1": n("HD1"), "SW1": SW1,
        "ACN": VIN, "ACP": VBUS, "VAC": VBUS, "ACUV": VBUS, "ACOV": G, "FSW_SYNC": n("FSW")},
        nc=["NC"], fields={"Note": f"I2C 0x6B on mux channel {ch}. ACUV tied to VAC / ACOV to PGND (unused, per pin table)."})
    # power FETs: NTMFS5C628NL 60 V (>=1.5x28 V), I_D >> 3x 7 A
    q = "NTMFS5C628NLT1G"
    for g, d, s, gn in [(n("HD1g"), VIN, SW1, n("HD1")), (n("LD1g"), SW1, G, n("LD1")),
                        (n("HD2g"), VOUT, SW2, n("HD2")), (n("LD2g"), SW2, G, n("LD2"))]:
        D.FET(sh, q, g, d, s, vds=60, id100=100, irms=7.0)
        D.R(sh, "0", gn, g, fields={"Note": "gate resistor footprint (0 ohm; tune for EMI)"})
    D.L(sh, "TMPA1707SP-6R8MN-D", SW1, SW2, rated_i=22, isat=25, irms=7.0, ipk=8.6, value="6.8uH 22A")
    D.RSENSE(sh, VBUS, VIN, i_op=5.0)
    D.RSENSE(sh, VOUT, "VBAT", i_op=7.0)
    D.C(sh, "C_100n_16V", n("BT1"), SW1, fields={"V_across": 5.5})
    D.C(sh, "C_100n_16V", n("BT2"), SW2, fields={"V_across": 5.5})
    D.C(sh, "C_4u7_16V", n("REGN"), G)
    D.C(sh, "C_4u7_16V", n("REGN"), G)
    # sense filters
    D.C(sh, "C_470n_100V", VBUS, VIN, fields={"V_across": 1.0})
    D.C(sh, "C_100n_100V", VBUS, G)
    D.C(sh, "C_470n_100V", VIN, G)
    D.C(sh, "C_470n_50V", VOUT, "VBAT", fields={"V_across": 1.0})
    D.C(sh, "C_100n_50V", VOUT, G)
    D.C(sh, "C_100n_50V", "VBAT", G)
    # bulk
    for _ in range(4):
        D.C(sh, "C_4u7_100V", VIN, G)
    D.C(sh, "C_100n_100V", VIN, G)
    for _ in range(4):
        D.C(sh, "C_10u_50V", VOUT, G)
    D.C(sh, "C_1u_100V", VBUS, G, fields={"Note": "USB-C source bulk on VBUS (keep total within cSrcBulk spec)"})
    # programming resistors
    D.R(sh, "249k", "VBAT", n("FB"), fields={"Note": "VBAT_REG = 1.536 x (1 + 249k/20k) = 20.66 V (4.13 V/cell)"})
    D.R(sh, "20k", n("FB"), n("FBG"))
    D.R(sh, "7.5k", n("ICHG"), G, fields={"Note": "ICHG ceiling 50/7.5 = 6.7 A (stage output into the bus)"})
    D.R(sh, "4.02k", n("ILIM"), G, fields={"Note": "input limit 20/4.02 = 4.97 A with 5 mOhm (hardware ceiling, USB 5 A)"})
    D.R(sh, "80.6k", n("FSW"), G, fields={"Note": "~347 kHz"})
    D.R(sh, "5.23k", n("REGN"), n("TS"))
    D.R(sh, "30.1k", n("TS"), G)
    D.jlc_generic(sh, "NTC", "NTC_10k_0603", {"1": n("TS"), "2": G}, prefix="TH", value="10k NTC @connector",
                  footprint="Resistor_SMD:R_0603_1608Metric", fields={"Note": "Place at the USB-C connector: TS ADC = connector temperature"})
    D.R(sh, "10k", n("CE"), G, fields={"Note": "charge enabled in hardware; firmware uses EN_CHG"})
    D.TP(sh, n("CE"), small=True)
    D.TP(sh, n("STAT1"), small=True)
    D.TP(sh, n("STAT2"), small=True)
    D.JP(sh, "V3V3", n("PGLED"), note="LED cut")
    D.R(sh, "2.2k", n("PGLED"), n("PGLEDK"))
    D.IC(sh, "KT-0603R", {"A": n("PGLEDK"), "K": n("PG")}, prefix="D", value="PG LED")
    for t in (VBUS, VIN, VOUT, SW1, SW2):
        D.TP(sh, t)

    # ---------------------------------------------------------------- SuperSpeed mux + RTL8156BG
    D.IC(sh, "HD3SS3212IRKSR", {
        "OEn": G, "A0p": n("TXC_P"), "A0n": n("TXC_N"), "A1p": n("U3RXP"), "A1n": n("U3RXN"), "GND": G, "VCC": "V3V3",
        "SEL": n("MUXSELR"), "B0P": n("SSTX1P"), "B0N": n("SSTX1N"), "B1P": n("SSRX1P"), "B1N": n("SSRX1N"),
        "C0P": n("SSTX2P"), "C0N": n("SSTX2N"), "C1P": n("SSRX2P"), "C1N": n("SSRX2N"), "EP": G},
        nc=["RSVD1", "RSVD2"], fields={"Note": "SEL from TPS26750 GPIO0 configured as plug-orientation output. VERIFY RSVD pin handling"})
    D.C(sh, "C_100n_16V", "V3V3", G)
    D.R(sh, "1k", n("MUXSEL"), n("MUXSELR"), fields={"Note": "H-6: mux on always-on V3V3; series R on SEL"})
    D.C(sh, "C_100n_16V", n("U3TXP"), n("TXC_P"), fields={"Note": "USB3 TX AC coupling (device side)"})
    D.C(sh, "C_100n_16V", n("U3TXN"), n("TXC_N"))
    V09 = n("V0V95")
    D.v(V09, 1.0)
    mdi = {}
    for i, pair in enumerate("ABCD"):
        mdi[f"MDIP{i}"] = n(f"MDI{i}P")
        mdi[f"MDIN{i}"] = n(f"MDI{i}N")
    D.IC(sh, "RTL8156BG-CG", {
        "POW_EXT_SWR": n("EXTSWR"), "DVDD09": V09, "AVDD09": V09, "U3VDD09": V09, "U2VDD09": V09,
        "AVDD33": "V3V3_ETH", "AVDD33_XTAL": "V3V3_ETH", "DVDD33": "V3V3_ETH", "DVDD33_UPS": "V3V3_ETH", "U2VDD33": "V3V3_ETH",
        "DVDD09_UPS": n("UPS09"), "CKXTAL1": n("XI"), "CKXTAL2": n("XO"), "RSET": n("RSET"),
        **mdi, "LED2": n("LINKLED"), "U3SSTXP": n("U3TXP"), "U3SSTXN": n("U3TXN"),
        "U3SSRXP": n("U3RXP"), "U3SSRXN": n("U3RXN"), "U2DM": n("U2DN"), "U2DP": n("U2DP"), "GND": G},
        nc=["LANWAKEB", "GPI", "NC", "CKOUT", "EEDO/SPISO", "TWSI_SDA/SPICSB", "EECS/TWSI_SCL", "GPIO3", "GPIO2/SCL",
            "GPIO1/SDA", "CONFIG_SEQ", "DOCK_DET", "LED0/EEDI/SPISI", "LED1/EESK/SPISCK", "LED3", "GPIO4"],
        fields={"Note": "MAC in eFUSE (Realtek PG tool). RSET value VERIFY (2.49k assumed, as RTL8221B/RTL8372N)."})
    D.R(sh, "2.49k", n("RSET"), G)
    D.IC(sh, "NX3225SA-25MHZ-STD-CSR-6", {"1": n("XI"), "3": n("XO"), "GND": G}, prefix="Y", value="25MHz 10pF")
    D.C(sh, "C_12p_50V", n("XI"), G)
    D.C(sh, "C_12p_50V", n("XO"), G)
    D.C(sh, "C_1u_16V", n("UPS09"), G, fields={"Note": "DVDD09_UPS internal LDO output - own cap only. VERIFY value"})
    for _ in range(6):
        D.C(sh, "C_100n_16V", V09, G)
    D.C(sh, "C_22u_6V3", V09, G)
    for _ in range(6):
        D.C(sh, "C_100n_16V", "V3V3_ETH", G)
    D.C(sh, "C_10u_16V", "V3V3_ETH", G)
    D.R(sh, "1k", "V3V3_ETH", n("LINKLEDA"))
    D.IC(sh, "KT-0603R", {"A": n("LINKLEDA"), "K": n("LINKLED")}, prefix="D", value="LINK LED")
    # MDI PHY-to-PHY AC coupling to RTL8372N port (k-1). VERIFY values with Realtek (100 nF typical).
    for i, pair in enumerate("ABCD"):
        for pol in "PN":
            D.C(sh, "C_100n_16V", n(f"MDI{i}{pol}"), f"SW_P{k-1}MDI{pair}{pol}",
                fields={"Note": "PHY-to-PHY capacitive coupling (no magnetics)"})
    # NIC core buck: TPS62933P 21 V -> 0.95 V @ 310 kHz, enabled by RTL8156BG POW_EXT_SWR
    D.IC(sh, "TPS62933PDRLR", {"RT": n("BRT"), "EN": n("EXTSWR"), "VIN": "VBAT", "GND": G, "SW": n("BSW"),
                                "BST": n("BBST"), "PG": n("V09PG"), "FB": n("BFB")},
         fields={"Op_I": 0.65, "Rated_I": 3.0, "Note": "0.65 A max NIC core (datasheet) vs 3 A -> 4.6:1"})
    D.v(n("BSW"), 21.0)
    D.R(sh, "71.5k", n("BRT"), G, fields={"Note": "310 kHz (datasheet table)"})
    D.R(sh, "100k", n("EXTSWR"), G, fields={"Note": "keeps buck off while the NIC is unpowered"})
    D.C(sh, "C_100n_16V", n("BBST"), n("BSW"), fields={"V_across": 5.5})
    D.L(sh, "MAPM0630F-4R7M-LF", n("BSW"), V09, rated_i=5.0, isat=10.0, irms=0.65, ipk=1.0, value="4.7uH 5A")
    D.R(sh, "1.87k", V09, n("BFB"), fields={"Note": "0.8 x (1 + 1.87/10) = 0.950 V"})
    D.R(sh, "10k", n("BFB"), G)
    D.C(sh, "C_10u_50V", "VBAT", G)
    D.C(sh, "C_100n_50V", "VBAT", G)
    D.C(sh, "C_22u_6V3", V09, G)
    D.R(sh, "10k", n("V09PG"), "V3V3_ETH")
    D.TP(sh, V09)
    D.TP(sh, n("V09PG"), small=True)
    return sh
