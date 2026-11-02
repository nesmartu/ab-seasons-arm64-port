#!/usr/bin/env python3
"""Audit payload boundaries, APK signatures, alignment and patch metadata."""
import argparse,base64,copy,hashlib,json,shutil,struct,subprocess,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from apk_sign import signature_name,verify_v2
from manifest_info import inspect
from codec import decode
from lua_chunk import parse,walk,validate
from build import META
sha=lambda b:hashlib.sha256(b).hexdigest()
EXPECTED={
 'unlock_ragnahog_levels':{'config/episodes/episodesLatest.json':None},
 'quest_video':{'scripts/menus/combinedMenu/QuestLogFrame.lua':{'root.8'},'scripts/quests/QuestLog.lua':{'root.14'}},
 'unlock_all_episodes':{'scripts/settingsWrapper.lua':{'root.273'}},
 'unlock_all_levels':{'scripts/settingsWrapper.lua':{'root.'+str(i) for i in [52,84,273,275,344,82]},'scripts/gamelogic.lua':{'root.158'},'scripts/menus/seasons_layouts.lua':{'root.'+str(i) for i in [3,11,21,32,43,56,68,78,87,97,107,116,125,134,143,152]},'scripts/menus/level_selection_layouts.lua':{'root.12','root.21','root.30','root.38'}},
 'cosmetics':{'scripts/settingsWrapper.lua':{'root.258','root.255','root.259','root.285'}},
 'coins':{'scripts/settingsWrapper.lua':{'root.277'}},
}
def headers(section):
 out={}
 for line in section.replace(b'\r\n ',b'').split(b'\r\n'):
  if b': ' in line:
   a,b=line.split(b': ',1);out[a.decode()]=b.decode()
 return out

