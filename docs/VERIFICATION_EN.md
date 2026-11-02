# Automated verification

[Русский](VERIFICATION_RU.md)

Run from the repository root after installing requirements:

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s 4.1.1/tests -v
SEASONS_TEST_APK="$PWD/input/game.apk" python -m unittest discover -s SelectableFixes/tests -v
python tools/release.py --tools ../toolchains --jobs 4
```

Set `SEASONS_TEST_APK` to an actual original 6.6.2 input filename. Configuration tests use small manifest fixtures and need no full APK. Behavior tests execute original/patched Lua with mocked services: 64 flag combinations, idempotence, additive order, unrelated-resource preservation, 25 Ragnahog levels and three earned/unearned eggs, star/feather gates, one-time coins, quest interfaces, 108 cosmetics and 21 calendar/startup cases.

The release pipeline performs separate patch and port audits. It checks ZIP CRC/paths, original DEX/resources/engine preservation at the patch stage, selected Lua/JSON edits, ARM64 ELF/embedded guest/JNI/imports/relocations, 16 KiB ELF segment alignment, labels/icons/package/settings, signatures and ZIP alignment.

To check deterministic output in two clean directories (requires populated `input/`):

```bash
python tools/check_reproducible.py --tools ../toolchains --jobs 4
```

Use `--package-only` only to test repackaging with an already built matching bridge; it does not prove native compilation. For standalone per-flag builds/audits, use `python SelectableFixes/check_builds.py --input input/game.apk`. The standalone `--matrix` emits five combined presets and its `check_reproducible.py` compares them with a clean rebuild.

Generated logs/audits belong in ignored `reports/` folders, not versioned release history. The concise validation snapshot in this folder records what was actually checked for this source package. Device execution is a separate [test plan](DEVICE_TESTING_EN.md).
