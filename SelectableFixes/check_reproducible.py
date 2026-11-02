#!/usr/bin/env python3
"""Rebuild the five APKs in a clean directory and compare the complete signed bytes."""
import argparse,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
 (ROOT/'reports/current').mkdir(parents=True,exist_ok=True)
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,default=ROOT/'input/AngryBirdsSeasons_v6.6.2.apk');p.add_argument('--dist',type=Path,default=ROOT/'dist');a=p.parse_args();rows=[]
 with tempfile.TemporaryDirectory(prefix='seasons-rebuild-',dir=ROOT.parent) as t:
  root=Path(t)/'project';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('input','dist','validation_builds','reports','evidence','__pycache__','*.pyc'))
  subprocess.run([sys.executable,str(root/'build.py'),'--matrix','--input',str(a.input.resolve()),'--out-dir',str(root/'dist')],check=True)
  original=sorted(a.dist.glob('*.apk'));rebuilt=sorted((root/'dist').glob('*.apk'));assert [f.name for f in original]==[f.name for f in rebuilt] and len(original)==5
  for left,right in zip(original,rebuilt):
   x,y=left.read_bytes(),right.read_bytes();assert x==y,left.name
   rows.append({'output':left.name,'sha256':hashlib.sha256(x).hexdigest(),'clean_rebuild_equal':True});print(left.name+' signed-byte comparison PASS',flush=True)
 (ROOT/'reports/current/reproducibility.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()
