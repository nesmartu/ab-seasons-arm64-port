# Seasons 4.1.1 experiment

[Русский](README_RU.md) · [Shared build guide](../BUILD_EN.md)

Separate bridge for the older `MyRenderer`/`MyLegacyRenderer` JNI interface. Supply an original **4.1.1**, not 4.1.0, APK in this folder's `input/`. This experiment is part of the complete repository: it shares `../third_party/` and `../tools/wheels/`.

From the repository root, prepare the shared toolchain as in the main guide. Then:

```bash
cd 4.1.1
python tools/release.py --tools ../../toolchains --jobs 4
```

The default toolchain path is also `../../toolchains`. Outputs and reports are local to this experiment. Defaults: custom package `com.rovio.angrybirdsseasons.port411`, input-package preservation off, original display names/icons kept, render height 0, frame cap 60, network permission removed. No SelectableFixes stage is applied. `--package-only` requires a locally compiled matching bridge. A full repository archive is produced by `tools/make_source_archive.py`; shared dependencies are included.

Engine compatibility and gameplay remain experimental. This source package's two-input build validation concerns 6.6.2; no 4.1.1 device test is claimed. See the shared [components](../PROVENANCE_EN.md), [settings](../docs/SETTINGS_EN.md) and [device plan](../docs/DEVICE_TESTING_EN.md).
