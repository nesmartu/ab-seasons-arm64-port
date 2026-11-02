#!/usr/bin/env bash
# Read-only device inventory and log capture. Does not clear saves or install anything.
set -euo pipefail
OUT="${1:-device-logs}"
PACKAGE="${2:-com.rovio.seasonsport662.unofficial}"
mkdir -p "$OUT"
adb devices -l > "$OUT/devices.txt"
adb shell getprop ro.product.cpu.abilist > "$OUT/abis.txt"
adb shell getprop ro.build.version.release > "$OUT/android-version.txt"
adb shell getprop ro.build.fingerprint > "$OUT/build-fingerprint.txt"
adb shell getconf PAGE_SIZE > "$OUT/page-size.txt"
adb shell dumpsys package "$PACKAGE" > "$OUT/package.txt"
adb logcat -d -v threadtime > "$OUT/logcat.txt"
echo "Saved device inventory and logcat to $OUT"
