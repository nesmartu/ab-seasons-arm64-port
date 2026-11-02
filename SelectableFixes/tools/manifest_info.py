"""Read basic attributes from the input's binary AndroidManifest.xml."""
import struct

def inspect(data):
 u16=lambda p:struct.unpack_from('<H',data,p)[0];u32=lambda p:struct.unpack_from('<I',data,p)[0]
 strings=[];p=8;out={}
 def var(pos,utf8):
  if utf8:
   a=data[pos];return (((a&127)<<8)|data[pos+1],pos+2) if a&128 else (a,pos+1)
  a=u16(pos);return (((a&32767)<<16)|u16(pos+2),pos+4) if a&32768 else (a,pos+2)
 while p<len(data):
  kind,hs,size=struct.unpack_from('<HHI',data,p);assert size>=hs and p+size<=len(data)
  if kind==1:
   count,styles,flags,ss,st=struct.unpack_from('<5I',data,p+8);utf8=bool(flags&256)
   for i in range(count):
    q=p+ss+u32(p+hs+4*i)
    _,q=var(q,utf8)
    if utf8:n,q=var(q,True);strings.append(data[q:q+n].decode('utf-8',errors='replace'))
    else:n=_;strings.append(data[q:q+n*2].decode('utf-16le',errors='replace'))
  elif kind==0x0102:
   tag=strings[u32(p+20)];attrstart,attrsize,count=struct.unpack_from('<HHH',data,p+24)
   attrs={}
   for i in range(count):
    q=p+16+attrstart+i*attrsize;ns,name,raw=struct.unpack_from('<III',data,q);typ=data[q+15];v=u32(q+16)
    value=strings[v] if typ==3 else bool(v) if typ==18 else v
    attrs[strings[name]]=value
   if tag in ['manifest','uses-sdk','application']:out[tag]=attrs
  p+=size
 return out
