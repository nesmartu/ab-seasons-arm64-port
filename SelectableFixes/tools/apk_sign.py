"""Deterministic APK v1 (JAR/CMS) + v2 signer; RSA/SHA-256.
Format reference: https://source.android.com/docs/security/features/apksigning/v2
This project supplies a public TEST key. Use your own certificate for real releases.
"""
import base64,hashlib,io,struct,zipfile,copy
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import pkcs7
MAGIC=b'APK Sig Block 42';ID=0x7109871a;ALG=0x0103
u32=lambda n:struct.pack('<I',n)
u64=lambda n:struct.pack('<Q',n)
lp=lambda b:u32(len(b))+b
sha=lambda b:hashlib.sha256(b).digest()

def signature_name(n):
 n=n.upper()
 return n.startswith('META-INF/') and (n=='META-INF/MANIFEST.MF' or n.endswith(('.SF','.RSA','.DSA','.EC')) or n.split('/')[-1].startswith('SIG-'))

def manifest_header(name,value):
 # JAR lines are byte-limited; names in these APKs are UTF-8/ASCII.
 a=(name+': '+value).encode();out=[]
 out.append(a[:70]);a=a[70:]
 while a:out.append(b' '+a[:69]);a=a[69:]
 return b'\r\n'.join(out)+b'\r\n'

def jar_records(entries,key,cert):
 start=manifest_header('Manifest-Version','1.0')+manifest_header('Created-By','Seasons Ragnahog Fix')+b'\r\n'
 sections=[]
 for info,data in entries:
  if info.is_dir():continue
  s=manifest_header('Name',info.filename)+manifest_header('SHA-256-Digest',base64.b64encode(sha(data)).decode())+b'\r\n';sections.append((info.filename,s))
 manifest=start+b''.join(s for _,s in sections)
 sf=manifest_header('Signature-Version','1.0')+manifest_header('Created-By','Seasons Ragnahog Fix')+manifest_header('SHA-256-Digest-Manifest',base64.b64encode(sha(manifest)).decode())+manifest_header('X-Android-APK-Signed','2')+b'\r\n'
 for name,s in sections:sf+=manifest_header('Name',name)+manifest_header('SHA-256-Digest',base64.b64encode(sha(s)).decode())+b'\r\n'
 cms=pkcs7.PKCS7SignatureBuilder().set_data(sf).add_signer(cert,key,hashes.SHA256()).sign(serialization.Encoding.DER,[pkcs7.PKCS7Options.DetachedSignature,pkcs7.PKCS7Options.Binary,pkcs7.PKCS7Options.NoAttributes])
 return [('META-INF/MANIFEST.MF',manifest),('META-INF/CERT.SF',sf),('META-INF/CERT.RSA',cms)]

def end_record(a):
 pos=a.rfind(b'PK\x05\x06',max(0,len(a)-65557))
 assert pos>=0 and pos+22+struct.unpack_from('<H',a,pos+20)[0]==len(a),'invalid EOCD'
 assert struct.unpack_from('<HH',a,pos+4)==(0,0),'multidisk ZIP unsupported'
 assert struct.unpack_from('<H',a,pos+10)[0]!=65535,'ZIP64 unsupported'
 cdlen,cdoff=struct.unpack_from('<II',a,pos+12)
 assert cdoff+cdlen==pos,'central directory mismatch'
 return pos,cdoff,cdlen

def content_digest(parts):
 chunks=[]
 for part in parts:
  for i in range(0,len(part),1024*1024):
   c=part[i:i+1024*1024];chunks.append(sha(b'\xa5'+u32(len(c))+c))
 return sha(b'\x5a'+u32(len(chunks))+b''.join(chunks))

