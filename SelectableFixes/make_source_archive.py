#!/usr/bin/env python3
"""Create a standalone patcher source archive without game APKs or generated results."""
import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
SKIP = {'build', 'dist', 'reports', 'evidence', 'validation_builds', '__pycache__', '.venv', 'venv', '.git'}


def files():
    for path in sorted(ROOT.rglob('*')):
        rel = path.relative_to(ROOT)
        if not path.is_file() or path.is_symlink() or set(rel.parts) & SKIP:
            continue
        if path.suffix.lower() in {'.apk', '.ipa', '.pyc', '.zip'}:
            continue
        yield path, rel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, default=ROOT.parent/'deliverables')
    args = parser.parse_args()
    dest = args.out_dir.resolve()
    if dest == ROOT or ROOT in dest.parents:
        raise ValueError('Write archives outside the standalone source tree')
    dest.mkdir(parents=True, exist_ok=True)
    payload = [(p, rel) for p, rel in files() if rel.as_posix() != 'SOURCE_FILES.sha256']
    manifest = ''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+rel.as_posix()+'\n' for p, rel in payload)
    (ROOT/'SOURCE_FILES.sha256').write_text(manifest)
    out = dest/'ab-seasons-selectable-fixes-sources.zip'
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, rel in files():
            info = zipfile.ZipInfo(ROOT.name+'/'+rel.as_posix(), (2026, 11, 2, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(out) as archive:
        assert archive.testzip() is None
    print(out, out.stat().st_size, hashlib.sha256(out.read_bytes()).hexdigest(), flush=True)


if __name__ == '__main__':
    main()
