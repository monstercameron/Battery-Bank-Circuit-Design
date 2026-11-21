"""Battery cartridge PCB (separate KiCad project): 5S1P Samsung INR21700-50S, BQ7791500 standalone protector with
back-to-back low-side CHG/DSG FETs, 5 mOhm shunt, 30 A / 58 V / 2.5 kA MIDI fuse, BQ34Z100-G1 gauge behind an ISO1540
I2C isolator, opto-isolated CART_EN gate for the pack FETs, XT60PW-F power + 7 pogo target pads.

Reference: every number below is traceable to a datasheet table (round-1 review X-1, X-3, X-4, X-5, X-9, X-10, X-31).

BQ77915 (SLUSCU0L):
  Table 7-1   SRP = battery side of RSNS, SRN = pack side; LPWR floating for a single device; CBI low = balancing on;
              CBO floating (single device); CCFG floating = 5S (Table 9-7); PRES high = NORMAL, floating = HIBERNATE.
  Table 6-1   BQ7791500: OV 4.20 V, UV 2.90 V (load-removal recovery = Y), OCD1 = OCD2 = -60 mV, SCD -120 mV / 0.96 ms,
              OCC +60 mV. With 5 mOhm: OCD 12 A, SCD 24 A, OCC 12 A.
  9.3.2.7     SCD trips when (SRP - SRN) < V_SCD, i.e. discharge must make SRP - SRN NEGATIVE. Low-side: discharge current
              returns PACK- -> FETs -> SNS -> RSNS -> CELL0, so V(SNS) > V(CELL0); SRP=CELL0, SRN=SNS gives the negative sign.
  Table 9-3   OCDP 487 kOhm 1 % -> OCD1 350 ms / OCD2 180 ms (OCD1 = OCD2 = 60 mV on -00, so the 180 ms OCD2 governs).
  8.3 / 10-1  R_VDD 1k / C_VDD 1u, R_S 100 / C_S 0.1u, R_TS_PU 10k + 103AT, R_LD 470k, R_DSG 4.5k (4.7k used),
              R_GS_DSG 1M, R_GS_CHG 3.3M + R_CHG 1M (load-removal UV recovery enabled), R_CTRx 10M.
  8.5 EC      CTRC/CTRD: ENABLED < 0.6 V (vs VSS), DISABLED 2.04 V .. VDD+0.7 V, deglitch 8 ms. R_BAL 8-20 Ohm.
BQ34Z100-G1 (SLUSBZ5D): Table 5-1 SRP nearest BAT-, SRN nearest PACK-; 6.1 BAT/REGIN/SDA/SCL/VEN abs-max 5.5 V;
  REGIN 2.7-4.5 V; external divider so that max pack voltage is ~0.9 V at BAT (7.3.x VOLTSEL), 0.1 %/25 ppm resistors.
ISO1540 (SLLSEB6F): 6.3 side-1 C <= 40 pF, I_OL1 0.5-3.5 mA; 6.9 V_OL1 up to 0.8 V (so side 1 must NOT face the gauge,
  whose V_IL max is 0.6 V); 6.10 I_CC2 <= 6.7 mA at 3.3 V.
Samsung INR21700-50S: AC impedance (1 kHz) <= 14 mOhm (spec v0.2), typical 10.0 +/- 2 mOhm AC, 16.3 +/- 2 mOhm DC (10A-1A)
  (Samsung SDI 50S introduction 2021).
"""

import copy

from sexp import Sym

SOT23 = "Package_TO_SOT_SMD:SOT-23"


def _retype(part, mapping):
    """Per-instance pin electrical-type fix for EasyEDA imports with wrong types (TLV70433 OUT imported as power_in,
    ISO1540 all unspecified). Copies the embedded symbol so hardware/lib/lcsc.kicad_sym is untouched; the lead should
    make the same change in the library (see report)."""
    sym = dict(part.sym)
    sym["node"] = copy.deepcopy(part.sym["node"])
    sym["pins"] = [dict(p, etype=mapping.get(p["name"], p["etype"])) for p in part.sym["pins"]]

    def walk(n):
        for x in n:
            if isinstance(x, list) and x:
                if x[0] == Sym("pin") or (isinstance(x[0], Sym) and str(x[0]) == "pin"):
                    name = [y for y in x if isinstance(y, list) and y and str(y[0]) == "name"][0][1]
                    if name in mapping:
                        x[1] = Sym(mapping[name])
                else:
                    walk(x)
    walk(sym["node"])
    part.sym = sym
    return part


