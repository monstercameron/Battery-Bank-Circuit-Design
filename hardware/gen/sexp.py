"""Minimal S-expression reader/writer for KiCad files."""
import re

_TOKEN = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))')


class Sym(str):
    """Unquoted atom."""


def parse(text):
    stack, cur = [], []
    pos = 0
    n = len(text)
    while pos < n:
        m = _TOKEN.match(text, pos)
        if not m:
            break
        pos = m.end()
        lp, rp, qs, atom = m.groups()
        if lp:
            stack.append(cur)
            cur = []
        elif rp:
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif qs is not None:
            cur.append(qs[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        elif atom is not None:
            cur.append(Sym(atom))
    return cur[0] if len(cur) == 1 else cur


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def dump(node, indent=0):
    """Serialize a nested list back to text. Strings that are not Sym are quoted."""
    if isinstance(node, list):
        if not node:
            return "()"
        head = node[0]
        simple = all(not isinstance(x, list) for x in node)
        if simple:
            return "(" + " ".join(_atom(x) for x in node) + ")"
        pad = "  " * (indent + 1)
        parts = [_atom(head)] if not isinstance(head, list) else [dump(head, indent + 1)]
        out = "(" + parts[0]
        for x in node[1:]:
            if isinstance(x, list):
                out += "\n" + pad + dump(x, indent + 1)
            else:
                out += " " + _atom(x)
        return out + ")"
    return _atom(node)


def _atom(x):
    if isinstance(x, Sym):
        return str(x)
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, (int, float)):
        return fmtnum(x)
    return q(x)


def fmtnum(v):
    if isinstance(v, int):
        return str(v)
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def find(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def find1(node, key):
    r = find(node, key)
    return r[0] if r else None
