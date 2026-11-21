"""Auxiliary inputs: DC barrel jack (solar/adapter) + PoE (isolated VPOE), ORed into one forward-only
BQ25756 stage that charges the bus. USB-C inputs use each port's own bidirectional stage.

DC jack path: J -> TVS -> TPS26631 eFuse (back-to-back blocking FET, OV 26 V, UV 10 V, I_LIM 1.65 A
               = 3:1 on the 5 A jack) -> LM74700 ideal diode -> VIN_AUX
PoE path:     VPOE (isolated 20 V, see poe.py) -> LM74700 ideal diode -> VIN_AUX
TPS2663 datasheet: OVP/UVLO thresholds 1.2 V; I_LIM example 9.09k = 2 A (I = 18.18/R[kOhm]);
               blocking FET: source to IN_SYS, drain to IN, gate to B_GATE; pulldown FET across B_GATE/DRV/IN_SYS.
"""


def ideal_diode(D, sh, anode, cathode, tag):
    """LM74700 + N-FET ideal diode (ORing)."""
    g, vcap = f"{tag}_GATE", f"{tag}_VCAP"
    D.IC(sh, "LM74700QDBVRQ1", {"VCAP": vcap, "GND": "GND", "EN": anode, "CATHODE": cathode, "GATE": g, "ANODE": anode},
         fields={"Note": "ideal-diode ORing (reverse-current blocking)"})
    D.C(sh, "C_100n_50V", vcap, anode, fields={"V_across": 15.0, "Note": "VCAP charge-pump cap per LM74700 datasheet. VERIFY value/rating"})
    D.FET(sh, "NTMFS5C628NLT1G", g, cathode, anode, vds=60, id100=100, irms=2.5)
    D.v(g, 40.0)
    D.v(vcap, 40.0)


def efuse(D, sh, vin_raw, vout, tag, ilim_r="11k", note=""):
    """TPS26631 with input blocking FET, OV 24.3 V / UV 10.0 V, auto-retry."""
    ins = f"{tag}_INSYS"
    D.IC(sh, "TPS26631RGER", {
        "IN": f"{tag}_IN", "B_GATE": f"{tag}_BG", "DRV": f"{tag}_DRV", "IN_SYS": ins, "UVLO": f"{tag}_UV",
        "OVP": f"{tag}_OV", "GND": "GND", "dVdT": f"{tag}_DVDT", "ILIM": f"{tag}_ILIM", "MODE": "GND",
        "~{SHDN}": f"{tag}_EN", "IMON": f"{tag}_IMON", "~{FLT}": f"{tag}_FLT", "PGTH": vout, "PGOOD": f"{tag}_PG",
        "OUT": vout, "EP": "GND"}, nc=["N.C"],
        fields={"Op_I": 1.65, "Rated_I": 6.0, "Note": f"I_LIM {ilim_r} = 1.65 A (3:1 on 5 A jack). MODE=GND auto-retry. {note}"})
    for n_, v in [(f"{tag}_IN", 24.3), (ins, 24.3), (vout, 24.3), (f"{tag}_BG", 40), (f"{tag}_DRV", 40), (f"{tag}_UV", 3.6), (f"{tag}_OV", 3.6),
                  (f"{tag}_DVDT", 5.5), (f"{tag}_ILIM", 5.5), (f"{tag}_IMON", 5.5), (f"{tag}_EN", 3.6), (f"{tag}_FLT", 3.6), (f"{tag}_PG", 3.6)]:
        D.v(n_, v)
    # back-to-back blocking FET: S -> IN_SYS (connector side), D -> IN
    D.FET(sh, "NTMFS5C628NLT1G", f"{tag}_BG", f"{tag}_IN", ins, vds=60, id100=100, irms=1.67)
    D.IC(sh, "AO3400A", {"D": f"{tag}_BG", "G": f"{tag}_DRV", "S": ins}, prefix="Q",
         fields={"Note": "B_GATE fast pulldown (TPS2663 Fig 8-7)"})
    D.R(sh, "178k", ins, f"{tag}_UV", fields={"V_across": 24.3})
    D.R(sh, "14.3k", f"{tag}_UV", f"{tag}_OV")
    D.R(sh, "10k", f"{tag}_OV", "GND", fields={"Note": "UV 9.99 V / OV 24.3 V (1.2 V thresholds; OV at the 24 V jack rating)"})
    D.R(sh, ilim_r, f"{tag}_ILIM", "GND")
    D.C(sh, "C_22n_50V", f"{tag}_DVDT", "GND", fields={"Note": "inrush slew"})
    D.R(sh, "1k", f"{tag}_IMON", "GND", fields={"Note": "IMON scale VERIFY"})
    D.R(sh, "10k", f"{tag}_FLT", "V3V3")
    D.R(sh, "10k", f"{tag}_PG", "V3V3")
    D.R(sh, "100k", f"{tag}_EN", "V3V3", fields={"Note": "enabled by default; EXP can pull SHDN low"})
    D.C(sh, "C_1u_50V", ins, "GND")
    D.C(sh, "C_1u_50V", vout, "GND")
    D.TP(sh, f"{tag}_IMON", small=True)
    D.TP(sh, f"{tag}_FLT", small=True)


