#!/usr/bin/env python3
"""Static validation of the small rootful iOS9 tab-fix package.

This doesn't claim UI touch regression success before testing on real iPad.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/"releases/com.local.chougmium-tabsfix_0.1.0_iphoneos-arm.deb"
assert PACKAGE.is_file()
def field(k:str)->str:
    return subprocess.check_output(["dpkg-deb","-f",str(PACKAGE),k],text=True).strip()
assert field("Package")=="com.local.chougmium-tabsfix"
assert field("Version")=="0.1.0"
assert field("Architecture")=="iphoneos-arm"
assert "mobilesubstrate" in field("Depends")
assert "ru.computershik.venetium" in field("Depends")
with tempfile.TemporaryDirectory(prefix="chougmium-tabsfix-verify-") as path:
    subprocess.run(["dpkg-deb","-x",str(PACKAGE),path],check=True)
    base=Path(path)/"Library/MobileSubstrate/DynamicLibraries"
    files=sorted(x.name for x in base.iterdir())
    assert files==["ChougmiumTabsFix.dylib","ChougmiumTabsFix.plist"], files
    dylib=(base/"ChougmiumTabsFix.dylib").read_bytes()
    plist=(base/"ChougmiumTabsFix.plist").read_text()
    assert dylib[:8]==bytes.fromhex("cefaedfe0c000000"),"not ARMv7 Mach-O"
    assert 'Bundles = ( "ru.computershik.venetium" );' in plist
    assert "Yozora" not in plist and "SpringBoard" not in plist
    for symbol in (b"VITabGrid",b"VIMenu",b"Fermer l'onglet",b"Close tab",b"chougmium.close-current-tab"):
        assert symbol in dylib, symbol
    assert len(dylib)>1000
src=(ROOT/"src/chougmium_tabfix.m").read_text()
assert "gesture.cancelsTouchesInView = NO;" in src
assert "shouldReceiveTouch" in src
assert "UIControlEventTouchUpInside" in src
assert "method_setImplementation" in src
assert "closeTab:" in src
for forbidden in ("WebKit.framework","UIWebView","WKWebView","unlink(","removeItemAtPath","reboot","launchctl"):
    assert forbidden not in src
print("PASS: scoped ARMv7 iOS9 MobileSubstrate tweak, safe package, both close-tab actions")
print("sha256="+hashlib.sha256(PACKAGE.read_bytes()).hexdigest())
