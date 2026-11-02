#!/usr/bin/env python3
"""Build the ARM32 guest runtime and real 64-bit Seasons/Dynarmic bridge. Linux x86_64."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
from dex_native_reader import from_apk
from config import ENGINE

ROOT = Path(__file__).resolve().parents[1]


def run(cmd, log=None):
    print('+', ' '.join(map(str, cmd)), flush=True)
    if log:
        with open(log, 'w') as f:
            result = subprocess.run(list(map(str, cmd)), stdout=f, stderr=subprocess.STDOUT)
        if result.returncode:
            print(Path(log).read_text()[-16000:])
            raise SystemExit(result.returncode)
    else:
        subprocess.run(list(map(str, cmd)), check=True)


def blob(src, dst):
    b = Path(src).read_bytes()
    Path(dst).write_text(''.join(','.join(map(str, b[i:i+24])) + ',\n' for i in range(0, len(b), 24)))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apk', type=Path, required=True)
    ap.add_argument('--tools', type=Path, default=ROOT.parent / 'toolchains')
    ap.add_argument('--abi', choices=['arm64-v8a', 'x86_64'], default='arm64-v8a')
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--trace', action='store_true')
    a = ap.parse_args()
    t = a.tools.resolve()
    ndk = t / 'android-ndk-r27d'
    llvm = ndk / 'toolchains/llvm/prebuilt/linux-x86_64/bin'
    cmake = t / 'python/cmake/data/bin/cmake'
    ninja = t / 'python/ninja/data/bin/ninja'
    dyn = ROOT / 'third_party/dynarmic'
    gen = ROOT / 'bridge/gen'
    out = ROOT / 'bridge/out' / a.abi
    build = ROOT / 'build' / a.abi
    gb = ROOT / 'build/guest'
    logs = ROOT / 'reports'
    for p in [gen, out, build, gb, logs]:
        p.mkdir(parents=True, exist_ok=True)
    (ROOT / 'build/tmp').mkdir(exist_ok=True)
    os.environ['TMPDIR'] = str(ROOT / 'build/tmp')
    os.environ['SOURCE_DATE_EPOCH'] = '1793404800'
    apk = a.apk.resolve()
    with zipfile.ZipFile(apk) as z:
        engine = z.read('lib/armeabi-v7a/'+ENGINE)
    (gen / 'guest-engine.bin').write_bytes(engine)
    (ROOT / 'bridge/natives.txt').write_text('\n'.join(from_apk(apk))+'\n')
    (gen / 'engine_blob.S').write_text(
        '.section .rodata.abs662_guest,"a"\n.balign 16\n'
        '.global abs662_guest_image\n.hidden abs662_guest_image\nabs662_guest_image:\n'
        f'.incbin "{(gen / "guest-engine.bin").as_posix()}"\n'
        '.global abs662_guest_image_end\n.hidden abs662_guest_image_end\nabs662_guest_image_end:\n'
        '.section .note.GNU-stack,""\n')
    run([sys.executable, ROOT / 'tools/patch_dynarmic.py', dyn], logs / 'dynarmic-patches.log')
    # xbyak divides by a zero SMT width on some virtual AMD CPUs.
    xu = dyn / 'externals/xbyak/xbyak/xbyak_util.h'
    s = xu.read_text()
    s = s.replace('actual_logical_cores / smt_width,',
                  '(smt_width ? actual_logical_cores / smt_width : actual_logical_cores),')
    xu.write_text(s)
    cc = [str(llvm / 'clang'), '--target=armv7a-linux-androideabi16', '-marm',
          '-mfloat-abi=softfp', '-mfpu=neon', f'-ffile-prefix-map={ROOT}=.']
    run(cc + ['-O2', '-fPIC', '-ffreestanding', '-fno-stack-protector', '-c',
              ROOT / 'bridge/guest/rt.c', '-o', gb / 'rt.o'])
    run(cc + ['-c', ROOT / 'bridge/guest/setjmp.S', '-o', gb / 'setjmp.o'])
    builtins = subprocess.check_output(cc + ['-print-libgcc-file-name'], text=True).strip()
    run(cc + ['-shared', '-nostdlib', '-Wl,-soname,libabsw_rt.so', '-Wl,--hash-style=both',
              '-o', gb / 'libabsw_rt.so', gb / 'rt.o', gb / 'setjmp.o', builtins])
    blob(gb / 'libabsw_rt.so', gen / 'guest_rt_blob.inc')
    (ROOT / 'bridge/out/guest').mkdir(parents=True, exist_ok=True)
    shutil.copy2(gb / 'libabsw_rt.so', ROOT / 'bridge/out/guest/libabsw_rt.so')
    run(cc + ['-c', ROOT / 'bridge/guest/kuser.S', '-o', gb / 'kuser.o'])
    run([llvm / 'llvm-objcopy', '-O', 'binary', '--only-section=.text', gb / 'kuser.o', gb / 'kuser.bin'])
    assert (gb / 'kuser.bin').stat().st_size == 0xa0
    blob(gb / 'kuser.bin', gen / 'kuser_blob.inc')
    run([sys.executable, ROOT / 'tools/gen_natives.py', ROOT / 'bridge/natives.txt', gen / 'natives_gen.inc'])
    run([cmake, '-S', ROOT / 'bridge', '-B', build, '-G', 'Ninja',
         f'-DCMAKE_MAKE_PROGRAM={ninja}', f'-DCMAKE_TOOLCHAIN_FILE={ndk}/build/cmake/android.toolchain.cmake',
         f'-DANDROID_ABI={a.abi}', '-DANDROID_PLATFORM=android-26', '-DANDROID_STL=c++_static',
         '-DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON', '-DCMAKE_BUILD_TYPE=RelWithDebInfo',
         f'-DBoost_INCLUDE_DIR={ROOT}/third_party/boost', f'-DDYNARMIC_SRC={dyn}',
         f'-DABSW_GEN_DIR={gen}', f'-DABSW_TRACE={"ON" if a.trace else "OFF"}'],
        logs / f'configure-{a.abi}.log')
    run([cmake, '--build', build, '--target', 'AngryBirdsSeasonsFull', '-j', a.jobs],
        logs / f'build-{a.abi}.log')
    lib = 'libAngryBirdsSeasonsFull.so'
    run([llvm / 'llvm-strip', '--strip-unneeded', '-o', out / lib, build / lib])
    shutil.copy2(build / lib, out / 'libAngryBirdsSeasonsFull.debug.so')
    print('Built', out / lib, (out / lib).stat().st_size, 'bytes')


if __name__ == '__main__':
    main()