def bq_stage(D, sh, tag, vac, ch, ichg_r, ilim_r, ce_net, note, irms, vmax=24.3):
    """BQ25756 stage between vac and VBAT (forward or reverse)."""
    n = lambda s: f"{tag}_{s}"  # noqa: E731
    VIN, VOUT, SW1, SW2 = n("VIN"), n("VOUT"), n("SW1"), n("SW2")
    for net, v in [(VIN, vmax), (vac, vmax), (VOUT, 21.0), (SW1, vmax), (SW2, 21.0)]:
        D.v(net, v)
    for s in ("REGN", "TS", "ICHG", "ILIM", "FB", "FBG", "FSW", "PGLED", "PGLEDK", "PG", "STAT1", "STAT2"):
        D.v(n(s), 5.5)
    D.IC(sh, "BQ25756RRVR", {
        "SCL": f"I2C{ch}_SCL", "SDA": f"I2C{ch}_SDA", "~{INT}": "CHG_INT_N", "STAT1": n("STAT1"), "STAT2": n("STAT2"),
        "~{PG}": n("PG"), "~{CE}": ce_net, "TS": n("TS"), "ICHG": n("ICHG"), "ILIM_HIZ": n("ILIM"), "FBG": n("FBG"),
        "FB": n("FB"), "SRN": "VBAT", "SRP": VOUT, "PGND": "GND", "SW2": SW2, "HIDRV2": n("HD2"), "BTST2": n("BT2"),
        "LODRV2": n("LD2"), "DRV_SUP": n("REGN"), "REGN": n("REGN"), "LODRV1": n("LD1"), "BTST1": n("BT1"),
        "HIDRV1": n("HD1"), "SW1": SW1, "ACN": VIN, "ACP": vac, "VAC": vac, "ACUV": vac, "ACOV": "GND", "FSW_SYNC": n("FSW")},
        nc=["NC"], fields={"Note": f"I2C 0x6B on mux channel {ch}. {note}"})
    for g, d, s, gn in [(n("HD1g"), VIN, SW1, n("HD1")), (n("LD1g"), SW1, "GND", n("LD1")),
                        (n("HD2g"), VOUT, SW2, n("HD2")), (n("LD2g"), SW2, "GND", n("LD2"))]:
        D.FET(sh, "NTMFS5C628NLT1G", g, d, s, vds=60, id100=100, irms=irms)
        D.R(sh, "0", gn, g)
    D.L(sh, "TMPA1707SP-6R8MN-D", SW1, SW2, rated_i=22, isat=25, irms=irms, ipk=irms + 1.6, value="6.8uH 22A")
    D.RSENSE(sh, vac, VIN, i_op=2.7)
    D.RSENSE(sh, VOUT, "VBAT", i_op=irms)
    D.C(sh, "C_100n_16V", n("BT1"), SW1, fields={"V_across": 5.5})
    D.C(sh, "C_100n_16V", n("BT2"), SW2, fields={"V_across": 5.5})
    D.C(sh, "C_4u7_16V", n("REGN"), "GND")
    D.C(sh, "C_4u7_16V", n("REGN"), "GND")
    D.C(sh, "C_470n_50V", vac, VIN, fields={"V_across": 1.0})
    D.C(sh, "C_100n_50V", vac, "GND")
    D.C(sh, "C_470n_50V", VIN, "GND")
    D.C(sh, "C_470n_50V", VOUT, "VBAT", fields={"V_across": 1.0})
    D.C(sh, "C_100n_50V", VOUT, "GND")
    for _ in range(3):
        D.C(sh, "C_10u_50V", VIN, "GND")
    for _ in range(3):
        D.C(sh, "C_10u_50V", VOUT, "GND")
    D.R(sh, "249k", "VBAT", n("FB"))
    D.R(sh, "20k", n("FB"), n("FBG"), fields={"Note": "20.66 V bus regulation"})
    D.R(sh, ichg_r, n("ICHG"), "GND")
    D.R(sh, ilim_r, n("ILIM"), "GND")
    D.R(sh, "80.6k", n("FSW"), "GND")
    D.R(sh, "5.23k", n("REGN"), n("TS"))
    D.R(sh, "30.1k", n("TS"), "GND")
    D.jlc_generic(sh, "NTC", "NTC_10k_0603", {"1": n("TS"), "2": "GND"}, prefix="TH", value="10k NTC @stage",
                  footprint="Resistor_SMD:R_0603_1608Metric")
    D.TP(sh, n("STAT1"), small=True)
    D.TP(sh, n("STAT2"), small=True)
    D.JP(sh, "V3V3", n("PGLED"), note="LED cut")
    D.R(sh, "2.2k", n("PGLED"), n("PGLEDK"))
    D.IC(sh, "KT-0603R", {"A": n("PGLEDK"), "K": n("PG")}, prefix="D", value="PG LED")
    for t in (VIN, VOUT, SW1, SW2):
        D.TP(sh, t)


