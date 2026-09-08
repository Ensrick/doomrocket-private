# Project status

Snapshot updated 2026-09-08. GitHub Issues is the live work queue; this page is
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

**v0.1.65-dev is in preparation, not published.** It addresses the close-range
idle gap with repositioning after a kick, tracked separately as
[#13](https://github.com/Ensrick/doomrocket-private/issues/13). The user selected
movement, not a shorter kick cooldown or stronger knockback. Do not ask testers
to validate this candidate until publication is explicitly verified.

The current live TEST item remains **v0.1.64-dev**, published September 7 at
17:47:44 UTC (content handle `1532641586336614793`, 95,349,849 bytes). Its clean
build, five material splices, 150 package tests, ragdoll regressions, and
GitHub source validation passed. See the [publication record](docs/testing/2026-09-07_TESTER_RESULTS.md)
and [portrait pipeline](docs/WARLOCK_PORTRAIT_PIPELINE.md).

Crunch's later September 7 capture **does load v0.1.64-dev** and visibly confirms
that completed loads survive kicks without another reload. The host log also
shows an interrupted unfinished reload restarting correctly. This supersedes
the earlier v0.1.63-only report. [Evidence and limits](docs/testing/2026-09-08_TESTER_RESULTS.md):
remote-client and final-second interruption checks remain; no visible portrait
result has been supplied. Public alpha v0.1.55-alpha remains unchanged.

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
| Close-range shove, rocket exclusion, reload preservation | v0.1.64 host pass; client/edge-case checks remain; v0.1.65 reposition candidate in preparation |
| Engineer kill-feed portrait | New 60x70 artwork published in TEST v0.1.64; visible acceptance pending |
| Stormvermin-style armor and health | Implemented; difficulty and damage parity still need explicit runtime checks |
| Distance-aware ballistic aim | Implemented offline; runtime aiming verification remains |
| Custom sound bank and voice events | Host playback and death interruption confirmed; remote-client behavior and final audio quality remain |
| Flexible backpack tube, chimney smoke, final animation/rig work | Open development work |

## Exact next playtest

After verified publication, use `docs/TESTER_QUICKSTART.md` and the #13
reposition matrix in `docs/testing/WARLOCK_COMBAT_TEST_PROTOCOL.md`. Verify
`[doomrocket:LOAD] v0.1.65-dev`, then test open-ground retreats, pursuit,
walls/corners, no route, and target/death/stagger interruptions. Retain the #12
loaded and unfinished reload tests. Confirm aiming resumes with the correct
weapon load. Verify the new portrait's
red/green colors, size, and normal attacker/victim orientation. Capture both host and
remote-client views/logs. Retain the #7/#8 impact matrix and existing
career-switch/death-voice regressions in the multiplayer pass.
