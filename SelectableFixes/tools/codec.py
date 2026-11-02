"""AES-256-CBC + Rovio custom LZMA wrapper used by original Seasons 6.6.2 assets."""
import lzma
from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
KEY=b'zePhest5faQuX2S2Apre@4reChAtEvUt';MAGIC=b'\x89LZMA\r\n\x1a\n'
def decode(data):
 d=Cipher(algorithms.AES(KEY),modes.CBC(bytes(16))).decryptor();plain=d.update(data)+d.finalize()
 assert plain.startswith(MAGIC),'not the expected Seasons asset format'
 expected=int.from_bytes(plain[14:22],'little');assert 0<expected<64*1024*1024
 dec=lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
 out=dec.decompress(plain[9:],max_length=expected);assert len(out)==expected
 return out

def encode(data):
 raw=lzma.compress(data,format=lzma.FORMAT_ALONE,filters=[{'id':lzma.FILTER_LZMA1,'dict_size':65536,'lc':3,'lp':0,'pb':2,'mode':lzma.MODE_NORMAL,'nice_len':64,'mf':lzma.MF_BT4}])
 wrapped=MAGIC+raw[:5]+len(data).to_bytes(8,'little')+raw[13:]
 n=16-len(wrapped)%16;wrapped+=bytes([n])*n
 e=Cipher(algorithms.AES(KEY),modes.CBC(bytes(16))).encryptor();result=e.update(wrapped)+e.finalize()
 assert decode(result)==data
 return result
