#!/usr/bin/env python3
"""Build and audit each selectable fix, all-off and optional modified inputs.
Use build.py --matrix to build the five combined presets.
"""
from pathlib import Path
import argparse,json,sys
from build import build,load_config
from verify import audit
ROOT=Path(__file__).resolve().parent

def main():
 (ROOT/'reports/current').mkdir(parents=True,exist_ok=True)
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,default=ROOT/'input/AngryBirdsSeasons_v6.6.2.apk');p.add_argument('--mods',type=Path,nargs='*',default=[]);a=p.parse_args();c=load_config(ROOT/'build_config.toml');dest=ROOT/'validation_builds';dest.mkdir(exist_ok=True);rows=[]
 jobs=[('all_off',{})]+[(name,{name:True}) for name in ['unlock_all_episodes','unlocked_all_with_coins','unlock_ragnahog_levels','quest_video','cosmetics','unlock_all_levels']]
 for name,flags in jobs:
  out=dest/(name+'.apk');r=build(a.input,out,flags,c['options'],c['build']['key'],c['build']['cert']);v=audit(a.input,out);rows.append({'case':name,'build':r,'audit':v});print(name+' build and audit PASS',flush=True)
 for i,inp in enumerate(a.mods):
  flags=dict(unlock_all_episodes=True,unlocked_all_with_coins=True,unlock_ragnahog_levels=True,quest_video=True,cosmetics=True);out=dest/('existing_mod_'+str(i)+'.apk');r=build(inp,out,flags,c['options'],c['build']['key'],c['build']['cert']);v=audit(inp,out);rows.append({'case':'existing_mod_'+str(i),'build':r,'audit':v});print(inp.name+' build and audit PASS',flush=True)
 (ROOT/'reports/current/individual_builds.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()
