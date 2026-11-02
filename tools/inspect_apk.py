#!/usr/bin/env python3
"""Static compatibility and preservation checks; never claims device execution."""
import argparse,hashlib,json,re,struct,zipfile
from pathlib import Path
from config import ROOT,ENGINE,settings
from elf_reader import Elf
from dex_native_reader import from_apk
from gen_natives import mangle
from axml import manifest_attrs
from package_apk import asset_index,apply_icons

def digest(b):return hashlib.sha256(b).hexdigest()

def preflight(src):
 with zipfile.ZipFile(src) as z:ge=Elf(z.read('lib/armeabi-v7a/'+ENGINE))
 if ge.bits!=32 or ge.machine!=40:raise ValueError('Expected an ARM32 Seasons engine')
 cpp='\n'.join(p.read_text() for p in (ROOT/'bridge/src').glob('*.cpp'))
 provided=set(re.findall(r'(?:H|HE|HRAW|add_data|add_table_pointer)\("([^"]+)"',cpp))
 runtime=Elf((ROOT/'bridge/out/guest/libabsw_rt.so').read_bytes())
 missing=sorted(ge.imports()-provided-runtime.exports())
 if missing:raise ValueError('Unsupported engine imports: '+', '.join(missing))
 native_rows=from_apk(src);table=set()
 for row in native_rows:
  m=re.fullmatch(r'(?:static )?([\w.$]+)\.([\w$]+)(\(.*)',row)
  if m and m[1].startswith('com.rovio.'):table.add('Java_'+mangle(m[1].replace('.','/'))+'_'+mangle(m[2]))
 exports={n for n in ge.exports() if n.startswith('Java_')}
 # Extra engine exports without DEX declarations are never registered or called.
 reloc=ge.relocations32()
 if reloc.keys()-{0,2,3,21,22,23}:raise ValueError('Unsupported ELF relocations: '+str(reloc))
 return dict(guest_imports=len(ge.imports()),missing_imports=missing,unused_jni_exports=sorted(exports-table),guest_jni_exports=len(exports),dex_native_methods=len(native_rows),relocations=dict(reloc))


def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('apk',type=Path);ap.add_argument('--source',type=Path,required=True)
 ap.add_argument('--json',type=Path);ap.add_argument('--config',type=Path)
 a=ap.parse_args();cfg=settings(a.source,a.config);checks=preflight(a.source)
 with zipfile.ZipFile(a.source) as src,zipfile.ZipFile(a.apk) as built:
  assert built.testzip() is None
  assert len(built.namelist())==len(set(built.namelist()))
  guest=src.read('lib/armeabi-v7a/'+ENGINE);libs=[n for n in built.namelist() if n.startswith('lib/')]
  assert libs==['lib/arm64-v8a/'+ENGINE],libs
  hb=built.read(libs[0]);host=Elf(hb)
  assert host.bits==64 and host.machine==183 and hb.count(guest)==1
  alignments=[s[-1] for s in host.segments if s[0]==1];assert all(n>=16384 for n in alignments)
  expected={n:src.read(n) for n in src.namelist() if not n.endswith('/')}
  icon_changes=apply_icons(expected,cfg)
  assets=[n for n in expected if n.startswith('assets/') and n!='assets/assets.list']
  assert all(expected[n]==built.read(n) for n in assets)
  dex=[n for n in expected if n.endswith('.dex')];assert all(expected[n]==built.read(n) for n in dex)
  assert expected['resources.arsc']==built.read('resources.arsc')
  assert all(expected[n]==built.read(n) for n in expected if n.startswith('res/'))
  assert built.read('assets/assets.list')==asset_index(built.namelist())
  tags=manifest_attrs(built.read('AndroidManifest.xml'))
  manifest=next(v for k,v in tags if k=='manifest');app=next(v for k,v in tags if k=='application');sdk=next(v for k,v in tags if k=='uses-sdk')
  assert manifest['package']==cfg['app']['package']
  if cfg['app']['preserve_original_name']:
   original_tags=manifest_attrs(src.read('AndroidManifest.xml'))
   assert [(k,v['label']) for k,v in tags if 'label' in v]==[(k,v['label']) for k,v in original_tags if 'label' in v]
  else:
   assert app['label']==cfg['app']['name']
   assert all(v['label']==cfg['app']['name'] for k,v in tags if k in ['activity','activity-alias'] and 'label' in v)
  assert sdk['minSdkVersion']==26 and sdk['targetSdkVersion']==28
  internet=any(k=='uses-permission' and v.get('name')=='android.permission.INTERNET' for k,v in tags)
  assert internet==cfg['bridge']['allow_network']
 report=dict(kind='static checks; no device execution',input=a.source.name,input_sha256=digest(a.source.read_bytes()),apk=a.apk.name,apk_sha256=digest(a.apk.read_bytes()),guest_sha256=digest(guest),host_sha256=digest(hb),exact_guest_embedded=True,host_load_alignment=alignments,unchanged_assets=len(assets),unchanged_dex_files=dex,resources_preserved_except_configured_icons=True,icons_replaced=icon_changes,settings=cfg,runtime_tested=False,**checks)
 text=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
 if a.json:a.json.parent.mkdir(parents=True,exist_ok=True);a.json.write_text(text)
 print(text)

if __name__=='__main__':main()
