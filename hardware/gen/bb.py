"""Design-entry helpers: concise constructors for parts with JLCPCB data and ratings attached.

Every part carries machine-checkable ratings so hardware/checks can enforce
docs/design-rules.md (3:1 on current/power, 2x / 1.5x voltage derating).
"""
import json
import os

import generics
import symlib
from kicad_writer import Part, Project

HERE = os.path.dirname(os.path.abspath(__file__))
_LIB = None
_PASS = None

# KiCad standard-library footprints for generic packages
FP = {
    "R0402": "Resistor_SMD:R_0402_1005Metric", "R0603": "Resistor_SMD:R_0603_1608Metric",
    "R0805": "Resistor_SMD:R_0805_2012Metric", "R1206": "Resistor_SMD:R_1206_3216Metric",
    "R2512": "Resistor_SMD:R_2512_6332Metric",
    "C0402": "Capacitor_SMD:C_0402_1005Metric", "C0603": "Capacitor_SMD:C_0603_1608Metric",
    "C0805": "Capacitor_SMD:C_0805_2012Metric", "C1206": "Capacitor_SMD:C_1206_3216Metric",
    "C1210": "Capacitor_SMD:C_1210_3225Metric", "C1812": "Capacitor_SMD:C_1812_4532Metric",
    "C1808": "Capacitor_SMD:C_1808_4520Metric",
    "LED0603": "LED_SMD:LED_0603_1608Metric",
    "SOT23": "Package_TO_SOT_SMD:SOT-23", "SMB": "Diode_SMD:D_SMB", "SMA": "Diode_SMD:D_SMA",
    "SOD123": "Diode_SMD:D_SOD-123", "SOD323": "Diode_SMD:D_SOD-323",
    "TP": "TestPoint:TestPoint_Pad_D1.5mm", "TP1": "TestPoint:TestPoint_Pad_D1.0mm",
    "SJ": "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm",
    "SJ_OPEN": "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
    "XTAL3225": "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    "TAGCONNECT": "Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical",
    "PADS1x6": "Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical",
    "PADS1x4": "Connector_PinHeader_1.27mm:PinHeader_1x04_P1.27mm_Vertical",
    "QWIIC": "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
}

# package working-voltage and power ratings (resistors), used by the checker
RES_PKG = {"0402": (50, 0.0625), "0603": (75, 0.1), "0805": (150, 0.125), "1206": (200, 0.25), "2512": (200, 1.0)}


def lib():
    global _LIB
    if _LIB is None:
        _LIB = symlib.load_lcsc()
    return _LIB


def passives():
    global _PASS
    if _PASS is None:
        with open(os.path.join(HERE, "passives.json"), encoding="utf-8") as f:
            _PASS = json.load(f)
    return _PASS


def _gsym(kind):
    g = generics.build()[kind]
    pins = []
    for sub in g["node"]:
        if isinstance(sub, list) and sub and sub[0] == "symbol":
            for p in sub:
                if isinstance(p, list) and p and p[0] == "pin":
                    at = [x for x in p if isinstance(x, list) and x[0] == "at"][0]
                    name = [x for x in p if isinstance(x, list) and x[0] == "name"][0][1]
                    num = [x for x in p if isinstance(x, list) and x[0] == "number"][0][1]
                    pins.append({"x": at[1], "y": at[2], "angle": at[3], "name": name, "number": num, "etype": str(p[1])})
    return {"lib_id": g["node"][1], "node": g["node"], "pins": pins}


def _lsym(name):
    s = lib().get(name)
    return {"lib_id": s.lib_id, "node": s.embedded(), "pins": s.pins, "fp": s.props.get("Footprint", ""),
            "lcsc": s.props.get("LCSC Part", ""), "mpn": s.props.get("MPN", "")}


MISSING = set()


def _jlc_fields(key):
    r = passives().get(key)
    if not r:
        MISSING.add(key)
        parts = key.split("_")
        pkg = parts[-1] if parts[-1][:1].isdigit() else "0402"
        r = {"code": "", "mpn": key, "lib": "expand", "preferred": False, "package": pkg,
             "attrs": {"Capacitance": parts[1] if len(parts) > 1 else "?", "Voltage Rating": parts[2] if len(parts) > 2 and parts[2].endswith("V") else "0V"}}
    return {"LCSC": r["code"], "MPN": r["mpn"], "JLC_Class": "Basic" if r["lib"] == "base" else ("Preferred" if r["preferred"] else "Extended")}, r