def build(D):
    sh = D.sheet("cartridge", "Battery cartridge: 5S protector, FETs, fuse, isolated gauge")
    VSS = "CELL0"

    # ------------------------------------------------------------------ helpers (LCSC parts not in passives.json)
    def Rx(value, n1, n2, lcsc, mpn, pkg="0402", key=None, **f):
        fields = {"LCSC": lcsc, "MPN": mpn, "JLC_Class": f.pop("cls", "Extended")}
        fields.update(f)
        return D.R(sh, value, n1, n2, key=key or f"R_{value}_{pkg}_{mpn}", pkg=pkg, fields=fields)

    def Q(kind, mpn, lcsc, g, d, s, vds, note, cls="Extended"):
        return D.jlc_generic(sh, kind, f"Q_{mpn}", {"G": g, "D": d, "S": s}, prefix="Q", value=mpn, footprint=SOT23,
                             fields={"LCSC": lcsc, "MPN": mpn, "JLC_Class": cls, "Vds_rated": vds, "_drain_net": d,
                                     "Note": note})

    # ------------------------------------------------------------------ net worst-case voltages (vs CELL0)
    for i in range(6):
        D.v(f"CELL{i}", 4.2 * i)
        D.v(f"VC{i}F", 4.2 * i)
    # Main-board-referenced nets ride on PACK_N, which can sit anywhere up to pack voltage when the FETs are open:
    # absolute worst = 21 V + 3.6 V. Parts between them carry V_across = 3.6 V (their real stress).
    for n_, v in [("PACK_P", 21.0), ("GAUGE_LDO_IN", 21.0), ("SNS", 0.1), ("FET_MID", 21.0), ("PACK_N", 21.0),
                  ("CRT_VDDF", 21.0), ("CRT_DSG", 15.0), ("CRT_DSG_G", 15.0), ("CRT_CHG", 21.0), ("CRT_CHG_G", 21.0),
                  ("CRT_LD", 21.0), ("CRT_CTR", 21.0), ("PRES_A", 21.0), ("PRES_B", 21.0), ("PRES_IN", 14.3),
                  ("GAUGE_DIVTOP", 21.0), ("GAUGE_DIVG", 21.0), ("GAUGE_DIVGN", 21.0), ("GAUGE_BAT", 1.0),
                  ("CART_3V3", 24.6), ("CART_SDA", 24.6), ("CART_SCL", 24.6), ("CART_EN", 24.6), ("CART_EN_A", 24.6)]:
        D.v(n_, v)
    for n_ in ("GAUGE_3V3", "ISO_VCC2", "ISO_EN_N", "GAUGE_SDA", "GAUGE_SCL", "GAUGE_TS", "GAUGE_VEN", "GAUGE_REG25",
               "CRT_SRP", "CRT_SRN", "GAUGE_SRP", "GAUGE_SRN", "CRT_AVDD", "CRT_OCDP", "CRT_TS", "CRT_VTB"):
        D.v(n_, 3.6)

    sh.note("X-4 isolation: gauge/protector reference = CELL0. Main board reference = PACK_N (pogo GND + XT60-), which "
            "floats from -21 V to +21 V vs CELL0 when the FETs are open. Nothing on the main side touches CELL0: I2C crosses "
            "ISO1540 U4 (side 1 = main, side 2 = gauge), CART_EN crosses PC817 U5, PRES_A/B is a floating loop.")
    sh.note("X-3 enable: pack FETs stay OFF until the main board drives CART_EN high (3.3 V, >= 2.5 mA, ref. pogo GND). "
            "CART_EN low/open -> opto off -> CTRC/CTRD pulled to VDD via 10M (DISABLED, EC 2.04..VDD+0.7 V) -> CHG+DSG off "
            "within ~8 ms (t_CTRDEG). Main board: detect cartridge by gauge ACK (0x55) through the isolator, read voltage, "
            "keep its own VBAT hot-swap switch OPEN, assert CART_EN, wait >= 20 ms, then ramp (precharge) its hot-swap.")
    sh.note("X-31 pogo targets (cartridge = flat ENIG pads D3.0 mm, pitch >= 4 mm; springs on the main board). Mating order: "
            "1 GND (PACK_N) first-make/last-break; 2 CART_3V3, 3 CART_SDA, 4 CART_SCL, 5 PRES_A, 6 PRES_B mid; "
            "7 CART_EN last-make/first-break. XT60 mates with FETs open (no current path); XT60 must stay mated >= 3 mm "
            "of travel after CART_EN breaks, or the bay latch-release must drop CART_EN first.")

    # ------------------------------------------------------------------ cells: tab landing pads (X-31)
    for name, net in (("B0-", "CELL0"), ("B5+", "CELL5")):
        D.CONN(sh, f"CELL_PWR_{name[:2]}", [name], {name: net}, prefix="BT",
               footprint="Connector_Wire:SolderWirePad_1x01_SMD_5x10mm",
               fields={"_nobom": True, "Op_I": 8.3, "Rated_I": 25.0,
                       "Note": f"pack {name} nickel-strip landing pad 5x10 mm (spot-weld/solder 0.15x8 mm Ni strip); "
                               "copper pour sized for 25 A (3 x 8.3 A)"})
    for i in range(6):
        D.CONN(sh, f"CELL_SENSE_B{i}", [f"B{i}S"], {f"B{i}S": f"CELL{i}"}, prefix="BT",
               footprint="Connector_Wire:SolderWirePad_1x01_SMD_2x4mm",
               fields={"_nobom": True, "Note": f"balance/sense tap B{i} (Kelvin: separate strip from the power tab; "
                                               "carries <= 14 mA balancing)"})

    # ------------------------------------------------------------------ fuse (X-10)
    i_pf = 21.0 / (5 * 0.007 + 0.001)    # A, prospective at full charge, fault ahead of shunt/FETs
    D.jlc_generic(sh, "F", "F_0498030.J", {"1": "CELL5", "2": "PACK_P"}, prefix="F", value="0498030.J 30A 58V 2.5kA",
                  footprint="",
                  fields={"LCSC": "C55118135", "MPN": "0498030.J", "JLC_Class": "Extended", "Op_I": 8.3, "Rated_I": 30.0,
                          "Interrupt_A": 2500, "Prospective_A": round(i_pf),
                          "Note": "X-10: I_pf = 21.0 V / (5 x 7 mOhm cell min + 1 mOhm Ni/Cu min) = 583 A, fault at the fuse "
                                  "load side (bypasses RSNS+FETs). 7 mOhm = 50S AC 10.0-2 mOhm (Samsung) less 15 % for warm "
                                  "cells; DC is 16.3 mOhm typ so this is a floor. Fuse cold R (2.06 mOhm) ignored. "
                                  "3 x 583 = 1750 A <= 2500 A @ 58 VDC (4.3:1). Littelfuse MIDI bolt-in, 41 x 12 mm: "
                                  "footprint = 2x M5 press-fit studs per 0498 drawing (custom, TBD at layout)."})
    D.checks.append(("X-10 fuse interrupt >= 3x prospective fault current", 2500 >= 3 * i_pf))

    # ------------------------------------------------------------------ protector BQ7791500 (X-1, X-9)
    D.IC(sh, "BQ7791500PWR", {
        "VDD": "CRT_VDDF", "AVDD": "CRT_AVDD", "VC5": "VC5F", "VC4": "VC4F", "VC3": "VC3F", "VC2": "VC2F", "VC1": "VC1F",
        "VC0": "VC0F", "VSS": VSS, "SRP": "CRT_SRP", "SRN": "CRT_SRN", "DSG": "CRT_DSG", "CHG": "CRT_CHG", "LD": "CRT_LD",
        "CBI": VSS, "OCDP": "CRT_OCDP", "TS": "CRT_TS", "VTB": "CRT_VTB", "PRES": "PRES_IN",
        "CTRC": "CRT_CTR", "CTRD": "CRT_CTR"},
        nc=["CCFG", "CBO", "LPWR"],
        fields={"Note": "Table 7-1: single device -> LPWR floating, CBO floating; CCFG floating = 5S (Table 9-7); "
                        "CBI to VSS = internal balancing enabled. SRP = CELL0 side, SRN = SNS side (X-1)."})
    # cell inputs: R_IN chosen for balancing current (X-9)
    r_in, rbal_min = 150.0, 8.0
    i_bal = 4.2 / (2 * r_in + rbal_min)
    for i in range(6):
        D.R(sh, "150", f"CELL{i}", f"VC{i}F", key="R_150_0603", pkg="0603",
            fields={"LCSC": "C22808", "MPN": "0603WAF1500T5E", "JLC_Class": "Basic", "V_across": 4.2,
                    "Op_P": round(i_bal ** 2 * r_in, 4),
                    "Note": f"R_IN: I_bal = 4.2/(2x150+R_BAL 8 min) = {i_bal*1000:.1f} mA <= 50 mA abs-max/3; "
                            "1 kOhm (Table 10-1) would give only ~2 mA; 33 Ohm (8.3 R_INI) runs 50 mA = no margin"})
        D.C(sh, "C_470n_50V", f"VC{i}F", VSS, fields={"Note": "C_IN: tau 150 x 0.47u = 70 us (between 8.3 R_INE/C_INE "
                                                               "100 us and R_INI/C_INI 33 us)"})
    D.checks.append(("X-9 balancing current <= 1/3 of 50 mA abs-max", i_bal <= 0.050 / 3 + 1e-4))
    D.R(sh, "1k", "CELL5", "CRT_VDDF", fields={"V_across": 1.0, "Note": "R_VDD 1k (Table 10-1)"})
    D.C(sh, "C_1u_50V", "CRT_VDDF", VSS, fields={"Note": "C_VDD 1u (Table 10-1)"})
    D.C(sh, "C_1u_16V", "CRT_AVDD", VSS, fields={"Note": "AVDD cap 1u (EC V_AVDD test cond.)"})
    Rx("487k", "CRT_OCDP", VSS, "C27010", "0402WGF4873TCE",
       Note="Table 9-3: 487k 1% -> OCD1 350 ms / OCD2 180 ms. -00 has OCD1 = OCD2 = 60 mV (12 A), so 180 ms governs: rides "
            "through hot-swap ramp and PD load steps; FET heating at 24 A for 180 ms is ~0.4 W/FET (negligible).")
    D.R(sh, "10k", "CRT_VTB", "CRT_TS", fields={"Note": "R_TS_PU 10k (Table 10-1)"})
    D.jlc_generic(sh, "NTC", "NTC_10k_0603", {"1": "CRT_TS", "2": VSS}, prefix="TH", value="10k NTC cells (protector)",
                  footprint="Resistor_SMD:R_0603_1608Metric")
    # current sense: SRP on the cell side, SRN on the pack side (X-1)
    D.RSENSE(sh, VSS, "SNS", i_op=8.3)
    D.R(sh, "100", VSS, "CRT_SRP", fields={"V_across": 0.2, "Note": "R_S 100 (Table 10-1). SRP = battery side (Table 7-1)"})
    D.R(sh, "100", "SNS", "CRT_SRN", fields={"V_across": 0.2, "Note": "R_S 100. SRN = pack side. Discharge -> SRP-SRN < 0 (SCD)"})
    D.C(sh, "C_100n_16V", "CRT_SRP", "CRT_SRN", fields={"V_across": 0.2, "Note": "C_S 0.1u (Table 10-1)"})
    # FETs: DSG (source SNS) and CHG (source PACK_N), common drain FET_MID, two in parallel per position
    for _ in range(2):
        D.FET(sh, "NTMFS5C628NLT1G", "CRT_DSG_G", "FET_MID", "SNS", vds=60, id100=100, irms=4.2)
        D.FET(sh, "NTMFS5C628NLT1G", "CRT_CHG_G", "FET_MID", "PACK_N", vds=60, id100=100, irms=4.2)
    D.R(sh, "4.7k", "CRT_DSG", "CRT_DSG_G", fields={"Note": "R_DSG 4.5k (8.3) -> 4.7k E12"})
    D.R(sh, "1M", "CRT_DSG_G", "SNS", fields={"Note": "R_GS_DSG 1M (Table 10-1), at the FETs"})
    D.R(sh, "1M", "CRT_CHG", "CRT_CHG_G", fields={"Note": "R_CHG 1M (8.3: with load-removal UV recovery)"})
    Rx("3.3M", "CRT_CHG_G", "PACK_N", "C270613", "0402WGF3304TCE",
       Note="R_GS_CHG 3.3M (Table 10-1: load removal enabled for UV recovery, -00 = Y in Table 6-1)")
    D.R(sh, "470k", "CRT_LD", "PACK_N", fields={"Note": "R_LD 470k (8.3 Recommended Operating Conditions)"})

    # ------------------------------------------------------------------ CART_EN -> CTRC/CTRD (X-3)
    Rx("10M", "CRT_VDDF", "CRT_CTR", "C26082", "0402WGF1005TCE", cls="Preferred",
       Note="R_CTRx 10M (8.3). Pull-up to VDD = DISABLED (2.04..VDD+0.7 V). Opto dark current 0.1 uA -> 1 V drop, still disabled")
    D.IC(sh, "PC817B_C2936042", {"AN": "CART_EN_A", "CAT": "PACK_N", "COL": "CRT_CTR", "EM": VSS}, prefix="U",
         fields={"Op_I": 0.0021, "Rated_I": 0.05,
                 "Note": "CART_EN opto: I_F = (3.3-1.2)/1k = 2.1 mA; CTR>=50% -> >=1 mA sink vs 2.1 uA needed; "
                         "V_CEO 35 V vs 21 V (1.67x). On -> CTRx < 0.6 V = ENABLED. Fail-safe: dead LED = FETs off."})
    D.R(sh, "1k", "CART_EN", "CART_EN_A", fields={"V_across": 3.6, "Op_P": 0.0045, "Note": "opto LED current limit"})

    # ------------------------------------------------------------------ presence loop (hibernate) + ISO side-2 power gate
    Rx("330k", "CELL5", "PRES_A", "C25778", "0402WGF3303TCE", cls="Preferred", key="R_330k_0402",
       Note="PRES loop top: pogo PRES_A is CELL5 via 330k (<= 64 uA if shorted)")
    D.R(sh, "47k", "PRES_B", "PRES_IN", fields={"Note": "PRES_IN = 21 x 100/477 = 4.4 V docked (>1.75 V V_PRESH max even at "
                                                         "10 V pack); PRES_B shorted to 21 V -> 14.3 V < 16 V (8.3) and < 20 V Vgs"})
    D.R(sh, "100k", "PRES_IN", VSS, fields={"Note": "removed -> PRES_IN low -> HIBERNATE after 4.5 s (no load/fault)"})
    D.C(sh, "C_100n_50V", "PRES_IN", VSS)
    Q("NMOS", "BSS138LT1G", "C82045", "PRES_IN", "ISO_EN_N", VSS, 50,
      "ISO side-2 power gate: on only when docked (PRES loop). Vgs(th) 0.5-1.5 V, Vgs +/-20 V")
    D.R(sh, "100k", "GAUGE_3V3", "ISO_EN_N")
    Q("PMOS", "AO3401A", "C15127", "ISO_EN_N", "ISO_VCC2", "GAUGE_3V3", 30,
      "ISO1540 VCC2 switch: removed cartridge does not pay I_CC2 (1.9-6.7 mA) -> shelf drain = gauge sleep only", cls="Basic")

    # ------------------------------------------------------------------ gauge supply (TLV70433)
    D.JP(sh, "PACK_P", "GAUGE_LDO_IN", i_op=0.008, note="gauge+ISO supply")
    i_ldo = 0.00015 + 0.0067 + 2 * 3.3 / 10e3 + 3.3 / 100e3 + 2.5 / 100e3
    ldo = D.IC(sh, "TLV70433DBVR", {"GND": VSS, "OUT": "GAUGE_3V3", "IN": "GAUGE_LDO_IN"}, nc=["NC"], prefix="U",
         fields={"Op_I": round(i_ldo, 4), "Rated_I": 0.15,
                 "Note": f"Load max {i_ldo*1000:.1f} mA = gauge 0.15 + ISO1540 I_CC2 6.7 (max, lines low) + side-2 pull-ups "
                         f"0.66 + gate/VEN pull-ups 0.06 -> {0.15/i_ldo:.0f}:1. Pd = (21-3.3) x {i_ldo*1000:.1f} mA = "
                         f"{(21-3.3)*i_ldo*1000:.0f} mW. IN 24 V max vs 21 V."})
    _retype(ldo, {"IN": "passive", "GND": "passive", "OUT": "power_out"})
    D.checks.append(("X-4 TLV70433 load <= 1/3 of 150 mA", i_ldo <= 0.05))
    D.C(sh, "C_1u_50V", "GAUGE_LDO_IN", VSS)
    D.C(sh, "C_1u_16V", "GAUGE_3V3", VSS)

    # ------------------------------------------------------------------ gauge BQ34Z100-G1 (X-1, X-5)
    D.IC(sh, "BQ34Z100PWR-G1", {"VEN": "GAUGE_VEN", "BAT": "GAUGE_BAT", "CE": "GAUGE_3V3", "REGIN": "GAUGE_3V3",
                                "REG25": "GAUGE_REG25", "VSS": VSS, "SRP": "GAUGE_SRP", "SRN": "GAUGE_SRN",
                                "P6/TS": "GAUGE_TS", "P4/SCL": "GAUGE_SCL", "P3/SDA": "GAUGE_SDA",
                                "P1": VSS, "P2": VSS, "P5/HDQ": VSS},
         fields={"Note": "0x55. Stores Qmax/cycle count = cartridge health record. Table 5-1: P1/P2 unused -> VSS, HDQ -> VSS. "
                         "SRP = CELL0 side, SRN = SNS side (X-1). Set VOLTSEL=1, Voltage Divider cal."})
    D.C(sh, "C_100n_16V", "GAUGE_3V3", VSS, fields={"Note": "REGIN 0.1u at pin (Table 5-1)"})
    D.C(sh, "C_1u_16V", "GAUGE_REG25", VSS)
    D.R(sh, "100", VSS, "GAUGE_SRP", fields={"V_across": 0.2, "Note": "SRP nearest BAT- (Table 5-1)"})
    D.R(sh, "100", "SNS", "GAUGE_SRN", fields={"V_across": 0.2, "Note": "SRN nearest PACK- (Table 5-1)"})
    D.C(sh, "C_100n_16V", "GAUGE_SRP", "GAUGE_SRN", fields={"V_across": 0.2})
    D.jlc_generic(sh, "NTC", "NTC_10k_0603", {"1": "GAUGE_TS", "2": VSS}, prefix="TH", value="10k NTC cells (gauge)",
                  footprint="Resistor_SMD:R_0603_1608Metric")
    # High-side switched divider (X-5): P-FET on top, N-FET from VEN; bottom leg permanently to CELL0.
    r_top, r_bot, v_top = 220e3, 10e3, 21.0
    v_bat = v_top * r_bot / (r_top + r_bot)
    D.R(sh, "100k", "GAUGE_REG25", "GAUGE_VEN", fields={"Note": "VEN pull-up (VEN listed open-drain, 6.1); reset/Hi-Z -> "
                                                                "divider ON = 0.913 V, still safe"})
    Q("NMOS", "BSS138LT1G", "C82045", "GAUGE_VEN", "GAUGE_DIVGN", VSS, 50,
      "VEN level shifter: Vgs 2.0-2.5 V vs Vth 1.5 V max; drain sees PACK_P 21 V when off (50 V part)")
    D.R(sh, "100k", "GAUGE_DIVG", "GAUGE_DIVGN", fields={"Note": "limits P-FET Vgs to -21x100/200 = -10.5 V (+/-20 V)"})
    D.R(sh, "100k", "PACK_P", "GAUGE_DIVG", fields={"Note": "P-FET gate pull-up: off unless VEN high"})
    Q("PMOS", "LBSS84LT1G", "C8492", "GAUGE_DIVG", "GAUGE_DIVTOP", "PACK_P", 50,
      "divider top switch (TI multicell high-side switched divider); Vds 50 V vs 21 V", cls="Preferred")
    Rx("220k", "GAUGE_DIVTOP", "GAUGE_BAT", "C278545", "ERA3AEB224V", pkg="0603",
       Note=f"0.1 % 25 ppm. X-5 proof: divider ON -> BAT = 21 x 10/230 = {v_bat:.3f} V; OFF -> BAT pulled to 0 V by the "
            "permanent 10k (P-FET leakage <= 1 uA -> <= 10 mV); P-FET shorted -> 0.913 V; gauge unpowered (REG25 = 0) -> "
            "OFF. Only a double fault (10k open AND P-FET on) reaches PACK_P via 220k (<= 95 uA).")
    Rx("10k", "GAUGE_BAT", VSS, "C95204", "RT0603BRD0710KL", pkg="0603",
       Note="0.1 % 25 ppm bottom leg, permanently to CELL0 (never switched)")
    D.C(sh, "C_100n_16V", "GAUGE_BAT", VSS)
    D.checks.append(("X-5 gauge BAT <= 5.5 V abs-max with divider on at 21 V", v_bat <= 5.5))

    # ------------------------------------------------------------------ I2C isolator ISO1540 (X-4)
    iso = D.IC(sh, "ISO1540DR", {"VCC1": "CART_3V3", "GND1": "PACK_N", "SDA1": "CART_SDA", "SCL1": "CART_SCL",
                           "VCC2": "ISO_VCC2", "GND2": VSS, "SDA2": "GAUGE_SDA", "SCL2": "GAUGE_SCL"}, prefix="U",
         fields={"Note": "Side 1 = main board (via pogo, ref PACK_N): V_OL1 0.57-0.8 V needs a master with V_IL >= 0.8 V "
                         "(TCA9548A 0.99 V); side-1 bus <= 40 pF, I_OL1 0.5-3.5 mA (ISO1540 6.3). Side 2 = gauge "
                         "(ref CELL0, V_OL2 <= 0.4 V vs gauge V_IL 0.6 V). 2.5 kVrms barrier vs 42 V worst offset."})
    _retype(iso, {**{p: "passive" for p in ("VCC1", "VCC2", "GND1", "GND2")},
                  **{p: "bidirectional" for p in ("SDA1", "SCL1", "SDA2", "SCL2")}})
    D.C(sh, "C_100n_16V", "CART_3V3", "PACK_N", fields={"V_across": 3.6, "Note": "VCC1 decoupling, main-side reference"})
    D.C(sh, "C_100n_16V", "ISO_VCC2", VSS)
    for n_ in ("CART_SDA", "CART_SCL"):
        D.R(sh, "2.2k", "CART_3V3", n_, fields={"V_across": 3.6, "Note": "side-1 pull-up: 3.6/2.2k = 1.6 mA (0.5-3.5 mA); "
                                                                    "main-board pull-ups on this branch must be >= 4.7k"})
    for n_ in ("GAUGE_SDA", "GAUGE_SCL"):
        D.R(sh, "10k", "ISO_VCC2", n_, fields={"Note": "side-2 / gauge pull-up 10k (BQ34Z100 Table 5-1) on the SWITCHED "
                                                       "rail: ISO1540 I/O abs-max VCC2+0.5 V when unpowered"})

    # ------------------------------------------------------------------ pack connector + pogo targets (X-31)
    D.IC(sh, "XT60PW-F_C428722", {"+": "PACK_P", "-": "PACK_N"}, nc=["1", "2"], prefix="J", value="XT60 female",
         fields={"Op_I": 8.3, "Rated_I": 30.0, "Note": "Mates with FETs open: PACK_N isolated until CART_EN"})
    pogo = [("1", "GND", "PACK_N", "FIRST make / last break (mates with BWCD-L6.0W2.0H2.0 C2826551 on the main board)"),
            ("2", "CART_3V3", "CART_3V3", "mid (BWCD-L5.5W2.0H3.0 C2826550); ISO side-1 supply <= 7.1 mA + pull-ups"),
            ("3", "CART_SDA", "CART_SDA", "mid (C2826550)"),
            ("4", "CART_SCL", "CART_SCL", "mid (C2826550)"),
            ("5", "PRES_A", "PRES_A", "mid (C2826550); CELL5 via 330k, shorted to PRES_B on the main board"),
            ("6", "PRES_B", "PRES_B", "mid (C2826550); returns to PRES_IN"),
            ("7", "CART_EN", "CART_EN", "LAST make / first break (BWCD-L5.0W2.0H2.5 C2826549); opto LED anode via 1k")]
    for num, name, net, note in pogo:
        D.CONN(sh, f"POGO{num}_{name}", [name], {name: net}, prefix="P", footprint="TestPoint:TestPoint_Pad_D3.0mm",
               fields={"_nobom": True, "Note": f"Pogo target {num}/7: flat ENIG pad D3.0 mm, pitch >= 4 mm. {note}"})

    # ------------------------------------------------------------------ test points
    for t in ("PACK_P", "PACK_N", "CELL5", "CELL0", "CRT_DSG", "CRT_CHG", "SNS", "CRT_CTR", "PRES_IN", "GAUGE_3V3",
              "ISO_VCC2", "GAUGE_BAT"):
        D.TP(sh, t)
    for t in ("GAUGE_SDA", "GAUGE_SCL"):
        D.TP(sh, t, small=True)
    return sh
