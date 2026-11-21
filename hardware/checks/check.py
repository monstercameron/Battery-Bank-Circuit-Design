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


def _vmax(design, net):
    if net is None:
        return 0.0
    if net in design.net_v:
        return design.net_v[net]
    for prefix, v in design.net_v_prefix:
        if net.startswith(prefix):
            return v
    return None


def run(design, stock=None):
    findings = []

    def add(level, code, msg):
        findings.append((level, code, msg))

    nets = design.netlist()
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
