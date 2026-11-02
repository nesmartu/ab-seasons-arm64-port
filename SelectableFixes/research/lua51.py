import struct,json,sys
from pathlib import Path
OPS='MOVE LOADK LOADBOOL LOADNIL GETUPVAL GETGLOBAL GETTABLE SETGLOBAL SETUPVAL SETTABLE NEWTABLE SELF ADD SUB MUL DIV MOD POW UNM NOT LEN CONCAT JMP EQ LT LE TEST TESTSET CALL TAILCALL RETURN FORLOOP FORPREP TFORLOOP SETLIST CLOSE CLOSURE VARARG'.split()
class Parser:
 def __init__(self,a):
  self.a=a;assert a[:4]==b'\x1bLua' and a[4]==0x51;self.pos=12;self.end='<' if a[6] else '>';self.ints,self.st,self.ins,self.num=a[7:11]
 def read(self,n):o=self.a[self.pos:self.pos+n];self.pos+=n;assert len(o)==n;return o
 def uint(self,n=None):return int.from_bytes(self.read(n or self.ints),'little' if self.end=='<' else 'big')
 def string(self):
  n=self.uint(self.st)
  return self.read(n)[:-1].decode('utf-8',errors='backslashreplace') if n else None
 def proto(self,path='root'):
  source=self.string();line,last=self.uint(),self.uint();nup,nparams,vararg,stack=self.read(4)
  code=[self.uint(self.ins) for _ in range(self.uint())];ks=[]
  for _ in range(self.uint()):
   t=self.read(1)[0]
   if t==0:v=None
   elif t==1:v=bool(self.read(1)[0])
   elif t==3:v=struct.unpack(self.end+('f' if self.num==4 else 'd'),self.read(self.num))[0]
   elif t==4:v=self.string()
   else:raise ValueError(t)
   ks.append(v)
  protos=[self.proto(path+'.'+str(i)) for i in range(self.uint())]
  lines=[self.uint() for _ in range(self.uint())]
  locs=[(self.string(),self.uint(),self.uint()) for _ in range(self.uint())]
  ups=[self.string() for _ in range(self.uint())]
  return dict(path=path,source=source,line=line,last=last,nup=nup,params=nparams,vararg=vararg,stack=stack,code=code,ks=ks,protos=protos,lines=lines,locals=locs,ups=ups)
def walk(p):
 yield p
 for c in p['protos']:yield from walk(c)
def fmt(p):
 out=[f"FUNCTION {p['path']} params={p['params']} stack={p['stack']} up={p['nup']}", 'K='+repr(p['ks'])]
 def rk(x):return 'K'+str(x-256)+'='+repr(p['ks'][x-256]) if x>=256 else 'R'+str(x)
 for pc,w in enumerate(p['code']):
  op=w&63;a=w>>6&255;c=w>>14&511;b=w>>23&511;bx=w>>14;sbx=bx-131071;name=OPS[op]
  if name in ['GETGLOBAL','SETGLOBAL','LOADK']:s=f'R{a}, K{bx}={p["ks"][bx]!r}'
  elif name=='GETTABLE':s=f'R{a}, R{b}, {rk(c)}'
  elif name=='SETTABLE':s=f'R{a}, {rk(b)}, {rk(c)}'
  elif name=='SELF':s=f'R{a}, R{b}, {rk(c)}'
  elif name in ['EQ','LT','LE']:s=f'{a}, {rk(b)}, {rk(c)}'
  elif name in ['ADD','SUB','MUL','DIV','MOD','POW']:s=f'R{a}, {rk(b)}, {rk(c)}'
  elif name in ['JMP','FORLOOP','FORPREP']:s=f'R{a}, -> {pc+1+sbx:04d}'
  elif name=='CLOSURE':s=f'R{a}, {p["path"]}.{bx}'
  else:s=f'{a}, {b}, {c}'
  out.append(f'{pc:04d} {name:10s} {s}')
 return '\n'.join(out)
if __name__=='__main__':
 p=Parser(Path(sys.argv[1]).read_bytes()).proto()
 if len(sys.argv)>2:
  terms=sys.argv[2:]
  for q in walk(p):
   if any(any(t.lower() in str(k).lower() for t in terms) for k in q['ks']):print(fmt(q)+'\n')
 else:print(fmt(p))
