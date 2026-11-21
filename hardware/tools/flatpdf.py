"""Decrypt (RC4 R2/R3, empty user password) + flatten object streams into a simple PDF-like file that pdftxt.py can read."""
import hashlib
import re
import sys
import zlib

PAD = bytes.fromhex("28BF4E5E4E758A4164004E56FFFA01082E2E00B6D0683E802F0CA9FE6453697A")


def rc4(key, data):
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 255
        S[i], S[j] = S[j], S[i]
    i = j = 0
    out = bytearray(len(data))
    for k, b in enumerate(data):
        i = (i + 1) & 255
        j = (j + S[i]) & 255
        S[i], S[j] = S[j], S[i]
        out[k] = b ^ S[(S[i] + S[j]) & 255]
    return bytes(out)


def pdfstr(raw):
    # parse literal string bytes (raw includes parentheses content)
    out = bytearray()
    i = 0
    while i < len(raw):
        c = raw[i]
        if c == 0x5C:
            i += 1
            n = raw[i]
            if 0x30 <= n <= 0x37:
                s = bytes([n])
                while len(s) < 3 and i + 1 < len(raw) and 0x30 <= raw[i + 1] <= 0x37:
                    i += 1
                    s += bytes([raw[i]])
                out.append(int(s, 8) & 255)
            else:
                out += {ord('n'): b'\n', ord('r'): b'\r', ord('t'): b'\t', ord('b'): b'\b', ord('f'): b'\f'}.get(n, bytes([n]))
        else:
            out.append(c)
        i += 1
    return bytes(out)


def get_str(enc, key):
    m = re.search(rb'/' + key + rb'\s*<([0-9A-Fa-f]+)>', enc)
    if m:
        return bytes.fromhex(m.group(1).decode())
    m = re.search(rb'/' + key + rb'\s*\(', enc)
    i = m.end()
    depth = 1
    j = i
    while depth:
        if enc[j] == 0x5C:
            j += 2
            continue
        if enc[j] == 0x28:
            depth += 1
        elif enc[j] == 0x29:
            depth -= 1
        j += 1
    return pdfstr(enc[i:j - 1])


def main(src, dst):
    d = open(src, 'rb').read()
    key = None
    me = re.search(rb'/Encrypt\s+(\d+)\s+0\s+R', d)
    if me:
        en = int(me.group(1))
        mo = re.search(rb'[^0-9]' + str(en).encode() + rb'\s+0\s+obj(.*?)endobj', d, re.S)
        enc = mo.group(1)
        O = get_str(enc, b'O')[:32]
        P = int(re.search(rb'/P\s*(-?\d+)', enc).group(1))
        R = int(re.search(rb'/R\s*(\d+)', enc).group(1))
        L = int(re.search(rb'/Length\s*(\d+)', enc).group(1)) if re.search(rb'/Length\s*(\d+)', enc) else 40
        ids = re.findall(rb'/ID\s*\[\s*<([0-9A-Fa-f]+)>', d)
        if ids:
            ID = bytes.fromhex(ids[-1].decode())
        else:
            mi = re.search(rb'/ID\s*\[\s*\(', d)
            # literal string ID
            i = mi.end(); j = i; depth = 1
            while depth:
                if d[j] == 0x5C:
                    j += 2; continue
                if d[j] == 0x28: depth += 1
                elif d[j] == 0x29: depth -= 1
                j += 1
            ID = pdfstr(d[i:j - 1])
        n = L // 8
        h = hashlib.md5(PAD + O + (P & 0xFFFFFFFF).to_bytes(4, 'little') + ID)
        k = h.digest()
        if R >= 3:
            for _ in range(50):
                k = hashlib.md5(k[:n]).digest()
        key = k[:n]
        print('key', key.hex(), 'R', R, 'n', n, file=sys.stderr)
    objs = {}
    for mo in re.finditer(rb'(?<![0-9])(\d+)\s+(\d+)\s+obj(.*?)endobj', d, re.S):
        objs[int(mo.group(1))] = (int(mo.group(2)), mo.group(3))

    def stream(num, gen, body):
        s = re.search(rb'stream\r?\n', body)
        if not s:
            return None, body
        e = body.rfind(b'endstream')
        raw = body[s.end():e]
        head = body[:s.start()]
        if key and b'/XRef' not in head:
            ok = key + num.to_bytes(4, 'little')[:3] + gen.to_bytes(2, 'little')
            raw = rc4(hashlib.md5(ok).digest()[:min(len(key) + 5, 16)], raw)
        if b'FlateDecode' in head:
            try:
                raw = zlib.decompressobj().decompress(raw)
            except Exception:
                return None, head
        return raw, head

    flat = {}
    for num, (gen, body) in objs.items():
        data, head = stream(num, gen, body)
        if data is None:
            flat[num] = body
            continue
        if b'/ObjStm' in head:
            N = int(re.search(rb'/N\s+(\d+)', head).group(1))
            First = int(re.search(rb'/First\s+(\d+)', head).group(1))
            nums = list(map(int, data[:First].split()))
            pairs = [(nums[2 * i], nums[2 * i + 1]) for i in range(N)]
            for i, (on, off) in enumerate(pairs):
                end = pairs[i + 1][1] if i + 1 < N else len(data) - First
                if on not in flat:
                    flat[on] = data[First + off:First + end]
            continue
        head2 = head.replace(b'/FlateDecode', b'')
        flat[num] = head2 + b'\nstream\n' + data + b'\nendstream\n'
    with open(dst, 'wb') as f:
        for num in sorted(flat):
            f.write(b'\n%d 0 obj\n' % num + flat[num] + b'\nendobj\n')


main(sys.argv[1], sys.argv[2])
