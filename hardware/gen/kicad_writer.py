"""Write a hierarchical KiCad schematic from a code-defined netlist.

Every connected pin gets a global label at its connection point (no wires), so
connectivity is exactly the netlist defined in Python. Unconnected pins get an
explicit no-connect flag only when the design says so; anything else is left
open so KiCad's ERC reports it.
"""
import copy
import os
import uuid as _uuid

import generics
import sexp
from sexp import Sym

GRID = 1.27
PROJECT = "battery-bank"


def uid(seed):
    return str(_uuid.uuid5(_uuid.NAMESPACE_URL, "bb/" + seed))


def snap(v):
    return round(round(v / GRID) * GRID, 4)


class Part:
    def __init__(self, sheet, ref, sym, value, footprint="", fields=None, conns=None, dnp=False, symdef=None):
        self.sheet = sheet
        self.ref = ref
        self.sym = sym          # dict with keys: lib_id, node (embedded), pins (list of pin dicts)
        self.value = value
        self.footprint = footprint
        self.fields = fields or {}
        self.conns = conns or {}  # pin key (number or name) -> net
        self.nc = set()
        self.dnp = dnp
        self.x = self.y = 0.0

    def pin_list(self):
        return self.sym["pins"]

    def resolve(self):
        """Return list of (pin, net) with pin keys resolved to concrete pins."""
        out = []
        pins = self.pin_list()
        used = set()
        for key, net in self.conns.items():
            matches = [p for p in pins if p["number"] == str(key)] or [p for p in pins if p["name"] == key]
            if not matches:
                raise KeyError(f"{self.ref}: no pin '{key}' in {self.sym['lib_id']}")
            for p in matches:
                if id(p) in used:
                    continue
                used.add(id(p))
                out.append((p, net))
        for key in self.nc:
            matches = [p for p in pins if p["number"] == str(key)] or [p for p in pins if p["name"] == key]
            if not matches:
                raise KeyError(f"{self.ref}: no pin '{key}' for NC")
            for p in matches:
                if id(p) not in used:
                    used.add(id(p))
                    out.append((p, None))
        return out

    def unconnected(self):
        resolved = {id(p) for p, _ in self.resolve()}
        return [p for p in self.pin_list() if id(p) not in resolved]


class Sheet:
    def __init__(self, project, name, title, page_size="A1"):
        self.project = project
        self.name = name
        self.title = title
        self.page_size = page_size
        self.parts = []
        self.notes = []
        self.uuid = uid("sheet/" + name)

    def add(self, part):
        part.sheet = self
        self.parts.append(part)
        return part

    def note(self, text):
        self.notes.append(text)


