#!/usr/bin/env python3
"""Copy hardware/mechanical/mech_spec.json into docs/assets/ for the GitHub Pages 3D model.

GitHub Pages serves only docs/, so the viewer (docs/assets/device3d.js) cannot fetch the
spec from hardware/. Run this after every change to mech_spec.json:

    python docs/assets/sync_mech_spec.py

It writes docs/assets/mech_spec.json (fetched by the viewer) and refreshes the inline
fallback copy between /*SPEC-BEGIN*/ and /*SPEC-END*/ in device3d.js, so the model still
renders if the fetch fails. Pass --check to only report whether the copies are stale
(exit code 1 if they are), e.g. in CI.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent.parent / "hardware" / "mechanical" / "mech_spec.json"
DST = HERE / "mech_spec.json"
JS = HERE / "device3d.js"
MARK = re.compile(r"/\*SPEC-BEGIN\*/.*?/\*SPEC-END\*/", re.S)


def main() -> int:
    check = "--check" in sys.argv[1:]
    spec = json.loads(SRC.read_text(encoding="utf-8"))  # validates the JSON
    pretty = json.dumps(spec, indent=2, ensure_ascii=False) + "\n"
    inline = "/*SPEC-BEGIN*/" + json.dumps(spec, separators=(",", ":"), ensure_ascii=True) + "/*SPEC-END*/"
    js = JS.read_text(encoding="utf-8")
    if not MARK.search(js):
        print(f"error: no /*SPEC-BEGIN*/.../*SPEC-END*/ marker in {JS}", file=sys.stderr)
        return 2
    new_js = MARK.sub(lambda _m: inline, js, count=1)
    stale = [p.name for p, new in ((DST, pretty), (JS, new_js))
             if not p.exists() or p.read_text(encoding="utf-8") != new]
    if check:
        print("stale: " + ", ".join(stale) if stale else "mech_spec copies are up to date")
        return 1 if stale else 0
    DST.write_text(pretty, encoding="utf-8", newline="\n")
    JS.write_text(new_js, encoding="utf-8", newline="\n")
    print(f"synced {SRC.name} (rev {spec.get('rev')}) -> {DST.relative_to(HERE.parent.parent)} and inline fallback in {JS.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
