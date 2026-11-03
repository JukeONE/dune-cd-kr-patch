import sys, os, struct, re, subprocess, json
sys.path.insert(0, os.path.dirname(__file__))
import bdf, hsq, phrase

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
U = os.path.join(ROOT, 'u'); X = os.path.join(ROOT, 'x'); KO = os.path.join(ROOT, 'ko')
OUT = os.path.join(ROOT, 'out'); os.makedirs(OUT, exist_ok=True)

LEADS = list(range(0x09, 0x0D)) + list(range(0x0E, 0x20)) + [ord(c) for c in '#$;@&']
TRAILS = [c for c in range(0x41, 0x5B) if chr(c) not in 'ACDELOPST'] + list(range(0x61, 0x7B)) + [ord(c) for c in '[\\]^_`{|}~']
NT = len(TRAILS)
SPECIAL = set(LEADS) | set(TRAILS)

def parse_escapes(s):
    """returns list of tokens: ('b', byte) or ('c', unicode char)"""
    out = []; i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            n = s[i+1]
            if n == 'x': out.append(('b', int(s[i+2:i+4], 16))); i += 4; continue
            if n == 'r': out.append(('b', 13)); i += 2; continue
            if n == '\\': out.append(('c', '\\')); i += 2; continue
        out.append(('c', s[i])); i += 1
    return out