def build(D):
    sh = D.sheet("power_input", "Aux inputs: DC jack (solar/adapter) + PoE, ORed into a forward-only charger stage")
    sh.note("DC jack limited to 1.65 A by the eFuse (3:1 on the 5 A jack rating) -> 40 W at 24 V.")
    sh.note("Inputs OR by highest voltage. Firmware can force a source by disabling an eFuse (SHDN) / PoE path.")
    D.IC(sh, "DC-005-5A-2.0", {"1": "DCI_RAW", "2": "GND", "3": "GND"}, prefix="J", value="DC IN 2.0mm",
         fields={"Op_I": 1.65, "Rated_I": 5.0, "Note": "pin1 centre (+). VERIFY pin map on footprint"})
    D.v("DCI_RAW", 24.3)
    D.IC(sh, "SMBJ33A", {"K": "DCI_RAW", "A": "GND"}, prefix="D", fields={"Note": "jack TVS (standoff 33 V >= 26.4 V)"})
    D.C(sh, "C_1u_50V", "DCI_RAW", "GND")
    # eFuse: IN_SYS is the connector side when a blocking FET is used
    D.JP(sh, "DCI_RAW", "DCI_INSYS", i_op=1.65, note="DC-in isolate")
    efuse(D, sh, "DCI_RAW", "DCI_OUT", "DCI")
    D.v("DCI_OUT", 24.3)
    ideal_diode(D, sh, "DCI_OUT", "VIN_AUX", "DCI_ORING")
    ideal_diode(D, sh, "VPOE", "VIN_AUX", "POE_ORING")
    D.C(sh, "C_10u_50V", "VIN_AUX", "GND")
    D.C(sh, "C_10u_50V", "VIN_AUX", "GND")
    D.TP(sh, "VIN_AUX")
    D.TP(sh, "DCI_OUT")
    # forward-only charger stage (input ~46 W max -> ~3.1 A into the bus)
    bq_stage(D, sh, "INS", "VIN_AUX", 4, ichg_r="15k", ilim_r="7.5k", ce_net="INS_CE",
             note="Forward only (EN_REV never set). ICHG 50/15k = 3.33 A, ILIM 20/7.5k = 2.67 A.", irms=3.4)
    D.R(sh, "10k", "INS_CE", "GND")
    D.TP(sh, "INS_CE", small=True)
    return sh
