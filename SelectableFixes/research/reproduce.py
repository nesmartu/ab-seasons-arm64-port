#!/usr/bin/env python3
"""Regenerate payload/DEX comparisons, seed metadata and before/after Lua evidence.
Never installs or executes an APK or imports a mod's saved profile.
"""
import argparse,hashlib,io,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools'),str(ROOT/'research')]
from build import transform,signature_name
from dex_reader import Dex
from dex_semantic_diff import compare,instructions
sha=lambda b:hashlib.sha256(b).hexdigest()

def seed_unlocked(z):
 from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
 if 'assets/data.save' not in z.namelist():return None
 dex=Dex(z.read('classes.dex'));arrays={1:bytearray(16),7:bytearray(16)};counts={1:set(),7:set()}
 for method,offset in dex.defined:
  if 'Lcom/savegame/SavesRestoringPortable;->SmartDataRestoreForYou(' not in method:continue
  c=dex.code(offset)
  for i in range(len(c)-5):
   if c[i]==0x0c13 and c[i+2]==0x0d13 and c[i+4]==0x0d4f and c[i+5] in [0x0c01,0x0c07] and c[i+1]<16:
    reg=c[i+5]&255;arrays[reg][c[i+1]]=c[i+3]&255;counts[reg].add(c[i+1])
 assert len(counts[1])==len(counts[7])==16
 d=Cipher(algorithms.AES(bytes(arrays[7])),modes.CBC(bytes(arrays[1]))).decryptor();raw=d.update(z.read('assets/data.save'))+d.finalize();n=raw[-1];assert raw[-n:]==bytes([n])*n
 inner=zipfile.ZipFile(io.BytesIO(raw[:-n]));return {'outer_format':'AES-128-CBC/PKCS7 then ZIP','entries':[{'name':n,'size':inner.getinfo(n).file_size,'sha256':sha(inner.read(n))} for n in inner.namelist()],'inner_settings_decrypted':False}

def seed_money(z):
 if 'assets/data/toons.ogg' not in z.namelist():return None
 inner=zipfile.ZipFile(io.BytesIO(z.read('assets/data/toons.ogg')))
 return {'outer_format':'ZIP despite .ogg filename','entries':[{'name':n,'size':inner.getinfo(n).file_size,'sha256':sha(inner.read(n))} for n in inner.namelist()],'inner_settings_decrypted':False,'profile_imported_into_build':False}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path,default=ROOT/'input/AngryBirdsSeasons_v6.6.2.apk');p.add_argument('--unlocked',type=Path);p.add_argument('--money',type=Path);a=p.parse_args();reports=ROOT/'reports';reports.mkdir(exist_ok=True);evidence=ROOT/'research/evidence';evidence.mkdir(exist_ok=True)
 with zipfile.ZipFile(a.original) as z:
  original={n:z.read(n) for n in z.namelist() if not signature_name(n)};dex=z.read('classes.dex')
  reference={n:sha(b) for n,b in original.items()};(reports/'original_reference.json').write_text(json.dumps({'apk_sha256':sha(a.original.read_bytes()),'entries':reference},indent=2)+'\n')
  patched,ev,new=transform(original,dict(unlock_all_episodes=True,unlocked_all_with_coins=True,unlock_all_levels=True,unlock_ragnahog_levels=True,quest_video=True,cosmetics=True),{'coins_amount':1000000})
  for row in ev:
   name=row['file'].replace('/','_')+'.'+row['prototype']
   (evidence/(name+'.before.dis')).write_text(row['before']+'\n');(evidence/(name+'.after.dis')).write_text(row['after']+'\n')
 comparisons=[]
 for label,file in [('unlocked',a.unlocked),('money_unlocked',a.money)]:
  if file is None:continue
  with zipfile.ZipFile(file) as z:
   data={n:z.read(n) for n in z.namelist() if not signature_name(n)}
   changed=[{'entry':n,'original_sha256':sha(original[n]),'modified_sha256':sha(data[n])} for n in sorted(set(data)&set(original)) if data[n]!=original[n]]
   lua=[n for n in original if n.startswith('assets/data/') and n.endswith(('.lua','.json'))]
   row={'label':label,'apk_sha256':sha(file.read_bytes()),'changed_entries':changed,'added_entries':sorted(set(data)-set(original)),'removed_entries':sorted(set(original)-set(data)),'lua_json_resources_equal':all(data.get(n)==original[n] for n in lua),'lua_json_resources_checked':len(lua),'native_libraries_equal':all(data.get(n)==original[n] for n in original if n.startswith('lib/') and n.endswith('.so')),'seed':seed_unlocked(z) if label=='unlocked' else seed_money(z)}
   semantic=compare(dex,data['classes.dex']);(reports/(label+'_dex_comparison.json')).write_text(json.dumps(semantic,indent=2)+'\n')
   row['dex_summary']={'added_methods':len(semantic['added_methods']),'removed_methods':len(semantic['removed_methods']),'changed_methods':len(semantic['changed_methods']),'unchanged_code_methods':semantic['unchanged_code_methods']};comparisons.append(row)
   # Preserve just restoration helper instructions, without executing them.
   d=Dex(data['classes.dex']);helpers={m:instructions(d,o) for m,o in d.defined if any(s in m for s in ['Lcom/android/Utils;->Start(','Lcom/android/Utils;->InternalDataRestore(','Lcom/savegame/SavesRestoringPortable;->DoSmth(','Lcom/savegame/SavesRestoringPortable;->SmartDataRestoreForYou('])}
   (reports/(label+'_restoration_helpers.json')).write_text(json.dumps(helpers,indent=2)+'\n')
 if comparisons:(reports/'input_comparisons.json').write_text(json.dumps(comparisons,indent=2)+'\n')
 print(json.dumps({'original_sha256':sha(a.original.read_bytes()),'comparisons':[(r['label'],r['dex_summary']) for r in comparisons],'lua_evidence_functions':len(ev)},indent=2))
if __name__=='__main__':main()
