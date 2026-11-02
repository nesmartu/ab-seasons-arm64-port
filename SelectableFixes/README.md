# SelectableFixes

[Русский](README_RU.md) · [Main project](../README.md) · [Patch internals](RESEARCH_EN.md)

Independent JSON/Lua patcher for original Angry Birds Seasons 6.6.2 / 6620 Android APKs. It creates **ARM32** APKs, preserves the original package/labels/DEX/native engines, and signs with the included public development PEM key. It needs Python 3.11+, standard `lzma` and `cryptography==50.0.2`; no Android SDK/NDK, Java, Gradle or Lua compiler is required.

From the repository root:

```bash
python -m pip install -r SelectableFixes/requirements.txt
python SelectableFixes/build.py --input input/game.apk --out-dir standalone-dist
python SelectableFixes/verify.py --input input/game.apk --dir standalone-dist
```

Replace `input/game.apk` with your original 6.6.2 file. With no CLI input, `build_config.toml` expects `SelectableFixes/input/AngryBirdsSeasons_v6.6.2.apk`. Paths in a selected standalone config resolve relative to that config's folder; preset configs therefore use `../input/`, `../signing/` and `../dist/`. CLI paths resolve from the working directory. `--config` selects a preset under `SelectableFixes/configs/`.

Defaults match the main project's fixes: episode access, Ragnahog and quest hints on; money, cosmetics and full levels off. [Settings and scope](../docs/SETTINGS_EN.md) describe each flag and compatibility aliases. Standalone `[options].coins_amount` sets the one-time minimum balance; `[build]` selects input, output directory, filename suffix and key/certificate paths. The suffix changes only the filename. Standalone does not implement the main builder's package/render settings.

```bash
# Build five combined presets from one original input:
python SelectableFixes/build.py --matrix --input input/game.apk
python SelectableFixes/verify.py --input input/game.apk
python SelectableFixes/check_reproducible.py --input input/game.apk
# Build/audit all-off and each individual flag:
python SelectableFixes/check_builds.py --input input/game.apk
```

`verify.py` audits resource boundaries, unchanged DEX/resources/native engines, selected Lua prototypes, ZIP CRC/alignment, v1 hashes/CMS (OpenSSL CLI when present), v2 signing and tamper rejection. It writes audit JSON next to outputs under `reports/`. Behavior tests use `SEASONS_TEST_APK` as in the main [verification guide](../docs/VERIFICATION_EN.md). These are automated checks, not device gameplay tests.

False flags do not undo patches or saved progress. To remove a broad patch, rebuild from an original input; previously saved unlocks remain. Unsupported resource structures or modified patch metadata fail instead of silently creating a partial result. Use only 6.6.2; there is no whole-APK hash allowlist. Sources contain no input/output APKs. Generate a standalone source ZIP with `python SelectableFixes/make_source_archive.py --out-dir /path/outside/source`.
