"""Auxiliary inputs: DC barrel jack (solar/adapter) + PoE (isolated VPOE), ORed into one forward-only
BQ25756 stage that charges the bus. USB-C inputs use each port's own bidirectional stage.

DC jack path: J -> 4 A fuse -> SMBJ33CA (bidirectional, P-6/X-7) -> TPS26631 eFuse (back-to-back blocking FET,
               OV 27.1 V / UV 10.4 V, I_LIM 1.65 A = 3:1 on the 5 A jack) -> LM74700 ideal diode -> VIN_AUX
PoE path:     VPOE (isolated 20 V, see poe.py) -> LM74700 ideal diode -> VIN_AUX

TPS2663 datasheet (SLVSE94G) values used here:
  V(UVLOR) = V(OVPR) = 1.176 / 1.2 / 1.224 V; V(OVPF) 1.122 V. OVP turn-off delay 8.5-14 us.
  I_OL = 18/R_ILIM[kOhm] (30k = 0.6 A, 9k = 2.0 A +-8 %); IMON gain 27.9 uA/A; ~SHDN open-circuit 2.48-3.3 V,
  V(SHUTR) 2 V, I(SHDN) at 0 V <= 10 uA; MODE = GND -> auto-retry; "Leave B_GATE / DRV floating if no blocking FET,
  short IN_SYS to IN"; IMON / PGOOD may float; IN, IN_SYS, OUT >= 0.1 uF.
  Abs max: DRV - IN_SYS 20 V (-> 2N7002, Vgs +-20 V, P-41); SHDN / OVP / ILIM 5.5 V; IN, OUT 67 V.

OV/UV re-derivation (P-15 / X-22): adapter window 24 V + 5 % = 25.2 V must pass at the LOW corner; DC-out VAC_REV
  24 V +2 % = 24.5 V must pass its own eFuse. 200k / 16.2k / 10k:
    OV = 1.2 x 226.2/10 = 27.1 V nominal, 26.4 V low corner (1.176 V, -0.7 % ratio), 27.9 V high corner.
    UV = 1.2 x 226.2/26.2 = 10.4 V.
  Consequences: every net behind the DC-in eFuse (DCI_OUT, VIN_AUX, INS_*) is rated 27.9 V worst case
  -> MLCC >= 55.8 V (100 V parts), polymer >= 34.9 V (50 V parts), FETs >= 41.9 V (60 V parts).
  DCI_RAW / DCI_INSYS: 33 V = TVS standoff (largest voltage the input survives continuously) -> 100 V MLCC.
"""

POLY = "MA50V47M6X9"   # C54321575: 47 uF 50 V aluminium polymer, 30 mOhm, 2.6 A ripple @100 kHz (pin 1 = +)


def polymer(D, sh, net, vmax, note=""):
    """47 uF / 50 V polymer bulk cap (design-rules 1.3: polymer >= 1.25 x net max)."""
    D.IC(sh, POLY, {"1": net, "2": "GND"}, prefix="C", value="47uF 50V polymer",
         fields={"Rated_V": 50.0, "Note": f"pin 1 = + (silk '+'). {note}".strip()})
    D.checks.append((f"polymer on {net}: 50 V >= 1.25 x {vmax} V", 50.0 >= 1.25 * vmax - 1e-6))


def logic_fet(D, sh, gate, drain, pulldown="100k", note=""):
    """2N7002 (60 V, Vgs +-20 V) open-drain pull-down, gate held low by default."""
    D.IC(sh, "2N7002", {"G": gate, "D": drain, "S": "GND"}, prefix="Q", fields={"Note": note} if note else None)
    D.R(sh, pulldown, gate, "GND", fields={"Note": "default: FET off"})


