"""Open episode access only; preserve level, egg, star and feather predicates."""
from lua_chunk import boolean
NAME='unlock_all_episodes'
def apply(ctx,options):
 p=ctx.proto('scripts/settingsWrapper.lua','root.273',params=2,nup=1,requires=['unlockedEpisodes'])
 boolean(p,True)
