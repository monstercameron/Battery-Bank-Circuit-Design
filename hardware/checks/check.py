"""Design checks run on every build (see docs/design-rules.md).

1. Voltage derating:   MLCC rating >= 2x worst-case net voltage; resistor package working voltage
                       >= worst-case voltage across it; discretes per their Rated_V field (1.5x).
2. 3:1 current/power:  any part with Op_P/Op_I/Op_Irms fields must have Rated_* >= 3x Op.
3. Netlist sanity:     every net has >= 2 pins; every non-NC pin is connected; no net is unnamed;
                       every net has a known worst-case voltage.
4. BOM sanity:         every BOM part has an LCSC number; stock >= 5x build quantity.
Returns a list of findings; exits non-zero if any are ERRORs.
"""
import sys

BUILD_QTY = 5

# IC pin absolute-maximum voltages (V), from the datasheets in docs/datasheets (C-19).
# Key = LCSC symbol name; value = {pin name: abs-max}. Checked against each net's worst-case voltage.
PIN_ABS_MAX = {
    # TPS62933 DS 6.1: EN 6 V; VIN 32 V
    "TPS62933PDRLR": {"EN": 6.0, "VIN": 32.0, "FB": 6.0, "PG": 6.0},
    "TPS62933FDRLR": {"EN": 6.0, "VIN": 32.0, "FB": 6.0},
    "TPS62933DRLR": {"EN": 6.0, "VIN": 32.0, "FB": 6.0},
    # TPS26750 DS 5.1
    "TPS26750SRSMR_C42166327": {"PP5V": 6.0, "VIN_3V3": 4.0, "ADCIN1": 4.0, "ADCIN2": 4.0, "VBUS": 28.0, "CC1": 26.0, "CC2": 26.0,
                                "I2Cc_SDA": 4.0, "I2Cc_SCL": 4.0, "I2Ct_SDA": 4.0, "I2Ct_SCL": 4.0, "GPIO0": 6.0, "GPIO1": 6.0, "GPIO2": 6.0},
    # TPD4S480 DS 6.1
    "TPD4S480RUKR_C43131250": {"VPWR": 5.0, "EPR_EN": 6.0, "VBUS_LV": 24.0, "CC1": 6.0, "CC2": 6.0, "SBU1": 6.0, "SBU2": 6.0,
                               "C_CC1": 63.0, "C_CC2": 63.0, "C_SBU1": 63.0, "C_SBU2": 63.0, "VBUS": 63.0, "VBIAS": 63.0},
    # BQ25756 DS: VAC 85 V abs-max (operating 70 V)
    "BQ25756RRVR": {"VAC": 85.0},
    # TPS2663 DS 6.1: OVP/dVdT/IMON/MODE/ILIM 5.5 V, SHDN 5 V (expected 0-5 operating), IN 67 V
    "TPS26631RGER": {"OVP": 5.5, "dVdT": 5.5, "IMON": 5.5, "MODE": 5.5, "ILIM": 5.5, "IN": 67.0, "IN_SYS": 67.0, "OUT": 67.0},
    "TPS26631PWPR": {"OVP": 5.5, "dVdT": 5.5, "IMON": 5.5, "MODE": 5.5, "ILIM": 5.5, "IN": 67.0, "IN_SYS": 67.0, "OUT": 67.0},
    # AL8860Q DS: CTRL 6 V, VIN 42 V
    "AL8860QMP-13": {"CTRL": 6.0, "VIN": 42.0},
    # HD3SS3212 DS 7.1: VCC 4 V
    "HD3SS3212IRKSR": {"VCC": 4.0},
    # TPS2373 DS: VDD/RTN 100 V, VC_IN 25 V, APD/UVLO_SEL 6.5 V
    "TPS2373-4RGWR": {"VDD": 100.0, "VC_IN": 25.0},
    # LM5155 DS: BIAS 45 V
    "LM5155DSSR": {"BIAS": 45.0},
}


def _vmax(design, net):
    if net is None:
        return 0.0
    if net in design.net_v:
        return design.net_v[net]
    for prefix, v in design.net_v_prefix:
        if net.startswith(prefix):
            return v
    return None


