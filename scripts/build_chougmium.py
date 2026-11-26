#!/usr/bin/env python3
"""Repackage verified Venetium for iOS 9 as Chougmium, preserving the Chromium executable.

No Chromium recompilation, resident process, Safari mutation or secret required.
"""
from __future__ import annotations

import argparse
import hashlib
import gzip
import lzma
import os
import plistlib
import re
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_URL = "https://computershik73.github.io/repo/beta/debs/ru.computershik.venetium_150.7871.222.1_iphoneos-arm.deb"
UPSTREAM_SHA256 = "7b7881b5b7f1ad1c8cab77af27fe90e79a7f764b260a1848fa45f89dadc7b310"
UPSTREAM_EXE_SHA256 = "2dacf0c78e0313a098b9f5c8f6a85a9a19f92df23530543599a3d0dc2ff7bca2"
SHIM = ROOT / "releases/com.local.venetium-uikit-compat_0.1.1_iphoneos-arm.deb"
ICON = ROOT / "assets/chougmium-icon.png"
NEW_VERSION = "150.7871.222.1+chougmium5"
RELEASE = ROOT / "docs/debs" / f"ru.computershik.venetium_{NEW_VERSION}_iphoneos-arm.deb"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(*args: str) -> None:
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def get_upstream(target: Path, requested: Path | None) -> None:
    if requested is not None:
        shutil.copyfile(requested, target)
    else:
        with urllib.request.urlopen(UPSTREAM_URL, timeout=60) as response, target.open("wb") as out:
            shutil.copyfileobj(response, out)
    if sha256(target) != UPSTREAM_SHA256:
        raise ValueError("Upstream .deb SHA256 mismatch: refusing to repackage")


def update_control(filename: Path) -> None:
    s = filename.read_text()
    assert re.search(r"(?m)^Package: ru\.computershik\.venetium$", s)
    assert re.search(r"(?m)^Version: 150\.7871\.222\.1$", s)
    for key, value in {
        "Name": "Chougmium",
        "Version": NEW_VERSION,
        "Description": "Standalone Chromium 150 for older jailbroken iPads, with Chougmium icon and iOS 9 keyboard compatibility.",
        "Maintainer": "GodsQuantum (custom packaging)",
        "Author": "Computershik73 (Venetium upstream); GodsQuantum (custom edition)",
        "Depends": "firmware (>= 9.0), firmware (<< 10.0), mobilesubstrate",
    }.items():
        s, count = re.subn(r"(?m)^" + re.escape(key) + r": .*?$", lambda _m: f"{key}: {value}", s)
        if count != 1:
            raise ValueError(f"Unexpected control field {key}: {count} replacements")
    s += "Conflicts: com.local.venetium-uikit-compat\n"
    s += "Replaces: com.local.venetium-uikit-compat\n"
    filename.write_text(s)


