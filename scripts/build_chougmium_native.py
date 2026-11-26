#!/usr/bin/env python3
"""Build native iOS user IPA + scoped optional Substrate compatibility package.

Reuses the exact branded, signed app from a verified rootful release. No
system-directory relocation, new signing, launcher daemon or fake package.
The IPA preserves upstream bundle identity but is subject to the iOS sandbox.
"""
from __future__ import annotations

import argparse
import hashlib
import plistlib
import re
import shutil
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXE_SHA = "2dacf0c78e0313a098b9f5c8f6a85a9a19f92df23530543599a3d0dc2ff7bca2"
DEFAULT_DEB = ROOT / "docs/debs/ru.computershik.venetium_150.7871.222.1+chougmium5_iphoneos-arm.deb"
DEFAULT_SHA = "54bc56d68c593cc24ded3a64f9898bb5fdff246fd7be4a5cf9fd3f49bb0b8ef3"
TABFIX = ROOT / "releases/com.local.chougmium-tabsfix_0.1.0_iphoneos-arm.deb"
TABFIX_SHA = "e1c67678b973237859209ac0fa31a560d6378cd737330bb2a90070d5a8e1517c"
BID = "ru.computershik.venetium"
COMPAT = "com.local.chougmium-native-compat"
TWEAKS = Path("Library/MobileSubstrate/DynamicLibraries")

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def field(deb, key):
    return subprocess.check_output(["dpkg-deb", "-f", str(deb), key], text=True).strip()

def extract(deb, target):
    target.mkdir()
    subprocess.run(["dpkg-deb", "-x", str(deb), str(target)], check=True)

def build(deb, expected, out):
    assert sha(deb) == expected, "Browser archive mismatch"
    assert sha(TABFIX) == TABFIX_SHA, "Tab repair archive mismatch"
    assert field(deb,"Package") == BID
    version = field(deb,"Version")
    assert version.startswith("150.7871.222.1+chougmium"), version
    out.mkdir(parents=True, exist_ok=True)
    ipa = out / f"Chougmium_{version}_iphoneos-arm.ipa"
    compat = out / f"{COMPAT}_0.1.0_iphoneos-arm.deb"
    with tempfile.TemporaryDirectory(prefix="chougmium-native-") as tmp:
        t = Path(tmp)
        extract(deb,t/"browser")
        extract(TABFIX,t/"tabfix")
        app = t/"browser/Applications/Venetium.app"
        info = plistlib.loads((app/"Info.plist").read_bytes())
        assert info["CFBundleIdentifier"] == BID
        assert info["CFBundleExecutable"] == "Venetium"
        assert info["CFBundleDisplayName"] == "Chougmium"
        assert sha(app/"Venetium") == EXE_SHA
        assert all(not p.is_symlink() for p in app.rglob("*"))
        assert (app/"Venetium").stat().st_mode & 0o111
        # Keep the executable/signature and every app resource byte-identical.
        tempipa=t/ipa.name
        with zipfile.ZipFile(tempipa,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in sorted(app.rglob("*")):
                if not p.is_file():
                    continue
                item=zipfile.ZipInfo("Payload/"+app.name+"/"+p.relative_to(app).as_posix(),(2026,11,1,22,14,14))
                item.create_system=3
                item.external_attr=(stat.S_IFREG | stat.S_IMODE(p.stat().st_mode))<<16
                z.writestr(item,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
        with zipfile.ZipFile(tempipa) as z:
            assert z.testzip() is None
            assert all(n.startswith("Payload/Venetium.app/") for n in z.namelist())
            for p in app.rglob("*"):
                if p.is_file():
                    n="Payload/"+app.name+"/"+p.relative_to(app).as_posix()
                    assert hashlib.sha256(z.read(n)).hexdigest()==sha(p),n
        d=t/"compat"
        (d/TWEAKS).mkdir(parents=True)
        (d/"DEBIAN").mkdir()
        # A true IPA cannot satisfy a dpkg dependency; keep only real system
        # dependencies. No app payload in this small compatibility package.
        (d/"DEBIAN/control").write_text("""Package: com.local.chougmium-native-compat
Name: Chougmium Native Compatibility
Version: 0.1.0
Architecture: iphoneos-arm
Maintainer: GodsQuantum
Section: Tweaks
Depends: firmware (>= 9.0), firmware (<< 10.0), mobilesubstrate
Conflicts: ru.computershik.venetium, com.local.venetium-uikit-compat, com.local.chougmium-tabsfix
Description: Scoped keyboard, branding and tab-control repairs for the native Chougmium IPA on jailbroken iOS 9. No browser bundle.
""")
        for source,stem in [(t/"browser","VenetiumUIKitCompat"),(t/"tabfix","ChougmiumTabsFix")]:
            for ext in (".dylib",".plist"):
                p=source/TWEAKS/(stem+ext)
                assert p.is_file()
                if ext==".plist":
                    raw=p.read_bytes()
                    try:
                        assert plistlib.loads(raw)["Filter"]=={"Bundles":[BID]}
                    except plistlib.InvalidFileException:
                        # MobileSubstrate also accepts the legacy OpenStep plist.
                        assert re.fullmatch(r'\{\s*Filter\s*=\s*\{\s*Bundles\s*=\s*\(\s*"ru\.computershik\.venetium"\s*\)\s*;\s*\}\s*;\s*\}\s*',raw.decode()),p
                shutil.copy2(p,d/TWEAKS/p.name)
                assert sha(p)==sha(d/TWEAKS/p.name)
        tempdeb=t/compat.name
        subprocess.run(["dpkg-deb","-b","--root-owner-group","-Zgzip",str(d),str(tempdeb)],check=True,stdout=subprocess.DEVNULL)
        extract(tempdeb,t/"check")
        assert not (t/"check/Applications").exists()
        for p in (d/TWEAKS).iterdir():
            assert sha(p)==sha(t/"check"/TWEAKS/p.name)
        shutil.copy2(tempipa,ipa)
        if compat.exists():
            old=t/"existing-compat"
            extract(compat,old)
            assert subprocess.check_output(["dpkg-deb","-f",str(compat)])==subprocess.check_output(["dpkg-deb","-f",str(tempdeb)]),"Compatibility metadata changed; bump its version"
            old_files={p.relative_to(old):sha(p) for p in old.rglob("*") if p.is_file()}
            new_files={p.relative_to(t/"check"):sha(p) for p in (t/"check").rglob("*") if p.is_file()}
            assert old_files==new_files,"Compatibility payload changed; bump its version"
        else:
            shutil.copy2(tempdeb,compat)
    for p in (ipa,compat):
        print("VERIFIED",p,p.stat().st_size,sha(p),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--deb",type=Path,default=DEFAULT_DEB)
    p.add_argument("--sha256",default=DEFAULT_SHA)
    p.add_argument("--output-dir",type=Path,default=ROOT/".cache/ios9-return")
    a=p.parse_args()
    build(a.deb,a.sha256,a.output_dir)