def sign_v2(a,key,cert):
 eocd,cd,_=end_record(a);digest=content_digest([a[:cd],a[cd:eocd],a[eocd:]])
 certder=cert.public_bytes(serialization.Encoding.DER)
 pub=key.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)
 signed=lp(lp(u32(ALG)+lp(digest)))+lp(lp(certder))+lp(b'')
 sig=key.sign(signed,padding.PKCS1v15(),hashes.SHA256())
 signer=lp(signed)+lp(lp(u32(ALG)+lp(sig)))+lp(pub)
 value=lp(lp(signer));pair=u64(4+len(value))+u32(ID)+value
 size=len(pair)+24;block=u64(size)+pair+u64(size)+MAGIC
 tail=bytearray(a[eocd:]);struct.pack_into('<I',tail,16,cd+len(block))
 return a[:cd]+block+a[cd:eocd]+tail

def build_zip(entries):
 buf=io.BytesIO()
 with zipfile.ZipFile(buf,'w',allowZip64=False) as z:
  for original,data in entries:
   info=copy.copy(original);info.extra=b''
   # All STORED resources are aligned to 4 bytes. Native .so files here are DEFLATED.
   if info.compress_type==zipfile.ZIP_STORED:
    off=buf.tell()+30+len(info.filename.encode('utf-8'));info.extra=b'\0'*((-off)%4)
   z.writestr(info,data,compress_type=info.compress_type,compresslevel=9)
 return buf.getvalue()

def sign_entries(entries,key_path,cert_path):
 key=serialization.load_pem_private_key(Path(key_path).read_bytes(),password=None)
 cert=x509.load_pem_x509_certificate(Path(cert_path).read_bytes())
 assert cert.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)==key.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)
 v1=jar_records(entries,key,cert)
 for name,data in v1:
  info=zipfile.ZipInfo(name,(2026,11,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;entries.append((info,data))
 return sign_v2(build_zip(entries),key,cert)

def read_lp(a,p=0):
 n=struct.unpack_from('<I',a,p)[0];end=p+4+n;assert end<=len(a)
 return a[p+4:end],end

def verify_v2(a):
 eocd,cd,_=end_record(a);assert a[cd-16:cd]==MAGIC
 size=struct.unpack_from('<Q',a,cd-24)[0];start=cd-size-8
 assert start>=0 and struct.unpack_from('<Q',a,start)[0]==size
 p=start+8;blocks={}
 while p<cd-24:
  n=struct.unpack_from('<Q',a,p)[0];p+=8;ident=struct.unpack_from('<I',a,p)[0];blocks[ident]=a[p+4:p+n];p+=n
 assert p==cd-24 and ID in blocks
 signers,last=read_lp(blocks[ID]);assert last==len(blocks[ID])
 signer,last=read_lp(signers);assert last==len(signers),'expected one signer'
 signed,p=read_lp(signer);signatures,p=read_lp(signer,p);pub,p=read_lp(signer,p);assert p==len(signer)
 signature,last=read_lp(signatures);assert last==len(signatures)
 alg=struct.unpack_from('<I',signature)[0];sig,last=read_lp(signature,4);assert alg==ALG and last==len(signature)
 digests,p=read_lp(signed);certs,p=read_lp(signed,p);attrs,p=read_lp(signed,p);assert p==len(signed)
 record,last=read_lp(digests);assert last==len(digests) and struct.unpack_from('<I',record)[0]==alg
 digest,last=read_lp(record,4);assert last==len(record)
 certder,last=read_lp(certs);assert last==len(certs);cert=x509.load_der_x509_certificate(certder)
 key=serialization.load_der_public_key(pub)
 assert key.public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)==cert.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)
 key.verify(sig,signed,padding.PKCS1v15(),hashes.SHA256())
 tail=bytearray(a[eocd:]);struct.pack_into('<I',tail,16,start)
 assert digest==content_digest([a[:start],a[cd:eocd],tail]),'APK digest mismatch'
 return {'scheme':'v2','algorithm':'RSA_PKCS1_SHA256','certificate_sha256':sha(certder).hex(),'content_digest_sha256':digest.hex(),'signers':1}