def update_icons(app: Path) -> None:
    if not ICON.is_file():
        raise FileNotFoundError(ICON)
    # Never re-introduce the old 128-pixel indexed/paletted artwork:
    # the iPad displays dithered color bands when that icon is enlarged.
    src_info = subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,pix_fmt",
         "-of", "csv=p=0", str(ICON)], text=True,
    ).strip().split(",")
    if len(src_info) != 3:
        raise ValueError("Could not verify high-resolution icon depth")
    width, height, pix_fmt = int(src_info[0]), int(src_info[1]), src_info[2]
    if min(width, height) < 512 or pix_fmt not in ("rgb24", "rgba"):
        raise ValueError(f"Indexed or low-resolution icon refused: {src_info}")
    icons = sorted(app.glob("Icon*.png"))
    if len(icons) < 10:
        raise ValueError("Missing upstream icon resources")
    for icon in icons:
        output = subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0", str(icon)],
            text=True,
        ).strip()
        width, height = [int(v) for v in output.split(",")]
        if not (16 <= width <= 1024 and 16 <= height <= 1024):
            raise ValueError(f"Suspicious upstream icon dimensions: {icon.name}: {output}")
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-i", str(ICON), "-vf", f"scale={width}:{height}:flags=lanczos",
            "-frames:v", "1", str(icon))
    info_path = app / "Info.plist"
    info_data = info_path.read_bytes()
    info = plistlib.loads(info_data)
    if info.get("CFBundleIdentifier") != "ru.computershik.venetium":
        raise ValueError("Unexpected bundle id")
    if info.get("CFBundleExecutable") != "Venetium":
        raise ValueError("Unexpected executable; cannot preserve app data")
    info["CFBundleDisplayName"] = "Chougmium"
    info["CFBundleName"] = "Chougmium"
    info_path.write_bytes(plistlib.dumps(
        info, fmt=plistlib.FMT_BINARY if info_data.startswith(b"bplist") else plistlib.FMT_XML
    ))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-deb", type=Path, help="Verified upstream download cached locally")
    parser.add_argument("--rootful-only", action="store_true", help="Build only the traditional Cydia package; default also builds native IPA")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="chougmium-build-") as tmp:
        t = Path(tmp)
        package = t / "upstream.deb"
        get_upstream(package, args.upstream_deb)
        extracted = t / "staging"
        extracted.mkdir()
        run("dpkg-deb", "-R", str(package), str(extracted))
        app = extracted / "Applications/Venetium.app"
        if sha256(app / "Venetium") != UPSTREAM_EXE_SHA256:
            raise ValueError("Upstream Chromium executable changed: fail closed")
        update_control(extracted / "DEBIAN/control")
        update_icons(app)
        # Keys remain unchanged because the upstream binary uses them.
        # Keep explicit upstream credits and historical project names.
        for path in sorted(app.glob("*.lproj/Localizable.strings")):
            raw = path.read_bytes()
            strings = plistlib.loads(raw)
            for key, value in strings.items():
                if not isinstance(value, str):
                    continue
                if key.startswith(("Venetium for Windows", "Venetium is Chromium 150 for Windows", "Venetium on GitHub")):
                    continue
                strings[key] = value.replace("Venetium", "Chougmium").replace("venetium", "Chougmium")
            path.write_bytes(plistlib.dumps(strings, fmt=plistlib.FMT_BINARY if raw.startswith(b"bplist") else plistlib.FMT_XML))
        shim_dir = t / "shim"
        shim_dir.mkdir()
        run("dpkg-deb", "-x", str(SHIM), str(shim_dir))
        source = shim_dir / "Library/MobileSubstrate/DynamicLibraries"
        dest = extracted / "Library/MobileSubstrate/DynamicLibraries"
        dest.mkdir(parents=True)
        for name in ("VenetiumUIKitCompat.dylib", "VenetiumUIKitCompat.plist"):
            shutil.copy2(source / name, dest / name)
        if sha256(app / "Venetium") != UPSTREAM_EXE_SHA256:
            raise ValueError("Chromium executable unexpectedly modified")
        RELEASE.parent.mkdir(parents=True, exist_ok=True)
        temp_release = t / RELEASE.name
        epoch = 1793571254  # 2026-11-01T22:14:14Z upstream release
        for path in (extracted, *extracted.rglob("*")):
            os.utime(path, (epoch, epoch), follow_symlinks=False)
        os.environ["SOURCE_DATE_EPOCH"] = str(epoch)
        gzip_package = t / "intermediate.deb"
        run("dpkg-deb", "-b", "--root-owner-group", "-Zgzip", "-z6", str(extracted), str(gzip_package))
        # Modern dpkg no longer *creates* LZMA; reassemble the proven upstream
        # data.tar.lzma format so the legacy iPad sees identical compression.
        parts = t / "archive-parts"
        parts.mkdir()
        subprocess.run(["ar", "x", str(gzip_package)], cwd=parts, check=True)
        with gzip.open(parts / "data.tar.gz", "rb") as source, \
                lzma.open(parts / "data.tar.lzma", "wb", format=lzma.FORMAT_ALONE, preset=6) as dest:
            shutil.copyfileobj(source, dest, length=1024 * 1024)
        (parts / "data.tar.gz").unlink()
        for file in (parts / "debian-binary", parts / "control.tar.gz", parts / "data.tar.lzma"):
            os.utime(file, (epoch, epoch))
        subprocess.run(["ar", "rcsD", str(temp_release), "debian-binary", "control.tar.gz", "data.tar.lzma"],
                       cwd=parts, check=True)
        shutil.copyfile(temp_release, RELEASE)
    print("BUILT", RELEASE, RELEASE.stat().st_size, "SHA256", sha256(RELEASE))
    if not args.rootful_only:
        from build_chougmium_native import build as build_native
        build_native(RELEASE, sha256(RELEASE), ROOT / ".cache/ios9-return")


if __name__ == "__main__":
    main()

