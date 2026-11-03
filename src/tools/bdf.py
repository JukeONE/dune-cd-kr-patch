import re
def load(fn):
    t=open(fn,encoding='utf-8').read(); asc=int(re.search(r'FONT_ASCENT (\d+)',t).group(1))
    g={}
    for m in re.finditer(r'ENCODING (\d+)\n(.*?)ENDCHAR',t,re.S):
        cp=int(m.group(1)); s=m.group(2)
        w,h,xo,yo=map(int,re.search(r'BBX (-?\d+) (-?\d+) (-?\d+) (-?\d+)',s).group(1,2,3,4))
        dw=int(re.search(r'DWIDTH (\d+)',s).group(1))
        rows=[int(x,16) for x in s.split('BITMAP\n')[1].split()]
        nb=(w+7)//8
        # to list of pixel sets: (x,y) with y from top of bbox
        px=set()
        for r,v in enumerate(rows):
            for c in range(w):
                if v>>(nb*8-1-c)&1: px.add((c+xo,r))
        g[cp]=dict(w=w,h=h,xo=xo,yo=yo,dw=dw,px=px)
    return g,asc
