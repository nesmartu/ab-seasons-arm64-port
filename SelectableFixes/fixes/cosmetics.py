"""Grant all shipped Bird Wear entries; preserve unrelated quest records."""
import json
from lua_chunk import Assembler,abc,abx
NAME='cosmetics';SW='scripts/settingsWrapper.lua'

def prepend_grant(p):
 r=p['stack'];assert r+2<=250
 # Parameters and original registers are untouched; relative jumps still work.
 ks=p['ks'];start=[]
 for key in ['settingsWrapper','getCompletedQuests']:
  if key not in ks:ks.append(key)
 start += [abx('GETGLOBAL',r,ks.index('settingsWrapper')),abx('LOADK',r+1,ks.index('getCompletedQuests')),abc('GETTABLE',r,r,r+1),abc('MOVE',r+1,0),abc('CALL',r,2,1)]
 if p['code'][:5]==start:return
 p['code']=start+p['code'];p['stack']=r+2;p['lines']=[];p['locals']=[]

def apply(ctx,options):
 journal=json.loads(ctx.raw('config/quests/BirdJournalPages.json'));quests=json.loads(ctx.raw('config/quests/Quests.json'))
 # Quests.json structure is checked below rather than assumed from the filename.
 if 'quests' in quests:quests=quests['quests']
 rows={}
 for page in journal['pages']:
  for bird in page:
   for frame in bird['frames']:
    qid=frame.get('questId')
    if qid:
     q=quests[qid];rows[qid]=q.get('questTargets',[])
 if len(rows)!=108:raise ValueError(('Unexpected Bird Wear catalogue',len(rows)))
 p=ctx.proto(SW,'root.258',params=1,nup=1)
 a=Assembler();a.emit('GETUPVAL',1,0);a.get(2,1,'completedQuests')
 a.emit('TEST',2,0,1);a.jmp('table_ready');a.emit('NEWTABLE',2);a.set(1,'completedQuests',2);a.label('table_ready')
 a.emit('LOADBOOL',4,1)
 for i,(qid,targets) in enumerate(sorted(rows.items())):
  a.get(3,2,qid);a.emit('TEST',3,0,1);a.jmp('quest_'+str(i));a.emit('NEWTABLE',3);a.set(2,qid,3);a.label('quest_'+str(i))
  a.set(3,'completed',4)
  a.emit('NEWTABLE',5)
  for j,target in enumerate(targets,1):
   a.load(6,target);a.set(5,float(j),6)
  a.set(3,'collectedStamps',5);a.load(6,float(max(1,len(targets))));a.set(3,'currentItem',6)
 a.emit('RETURN',2,2);a.finish(p)
 for path in ['root.255','root.259']:
  p=ctx.proto(SW,path,params=2,nup=1);prepend_grant(p)
 # The journal remains accessible before the original tutorial would release it.
 from lua_chunk import boolean
 boolean(ctx.proto(SW,'root.285',params=1,nup=1),False)
