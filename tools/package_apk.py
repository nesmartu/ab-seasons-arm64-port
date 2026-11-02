#!/usr/bin/env python3
"""Package original Seasons 6.6.2 with the rebuilt 64-bit bridge; no Gradle/Java compilation."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

from axml import patch_manifest
from config import settings
from dex_native_reader import from_apk
import json

ROOT = Path(__file__).resolve().parents[1]
ENGINE = 'libAngryBirdsSeasonsFull.so'
STAMP = (2026, 10, 31, 0, 0, 0)


def sha256(p):
    with open(p, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def old_signature(name):
    if not name.upper().startswith('META-INF/'):
        return False
    return name.upper().endswith(('.SF', '.RSA', '.DSA', '.EC', '/MANIFEST.MF'))


def asset_index(names):
    entries = set()
    for n in names:
        if not n.startswith('assets/') or n == 'assets/assets.list' or n.endswith('/'):
            continue
        parts = n[7:].split('/')
        entries.add('/'.join(parts))
        entries.update('/'.join(parts[:k]) + '/' for k in range(1, len(parts)))
    return ''.join(e+'\n' for e in sorted(entries)).encode()


def apply_icons(content, cfg):
    if not cfg['icons']['custom']:
        return []
    directory = (ROOT / cfg['icons']['directory']).resolve()
    targets = sorted(n for n in content if n.startswith(('res/drawable','res/mipmap')) and n.endswith('/icon.png'))
    fallback = directory / 'icon.png'
    overrides = {p.relative_to(directory).as_posix():p for p in (directory/'res').rglob('*') if p.is_file()}
    unknown = set(overrides)-set(targets)
    if unknown:
        raise ValueError('Unknown icon resource paths: '+str(sorted(unknown)))
    changed=[]
    for name in targets:
        p=overrides.get(name, fallback)
        if not p.is_file():
            continue
        data=p.read_bytes()
        if not data.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('Custom icon must be a PNG: '+str(p))
        content[name]=data
        changed.append(name)
    if not changed:
        raise ValueError('Custom icons enabled but no matching PNG files found')
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apk', type=Path, required=True)
    ap.add_argument('--config', type=Path)
    ap.add_argument('--lib', type=Path)
    ap.add_argument('--tools', type=Path, default=ROOT.parent / 'toolchains')
    ap.add_argument('--abi', choices=['arm64-v8a', 'x86_64'], default='arm64-v8a')
    ap.add_argument('--out', type=Path)
    ap.add_argument('--allow-network', action='store_true', help='retain INTERNET permission (default: offline)')
    a = ap.parse_args()
    cfg = settings(a.apk, a.config)
    expected = [n for n in from_apk(a.apk) if n.removeprefix('static ').startswith('com.rovio.')]
    actual = [n for n in (ROOT/'bridge/natives.txt').read_text().splitlines() if n.removeprefix('static ').startswith('com.rovio.')]
    if expected != actual:
        raise ValueError('Bridge JNI declarations differ from input; run a full build first')
    network = a.allow_network or cfg['bridge']['allow_network']
    out = a.out or ROOT / 'dist' / (a.apk.stem+'-arm64.apk')
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    bt = a.tools.resolve() / 'sdk/android-16'
    env = dict(os.environ)
    java_home = Path(env.get('JAVA_HOME') or Path(shutil.which('java')).resolve().parents[1])
    env['JAVA_HOME'] = str(java_home)
    env['LD_LIBRARY_PATH'] = ':'.join(map(str, [bt/'lib64', java_home/'lib', java_home/'lib/server'])) + ':' + env.get('LD_LIBRARY_PATH','')
    tmp = ROOT / 'build/tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    env['TMPDIR'] = str(tmp)
    env['JAVA_TOOL_OPTIONS'] = '-Djava.io.tmpdir=' + str(tmp)
    unsigned = out.with_suffix('.unsigned.apk')
    aligned = out.with_suffix('.aligned.apk')
    lib = a.lib or ROOT / 'bridge/out' / a.abi / ENGINE
    with zipfile.ZipFile(a.apk) as src:
        content = {i.filename: src.read(i) for i in src.infolist()
                   if not i.is_dir() and not i.filename.startswith('lib/') and not old_signature(i.filename)}
        content['AndroidManifest.xml'] = patch_manifest(content['AndroidManifest.xml'], package=cfg['app']['package'], offline=not network, app_name=None if cfg['app']['preserve_original_name'] else cfg['app']['name'])
        content[f'lib/{a.abi}/{ENGINE}'] = lib.read_bytes()
        # The ARM32 guest is embedded as data inside the ELF64 bridge.
        assert src.read('lib/armeabi-v7a/'+ENGINE) in content[f'lib/{a.abi}/{ENGINE}']
    icon_changes = apply_icons(content, cfg)
    content['assets/absw/render_height'] = (str(cfg['bridge']['render_height'])+'\n').encode()
    content['assets/absw/max_fps'] = (str(cfg['bridge']['max_fps'])+'\n').encode()
    metadata = dict(project='ab-seasons-arm64-port', input_sha256=sha256(a.apk), app=cfg['app'], bridge=cfg['bridge'], icons_replaced=icon_changes, selectable_fixes=cfg['selectable_fixes'], fixes=cfg['fixes'])
    content['assets/abs662/build.txt'] = json.dumps(metadata, ensure_ascii=False, sort_keys=True).encode() + b'\n'
    content['assets/assets.list'] = asset_index(content)
    with zipfile.ZipFile(unsigned, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(content.items()):
            info = zipfile.ZipInfo(name, STAMP)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data, compresslevel=9)
    subprocess.run([str(bt/'zipalign'), '-f', '4', str(unsigned), str(aligned)], check=True, env=env)
    ks = ROOT/'signing/experiment1.p12'
    if not ks.exists():
        ks.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['keytool', '-genkeypair', '-storetype', 'PKCS12', '-keystore', str(ks),
                        '-alias', 'abs662', '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000',
                        '-dname', 'CN=Seasons Dynarmic Experiment 1', '-storepass', 'abs662-experiment',
                        '-keypass', 'abs662-experiment'], check=True, env=env)
    subprocess.run([str(bt/'apksigner'), 'sign', '--ks', str(ks), '--ks-pass', 'pass:abs662-experiment',
                    '--ks-key-alias', 'abs662', '--v1-signing-enabled', 'false', '--v2-signing-enabled', 'true',
                    '--v3-signing-enabled', 'true', '--v4-signing-enabled', 'false',
                    '--out', str(out), str(aligned)], check=True, env=env)
    subprocess.run([str(bt/'apksigner'), 'verify', '--verbose', str(out)], check=True, env=env)
    subprocess.run([str(bt/'zipalign'), '-c', '4', str(out)], check=True, env=env)
    unsigned.unlink()
    aligned.unlink()
    print(out, out.stat().st_size, 'bytes; sha256', sha256(out))


if __name__ == '__main__':
    main()
