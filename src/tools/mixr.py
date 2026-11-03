# MIXR (Mixer Panel) Korean localization
import sys,struct,os
sys.path.insert(0,os.path.dirname(__file__))
from spr import sheet
from bdf import load
from irul import rle_row
def dec(d,o):
    w0,h,pal=struct.unpack_from('<HBB',d,o); rle=w0&0x8000; w=w0&0x7fff; p=o+4
    rb=(w+1)//2; rb+=rb&1; rows=[]
    for y in range(h):
        row=bytearray()
        if rle:
            while len(row)<rb:
                c=d[p]; p+=1
                if c&0x80: row+=bytes([d[p]])*(257-c); p+=1
                else: row+=d[p:p+c+1]; p+=c+1
        else: row+=d[p:p+rb]; p+=rb
        px=[]
        for b in row: px+=[b&15,b>>4]
        rows.append(px)   # keep padding pixels
    return dict(w=w,h=h,pal=pal,rle=bool(rle),rows=rows)
def enc(s):
    out=struct.pack('<HBB',s['w']|(0x8000 if s['rle'] else 0),s['h'],s['pal'])
    for r in s['rows']:
        b=bytes(r[i]|(r[i+1]<<4) for i in range(0,len(r),2))
        out+=rle_row(b) if s['rle'] else b
    return out
# 6px 손글씨 한글 (믹서 오른쪽 아래 버튼용 — 7px 피치에 1줄 간격 확보)
G6={
'자':["###.#.",
      ".#..#.",
      ".#..##",
      "#.#.#.",
      "#.#.#.",
      "....#."],
'막':["###.#.",
      "#.#.##",
      "###.#.",
      "......",
      "#####.",
      "....#."],
'말':["###.#.",
      "###.##",
      "......",
      "####..",
      ".##...",
      "####.."],
'풍':["#####",
      ".#.#.",
      "#####",
      "..#..",
      ".###.",
      ".###."],
'선':[".#..#",
      ".#.##",
      "#.#.#",
      ".....",
      "#....",
      "####."],
'없':[".##..#.",
      "#..###.",
      ".##..#.",
      ".......",
      "#.#..#.",
      "###.#.#"],
'음':["..##..",
      ".#..#.",
      "..##..",
      "######",
      ".#..#.",
      ".####."],
'선':[".#...#",
      ".#..##",
      "#.#..#",
      "......",
      ".#....",
      ".####."],
}

def text6(text):
    pts=[];x=0
    for ch in text:
        if ch==' ': x+=3; continue
        for y,r in enumerate(G6[ch]):
            for i,c in enumerate(r):
                if c=='#': pts.append((x+i,y))
        x+=len(G6[ch][0])+1
    return pts,max(p[0] for p in pts)+1
def text_px(g,text):
    pts=[];x=0
    for ch in text:
        if ch==' ': x+=4; continue
        G=g[ord(ch)]
        for (px,py) in G['px']: pts.append((x+px,py))
        x+=G['dw']
    w=max(p[0] for p in pts)+1
    return pts,w
import json
# 오른쪽 아래 버튼은 줄 간격이 7픽셀이라 달무리 8픽셀에서 2줄씩 빼서 6줄로 만든다
DROP6={'자':[6,7],'막':[2,7],'말':[2,6],'선':[4,5],'없':[2,5]}
HAND6={'풍':[".#####.",
             "..#.#..",
             "#######",
             "...#...",
             "..###..",
             "..###.."],
       '음':["..###..",
             ".#...#.",
             "..###..",
             "#######",
             ".#...#.",
             ".#####."]}
def textd(J,text,drop=None):
    pts=[];x=0
    for ch in text:
        if ch==' ': x+=4; continue
        if drop is not None and ch in HAND6: rows=[[c=='#' for c in r]+[0] for r in HAND6[ch]]
        else: rows=[r for y,r in enumerate(J[ch]) if y not in (drop or {}).get(ch,())]
        for y,r in enumerate(rows):
            for i in range(8):
                if r[i]: pts.append((x+i,y))
        x+=9 if drop is not None else 8
    return pts,max(p[0] for p in pts)+1
def build(src,fontfn):
    d=open(src,'rb').read()
    t,offs=sheet(d); S=[dec(d,o) for o in offs]
    J=json.load(open(fontfn,encoding='utf-8'))
    P=S[0]['rows']
    # ---- top labels (text A + shadow, background 1)
    def label(boxes,shadow,lines):
        xs=[];
        for (x0,x1,y0,y1) in boxes:
          for y in range(y0,y1+1):
            for x in range(x0,x1+1):
                if P[y][x] in (0xA,shadow): xs.append(x); P[y][x]=1
        cx=(min(xs)+max(xs)+1)//2
        for (text,ty) in lines:
            pts,w=textd(J,text); left=cx-w//2
            S_=set((left+px,ty+py) for px,py in pts)
            for (x,y) in S_: P[y][x]=0xA
            for (x,y) in S_:
                if (x+1,y) not in S_: P[y][x+1]=shadow
    label([(4,44,25,33)],5,[('음성',24)])
    label([(45,72,15,25)],6,[('음악',15)])
    label([(73,117,15,25),(73,133,26,33)],6,[('음성 중',15),('음악',24)])
    # ---- subtitle buttons 44..49 (sel/unsel pairs)
    texts={44:'자막',45:'자막',46:'말풍선',47:'말풍선',48:'자막없음',49:'자막없음'}
    selgrad=[0xF,0xF,0xE,0xE,0xC,0xC,0xA]
    origs={i:[r[:] for r in S[i]['rows']] for i in texts}
    for i,text in texts.items():
        R=S[i]['rows']; w=S[i]['w']
        U=origs[i|1]
        inner=[x for x in range(w) if U[0][x]==3 and U[6][x]==3]
        txt=[x for x in inner if any(U[y][x]!=3 for y in range(7))]
        ta,tb=min(txt),max(txt)
        for y in range(7):
            for x in range(ta,tb+1): R[y][x]=3
        a,b=min(inner),max(inner)
        pts,tw=textd(J,text,DROP6)
        left=(a+b+1-tw)//2
        for px,py in pts:
            R[py+1][left+px]= selgrad[py+1] if i%2==0 else 8
    # paste unselected versions into panel where originals match
    for i in (45,47,49):
        o=origs[i]; w=S[i]['w']; h=7; found=None
        for py in range(len(P)-h+1):
            for px in range(S[0]['w']-w+1):
                if all(P[py+y][px+x]==o[y][x] for y in range(h) for x in range(w)):
                    found=(px,py); break
            if found: break
        assert found,i
        px,py=found
        for y in range(h):
            for x in range(w): P[py+y][px+x]=S[i]['rows'][y][x]
    # rebuild
    ends=offs[1:]+[len(d)]
    blobs=[enc(s) if k in (0,44,45,46,47,48,49) else d[offs[k]:ends[k]] for k,s in enumerate(S)]
    n=len(blobs); body=bytearray(); tab=[]
    for b in blobs: tab.append(2*n+len(body)); body+=b
    return struct.pack('<H',2)+struct.pack('<%dH'%n,*tab)+bytes(body), d
if __name__=='__main__':
    out,orig=build(sys.argv[1],sys.argv[2])
    open(sys.argv[3],'wb').write(out)
