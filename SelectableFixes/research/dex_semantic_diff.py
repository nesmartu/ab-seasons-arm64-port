"""Compare DEX instruction streams after resolving relocated pool references.
This is an instruction-level comparison, not a proof of semantic equivalence.
Instruction formats: https://source.android.com/docs/core/runtime/dalvik-bytecode
"""
import struct
from dex_reader import Dex

def instructions(d,offset):
 code=d.code(offset);out=[];p=0
 if not hasattr(d,'field_names'):
  d.field_names=[];nf,fo=d.u(80),d.u(84)
  for i in range(nf):
   cl,ty,name=struct.unpack_from('<HHI',d.a,fo+8*i);d.field_names.append(d.types[cl]+'->'+d.strs[name]+':'+d.types[ty])
 fields=d.field_names
 two={2,5,8,0x13,0x15,0x16,0x19,0x1a,0x1c,0x1f,0x20,0x22,0x23,0x29}|set(range(0x2d,0x3e))|set(range(0x44,0x6e))|set(range(0x90,0xb0))|set(range(0xd0,0xe3))
 three={3,6,9,0x14,0x17,0x1b,0x24,0x25,0x26,0x2a,0x2b,0x2c}|set(range(0x6e,0x73))|set(range(0x74,0x79))
 while p<len(code):
  op=code[p]&255;ident=code[p]
  if op==0 and ident in [0x100,0x200,0x300]:
   if ident==0x100:n=4+2*code[p+1]
   elif ident==0x200:n=2+4*code[p+1]
   else:n=4+(code[p+1]*(code[p+2]|code[p+3]<<16)+1)//2
  else:n=5 if op==0x18 else 3 if op in three else 2 if op in two else 1
  row=list(code[p:p+n]);assert len(row)==n,('Truncated DEX instruction',p,op)
  if op in [0x1a,0x1b]:
   idx=row[1] if op==0x1a else row[1]|row[2]<<16;row[1:]=['string',d.strs[idx]]
  elif op in [0x1c,0x1f,0x20,0x22,0x23,0x24,0x25]:row[1]=['type',d.types[row[1]]]
  elif 0x52<=op<=0x6d:row[1]=['field',fields[row[1]]]
  elif 0x6e<=op<=0x72 or 0x74<=op<=0x78:row[1]=['method',d.methods[row[1]]]
  out.append({'pc':p,'instruction':row});p+=n
 return out

def compare(original,modified):
 a,b=Dex(original),Dex(modified);left={m:o for m,o in a.defined};right={m:o for m,o in b.defined};changed=[]
 for name in sorted(set(left)&set(right)):
  x=instructions(a,left[name]);y=instructions(b,right[name])
  if [r['instruction'] for r in x]!=[r['instruction'] for r in y]:
   changed.append({'method':name,'before_units':len(a.code(left[name])),'after_units':len(b.code(right[name])),'before':x,'after':y})
 return {'added_methods':sorted(set(right)-set(left)),'removed_methods':sorted(set(left)-set(right)),'changed_methods':changed,'unchanged_code_methods':len(set(left)&set(right))-len(changed)}
