"""Shared patch context: inspect structure, edit only selected resource entries."""
import copy,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from codec import decode,encode
from lua_chunk import parse,dump,validate,walk,fmt
PREFIX='assets/data/'
class Context:
 def __init__(self,entries):self.entries=entries;self.chunks={};self.evidence=[]
 def raw(self,name):return decode(self.entries[PREFIX+name])
 def chunk(self,name):
  if name not in self.chunks:
   raw=self.raw(name);self.chunks[name]=(raw,parse(raw))
  return self.chunks[name][1]
 def proto(self,name,path,params=None,nup=None,requires=()):
  p=next(q for q in walk(self.chunk(name)) if q['path']==path)
  if params is not None and p['params']!=params:raise ValueError((name,path,'parameters differ'))
  if nup is not None and p['nup']!=nup:raise ValueError((name,path,'upvalues differ'))
  if not all(k in p['ks'] for k in requires):raise ValueError((name,path,'unsupported function structure',requires))
  self.evidence.append({'file':name,'prototype':path,'before':fmt(p)})
  return p
 def finish(self):
  for name,(raw,p) in self.chunks.items():
   validate(p);changed=dump(p,raw[:12]);check=parse(changed);validate(check)
   # Preserve original encrypted bytes when the decoded chunk is unchanged.
   if changed!=raw:self.entries[PREFIX+name]=encode(changed)
  for e in self.evidence:
   p=next(q for q in walk(self.chunks[e['file']][1]) if q['path']==e['prototype']);e['after']=fmt(p)
