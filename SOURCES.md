# Source, attribution and redistribution notices — LATCHI WATCHING

LATCHI WATCHING is an independent native desktop adaptation. It is not an official
recloudstream desktop release, and it does not claim to reproduce all Android features.

## Application source (GPL-3.0)

- LATCHI fork: https://github.com/latchidz/latchi-watching-desktop-cloudstream
- Native development branch: `latchi-native-windows`.
- Native base: https://github.com/dcenhance/cloudstream-pc at
  `e1e91aea4d7d1b55a9756c06c94eb8272ae8d324`.
- Original application and retained provider API: https://github.com/recloudstream/cloudstream.
- Original player vectors and notices remain under `linux-native/player/upstream/`.
- LATCHI changes: Arabic source hub, source cards and launcher artwork, Windows
  product/profile identity, channel-isolated update policy, package/runtime probes,
  automated verification, installer and public release integration.
- See `LICENSE` for GNU GPL version 3. Source ZIPs accompanying each LATCHI release
  contain the exact first-party code and build scripts used to produce it.

The earlier handoff's uncommitted local archive was not available. This branch
reconstructs the native path from the attributed public base; it does not pretend
to recover the exact missing worktree. Existing LATCHI branches/releases are preserved.

## Third-party binary runtime and corresponding source

The release builder reuses only SHA-256-pinned, audited third-party runtime bytes
from CloudStream PC `v0.1.0-preview.3`. Its old application EXE is deleted before
building LATCHI. The first-party provider-host JAR is rebuilt and replaced; all
other library bytes are checked against the retained audited inventory.

- Runtime ZIP SHA-256:
  `116b5847c93ea7fc9ba31f2c2882bf26f958fecb5f4e2ed47d1310a3f985de28`.
- Qt 6.8.3, libmpv, FFmpeg, SDL2, Mesa/Vulkan, Microsoft runtime and Temurin Java
  carry their original notices in the shipped `licenses/` and Java `legal/` trees.
- Dependency source/support archives are mirrored, byte-for-byte with checksums,
  into the same public LATCHI release as the binary. Their upstream provenance is
  the immutable release https://github.com/dcenhance/cloudstream-pc/releases/tag/v0.1.0-preview.3.
- `packaging/windows-licenses/` retains audits, dependency licenses, source-support
  inventories and build/provenance information.
- Shared LGPL libraries remain replaceable. Their licenses permit debugging of
  user modifications; no additional anti-replacement restriction is imposed.

## Source-card marks and extension metadata

Provider IDs and official metadata are taken from the public third-party manifest:
https://raw.githubusercontent.com/Abodabodd/re-3arabi/refs/heads/builds/plugins.json

`linux-native/assets/latchi-sources/sources.json` records the origin, availability,
original size and fetched SHA-256 of each displayed provider mark. Marks and names
identify the respective providers; they remain their owners' trademarks/artwork,
not original LATCHI logos or an endorsement. `tools/render_latchi_source_cards.py`
recreates the LATCHI-owned backgrounds, typography, layout and launcher icon.

No `.cs3` plugin binary is bundled in the installed application. Installing one
requires explicit user consent, a trusted repository and hash validation. Plugins
execute third-party code in a separate JVM process, not in a security sandbox.
Provider sites, licenses, catalog availability, legal viewing rights and ongoing
compatibility remain third-party responsibilities.

## Verification limitations

Hosted Windows software rendering and a null audio sink are not proof of physical
GPU/audio/controller support. A generated lawful local video tests the player;
live provider playback and an upgrade from the separate Electron 0.1.2 product
must not be claimed unless separately verified. See `WINDOWS-VERIFICATION.json`
and release notes for actual results, including provider catalog/network failures.

The Windows installer is unsigned. Never disable system protections to install it.
