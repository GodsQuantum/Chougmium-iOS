#!/usr/bin/env python3
"""Build a scoped iOS9 rootful MobileSubstrate tab interaction repair.

This is an optional INTERIM Venetium UI repair, not the chosen next browser engine.
"""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
PKG = "com.local.chougmium-tabsfix"
VERSION = "0.1.0"
TARGET = ROOT/"releases"/f"{PKG}_{VERSION}_iphoneos-arm.deb"

CONTROL = f"""Package: {PKG}
Name: Chougmium Tab Controls Repair
Version: {VERSION}
Architecture: iphoneos-arm
Depends: firmware (>= 9.0), firmware (<< 10.0), mobilesubstrate, ru.computershik.venetium (>= 150.7871.222.1)
Conflicts: 
Maintainer: GodsQuantum (private iPad 2 fork)
Section: Tweaks
Priority: optional
Description: Fix close-tab touches and add native Close tab menu action, without touching web engine.
"""

def sha256(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()

def build(theos: Path, *, package: str=PKG, version: str=VERSION,
          dylib_name: str="ChougmiumTabsFix",
          source: str="src/chougmium_tabfix.m",
          bundle: str="ru.computershik.venetium",
          control: str=CONTROL) -> None:
    target=ROOT/"releases"/f"{package}_{version}_iphoneos-arm.deb"
    tc=theos/"toolchain/linux/iphone/bin"
    sdk=theos/"sdks/iPhoneOS10.3.sdk"
    clang=tc/"clang"
    signer=tc/"ldid"
    assert clang.is_file() and signer.is_file() and sdk.is_dir(), "Theos ARMv7 toolchain/SDK missing"
    with TemporaryDirectory(prefix="chougmium-tabfix-build-") as tmp:
        stage=Path(tmp)/"stage"
        tweak=stage/"Library/MobileSubstrate/DynamicLibraries"
        debian=stage/"DEBIAN"
        tweak.mkdir(parents=True)
        debian.mkdir()
        dylib=tweak/f"{dylib_name}.dylib"
        command=[
            str(clang),"-target","armv7-apple-ios9.0","-isysroot",str(sdk),
            "-fobjc-arc","-fblocks","-dynamiclib","-O2",
            "-Wall","-Wextra","-Werror","-fvisibility=hidden",
            "-Wl,-segalign,4000",
            f"-Wl,-install_name,/Library/MobileSubstrate/DynamicLibraries/{dylib_name}.dylib",
            "-Wl,-no_uuid",
            "-framework","Foundation",
            "-framework","UIKit","-lobjc",
            "-o",str(dylib),str(ROOT/source)
        ]
        subprocess.run(command,check=True)
        subprocess.run([str(signer),"-S",str(dylib)],check=True)
        (tweak/f"{dylib_name}.plist").write_text(
            f'{{ Filter = {{ Bundles = ( "{bundle}" ); }}; }}\n')
        (debian/"control").write_text(control.replace("Conflicts: \n",""))
        for dirpath in (stage, stage/"Library", stage/"Library/MobileSubstrate", tweak, debian):
            dirpath.chmod(0o755)
        for file in (tweak/f"{dylib_name}.plist",debian/"control"):
            file.chmod(0o644)
        dylib.chmod(0o755)
        epoch=1795435200
        for entry in (stage,*stage.rglob("*")):
            os.utime(entry,(epoch,epoch),follow_symlinks=False)
        env={**os.environ,"SOURCE_DATE_EPOCH":str(epoch)}
        subprocess.run(["dpkg-deb","-Zgzip","--build","--root-owner-group",str(stage),str(target)],
                       check=True,env=env,capture_output=True,text=True)
    print("BUILT",target.name,"size",target.stat().st_size,"SHA256",sha256(target))
    print("NO_ENGINE_REBUILD NO_DAEMON FILTERED_TO="+bundle)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--theos",type=Path,default=Path.home()/".local/share/theos")
    build(parser.parse_args().theos)
