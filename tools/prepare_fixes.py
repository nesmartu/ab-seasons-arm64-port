"""Run the unmodified standalone patch engine in an isolated Python process."""
import json
import subprocess
import sys
from pathlib import Path
from config import ROOT, fixes_active

def output_stem(apk, cfg):
    if not fixes_active(cfg):return apk.stem + '-original'
    f=cfg['fixes']; names=[]
    if f['unlock_all_episodes'] or f['unlocked_all_with_coins']:names.append('unlocked')
    if f['unlocked_all_with_coins']:names.append('money')
    if f['unlock_ragnahog_levels']:names.append('ragnahogfix')
    if f['quest_video']:names.append('questfix')
    if f['cosmetics']:names.append('cosmeticsopened')
    if f['unlock_all_levels']:names.append('alllevels')
    return apk.stem + '+' + '+'.join(names)

def prepare(apk, cfg, work, reportdir):
    if not fixes_active(cfg):return apk
    patcher=ROOT/'SelectableFixes'
    work.mkdir(parents=True,exist_ok=True)
    # Keep the complete original filename: variants are keyed by that filename.
    prepared=work/apk.name
    config=work/'patch_config.toml'
    q=lambda p:json.dumps(str(p.resolve()))
    text='[build]\ninput='+q(apk)+'\noutput_dir='+q(work)+'\n'
    text+='key='+q(patcher/'signing/test-key.pem')+'\ncert='+q(patcher/'signing/test-cert.pem')+'\n'
    text+='[fixes]\n'+''.join(k+' = '+str(v).lower()+'\n' for k,v in cfg['fixes'].items())
    text+='[options]\ncoins_amount = '+str(cfg['selectable_fixes']['coins_amount'])+'\n'
    config.write_text(text,encoding='utf-8')
    code="""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); sys.path[:0]=[str(root),str(root/'tools')]
from build import build,load_config
from verify import audit
c=load_config(sys.argv[2]); b=c['build']; out=Path(sys.argv[3])
r=build(b['input'],out,c['fixes'],c['options'],b['key'],b['cert'])
v=audit(b['input'],out)
Path(sys.argv[4]).write_text(json.dumps({'build':r,'audit':v},indent=2)+'\\n')
"""
    with (reportdir/'fixes.log').open('w') as log:
        subprocess.run([sys.executable,'-c',code,str(patcher),str(config),str(prepared),str(reportdir/'fixes.json')],stdout=log,stderr=subprocess.STDOUT,check=True)
    return prepared
