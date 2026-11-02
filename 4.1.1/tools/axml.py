"""Small Android binary XML editor; preserves resource IDs and unknown chunks.

Only the manifest is modified. DEX classes and resources.arsc stay byte-identical.
"""
import struct

NO = 0xffffffff


def u32(b, p):
    return struct.unpack_from('<I', b, p)[0]


def len8(b, p):
    v = b[p]
    return (((v & 127) << 8) | b[p+1], p+2) if v & 128 else (v, p+1)


def len16(b, p):
    v = struct.unpack_from('<H', b, p)[0]
    return (((v & 32767) << 16) | struct.unpack_from('<H', b, p+2)[0], p+4) if v & 32768 else (v, p+2)


def enc8(n):
    return bytes([(n >> 8) | 128, n & 255]) if n > 127 else bytes([n])


def enc16(n):
    return struct.pack('<HH', (n >> 16) | 32768, n & 65535) if n > 32767 else struct.pack('<H', n)


def strings(chunk):
    count, styles, flags, start, style_start = struct.unpack_from('<5I', chunk, 8)
    assert styles == 0, 'Styled XML pool is not supported'
    result = []
    for i in range(count):
        p = start + u32(chunk, 28+4*i)
        if flags & 256:
            _, p = len8(chunk, p)
            n, p = len8(chunk, p)
            result.append(chunk[p:p+n].decode('utf-8'))
        else:
            n, p = len16(chunk, p)
            result.append(chunk[p:p+2*n].decode('utf-16le'))
    return result, flags


def pool(values, flags):
    offsets, data = [], bytearray()
    for s in values:
        offsets.append(len(data))
        n = len(s.encode('utf-16le')) // 2
        if flags & 256:
            b = s.encode('utf-8')
            data.extend(enc8(n) + enc8(len(b)) + b + b'\0')
        else:
            data.extend(enc16(n) + s.encode('utf-16le') + b'\0\0')
    while len(data) % 4:
        data.append(0)
    start = 28 + 4*len(values)
    # Replaced values may no longer be sorted.
    header = struct.pack('<HH6I', 1, 28, start+len(data), len(values), 0, flags & ~1, start, 0)
    return header + struct.pack('<%dI' % len(values), *offsets) + data


def patch_manifest(data, package='com.rovio.seasons662.dynarmic', offline=True, app_name='Angry Birds Seasons'):
    assert data[:4] == b'\x03\0\x08\0'
    chunks, p = [], 8
    while p < len(data):
        typ, hdr, size = struct.unpack_from('<HHI', data, p)
        assert size >= hdr >= 8 and p + size <= len(data)
        chunks.append([typ, bytearray(data[p:p+size])])
        p += size
    assert p == len(data)
    pool_index = next(i for i,c in enumerate(chunks) if c[0] == 1)
    values, flags = strings(chunks[pool_index][1])
    original = None
    for typ, chunk in chunks:
        if typ != 0x102 or values[u32(chunk, 20)] != 'manifest':
            continue
        start, width, count = struct.unpack_from('<HHH', chunk, 24)
        for i in range(count):
            off = 16 + start + i*width
            if values[u32(chunk, off+4)] == 'package' and chunk[off+15] == 3:
                original = values[u32(chunk, off+16)]
    if not original:
        raise ValueError('Input manifest has no package attribute')
    values = [s.replace(original, package) for s in values]
    label = len(values) if app_name is not None else None
    if app_name is not None:
        values.append(app_name)
    stack, output = [], []
    skip_depth = None
    changed = {'minSdkVersion': 0, 'targetSdkVersion': 0, 'label': 0, 'internet_removed': 0}
    for typ, c in chunks:
        if typ == 0x102:
            tag = values[u32(c, 20)]
            stack.append(tag)
            attr_start, attr_size, count = struct.unpack_from('<HHH', c, 24)
            attrs = [(16 + attr_start + i*attr_size) for i in range(count)]
            def attrname(a):
                return values[u32(c, a+4)]
            if offline and tag == 'uses-permission':
                for a in attrs:
                    if attrname(a) == 'name' and c[a+15] == 3 and values[u32(c,a+16)] == 'android.permission.INTERNET':
                        skip_depth = len(stack)
                        changed['internet_removed'] += 1
            for a in attrs:
                name = attrname(a)
                if tag == 'uses-sdk' and name in ['minSdkVersion', 'targetSdkVersion']:
                    struct.pack_into('<I', c, a+8, NO)
                    c[a+15] = 0x10
                    struct.pack_into('<I', c, a+16, 26 if name == 'minSdkVersion' else 28)
                    changed[name] += 1
                if app_name is not None and tag in ['application', 'activity', 'activity-alias'] and name == 'label':
                    struct.pack_into('<I', c, a+8, label)
                    c[a+15] = 3
                    struct.pack_into('<I', c, a+16, label)
                    if tag == 'application':
                        changed['label'] += 1
        if skip_depth is None:
            output.append((typ, c))
        if typ == 0x103:
            if skip_depth == len(stack):
                skip_depth = None
            stack.pop()
    assert not stack and all(changed[k] == 1 for k in ['minSdkVersion','targetSdkVersion']), changed
    assert changed['label'] == (0 if app_name is None else 1), changed
    assert not offline or changed['internet_removed'] == 1, changed
    body = b''.join(pool(values, flags) if typ == 1 else bytes(c) for typ,c in output)
    return struct.pack('<HHI', 3, 8, len(body)+8) + body


def manifest_attrs(data):
 p=8
 while struct.unpack_from('<H',data,p)[0]!=1:p+=struct.unpack_from('<I',data,p+4)[0]
 vals,_=strings(data[p:p+struct.unpack_from('<I',data,p+4)[0]]);tags=[];p=8
 while p<len(data):
  typ,_,size=struct.unpack_from('<HHI',data,p)
  if typ==0x102:
   c=data[p:p+size];tag=vals[struct.unpack_from('<I',c,20)[0]]
   start,width,count=struct.unpack_from('<HHH',c,24);attrs={}
   for i in range(count):
    a=16+start+i*width;n=vals[struct.unpack_from('<I',c,a+4)[0]];v=struct.unpack_from('<I',c,a+16)[0]
    attrs[n]=vals[v] if c[a+15]==3 else v
   tags.append((tag,attrs))
  p+=size
 return tags

