import struct
def unhsq(d):
    usize=d[0]|d[1]<<8; csize=d[3]|d[4]<<8
    assert sum(d[:6])&0xff==0xab, 'bad hsq header'
    p=6; out=bytearray(); q=1
    def bit():
        nonlocal q,p
        if q==1:
            q=0x10000|d[p]|d[p+1]<<8; p+=2
        b=q&1; q>>=1; return b
    while True:
        if bit():
            out.append(d[p]); p+=1
        else:
            if bit():
                w=d[p]|d[p+1]<<8; p+=2
                cnt=w&7; off=(w>>3)-8192
                if cnt==0:
                    cnt=d[p]; p+=1
                    if cnt==0: break
            else:
                cnt=bit()<<1; cnt|=bit()
                off=d[p]-256; p+=1
            cnt+=2
            for _ in range(cnt): out.append(out[off])
    assert len(out)==usize,(len(out),usize)
    return bytes(out)

def hsq_literal(data):
    """HSQ compressor (literal + simple LZ) compatible with unhsq."""
    data=bytes(data); out=bytearray(); st={'pos':None,'n':16}
    def bit(b):
        if st['n']==16:
            st['pos']=len(out); out.extend(b'\0\0'); st['n']=0
        if b: out[st['pos']+(st['n']>>3)] |= 1<<(st['n']&7)
        st['n']+=1
    # hash chain LZ
    i=0; n=len(data); table={}
    while i<n:
        best_len=0; best_off=0
        if i+2<n:
            key=data[i:i+3]
            for j in reversed(table.get(key,[])[-32:]):
                off=i-j
                if off>8192: continue
                l=0
                while i+l<n and l<255+2 and data[j+l]==data[i+l]: l+=1
                if l>best_len: best_len,best_off=l,off
        if best_len>=3 and not (best_off>256 and best_len<3):
            L=best_len
            if best_off<=256 and L<=5:
                bit(0); bit(0); c=L-2; bit(c>>1&1); bit(c&1); out.append(256-best_off)
            else:
                L=min(L,257)
                bit(0); bit(1); w=((8192-best_off)<<3)
                if L-2<=7: w|=L-2; out+=bytes([w&255,w>>8])
                else: out+=bytes([w&255,w>>8,L-2])
            for k in range(L):
                if i+k+2<n: table.setdefault(data[i+k:i+k+3],[]).append(i+k)
            i+=L
        else:
            bit(1); out.append(data[i])
            if i+2<n: table.setdefault(data[i:i+3],[]).append(i)
            i+=1
    bit(0); bit(1); out+=b'\0\0\0'
    total=len(out)+6
    assert len(data)<65536 and total<65536
    h=bytearray([len(data)&255,len(data)>>8,0,total&255,total>>8,0])
    h[5]=(0xab-sum(h[:5]))&0xff
    return bytes(h+out)
