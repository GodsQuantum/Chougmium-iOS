#!/usr/bin/env python3
"""Regression contract for the Chougmium iOS 9 one-package release."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import plistlib
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "docs/debs/ru.computershik.venetium_150.7871.222.1+chougmium4_iphoneos-arm.deb"
UPSTREAM_EXE_SHA = "2dacf0c78e0313a098b9f5c8f6a85a9a19f92df23530543599a3d0dc2ff7bca2"

def dpkg_field(name):
    return subprocess.check_output(["dpkg-deb", "-f", str(PKG), name], text=True).strip()

def check():
    assert PKG.is_file(), "Chougmium package does not exist yet"
    assert dpkg_field("Package") == "ru.computershik.venetium", "preserve app identity"
    assert dpkg_field("Name") == "Chougmium"
    assert dpkg_field("Version") == "150.7871.222.1+chougmium4"
    assert dpkg_field("Architecture") == "iphoneos-arm"
    assert "data.tar.lzma" in subprocess.check_output(["ar", "t", str(PKG)], text=True).splitlines(), "Use proven upstream Cydia compression"
    depends = dpkg_field("Depends")
    assert "firmware (>= 9.0)" in depends and "firmware (<< 10.0)" in depends
    assert "mobilesubstrate" in depends
    with TemporaryDirectory(prefix="chougmium-verify-") as tmp:
        subprocess.run(["dpkg-deb", "-x", str(PKG), tmp], check=True)
        root = Path(tmp)
        app = root / "Applications/Venetium.app"
        info = plistlib.loads((app / "Info.plist").read_bytes())
        assert info["CFBundleIdentifier"] == "ru.computershik.venetium"
        assert info["CFBundleExecutable"] == "Venetium"
        assert info["CFBundleDisplayName"] == "Chougmium"
        assert info["CFBundleName"] == "Chougmium"
        assert (app / "Venetium").stat().st_size > 100_000_000
        assert hashlib.sha256((app / "Venetium").read_bytes()).hexdigest() == UPSTREAM_EXE_SHA
        assert len(list(app.glob("Icon*.png"))) >= 10
        for icon in app.glob("Icon*.png"):
            raw = icon.read_bytes()
            assert raw.startswith(b"\x89PNG\r\n\x1a\n"), icon.name
            # PNG IHDR color type 2 means RGB; reject the legacy color-map type 3.
            assert raw[25] in (2,6), (icon.name, raw[25])
        for path in app.glob("*.lproj/Localizable.strings"):
            strings = plistlib.loads(path.read_bytes())
            for key, value in strings.items():
                if key == "About Venetium":
                    assert "Venetium" not in value, (path, value)
        tweak = root / "Library/MobileSubstrate/DynamicLibraries"
        assert (tweak / "VenetiumUIKitCompat.dylib").is_file()
        binary=(tweak / "VenetiumUIKitCompat.dylib").read_bytes()
        for name in (b"VINewTabPage", b"VIAboutList", b"Chougmium"):
            assert name in binary, name
        assert plistlib.loads((tweak / "VenetiumUIKitCompat.plist").read_bytes())["Filter"] == {
            "Bundles": ["ru.computershik.venetium"]
        }
        assert (root / "Applications/Venetium.app/filters/filters.indexed").is_file()
        assert not (root / "Applications/Chougmium.app").exists(), "do not break upstream internal paths"
    raw=(ROOT/"assets/chougmium-icon.png").read_bytes()
    import struct
    width,height=struct.unpack(">II",raw[16:24])
    assert min(width,height)>=512 and raw[25]==2
    print("PASS: standalone Chromium 150, 24-bit high-definition icon, and unchanged UIKit shim")

if __name__ == "__main__":
    check()