def ideal_diode(D, sh, anode, cathode, tag, en=None, vmax=28.0):
    """LM74700 + N-FET ideal diode (ORing).

    en: None -> EN tied to ANODE (always on). Otherwise the name of an active-high DISABLE net from the expander:
        EN is pulled to ANODE by 100k (EN abs max 65 V, DS 6.1) and a 2N7002 pulls it low when the net is high.
        Default (expander hi-Z, gate pull-down) = enabled. Disabled only turns the FET off: the body diode still
        conducts forward, so this selects the drop, not the source (use the eFuse SHDN to disconnect DC-in).
    """
    g, vcap = f"{tag}_GATE", f"{tag}_VCAP"
    en_pin = anode
    if en:
        en_pin = D.v(f"{tag}_EN", vmax)
        D.R(sh, "100k", anode, en_pin, fields={"V_across": vmax, "Note": "EN default on (pulled to ANODE)"})
        logic_fet(D, sh, en, en_pin, note=f"{en} high = ORing FET off (body diode still conducts)")
    D.IC(sh, "LM74700QDBVRQ1", {"VCAP": vcap, "GND": "GND", "EN": en_pin, "CATHODE": cathode, "GATE": g, "ANODE": anode},
         fields={"Note": "ideal-diode ORing (reverse-current blocking). GATE/VCAP - ANODE abs max 15 V"})
    D.C(sh, "C_100n_50V", vcap, anode, fields={"V_across": 15.0, "Note": "VCAP charge-pump cap 0.1 uF (LM74700 DS test condition C(VCAP) = 0.1 uF)"})
    D.FET(sh, "NTMFS5C628NLT1G", g, cathode, anode, vds=60, id100=100, irms=2.5)
    D.v(g, vmax + 15.0)
    D.v(vcap, vmax + 15.0)