class Project:
    def __init__(self, name=PROJECT):
        self.name = name
        self.sheets = []
        self.root_uuid = uid("root/" + name)
        self.lib_symbols = {}
        self.ref_counts = {}

    def sheet(self, name, title, page_size="A1"):
        s = Sheet(self, name, title, page_size)
        self.sheets.append(s)
        return s

    def next_ref(self, prefix):
        n = self.ref_counts.get(prefix, 0) + 1
        self.ref_counts[prefix] = n
        return f"{prefix}{n}"

    # ------------------------------------------------------------------ layout
    @staticmethod
    def _extent(part):
        pins = part.pin_list()
        if not pins:
            return (-5, -5, 5, 5)
        lab = max([len(n or "") for _, n in part.resolve()] + [4]) * 1.0 + 4
        xs = [p["x"] for p in pins]
        ys = [p["y"] for p in pins]
        return (min(xs) - lab, min(ys) - 5, max(xs) + lab, max(ys) + 5)

    def layout(self, sheet):
        x0, y0 = 30.0, 40.0
        maxw = {"A0": 1150, "A1": 800, "A2": 560, "A3": 400}.get(sheet.page_size, 800)
        x, y, rowh = x0, y0, 0.0
        for p in sheet.parts:
            ex = self._extent(p)
            w, h = ex[2] - ex[0], ex[3] - ex[1]
            if x + w > maxw and x > x0:
                x = x0
                y += rowh + 8
                rowh = 0
            p.x = snap(x - ex[0])
            p.y = snap(y + ex[3])
            x += w + 6
            rowh = max(rowh, h)

    # ----------------------------------------------------------------- writing
    def _label(self, net, x, y, angle):
        return [Sym("global_label"), net, [Sym("shape"), Sym("bidirectional")], [Sym("at"), x, y, angle],
                [Sym("fields_autoplaced"), Sym("yes")],
                [Sym("effects"), [Sym("font"), [Sym("size"), 1.0, 1.0]], [Sym("justify"), Sym("right" if angle == 180 else "left")]] if angle in (0, 180)
                else [Sym("effects"), [Sym("font"), [Sym("size"), 1.0, 1.0]]],
                [Sym("uuid"), uid(f"lbl/{net}/{x}/{y}")]]

    def _symbol_instance(self, sheet, part):
        node = [Sym("symbol"), [Sym("lib_id"), part.sym["lib_id"]], [Sym("at"), part.x, part.y, 0], [Sym("unit"), 1],
                [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("no" if part.fields.get("_nobom") else "yes")],
                [Sym("on_board"), Sym("yes")], [Sym("dnp"), Sym("yes" if part.dnp else "no")],
                [Sym("uuid"), uid(f"sym/{part.ref}")]]
        ext = self._extent(part)
        props = [("Reference", part.ref, ext[3] - 2), ("Value", part.value, ext[1] + 2),
                 ("Footprint", part.footprint, None), ("Datasheet", part.fields.get("Datasheet", ""), None)]
        for k, v in part.fields.items():
            if k.startswith("_") or k == "Datasheet":
                continue
            props.append((k, v, None))
        for name, val, dy in props:
            hide = dy is None
            node.append([Sym("property"), name, str(val), [Sym("at"), part.x, part.y - (dy if dy else 0), 0],
                         [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]] + ([Sym("hide")] if hide else [])])
        for p in part.pin_list():
            node.append([Sym("pin"), p["number"], [Sym("uuid"), uid(f"pin/{part.ref}/{p['number']}/{p['name']}")]])
        node.append([Sym("instances"), [Sym("project"), self.name,
                     [Sym("path"), f"/{self.root_uuid}/{sheet.uuid}", [Sym("reference"), part.ref], [Sym("unit"), 1]]]])
        return node

    def write_sheet(self, sheet, outdir):
        self.layout(sheet)
        libs = {}
        items = []
        for part in sheet.parts:
            libs[part.sym["lib_id"]] = part.sym["node"]
            items.append(self._symbol_instance(sheet, part))
            for p, net in part.resolve():
                ax, ay = snap(part.x + p["x"]), snap(part.y - p["y"])
                if net is None:
                    items.append([Sym("no_connect"), [Sym("at"), ax, ay], [Sym("uuid"), uid(f"nc/{part.ref}/{p['number']}")]])
                else:
                    angle = int((p["angle"] + 180) % 360)
                    items.append(self._label(net, ax, ay, angle))
        texts = []
        ty = 20.0
        for t in [sheet.title] + sheet.notes:
            texts.append([Sym("text"), t, [Sym("exclude_from_sim"), Sym("no")], [Sym("at"), 20, ty, 0],
                          [Sym("effects"), [Sym("font"), [Sym("size"), 2.0 if t == sheet.title else 1.5, 2.0 if t == sheet.title else 1.5]],
                           [Sym("justify"), Sym("left")]], [Sym("uuid"), uid(f"txt/{sheet.name}/{ty}")]])
            ty += 3.5
        doc = [Sym("kicad_sch"), [Sym("version"), 20231120], [Sym("generator"), "bb_gen"], [Sym("generator_version"), "1.0"],
               [Sym("uuid"), sheet.uuid], [Sym("paper"), sheet.page_size],
               [Sym("title_block"), [Sym("title"), sheet.title], [Sym("company"), "Battery Bank"], [Sym("rev"), "A"]],
               [Sym("lib_symbols")] + list(libs.values())] + texts + items
        with open(os.path.join(outdir, f"{sheet.name}.kicad_sch"), "w", encoding="utf-8") as f:
            f.write(sexp.dump(doc) + "\n")

    def write_root(self, outdir):
        items = []
        x, y = 25.0, 40.0
        for i, s in enumerate(self.sheets):
            w, h = 60.0, 12.0
            items.append([Sym("sheet"), [Sym("at"), x, y], [Sym("size"), w, h], [Sym("fields_autoplaced"), Sym("yes")],
                          [Sym("stroke"), [Sym("width"), 0.1524], [Sym("type"), Sym("solid")]],
                          [Sym("fill"), [Sym("color"), 0, 0, 0, 0.0]], [Sym("uuid"), s.uuid],
                          [Sym("property"), "Sheetname", s.name, [Sym("at"), x, y - 0.7, 0],
                           [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]], [Sym("justify"), Sym("left"), Sym("bottom")]]],
                          [Sym("property"), "Sheetfile", f"{s.name}.kicad_sch", [Sym("at"), x, y + h + 0.6, 0],
                           [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]], [Sym("justify"), Sym("left"), Sym("top")]]],
                          [Sym("instances"), [Sym("project"), self.name, [Sym("path"), f"/{self.root_uuid}", [Sym("page"), str(i + 2)]]]]])
            x += 75
            if x > 700:
                x = 25.0
                y += 25
        doc = [Sym("kicad_sch"), [Sym("version"), 20231120], [Sym("generator"), "bb_gen"], [Sym("generator_version"), "1.0"],
               [Sym("uuid"), self.root_uuid], [Sym("paper"), "A2"],
               [Sym("title_block"), [Sym("title"), "Battery Bank / Travel Router - top level"], [Sym("rev"), "A"]],
               [Sym("lib_symbols")]] + items + [[Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]]]
        with open(os.path.join(outdir, f"{self.name}.kicad_sch"), "w", encoding="utf-8") as f:
            f.write(sexp.dump(doc) + "\n")

    def write(self, outdir):
        os.makedirs(outdir, exist_ok=True)
        for s in self.sheets:
            self.write_sheet(s, outdir)
        self.write_root(outdir)

    # ------------------------------------------------------------------ netlist
    def netlist(self):
        nets = {}
        for s in self.sheets:
            for part in s.parts:
                for p, net in part.resolve():
                    if net is None:
                        continue
                    nets.setdefault(net, []).append((part, p))
        return nets
