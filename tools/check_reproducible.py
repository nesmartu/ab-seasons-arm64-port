#!/usr/bin/env python3
"""Compile/package twice in different clean directories and compare signed APKs."""
import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path
from config import ROOT

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def collect_outputs(project):
    # Compare release artifacts only. Temporary unsigned/aligned APKs are not outputs.
    batch=json.loads((project/'reports/batch.json').read_text())
    names=[name for item in batch for name in [item['output'],item.get('bridge',Path(item['input']).stem+'.bridge.so')]]
    return {name:sha(project/'dist'/name) for name in sorted(names)}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--tools',type=Path,default=ROOT.parent/'toolchains')
    ap.add_argument('--config',type=Path,default=ROOT/'build_config.toml')
    ap.add_argument('--jobs',type=int,default=4)
    ap.add_argument('--package-only',action='store_true',help='check packaging only; skip native compilation')
    a=ap.parse_args();runs=[]
    with tempfile.TemporaryDirectory(prefix='seasons-repro-',dir=ROOT.parent,ignore_cleanup_errors=True) as tmp:
        for name in ['first','second']:
            dst=Path(tmp)/name/ROOT.name
            shutil.copytree(ROOT,dst,ignore=shutil.ignore_patterns('build','dist','__pycache__','bonus','4.1.1'))
            shutil.copyfile(a.config, dst/'repro_config.toml')
            cmd=[sys.executable,str(dst/'tools/release.py'),'--tools',str(a.tools.resolve()),'--jobs',str(a.jobs),'--config',str(dst/'repro_config.toml')]
            if a.package_only:cmd.append('--package-only')
            subprocess.run(cmd,check=True)
            runs.append(collect_outputs(dst))
    if not runs[0]:raise RuntimeError('No outputs')
    result=dict(identical=runs[0]==runs[1],native_rebuilt=not a.package_only,first=runs[0],second=runs[1],python=platform.python_version(),zlib=zlib.ZLIB_RUNTIME_VERSION)
    (ROOT/'reports/reproducibility.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if not result['identical']:raise SystemExit(1)

if __name__=='__main__':main()
