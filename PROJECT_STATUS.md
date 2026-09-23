# Project status

Updated 2026-09-23. [GitHub Issues](https://github.com/Ensrick/doomrocket-private/issues)
is the live work queue; this page is a short re-entry map.

| Question | Current answer |
| --- | --- |
| Stable player build | [Public alpha v0.1.56-alpha](https://steamcommunity.com/sharedfiles/filedetails/?id=3771657344) |
| Published experimental build | [Development TEST v0.1.77-dev](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730), verified 2026-09-23 03:46 UTC (96,322,558 bytes; content handle 746099109113510749). [Release record](https://github.com/Ensrick/doomrocket-private/releases/tag/v0.1.77-dev) |
| Next TEST work | Firmer hose rest shape for [#3](https://github.com/Ensrick/doomrocket-private/issues/3) is an **unpublished candidate**. The hand/weapon sway mismatch in [#28](https://github.com/Ensrick/doomrocket-private/issues/28) still needs engineering diagnosis and a new published build. |
| Development reports | [Development issue chooser](https://github.com/Ensrick/doomrocket-private/issues/new/choose) |
| Public-alpha reports | [Public issue chooser](https://github.com/Ensrick/doomrocket-public/issues/new/choose) |
| Can both builds be enabled? | No. They share an internal mod identity; enable exactly one. |

## Current evidence and work

Crunch confirms that the **v0.1.77-dev hose is visible and has physics**. The
matching host log shows eight clean hose lifecycles and 11,562 sustained pose
writes. He reports that the hose should hold its authored curve more firmly at
rest. The solver-tuning candidate keeps the physics but is **not on Workshop
yet**. [#3](https://github.com/Ensrick/doomrocket-private/issues/3) remains
blocked from further acceptance until a new TEST build is published. Do not
ask Crunch to repeat the basic visibility test on v0.1.77-dev.

The launcher visibly sways away from the Engineer's hands. This observation is
accepted in [#28](https://github.com/Ensrick/doomrocket-private/issues/28).
The launcher follows the hidden native carrier while the hands follow a
separate visible animation controller. Matched offline clips align closely,
so runtime phase, blend, or aim differences need same-frame measurement before
any transform change. No additional playtest of this known failure is needed
on v0.1.77-dev.

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
