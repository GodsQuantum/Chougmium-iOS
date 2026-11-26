#!/usr/bin/env python3
"""Build a flat Cydia feed from the two pinned release artifacts."""
from pathlib import Path
import bz2,gzip,hashlib,io,subprocess,tarfile
from email.utils import formatdate
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"docs"
expected={"ru.computershik.venetium":"150.7871.222.1+chougmium4","com.local.chougmium-tabsfix":"0.1.0"}
def digest(data,alg):return hashlib.new(alg,data).hexdigest()
entries=[];seen=set()
for p in sorted((D/"debs").glob("*.deb")):
    field=lambda k:subprocess.check_output(["dpkg-deb","-f",str(p),k],text=True).strip()
    pkg=field("Package")
    assert pkg in expected and pkg not in seen and field("Version")==expected[pkg]
    assert field("Architecture")=="iphoneos-arm";seen.add(pkg)
    b=p.read_bytes()
    ctl=subprocess.check_output(["dpkg-deb","-f",str(p)],text=True).rstrip()
    entries.append(ctl+"\n"+f"Filename: debs/{p.name}\nSize: {len(b)}\nMD5sum: {digest(b,'md5')}\nSHA1: {digest(b,'sha1')}\nSHA256: {digest(b,'sha256')}\nIcon: icons/Chougmium.png\n\n")
assert seen==set(expected)
content="".join(entries).encode()
files={"Packages":content,"Packages.gz":gzip.compress(content,mtime=0),"Packages.bz2":bz2.compress(content)}
for name,b in files.items():(D/name).write_bytes(b)
release=["Origin: Chougmium","Label: Chougmium","Suite: stable","Codename: stable","Architectures: iphoneos-arm","Components: main","Description: Local Chromium for jailbroken iOS 9",f"Date: {formatdate(usegmt=True)}"]
for alg,label in [("md5","MD5Sum"),("sha256","SHA256")]:
    release.append(label+":")
    for name,b in files.items():release.append(f" {digest(b,alg)} {len(b)} {name}")
(D/"Release").write_text("\n".join(release)+"\n")
sources=["LICENSE","README.md","Makefile","control","VenetiumUIKitCompat.plist","assets/chougmium-icon.png","docs/index.html"]
sources+=sorted(str(p.relative_to(ROOT)) for folder in ("src","scripts","tests") for p in (ROOT/folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
with (D/"source/Chougmium-patches.tar.gz").open("wb") as raw, gzip.GzipFile(fileobj=raw,mode="wb",mtime=0) as gz,tarfile.open(fileobj=gz,mode="w") as tar:
    for name in sources:
        p=ROOT/name;info=tar.gettarinfo(str(p),arcname="Chougmium/"+name)
        info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=""
        with p.open("rb") as f:tar.addfile(info,f)
print("PASS: two packages indexed and public patch source archived")
