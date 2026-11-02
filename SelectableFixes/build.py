#!/usr/bin/env python3
"""Build selectable ARM32 Seasons 6.6.2 fixes from an original APK.
Use --matrix to build five preset combinations.
"""
import argparse,copy,hashlib,importlib,json,sys,tomllib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from apk_sign import sign_entries,signature_name,verify_v2
from manifest_info import inspect
from fixes.common import Context
META='assets/seasons_selectable_fixes.json'
FLAGS={'unlock_all_episodes','unlocked_all_with_coins','unlock_ragnahog_levels','quest_video','cosmetics','unlock_all_levels'}
ORDER=['unlock_ragnahog_levels','quest_video','unlock_all_episodes','unlock_all_levels','cosmetics','coins']
MATRIX=[('unlocked+ragnahogfix+questfix',False,False),('unlocked+money+ragnahogfix+questfix',True,False),('unlocked+ragnahogfix+questfix+cosmeticsopened',False,True),('unlocked+money+ragnahogfix+questfix+cosmeticsopened',True,True),('unlocked+money+ragnahogfix+questfix+cosmeticsopened+alllevels',True,True)]
sha=lambda b:hashlib.sha256(b).hexdigest()

def load_config(path):
 path=Path(path).resolve();c=tomllib.loads(path.read_text());base=path.parent
 if set(c)-{'build','fixes','options'}:raise ValueError('Unknown top-level configuration section')
 allowed={'input','output_dir','suffix','key','cert'}
 if set(c.get('build',{}))-allowed:raise ValueError('Unknown build setting')
 c['fixes']=normalize_flags(c.get('fixes',{}))
 if set(c.get('fixes',{}))-FLAGS:raise ValueError('Unknown fix flag')
 if set(c.get('options',{}))-{'coins_amount'}:raise ValueError('Unknown patch option')
 b=c.setdefault('build',{})
 for k,default in [('input','input'),('output_dir','dist'),('key','signing/test-key.pem'),('cert','signing/test-cert.pem')]:b[k]=(base/b.get(k,default)).resolve()
 b.setdefault('suffix','_SelectedFixes')
 if any(ch in b['suffix'] for ch in '/\\\0'):raise ValueError('suffix must be a filename suffix')
 f=c.setdefault('fixes',{})
 for k in FLAGS:
  f.setdefault(k,False)
  if type(f[k]) is not bool:raise ValueError(k+' must be true or false')
 o=c.setdefault('options',{});o.setdefault('coins_amount',1000000)
 if type(o['coins_amount']) is not int or not 1<=o['coins_amount']<=16000000:raise ValueError('coins_amount must be an integer in 1..16000000')
 return c

def normalize_flags(flags):
 f=dict(flags)
 if 'ragnahog' in f:
  if 'unlock_ragnahog_levels' in f:raise ValueError('Conflicting Ragnahog flags')
  f['unlock_ragnahog_levels']=f.pop('ragnahog')
 # Old names represented the broad patch, never silently reinterpret them as narrow.
 for old,new in [('unlocked_all','unlock_all_episodes')]:
  if old in f:
   if new in f:raise ValueError('Use either '+old+' or '+new+', not both')
   value=f.pop(old)
   if type(value) is not bool:raise ValueError(old+' must be true or false')
   f[new]=value
   if value:f['unlock_all_levels']=True
 return f

def selected(flags):
 effective=normalize_flags(flags)
 if effective.get('unlock_all_levels'):effective['unlock_all_episodes']=True
 if effective.get('unlocked_all_with_coins'):effective['unlock_all_episodes']=True;effective['coins']=True
 return [k for k in ORDER if effective.get(k,False)]

