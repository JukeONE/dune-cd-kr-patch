import struct, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import bdf
COLOR = 118
def render(text, g, asc, top=2, h=9):
    xs = []; x = 0
    for ch in text:
        cp = ord(ch); gl = g.get(cp) or g[ord('?')]
        for px, py in gl['px']:
            y = asc - gl['yo'] - gl['h'] + py - top
            if 0 <= y < h: xs.append((x + px, y))
        x += gl['dw']
    w = max(1, x)
    rows = [bytearray(w) for _ in range(h)]
    for px, py in xs:
        if 0 <= px < w: rows[py][px] = COLOR
    # trim right blank columns
    while w > 1 and all(r[w-1] == 0 for r in rows): w -= 1
    pad = max(0, (320 - w) // 2)
    return w + pad, [bytearray(pad) + r[:w] for r in rows]
def rle_row(r):
    out = bytearray(); i = 0; lit = bytearray()
    def flush():
        nonlocal lit
        while lit:
            chunk = lit[:128]; out.append(len(chunk) - 1); out.extend(chunk); lit = lit[128:]
    while i < len(r):
        j = i
        while j < len(r) and r[j] == r[i] and j - i < 129: j += 1
        n = j - i
        if n >= 3:
            flush(); out.append(257 - n); out.append(r[i]); i = j
        else:
            lit.extend(r[i:j]); i = j
    flush(); return bytes(out)
def build(lines, g, asc):
    sprites = []
    for t in lines:
        w, rows = render(t, g, asc)
        s = struct.pack('<HBB', 0x8000 | w, len(rows), 0xfe) + b''.join(rle_row(r) for r in rows)
        sprites.append(s)
    n = len(sprites); table = []; body = bytearray(); base = 2 * n
    for s in sprites: table.append(base + len(body)); body += s
    return struct.pack('<H', 2) + struct.pack('<%dH' % n, *table) + bytes(body)
