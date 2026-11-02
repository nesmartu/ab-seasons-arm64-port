import struct
from collections import Counter

class Elf:
    def __init__(self, b):
        assert b[:4] == b'\x7fELF' and b[5] == 1
        self.b, self.bits = b, b[4]*32
        self.machine = struct.unpack_from('<H', b, 18)[0]
        if self.bits == 32:
            phoff, shoff = struct.unpack_from('<II', b, 28)
            phent, phnum, shent, shnum = struct.unpack_from('<4H', b, 42)
            shfmt, phfmt = '<10I', '<8I'
        else:
            phoff, shoff = struct.unpack_from('<QQ', b, 32)
            phent, phnum, shent, shnum = struct.unpack_from('<4H', b, 54)
            shfmt, phfmt = '<II4QII2Q', '<II6Q'
        self.sections = [struct.unpack_from(shfmt, b, shoff+i*shent) for i in range(shnum)]
        self.segments = [struct.unpack_from(phfmt, b, phoff+i*phent) for i in range(phnum)]
        self.symbols = {}
        for s in self.sections:
            if s[1] != 11:
                continue
            strings_sec = self.sections[s[6]]
            st = b[strings_sec[4]:strings_sec[4]+strings_sec[5]]
            for p in range(s[4], s[4]+s[5], s[9]):
                if self.bits == 32:
                    name, value, size, info, other, index = struct.unpack_from('<IIIBBH', b, p)
                else:
                    name, info, other, index, value, size = struct.unpack_from('<IBBHQQ', b, p)
                n = st[name:st.find(b'\0',name)].decode()
                if n:
                    self.symbols[n] = dict(value=value, size=size, bind=info>>4, index=index)

    def imports(self):
        return {n for n,s in self.symbols.items() if s['index'] == 0}

    def exports(self):
        return {n for n,s in self.symbols.items() if s['index'] != 0}

    def relocations32(self):
        assert self.bits == 32
        return Counter(struct.unpack_from('<II', self.b, p)[1] & 255
                       for s in self.sections if s[1] == 9
                       for p in range(s[4], s[4]+s[5], s[9]))

