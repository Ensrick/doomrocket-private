# Project status

Snapshot updated 2026-09-03. GitHub Issues is the live work queue; this page is
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

The current source candidate is `v0.1.62-dev` for Workshop item `3794172730`.
It retains the idempotent rocket detonation work from v0.1.61 and targets three
new reports: the career-switch deleted-target crash in
[issue #9](https://github.com/Ensrick/doomrocket-private/issues/9), custom sound
registration/playback in [issue #10](https://github.com/Ensrick/doomrocket-private/issues/10),
and the never-selected close-range shove in
[issue #11](https://github.com/Ensrick/doomrocket-private/issues/11).

The clean SDK build, verified material splice, complete local pipeline, and
GitHub source workflow pass. Those checks are necessary but do not prove the
fix in game. Keep
#8 open until the TEST Workshop build passes ground impact, player impact,
shot-down rocket, attacker-death, multi-rocket stress, and host/remote-client
tests. Then recheck the earlier native audio/explosion crash in
[issue #7](https://github.com/Ensrick/doomrocket-private/issues/7).

## Feature state

| Area | State |
| --- | --- |
| Accepted body, textures, weapon placement, death drop, host ragdoll | Public alpha; do not replace with unverified TEST work |
| Stormvermin-style survivability and close-range shove | v0.1.62 direct Ratling-tree gate; runtime/balance verification remains |
| Distance-aware ballistic aim | Implemented offline; runtime aiming verification remains |
| Custom sound bank and voice events | In development; runtime event registration/playback remains a blocker |
| Flexible backpack tube, chimney smoke, final animation/rig work | Open development work |

## Exact next playtest

Use `docs/TESTER_QUICKSTART.md`. Verify the v0.1.62 load marker, then test the
issue #8 impact matrix, switch career while a living and dead Bombardier are in
the Keep, approach within 1.8 m for a shove, and exercise every custom sound.
Require one explosion and one impact per rocket, `shove_selected`/`shove_begin`
telemetry at close range, and non-zero sound `playing_id` values. Attach the
original console log and state the host/client role.
