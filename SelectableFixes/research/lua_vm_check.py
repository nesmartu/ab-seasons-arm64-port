"""Small interpreter for the Lua 5.1 opcodes reached by the inspected functions.
This executes original bytecode with mocked Android/network services, not the game.
"""
from pathlib import Path
from lua51 import Parser,OPS
import json

def truth(v):return v is not None and v is not False

def get(t,k):
 if isinstance(t,list):return t[int(k)-1] if isinstance(k,(int,float)) and 1<=int(k)<=len(t) else None
 if isinstance(t,dict):return t.get(k)
 if t is None:raise TypeError(('index nil',k))
 return getattr(t,k,None)

def run(p,env,args=(),upvalues=()):
 regs=[None]*256
 for i,v in enumerate(args):regs[i]=v
 pc=0;steps=0;top=len(args)
 def rk(x):return p['ks'][x-256] if x>=256 else regs[x]
 while pc<len(p['code']):
  steps+=1;assert steps<100000,'step limit'
  w=p['code'][pc];op=w&63;a=w>>6&255;b=w>>23&511;c=w>>14&511;bx=w>>14;sbx=bx-131071;name=OPS[op];pc+=1
  if name=='MOVE':regs[a]=regs[b]
  elif name=='GETUPVAL':regs[a]=upvalues[b]
  elif name=='SETGLOBAL':env[p['ks'][bx]]=regs[a]
  elif name=='NEWTABLE':regs[a]={}
  elif name=='SETTABLE':
   t=regs[a];key=rk(b);value=rk(c)
   if value is None:t.pop(key,None)
   else:t[key]=value
  elif name=='SETLIST':
   assert b and c
   for i in range(1,b+1):regs[a][(c-1)*50+i]=regs[a+i]
  elif name=='NOT':regs[a]=not truth(regs[b])
  elif name=='CLOSE':pass
  elif name=='LOADK':regs[a]=p['ks'][bx]
  elif name=='LOADNIL':
   for i in range(a,b+1):regs[i]=None
  elif name=='LOADBOOL':
   regs[a]=bool(b)
   if c:pc+=1
  elif name=='GETGLOBAL':regs[a]=env.get(p['ks'][bx])
  elif name=='GETTABLE':regs[a]=get(regs[b],rk(c))
  elif name=='SELF':regs[a+1]=regs[b];regs[a]=get(regs[b],rk(c))
  elif name in ['CALL','TAILCALL']:
   count=b-1 if b else top-a-1
   assert callable(regs[a]),(p['path'],pc-1,a,regs[a:a+max(b,1)])
   ret=regs[a](*regs[a+1:a+1+count]);ret=ret if isinstance(ret,tuple) else (ret,)
   if name=='TAILCALL':return ret
   if c==0:
    for i,v in enumerate(ret):regs[a+i]=v
    top=a+len(ret)
   else:
    for i in range(c-1):regs[a+i]=ret[i] if i<len(ret) else None
  elif name=='CLOSURE':
   child=p['protos'][bx];captured=[]
   for i in range(child['nup']):
    bind=p['code'][pc];pc+=1;bo=OPS[bind&63];br=bind>>23&511
    assert bo in ['MOVE','GETUPVAL']
    captured.append(regs[br] if bo=='MOVE' else upvalues[br])
   regs[a]=lambda *args,child=child,captured=captured:run(child,env,args,captured)
  elif name=='RETURN':return tuple(regs[a:a+b-1 if b else top])
  elif name=='JMP':pc+=sbx
  elif name=='TESTSET':
   if truth(regs[b])==bool(c):regs[a]=regs[b]
   else:pc+=1
  elif name=='TEST':
   if truth(regs[a])!=bool(c):pc+=1
  elif name in ['EQ','LT','LE']:
   x,y=rk(b),rk(c)
   v=(((isinstance(x,(int,float)) and not isinstance(x,bool) and isinstance(y,(int,float)) and not isinstance(y,bool)) or type(x)==type(y)) and x==y) if name=='EQ' else (x<y if name=='LT' else x<=y)
   if bool(v)!=bool(a):pc+=1
  elif name=='ADD':regs[a]=rk(b)+rk(c)
  elif name=='LEN':regs[a]=len(regs[b])
  elif name=='CONCAT':regs[a]=''.join(str(x) for x in regs[b:c+1])
  elif name=='FORPREP':regs[a]-=regs[a+2];pc+=sbx
  elif name=='FORLOOP':
   regs[a]+=regs[a+2]
   if (regs[a+2]>0 and regs[a]<=regs[a+1]) or (regs[a+2]<=0 and regs[a]>=regs[a+1]):regs[a+3]=regs[a];pc+=sbx
  elif name=='TFORLOOP':
   vals=regs[a](regs[a+1],regs[a+2]);vals=vals if isinstance(vals,tuple) else (vals,)
   for i in range(c):regs[a+3+i]=vals[i] if i<len(vals) else None
   if regs[a+3] is not None:regs[a+2]=regs[a+3]
   else:pc+=1
  else:raise NotImplementedError((p['path'],pc-1,name))
 raise RuntimeError('no return')

