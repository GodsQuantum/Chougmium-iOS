#!/usr/bin/env python3
"""Validate the exact signed Cydia artifact without deploying to a device."""
from pathlib import Path
import plistlib
import struct
import subprocess
from tempfile import TemporaryDirectory

root = Path(__file__).resolve().parents[1]
pkg = root / "releases" / "com.local.venetium-uikit-compat_0.1.1_iphoneos-arm.deb"
assert pkg.is_file(), "signed release package missing"

def field(name: str) -> str:
    return subprocess.check_output(["dpkg-deb", "-f", str(pkg), name], text=True).strip()

assert field("Architecture") == "iphoneos-arm"
assert field("Package") == "com.local.venetium-uikit-compat"
assert "ru.computershik.venetium" in field("Depends")

with TemporaryDirectory(prefix="venetium-compat-verify-") as td:
    subprocess.run(["dpkg-deb", "-x", str(pkg), td], check=True)
    root_dir = Path(td)
    files = sorted(str(p.relative_to(root_dir)) for p in root_dir.rglob("*") if p.is_file())
    base = "Library/MobileSubstrate/DynamicLibraries"
    assert files == [f"{base}/VenetiumUIKitCompat.dylib", f"{base}/VenetiumUIKitCompat.plist"], files
    manifest = plistlib.loads((root_dir / f"{base}/VenetiumUIKitCompat.plist").read_bytes())
    assert manifest["Filter"] == {"Bundles": ["ru.computershik.venetium"]}
    binary = (root_dir / f"{base}/VenetiumUIKitCompat.dylib").read_bytes()
    magic, cputype, _, _, ncmds, _, _ = struct.unpack_from("<7I", binary)
    assert magic == 0xFEEDFACE and cputype == 12, "must be ARMv7 Mach-O"
    off, has_signature, min_ios9 = 28, False, False
    for _ in range(ncmds):
        cmd, size = struct.unpack_from("<2I", binary, off)
        if cmd == 0x1D:
            has_signature = True
        if cmd == 0x25:
            ver = struct.unpack_from("<I", binary, off + 8)[0]
            min_ios9 = (ver >> 16, (ver >> 8) & 255) == (9, 0)
        off += size
    assert has_signature and min_ios9, "signed iOS 9 binary required"

print("PASS: signed ARMv7 iOS 9 tweak; only Venetium library/filter; expected dependencies")

