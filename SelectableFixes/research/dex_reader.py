import struct,zipfile,json
from pathlib import Path
class Dex:
 def __init__(self,a):
  self.a=a;u=lambda o:struct.unpack_from('<I',a,o)[0];self.u=u
  ns,so=u(56),u(60);self.strs=[]
  for i in range(ns):
   p=u(so+4*i);_,p=self.uleb(p);self.strs.append(a[p:a.index(b'\0',p)].decode('utf-8',errors='replace'))
  nt,to=u(64),u(68);self.types=[self.strs[u(to+4*i)] for i in range(nt)]
  np,po=u(72),u(76);self.protos=[]
  for i in range(np):
   short,ret,params=struct.unpack_from('<III',a,po+12*i);args=[]
   if params:
    args=[self.types[struct.unpack_from('<H',a,params+4+2*j)[0]] for j in range(u(params))]
   self.protos.append('('+''.join(args)+')'+self.types[ret])
  nm,mo=u(88),u(92);self.methods=[]
  for i in range(nm):
   cl,pr,n=struct.unpack_from('<HHI',a,mo+8*i);self.methods.append(self.types[cl]+'->'+self.strs[n]+self.protos[pr])
  self.defined=[];nc,co=u(96),u(100)
  for i in range(nc):
   vs=struct.unpack_from('<8I',a,co+32*i);cd=vs[6]
   if not cd:continue
   p=cd;nums=[]
   for _ in range(4):v,p=self.uleb(p);nums.append(v)
   for _ in range(sum(nums[:2])):
    _,p=self.uleb(p);_,p=self.uleb(p)
   for n in nums[2:]:
    idx=0
    for _ in range(n):
     diff,p=self.uleb(p);idx+=diff;flags,p=self.uleb(p);code,p=self.uleb(p);self.defined.append((self.methods[idx],code))
 def uleb(self,p):
  n=0;s=0
  while True:
   b=self.a[p];p+=1;n|=(b&127)<<s
   if b<128:return n,p
   s+=7
 def code(self,p):
  if not p:return []
  n=self.u(p+12);return list(struct.unpack_from('<'+'H'*n,self.a,p+16))
