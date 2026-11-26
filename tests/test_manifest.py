from pathlib import Path
import plistlib

root = Path(__file__).resolve().parents[1]
manifest = plistlib.loads((root / "VenetiumUIKitCompat.plist").read_bytes())
assert manifest["Filter"] == {"Bundles": ["ru.computershik.venetium"]}
control = (root / "control").read_text()
assert "Architecture: iphoneos-arm" in control
assert "firmware (>= 9.0)" in control
assert "firmware (<< 10.0)" in control
assert "mobilesubstrate" in control
assert "ru.computershik.venetium" in control
print("PASS: Cydia package restricted to Venetium on iOS 9")

