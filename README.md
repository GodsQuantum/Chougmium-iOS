# Chougmium

<img src="assets/chougmium-icon.png" width="112" alt="Chougmium app icon">

**A standalone Chromium 150 browser for jailbroken iPad 2 / iOS 9.**  
An independent packaging and compatibility edition of [Venetium for iOS](https://github.com/Computershik73/Venetium-iOS), not Google Chrome.

[Install from your iPad](https://godsquantum.github.io/Chougmium-iOS/) · [Releases](https://github.com/GodsQuantum/Chougmium-iOS/releases) · [Source and credits](#source-and-license)

## Current release

Version 150.7871.222.1+chougmium5 restores the original globe artwork exactly. The recommended native IPA installs in the iOS user-app container on the data partition, with the original Chromium executable and all 17 icons verified on iPad 2.

## Features

- Chromium/Blink and V8 run on the device, not on a remote browser server.
- Original Venetium browser engine, bookmarks, multiple tabs and built-in filter list.
- Rootful browser package preserves the upstream app identity, executable and profile path.
- Scoped iOS 9 keyboard compatibility fix for the missing UIWindow coordinateSpace selector.
- Chougmium icon, new-tab and About branding.
- Optional tab-controls repair: native Close tab menu and corrected close-button touch handling.

## Install on the iPad

**Recommended: native IPA (data partition).** Requires jailbroken iOS 9, AppSync Unified and a trusted IPA installer. On an existing native installation, upgrade with the same bundle identifier; do not uninstall or clear its profile.

- [Native Chougmium IPA](https://github.com/GodsQuantum/Chougmium-iOS/releases/download/v150.7871.222.1-chougmium5/Chougmium_150.7871.222.1%2Bchougmium5_iphoneos-arm.ipa)
- [Native compatibility package (.deb)](https://github.com/GodsQuantum/Chougmium-iOS/releases/download/v150.7871.222.1-chougmium5/com.local.chougmium-native-compat_0.1.0_iphoneos-arm.deb): scoped keyboard and tab repairs, requires MobileSubstrate; contains no browser bundle.

Do not combine the native IPA with the rootful browser DEB or the old separate tab repair. If migrating from that edition, preserve the existing profile, remove both rootful packages, install the IPA using appinst, install its compatibility package, then restore the profile to the appropriate native data container. The sandbox may limit hardware video decoding.

**Alternative: legacy rootful Cydia installation.** This uses the system partition and is not recommended on storage-constrained devices. Add the [Cydia source](https://godsquantum.github.io/Chougmium-iOS/) only if you deliberately choose this mode. [Rootful browser DEB](https://github.com/GodsQuantum/Chougmium-iOS/releases/download/v150.7871.222.1-chougmium5/ru.computershik.venetium_150.7871.222.1%2Bchougmium5_iphoneos-arm.deb) · [Rootful tab repair](https://github.com/GodsQuantum/Chougmium-iOS/releases/download/v150.7871.222.1-chougmium5/com.local.chougmium-tabsfix_0.1.0_iphoneos-arm.deb).

**iOS 9 HTTPS caveat:** a real native HTTPS request on iPad 2 returned NSURLErrorDomain -1202 against GitHub Pages. iOS 9 predates built-in ISRG Root X1 trust. See [official certificate compatibility](https://letsencrypt.org/docs/certificate-compatibility/). If needed, obtain verified release packages on a modern computer and transfer them to the iPad with your usual trusted installer. Direct Cydia installation from the public URL is not certified. Do not disable certificate validation.

## Compatibility and known limitations

iOS 9.x, ARMv7, jailbreak. Native IPA installation, original engine hash, 17 icon resources and launch verified on iPad 2 / iOS 9.3.5. The original Chromium executable is unchanged. The keyboard repair is narrowly scoped; not every modern site or media format is supported. With the iPad 2's 512 MB RAM, complex web apps and many tabs can be slow or terminate under memory pressure. Do not use an old jailbroken device as a security-sensitive daily browser. No promise of current Chrome security updates, extensions or Google account sync.

The native compatibility companion contains the existing scoped keyboard and tab repairs. The rootful alternative uses its own separate tab-repair package. Do not modify the system partition or globally weaken TLS.

## Screenshots

The icon above is the shipped app artwork, not a screenshot. Genuine screenshots of this release will be added after capture on the device; no simulated interface is represented as real.

## Build and verify

Build the scoped UIKit shim with Theos (ARMv7 toolchain and iPhoneOS10.3 SDK), then repackage the exact verified upstream .deb. The repackager requires Python 3, dpkg-deb, ar and FFmpeg; it refuses a mismatching upstream SHA-256. The corresponding source of the original engine is described below.

```sh
export THEOS="$HOME/.local/share/theos"
./scripts/build.sh
python3 scripts/build_chougmium.py
python3 scripts/build_chougmium_tabfix.py --theos "$THEOS"
cp releases/com.local.chougmium-tabsfix_0.1.0_iphoneos-arm.deb docs/debs/
python3 scripts/build_feed.py
python3 tests/test_chougmium_package.py
python3 tests/test_chougmium_tabfix.py
python3 tests/test_feed.py
```

## Source and license

This distribution preserves the original Venetium Chromium binary. Original app and engine integration by the Venetium-iOS authors and Computershik73. The upstream corresponding source is the [version 150.7871.222.1 commit 20d7340](https://github.com/Computershik73/Venetium-iOS/tree/20d7340140aaeb59b00e392f6bca6dd6568b4c9a), including its Chromium patches and build scripts that fetch the pinned engine source. [Download the upstream source snapshot](https://github.com/Computershik73/Venetium-iOS/archive/20d7340140aaeb59b00e392f6bca6dd6568b4c9a.tar.gz). Follow the upstream build instructions and notices for Chromium and its third-party components. The local compatibility changes, packaging scripts and build instructions are available here under GPL-3.0. The original third-party filter license is retained in the application.

[Local patch source archive](https://godsquantum.github.io/Chougmium-iOS/source/Chougmium-patches.tar.gz) · [GPL-3.0](LICENSE)

Chougmium is a community project, not affiliated with Google or Apple.