def _ohms(value):
    """'4.7k' -> 4700, '1M' -> 1e6, '5m 1% 3W' -> 0.005, '2R2' -> 2.2; None if unparseable or 0 (jumper)."""
    import re
    s = str(value).strip().split()[0] if str(value).strip() else ""
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([RrkKMm]?)(\d*)", s)
    if not m:
        return None
    num, unit, frac = m.groups()
    v = float(num + ("." + frac if frac else ""))
    v *= {"": 1, "R": 1, "r": 1, "k": 1e3, "K": 1e3, "M": 1e6, "m": 1e-3}[unit]
    return v or None


def stock_check(design, add):
    """C-20: every LCSC part in stock >= BUILD_QTY x per-board quantity (uses hardware/tools/jlc.py, cached)."""
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
    import jlc
    qty = {}
    for sh in design.sheets:
        for part in sh.parts:
            code = part.fields.get("LCSC")
            if code and not part.fields.get("_nobom") and not part.dnp:
                qty[code] = qty.get(code, 0) + 1
    for code, n in sorted(qty.items()):
        try:
            r = jlc.part(code)
        except Exception as e:  # noqa: BLE001
            add("WARN", "STOCK", f"{code}: lookup failed ({e})")
            continue
        if not r:
            add("WARN", "STOCK", f"{code}: not found in JLCPCB search")
        elif (r.get("stock") or 0) < BUILD_QTY * n:
            add("ERROR", "STOCK", f"{code} {r.get('mpn')}: stock {r.get('stock')} < {BUILD_QTY} boards x {n}/board")


