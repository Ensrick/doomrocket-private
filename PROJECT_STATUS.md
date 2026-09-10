# Project status

Snapshot updated 2026-09-10. GitHub Issues is the live work queue; this page is
the short re-entry map, not a second backlog.

## One-minute re-entry

| Question | Answer |
| --- | --- |
| Stable player build | [Public alpha v0.1.56-alpha](https://steamcommunity.com/sharedfiles/filedetails/?id=3771657344) |
| Published experimental build | [Development TEST v0.1.65-dev](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730), known relocation crash; testing paused |
| Unpublished source candidate | v0.1.66-dev: measured chimney smoke prototype, no hose physics |
| Development reports | [Issue chooser](https://github.com/Ensrick/doomrocket-private/issues/new/choose) |
| Public-alpha reports | [Public issue chooser](https://github.com/Ensrick/doomrocket-public/issues/new/choose) |
| Can both builds be enabled? | No. They share an internal mod identity; use exactly one. |

## Publication hold and current work

**TEST v0.1.65-dev is published, but not accepted as stable.** Crunch reported
a relocation crash, tracked in [#14](https://github.com/Ensrick/doomrocket-private/issues/14).
The action-network lookup needs correction and regression testing before a
replacement TEST upload. Successful compilation and the earlier mocked tests
did not establish runtime/network safety. Do not send testers back to the
v0.1.65 reposition matrix as though that crash were resolved.

The source candidate **v0.1.66-dev is not on Workshop**. It adds a native
Warpfire backpack smoke emitter at a measured chimney rim, with ownership and
teardown guards. It does not fix #14, change the model/rig, or implement hose
physics. Its coordinates and lifecycle are checked offline; visible placement,
scale, host/client behavior, and runtime safety still require an in-game pass.
See [hose/smoke research and acceptance](docs/research/BACKPACK_HOSE_AND_SMOKE.md).

The public Workshop item was separately updated to **v0.1.56-alpha** with the
Engineer kill-feed portrait and narrow target guards, retaining its accepted
baseline. [Public release record](https://github.com/Ensrick/doomrocket-public/releases/tag/v0.1.56-alpha).
No development audio, combat, reposition, or smoke experiment was implicitly
promoted. This hose/smoke work does not upload or alter either Workshop item.

## Feature state

| Area | State |
| --- | --- |
| Accepted body, textures, weapon placement, death drop, host ragdoll | Public alpha; preserve this baseline |
| Engineer kill-feed portrait | Published in public v0.1.56-alpha and TEST; visible acceptance still needed |
| Career-switch crash | v0.1.63 host reproduction passes; remote-client verification remains |
| Close-range shove, rocket exclusion, reload preservation | v0.1.64 host pass; client/edge-case checks remain |
| Reposition after kick | v0.1.65 published with reported crash #14; not ready for further playtesting |
| Stormvermin-style armor and health | Implemented in development; difficulty/damage parity needs explicit runtime checks |
| Distance-aware ballistic aim | Implemented offline in development; runtime aiming verification remains |
| Custom sound bank and voice events | Host playback and death interruption confirmed; clients and final audio quality remain |
| Chimney smoke #4 | Measured native-effect prototype in unpublished v0.1.66; runtime acceptance pending |
| Flexible hose physics #3 | Separate 29-control rig, two-ended Lua physics and SDK import demonstrated offline; not loaded by the mod. [Lab and remaining integration](docs/research/HOSE_RIG_AND_PHYSICS.md) |

## Retained evidence and next test

The [September 8 record](docs/testing/2026-09-08_TESTER_RESULTS.md) confirms
v0.1.64 host reload preservation and interrupted-reload recovery. Its original
v0.1.65 playtest invitation is superseded by the #14 hold above. The
[September 5 record](docs/testing/2026-09-05_TESTER_RESULTS.md) retains host
career-switch, voice interruption, and close-range launch evidence.
Remote-client checks for #9/#10/#11 remain outstanding; #7/#8 still need their
full explosion/removal/stress matrix. Incidental crash-free impacts do not
complete those gates.

First fix and validate #14 separately, then publish a clearly identified TEST
candidate. Only after that, use [the quickstart](docs/TESTER_QUICKSTART.md),
the combat protocol, and [smoke acceptance](docs/research/BACKPACK_HOSE_AND_SMOKE.md#runtime-smoke-acceptance).
Record the actual loaded banner and both host/client logs. Public portrait
checks can proceed independently on v0.1.56-alpha with TEST disabled.