def transform(entries,flags,options):
 original=dict(entries);entries=dict(entries);ctx=Context(entries);requested=selected(flags);old={}
 if META in entries:
  old=json.loads(entries[META]);assert old['format']==1,'Unknown patch metadata version'
  for n,h in old.get('modified_hashes',{}).items():
   if n not in entries or sha(entries[n])!=h:raise ValueError('Previously patched resource changed: '+n)
 applied=dict(old.get('applied',{}));new=[]
 if 'ragnahog' in applied:applied['unlock_ragnahog_levels']=applied.pop('ragnahog')
 if 'unlocked_all' in applied:
  applied['unlock_all_levels']=applied.pop('unlocked_all');applied['unlock_all_episodes']={}
 for name in requested:
  settings={'coins_amount':options['coins_amount']} if name=='coins' else {}
  if name in applied:
   if applied[name]!=settings:raise ValueError('Patch '+name+' already exists with different options; rebuild from the original input')
   continue
  importlib.import_module('fixes.'+name).apply(ctx,options);applied[name]=settings;new.append(name)
 ctx.finish()
 if applied:
  touched=set(old.get('modified_hashes',{}))|{n for n,b in entries.items() if n!=META and b!=original.get(n)}
  provenance={'format':1,'project':'Seasons662 Selectable Fixes','applied':applied}
  if 'unlock_ragnahog_levels' in applied:touched.add('assets/data/config/episodes/episodesLatest.json')
  provenance['modified_hashes']={n:sha(entries[n]) for n in sorted(touched)}
  entries[META]=(json.dumps(provenance,sort_keys=True,separators=(',',':'))+'\n').encode()
 return entries,ctx.evidence,new

def build(inp,out,flags,options,key,cert):
 inp=Path(inp).resolve();out=Path(out).resolve()
 if inp==out:raise ValueError('Output must not overwrite the input APK')
 with zipfile.ZipFile(inp) as z:
  if len(z.namelist())!=len(set(z.namelist())):raise ValueError('Duplicate ZIP paths')
  if z.testzip() is not None:raise ValueError('Input ZIP CRC check failed')
  info=inspect(z.read('AndroidManifest.xml'))
  if info['manifest'].get('package')!='com.rovio.angrybirdsseasons' or info['manifest'].get('versionName')!='6.6.2':raise ValueError(('Only Seasons 6.6.2 is supported',info))
  before={i.filename:z.read(i) for i in z.infolist() if not signature_name(i.filename)}
  after,evidence,new=transform(before,flags,options)
  items=[]
  for i in z.infolist():
   if not signature_name(i.filename):items.append((copy.copy(i),after[i.filename]))
  for n in sorted(set(after)-set(before)):
   i=zipfile.ZipInfo(n,(2009,1,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;items.append((i,after[n]))
 data=sign_entries(items,Path(key),Path(cert));out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
 audit={'input':str(inp),'input_sha256':sha(inp.read_bytes()),'output':out.name,'output_sha256':sha(data),'output_bytes':len(data),'requested_flags':flags,'effective_patches':selected(flags),'new_patches':new,'options':options,'manifest':info,'modified_game_entries':sorted(n for n in before if before[n]!=after[n]),'added_entries':sorted(set(after)-set(before)),'v2':verify_v2(data),'device_tested':False}
 report_dir=out.parent/'reports';report_dir.mkdir(exist_ok=True)
 (report_dir/(out.stem+'.json')).write_text(json.dumps(audit,indent=2,ensure_ascii=False)+'\n')
 (report_dir/(out.stem+'.evidence.json')).write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+'\n')
 return audit

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,default=ROOT/'build_config.toml');p.add_argument('--input',type=Path);p.add_argument('--out-dir',type=Path);p.add_argument('--matrix',action='store_true');a=p.parse_args()
 c=load_config(a.config);b=c['build'];inp=a.input.resolve() if a.input else b['input'];outdir=a.out_dir.resolve() if a.out_dir else b['output_dir']
 inputs=sorted(inp.glob('*.apk')) if inp.is_dir() else [inp]
 if not inputs or not all(f.is_file() for f in inputs):raise ValueError('No input APK found; set build.input or use --input')
 if a.matrix and len(inputs)!=1:raise ValueError('--matrix requires exactly one original input APK')
 for f in inputs:
  jobs=[]
  if a.matrix:
   for name,money,cosmetics in MATRIX:
    flags=dict(unlock_all_episodes=True,unlocked_all_with_coins=money,unlock_ragnahog_levels='ragnahogfix' in name,quest_video=True,cosmetics=cosmetics,unlock_all_levels='alllevels' in name);jobs.append((outdir/('Seasons662_'+name+'.apk'),flags))
  else:jobs=[(outdir/(f.stem+b['suffix']+'.apk'),c['fixes'])]
  for out,flags in jobs:
   r=build(f,out,flags,c['options'],b['key'],b['cert']);print(json.dumps({k:r[k] for k in ['output','output_sha256','effective_patches','modified_game_entries']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
