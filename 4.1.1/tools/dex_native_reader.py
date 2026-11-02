"""Extract native declarations directly from DEX class_data (no Java tool needed)."""
import struct
import zipfile

def natives(data):
    if not data.startswith(b'dex\n'):
        raise ValueError('Unsupported DEX header')
    def u32(p): return struct.unpack_from('<I', data, p)[0]
    def uleb(p):
        value = shift = 0
        for _ in range(5):
            b = data[p]; p += 1
            value |= (b & 127) << shift
            if b < 128: return value,p
            shift += 7
        raise ValueError('Invalid DEX ULEB128')
    sc,so = u32(56),u32(60)
    strings=[]
    for i in range(sc):
        p=u32(so+4*i); _,p=uleb(p)
        strings.append(data[p:data.index(b'\0',p)].decode('utf-8', errors='replace'))
    tc,to=u32(64),u32(68)
    types=[strings[u32(to+4*i)] for i in range(tc)]
    pc,po=u32(72),u32(76)
    protos=[]
    for i in range(pc):
        _,ret,args=struct.unpack_from('<III',data,po+12*i)
        params=[] if not args else [types[j] for j in struct.unpack_from('<'+'H'*u32(args),data,args+4)]
        protos.append('('+''.join(params)+')'+types[ret])
    mc,mo=u32(88),u32(92)
    methods=[struct.unpack_from('<HHI',data,mo+8*i) for i in range(mc)]
    cc,co=u32(96),u32(100)
    out=[]
    for i in range(cc):
        p=u32(co+32*i+24)
        if not p: continue
        counts=[]
        for _ in range(4):
            v,p=uleb(p);counts.append(v)
        for _ in range(counts[0]+counts[1]):
            _,p=uleb(p);_,p=uleb(p)
        for count in counts[2:]:
            index=0
            for _ in range(count):
                delta,p=uleb(p); access,p=uleb(p); _,p=uleb(p)
                index+=delta
                if access & 0x100:
                    cls,proto,name=methods[index]
                    out.append(('static ' if access & 8 else '')+types[cls][1:-1].replace('/','.')+'.'+strings[name]+protos[proto])
    return out

def from_apk(path):
    with zipfile.ZipFile(path) as z:
        result=[]
        for name in sorted(z.namelist()):
            if name.startswith('classes') and name.endswith('.dex') and '/' not in name:
                result.extend(natives(z.read(name)))
    return sorted(set(result), key=lambda s:s.removeprefix('static '))
