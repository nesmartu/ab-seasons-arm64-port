# ab-seasons-arm64-port

[Русский](README_AI_RU.md) · [Build guide](BUILD_EN.md) · [Components and licenses](PROVENANCE_EN.md)

Unofficial Android ARM64 adaptation of the Angry Birds Seasons ARM32 engine using Dynarmic. The main project targets Seasons 6.6.2. The separate `4.1.1/` experiment uses a different bridge/JNI interface.

Supply your own original APK in `input/`; game APKs, assets and engine-containing ARM64 libraries are not included. Build scripts extract and embed the original engine locally. Host requirements: Linux x86_64, Python 3.11+, Java 17. Outputs target Android API 26+, `arm64-v8a`, targetSdk 28.

```bash
python3 -m venv ../seasons-venv
source ../seasons-venv/bin/activate
python -m pip install -r requirements.txt
python tools/setup_toolchain.py --tools ../toolchains
# Place your original 6.6.2 APK in input/ first.
python tools/release.py --tools ../toolchains --jobs 4
```

The default build applies episode access, the Ragnahog calendar repair and immediate quest video hints before compiling the port. Coins, cosmetics and full level unlock are off. Output package: `com.rovio.angrybirdsseasons.port`; original display labels and icons are preserved. Input-package preservation and `.fixed` are off. Render height is 1080, frame cap 60, INTERNET permission removed. See [settings](docs/SETTINGS_EN.md) and `build_config.toml`.

| Preset in `configs/` | Game changes |
|---|---|
| `original.toml` | No selectable fixes |
| `unlocked_ragnahog_quest.toml` | Default episode access + Ragnahog + quest hints |
| `unlocked_money_ragnahog_quest.toml` | Same + one-time minimum coin balance |
| `unlocked_money_ragnahog_quest_cosmetics.toml` | Same + all 108 Bird Wear items |
| `unlocked_money_ragnahog_quest_cosmetics_alllevels.toml` | Same + all shipped local levels/eggs/bonuses |

Use `--config configs/original.toml`, for example. All presets share the default package and public development signing key, so they replace one another. Package ID and cryptographic certificate are separate settings; the original Rovio certificate cannot sign modified builds.

`unlock_all_episodes` retains ordinary progression and earned egg/star/feather gates. `unlock_ragnahog_levels` opens the 25 regular Ragnahog calendar levels and preserves its three bonus/egg requirements. `unlock_all_levels` explicitly bypasses local level/egg/bonus access; it does not award scores or restore missing online content. Disabled patches do not undo modifications or saved unlocks.

`SelectableFixes/` also runs independently and produces ARM32 APKs. Fixes are supported only for 6.6.2. Engine ELF/import/relocation/JNI checks remain active; there is no whole-APK hash or filename allowlist. Other engines may require bridge changes.

Repository layout: `bridge/` native bridge and generated helper code; `third_party/` shared vendored dependencies; `tools/` compilation, packaging and audits; `configs/` presets; `tests/` configuration checks; `SelectableFixes/` patcher/tests; `4.1.1/` older-engine experiment. Generated `build/`, `dist/` and `reports/` are ignored and excluded from source archives.

See [verification](docs/VERIFICATION_EN.md) and [device checks](docs/DEVICE_TESTING_EN.md). Successful automated builds do not establish installation or gameplay compatibility. Component licenses/notices remain in their original languages; project guides are available in English and Russian.
