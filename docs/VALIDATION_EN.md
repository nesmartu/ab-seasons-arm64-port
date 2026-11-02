# Validation snapshot

[Русский](VALIDATION_RU.md) · [Commands](VERIFICATION_EN.md)

Checked on 2026-11-02, Linux x86_64, Python 3.12.14, zlib 1.3.2, Java 17, pinned NDK r27d/Build Tools 36.0.0/CMake 3.30.5/Ninja 1.11.1.1. Machine-readable results: [validation.json](validation.json).

| Check | Result |
|---|---|
| Default full native build, original 6.6.2 | Pass |
| Default full native build, alternate-source attachment | Pass |
| Separate patch/port audits, signatures, alignment, data preservation | Pass for both inputs |
| Two clean full native repeat runs | Signed APKs and bridges byte-identical; also match the initial builds |
| Main / 4.1.1 configuration tests | 14 / 12 passed |
| Lua behavior tests on each input | 18 / 18 passed; includes 64 flag combinations |
| Standalone default ARM32 build + audit | Pass, including independent OpenSSL CMS check |
| Authored Python/TOML syntax, documentation links, RU/EN pairs | Pass |

Both supplied APK files have identical bytes and SHA-256 `4d02bef2a363b48d33744c748588a2f8e1d5fcf96b4bd8ea6973a8c9ec84a148`. This validates both supplied paths, but does not demonstrate compatibility with a different repack or engine. Default package remains `com.rovio.angrybirdsseasons.port`; default fixes are episode access, Ragnahog and quest hints.

The 4.1.1 configuration and shared dependency/tool paths were checked, but its native bridge was not rebuilt in this validation. Installation/gameplay on Android devices was not tested. Generated logs and historical build reports are excluded from the source package.
