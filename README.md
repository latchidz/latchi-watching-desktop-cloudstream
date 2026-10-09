# LATCHI WATCHING — native CloudStream desktop

An independent **Windows x64 Qt 6 / libmpv application with a separate JVM provider
host**, not a website launcher and not the former Compose `Hello, World!` MSI.

## الصفحة الرئيسية

تفتح مباشرة على المصادر: قصة عشق ١، قصة عشق ٢، قرمزي، ماي سيما، توب سينما،
توك توك سيما، تونيفليكس، وي سيما. بطاقات عربية/إنجليزية بنسبة 3:1 وشعارات
المصادر الأصلية، تخطيط RTL متجاوب وتنقّل بلوحة المفاتيح. تثبيت الإضافات يحتاج
موافقة صريحة، والتحقق من البصمة والتحويل والتسجيل قبل فتح الكتالوغ.

Existing native features are retained: repositories and `.cs3` conversion,
provider catalog/search/details/episodes, embedded libmpv playback, local history
and collections, downloads, preferences and consent-gated verified updates.
Provider sites remain external dependencies; compatibility and playback must be
tested rather than inferred from a successful package build.

## Build and public releases

- Source branch: [`latchi-native-windows`](https://github.com/latchidz/latchi-watching-desktop-cloudstream/tree/latchi-native-windows).
- Windows workflow: `.github/workflows/windows-release.yml` (MSVC 2022, Qt 6.8.3, Java 17).
- The workflow requires packaging tests, native suites, real `.cs3` conversion and
  registration, at least one real provider catalog/details round trip, a generated
  lawful-video player test, fresh extraction and installer/uninstaller smoke tests.
- Publication is a separate job. It uses a repository secret only in the publish
  step, never in the build or plugin execution environment.
- Public distribution: [`latchidz/LATCHI-RELEASES`](https://github.com/latchidz/LATCHI-RELEASES),
  channel `watching-cloudstream-v<version>`.
- Releases include Setup, portable ZIP, exact application source, third-party
  corresponding source/support, checksum, notices and actual verification results.
- [دليل التثبيت العربي](docs/INSTALL-AR.md).

The Windows installer is unsigned. Do not disable Windows protections. A hosted
software-rendered build does not certify physical GPU/audio/controllers or an
upgrade from Electron 0.1.2. Live provider playback is not inferred from catalog
or registration tests. Read each release's results and limitations.

## Local source validation (Linux, not Windows certification)

```bash
python3 -m unittest discover -s packaging -p 'test_*.py'
python3 scripts/verify_arabic_source_packages.py
mkdir -p linux-native/build/app
cd linux-native/build/app
qmake6 ../../cloudstream-linux.pro CONFIG+=release
make -j2
```

Qt 6, libmpv and SDL2 development packages are required. Building the provider host
requires Java 17 and `./gradlew :provider-host:test :provider-host:installDist`.
`tools/render_latchi_source_cards.py` recreates card art and the launcher icon
using Pillow/RAQM/DejaVu Sans and records third-party mark provenance.

## Source and license

GPL version 3. Original copyrights, vector attribution, dependency licenses and
legal files are retained. This branch is reconstructed from the public native
base because the prior uncommitted handoff ZIP was unavailable; it is not a claim
to have recovered that exact worktree. Existing LATCHI branches and releases are
preserved. See [SOURCES.md](SOURCES.md), [LICENSE](LICENSE), and the retained
`packaging/windows-licenses/` audit for upstream provenance and redistribution.
