# Project status

Snapshot updated 2026-09-16. GitHub Issues is the live work queue; this page is
the short re-entry map, not a second backlog.

## One-minute re-entry

| Question | Answer |
| --- | --- |
| Stable player build | [Public alpha v0.1.56-alpha](https://steamcommunity.com/sharedfiles/filedetails/?id=3771657344) |
| Published experimental build | [Development TEST v0.1.72-dev](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730), verified upload 2026-09-15 17:17 UTC (manifest 5073916577951013553, 96,240,966 bytes). Crunch reports no spawn crash but no visible hose |
| Current release candidate | v0.1.73-dev: targeted missing-hose diagnostics; no claimed visibility fix. Publication pending |
| Development reports | [Issue chooser](https://github.com/Ensrick/doomrocket-private/issues/new/choose) |
| Public-alpha reports | [Public issue chooser](https://github.com/Ensrick/doomrocket-public/issues/new/choose) |
| Can both builds be enabled? | No. They share an internal mod identity; use exactly one. |

## What changed; what is ready

**v0.1.72-dev fixes the spawn assertion, but its hose is not visible.**
[Crunch's PR #21 follow-up](https://github.com/Ensrick/doomrocket-private/pull/21#issuecomment-5690555871)
and both matching v0.1.72-dev logs record one hose creation, no three-second
simulation sample, then cleanup on death. Existing silent early exits prevent
a reliable cause diagnosis. Candidate **v0.1.73-dev** adds bounded rejection
reasons, first pose-write readback and cleanup counters, with a log analyzer.
The solver, rig, materials, animation ownership and safety guards are unchanged.
Wait for verified publication before testing; visibility is not yet fixed.

**Published 2026-09-14 as TEST v0.1.71-dev** through the canonical adapter from
merged `ce88c4ea` (PR #19): Steam `workshop_log.txt` shows `Upload starting` 01:57:17,
`Uploaded new content ( ManifestID 447865338390972850 )` 01:57:31 and `Upload finished ... OK`;
the adapter verified the Steam metadata (title, public visibility, 96,240,779 bytes,
content handle) before releasing the claim. v0.1.68-dev and v0.1.70-dev have GitHub
prereleases but never reached Steam; the causes and the verified preflight are in
[docs/RELEASE_CHANNELS.md](docs/RELEASE_CHANNELS.md#verified-preflight-2026-09-14).
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

After explicit v0.1.73 TEST publication confirmation, use
[the quickstart](docs/TESTER_QUICKSTART.md) and
[candidate checklist](docs/testing/2026-09-12_TEST_CANDIDATE.md).
Check `[doomrocket:LOAD] v0.1.73-dev` on every peer; attach complete host/client
logs and a continuous hose/aiming video. Public portrait checks can proceed
independently on v0.1.56-alpha with TEST disabled.
