# Components and licensing provenance

[Русский](PROVENANCE_RU.md)

| Component | Recorded source/version | Location |
|---|---|---|
| Bridge base | [MrEmpathy/angry-birds-star-wars-II-arm64](https://github.com/MrEmpathy/angry-birds-star-wars-II-arm64), commit `18615db1805fdf8ef3f93a8ba82608f1d206c1b7` | `bridge/`, adapted runtime/shims/JNI tools; separate adaptation in `4.1.1/` |
| Dynarmic | [Vita3K/dynarmic](https://github.com/Vita3K/dynarmic), commit `c9298d3d39323032420e77ddda4d4266e758fa5e` | `third_party/dynarmic/`; local patches in each `tools/patch_dynarmic.py` and SMT guard in build.py |
| Boost | 1.86.0, [upstream archive](https://archives.boost.io/release/1.86.0/source/boost_1_86_0.tar.gz) | `third_party/boost/`; Boost Software License 1.0 |
| Vendored Dynarmic dependencies | fmt 10.1.0, mcl 0.1.12, oaknut 2.0.2, robin-map 0.6.2, xbyak 7.05, Zydis 4.0.0.0, Zycore 1.4.0.0, biscuit 0.14.0, Catch2 3.5.0 | `third_party/dynarmic/externals/`; individual notices retained |
| Bridge utility sources | dlmalloc 2.8.6; stb_sprintf 1.10 | `bridge/third_party/` and `4.1.1/bridge/third_party/`; notices in source |
| Android tools | NDK r27d / 27.3.13750724; Build Tools 36.0.0 | downloaded by setup; URL/SHA-256 in setup and `VERSIONS.lock.json` |
| Host build wheels | CMake 3.30.5; Ninja package 1.11.1.1 | `tools/wheels/`; packaged notices retained |
| Python patch dependency | cryptography 50.0.2 | pinned in requirements; installed separately |

Independent commits for vendored dependency subtrees were not recorded; the archive checksum manifest pins their contents. Not every vendored subtree is linked for ARM64. The earlier bridge base cited by upstream documentation is [angry-birds-starwars-hd-arm64](https://github.com/MrEmpathy/angry-birds-starwars-hd-arm64); its exact earlier commit is not recorded.

A bridge-wide license grant was not present in the source provenance. No new blanket license is asserted for this combined repository. Retain component licenses and obtain any missing permissions before redistributing or relicensing those sources. Game engine/assets belong to their respective rights holders; APKs and prebuilt bridges embedding the game engine are not part of the source package.

The bridge translates ARMv7 guest code through Dynarmic and provides Android/JNI/GLES/libc shims. ARM32 helper runtime uses softfp/NEON, ARM64 host API 26/C++20/static libc++, with 16 KiB ELF load alignment checks. ZIP timestamps and SOURCE_DATE_EPOCH are fixed by the scripts; byte-identical output also depends on pinned tools and compression libraries.

The included port PKCS12 key is a public development key, RSA-2048, alias `abs662`, password `abs662-experiment`; v2/v3 signing is enabled and v1/v4 disabled. It is not a private production credential. The standalone ARM32 patcher uses a separate public PEM key/certificate and v1/v2 signatures. Neither key is Rovio's original key. See `signing/README_EN.md`.

SelectableFixes modifies encoded JSON/Lua resources without importing another saved profile or replacing DEX/native engines. Its local research utilities include Lua/DEX readers and a limited VM for mocked behavior tests. Format references: [Lua 5.1](https://www.lua.org/manual/5.1/manual.html), [DEX](https://source.android.com/docs/core/runtime/dalvik-bytecode), [APK v2](https://source.android.com/docs/security/features/apksigning/v2). Resource-key reference: [Angry_Birds_Decompilation](https://github.com/jooapa/Angry_Birds_Decompilation). These are provenance references, not downloaded build dependencies.
