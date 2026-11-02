# Build guide

[Русский](BUILD_RU.md) · [Overview](README.md)

Run commands from `ab-seasons-arm64-port/`. Linux x86_64 is the supported toolchain host. Allow approximately 12 GB disk and 8 GB RAM; use `--jobs 1` or `--jobs 2` on smaller machines. Install Python 3.11+ with venv/pip, Java 17, CA certificates and unzip. No Android Studio, Gradle, apktool or Java compilation is required.

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip openjdk-17-jdk-headless ca-certificates unzip
python3 -m venv ../seasons-venv
source ../seasons-venv/bin/activate
python -m pip install -r requirements.txt
python tools/setup_toolchain.py --tools ../toolchains
# Copy an original Seasons 6.6.2 APK into input/.
python tools/release.py --tools ../toolchains --jobs 4
```

Setup downloads checksum-verified NDK r27d and Build Tools 36.0.0, and installs CMake 3.30.5/Ninja 1.11.1.1 from bundled wheels. These checksums validate tools, not game inputs. Setup requires network access; subsequent builds can run offline. Dependency sources and licenses are vendored under `third_party/`.

With no `--apk`, every direct `input/*.apk` is processed; filenames need not match the example. To select one file or another preset:

```bash
python tools/release.py --tools ../toolchains --apk /path/to/game.apk
python tools/release.py --tools ../toolchains --config configs/original.toml
```

The release command checks compatibility, applies enabled fixes to `build/prepared/<output-stem>/<input-name>.apk`, audits that ARM32 result, compiles the guest runtime and ARM64 bridge, signs/aligns the port and checks data preservation. Fix failure aborts the build. The original input is not overwritten. Use `tools/release.py` for this complete pipeline; low-level `tools/build.py` and `tools/package_apk.py` do not apply fixes themselves.

Results: `dist/<input-stem><recipe>-arm64.apk` and matching `.bridge.so`. Reports: `reports/<input-stem><recipe>/`, batch index `reports/batch.json`. Recipes are encoded in output filenames; changing only package/render settings can overwrite the same recipe output. See [settings](docs/SETTINGS_EN.md).

After a full build, `--package-only` can reuse that bridge only if the input engine bytes and JNI declarations match. The archive contains no prebuilt port bridge. A missing bridge or an engine/JNI mismatch requires a full build. Moving an existing CMake build directory also requires removing `build/` first.

On Windows use Ubuntu x86_64 under WSL2, extract the project into the Linux filesystem and run the Linux commands. On macOS use a Linux x86_64 VM or Docker with `--platform linux/amd64`; Apple Silicon needs emulation. Native PowerShell/macOS/Termux and Linux ARM64 are not supported by the pinned host tools. Those alternative hosts are not separately validated here.

The [standalone patcher](SelectableFixes/README.md) needs only Python and cryptography. The [4.1.1 experiment](4.1.1/README.md) uses its own input/config/bridge and the shared dependencies/toolchain; it does not apply 6.6.2 fixes.

Run [verification commands](docs/VERIFICATION_EN.md) after changes. Create a clean source ZIP with:

```bash
python tools/make_source_archive.py ../ab-seasons-arm64-port-sources.zip
```

The output must be outside the source tree. APKs, generated reports, build/dist caches, port bridges containing game engines and generated engine blobs are excluded. Input README files, helper runtime, public development keys, vendored dependencies and tool wheels remain. `SOURCE_FILES.sha256` records every archived payload file except itself. Do not replace license notices with a project-wide license without resolving the bridge's licensing provenance.
