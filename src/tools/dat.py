import struct, sys, os
def read_index(f):
    f.seek(0); n=struct.unpack('<H',f.read(2))[0]; ents=[]
    for i in range(n):
        b=f.read(25)
        name=b[:16].split(b'\0')[0].decode('latin1'); size,off=struct.unpack('<II',b[16:24]); ents.append((name,size,off,b[24]))
    return ents
if __name__=='__main__':
    src,out=sys.argv[1],sys.argv[2]
    with open(src,'rb') as f:
        ents=read_index(f)
        print(len(ents),'entries')
        for name,size,off,fl in ents:
            if not name: continue
            f.seek(off); open(os.path.join(out,name),'wb').write(f.read(size))
