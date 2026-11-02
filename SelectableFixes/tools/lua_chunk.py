"""Lossless Lua 5.1 chunk reader/writer and a tiny instruction assembler.
No source decompiler or external Lua compiler is used.
"""
import struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from lua51 import Parser,walk,fmt,OPS

def parse(raw):
 parser=Parser(raw);root=parser.proto()
 if parser.pos!=len(raw):raise ValueError('trailing Lua chunk data')
 if dump(root,raw[:12])!=raw:raise ValueError('Lua chunk cannot be round-tripped losslessly')
 return root

def dump(p,header):
 assert header[7:11]==bytes([4,4,4,4]) and header[6]==1,'expected little-endian 32-bit Lua 5.1'
 def u(v):return struct.pack('<I',v)
 def s(v):
  if v is None:return u(0)
  b=v.encode('utf-8')+b'\0';return u(len(b))+b
 def vector(xs,f):return u(len(xs))+b''.join(f(x) for x in xs)
 def constant(v):
  if v is None:return b'\0'
  if isinstance(v,bool):return b'\1'+bytes([v])
  if isinstance(v,(int,float)):return b'\3'+struct.pack('<f',v)
  if isinstance(v,str):return b'\4'+s(v)
  raise TypeError(v)
 def proto(q):
  b=s(q['source'])+u(q['line'])+u(q['last'])+bytes([q['nup'],q['params'],q['vararg'],q['stack']])
  b+=vector(q['code'],u)+vector(q['ks'],constant)+vector(q['protos'],proto)
  b+=vector(q['lines'],u)+vector(q['locals'],lambda x:s(x[0])+u(x[1])+u(x[2]))+vector(q['ups'],s)
  return b
 return header+proto(p)

def abc(op,a=0,b=0,c=0):return OPS.index(op)|(a<<6)|(c<<14)|(b<<23)
def abx(op,a,bx):return OPS.index(op)|(a<<6)|(bx<<14)
def jump(pc,dest):return abx('JMP',0,131071+dest-pc-1)

class Assembler:
 def __init__(self):self.code=[];self.ks=[];self.labels={};self.refs=[]
 def k(self,value):
  for i,v in enumerate(self.ks):
   if type(v)==type(value) and v==value:return i
  self.ks.append(value);return len(self.ks)-1
 def emit(self,op,a=0,b=0,c=0):self.code.append(abc(op,a,b,c))
 def load(self,reg,value):self.code.append(abx('LOADK',reg,self.k(value)))
 def glob(self,reg,name):self.code.append(abx('GETGLOBAL',reg,self.k(name)))
 def label(self,name):assert name not in self.labels;self.labels[name]=len(self.code)
 def jmp(self,name):self.refs.append((len(self.code),name));self.code.append(0)
 def get(self,dest,table,key,scratch=7):self.load(scratch,key);self.emit('GETTABLE',dest,table,scratch)
 def set(self,table,key,val,scratch=7):self.load(scratch,key);self.emit('SETTABLE',table,scratch,val)
 def finish(self,p,stack=8):
  for pc,name in self.refs:self.code[pc]=jump(pc,self.labels[name])
  p['code']=self.code;p['ks']=self.ks;p['stack']=max(stack,p['params'],2)
  p['protos']=[];p['lines']=[];p['locals']=[];p['ups']=[]

def boolean(p,value):
 a=Assembler();a.emit('LOADBOOL',p['params'],int(value));a.emit('RETURN',p['params'],2);a.finish(p,p['params']+1)
def constant_return(p,value):
 a=Assembler();a.load(p['params'],value);a.emit('RETURN',p['params'],2);a.finish(p,p['params']+1)

def validate(root):
 """Check modified chunks for out-of-range registers/constants/jumps and closure bindings."""
 for p in walk(root):
  assert 2<=p['stack']<=250,(p['path'],'stack')
  assert not p['lines'] or len(p['lines'])==len(p['code'])
  for pc,w in enumerate(p['code']):
   op=w&63;assert op<len(OPS);op=OPS[op];a=w>>6&255;b=w>>23&511;c=w>>14&511;bx=w>>14
   # CLOSURE upvalue binding words are valid MOVE/GETUPVAL instructions too.
   if op not in ['JMP','EQ','LT','LE','CLOSE']:assert a<p['stack'],(p['path'],pc,op,a)
   if op in ['LOADK','GETGLOBAL','SETGLOBAL']:assert bx<len(p['ks'])
   if op=='CLOSURE':assert bx<len(p['protos'])
   if op in ['JMP','FORLOOP','FORPREP']:assert 0<=pc+1+bx-131071<len(p['code'])
   if op in ['GETTABLE','SELF']:assert c< p['stack'] or c>=256 and c-256<len(p['ks'])
   if op in ['SETTABLE','ADD','SUB','MUL','DIV','MOD','POW','EQ','LT','LE']:
    for r in [b,c]:assert r<p['stack'] or r>=256 and r-256<len(p['ks'])
 return True