def efuse(D, sh, vin_raw, vout, tag, ilim_r="11k", note="", ov_div=("200k", "16.2k", "10k"), shdn="pullup",
          vin_max=33.0, vout_max=27.9, pgth=("100k", "13k"), blocking=True, jp=True, i_op=1.65, rated_note=None,
          imon=True):
    """TPS26631 eFuse, auto-retry. Defaults: OV 27.1 V / UV 10.4 V (see module docstring), PGOOD at 10.4 V.

    shdn: "pullup" -> ~SHDN = {tag}_EN with 100k to V3V3 (an expander may drive {tag}_EN directly);
          "open"   -> ~SHDN not connected (internal 2.7 V open-circuit = enabled, works with V3V3 dead);
          any other string -> name of an active-high DISABLE gate net driving a 2N7002 on ~SHDN (P-14: enabled with
          V3V3 dead, firmware can still shut it down).
    blocking: True -> external back-to-back blocking FET (reverse polarity), False -> IN_SYS shorted to IN.
    jp: solder-jumper feed from vin_raw (C-42 / design-rules 2.2).
    """
    ins = f"{tag}_INSYS"
    vin = f"{tag}_IN" if blocking else ins
    en = f"{tag}_EN"
    conns = {"IN": vin, "IN_SYS": ins, "UVLO": f"{tag}_UV", "OVP": f"{tag}_OV", "GND": "GND", "dVdT": f"{tag}_DVDT",
             "ILIM": f"{tag}_ILIM", "MODE": "GND", "~{FLT}": f"{tag}_FLT", "PGTH": f"{tag}_PGTH", "PGOOD": f"{tag}_PG",
             "OUT": vout, "EP": "GND"}
    nc = ["N.C"]
    if blocking:
        conns.update({"B_GATE": f"{tag}_BG", "DRV": f"{tag}_DRV"})
    else:
        nc += ["B_GATE", "DRV"]
    if shdn == "open":
        nc.append("~{SHDN}")
    else:
        conns["~{SHDN}"] = en
    if imon:
        conns["IMON"] = f"{tag}_IMON"
    else:
        nc.append("IMON")
    r1, r2, r3 = ov_div
    kv = lambda s: float(s.rstrip("k")) * (1000.0 if s.endswith("k") else 1.0)  # noqa: E731
    t = kv(r1) + kv(r2) + kv(r3)
    ov, uv = 1.2 * t / kv(r3), 1.2 * t / (kv(r2) + kv(r3))
    ilim = 18.0 / (kv(ilim_r) / 1000.0)
    D.IC(sh, "TPS26631RGER", conns, nc=nc,
         fields={"Op_I": i_op, "Rated_I": 6.0,
                 "Note": f"I_LIM {ilim_r} = {ilim:.2f} A nominal (18/R, +-8 %). OV {ov:.1f} V / UV {uv:.1f} V. "
                         f"MODE=GND auto-retry. {rated_note or ''} {note}".strip()})
    for n_, v in [(vin, vin_max), (ins, vin_max), (vout, vout_max), (f"{tag}_UV", 3.6), (f"{tag}_OV", 3.6), (f"{tag}_PGTH", 3.6),
                  (f"{tag}_DVDT", 5.5), (f"{tag}_ILIM", 5.5), (f"{tag}_IMON", 5.5), (en, 3.6), (f"{tag}_FLT", 3.6), (f"{tag}_PG", 3.6)]:
        D.v(n_, v)
    if jp:
        D.JP(sh, vin_raw, ins, i_op=i_op, note=f"{tag} isolate")
    if blocking:
        D.v(f"{tag}_BG", vin_max + 14.0)
        D.v(f"{tag}_DRV", vin_max + 20.0)
        # back-to-back blocking FET: S -> IN_SYS (connector side), D -> IN
        D.FET(sh, "NTMFS5C628NLT1G", f"{tag}_BG", vin, ins, vds=60, id100=100, irms=i_op * 1.08)
        D.IC(sh, "2N7002", {"D": f"{tag}_BG", "G": f"{tag}_DRV", "S": ins}, prefix="Q",
             fields={"Note": "B_GATE fast pulldown (TPS2663 Fig 8-7). 2N7002 Vgs +-20 V >= DRV-IN_SYS abs max 20 V (P-41)"})
    D.R(sh, r1, ins, f"{tag}_UV", fields={"V_across": vin_max})
    D.R(sh, r2, f"{tag}_UV", f"{tag}_OV")
    D.R(sh, r3, f"{tag}_OV", "GND", fields={"Note": f"UV {uv:.2f} V / OV {ov:.2f} V nominal (1.2 V thresholds, 1.176-1.224 V)"})
    D.R(sh, ilim_r, f"{tag}_ILIM", "GND")
    D.C(sh, "C_22n_50V", f"{tag}_DVDT", "GND", fields={"Note": "inrush slew (>= 10 nF)"})
    if imon:
        D.R(sh, "30.1k", f"{tag}_IMON", "GND",
            fields={"Note": "P-35: 27.9 uA/A x 30.1k = 0.84 V/A (1.39 V at 1.65 A, 2.8 V at the 2x pulse; < 4 V). Route to an ADC (VERIFY channel)"})
        D.TP(sh, f"{tag}_IMON", small=True)
    D.R(sh, "10k", f"{tag}_FLT", "V3V3")
    D.R(sh, "10k", f"{tag}_PG", "V3V3")
    pt, pb = pgth
    pg_v = 1.2 * (kv(pt) + kv(pb)) / kv(pb)
    D.R(sh, pt, vout, f"{tag}_PGTH", fields={"V_across": vout_max})
    D.R(sh, pb, f"{tag}_PGTH", "GND", fields={"Note": f"P-34: PGOOD at OUT >= {pg_v:.1f} V (PGTH 1.2 V)"})
    if shdn == "pullup":
        D.R(sh, "100k", en, "V3V3", fields={"Note": "enabled by default; expander can pull SHDN low"})
    elif shdn != "open":
        logic_fet(D, sh, shdn, en, pulldown="100k",
                  note=f"P-14: {shdn} high = eFuse off. SHDN otherwise floats to its internal 2.7 V -> enabled with V3V3 dead")
    D.C(sh, "C_1u_100V" if 2 * vin_max > 50 else "C_1u_50V", ins, "GND")
    D.C(sh, "C_1u_100V" if 2 * vout_max > 50 else "C_1u_50V", vout, "GND")
    D.TP(sh, f"{tag}_FLT", small=True)
    D.TP(sh, f"{tag}_PG", small=True)


