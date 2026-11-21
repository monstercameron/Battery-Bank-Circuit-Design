"""Battery cartridge PCB (separate KiCad project): 5S1P Samsung 50S, BQ7791500 standalone protector with
back-to-back low-side CHG/DSG FETs, 5 mOhm shunt, 25 A / 72 V fuse, BQ34Z100-G1 gauge (stats live in the pack),
XT60PW-F power + pogo landing pads, and a presence loop that keeps a removed cartridge in HIBERNATE (dead contacts).

BQ77915 (datasheet Table 10-1): R_IN 1k / C_IN 0.1 uF per VCx, R_VDD 1k / C_VDD 1 uF, R_S 100 / C_S 0.1 uF,
  103AT NTC with pull-up to VTB; CCFG floating = 5-cell; BQ7791500 = OV 4.20 V, UV 2.90 V, OCD1 60 mV, SCD 120 mV.
  With 5 mOhm: OCD1 = 12 A (> 8.3 A design, < 25 A cell), SCD = 24 A. PRES high = NORMAL, low = HIBERNATE.
BQ34Z100-G1: REGIN 2.7-4.5 V (TLV70433 from the pack), BAT divided to ~0.9 V, VEN switches the divider, I2C 0x55.
"""


def build(D):
    sh = D.sheet("cartridge", "Battery cartridge: 5S protector, FETs, fuse, gauge")
    sh.note("Presence loop: pogo PRES_A (pack top via 100k) is shorted to PRES_B on the main board. Removed cartridge = PRES low = HIBERNATE.")
    sh.note("Ground: VSS = BAT- (cell 0). PACK- (main-board GND) is after the CHG/DSG FETs.")
    VSS = "CELL0"
    for i in range(6):
        D.v(f"CELL{i}", 4.2 * i)
    for n_, v in [("PACK_P", 21.0), ("FUSE_IN", 21.0), ("SNS", 0.1), ("FET_MID", 21.0), ("PACK_N", 21.0), ("PRES_A", 21.0),
                  ("CRT_VDD", 21.0), ("CRT_DSG", 15.0), ("CRT_CHG", 21.0), ("CRT_LD", 21.0), ("GAUGE_DIVTOP", 21.0)]:
        D.v(n_, v)
    D.CONN(sh, "CELL_TABS", ["B0", "B1", "B2", "B3", "B4", "B5"],
           {"B0": "CELL0", "B1": "CELL1", "B2": "CELL2", "B3": "CELL3", "B4": "CELL4", "B5": "CELL5"}, footprint="", prefix="BT",
           fields={"_nobom": True, "Note": "nickel-strip tab pads for 5x Samsung 50S (spot-welded). Wide copper: 8.3 A x3"})
    # fuse in the pack + path
    D.IC(sh, "STS2250", {"1": "CELL5", "2": "PACK_P"}, prefix="F", value="25A 72V",
         fields={"Op_I": 8.3, "Rated_I": 25.0, "Note": "500 A @72 VDC interrupt. Fault current of 5x 50S TBD (VERIFY interrupt margin)"})
    # protector
    D.IC(sh, "BQ7791500PWR", {
        "VDD": "CRT_VDDF", "AVDD": "CRT_AVDD", "VC5": "VC5F", "VC4": "VC4F", "VC3": "VC3F", "VC2": "VC2F", "VC1": "VC1F", "VC0": "VC0F",
        "VSS": VSS, "SRP": "CRT_SRP", "SRN": "CRT_SRN", "DSG": "CRT_DSG", "CHG": "CRT_CHG", "LD": "CRT_LD", "LPWR": VSS,
        "CBI": VSS, "OCDP": "CRT_OCDP", "TS": "CRT_TS", "VTB": "CRT_VTB", "PRES": "PRES_B", "CTRC": "CRT_CTRC", "CTRD": "CRT_CTRD"},
        nc=["CCFG", "CBO"], fields={"Note": "CCFG floating = 5S. LPWR/CBI to VSS for a single device (VERIFY). SRP/SRN polarity VERIFY."})
    for i in range(6):
        D.R(sh, "1k", f"CELL{i}", f"VC{i}F", fields={"V_across": 4.2, "Op_P": 0.005})
        D.C(sh, "C_100n_16V" if i == 0 else "C_100n_50V", f"VC{i}F", VSS)
        D.v(f"VC{i}F", 4.2 * i)
    D.R(sh, "1k", "CELL5", "CRT_VDDF", fields={"V_across": 1.0})
    D.C(sh, "C_1u_50V", "CRT_VDDF", VSS)
    D.v("CRT_VDDF", 21.0)
    D.C(sh, "C_1u_16V", "CRT_AVDD", VSS, fields={"Note": "AVDD regulator cap VERIFY value"})
    D.R(sh, "1M", "CRT_OCDP", VSS, fields={"Note": "OCD1/2 delay programming VERIFY"})
    D.R(sh, "10k", "CRT_CTRC", VSS)
    D.R(sh, "10k", "CRT_CTRD", VSS)
    D.R(sh, "10k", "CRT_VTB", "CRT_TS")
    D.jlc_generic(sh, "NTC", "NTC_10k_0603", {"1": "CRT_TS", "2": VSS}, prefix="TH", value="10k NTC cells (protector)",
                  footprint="Resistor_SMD:R_0603_1608Metric")
    # presence / hibernate
    D.R(sh, "100k", "CELL5", "PRES_A", pkg="0603")
    D.R(sh, "1M", "PRES_B", VSS, pkg="0603", fields={"Note": "PRES low (HIBERNATE) when the cartridge is out"})
    D.v("PRES_B", 21.0)
    # current sense (low side, BAT-)
    D.RSENSE(sh, VSS, "SNS", i_op=8.3)
    D.R(sh, "100", VSS, "CRT_SRN", fields={"V_across": 0.2})
    D.R(sh, "100", "SNS", "CRT_SRP", fields={"V_across": 0.2})
    D.C(sh, "C_100n_16V", "CRT_SRP", "CRT_SRN", fields={"V_across": 0.2})
    # back-to-back low-side FETs: DSG (source at SNS), CHG (source at PACK-), common drain FET_MID
    for _ in range(2):  # two in parallel per position for 3:1 thermal margin
        D.FET(sh, "NTMFS5C628NLT1G", "CRT_DSG", "FET_MID", "SNS", vds=60, id100=100, irms=4.2)
        D.FET(sh, "NTMFS5C628NLT1G", "CRT_CHG", "FET_MID", "PACK_N", vds=60, id100=100, irms=4.2)
    D.R(sh, "100k", "CRT_LD", "PACK_N", fields={"Note": "load-removal detect VERIFY value"})
    # pack connector + pogo landing pads
    D.IC(sh, "XT60PW-F_C428722", {"+": "PACK_P", "-": "PACK_N"}, nc=["1", "2"], prefix="J", value="XT60 female",
         fields={"Op_I": 8.3, "Rated_I": 30.0})
    for name, net in [("POGO GND", "PACK_N"), ("POGO SDA", "CRT_SDA"), ("POGO SCL", "CRT_SCL"), ("POGO PRES_A", "PRES_A"), ("POGO PRES_B", "PRES_B")]:
        D.generic(sh, "TP", name, "TestPoint:TestPoint_Pad_D2.0mm", {"1": net}, prefix="P", fields={"_nobom": True})
    # gauge
    D.IC(sh, "TLV70433DBVR", {"GND": VSS, "OUT": "GAUGE_3V3", "IN": "PACK_P"}, nc=["NC"], prefix="U",
         fields={"Op_I": 0.002, "Rated_I": 0.15, "Note": "24 V max in vs 21 V pack"})
    D.C(sh, "C_1u_50V", "PACK_P", VSS)
    D.C(sh, "C_1u_16V", "GAUGE_3V3", VSS)
    D.IC(sh, "BQ34Z100PWR-G1", {"VEN": "GAUGE_VEN", "BAT": "GAUGE_BAT", "CE": "GAUGE_3V3", "REGIN": "GAUGE_3V3",
                                "REG25": "GAUGE_REG25", "VSS": VSS, "SRP": "GAUGE_SRP", "SRN": "GAUGE_SRN",
                                "P6/TS": "GAUGE_TS", "P4/SCL": "CRT_SCL", "P3/SDA": "CRT_SDA"},
         nc=["P1", "P2", "P5/HDQ"], fields={"Note": "0x55. Stores Qmax/cycle count = cartridge health record."})
    D.C(sh, "C_1u_16V", "GAUGE_REG25", VSS)
    D.R(sh, "220k", "PACK_P", "GAUGE_BAT", fields={"Note": "21 V -> 0.913 V with 10k"})
    D.R(sh, "10k", "GAUGE_BAT", "GAUGE_DIVLO")
    D.IC(sh, "AO3400A", {"D": "GAUGE_DIVLO", "G": "GAUGE_VEN", "S": VSS}, prefix="Q", fields={"Note": "divider switch (VEN)"})
    D.C(sh, "C_100n_16V", "GAUGE_BAT", VSS)
    D.R(sh, "100", VSS, "GAUGE_SRN", fields={"V_across": 0.2})
    D.R(sh, "100", "SNS", "GAUGE_SRP", fields={"V_across": 0.2})
    D.C(sh, "C_100n_16V", "GAUGE_SRP", "GAUGE_SRN", fields={"V_across": 0.2})
    D.jlc_generic(sh, "NTC", "NTC_10k_0603", {"1": "GAUGE_TS", "2": VSS}, prefix="TH", value="10k NTC cells (gauge)",
                  footprint="Resistor_SMD:R_0603_1608Metric")
    for n_ in ("CRT_SDA", "CRT_SCL", "GAUGE_3V3", "GAUGE_TS", "GAUGE_VEN", "GAUGE_BAT", "GAUGE_DIVLO", "GAUGE_REG25",
               "CRT_SRP", "CRT_SRN", "GAUGE_SRP", "GAUGE_SRN", "CRT_AVDD", "CRT_OCDP", "CRT_TS", "CRT_VTB", "CRT_CTRC", "CRT_CTRD"):
        D.v(n_, 3.6)
    for t in ("PACK_P", "PACK_N", "CELL5", "CELL0", "CRT_DSG", "CRT_CHG", "SNS"):
        D.TP(sh, t)
    return sh