def run(design, stock=None):
    findings = []

    def add(level, code, msg):
        findings.append((level, code, msg))

    nets = design.netlist()
    undetermined = []
    # ---- netlist sanity
    for net, pins in nets.items():
        if len(pins) < 2 and not net.startswith("NC_"):
            refs = ", ".join(f"{p.ref}.{pin['number']}({pin['name']})" for p, pin in pins)
            add("ERROR", "NET1", f"net '{net}' has only one connection: {refs}")
        if _vmax(design, net) is None:
            add("WARN", "NETV", f"net '{net}' has no worst-case voltage assigned")
    for sh in design.sheets:
        for part in sh.parts:
            for p in part.unconnected():
                add("ERROR", "OPEN", f"{part.ref} ({part.value}) pin {p['number']} '{p['name']}' is unconnected and not marked NC")
    # ---- board partition: a net spanning boards must pass through a B2B connector on each board it touches
    def _board(part):
        return str(part.fields.get("Board") or getattr(part.sheet, "board", "A"))
    for net, pins in nets.items():
        if net == "GND":
            continue
        boards = {_board(p) for p, _ in pins}
        if len(boards) > 1:
            b2b = {_board(p) for p, _ in pins if p.fields.get("B2B")}
            missing = boards - b2b
            if missing:
                add("ERROR", "BOARD", f"net '{net}' spans boards {sorted(boards)} but has no board-to-board connector on {sorted(missing)}")
    # ---- IC pin absolute maximum (C-19)
    for sh in design.sheets:
        for part in sh.parts:
            sym = part.sym["lib_id"].split(":")[-1]
            lim = PIN_ABS_MAX.get(sym)
            if not lim:
                continue
            for p, net in part.resolve():
                if net is None or p["name"] not in lim:
                    continue
                v = _vmax(design, net) or 0.0
                if v > lim[p["name"]] + 1e-6:
                    add("ERROR", "PINV", f"{part.ref} {sym} pin {p['name']} on '{net}' sees {v} V > abs-max {lim[p['name']]} V")
    # ---- derating
    for sh in design.sheets:
        for part in sh.parts:
            f = part.fields
            conns = [n for _, n in part.resolve() if n is not None]
            vnets = [(_vmax(design, n) or 0.0) for n in conns]
            vworst = max(vnets) if vnets else 0.0
            kind = part.sym["lib_id"].split(":")[-1]
            if "V_across" in f:          # bootstrap caps, divider legs: designer-stated stress
                vworst = float(f["V_across"])
            if kind == "C" and "Rated_V" in f:
                if f["Rated_V"] < 2 * vworst - 1e-6:
                    add("ERROR", "VCAP", f"{part.ref} {part.value}: rated {f['Rated_V']} V < 2 x {vworst} V on {conns}")
            if kind == "R" and "Rated_V" in f and len(vnets) == 2:
                across = float(f["V_across"]) if "V_across" in f else (abs(vnets[0] - vnets[1]) if 0.0 in vnets else max(vnets))
                if f["Rated_V"] < across - 1e-6:
                    add("ERROR", "VRES", f"{part.ref} {part.value}: package working voltage {f['Rated_V']} V < {across} V across")
                # X-34: no designer power figure -> compute the worst case V^2/R from the net voltages
                if not f.get("Op_P") and f.get("Rated_P"):
                    ohms = _ohms(part.value)
                    if ohms:
                        if "V_across" in f:
                            v_r = float(f["V_across"])
                        elif 0.0 in vnets or vnets[0] != vnets[1]:
                            v_r = abs(vnets[0] - vnets[1])
                        else:
                            v_r = None      # both ends on equal non-zero rails: stress set by the circuit, not the nets
                            undetermined.append(part.ref)
                        if v_r is not None:
                            p_w = v_r * v_r / ohms
                            if 3 * p_w > float(f["Rated_P"]) + 1e-9:
                                add("ERROR", "3TO1R", f"{part.ref} {part.value}: worst-case {v_r:.2f} V across -> {p_w*1000:.1f} mW "
                                    f"vs rated {float(f['Rated_P'])*1000:.0f} mW ({float(f['Rated_P'])/p_w:.2f}:1 < 3:1; "
                                    f"set Op_P with a justification if the net voltages overstate the stress)")
            if "Vds_rated" in f:
                d = f.get("_drain_net")
                if d and f["Vds_rated"] < 1.5 * (_vmax(design, d) or 0):
                    add("ERROR", "VFET", f"{part.ref}: Vds {f['Vds_rated']} V < 1.5 x {_vmax(design, d)} V")
            # 3:1 current / power
            for op, rated in (("Op_P", "Rated_P"), ("Op_I", "Rated_I"), ("Op_Irms", "Rated_I"), ("Op_Ipk", "Isat")):
                if op in f and rated in f and f[op]:
                    ratio = float(f[rated]) / float(f[op]) if float(f[op]) else 99
                    need = 2.0 if op == "Op_Ipk" else 3.0
                    if ratio < need - 1e-6:
                        if f.get("Derating_Exception"):
                            add("INFO", "3TO1X", f"{part.ref} {part.value}: {ratio:.2f}:1 accepted exception -> {f['Derating_Exception']}")
                        else:
                            add("ERROR", "3TO1", f"{part.ref} {part.value}: {rated}={f[rated]} vs {op}={f[op]} -> {ratio:.2f}:1 (< {need:.0f}:1)")
            if f.get("_power_part") and not any(k in f for k in ("Op_P", "Op_I", "Op_Irms")):
                add("WARN", "3TO1?", f"{part.ref} {part.value}: power part without operating current/power annotation")
    # ---- BOM
    for sh in design.sheets:
        for part in sh.parts:
            if part.fields.get("_nobom") or part.dnp:
                continue
            if not part.fields.get("LCSC"):
                add("WARN" if part.fields.get("Consigned") else "ERROR", "LCSC",
                    f"{part.ref} {part.value}: no LCSC part number" + (" (consigned)" if part.fields.get("Consigned") else ""))
    if stock:
        stock_check(design, add)
    if undetermined:
        add("INFO", "3TO1R", f"{len(undetermined)} resistors sit between equal non-zero rails; dissipation not derivable from net "
            f"voltages (series/gate/pull resistors): {', '.join(sorted(undetermined)[:12])}{' ...' if len(undetermined) > 12 else ''}")
    if getattr(design, "defaulted_nets", None):
        add("INFO", "NETV", f"{len(design.defaulted_nets)} nets had no explicit voltage and were treated as 3.6 V logic")
    # ---- design-level assertions
    for desc, ok in design.checks:
        if not ok:
            add("ERROR", "ASSERT", desc)
    return findings


def report(findings, path=None):
    lines = []
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    for lvl, code, msg in sorted(findings, key=lambda x: (order[x[0]], x[1], x[2])):
        lines.append(f"{lvl:<5} {code:<6} {msg}")
    n_err = sum(1 for f in findings if f[0] == "ERROR")
    n_warn = sum(1 for f in findings if f[0] == "WARN")
    lines.append(f"\n{n_err} errors, {n_warn} warnings")
    text = "\n".join(lines)
    if path:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    return text, n_err


if __name__ == "__main__":
    print("run via hardware/gen/build.py")
    sys.exit(0)
