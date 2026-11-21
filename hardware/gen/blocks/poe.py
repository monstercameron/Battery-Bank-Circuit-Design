"""PoE powered device on the RJ45 (802.3bt Type 3, Class 6 ~51 W) with an isolated flyback to VPOE (~20 V).
TPS2373-4 (datasheet): VDD bypass 0.1 uF; DEN 24.9k to VDD; REF 49.9k to VSS; RCLSA 63.4 (class 4) + RCLSB 249 (class 1)
= Class 6; APD to RTN; AMPS_CTL/MPS_DUTY/UVLO_SEL open; VC_OUT 1 uF to RTN (startup supply); VC_IN from the aux winding.
Converter: LM5155 flyback controller (TIDA-050023 style) + 200 V FET + transformer (consigned) + TL431/PC817 feedback.
Primary side (POE_*, PRI_*) is isolated from system GND: 1500 V AC. Many values marked VERIFY until the flyback is designed.
"""


def build(D):
    sh = D.sheet("poe", "RJ45 + PoE PD (802.3bt Class 6) + isolated flyback to VPOE")
    G = "GND"
    sh.note("ISOLATION: everything named POE_*/PRI_* is primary side. Keep >= 2.5 mm creepage to secondary/GND (1500 V AC).")
    # RJ45 MagJack (2.5GBASE-T + bt) - consigned (none stocked at LCSC). Pins: PHY side TDx, center taps, cable-side PoE taps.
    D.CONN(sh, "RJ45_POE_2G5", ["TD0+", "TD0-", "TD1+", "TD1-", "TD2+", "TD2-", "TD3+", "TD3-", "CT",
                                "POE_12", "POE_36", "POE_45", "POE_78", "SHIELD", "LEDG_A", "LEDG_K"],
           {"TD0+": "RJ_TD0P", "TD0-": "RJ_TD0N", "TD1+": "RJ_TD1P", "TD1-": "RJ_TD1N", "TD2+": "RJ_TD2P", "TD2-": "RJ_TD2N",
            "TD3+": "RJ_TD3P", "TD3-": "RJ_TD3N", "CT": "RJ_CT", "POE_12": "POE_P12", "POE_36": "POE_P36", "POE_45": "POE_P45",
            "POE_78": "POE_P78", "SHIELD": "RJ_SHIELD", "LEDG_A": "RJ_LEDA", "LEDG_K": "ETH_PHY_INT"},
           footprint="", prefix="J", fields={"Consigned": True, "Op_I": 0.6, "Rated_I": 1.0,
                                             "Derating_Exception": "802.3bt per-pair current, docs/design-rules.md 1.4",
                                             "Note": "Candidates: YAGEO JXF0 / Pulse JXK0-2500NL / Daburn 56F-1803DGDZ2NL"})
    D.C(sh, "C_100n_16V", "RJ_CT", G, fields={"Note": "PHY-side centre-tap bypass"})
    D.C(sh, "C_1n_2kV", "RJ_SHIELD", G, fields={"V_across": 0, "Note": "shield to chassis via 1 nF 2 kV (+1M bleed)"})
    D.R(sh, "1M", "RJ_SHIELD", G, pkg="0805")
    D.R(sh, "1k", "V3V3_ETH", "RJ_LEDA")
    for n_ in ("POE_P12", "POE_P36", "POE_P45", "POE_P78"):
        D.v(n_, 57.0)
    # two full bridges (Schottky, 100 V 3 A; ~0.9 A per pair-set -> 3.3:1)
    for p in ("POE_P12", "POE_P36", "POE_P45", "POE_P78"):
        D.IC(sh, "SS310SMA", {"A": p, "K": "POE_VDD"}, prefix="D", fields={"Op_I": 0.9, "Rated_I": 3.0})
        D.IC(sh, "SS310SMA", {"A": "POE_VSS", "K": p}, prefix="D", fields={"Op_I": 0.9, "Rated_I": 3.0})
    D.v("POE_VDD", 57.0)
    D.v("POE_VSS", 0.0)
    D.IC(sh, "SMAJ58A", {"K": "POE_VDD", "A": "POE_VSS"}, prefix="D", fields={"Note": "58 V standoff (PSE 57 V max)"})
    D.IC(sh, "TPS2373-4RGWR", {
        "VDD": "POE_VDD", "DEN": "POE_DEN", "CLSA": "POE_CLSA", "VSS": "POE_VSS", "CLSB": "POE_CLSB", "REF": "POE_REF",
        "APD": "POE_RTN", "RTN": "POE_RTN", "PG": "POE_PG", "VC_OUT": "POE_VCC", "VC_IN": "POE_VAUX", "EP": "POE_VSS"},
        nc=["AMPS_CTL", "MPS_DUTY", "UVLO_SEL", "TPL", "TPH", "#BT", "NC"],
        fields={"Op_I": 0.95, "Rated_I": 2.2, "Derating_Exception": "IC-internal hot-swap FET, docs/design-rules.md 1.4", "Note": "hot-swap FET 0.1 ohm / 2.2 A (TPS2373-4)"})
    D.v("POE_RTN", 0.0)  # primary-side reference (isolated)
    D.C(sh, "C_100n_250V", "POE_VDD", "POE_VSS")
    D.R(sh, "24.9k", "POE_VDD", "POE_DEN", pkg="0805", fields={"Note": "detection signature"})
    D.R(sh, "63.4", "POE_CLSA", "POE_VSS", pkg="0805", fields={"Note": "class 4 events 1-2 (Class 6)"})
    D.R(sh, "249", "POE_CLSB", "POE_VSS", pkg="0805", fields={"Note": "class 1 events 3+ (Class 6)"})
    D.R(sh, "49.9k", "POE_REF", "POE_VSS", pkg="0805")
    D.C(sh, "C_1u_16V", "POE_VCC", "POE_RTN", fields={"V_across": 20.0, "Note": "VC_OUT 1 uF (VERIFY voltage rating >= 40 V)"})
    D.C(sh, "C_100n_50V", "POE_VAUX", "POE_RTN", fields={"V_across": 20.0})
    D.v("POE_VCC", 20.0)
    D.v("POE_VAUX", 20.0)
    D.v("POE_PG", 20.0)
    # bulk across VDD-RTN (electrolytic, 100 V >= 1.25 x 57 V)
    D.IC(sh, "RV100V47M8X10", {"1": "POE_VDD", "2": "POE_RTN"}, prefix="C", value="47uF 100V elec",
         fields={"Note": "pin 1 = + VERIFY on footprint", "Rated_V": 100})
    # flyback controller on the primary (referenced to POE_RTN). Its VCC/BIAS come from TPS2373 VC_OUT / aux winding.
    D.IC(sh, "LM5155DSSR", {"BIAS": "POE_VCC", "VCC": "PRI_VCC", "GATE": "PRI_GATE", "PGND": "POE_RTN", "CS": "PRI_CS",
                            "COMP": "PRI_COMP", "AGND": "POE_RTN", "FB": "PRI_FB", "SS": "PRI_SS", "RT": "PRI_RT",
                            "PGOOD": "PRI_PGOOD", "UVLO/SYNC": "POE_PG", "EP": "POE_RTN"},
         fields={"Note": "Flyback per TIDA-050023 (LM51551) - all compensation/feedback values VERIFY in the converter design"})
    for n_, v in [("PRI_VCC", 6.0), ("PRI_GATE", 6.0), ("PRI_CS", 1.0), ("PRI_COMP", 3.0), ("PRI_FB", 3.0), ("PRI_SS", 3.0),
                  ("PRI_RT", 3.0), ("PRI_PGOOD", 6.0), ("PRI_DRAIN", 125.0), ("PRI_SNUB", 125.0)]:
        D.v(n_, v)
    D.C(sh, "C_1u_16V", "PRI_VCC", "POE_RTN", fields={"V_across": 6.0})
    D.C(sh, "C_47n_50V", "PRI_SS", "POE_RTN", fields={"V_across": 3.0})
    D.R(sh, "100k", "PRI_RT", "POE_RTN", fields={"Note": "RT sets f_sw VERIFY (~250 kHz)"})
    D.R(sh, "10k", "PRI_PGOOD", "PRI_VCC")
    D.R(sh, "10k", "PRI_FB", "POE_RTN", fields={"Note": "FB tied low; opto controls COMP (VERIFY topology)"})
    D.C(sh, "C_10n_50V", "PRI_COMP", "POE_RTN", fields={"V_across": 3.0})
    D.R(sh, "10k", "PRI_COMP", "PRI_COMPR")
    D.C(sh, "C_100n_16V", "PRI_COMPR", "POE_RTN", fields={"V_across": 3.0})
    D.v("PRI_COMPR", 3.0)
    D.IC(sh, "FR9N20D", {"G": "PRI_GATE", "D": "PRI_DRAIN", "S": "PRI_CS"}, prefix="Q",
         fields={"Vds_rated": 200, "_drain_net": "PRI_DRAIN", "Rated_I": 7.0, "Op_Irms": 1.6, "Note": "primary switch 200 V; RCD snubber clamps the drain <= 125 V (57 V + reflected + spike) VERIFY on bench"})
    D.IC(sh, "1206W4F200LT5E", {"1": "PRI_CS", "2": "POE_RTN"}, prefix="R", value="0.2R CS VERIFY",
         fields={"Op_P": 0.08, "Rated_P": 0.25})
    # RCD snubber
    D.IC(sh, "B1100-13-F", {"A": "PRI_DRAIN", "C": "PRI_SNUB"}, prefix="D")
    D.R(sh, "10k", "PRI_SNUB", "POE_VDD", pkg="0805", fields={"Note": "snubber R VERIFY (power!)"})
    D.C(sh, "C_100n_250V", "PRI_SNUB", "POE_VDD", fields={"V_across": 100.0})
    # transformer (consigned): PRI from POE_VDD to drain, SEC to rectifier, AUX for VC_IN
    D.CONN(sh, "T_POE_FLYBACK", ["PRI_A", "PRI_B", "SEC_A", "SEC_B", "AUX_A", "AUX_B"],
           {"PRI_A": "POE_VDD", "PRI_B": "PRI_DRAIN", "SEC_A": "SEC_SW", "SEC_B": G, "AUX_A": "PRI_AUXSW", "AUX_B": "POE_RTN"},
           footprint="", prefix="T", fields={"Consigned": True, "Note": "Wurth WE-PoE++ flyback ~51 W, 1500 V AC, turns ratio TBD"})
    D.IC(sh, "B1100-13-F", {"A": "PRI_AUXSW", "C": "POE_VAUX"}, prefix="D")
    D.v("PRI_AUXSW", 60.0)
    D.v("SEC_SW", 60.0)
    # secondary rectifier + output
    D.IC(sh, "MBR20100CT-G1", {"1": "SEC_SW", "3": "SEC_SW", "2": "VPOE"}, prefix="D",
         fields={"Op_I": 2.6, "Rated_I": 10.0, "Note": "dual 10 A common cathode, both anodes paralleled"})
    for _ in range(3):
        D.C(sh, "C_10u_50V", "VPOE", G)
    D.IC(sh, "MVK-35VC100-M-6.3*8", {"1": "VPOE", "2": G}, prefix="C", value="100uF 35V elec", fields={"Rated_V": 35})
    # isolated feedback: TL431 + PC817
    D.R(sh, "71.5k", "VPOE", "SEC_REF", fields={"Note": "2.495 x (1 + 71.5/10) = 20.3 V"})
    D.R(sh, "10k", "SEC_REF", G)
    D.IC(sh, "TL431_C181103", {"REF": "SEC_REF", "C": "SEC_OPTO_K", "A": G}, prefix="U")
    D.R(sh, "1k", "VPOE", "SEC_OPTO_A")
    D.IC(sh, "PC817B_C2936042", {"AN": "SEC_OPTO_A", "CAT": "SEC_OPTO_K", "COL": "PRI_COMP", "EM": "POE_RTN"}, prefix="U",
         fields={"Note": "isolation barrier: opto rated 5 kV"})
    D.C(sh, "C_1n_2kV", "POE_RTN", G, fields={"V_across": 0.0, "Note": "Y-capacitor across the barrier (EMI)"})
    for n_ in ("SEC_REF", "SEC_OPTO_K", "SEC_OPTO_A"):
        D.v(n_, 22.0)
    D.TP(sh, "VPOE")
    D.TP(sh, "POE_PG", small=True)
    return sh
