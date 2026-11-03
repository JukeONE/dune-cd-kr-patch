"""원본 대비 차이 데이터(patch.json) 생성: EXE와 DNCHAR.BIN은 사용자 원본에 적용"""
import json, hashlib, base64, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import dat
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def chunks(orig, new):
    out = []; i = 0; n = len(new)
    while i < n:
        if (orig[i] if i < len(orig) else 0) == new[i]: i += 1; continue
        j = i
        ref = lambda k: orig[k:k+8] + bytes(max(0, 8 - len(orig[k:k+8])))
        while j < n and not (ref(j)[:len(new[j:j+8])] == new[j:j+8]): j += 1
        out.append({'o': i, 'd': base64.b64encode(new[i:j]).decode()}); i = j
    return out
def entry(orig, new):
    return {'md5': hashlib.md5(orig).hexdigest(), 'size': len(orig), 'newSize': len(new), 'chunks': chunks(orig, new)}
oexe = open(os.path.join(ROOT, 'orig', 'dncdprg.exe'), 'rb').read()
nexe = open(os.path.join(ROOT, 'out', 'DNCDPRG.EXE'), 'rb').read()
odch = open(os.path.join(ROOT, 'x', 'DNCHAR.BIN'), 'rb').read()
ndch = open(os.path.join(ROOT, 'out', 'DNCHAR.BIN'), 'rb').read()
p = {'exe': entry(oexe, nexe), 'dat': {'DNCHAR.BIN': entry(odch, ndch)}}
# self-check
def apply(o, e):
    b = bytearray(o[:e['newSize']]) + bytearray(max(0, e['newSize'] - len(o)))
    for c in e['chunks']:
        d = base64.b64decode(c['d']); b[c['o']:c['o']+len(d)] = d
    return bytes(b)
assert apply(oexe, p['exe']) == nexe and apply(odch, p['dat']['DNCHAR.BIN']) == ndch
out = sys.argv[1]
json.dump(p, open(out, 'w'), separators=(',', ':'))
print('exe chunks', len(p['exe']['chunks']), 'dchar chunks', len(p['dat']['DNCHAR.BIN']['chunks']), os.path.getsize(out))