class Design(Project):
    """Project with net-voltage bookkeeping for the derating checker."""

    def __init__(self, name="battery-bank"):
        super().__init__(name)
        self.net_v = {}          # net -> worst-case max voltage
        self.net_v_prefix = []   # (prefix, vmax) fallbacks, first match wins
        self.checks = []         # extra assertions: (description, ok_bool)

    def vp(self, prefix, vmax):
        self.net_v_prefix.append((prefix, vmax))

    def L(self, sh, symname, n1, n2, rated_i, isat, irms, ipk, value=None):
        return self.IC(sh, symname, {"1": n1, "2": n2}, prefix="L", value=value,
                       fields={"Rated_I": rated_i, "Isat": isat, "Op_Irms": irms, "Op_Ipk": ipk, "_power_part": True})

    def FET(self, sh, symname, g, d, s, vds, id100, irms, prefix="Q"):
        return self.IC(sh, symname, {"G": g, "D": d, "S": s}, prefix=prefix,
                       fields={"Vds_rated": vds, "_drain_net": d, "Rated_I": id100, "Op_Irms": irms, "_power_part": True})

    def v(self, net, vmax):
        self.net_v[net] = vmax
        return net

    # --------------------------------------------------------------- generics
    def R(self, sh, value, n1, n2, key=None, pkg="0402", p_op=0.0, fields=None, ref=None):
        key = key or f"R_{value}_{pkg}"
        f, r = _jlc_fields(key)
        vrat, prat = RES_PKG[pkg]
        f.update({"Rated_V": vrat, "Rated_P": prat, "Op_P": p_op})
        f.update(fields or {})
        return sh.add(Part(sh, ref or self.next_ref("R"), _gsym("R"), value, FP["R" + pkg], f, {"1": n1, "2": n2}))

    def C(self, sh, key, n1, n2, fields=None, ref=None, dnp=False):
        f, r = _jlc_fields(key)
        pkg = r["package"]
        vr = r["attrs"].get("Voltage Rating", "0V").replace("V", "").strip()
        mult = 1000.0 if vr.lower().endswith("k") else 1.0
        f.update({"Rated_V": float(vr.rstrip("kK")) * mult})
        f.update(fields or {})
        val = f'{r["attrs"].get("Capacitance", "?")} {r["attrs"].get("Voltage Rating", "")}'
        return sh.add(Part(sh, ref or self.next_ref("C"), _gsym("C"), val, FP.get("C" + pkg, ""), f, {"1": n1, "2": n2}, dnp=dnp))

    def RSENSE(self, sh, n1, n2, i_op, value="5m"):
        f, r = _jlc_fields("RS_5m_2512")
        p_op = i_op * i_op * 0.005
        f.update({"Rated_P": 3.0, "Op_P": round(p_op, 3), "Rated_V": 200})
        return sh.add(Part(sh, self.next_ref("R"), _gsym("R"), "5m 1% 3W", FP["R2512"], f, {"1": n1, "2": n2}))

    def LED(self, sh, color, a, k):
        f, _ = _jlc_fields("LED_G_0603" if color == "G" else "LED_R_0603")
        return sh.add(Part(sh, self.next_ref("D"), _gsym("LED"), f"LED {color}", FP["LED0603"], f, {"A": a, "K": k}))

    def TP(self, sh, net, small=False):
        return sh.add(Part(sh, self.next_ref("TP"), _gsym("TP"), net, FP["TP1" if small else "TP"], {"_nobom": True}, {"1": net}))

    def JP(self, sh, n1, n2, i_op=0.0, open_=False, note=""):
        # solder-bridge jumper: copper only, no BOM. Width sized by layout for 3x current.
        return sh.add(Part(sh, self.next_ref("JP"), _gsym("JP"), "SJ " + note, FP["SJ_OPEN" if open_ else "SJ"],
                           {"_nobom": True, "Op_I": i_op}, {"1": n1, "2": n2}))

    def generic(self, sh, kind, value, footprint, conns, fields=None, prefix=None, dnp=False):
        sym = _gsym(kind)
        return sh.add(Part(sh, self.next_ref(prefix or sym["lib_id"].split(":")[1][:1]), sym, value, footprint, fields or {}, conns, dnp=dnp))

    def jlc_generic(self, sh, kind, key, conns, fields=None, prefix=None, value=None, footprint=None, dnp=False):
        f, r = _jlc_fields(key)
        f.update(fields or {})
        sym = _gsym(kind)
        fp = footprint or {"SMB": FP["SMB"], "SMA": FP["SMA"], "SOT-23": FP["SOT23"], "SOT-23-3": FP["SOT23"],
                           "SOD-123": FP["SOD123"], "SOD-123F": FP["SOD123"], "SOD-323": FP["SOD323"]}.get(r["package"], "")
        return sh.add(Part(sh, self.next_ref(prefix or "U"), sym, value or r["mpn"], fp, f, conns, dnp=dnp))

    def CONN(self, sh, name, pin_names, conns, footprint="", fields=None, prefix="J", value=None, nc=(), dnp=False):
        """Generic N-pin connector/module symbol (for parts without an LCSC symbol, e.g. consigned modules)."""
        g = generics.connector(name, pin_names)
        pins = []
        for sub in g["node"]:
            if isinstance(sub, list) and sub and sub[0] == "symbol":
                for p in sub:
                    if isinstance(p, list) and p and p[0] == "pin":
                        at = [x for x in p if isinstance(x, list) and x[0] == "at"][0]
                        nm = [x for x in p if isinstance(x, list) and x[0] == "name"][0][1]
                        num = [x for x in p if isinstance(x, list) and x[0] == "number"][0][1]
                        pins.append({"x": at[1], "y": at[2], "angle": at[3], "name": nm, "number": num, "etype": "passive"})
        sym = {"lib_id": g["node"][1], "node": g["node"], "pins": pins}
        part = Part(sh, self.next_ref(prefix), sym, value or name, footprint, fields or {}, conns, dnp=dnp)
        part.nc = set(nc)
        return sh.add(part)

    # ------------------------------------------------------------- LCSC parts
    def IC(self, sh, symname, conns, nc=(), prefix="U", value=None, fields=None, ref=None, dnp=False):
        s = _lsym(symname)
        f = {"LCSC": s["lcsc"], "MPN": s["mpn"] or symname}
        f.update(fields or {})
        part = Part(sh, ref or self.next_ref(prefix), s, value or (s["mpn"] or symname), s["fp"], f, conns, dnp=dnp)
        part.nc = set(nc)
        return sh.add(part)
