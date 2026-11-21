"""Build the KiCad schematic, run design checks, export the JLCPCB BOM.

    python hardware/gen/build.py            # full design
    python hardware/gen/build.py --only usbc_port   # subset (for quick iteration)
"""
import argparse
import csv
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "checks"))

import check  # noqa: E402
from bb import Design  # noqa: E402
from blocks import (aux_power, audio, battery, dc_output, ethernet, lighting, lora, mcu, power_input,  # noqa: E402
                    poe, qi, usb_a, usbc_port)

OUT = os.path.join(ROOT, "kicad")


def net_voltages(D):
    """Worst-case net voltages (docs/design-rules.md 1.3). Exact entries first, then prefixes."""
    for net, v in {"GND": 0.0, "VBAT": 21.0, "V3V3": 3.6, "V3V3_ETH": 3.6, "V3V3_LORA": 3.6, "V5_PD": 5.5,
                   "V5_AUX": 5.5, "V5_GLOW": 5.5, "V12_QI": 12.4, "V12_RTR": 12.4, "V0V95_SW": 1.0,
                   "VDCIN": 24.3, "VIN_AUX": 24.3, "VPOE": 22.0, "VDCOUT": 24.0, "VDCOUT_RAW": 24.0,
                   "PD_INT_N": 3.6, "CHG_INT_N": 3.6, "I2C_SDA": 3.6, "I2C_SCL": 3.6}.items():
        D.v(net, v)
    for prefix, v in [("I2C", 3.6), ("SW_P", 3.6), ("POE_", 57.0), ("PSE", 57.0), ("PRI_", 57.0),
                      ("VBUS_C", 28.0), ("VIN_C", 28.0), ("ESP_", 3.6), ("EXP_", 3.6), ("LORA_", 3.6),
                      ("ETH_", 3.6), ("AUD_", 5.5), ("LED_", 5.5), ("USBA_", 12.6), ("QI_", 12.6),
                      ("DCO_", 24.0), ("DCI_", 24.3), ("INS_", 24.3), ("CART_", 21.0), ("SEC_", 22.0),
                      ("RTR_", 12.6), ("NFC_", 3.6)]:
        D.vp(prefix, v)
    # anything ending in a per-port suffix defaults to the logic level unless set exactly
    for k in range(1, 5):
        D.vp(f"", 0)  # placeholder removed below
    D.net_v_prefix = [p for p in D.net_v_prefix if p[0]]


def default_logic(D):
    """Nets without an explicit voltage are treated as 3.6 V logic for the derating check."""
    for net in D.netlist():
        if net not in D.net_v and not any(net.startswith(p) for p, _ in D.net_v_prefix):
            D.net_v.setdefault(net, 3.6)


def bom(D, path):
    rows = {}
    for sh in D.sheets:
        for p in sh.parts:
            if p.fields.get("_nobom") or p.dnp:
                continue
            key = (p.value, p.footprint, p.fields.get("LCSC", ""))
            rows.setdefault(key, []).append(p.ref)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "Qty"])
        for (val, fp, lcsc), refs in sorted(rows.items(), key=lambda r: r[1][0]):
            w.writerow([val, ",".join(sorted(refs, key=lambda r: (r.rstrip("0123456789"), int("".join(c for c in r if c.isdigit()) or 0)))),
                        fp.split(":")[-1], lcsc, len(refs)])
    return len(rows), sum(len(v) for v in rows.values())


def build(only=None):
    D = Design()
    net_voltages(D)
    blocks = [("usbc_port", lambda: [usbc_port.build(D, k) for k in range(1, 5)]),
              ("power_input", lambda: power_input.build(D)), ("poe", lambda: poe.build(D)),
              ("battery", lambda: battery.build(D)), ("aux_power", lambda: aux_power.build(D)),
              ("ethernet", lambda: ethernet.build(D)), ("mcu", lambda: mcu.build(D)), ("lora", lambda: lora.build(D)),
              ("audio", lambda: audio.build(D)), ("lighting", lambda: lighting.build(D)),
              ("dc_output", lambda: dc_output.build(D)), ("usb_a", lambda: usb_a.build(D)), ("qi", lambda: qi.build(D))]
    for name, fn in blocks:
        if only and name not in only:
            continue
        fn()
    default_logic(D)
    return D