def bq_stage(D, sh, tag, vac, ch, ichg_r, ilim_r, ce_net, note, irms, vmax=24.3, ilim_sw=(), bulk=True, bus_jp=True):
    """BQ25756 stage between vac and VBAT (forward or reverse).

    ilim_sw: [(R, gate_net), ...] extra ILIM_HIZ resistors switched in parallel by logic N-FETs (100k gate pull-downs,
             so the hardware default is the base ilim_r). K_ILIM = 20 A*kOhm at 5 mOhm (50 A*kOhm at 2 mOhm, DS).
    bulk: P-9 - BQ25756 DS 5.3 needs >= 80 uF effective on each side: 2x 47 uF polymer (75 uF at -20 %) + the MLCCs.
    bus_jp: design-rules 2.2 isolation link between the stage's battery-side sense node and VBAT.
    """
    n = lambda s: f"{tag}_{s}"  # noqa: E731
    VIN, VOUT, SW1, SW2 = n("VIN"), n("VOUT"), n("SW1"), n("SW2")
    BAT = n("BAT") if bus_jp else "VBAT"
    for net, v in [(VIN, vmax), (vac, vmax), (VOUT, 21.0), (SW1, vmax), (SW2, 21.0)]:
        D.v(net, v)
    if bus_jp:
        D.v(BAT, 21.0)
    for s in ("REGN", "TS", "ICHG", "ILIM", "FB", "FBG", "FSW", "PGLED", "PGLEDK", "PG", "STAT1", "STAT2"):
        D.v(n(s), 5.5)
    D.IC(sh, "BQ25756RRVR", {
        "SCL": f"I2C{ch}_SCL", "SDA": f"I2C{ch}_SDA", "~{INT}": "CHG_INT_N", "STAT1": n("STAT1"), "STAT2": n("STAT2"),
        "~{PG}": n("PG"), "~{CE}": ce_net, "TS": n("TS"), "ICHG": n("ICHG"), "ILIM_HIZ": n("ILIM"), "FBG": n("FBG"),
        "FB": n("FB"), "SRN": BAT, "SRP": VOUT, "PGND": "GND", "SW2": SW2, "HIDRV2": n("HD2"), "BTST2": n("BT2"),
        "LODRV2": n("LD2"), "DRV_SUP": n("REGN"), "REGN": n("REGN"), "LODRV1": n("LD1"), "BTST1": n("BT1"),
        "HIDRV1": n("HD1"), "SW1": SW1, "ACN": VIN, "ACP": vac, "VAC": vac, "ACUV": vac, "ACOV": "GND", "FSW_SYNC": n("FSW")},
        nc=["NC"], fields={"Note": f"I2C 0x6B on mux channel {ch}. {note}"})
    for g, d, s, gn in [(n("HD1g"), VIN, SW1, n("HD1")), (n("LD1g"), SW1, "GND", n("LD1")),
                        (n("HD2g"), VOUT, SW2, n("HD2")), (n("LD2g"), SW2, "GND", n("LD2"))]:
        D.FET(sh, "NTMFS5C628NLT1G", g, d, s, vds=60, id100=100, irms=irms)
        D.R(sh, "0", gn, g)
    D.L(sh, "TMPA1707SP-6R8MN-D", SW1, SW2, rated_i=22, isat=25, irms=irms, ipk=irms + 1.6, value="6.8uH 22A")
    D.RSENSE(sh, vac, VIN, i_op=2.7)
    D.RSENSE(sh, VOUT, BAT, i_op=irms)
    hv = 2 * vmax > 50   # VIN-side MLCC must be >= 2 x vmax (design-rules 1.3)
    D.C(sh, "C_100n_16V", n("BT1"), SW1, fields={"V_across": 5.5})
    D.C(sh, "C_100n_16V", n("BT2"), SW2, fields={"V_across": 5.5})
    D.C(sh, "C_4u7_16V", n("REGN"), "GND")
    D.C(sh, "C_4u7_16V", n("REGN"), "GND")
    D.C(sh, "C_470n_50V", vac, VIN, fields={"V_across": 1.0})
    D.C(sh, "C_100n_100V" if hv else "C_100n_50V", vac, "GND")
    D.C(sh, "C_470n_100V" if hv else "C_470n_50V", VIN, "GND")
    D.C(sh, "C_470n_50V", VOUT, BAT, fields={"V_across": 1.0})
    D.C(sh, "C_100n_50V", VOUT, "GND")
    for _ in range(3):
        D.C(sh, "C_4u7_100V" if hv else "C_10u_50V", VIN, "GND")
    for _ in range(3):
        D.C(sh, "C_10u_50V", VOUT, "GND")
    if bulk:
        for _ in range(2):
            polymer(D, sh, VIN, vmax, note="P-9 input bulk (BQ25756 DS 5.3: C_IN >= 80 uF effective)")
        for _ in range(2):
            polymer(D, sh, VOUT, 21.0, note="P-9 output bulk (BQ25756 DS 5.3: C_OUT >= 80 uF effective)")
        # effective-capacitance budget: polymer at -20 % tolerance, MLCC derated (X7R 100 V 1210 ~60 % at <= 28 V,
        # X5R 50 V 1206 ~35 % at 21 V; VERIFY against the vendor DC-bias curves)
        c_in = 2 * 47 * 0.8 + 3 * (4.7 * 0.6 if hv else 10 * 0.35)
        c_out = 2 * 47 * 0.8 + 3 * 10 * 0.35
        D.checks.append((f"{tag}: BQ25756 C_IN effective {c_in:.0f} uF >= 80 uF", c_in >= 80))
        D.checks.append((f"{tag}: BQ25756 C_OUT effective {c_out:.0f} uF >= 80 uF", c_out >= 80))
    D.R(sh, "249k", BAT, n("FB"), fields={"Note": "P-12: should be 0.1 % / 25 ppm thin film (passives key needed)"})
    D.R(sh, "20k", n("FB"), n("FBG"), fields={"Note": "20.66 V bus regulation. P-12: 0.1 % thin film needed"})
    D.R(sh, ichg_r, n("ICHG"), "GND")
    D.R(sh, ilim_r, n("ILIM"), "GND")
    for r, gate in ilim_sw:
        D.R(sh, r, n("ILIM"), f"{n('ILIM')}_{gate}")
        D.v(f"{n('ILIM')}_{gate}", 5.5)
        D.IC(sh, "AO3400A", {"D": f"{n('ILIM')}_{gate}", "G": gate, "S": "GND"}, prefix="Q",
             fields={"Note": f"ILIM step: {gate} high adds {r} in parallel"})
        D.R(sh, "100k", gate, "GND", fields={"Note": "default off: base ILIM only"})
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
    if bus_jp:
        D.JP(sh, BAT, "VBAT", i_op=irms, note=f"{tag} bus isolate")
        D.TP(sh, BAT)


