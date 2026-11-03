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
UNSEL=0xB
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
    # ---- 자막 옵션 3개: 실행파일 패치로 7px 2칸(14px) 간격으로 재배치
    #   그리기: 행 7/9/11 (패널 y 88/102/116), 클릭: 행 7-8/9-10/11-12
    BX,BW,BH=134,65,14
    BANDS=[88,102,116]; TOFF=3; CX=167
    texts=['자막','말풍선','자막없음']
    selgrad=[0xF,0xF,0xE,0xE,0xC,0xC,0xA,0xA]
    for y in range(88,137):
        for x in range(BX,BX+BW):
            if P[y][x]==8: P[y][x]=3
    clean=[r[:] for r in P]
    def put(rows,ox,oy,text,sel):
        pts,tw=textd(J,text); left=CX-tw//2
        for px,py in pts:
            rows[oy+TOFF+py][left+px-ox]= selgrad[py] if sel else 8
        if sel:
            arrow=[(0,0),(0,1),(1,1),(0,2),(1,2),(2,2),(0,3),(1,3),(0,4)]
            for ax,ay in arrow:
                yy=oy+TOFF+2+ay; c=selgrad[2+ay]
                rows[yy][left-5+ax-ox]=c
                rows[yy][left+tw+4-ax-ox]=c
    for k,t in enumerate(texts): put(P,0,BANDS[k],t,False)
    for k,t in enumerate(texts):
        for sel,idx in ((True,44+2*k),(False,45+2*k)):
            band=[clean[BANDS[k]+y][:] for y in range(BH)]
            put(band,0,0,t,sel)
            rw=((BW+1)//2+1)//2*2*2
            rows=[[band[y][BX+x] for x in range(BW)]+[0]*(rw-BW) for y in range(BH)]
            S[idx]['rows']=rows; S[idx]['h']=BH
    # rebuild
    ends=offs[1:]+[len(d)]
    blobs=[enc(s) if k in (0,44,45,46,47,48,49) else d[offs[k]:ends[k]] for k,s in enumerate(S)]
    n=len(blobs); body=bytearray(); tab=[]
    for b in blobs: tab.append(2*n+len(body)); body+=b
    return struct.pack('<H',2)+struct.pack('<%dH'%n,*tab)+bytes(body), d
if __name__=='__main__':
    out,orig=build(sys.argv[1],sys.argv[2])
    open(sys.argv[3],'wb').write(out)
