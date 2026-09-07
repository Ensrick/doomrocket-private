# Project status

Snapshot updated 2026-09-07. GitHub Issues is the live work queue; this page is
the short re-entry map, not a second backlog.

## One-minute re-entry

| Question | Answer |
| --- | --- |
| Stable player build | [Public alpha v0.1.55-alpha](https://steamcommunity.com/sharedfiles/filedetails/?id=3771657344) |
| Experimental build | [Development TEST](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730) |
| Development reports | [Issue chooser](https://github.com/Ensrick/doomrocket-private/issues/new/choose) |
| Public-alpha reports | [Public issue chooser](https://github.com/Ensrick/doomrocket-public/issues/new/choose) |
| Can both builds be enabled? | No. They share an internal mod identity; use exactly one. |

## Current TEST build

Published **`v0.1.64-dev`** on September 7 at 17:47:44 UTC: the completed-reload fix
for [issue #12](https://github.com/Ensrick/doomrocket-private/issues/12), now
combined with Crunch's new 60x70 kill-feed portrait. Clean compilation, all
five material splices, 150 package tests, ragdoll regressions, and GitHub
source validation pass. The published package is 95,349,849 bytes;
do not reuse the September 5 package hashes. See the [current evidence/build record](docs/testing/2026-09-07_TESTER_RESULTS.md)
and [portrait pipeline](docs/WARLOCK_PORTRAIT_PIPELINE.md).

Crunch's September 7 "still reloading twice" capture loads **v0.1.63-dev** at
line 1160. It confirms the existing old-version defect, not failure of the
then-unpublished fix. The previous Steam API initialization failure was
resolved by a normal Steam restart authorized by the user. No game reinstall,
registry edits, or binary replacements were needed.

The verified upload is `v0.1.64-dev` on Workshop item `3794172730` (content
handle `1532641586336614793`, 95,349,849 bytes). Steam confirms the exact title,
public visibility, TEST thumbnail, development warning, requirements, and
bug-report links. See the matching `v0.1.64-dev` tag/prerelease.

The release is ready for runtime testing, not accepted as an in-game fix yet.
Public alpha v0.1.55-alpha remains unchanged.

Crunch's September 5 reports confirm the v0.1.63 fixes on host: 38 career
changes without the reported crash, 16 active voice interruptions on death,
and 35 consecutive shoves with close-range launches blocked. Read the
[evidence and its limits](docs/testing/2026-09-05_TESTER_RESULTS.md).
Remote-client checks for #9/#10/#11 remain outstanding. #7/#8 still need the
full explosion/removal/stress matrix; incidental crash-free impacts do not
complete that acceptance gate.

## Feature state

| Area | State |
| --- | --- |
| Accepted body, textures, weapon placement, death drop, host ragdoll | Public alpha; do not replace with unverified TEST work |
| Career-switch crash | v0.1.63 host reproduction passes; remote-client verification remains |
| Close-range shove and rocket exclusion | v0.1.63 host repetition passes; v0.1.64 addresses the separate reload restart |
| Engineer kill-feed portrait | New 60x70 artwork published in TEST v0.1.64; visible acceptance pending |
| Stormvermin-style armor and health | Implemented; difficulty and damage parity still need explicit runtime checks |
| Distance-aware ballistic aim | Implemented offline; runtime aiming verification remains |
| Custom sound bank and voice events | Host playback and death interruption confirmed; remote-client behavior and final audio quality remain |
| Flexible backpack tube, chimney smoke, final animation/rig work | Open development work |

## Exact next playtest

Use `docs/TESTER_QUICKSTART.md` and the issue #12 reload matrix in
`docs/testing/WARLOCK_COMBAT_TEST_PROTOCOL.md`. Verify the published build's
`[doomrocket:LOAD] v0.1.64-dev` marker, then test a shove after a completed reload, during an
unfinished reload, and before the first shot. Step out of shove range and
confirm aiming resumes with the correct weapon load. Verify the new portrait's
red/green colors, size, and normal attacker/victim orientation. Capture both host and
remote-client views/logs. Retain the #7/#8 impact matrix and existing
career-switch/death-voice regressions in the multiplayer pass.
