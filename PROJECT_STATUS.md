# Project status

Snapshot updated 2026-09-05. GitHub Issues is the live work queue; this page is
the short re-entry map, not a second backlog.

## One-minute re-entry

| Question | Answer |
| --- | --- |
| Stable player build | [Public alpha v0.1.55-alpha](https://steamcommunity.com/sharedfiles/filedetails/?id=3771657344) |
| Experimental build | [Development TEST](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730) |
| Development reports | [Issue chooser](https://github.com/Ensrick/doomrocket-private/issues/new/choose) |
| Public-alpha reports | [Public issue chooser](https://github.com/Ensrick/doomrocket-public/issues/new/choose) |
| Can both builds be enabled? | No. They share an internal mod identity; use exactly one. |

## Current TEST candidate

The source candidate is `v0.1.64-dev`, fixing the completed reload that restarts
after each shove in [issue #12](https://github.com/Ensrick/doomrocket-private/issues/12).
Its build and publication checks are pending. The last verified upload is
`v0.1.63-dev` on Workshop item `3794172730` (content handle
`6015138325193005907`, 95,645,866 bytes, verified 2026-09-03).

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
| Stormvermin-style armor and health | Implemented; difficulty and damage parity still need explicit runtime checks |
| Distance-aware ballistic aim | Implemented offline; runtime aiming verification remains |
| Custom sound bank and voice events | Host playback and death interruption confirmed; remote-client behavior and final audio quality remain |
| Flexible backpack tube, chimney smoke, final animation/rig work | Open development work |

## Exact next playtest

Use `docs/TESTER_QUICKSTART.md` and the issue #12 reload matrix in
`docs/testing/WARLOCK_COMBAT_TEST_PROTOCOL.md`. Once v0.1.64 is published,
verify its load marker, then test a shove after a completed reload, during an
unfinished reload, and before the first shot. Step out of shove range and
confirm aiming resumes with the correct weapon load. Capture both host and
remote-client views/logs. Retain the #7/#8 impact matrix and existing
career-switch/death-voice regressions in the multiplayer pass.
