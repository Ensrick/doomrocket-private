# Project status

Snapshot updated 2026-09-02. GitHub Issues is the live work queue; this page is
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

The next source candidate is `v0.1.61-dev`. Its principal change makes rocket
detonation an idempotent terminal transition and defers the authoritative
explosion request to the engine's network/damage phase. This targets
[issue #8](https://github.com/Ensrick/doomrocket-private/issues/8), whose log
recorded one projectile attempting 113 impacts after a stale-position failure.

Offline regression tests are necessary but do not prove the fix in game. Keep
#8 open until the TEST Workshop build passes ground impact, player impact,
shot-down rocket, attacker-death, multi-rocket stress, and host/remote-client
tests. Then recheck the earlier native audio/explosion crash in
[issue #7](https://github.com/Ensrick/doomrocket-private/issues/7).

## Feature state

| Area | State |
| --- | --- |
| Accepted body, textures, weapon placement, death drop, host ragdoll | Public alpha; do not replace with unverified TEST work |
| Stormvermin-style survivability and close-range shove | Implemented in TEST; runtime/balance verification remains |
| Distance-aware ballistic aim | Implemented offline; runtime aiming verification remains |
| Custom sound bank and voice events | In development; runtime event registration/playback remains a blocker |
| Flexible backpack tube, chimney smoke, final animation/rig work | Open development work |

## Exact next playtest

Use `docs/TESTER_QUICKSTART.md`, then run the issue #8 matrix above. Require one
explosion, one damage application, one impact record, and projectile removal per
rocket, with no stale-vector error, assertion, or crash. Attach the original
console log and state the host/client role.
