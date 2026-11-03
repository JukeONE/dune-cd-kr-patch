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
def text_px(g,text):
    pts=[];x=0
    for ch in text:
        if ch==' ': x+=4; continue
        G=g[ord(ch)]
        for (px,py) in G['px']: pts.append((x+px,py))
        x+=G['dw']
    w=max(p[0] for p in pts)+1
    return pts,w
def build(src,fontfn):
    d=open(src,'rb').read()
    t,offs=sheet(d); S=[dec(d,o) for o in offs]
    g,asc=load(fontfn)
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
            pts,w=text_px(g,text); left=cx-w//2
            S_=set((left+px,ty+py) for px,py in pts)
            for (x,y) in S_: P[y][x]=0xA
            for (x,y) in S_:
                if (x+1,y) not in S_: P[y][x+1]=shadow
    label([(4,44,25,33)],5,[('음성',25)])
    label([(45,72,15,25)],6,[('음악',16)])
    label([(73,117,15,25),(73,133,26,33)],6,[('음성 중',16),('음악',25)])
    # ---- subtitle buttons 44..49 (sel/unsel pairs)
    texts={44:'자막',45:'자막',46:'말풍선',47:'말풍선',48:'자막없음',49:'자막없음'}
    selgrad=[0xF,0xF,0xE,0xE,0xC,0xC,0xA]
    origs={i:[r[:] for r in S[i]['rows']] for i in texts}
    for i,text in texts.items():
        R=S[i]['rows']; w=S[i]['w']
        inner=[x for x in range(w) if R[0][x]==3 and R[6][x]==3]
        a,b=min(inner),max(inner)
        for y in range(7):
            for x in range(a,b+1): R[y][x]=3
        pts,tw=text_px(g,text)
        # left-align like original panel: all at same column; center 자막없음 within its interior
        left=(a+b+1-tw)//2
        for px,py in pts:
            R[py][left+px]= selgrad[py] if i%2==0 else 8
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