def audit(inp,out):
 inp,out=Path(inp),Path(out);raw=out.read_bytes();sig=verify_v2(raw)
 with zipfile.ZipFile(inp) as a,zipfile.ZipFile(out) as b:
  assert b.testzip() is None and len(b.namelist())==len(set(b.namelist()))
  an={n for n in a.namelist() if not signature_name(n)};bn={n for n in b.namelist() if not signature_name(n)}
  assert an<=bn and bn-an<= {META},('Unexpected added/removed game entries',an-bn,bn-an)
  meta=json.loads(b.read(META)) if META in bn else {'applied':{},'modified_hashes':{}}
  allowed={}
  for fix in meta['applied']:
   if fix=='unlocked_all':fix='unlock_all_levels'
   if fix=='ragnahog':fix='unlock_ragnahog_levels'
   assert fix in EXPECTED
   for n,paths in EXPECTED[fix].items():
    target='assets/data/'+n
    if paths is None:allowed[target]=None
    else:allowed.setdefault(target,set()).update(paths)
  changed=[n for n in sorted(an) if a.read(n)!=b.read(n)]
  assert set(changed)<=(set(allowed)|{META}),('Unexpected payload change',changed)
  functions={}
  for n in changed:
   if n.endswith('.lua'):
    old=parse(decode(a.read(n)));new=parse(decode(b.read(n)));validate(new)
    left={q['path']:{k:v for k,v in q.items() if k!='protos'} for q in walk(old)};right={q['path']:{k:v for k,v in q.items() if k!='protos'} for q in walk(new)}
    assert left.keys()==right.keys(),('Changed function tree',n)
    funcs={k for k in left if left[k]!=right[k]};assert funcs<=allowed[n],(n,'Unexpected changed prototypes',funcs-allowed[n]);functions[n]=sorted(funcs)
    for k in funcs:assert left[k]['nup']==right[k]['nup'] and left[k]['params']==right[k]['params'] and left[k]['vararg']==right[k]['vararg'],(n,k,'Changed function ABI')
   elif n.endswith('episodesLatest.json'):
    old=json.loads(decode(a.read(n)));new=json.loads(decode(b.read(n)));expected=copy.deepcopy(old);ep=expected['episodes']['episodeRagnahog'];ep['manual_level_progression']=False;ep['pages'][0]['all_levels_open']=True;assert expected==new
  for n,h in meta['modified_hashes'].items():assert sha(b.read(n))==h
  for n in ['AndroidManifest.xml','resources.arsc','classes.dex']+[n for n in an if n.startswith('lib/')]:assert a.read(n)==b.read(n),(n,'Must stay unchanged')
  aligned=0
  for i in b.infolist():
   if i.compress_type==zipfile.ZIP_STORED:
    nl,el=struct.unpack_from('<HH',raw,i.header_offset+26);assert (i.header_offset+30+nl+el)%4==0,i.filename;aligned+=1
  mf=b.read('META-INF/MANIFEST.MF');sf=b.read('META-INF/CERT.SF');cms=b.read('META-INF/CERT.RSA');sfh=headers(sf.split(b'\r\n\r\n')[0]);assert sfh['X-Android-APK-Signed']=='2';assert sfh['SHA-256-Digest-Manifest']==base64.b64encode(hashlib.sha256(mf).digest()).decode()
  sections={};covered=set()
  for section in mf.split(b'\r\n\r\n')[1:]:
   h=headers(section)
   if not h:continue
   n=h['Name'];assert n not in covered;covered.add(n);assert h['SHA-256-Digest']==base64.b64encode(hashlib.sha256(b.read(n)).digest()).decode();sections[n]=section+b'\r\n\r\n'
  assert covered=={n for n in bn if not n.endswith('/')}
  sfcovered=set()
  for section in sf.split(b'\r\n\r\n')[1:]:
   h=headers(section)
   if not h:continue
   n=h['Name'];sfcovered.add(n);assert h['SHA-256-Digest']==base64.b64encode(hashlib.sha256(sections[n]).digest()).decode()
  assert sfcovered==covered
  cmsresult='not run: OpenSSL not installed'
  if shutil.which('openssl'):
   with tempfile.TemporaryDirectory() as t:
    t=Path(t);(t/'sig.der').write_bytes(cms);(t/'CERT.SF').write_bytes(sf)
    r=subprocess.run(['openssl','cms','-verify','-inform','DER','-binary','-in',str(t/'sig.der'),'-content',str(t/'CERT.SF'),'-noverify'],capture_output=True);assert r.returncode==0 and r.stdout==sf,r.stderr.decode();cmsresult='PASS'
  item=b.getinfo('resources.arsc');nl,el=struct.unpack_from('<HH',raw,item.header_offset+26);pos=item.header_offset+30+nl+el;bad=bytearray(raw);bad[pos]^=1
  try:verify_v2(bytes(bad))
  except (AssertionError,ValueError):pass
  else:raise AssertionError('Tampered APK accepted')
  manifest=inspect(b.read('AndroidManifest.xml'))
  abis=sorted({n.split('/')[1] for n in bn if n.startswith('lib/') and n.endswith('.so')})
 return dict(input_sha256=sha(inp.read_bytes()),output=out.name,output_sha256=sha(raw),output_bytes=len(raw),manifest=manifest,abis=abis,modified_game_entries=changed,modified_lua_prototypes=functions,added_entries=sorted(bn-an),zip_crc='PASS',stored_entries_aligned_4=aligned,v1_hashes='PASS',v1_openssl=cmsresult,v2=sig,v2_tamper_rejected=True,device_tested=False)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--apk',type=Path);p.add_argument('--dir',type=Path,default=ROOT/'dist');a=p.parse_args()
 files=[a.apk] if a.apk else sorted(a.dir.glob('*.apk'));assert files,'No APKs to verify'
 rows=[]
 for f in files:
  r=audit(a.input,f);rows.append(r);print(json.dumps({'output':r['output'],'audit':'PASS','v1_openssl':r['v1_openssl'],'abis':r['abis']}),flush=True)
 dest=a.dir/'reports';dest.mkdir(parents=True,exist_ok=True);(dest/'audit.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()
