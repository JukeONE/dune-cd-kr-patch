import struct
def parse(d):
    first=struct.unpack_from('<H',d,0)[0]; n=first//2
    offs=struct.unpack_from('<%dH'%n,d,0)
    out=[]
    for i,o in enumerate(offs):
        e=d.index(b'\xff',o); out.append(d[o:e])
    return offs,out
