"""Search extracted datasheet text with context: python dsgrep.py <file-stem> <regex> [window] [max]"""
import os
import re
import sys

base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "datasheets", "text")
stem, pat = sys.argv[1], sys.argv[2]
win = int(sys.argv[3]) if len(sys.argv) > 3 else 300
mx = int(sys.argv[4]) if len(sys.argv) > 4 else 5
t = open(os.path.join(base, stem + ".txt"), encoding="utf-8", errors="ignore").read()
t = re.sub(r"\s+", " ", t)
for i, m in enumerate(re.finditer(pat, t, re.I)):
    if i >= mx:
        break
    s = max(0, m.start() - win // 3)
    print(f"--- [{m.start()}] ...{t[s:m.end() + win]}...\n")
