"""빌드 준비: 원본 Dune CD 폴더에서 dune.dat 을 풀고(x/), HSQ 를 압축 해제(u/), 원본 실행 파일을 orig/ 에 복사"""
import os, sys, shutil
sys.path.insert(0, os.path.dirname(__file__))
import dat, hsq
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
game = sys.argv[1]
for d in ('x', 'u', 'orig', 'out'): os.makedirs(os.path.join(ROOT, d), exist_ok=True)
shutil.copy(os.path.join(game, 'dncdprg.exe'), os.path.join(ROOT, 'orig', 'dncdprg.exe'))
with open(os.path.join(game, 'dune.dat'), 'rb') as f:
    for name, size, off, _ in dat.read_index(f):
        if not name or name.upper().endswith('.VOC'): continue
        f.seek(off); data = f.read(size)
        open(os.path.join(ROOT, 'x', name), 'wb').write(data)
        if name.upper().endswith('.HSQ'):
            open(os.path.join(ROOT, 'u', name[:-4] + '.BIN'), 'wb').write(hsq.unhsq(data))
print('done')