def pairs(v):
 items=list(enumerate(v,1)) if isinstance(v,list) else list(v.items());state={'i':0}
 def it(_,last):
  i=state['i'];state['i']+=1;return items[i] if i<len(items) else (None,None)
 return it,None,None

def test(root):
 p=Parser((root/'scripts/gamelogic.lua').read_bytes()).proto();cfg=json.loads((root/'config/episodes/episodesLatest.json').read_text());episode=cfg['episodes']['episodeRagnahog'];results=[]
 for patched in [False,True]:
  for available,past,bought in [(False,False,False),(True,True,False),(False,False,True)]:
   ep=json.loads(json.dumps(episode))
   if patched:ep['pages'][0]['all_levels_open']=True;ep['manual_level_progression']=False
   for i,l in enumerate(ep['pages'][0]['levels'],1):l['index']=i
   state={'last':1,'writes':[]};env={};env['_G']=env
   def setlast(_,key,value):state['last']=int(value);state['writes'].append(int(value))
   env.update(requireFile=lambda *a:None,getLocalEpisode=lambda key:ep if key=='episodeRagnahog' else None,
    g_specialId='absent-special-episode',allLocalEpisodeKeys=['episodeRagnahog'],releaseBuild=True,
    print=lambda *a:None,pairs=pairs,saveLuaFileWrapper=lambda *a:None,
    settingsWrapper={'getLastOpenLevel':lambda _,key:state['last'],'setLastOpenLevel':setlast,'isCurrentChristmasBought':lambda _:bought,'newOpenPigDaysLevelsExist':lambda *a:None},
    native={'TimeStamp':{'isTimeStampAvailable':lambda:available,'checkIfDatePassed':lambda *args:1 if past else -1,'getCurrentYear':lambda:2026,'getCurrentMonth':lambda:11,'getCurrentDay':lambda:1}})
   run(p['protos'][364],env)
   expected=200 if patched or past or bought else 0;assert state['last']==expected,(patched,available,past,bought,state)
   env.update(getLevelById=lambda name:(ep['pages'][0]['levels'][1],'episodeRagnahog',1,2),
      native={'TimeStamp':{'isTimeStampAvailable':lambda:available,'getSecondsToDate':lambda *a:-1 if past else 86400}})
   opened=run(p['protos'][158],env,('ragnahog_house',))[0]
   assert opened==bool(expected==200),(patched,opened,state)
   results.append(dict(patched=patched,timestamp_available=available,date_passed=past,bought=bought,last_open=state['last'],level_2_allowed=opened))
 return results
def startup_test(root):
 p=Parser((root/'scripts/gamelogic.lua').read_bytes()).proto();cfg=json.loads((root/'config/episodes/episodesLatest.json').read_text());episode=cfg['episodes']['episodeRagnahog'];results=[]
 for mode in ['original','calendar_flag_only','full_fix']:
  for cached in [0,1,2,25,200]:
   ep=json.loads(json.dumps(episode))
   if mode!='original':ep['pages'][0]['all_levels_open']=True
   if mode=='full_fix':ep['manual_level_progression']=False
   state={'last':cached};env={};env['_G']=env
   def setlast(_,key,value):state['last']=int(value)
   env.update(allLocalEpisodeKeys=['episodeRagnahog'],getLocalEpisode=lambda key:ep,print=lambda *a:None,tostring=str,highscores={},settingsWrapper={'getLastOpenLevel':lambda _,key:state['last'],'setLastOpenLevel':setlast})
   env['calculateLastOpenLevel']=lambda key:run(p['protos'][111],env,(key,))[0]
   run(p['protos'][84],env)
   expected=max(cached,29) if mode=='full_fix' else cached
   assert state['last']==expected,(mode,cached,state)
   env.update(getLevelById=lambda name:(ep['pages'][0]['levels'][1],'episodeRagnahog',1,2),native={'TimeStamp':{'isTimeStampAvailable':lambda:False}})
   opened=run(p['protos'][158],env,('ragnahog_house',))[0]
   assert opened==(expected>=2)
   results.append(dict(mode=mode,cached_last_open=cached,timestamp_callback_run=False,last_after_startup=state['last'],level_2_allowed=opened))
 return results

if __name__=='__main__':
 root=Path(__file__).resolve().parent/'decoded';print(json.dumps({'calendar':test(root),'startup':startup_test(root)},indent=2))
