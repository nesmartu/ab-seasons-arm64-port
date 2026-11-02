#!/usr/bin/env python3
"""Apply optional selectable fixes, then build and audit every input/*.apk."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from config import ROOT,inputs,settings
from inspect_apk import preflight
from prepare_fixes import prepare,output_stem

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--tools',type=Path,default=ROOT.parent/'toolchains')
 ap.add_argument('--jobs',type=int,default=4)
 ap.add_argument('--package-only',action='store_true')
 ap.add_argument('--apk',type=Path)
 ap.add_argument('--config',type=Path,default=ROOT/'build_config.toml')
 a=ap.parse_args();a.config=a.config.resolve();candidates=[a.apk.resolve()] if a.apk else inputs();plans=[]
 for apk in candidates:
  cfg=settings(apk,a.config);preflight(apk);plans.append((apk,cfg))
 packages=[cfg['app']['package'] for _,cfg in plans]
 if len(packages)!=len(set(packages)):
  print('Note: outputs share a package and replace each other. Use explicit [variants] IDs to install side by side.',flush=True)
 results=[]
 for apk,cfg in plans:
  stem=output_stem(apk,cfg)
  reportdir=ROOT/'reports'/stem;reportdir.mkdir(parents=True,exist_ok=True)
  out=ROOT/'dist'/(stem+'-arm64.apk')
  def run(args,name):
   with (reportdir/name).open('w') as log:
    subprocess.run([sys.executable,*map(str,args)],stdout=log,stderr=subprocess.STDOUT,check=True)
  print('Processing',apk.name,'->',out.name,flush=True)
  source=prepare(apk,cfg,ROOT/'build/prepared'/stem,reportdir)
  preflight(source)
  if not a.package_only:run([ROOT/'tools/build.py','--apk',source,'--tools',a.tools.resolve(),'--jobs',a.jobs],'build.log')
  run([ROOT/'tools/package_apk.py','--apk',source,'--tools',a.tools.resolve(),'--config',a.config,'--out',out],'package.log')
  run([ROOT/'tools/inspect_apk.py',out,'--source',source,'--config',a.config,'--json',reportdir/'audit.json'],'audit.log')
  bridge=stem+'.bridge.so'
  shutil.copyfile(ROOT/'bridge/out/arm64-v8a/libAngryBirdsSeasonsFull.so',ROOT/'dist'/bridge)
  results.append(dict(input=apk.name,output=out.name,bridge=bridge,package=cfg['app']['package'],settings=cfg,
                      fixes_audited=source!=apk))
 (ROOT/'reports/batch.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
 print('Completed',len(results),'APK(s)',flush=True)

if __name__=='__main__':main()