def build_cartridge():
    from blocks import cartridge
    D = Design("battery-cartridge")
    net_voltages(D)
    cartridge.build(D)
    default_logic(D)
    return D


def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--project", default="main", choices=["main", "cartridge"])
    a = ap.parse_args()
    if a.project == "cartridge":
        OUT = os.path.join(ROOT, "kicad_cartridge")
        D = build_cartridge()
    else:
        D = build(a.only)
    if os.path.isdir(OUT):
        for f in os.listdir(OUT):
            if f.endswith(".kicad_sch"):
                os.remove(os.path.join(OUT, f))
    os.makedirs(OUT, exist_ok=True)
    D.write(OUT)
    write_project_files(OUT, D.name)
    write_bb_library(D)
    n_lines, n_parts = bom(D, os.path.join(OUT, "bom_jlcpcb.csv"))
    findings = check.run(D)
    text, n_err = check.report(findings, os.path.join(OUT, "design_check.txt"))
    kicad_outputs(OUT)
    print(text[-3000:])
    print(f"\nsheets={len(D.sheets)} parts={sum(len(s.parts) for s in D.sheets)} bom_lines={n_lines} bom_parts={n_parts}")
    return 1 if n_err else 0


KICAD_CLI = os.environ.get("KICAD_CLI", os.path.expandvars(r"%LOCALAPPDATA%\Programs\KiCad\10.0\bin\kicad-cli.exe"))


def kicad_outputs(out):
    """KiCad ERC report + a PDF of every sheet so the build can be watched as it progresses."""
    import subprocess
    if not os.path.exists(KICAD_CLI):
        print("kicad-cli not found; skipping ERC/PDF")
        return
    name = [f for f in os.listdir(out) if f.endswith(".kicad_pro")][0][:-10]
    sch = os.path.join(out, name + ".kicad_sch")
    r = subprocess.run([KICAD_CLI, "sch", "erc", "--format", "report", "-o", os.path.join(out, "erc.rpt"), sch],
                       capture_output=True, text=True)
    print("KiCad ERC:", (r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr) else "?")
    subprocess.run([KICAD_CLI, "sch", "export", "pdf", "-o", os.path.join(out, name + "-schematic.pdf"), sch],
                   capture_output=True, text=True)


def write_bb_library(D):
    """Write every generic (bb:) symbol used by the design into hardware/lib/bb.kicad_sym."""
    import sexp
    from sexp import Sym
    nodes = {}
    for sh in D.sheets:
        for p in sh.parts:
            lid = p.sym["lib_id"]
            if lid.startswith("bb:") and lid not in nodes:
                node = list(p.sym["node"])
                node[1] = lid.split(":", 1)[1]
                nodes[lid] = node
    doc = [Sym("kicad_symbol_lib"), [Sym("version"), 20231120], [Sym("generator"), "bb_gen"]] + list(nodes.values())
    with open(os.path.join(ROOT, "lib", "bb.kicad_sym"), "w", encoding="utf-8") as f:
        f.write(sexp.dump(doc) + "\n")


def write_project_files(out, name="battery-bank"):
    lib = os.path.relpath(os.path.join(ROOT, "lib"), out).replace("\\", "/")
    with open(os.path.join(out, "sym-lib-table"), "w") as f:
        f.write('(sym_lib_table\n  (version 7)\n'
                f'  (lib (name "lcsc")(type "KiCad")(uri "${{KIPRJMOD}}/{lib}/lcsc.kicad_sym")(options "")(descr "LCSC/EasyEDA parts"))\n'
                f'  (lib (name "bb")(type "KiCad")(uri "${{KIPRJMOD}}/{lib}/bb.kicad_sym")(options "")(descr "Generic R/C/L/D/FET/TP symbols"))\n)\n')
    with open(os.path.join(out, "fp-lib-table"), "w") as f:
        f.write('(fp_lib_table\n  (version 7)\n'
                f'  (lib (name "lcsc")(type "KiCad")(uri "${{KIPRJMOD}}/{lib}/lcsc.pretty")(options "")(descr "LCSC/EasyEDA footprints"))\n)\n')
    pro = os.path.join(out, f"{name}.kicad_pro")
    src = os.path.join(HERE, "project_template.kicad_pro")
    if os.path.exists(src):
        shutil.copy(src, pro)


if __name__ == "__main__":
    sys.exit(main())
