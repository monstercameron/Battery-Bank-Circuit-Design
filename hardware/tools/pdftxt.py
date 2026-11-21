import sys, re, zlib

def parse_cmap(d):
    m = {}
    w = 1
    for blk in re.findall(rb'beginbfchar(.*?)endbfchar', d, re.S):
        for a, b in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', blk):
            w = len(a) // 2
            try:
                m[int(a, 16)] = bytes.fromhex(b.decode()).decode('utf-16-be', 'ignore')
            except Exception:
                pass
    for blk in re.findall(rb'beginbfrange(.*?)endbfrange', d, re.S):
        for a, b, c in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', blk):
            w = len(a) // 2
            lo, hi, base = int(a, 16), int(b, 16), int(c, 16)
            for i in range(lo, min(hi, lo + 5000) + 1):
                try:
                    m[i] = chr(base + i - lo)
                except Exception:
                    pass
    return m, w

def main(path):
    data = open(path, 'rb').read()
    objs = {}
    for mo in re.finditer(rb'(\d+)\s+0\s+obj(.*?)endobj', data, re.S):
        objs[int(mo.group(1))] = mo.group(2)
    def stream_of(body):
        s = re.search(rb'stream\r?\n(.*)endstream', body, re.S)
        if not s:
            return None
        raw = s.group(1)
        if b'FlateDecode' in body[:s.start()]:
            try:
                return zlib.decompressobj().decompress(raw)
            except Exception:
                return None
        return raw
    # font object -> cmap
    fontcmap = {}
    for n, body in objs.items():
        mt = re.search(rb'/ToUnicode\s+(\d+)\s+0\s+R', body)
        if mt and b'/Font' in body:
            tu = objs.get(int(mt.group(1)))
            if tu:
                d = stream_of(tu)
                if d:
                    fontcmap[n] = parse_cmap(d)
    # resource name -> font obj (global, last wins) ; also page-specific
    pages = []
    for n, body in objs.items():
        if re.search(rb'/Type\s*/Page[^s]', body):
            pages.append((n, body))
    def fontmap_for(body):
        fm = {}
        fd = re.search(rb'/Font\s*<<(.*?)>>', body, re.S)
        if not fd:
            mr = re.search(rb'/Resources\s+(\d+)\s+0\s+R', body)
            if mr:
                rb_ = objs.get(int(mr.group(1)), b'')
                fd = re.search(rb'/Font\s*<<(.*?)>>', rb_, re.S)
                if not fd:
                    mf = re.search(rb'/Font\s+(\d+)\s+0\s+R', rb_)
                    if mf:
                        fd = re.search(rb'<<(.*?)>>', objs.get(int(mf.group(1)), b''), re.S)
        if fd:
            for name, num in re.findall(rb'/([\w.+-]+)\s+(\d+)\s+0\s+R', fd.group(1)):
                fm[name] = int(num)
        return fm
    out = []
    pages.sort()
    for n, body in pages:
        fm = fontmap_for(body)
        cs = re.search(rb'/Contents\s*(\[[^\]]*\]|\d+\s+0\s+R)', body)
        if not cs:
            continue
        refs = [int(x) for x in re.findall(rb'(\d+)\s+0\s+R', cs.group(1))]
        content = b''
        for r in refs:
            d = stream_of(objs.get(r, b''))
            if d:
                content += d + b'\n'
        cur = None
        line = []
        for tok in re.finditer(rb'/([\w.+-]+)\s+[\d.]+\s+Tf|\((?:\\.|[^\\)])*\)|<[0-9A-Fa-f\s]*>|\bET\b|\bT\*|\bTd\b|\bTD\b', content):
            t = tok.group(0)
            if tok.group(1):
                f = fm.get(tok.group(1))
                cur = fontcmap.get(f)
            elif t.startswith(b'('):
                s = t[1:-1]
                s = re.sub(rb'\\([0-7]{1,3})', lambda m: bytes([int(m.group(1), 8) & 255]), s)
                s = re.sub(rb'\\(.)', rb'\1', s)
                if cur:
                    cm, w = cur
                    if w == 2:
                        line.append(''.join(cm.get(int.from_bytes(s[i:i+2], 'big'), '') for i in range(0, len(s) - 1, 2)))
                    else:
                        line.append(''.join(cm.get(b, chr(b)) for b in s))
                else:
                    line.append(s.decode('latin-1'))
            elif t.startswith(b'<'):
                h = re.sub(rb'\s', b'', t[1:-1]).decode()
                if cur:
                    cm, w = cur
                    st = 2 * w
                    line.append(''.join(cm.get(int(h[i:i+st], 16), '') for i in range(0, len(h), st)))
            else:
                line.append(' ')
                if t == b'ET':
                    out.append(''.join(line)); line = []
        out.append(''.join(line))
    sys.stdout.reconfigure(encoding='utf-8')
    print('\n'.join(out))

main(sys.argv[1])
