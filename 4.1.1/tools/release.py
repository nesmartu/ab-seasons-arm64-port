#!/usr/bin/env python3
"""Build every input/*.apk; preserve separate reports per input."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from config import ROOT,inputs,settings
from inspect_apk import preflight

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--tools',type=Path,default=ROOT.parent.parent/'toolchains')
 ap.add_argument('--jobs',type=int,default=4)
 ap.add_argument('--package-only',action='store_true')
 ap.add_argument('--apk',type=Path)
 ap.add_argument('--config',type=Path,default=ROOT/'build_config.toml')
 a=ap.parse_args(); candidates=[a.apk.resolve()] if a.apk else inputs();plans=[]
 for apk in candidates:
  cfg=settings(apk,a.config);preflight(apk);plans.append((apk,cfg))
 packages=[cfg['app']['package'] for _,cfg in plans]
 if len(packages)!=len(set(packages)):
  print('Note: outputs share a package and replace each other on installation. Use [variants] to install side by side.',flush=True)
 results=[]
 for apk,cfg in plans:
  reportdir=ROOT/'reports'/apk.stem;reportdir.mkdir(parents=True,exist_ok=True)
  out=ROOT/'dist'/(apk.stem+'-arm64.apk')
  def run(args,name):
   with (reportdir/name).open('w') as log:
    subprocess.run([sys.executable,*map(str,args)],stdout=log,stderr=subprocess.STDOUT,check=True)
  print('Processing',apk.name,flush=True)
  if not a.package_only:run([ROOT/'tools/build.py','--apk',apk,'--tools',a.tools.resolve(),'--jobs',a.jobs],'build.log')
  run([ROOT/'tools/package_apk.py','--apk',apk,'--tools',a.tools.resolve(),'--config',a.config,'--out',out],'package.log')
  run([ROOT/'tools/inspect_apk.py',out,'--source',apk,'--config',a.config,'--json',reportdir/'audit.json'],'audit.log')
  shutil.copyfile(ROOT/'bridge/out/arm64-v8a/libAngryBirdsSeasonsFull.so',ROOT/'dist'/(apk.stem+'.bridge.so'))
  results.append(dict(input=apk.name,output=out.name,package=cfg['app']['package']))
 (ROOT/'reports/batch.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
 print('Completed',len(results),'APK(s)',flush=True)

if __name__=='__main__':main()
