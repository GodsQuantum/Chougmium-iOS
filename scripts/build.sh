#!/bin/sh
set -eu
: "${THEOS:?Set THEOS to a working Theos installation (iPhoneOS10.3 SDK, ARMv7 toolchain)}"
cd "$(dirname "$0")/.."
./tests/run.sh
python3 tests/test_manifest.py
stage="$(mktemp -d "${TMPDIR:-/tmp}/venetium-compat-stage.XXXXXXXX")"
trap 'rm -rf "$stage"' EXIT
chmod 0755 "$stage"
make clean package FINALPACKAGE=1 THEOS_STAGING_DIR="$stage"
mkdir -p releases
cp packages/com.local.venetium-uikit-compat_0.1.1_iphoneos-arm.deb releases/
python3 tests/test_deb.py
sha256sum releases/com.local.venetium-uikit-compat_0.1.1_iphoneos-arm.deb

