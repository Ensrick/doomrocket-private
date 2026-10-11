# Project status

Updated 2026-10-11 UTC. [GitHub Issues](https://github.com/Ensrick/doomrocket-private/issues)
is the live work queue; this page is a short re-entry map.

| Question | Current answer |
| --- | --- |
| Stable player build | [Public alpha v0.1.59-alpha](https://steamcommunity.com/sharedfiles/filedetails/?id=3771657344) |
| Published experimental build | [Warlock Engineer TEST v0.1.85-dev](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730), verified 2026-10-11 01:13 UTC (96,226,816 bytes; content handle `2896541613366277250`). [Release record](https://github.com/Ensrick/doomrocket-private/releases/tag/v0.1.85-dev); [reviewed source](https://github.com/Ensrick/doomrocket-private/commit/95388a6a05298ebf2ef08caae7b181a01aab7ca4). |
| Next TEST work | Six issues are ready for solo checks on the verified v0.1.85-dev build: hose rest shape [#3](https://github.com/Ensrick/doomrocket-private/issues/3), near-range rocket clearance [#6](https://github.com/Ensrick/doomrocket-private/issues/6), crystal flame resizing [#15](https://github.com/Ensrick/doomrocket-private/issues/15), launcher/hand alignment [#28](https://github.com/Ensrick/doomrocket-private/issues/28), Dutch Spice arena waves [#35](https://github.com/Ensrick/doomrocket-private/issues/35), and lingering audio [#44](https://github.com/Ensrick/doomrocket-private/issues/44). Full sound cues [#5](https://github.com/Ensrick/doomrocket-private/issues/5) remain blocked on Arnaud's new masters; alpha crash [#34](https://github.com/Ensrick/doomrocket-private/issues/34) remains blocked with `needs-info` on crash evidence. |
| Development reports | [Development issue chooser](https://github.com/Ensrick/doomrocket-private/issues/new/choose) |
| Public-alpha reports | [Public issue chooser](https://github.com/Ensrick/doomrocket-public/issues/new/choose) |
| Can both builds be enabled? | No. They share an internal mod identity; enable exactly one. |

## Current evidence and work

The separate [Blender animation authoring guide](docs/ANIMATION_AUTHORING.md)
covers Arnaud's control rig, portable exporter, and isolated integration staging.
The integration candidate preserves all thirteen original compiled animations
and all 138 tracks. Authored poses own their body and accessory channels through
blends; the launcher follows their attachment frames. An opt-in runtime correction
supports the localized coat/belt skin during legacy playback without resampling
its clips. Generated handoff assets stay outside Git. This work is under review
as candidate v0.1.86-dev in [PR #47](https://github.com/Ensrick/doomrocket-private/pull/47); it does not
change the published builds. Native game playback and the written visual verdict
remain pending; the guide separates those from Blender, Lua, and SDK checks.

Crunch's October 8-10 replies accept the v0.1.84 balance plan, including the
flailing throw with movable camera and prompt rocket impacts. [#33](https://github.com/Ensrick/doomrocket-private/issues/33)
is closed; the 2 s aim (#16) and portrait frame (#30) are also closed. No repeat
acceptance request is needed for those changes.

The new lingering sound report (#44) is accepted. v0.1.85 tracks and stops exact
playing IDs, verifies silence, and covers retained corpses and inventory/world
teardown. Existing approved audio is packaged about 3 dB quieter without
changing its masters. New wind-up, flight and reload assets belong to Arnaud.

v0.1.85 corrects measured rocket hull/initialization defects and quantized floor
clearance (#6); current logs do not isolate the reported near-range shot, so a
new solo verdict remains necessary. It also replaces ineffective flame-variable
resizing (#15) with native attachment scale and immediate command comparisons.
Source tests do not establish how either change looks in the game.

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

The launcher/hand failure (#28) remains accepted. The latest v0.1.84 log contains
600 grip samples; the prior missing-trace status is obsolete. The v0.1.85
build transfers twelve existing upper-body joints through the custom parent
frames while preserving lower-body gait, scales and weapon links. Its probe
flushes scene poses before measurements. Missing custom jump clips remain an
Arnaud asset gap; unsupported events skip transfer to avoid stretching. Ordinary
movement/aim/reload alignment still needs a visual verdict on the published build.

Crunch's reports support closure of the career-switch crash
[#9](https://github.com/Ensrick/doomrocket-private/issues/9), death-voice bug
[#10](https://github.com/Ensrick/doomrocket-private/issues/10), relocation crash
[#14](https://github.com/Ensrick/doomrocket-private/issues/14), and earlier
animation-blender spawn crash
[#20](https://github.com/Ensrick/doomrocket-private/issues/20). The host ragdoll
result in [#1](https://github.com/Ensrick/doomrocket-private/issues/1) is also
accepted. Their issue records retain the supporting observations and logs.

Open issues tagged `ready-for-testing` have a verified published build and
concrete acceptance steps in the issue; `testing` records the pending in-game
verdict. `blocked` names a missing prerequisite: engineering, publication,
source assets, or diagnostic evidence. It is not a request to repeat an
acceptance test that cannot answer the current question. Follow the issue's current
status instead of re-running an older checklist. A **solo test is sufficient**;
written observations and the matching console log establish what happened.
No video, second player, or extra player coordination is required. See the
[TEST quickstart](docs/TESTER_QUICKSTART.md).

The verified release tag remains bound to reviewed source commit
`95388a6a05298ebf2ef08caae7b181a01aab7ca4`; later publication-record documentation must not move it.
Workshop verification confirms delivery, not an in-game pass.

The TEST and public channels remain separate. Use the established
[build, upload and release process](docs/RELEASE_CHANNELS.md) for the next TEST
candidate; do not infer publication from source changes or a local build. The
[hose implementation record](docs/research/HOSE_RIG_AND_PHYSICS.md),
[September 8 tester record](docs/testing/2026-09-08_TESTER_RESULTS.md), and
[September 12 candidate record](docs/testing/2026-09-12_TEST_CANDIDATE.md)
remain historical evidence, not current test gates. Public alpha is unchanged.
