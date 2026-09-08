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

**v0.1.65-dev is published and verified**, September 8 at 15:38:48 UTC. It
addresses the close-range idle gap with one bounded reposition after a kick,
tracked separately as [#13](https://github.com/Ensrick/doomrocket-private/issues/13).
The kick cooldown, shove force, ammo handling, and 1.8 m launch floor are
unchanged. Empty weapons finish reloading first; blocked routes fail safely.

Workshop item `3794172730` now has content handle `8123257090222204359`, exactly
95,350,820 bytes. Clean compilation, all five material splices, 173 package
tests (including 22 new reposition tests), ragdoll regressions, and source CI
pass. Steam confirms the title, public visibility, unchanged TEST thumbnail,
development warning, requirements, and bug-report links. See the
[current evidence/build record](docs/testing/2026-09-08_TESTER_RESULTS.md),
matching `v0.1.65-dev` tag/prerelease, and [portrait pipeline](docs/WARLOCK_PORTRAIT_PIPELINE.md).

The first upload hit the SDK's Steam API initialization crash: Steam was
elevated while the uploader was not. A normal graceful shutdown and
non-elevated restart resolved it; the retried package matched all validated
hashes. No force-kill, privilege elevation, game reinstall, or binary changes.
Repositioning still awaits visible host/client playtest acceptance.

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
| Close-range shove, rocket exclusion, reload preservation | v0.1.64 host pass; v0.1.65 reposition published for host/client playtest; client/edge-case checks remain |
| Engineer kill-feed portrait | New 60x70 artwork published in TEST v0.1.64; visible acceptance pending |
| Stormvermin-style armor and health | Implemented; difficulty and damage parity still need explicit runtime checks |
| Distance-aware ballistic aim | Implemented offline; runtime aiming verification remains |
| Custom sound bank and voice events | Host playback and death interruption confirmed; remote-client behavior and final audio quality remain |
| Flexible backpack tube, chimney smoke, final animation/rig work | Open development work |

## Exact next playtest

Use `docs/TESTER_QUICKSTART.md` and the #13
reposition matrix in `docs/testing/WARLOCK_COMBAT_TEST_PROTOCOL.md`. Verify
`[doomrocket:LOAD] v0.1.65-dev`, then test open-ground retreats, pursuit,
walls/corners, no route, and target/death/stagger interruptions. Retain the #12
loaded and unfinished reload tests. Confirm aiming resumes with the correct
weapon load. Verify the new portrait's
red/green colors, size, and normal attacker/victim orientation. Capture both host and
remote-client views/logs. Retain the #7/#8 impact matrix and existing
career-switch/death-voice regressions in the multiplayer pass.
