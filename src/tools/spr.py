import struct
def sheet(d):
    t=struct.unpack_from('<H',d,0)[0]; first=struct.unpack_from('<H',d,t)[0]; n=first//2
    return t,[struct.unpack_from('<H',d,t+2*i)[0]+t for i in range(n)]
def decode(d,o):
    w0,h,pal=struct.unpack_from('<HBB',d,o); rle=w0&0x8000; w=w0&0x7fff; p=o+4
    rowbytes=(w+1)//2
    rows=[]
    for y in range(h):
        row=bytearray()
        if rle:
            while len(row)<rowbytes:
                c=d[p]; p+=1
                if c&0x80:
                    cnt=257-c; row+=bytes([d[p]])*cnt; p+=1
                else:
                    row+=d[p:p+c+1]; p+=c+1
        else:
            row+=d[p:p+rowbytes]; p+=rowbytes
        px=[]
        for b in row[:rowbytes]: px+=[b&15,b>>4]
        rows.append(px[:w])
    return dict(w=w,h=h,pal=pal,rle=bool(rle),rows=rows,end=p)
