"""Pick JLCPCB parts for every passive/discrete value the design needs.

Selection rules (see docs/design-rules.md):
  * rating >= 3x the worst-case net voltage (caps, resistors via package working voltage, diodes, FETs)
  * prefer JLCPCB Basic, then Preferred, then Extended with the most stock
  * stock >= 500 so a 5-board build plus attrition is safe
Output: hardware/gen/passives.json (consumed by the schematic generator).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jlc  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gen", "passives.json")

MULT = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3, "": 1.0, "k": 1e3, "K": 1e3, "M": 1e6}


def num(s):
    """'100nF' -> 1e-7, '16V' -> 16, '4.7kΩ' -> 4700, '1/10W' -> 0.1"""
    if s is None:
        return None
    s = str(s).strip()
    m = re.match(r"^(\d+)/(\d+)\s*W", s)
    if m:
        return int(m.group(1)) / int(m.group(2))
    m = re.match(r"^([\d.]+)\s*([pnuµmkKM]?)", s)
    if not m:
        return None
    return float(m.group(1)) * MULT[m.group(2)]


def ok_stock(r, min_stock):
    return (r.get("stock") or 0) >= min_stock


def rank(r):
    return (0 if r["lib"] == "base" else (1 if r["preferred"] else 2), -(r["stock"] or 0))


def pick(query, pred, min_stock=500):
    cands = [r for r in jlc.search(query, 40) if pred(r) and ok_stock(r, min_stock)]
    cands.sort(key=rank)
    return cands[0] if cands else None


def cap(value, min_v, packages, dielectric=("X7R", "X5R", "C0G", "NP0")):
    target = num(value)

    def pred(r):
        a = r["attrs"]
        c = num(a.get("Capacitance"))
        v = num(a.get("Voltage Rating"))
        tc = (a.get("Temperature Coefficient") or "")
        return (c is not None and abs(c - target) / target < 0.01 and v is not None and v >= min_v
                and r["package"] in packages and any(d in tc for d in dielectric))
    best = None
    for pkg in packages:
        r = pick(f"{value} {pkg} capacitor", pred)
        if r and (best is None or rank(r) < rank(best)):
            best = r
    return best


def res(value, packages, min_p=0.0):
    target = num(value.replace("R", "").replace("Ω", "")) if value not in ("0", "0R") else 0.0

    def pred(r):
        a = r["attrs"]
        rv = a.get("Resistance")
        if rv is None:
            return False
        rv = rv.replace("Ω", "")
        val = num(rv)
        p = num(a.get("Power(Watts)"))
        tol = a.get("Tolerance") or ""
        if target == 0:
            match = val == 0
        else:
            match = val is not None and abs(val - target) / target < 0.005
        return match and r["package"] in packages and (p or 0) >= min_p and ("1%" in tol or target == 0)
    best = None
    for pkg in packages:
        q = f"{value}Ω {pkg} resistor" if target != 0 else f"0Ω {pkg} jumper resistor"
        r = pick(q, pred)
        if r and (best is None or rank(r) < rank(best)):
            best = r
    return best


def by_mpn(mpn, min_stock=100):
    for r in jlc.search(mpn, 20):
        if (r["mpn"] or "").upper().startswith(mpn.upper()) and ok_stock(r, min_stock):
            return r
    return None


# ---------------------------------------------------------------- requirements
# key: (kind, value, min_voltage or power, packages)
# Voltage rule for MLCCs: rating >= 2x net max (docs/design-rules.md 1.3)
#   0.95 V -> 6.3 V | 3.3 V -> 10 V | 5 V -> 16 V | 12 V -> 25 V | 21-24 V (VBAT, VDCIN, VPOE) -> 50 V
#   28 V VBUS -> >=56 V (63/100 V) | 57 V PoE primary -> >=114 V (200/250 V)
CAPS = {
    # <=5 V rails
    "C_100n_16V": ("100nF", 16, ["0402"]),
    "C_1u_16V": ("1uF", 16, ["0402", "0603"]),
    "C_2u2_16V": ("2.2uF", 16, ["0402", "0603"]),
    "C_4u7_16V": ("4.7uF", 16, ["0603", "0805"]),
    "C_10u_16V": ("10uF", 16, ["0603", "0805"]),
    "C_22u_10V": ("22uF", 10, ["0805", "1206"]),
    "C_47u_10V": ("47uF", 10, ["1206", "1210"]),
    "C_22u_6V3": ("22uF", 6.3, ["0603", "0805"]),
    # small-signal / crystal / filter (<=5 V nets) 50 V 0402
    "C_10n_50V": ("10nF", 50, ["0402"]),
    "C_1n_50V": ("1nF", 50, ["0402"]),
    "C_4n7_50V": ("4.7nF", 50, ["0402"]),
    "C_33n_50V": ("33nF", 50, ["0402"]),
    "C_47n_50V": ("47nF", 50, ["0402"]),
    "C_220n_16V": ("220nF", 16, ["0402"]),
    "C_470n_16V": ("470nF", 16, ["0402", "0603"]),
    "C_10p_50V": ("10pF", 50, ["0402"], ("C0G", "NP0")),
    "C_12p_50V": ("12pF", 50, ["0402"], ("C0G", "NP0")),
    "C_18p_50V": ("18pF", 50, ["0402"], ("C0G", "NP0")),
    "C_330p_50V": ("330pF", 50, ["0402"], ("C0G", "NP0")),
    "C_22n_50V": ("22nF", 50, ["0402"]),
    "C_100p_50V": ("100pF", 50, ["0402"], ("C0G", "NP0")),
    "C_2n2_50V": ("2.2nF", 50, ["0402"]),
    "C_100u_10V": ("100uF", 10, ["1206", "1210"]),
    # 12 V rail (Qi, router feed)
    "C_10u_25V": ("10uF", 25, ["0805", "1206"]),
    "C_22u_25V": ("22uF", 25, ["1206", "1210"]),
    # 21-24 V nets (VBAT, VDCIN, VPOE, VDCOUT): 50 V
    "C_100n_50V": ("100nF", 50, ["0402", "0603"]),
    "C_1u_50V": ("1uF", 50, ["0603", "0805"]),
    "C_4u7_50V": ("4.7uF", 50, ["0805", "1206"]),
    "C_10u_50V": ("10uF", 50, ["1206", "1210"]),
    "C_470n_50V": ("470nF", 50, ["0402", "0603"]),
    # 28 V VBUS nets: >= 63 V
    "C_100n_100V": ("100nF", 63, ["0603", "0805"]),
    "C_1u_100V": ("1uF", 63, ["0805", "1206"]),
    "C_2u2_100V": ("2.2uF", 63, ["1206", "1210"]),
    "C_4u7_100V": ("4.7uF", 63, ["1210", "1812"]),
    "C_470n_100V": ("470nF", 63, ["0603", "0805"]),
    "C_10n_100V": ("10nF", 63, ["0402", "0603"]),
    # PoE primary 57 V: >= 114 V
    "C_100n_250V": ("100nF", 114, ["0805", "1206"]),
    "C_1u_250V": ("1uF", 114, ["1206", "1210"]),
    # Y-cap across the PoE isolation barrier (2 kV class)
    "C_1n_2kV": ("1nF", 2000, ["1206", "1808", "1812"]),
}

RES = {
    # 0402 (50 V working -> <=16.7 V across) for logic and 5 V nets
    **{f"R_{v}_0402": (v, ["0402"], 0.0) for v in [
        "0", "10", "22", "33", "49.9", "100", "220", "330", "470", "1k", "1.5k", "2.2k", "2.49k", "4.7k", "5.1k",
        "10k", "12k", "15k", "20k", "22k", "24k", "33k", "40.2k", "47k", "49.9k", "56k", "68k", "80.6k",
        "100k", "120k", "150k", "200k", "220k", "330k", "470k", "1M", "6.04k", "12.4k", "124k",
        "249k", "5.23k", "30.1k", "4.02k", "7.5k", "11k", "191k", "16.2k", "31.6k", "52.3k", "140k", "1.87k", "3.92k", "1.2k", "680", "300k", "2k", "3.3k", "39k", "71.5k", "178k", "14.3k", "6.8k", "27k", "2.7k", "1.5M", "13k", "59k"]},
    # 0603 (75 V -> <=25 V across) for VBAT/VBUS-side dividers
    **{f"R_{v}_0603": (v, ["0603"], 0.0) for v in ["0", "10k", "100k", "200k", "1M", "330k", "470k", "1k", "4.7k", "470", "2.2"]},
    # 0805 (150 V -> <=50 V across) for PoE-side / 28 V-across dividers
    **{f"R_{v}_0805": (v, ["0805"], 0.0) for v in ["0", "10k", "100k", "1M", "24.9k", "63.4", "90.9", "33.2k", "249", "49.9k", "1k", "4.7k", "2.2k"]},
}

MPNS = {
    # sense resistors (5 mohm 2512 3 W)
    "RS_5m_2512": "LR2512D-3W-5mR",
    # low-side / signal FETs and diodes
    "Q_AO3400A": "AO3400A",
    "LED_G_0603": "KT-0603G",
    "LED_R_0603": "KT-0603R",
    "TVS_SMBJ24A": "SMBJ24A",
    "TVS_SMBJ33A": "SMBJ33A",
    "TVS_SMBJ26A": "SMBJ26A",
    "TVS_SMAJ58A": "SMAJ58A",
    "TVS_SMF5V0A": "SMF5.0A",
    "D_B5819W": "B5819W",
    "SW_TACT": "TS-1187A-B-A-B",
    "FB_600R_0603": "GZ1608D601TF",
    "NTC_10k_0603": "NCP18XH103F03RB",
    "FB_3A_0603": "UPZ1608E101-3R0TF",
    # power-stage FET candidates (60 V, 5x6)
    "Q_BSC016N06NS": "BSC016N06NS",
    "Q_NTMFS5C628NL": "NTMFS5C628NL",
    "Q_BSC034N06NS": "BSC034N06NS",
}

# Free-text searches whose top results are printed for manual choice (inductors, big FETs)
BROWSE = [
    "6.8uH 22A inductor", "6.8uH 25A inductor", "10uH 15A inductor", "4.7uH 10A inductor",
    "60V N-channel MOSFET DFN5x6 2mΩ", "60V MOSFET PDFN5x6", "100V P-channel MOSFET",
    "2.5G network transformer POE", "RJ45 POE magnetics",
]


def main():
    out = {}
    for key, spec in CAPS.items():
        value, vmin, pkgs = spec[0], spec[1], spec[2]
        diel = spec[3] if len(spec) > 3 else ("X7R", "X5R", "C0G", "NP0")
        r = cap(value, vmin, pkgs, diel)
        out[key] = r
        print(f"{key:<14}", jlc.fmt(r) if r else "-- NOT FOUND --")
    for key, (v, pkgs, pmin) in RES.items():
        r = res(v, pkgs, pmin)
        out[key] = r
        print(f"{key:<14}", jlc.fmt(r) if r else "-- NOT FOUND --")
    for key, mpn in MPNS.items():
        r = by_mpn(mpn)
        out[key] = r
        print(f"{key:<14}", jlc.fmt(r) if r else f"-- NOT FOUND ({mpn}) --")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    for q in BROWSE:
        print(f"\n== browse: {q}")
        for r in jlc.search(q, 12)[:8]:
            print("   ", jlc.fmt(r))


if __name__ == "__main__":
    main()
