"""Load symbols from KiCad .kicad_sym libraries and expose their pins."""
import os

import sexp
from sexp import Sym, find, find1


class LibSymbol:
    def __init__(self, lib, node):
        self.lib = lib
        self.node = node
        self.name = node[1]
        self.props = {p[1]: p[2] for p in find(node, "property")}
        self.pins = []  # dicts: number, name, x, y, angle, etype, unit
        for sub in find(node, "symbol"):
            # sub-unit name like NAME_1_1 -> unit index is the second-last field
            parts = sub[1].rsplit("_", 2)
            unit = int(parts[-2]) if len(parts) == 3 and parts[-2].isdigit() else 1
            for p in find(sub, "pin"):
                at = find1(p, "at")
                self.pins.append({
                    "etype": str(p[1]),
                    "x": float(at[1]), "y": float(at[2]), "angle": float(at[3]) if len(at) > 3 else 0.0,
                    "length": float(find1(p, "length")[1]) if find1(p, "length") else 2.54,
                    "name": find1(p, "name")[1],
                    "number": find1(p, "number")[1],
                    "unit": unit,
                })
        xs = [p["x"] for p in self.pins] or [0]
        ys = [p["y"] for p in self.pins] or [0]
        self.bbox = (min(xs), min(ys), max(xs), max(ys))

    @property
    def lib_id(self):
        return f"{self.lib}:{self.name}"

    def embedded(self):
        """Return the symbol node renamed with the library prefix, for a schematic's lib_symbols."""
        node = [Sym("symbol"), self.lib_id] + [x for x in self.node[2:]]
        return node

    def pins_named(self, name):
        return [p for p in self.pins if p["name"] == name]

    def pin_by_number(self, num):
        for p in self.pins:
            if p["number"] == str(num):
                return p
        return None


class Library:
    def __init__(self, path, nickname):
        with open(path, encoding="utf-8") as f:
            root = sexp.parse(f.read())
        self.nickname = nickname
        self.symbols = {}
        for s in find(root, "symbol"):
            ls = LibSymbol(nickname, s)
            self.symbols[ls.name] = ls

    def get(self, name):
        return self.symbols[name]


def load_lcsc():
    here = os.path.dirname(os.path.abspath(__file__))
    return Library(os.path.join(here, "..", "lib", "lcsc.kicad_sym"), "lcsc")


if __name__ == "__main__":
    import sys
    lib = load_lcsc()
    names = sys.argv[1:] or sorted(lib.symbols)
    for n in names:
        s = lib.symbols[n]
        print(f"\n## {n}  ({len(s.pins)} pins)  fp={s.props.get('Footprint')}")
        print("   " + ", ".join(f"{p['number']}:{p['name']}" for p in sorted(s.pins, key=lambda p: (len(p['number']), p['number']))))
