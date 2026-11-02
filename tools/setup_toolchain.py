#!/usr/bin/env python3
"""Install pinned Android tools into a user-writable directory. No sudo required."""
import argparse
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = [
    ('android-ndk-r27d-linux.zip', 'https://dl.google.com/android/repository/android-ndk-r27d-linux.zip',
     '601246087a682d1944e1e16dd85bc6e49560fe8b6d61255be2829178c8ed15d9', 'android-ndk-r27d'),
    ('build-tools_r36_linux.zip', 'https://dl.google.com/android/repository/build-tools_r36_linux.zip',
     '5d9ac77fb6ff43d9da518a337b4fcf8f9097113df531d99ccefe80ef7ce8250b', 'sdk/android-16'),
]


def sha(p):
    with open(p,'rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def extract(src, dst):
    links = []
    with zipfile.ZipFile(src) as z:
        for i in z.infolist():
            p = dst/i.filename
            assert dst.resolve() in p.resolve().parents, i.filename
            mode = i.external_attr >> 16
            if stat.S_ISLNK(mode):
                links.append((p,z.read(i).decode()))
            else:
                z.extract(i,dst)
                if mode & 0o777:
                    p.chmod(mode & 0o777)
    for p,target in links:
        assert dst.resolve() in (p.parent/target).resolve().parents
        p.unlink(missing_ok=True)
        p.symlink_to(target)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--tools', type=Path, default=ROOT.parent/'toolchains')
    a = ap.parse_args()
    t = a.tools.resolve()
    (t/'downloads').mkdir(parents=True,exist_ok=True)
    for name,url,expected,installed in DOWNLOADS:
        archive = t/'downloads'/name
        if not archive.exists() or sha(archive) != expected:
            partial = archive.with_suffix('.part')
            print('Downloading',name,flush=True)
            urllib.request.urlretrieve(url,partial)
            assert sha(partial) == expected, 'Download checksum mismatch: '+name
            partial.replace(archive)
        if not (t/installed).is_dir():
            print('Extracting',name,flush=True)
            dst = t if installed.startswith('android-ndk') else t/'sdk'
            dst.mkdir(parents=True,exist_ok=True)
            extract(archive,dst)
    subprocess.run([sys.executable,'-m','pip','install','--no-index','--find-links',str(ROOT/'tools/wheels'),
                    '--target',str(t/'python'),'cmake==3.30.5','ninja==1.11.1.1'],check=True)
    print('Toolchain ready:',t)
    print('Also install a working OpenJDK 17 runtime (java + keytool). No Gradle or SDK platform is required.')


if __name__ == '__main__':
    main()