def load_ko(fn):
    d = {}
    if not os.path.exists(fn): return d
    for line in open(fn, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line.strip() or line.startswith('#'): continue
        k, v = line.split('\t', 1)
        d[int(k)] = v
    return d

def syllables_in(texts):
    s = set()
    for t in texts:
        for kind, v in parse_escapes(t):
            if kind == 'c' and 0xAC00 <= ord(v) <= 0xD7A3: s.add(v)
    return s

def encode(text, smap):
    toks = parse_escapes(text); out = bytearray(); i = 0
    while i < len(toks):
        kind, v = toks[i]
        if kind == 'b':
            out.append(v)
            # variable parameters are copied raw
            if v == 0x80:
                for k in (1, 2):
                    kk, vv = toks[i+k]; out.append(vv if kk == 'b' else ord(vv))
                i += 3; continue
            if v in (0x91, 0x92):
                kk, vv = toks[i+1]; out.append(vv if kk == 'b' else ord(vv)); i += 2; continue
            i += 1; continue
        if 0xAC00 <= ord(v) <= 0xD7A3:
            out += bytes(smap[v])
        else:
            c = ord(v)
            if c > 0x7e or c in SPECIAL:
                raise ValueError('unsupported char %r in %r' % (v, text))
            out.append(c)
        i += 1
    return bytes(out)

def build_phrase(orig_bin, ko, smap, placeholder):
    offs, strs = phrase.parse(orig_bin)
    new = []
    for i, s in enumerate(strs):
        if i in ko: new.append(encode(ko[i], smap))
        elif placeholder is None: new.append(s)
        else: new.append(encode(placeholder % i, smap))
    n = len(strs); body = bytearray(); table = []
    base = n * 2
    for s in new:
        table.append(base + len(body)); body += s + b'\xff'
    tail = orig_bin[offs[-1]:]; tail = tail[tail.index(b'\xff')+1:]   # keep trailing bytes
    return struct.pack('<%dH' % n, *table) + bytes(body) + tail

def glyph_tables(sylls):
    g9, a9 = bdf.load(os.path.join(ROOT, 'font/Galmuri9.bdf'))
    g7, a7 = bdf.load(os.path.join(ROOT, 'font/Galmuri7.bdf'))
    dalp = os.path.join(ROOT, 'font', 'dalmoori8.json')
    DAL = json.load(open(dalp, encoding='utf-8')) if os.path.exists(dalp) else {}
    miss = [c for c in sylls if c not in DAL]
    if miss:   # regenerate Dalmoori glyphs for new syllables
        gd = os.path.join(ROOT, 'dalgen')
        json.dump(miss, open(os.path.join(gd, 'miss.json'), 'w'))
        subprocess.check_call(['node', '--experimental-transform-types', '--no-warnings', 'gen.ts', 'miss.json', 'miss_out.json'], cwd=gd)
        for ch, v in json.load(open(os.path.join(gd, 'miss_out.json'))).items():
            DAL[ch] = [[1 if c == '#' else 0 for c in r.split()] for r in v.strip().split('\n')]
        json.dump(DAL, open(dalp, 'w', encoding='utf-8'))
    L = bytearray(); R = bytearray(); S = bytearray(); B7 = bytearray(); GD = bytearray()
    for ch in sylls:
        g = g9[ord(ch)]; top = a9 - g['yo'] - g['h'] - 2
        rows = [0]*9
        for x, y in g['px']:
            rows[top + y] |= 1 << (15 - x)
        L += bytes(r >> 8 for r in rows); R += bytes((r << 8 & 0xff00) >> 8 for r in rows)
        dm = DAL[ch]
        GD.extend(bytes(sum(v << (7 - x) for x, v in enumerate(r)) for r in dm) + b'\0')
        g = g7[ord(ch)]; top = a7 - g['yo'] - g['h'] - 2
        rows = [0]*9
        for x, y in g['px']:
            rows[top + y] |= 1 << (7 - x)
        B7.extend(rows)
        g = g7[ord(ch)]; top = a7 - g['yo'] - g['h'] - 2
        rows = [0]*7
        for x, y in g['px']:
            rows[top + y] |= 1 << (7 - x)
        S += bytes(rows)
    open(os.path.join(ROOT, 'asm', 'g7b.bin'), 'wb').write(bytes(B7))
    open(os.path.join(ROOT, 'asm', 'gd.bin'), 'wb').write(bytes(GD))
    return bytes(L), bytes(R), bytes(S)

def main():
    cmd_ko = load_ko(os.path.join(KO, 'command.txt'))
    p1 = load_ko(os.path.join(KO, 'phrase1.txt')); p2 = load_ko(os.path.join(KO, 'phrase2.txt'))
    PH = '(미번역 %d)'
    texts = list(cmd_ko.values()) + list(p1.values()) + list(p2.values()) + [PH % 0]
    sylls = sorted(syllables_in(texts))
    if len(sylls) > len(LEADS) * NT: raise SystemExit('too many syllables %d' % len(sylls))
    smap = {ch: (LEADS[i // NT], TRAILS[i % NT]) for i, ch in enumerate(sylls)}
    print('syllables', len(sylls), 'capacity', len(LEADS) * NT)

    files = {}
    cmd = build_phrase(open(os.path.join(U, 'COMMAND1.BIN'), 'rb').read(), cmd_ko, smap, None)
    ph1 = build_phrase(open(os.path.join(U, 'PHRASE11.BIN'), 'rb').read(), p1, smap, PH)
    ph2 = build_phrase(open(os.path.join(U, 'PHRASE12.BIN'), 'rb').read(), p2, smap, PH)
    for n, d in [('COMMAND1', cmd), ('COMMAND4', cmd), ('PHRASE11', ph1), ('PHRASE41', ph1), ('PHRASE12', ph2), ('PHRASE42', ph2)]:
        c = hsq.hsq_literal(d); assert hsq.unhsq(c) == d
        files[n + '.HSQ'] = c

    import irul
    g9i, a9i = bdf.load(os.path.join(ROOT, 'font/Galmuri9.bdf'))
    il = [l.rstrip('\n').split('\t', 1)[1] for l in open(os.path.join(KO, 'irulan.txt'), encoding='utf-8') if l.strip()]
    ir = irul.build(il, g9i, a9i); c = hsq.hsq_literal(ir); assert hsq.unhsq(c) == ir
    files['IRUL1.HSQ'] = c; files['IRUL4.HSQ'] = c

    # font widths
    fnt = bytearray(open(os.path.join(X, 'DNCHAR.BIN'), 'rb').read())
    for c in LEADS: fnt[c] = 0; fnt[128 + c] = 0
    for c in TRAILS: fnt[c] = 10; fnt[128 + c] = 8
    files['DNCHAR.BIN'] = bytes(fnt)

    # hook segment
    L, R, S = glyph_tables(sylls)
    lt = [0xff]*256; tt = [0xff]*256
    for i, c in enumerate(LEADS): lt[c] = i
    for i, c in enumerate(TRAILS): tt[c] = i
    asm = os.path.join(ROOT, 'asm')
    open(os.path.join(asm, 'g9l.bin'), 'wb').write(L); open(os.path.join(asm, 'g9r.bin'), 'wb').write(R); open(os.path.join(asm, 'g7.bin'), 'wb').write(S)
    with open(os.path.join(asm, 'tables.inc'), 'w') as f:
        f.write('NT equ %d\n' % NT)
        f.write('dw big_draw, small_draw\n')
        f.write('leadtab: db %s\n' % ','.join(map(str, lt)))
        f.write('trailtab: db %s\n' % ','.join(map(str, tt)))
        f.write('g9l: incbin "g9l.bin"\ng9r: incbin "g9r.bin"\ng7: incbin "g7.bin"\ng7b: incbin "g7b.bin"\ngd: incbin "gd.bin"\n')
    subprocess.check_call(['nasm', '-f', 'bin', '-o', 'hook.bin', '-l', 'hook.lst', 'hook.asm'], cwd=asm)
    hook = open(os.path.join(asm, 'hook.bin'), 'rb').read()
    lst = open(os.path.join(asm, 'hook.lst')).read()
    def sym(name):
        m = re.search(r'^\s*\d+\s+([0-9A-F]{8})\s+(?:\S+\s+)?%s:' % name, lst, re.M)
        return int(m.group(1), 16)
    big, small = struct.unpack_from('<HH', hook, 0)

    # EXE patch
    exe = bytearray(open(os.path.join(ROOT, 'orig', 'dncdprg.exe'), 'rb').read())
    hdr = 512; img = bytearray(exe[hdr:])
    DSB = 0xF4B0; SEGOFF = DSB + 0xDD20; SEGPARA = SEGOFF >> 4
    assert len(img) <= SEGOFF
    img += b'\0' * (SEGOFF - len(img)); img += hook
    img += b'\0' * (-len(img) % 16)
    def patch(at, old, new):
        assert img[at:at+len(old)] == old, (hex(at), img[at:at+len(old)].hex())
        img[at:at+len(new)] = new
    patch(0xD096, bytes.fromhex('505351525657550632e4'), b'\x9a' + struct.pack('<HH', big, SEGPARA) + b'\xc3')
    patch(0xD12F, bytes.fromhex('505351525657550632e4'), b'\x9a' + struct.pack('<HH', small, SEGPARA) + b'\xc3')
    # ordinal suffix table (lang 0 and 3): 4 entries x 2 bytes -> '일'
    il = bytes(smap['일'])
    for lang in (0, 3):
        at = DSB + 0x251a + lang * 8
        assert img[at:at+8] == b'thstndrd', img[at:at+8]
        img[at:at+8] = il * 4
    # left-align dialogue: no extra space distribution (space = 6px, remainder 0)
    patch(0x8C2A, bytes.fromhex('03162cd8833e9c4700740542ff0e9c47'), bytes.fromhex('ba0600') + bytes.fromhex('03162cd8') + b'\x90' * 9)
    hook_paras = (len(hook) + 15) >> 4
    patch(0xE5AE, bytes.fromhex('b91ddde84b0b'), b'\x81\x06\xb9\x39' + struct.pack('<H', 0xDD2 + hook_paras + 1))
    # header
    h = bytearray(exe[:hdr])
    nrel, relo = struct.unpack_from('<H', h, 6)[0], struct.unpack_from('<H', h, 0x18)[0]
    for off in (0xD096 + 3, 0xD12F + 3):
        struct.pack_into('<HH', h, relo + 4 * nrel, off, 0); nrel += 1
    assert relo + 4 * nrel <= hdr
    struct.pack_into('<H', h, 6, nrel)
    total = hdr + len(img)
    struct.pack_into('<HH', h, 2, total % 512, (total + 511) // 512)
    struct.pack_into('<H', h, 0x0a, 0x40)  # minalloc
    files['DNCDPRG.EXE'] = bytes(h + img)
    for n, d in files.items(): open(os.path.join(OUT, n), 'wb').write(d)
    json.dump({'syllables': len(sylls), 'hook': len(hook), 'big': big, 'small': small}, open(os.path.join(OUT, 'info.json'), 'w'))
    print('hook bytes', len(hook), 'big', hex(big), 'small', hex(small), 'exe', len(files['DNCDPRG.EXE']))

if __name__ == '__main__':
    main()
