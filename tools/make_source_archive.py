#!/usr/bin/env python3
"""Archive repository sources/dependencies without game APKs or generated build results."""
import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def selected(p):
    rel = p.relative_to(ROOT)
    generated = {'build', 'dist', 'reports', 'validation_builds', 'deliverables', '.venv', 'venv'}
    if rel.parts[0] in generated:
        return False
    if len(rel.parts) > 1 and rel.parts[0] in {'4.1.1', 'SelectableFixes'} and rel.parts[1] in generated:
        return False
    if rel.parts[:3] == ('SelectableFixes', 'research', 'evidence'):
        return False
    if p.suffix.lower() in {'.apk', '.ipa', '.pyc'}:
        return False
    if '__pycache__' in rel.parts or '.git' in rel.parts or p.is_symlink():
        return False
    if any(part.startswith(('seasons-repro-', 'seasons-rebuild-')) for part in rel.parts):
        return False
    if p.name.startswith('.') and any(marker in p.name for marker in ['.apk.', '.whl.', '.so.']):
        return False
    local = rel.parts[1:] if rel.parts[0] == '4.1.1' else rel.parts
    if len(local) >= 3 and local[:2] == ('bridge', 'out') and local[2] in {'arm64-v8a', 'x86_64'}:
        return False
    if local in {('bridge', 'gen', 'guest-engine.bin'), ('bridge', 'gen', 'engine_blob.S')}:
        return False
    if rel.as_posix() == 'SOURCE_FILES.sha256':
        return False
    return p.is_file()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('out',type=Path)
    a = ap.parse_args()
    out = a.out.resolve()
    assert ROOT not in out.parents, 'Write archive outside the source tree'
    files = sorted(p for p in ROOT.rglob('*') if selected(p))
    manifest = []
    for p in files:
        with p.open('rb') as f:
            h = hashlib.file_digest(f,'sha256').hexdigest()
        manifest.append(h+'  '+p.relative_to(ROOT).as_posix()+'\n')
    (ROOT/'SOURCE_FILES.sha256').write_text(''.join(manifest))
    files.append(ROOT/'SOURCE_FILES.sha256')
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9,allowZip64=True) as z:
        for p in sorted(files):
            n = 'ab-seasons-arm64-port/'+p.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(n,(2026,10,31,0,0,0))
            info.create_system = 3
            info.external_attr = (p.stat().st_mode & 0xffff) << 16
            compression = zipfile.ZIP_STORED if p.suffix in ['.apk','.whl'] else zipfile.ZIP_DEFLATED
            z.writestr(info,p.read_bytes(),compress_type=compression,compresslevel=9)
    with zipfile.ZipFile(out) as z:
        bad = z.testzip()
        assert bad is None,bad
        assert len(z.namelist()) == len(set(z.namelist()))
    print('Wrote',out,out.stat().st_size,'bytes;',len(files),'files; ZIP CRC PASS',flush=True)


if __name__ == '__main__':
    main()
