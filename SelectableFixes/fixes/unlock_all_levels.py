"""Open shipped level buttons/access gates without forging scores or purchases."""
from lua_chunk import boolean,constant_return,OPS
NAME='unlock_all_levels'
SW='scripts/settingsWrapper.lua'

def bound_predicates(root,name):
 for i,w in enumerate(root['code']):
  if OPS[w&63]!='CLOSURE':continue
  reg=w>>6&255;child=root['protos'][w>>14];pc=i+1+child['nup']
  v=root['code'][pc];b=v>>23&511;c=v>>14&511
  if OPS[v&63]=='SETTABLE' and c==reg and b>=256 and root['ks'][b-256]==name:yield child['path']

def apply(ctx,options):
 for path,required in [('root.52',['getGoldenEgg']),('root.84',['openedPigDaysLevels']),('root.275',['unlockedBonusLevels'])]:
  p=ctx.proto(SW,path,params=2,requires=required);boolean(p,True)
 p=ctx.proto(SW,'root.344',params=2,requires=['starLockedEpisodes']);boolean(p,False)
 p=ctx.proto(SW,'root.82',params=2,nup=1,requires=['lastOpenLevelLP','calculateLastOpenLevel']);constant_return(p,200.0)
 p=ctx.proto('scripts/gamelogic.lua','root.158',params=1,nup=0,requires=['getLevelById','isTimeStampAvailable','stars_required']);boolean(p,True)
 # Calendar, social, golden egg and star/feather layouts have their own gates.
 for name,count in [('scripts/menus/seasons_layouts.lua',16),('scripts/menus/level_selection_layouts.lua',4)]:
  paths=list(bound_predicates(ctx.chunk(name),'isLevelOpen'))
  if len(paths)!=count:raise ValueError((name,'unexpected layout predicate count',paths))
  for path in paths:
   p=ctx.proto(name,path,params=1);boolean(p,True)
