# Project status

Snapshot updated 2026-09-13. GitHub Issues is the live work queue; this page is
the short re-entry map, not a second backlog.

## One-minute re-entry

| Question | Answer |
| --- | --- |
| Stable player build | [Public alpha v0.1.56-alpha](https://steamcommunity.com/sharedfiles/filedetails/?id=3771657344) |
| Published experimental build | [Development TEST v0.1.65-dev](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730), known relocation crash; testing paused |
| Current release candidate | v0.1.71-dev: semi-rigid hose, smoke, #14 lookup correction and #16 aiming delay. Carried from the validated v0.1.67 candidate; standalone receipt-authority publication in preparation |
| Development reports | [Issue chooser](https://github.com/Ensrick/doomrocket-private/issues/new/choose) |
| Public-alpha reports | [Public issue chooser](https://github.com/Ensrick/doomrocket-public/issues/new/choose) |
| Can both builds be enabled? | No. They share an internal mod identity; use exactly one. |

## What changed; what is ready

**Do not test the old v0.1.65-dev relocation build.** Candidate **v0.1.71-dev**
contains the actual hose runtime and registers the missing behavior-action
network names behind [#14](https://github.com/Ensrick/doomrocket-private/issues/14).
It still needs verified publication and matching in-game host/client results;
source changes and automated checks are not acceptance.

The September 12 baseline-uploader attempt failed before publication. Its
session diagnostics do not establish a current root cause or a standing Steam
blocker. A September 13 interactive retry transcript contains no completed
upload result. The user's September 13 instruction supersedes that retry path:
use [Vermintide 2 Tweaker's working build/deploy/upload method](docs/RELEASE_CHANNELS.md).
The exact upstream method and documentation are copied and hash-recorded there.
No routine Steam restart or separate interactive uploader is part of that method.
The original package hashes and build evidence remain in the
[candidate record](docs/testing/2026-09-12_TEST_CANDIDATE.md).

The hose retains Crunch's authored shape with damped secondary motion. It is a
separate 29-control, actor-free skin—not a loose rope or a replacement weapon.
Only the nearest eight eligible hoses within 40 m run; world/body collision is
not implemented. The hose disappears before death/drop so the accepted body,
loaded warhead and launcher physics remain independent.

[Candidate contents and short test checklist](docs/testing/2026-09-12_TEST_CANDIDATE.md)
are the next handoff. Public **v0.1.56-alpha remains unchanged**;
[its release record](https://github.com/Ensrick/doomrocket-public/releases/tag/v0.1.56-alpha)
is independent of this TEST work.

## Feature state

| Area | State |
| --- | --- |
| Accepted body, textures, weapon placement, death drop, host ragdoll | Public alpha; preserve this baseline |
| Engineer kill-feed portrait | Published in public v0.1.56-alpha and TEST; visible acceptance still needed |
| Career-switch crash | v0.1.63 host reproduction passes; remote-client verification remains |
| Close-range shove, rocket exclusion, reload preservation | v0.1.64 host pass; client/edge-case checks remain |
| Reposition after kick #14 | Missing network-action lookup registration corrected in v0.1.67 candidate; host/client reproduction pending |
| Stormvermin-style armor and health | Implemented in development; difficulty/damage parity needs explicit runtime checks |
| Distance-aware ballistic aim / #16 | Candidate holds aim for at least one second before the firing animation, while tracking; visible timing and multiplayer checks remain |
| Custom sound bank and voice events | Host playback and death interruption confirmed; clients and final audio quality remain |
| Chimney smoke #4 | Measured native-effect runtime included in v0.1.67 candidate; placement and host/client acceptance pending |
| Semi-rigid hose physics #3 | Production runtime, skin and lifecycle integrated in v0.1.67 candidate; visible in-game acceptance pending. [Implementation and evidence](docs/research/HOSE_RIG_AND_PHYSICS.md) |
| Under-barrel crystal flame #15 | Crystal measured and identified; effect selection is unresolved, so no flame is included. [Research](docs/research/WEAPON_CRYSTAL_FIRE.md) |

## Retained evidence and next test

The [September 8 record](docs/testing/2026-09-08_TESTER_RESULTS.md) confirms
v0.1.64 host reload preservation and interrupted-reload recovery. Its original
v0.1.65 playtest invitation is superseded by the #14 hold above. The
[September 5 record](docs/testing/2026-09-05_TESTER_RESULTS.md) retains host
career-switch, voice interruption, and close-range launch evidence.
Remote-client checks for #9/#10/#11 remain outstanding; #7/#8 still need their
full explosion/removal/stress matrix. Incidental crash-free impacts do not
complete those gates.

After explicit v0.1.68 TEST publication confirmation, use
[the quickstart](docs/TESTER_QUICKSTART.md) and
[candidate checklist](docs/testing/2026-09-12_TEST_CANDIDATE.md).
Check `[doomrocket:LOAD] v0.1.71-dev` on every peer; attach complete host/client
logs and a continuous hose/aiming video. Public portrait checks can proceed
independently on v0.1.56-alpha with TEST disabled.
