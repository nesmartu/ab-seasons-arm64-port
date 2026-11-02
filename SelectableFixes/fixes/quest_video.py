"""Take the existing successful quest-hint path immediately on button press.
Both the combined-menu tab and the standalone QuestLog popup are covered.
"""
from lua_chunk import jump,abc,OPS
NAME='quest_video'
SITES=[
 ('scripts/menus/combinedMenu/QuestLogFrame.lua','root.8',0,409,342,344,356,374,381,385,404),
 ('scripts/quests/QuestLog.lua','root.14',1,512,440,442,455,474,482,487,507),
]
def apply(ctx,options):
 for file,path,nup,length,branch,start,end,assign,call_begin,call_end,done in SITES:
  p=ctx.proto(file,path,params=4,nup=nup,requires=['WATCH_VIDEO_AND_GIVE_HINT','SIMULATE_SUCCESSFULL_QUEST_VIDEO','setQuestVideoWatched','levelTarget','levelTargetQuestId'])
  c=p['code'];k=p['ks']
  if len(c)!=length or OPS[c[branch]&63]!='EQ' or k[(c[branch]>>14&511)-256]!='WATCH_VIDEO_AND_GIVE_HINT':raise ValueError((file,'Unsupported quest click handler'))
  if c[start:start+4]==c[assign:assign+4]:continue
  # Resolve the original readiness access in either namespace.
  ready=c[start] if nup==0 else c[start+1]
  if (k[ready>>14] if nup==0 else k[(ready>>14&511)-256])!='questVideoReady':raise ValueError((file,'Unknown quest-video modification'))
  replacement=c[assign:assign+4]+c[call_begin:call_end]
  replacement.append(jump(start+len(replacement),done))
  replacement += [abc('MOVE',8,8)]*(end-start-len(replacement))
  c[start:end]=replacement
