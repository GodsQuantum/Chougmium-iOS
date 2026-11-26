from pathlib import Path
import bz2,gzip,hashlib,tarfile,subprocess
D=Path(__file__).resolve().parents[1]/"docs"
p=(D/"Packages").read_bytes()
assert bz2.decompress((D/"Packages.bz2").read_bytes())==gzip.decompress((D/"Packages.gz").read_bytes())==p
entries=[dict(line.split(": ",1) for line in e.splitlines() if ": " in line and not line.startswith(" ")) for e in p.decode().strip().split("\n\n")]
assert {e["Package"] for e in entries}=={"ru.computershik.venetium","com.local.chougmium-tabsfix"}
for e in entries:
    path=D/e["Filename"];b=path.read_bytes()
    assert len(b)==int(e["Size"]) and hashlib.sha256(b).hexdigest()==e["SHA256"]
    assert hashlib.sha1(b).hexdigest()==e["SHA1"] and hashlib.md5(b).hexdigest()==e["MD5sum"]
    assert subprocess.check_output(["dpkg-deb","-f",str(path),"Package"],text=True).strip()==e["Package"]
r=(D/"Release").read_text()
for name in ("Packages","Packages.gz","Packages.bz2"):
    b=(D/name).read_bytes()
    assert f" {hashlib.sha256(b).hexdigest()} {len(b)} {name}" in r
assert (D/".nojekyll").exists()
with tarfile.open(D/"source/Chougmium-patches.tar.gz") as z:
    names=z.getnames()
    assert "Chougmium/src/chougmium_tabfix.m" in names
    assert "Chougmium/src/branding.m" in names
    assert not any(x.endswith(("HANDOFF_CURRENT.md","AGENTS.md","CLAUDE.md",".env")) for x in names)
print("PASS: two-package index, compression, checksums, source archive")
