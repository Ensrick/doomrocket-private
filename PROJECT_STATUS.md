# Project status

Updated 2026-10-07 UTC. [GitHub Issues](https://github.com/Ensrick/doomrocket-private/issues)
is the live work queue; this page is a short re-entry map.

| Question | Current answer |
| --- | --- |
| Stable player build | [Public alpha v0.1.59-alpha](https://steamcommunity.com/sharedfiles/filedetails/?id=3771657344) |
| Published experimental build | [Warlock Engineer TEST v0.1.81-dev](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730), verified 2026-10-07 18:08 UTC (96,330,230 bytes; content handle 8373700339329978262). [Release record](https://github.com/Ensrick/doomrocket-private/releases/tag/v0.1.81-dev) |
| Next TEST work | The Dutch Spice Into the Nest arena fix in [#35](https://github.com/Ensrick/doomrocket-private/issues/35) is **ready for a solo check**. The balance pass for [#33](https://github.com/Ensrick/doomrocket-private/issues/33) and the 2 s aim floor for [#16](https://github.com/Ensrick/doomrocket-private/issues/16) are **ready for a solo check**. The firmer hose rest shape in [#3](https://github.com/Ensrick/doomrocket-private/issues/3) is **ready for a solo visual verdict**. Hand/weapon sway [#28](https://github.com/Ensrick/doomrocket-private/issues/28), near-range ground shots [#6](https://github.com/Ensrick/doomrocket-private/issues/6), sound [#5](https://github.com/Ensrick/doomrocket-private/issues/5), and crystal flame [#15](https://github.com/Ensrick/doomrocket-private/issues/15) need engineering; the portrait frame [#30](https://github.com/Ensrick/doomrocket-private/issues/30) is in the next candidate. |
| Development reports | [Development issue chooser](https://github.com/Ensrick/doomrocket-private/issues/new/choose) |
| Public-alpha reports | [Public issue chooser](https://github.com/Ensrick/doomrocket-public/issues/new/choose) |
| Can both builds be enabled? | No. They share an internal mod identity; enable exactly one. |

## Current evidence and work

v0.1.81-dev applies the #33 balance plan: rocket damage to other enemies x0.6,
a 2 s aim floor, Ratling Gunner health and armor, a distance-scaled push instead
of the camera-grabbing catapult, and detonation on contact. The Workshop page
lists health and rocket damage per difficulty, computed by executing vanilla's
damage chain.

v0.1.80-dev stops the mod from re-running vanilla breed and pickup settings at
load. That re-run had put back vanilla functions that Dutch Spice hooks, so its
Into the Nest arena Stormvermin never spawned (#34, #35). The Legend loading
crash in #35 is a misspelled breed (`skaven_storm_vzermin`) in Dutch Spice's
own Legend warlord spawn list and needs a Dutch Spice fix.

Crunch confirms that the **v0.1.77-dev hose is visible and has physics**. The
matching host log shows eight clean hose lifecycles and 11,562 sustained pose
writes. He asked for a firmer resting curve. The v0.1.79-dev Workshop build
strengthens the rest-shape spring while retaining the secondary physics.
[#3](https://github.com/Ensrick/doomrocket-private/issues/3) now asks only for
the new shape-and-motion visual verdict, not a repeat of basic visibility.

The launcher visibly sways away from the Engineer's hands. This observation is
accepted in [#28](https://github.com/Ensrick/doomrocket-private/issues/28).
The launcher follows the hidden native carrier while the hands follow a
separate visible animation controller. Matched offline clips align closely,
so runtime phase, blend, or aim differences need same-frame measurement before
any transform change. The bounded v0.1.79-dev pose probe is diagnostic only;
do not treat it as a grip fix or ask for another acceptance test on this build.

Crunch's reports support closure of the career-switch crash
[#9](https://github.com/Ensrick/doomrocket-private/issues/9), death-voice bug
[#10](https://github.com/Ensrick/doomrocket-private/issues/10), relocation crash
[#14](https://github.com/Ensrick/doomrocket-private/issues/14), and earlier
animation-blender spawn crash
[#20](https://github.com/Ensrick/doomrocket-private/issues/20). The host ragdoll
result in [#1](https://github.com/Ensrick/doomrocket-private/issues/1) is also
accepted. Their issue records retain the supporting observations and logs.

Open issues tagged `ready-for-testing` have a published build and concrete
steps in the issue. `blocked` means engineering or an unpublished feature is
needed before asking for another acceptance test. Follow the issue's current
status instead of re-running an older checklist. A **solo test is sufficient**;
written observations and the matching console log establish what happened.
No video, second player, or extra player coordination is required. See the
[TEST quickstart](docs/TESTER_QUICKSTART.md).

The TEST and public channels remain separate. Use the established
[build, upload and release process](docs/RELEASE_CHANNELS.md) for the next TEST
candidate; do not infer publication from source changes or a local build. The
[hose implementation record](docs/research/HOSE_RIG_AND_PHYSICS.md),
[September 8 tester record](docs/testing/2026-09-08_TESTER_RESULTS.md), and
[September 12 candidate record](docs/testing/2026-09-12_TEST_CANDIDATE.md)
remain historical evidence, not current test gates. Public alpha is unchanged.