# INS input-current hardware ceiling (P-16 / P-17): K_ILIM 20 A*kOhm.
#   base 20k            -> 1.00 A (hardware default, dead-battery case; ~20 W, safe on an 802.3at Type 2 PSE)
#   + 47k  (ILIM_A)     -> 14.0k -> 1.43 A (DC jack: below the 1.65 A eFuse, 34 W at 24 V)
#   + 30.1k (ILIM_B)    -> 12.0k -> 1.66 A (B alone: not a firmware state)
#   + both              -> 9.57k -> 2.09 A (PoE Class 6 only: 42 W at 20.3 V < 46 W flyback)
# The worst combination of the two switches is 2.09 A, so no firmware state exceeds the PoE class-6 budget.
INS_ILIM = [("47k", "EXP_INS_ILIM_A"), ("30.1k", "EXP_INS_ILIM_B")]


def build(D):
    sh = D.sheet("power_input", "Aux inputs: DC jack (solar/adapter) + PoE, ORed into a forward-only charger stage")
    sh.note("DC jack limited to 1.65 A by the eFuse (3:1 on the 5 A jack rating) -> 40 W at 24 V.")
    sh.note("eFuse OV 27.1 V nominal (26.4-27.9 V): passes a 24 V +5 % adapter at the low corner (X-22/P-15). Nets behind it rated 27.9 V.")
    sh.note("Dead battery (P-14): DC-in eFuse ~SHDN floats to its internal 2.7 V (enabled); EXP_DCI_DIS high (2N7002) shuts it down.")
    sh.note("INS ILIM: 1.00 A default; EXP_INS_ILIM_A -> 1.43 A (DC jack); A+B -> 2.09 A (PoE Class 6 only, after TPH/TPL read). Max any state 2.09 A.")
    sh.note("Firmware (P-11): pass-through -> EN_CHG_TMR=0, EN_TERM=0, VFB_REG for 4.04 V/cell float. Default mode keeps the 12 h timer "
            "(half rate in IAC_DPM); after expiry recover by toggling ~CE (EXP_INS_CHG_DIS) or EN_CHG (BQ25756 DS 6.3.x safety timer).")
    sh.note("Firmware must keep EN_ILIM_HIZ_PIN = 1 and EN_ICHG_PIN = 1 (BQ25756 DS: the pins can be disabled by register).")
    D.IC(sh, "DC-005-5A-2.0", {"1": "DCI_JACK", "2": "GND", "3": "GND"}, prefix="J", value="DC IN 2.0mm",
         fields={"Op_I": 1.65, "Rated_I": 5.0, "Note": "pin1 centre (+). VERIFY pin map on footprint"})
    D.v("DCI_JACK", 33.0)
    D.v("DCI_RAW", 33.0)
    D.IC(sh, "1206T4A63V", {"1": "DCI_JACK", "2": "DCI_RAW"}, prefix="F", value="4A 63V 1206",
         fields={"Note": "X-7: input fuse ahead of the TVS: opens on a sustained over-voltage source into the clamp. "
                         "4 A > 1.78 A max eFuse limit; 2x pulse (3.6 A) only for t_CB. 50 A interrupt @63 V (adapter-limited fault). "
                         "VERIFY I2t vs the eFuse 2x pulse and the cold-plug inrush."})
    D.IC(sh, "SMBJ33CA-C78420", {"1": "DCI_RAW", "2": "GND"}, prefix="D", value="SMBJ33CA",
         fields={"Note": "P-6/X-7: BIDIRECTIONAL TVS: a reversed adapter (down to -33 V) sees no conduction; the eFuse blocking FET "
                         "handles reverse polarity. Standoff 33 V > 27.9 V OV max; clamp 53.3 V < 67 V IN_SYS/IN abs max."})
    D.C(sh, "C_1u_100V", "DCI_RAW", "GND")
    # eFuse: IN_SYS is the connector side when a blocking FET is used (JP DCI_RAW -> DCI_INSYS inside efuse())
    efuse(D, sh, "DCI_RAW", "DCI_OUT", "DCI", shdn="EXP_DCI_DIS")
    ideal_diode(D, sh, "DCI_OUT", "VIN_AUX", "DCI_ORING", en="EXP_ORING_DC_DIS", vmax=27.9)
    ideal_diode(D, sh, "VPOE", "VIN_AUX", "POE_ORING", en="EXP_ORING_POE_DIS", vmax=22.0)
    D.v("VIN_AUX", 27.9)
    D.C(sh, "C_4u7_100V", "VIN_AUX", "GND")
    D.C(sh, "C_4u7_100V", "VIN_AUX", "GND")
    D.TP(sh, "VIN_AUX")
    D.TP(sh, "DCI_OUT")
    # forward-only charger stage
    bq_stage(D, sh, "INS", "VIN_AUX", 4, ichg_r="15k", ilim_r="20k", ce_net="INS_CE", vmax=27.9, ilim_sw=INS_ILIM,
             note="Forward only (EN_REV never set). ICHG 50/15k = 3.33 A. ILIM 20/20k = 1.00 A default, 2.09 A max (switched).",
             irms=3.4)
    # ~CE: 10k pull-down (charging enabled by default, dead-battery start) + diode-OR disable inputs.
    # CE V_IH 1.3 V / V_IL 0.4 V (BQ25756 DS): 3.3 V - 0.4 V Schottky = 2.9 V > 1.3 V.
    D.v("INS_CE", 3.6)
    D.R(sh, "10k", "INS_CE", "GND")
    D.IC(sh, "BAT54C,215", {"1": "EXP_INS_CHG_DIS", "2": "CHG_INHIBIT", "3": "INS_CE"}, prefix="D", value="BAT54C",
         fields={"Note": "~CE OR: EXP_INS_CHG_DIS (firmware stop / safety-timer reset by CE toggle) and CHG_INHIBIT "
                         "(system pack-current limiter, P-10). Either high -> charging off."})
    D.R(sh, "100k", "EXP_INS_CHG_DIS", "GND")
    D.TP(sh, "INS_CE", small=True)
    D.TP(sh, "CHG_INHIBIT", small=True)
    return sh
