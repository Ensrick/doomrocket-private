# Project status

Updated 2026-10-11 UTC. [GitHub Issues](https://github.com/Ensrick/doomrocket-private/issues)
is the live work queue; this page is a short re-entry map.

| Question | Current answer |
| --- | --- |
| Stable player build | [Public alpha v0.1.59-alpha](https://steamcommunity.com/sharedfiles/filedetails/?id=3771657344) |
| Published experimental build | [Warlock Engineer TEST v0.1.86-dev](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730), verified 2026-10-11 05:38 UTC (96,247,057 bytes; content handle `5089446611079694980`). [Release record](https://github.com/Ensrick/doomrocket-private/releases/tag/v0.1.86-dev); [reviewed source](https://github.com/Ensrick/doomrocket-private/commit/d8bee540f134e7468d23b3582dd1d148cb88a356). |
| Candidate under review | v0.1.87-dev preserves the original transition durations while composing smooth authored/legacy transitions. Executable Lua, numerical blend, final SDK/package, and legacy compiled-lane checks pass. The independent final acceptance gate binds their source/receipt identities before the canonical build. No v0.1.87-dev publication or native playback acceptance is claimed. |
| Next TEST work | Six issues remain ready for solo checks; v0.1.86-dev retains the playable assets from verified v0.1.85-dev: hose rest shape [#3](https://github.com/Ensrick/doomrocket-private/issues/3), near-range rocket clearance [#6](https://github.com/Ensrick/doomrocket-private/issues/6), crystal flame resizing [#15](https://github.com/Ensrick/doomrocket-private/issues/15), launcher/hand alignment [#28](https://github.com/Ensrick/doomrocket-private/issues/28), Dutch Spice arena waves [#35](https://github.com/Ensrick/doomrocket-private/issues/35), and lingering audio [#44](https://github.com/Ensrick/doomrocket-private/issues/44). Full sound cues [#5](https://github.com/Ensrick/doomrocket-private/issues/5) remain blocked on Arnaud's new masters; alpha crash [#34](https://github.com/Ensrick/doomrocket-private/issues/34) remains blocked with `needs-info` on crash evidence. |
| Development reports | [Development issue chooser](https://github.com/Ensrick/doomrocket-private/issues/new/choose) |
| Public-alpha reports | [Public issue chooser](https://github.com/Ensrick/doomrocket-public/issues/new/choose) |
| Can both builds be enabled? | No. They share an internal mod identity; enable exactly one. |

## Current evidence and work

The separate [Blender animation authoring guide](docs/ANIMATION_AUTHORING.md)
covers Arnaud's local control rig, portable exporter, and isolated integration
staging. TEST v0.1.86-dev ships the runtime/tooling reviewed in
[PR #47](https://github.com/Ensrick/doomrocket-private/pull/47). The default playable
package retains the shipping body, all thirteen original compiled animations,
and all 138 tracks; no authored or localized profile is active. The localized
coat/belt body, diagnostic clips, and generated artist handoff remain external
to Git and the Workshop package. In the v0.1.86-dev staged integrations, authored
poses own their body/accessory/speed channels and the launcher follows their
attachment frames. Authored/legacy boundaries use immediate transitions;
blends within either owner remain intact. Death retains its original clip and
physics handoff; authored death replacement is rejected.

The v0.1.87-dev candidate replaces those mixed cuts with `snapshot-blend-v1`.
All 154 visible transition durations remain exact. A hidden clone of the existing
outfit evaluates the incoming state on its own skeleton; the bridge blends the
last corrected displayed pose toward that moving target over the original
duration. Interrupted transitions start from the currently displayed pose.
Only legacy targets receive the twelve grip and seven localized outfit
corrections before mixing; authored targets retain their tracks. The launcher
follows the composed visible outfit, and ordinary same-owner blends remain
native. The outgoing pose is frozen during the bridge, so this does not claim
the advancing outgoing-state behavior of a native ASM blend.

The current compositor passes 36 executable Lua regressions and the ownership
controller passes 68, with an independent runtime safety review. Runtime guards
recover after finite hitches, synchronize the initial locomotion baseline,
validate finite root/aim data and loaded sampler availability, hide helper
geometry and shadows, and contain per-entry Lua errors. Bounded stop diagnostics
include helper/visible clocks; returning to native playback requires their
destination phase and clip lengths to agree. The stager copies and binds the
canonical package's explicit state-machine loading rule. All 74 staging guards
pass using actual Windows short-path aliases, along with three reviewed 43-file
overlay routes, nineteen package membership/format/path guards, twenty compiled
Lua table guards, and thirteen numerical reference/inventory guards.

The final fresh isolated SDK/package receipts verify 21 probe root-package
members, all 16 required type/resource pairs, and 12 graph-referenced animation
resources. The compiled Lua manifest matches 924 literal entries and all 138
ordered bones.
All thirteen original compiled clips retain all 138 tracks exactly; all 154
visible transition durations remain exact and all 154 sampler edges are zero.
The [authoring guide](docs/ANIMATION_AUTHORING.md) records the receipt hashes.

Blender, independent FBX import, and SDK checks passed for the v0.1.86-dev
handoff. Its complete legacy outfit audit executed actual Lua against float32
decoded scene poses: 24,077 poses and 850,158,870 weighted vertex comparisons,
with maximum skin error 1.410 mm below the fixed 2 mm gate. Those are historical
supporting results, not acceptance of the new compositor or helper. Current
old/new actual-Lua equivalence checks cover all 24,077 historical poses and
3,322,626 byte-identical float32 local matrices. They perform zero new weighted
vertex evaluations. The fresh compiled-lane bridge proves the 2,192,102-byte
scene/skin/bind/actor prefix, compiled bones, and all thirteen original animation
payloads exact. Together these proofs preserve the earlier 850,158,870 skin
comparisons and 1.410 mm maximum by identity, rather than repeating that work.

The new source-bound actual-Lua blend report passes 3,276 poses (1,638 ordinary
and 1,638 interrupted), 452,088 bone comparisons, and 115,675,560 weighted vertex
comparisons. Maximum skin error is 5.448 micrometres, below the unchanged 2 mm
gate. It also passes 234 pure-authored zero-write checks and 1,638 authored-helper
checks without legacy bone writes. The test uses the frozen continuous idle
diagnostic route, independent float32 API doubles and clocks, and injected
decoded SDK Hermite target poses. Death/stagger clips are numerical specimens,
not authored state registrations; this is not a native playback result.
Neither evidence set captures native `Unit` poses. The hidden helper's animation
event clock reset, evaluation while invisible, mixed transitions, and
outfit/launcher appearance still require an in-game written verdict; the game
is not installed here.

The updated external handoff is
`D:\Game Mods\Vermintide 2 modding\Projects\3D\WarlockEngineer_AnimationRig_Blends_2026-10-11`.
The previous v0.1.86-dev integration folder and archive remain frozen. The new
complete ZIP, `START_HERE.md`, and verification receipt are intended for the
canonical v0.1.87-dev GitHub release after verified publication and download
verification; no hosted delivery is claimed yet. The Workshop default still
uses the shipping body and an empty profile manifest, with all thirteen original
clips and 138 tracks retained. No new art or diagnostic animation is published.

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

The verified `v0.1.86-dev` release tag remains bound to reviewed source commit
`d8bee540f134e7468d23b3582dd1d148cb88a356`; later publication-record documentation must not move it.
Workshop verification confirms delivery, not an in-game pass.

The TEST and public channels remain separate. Use the established
[build, upload and release process](docs/RELEASE_CHANNELS.md) for the next TEST
candidate; do not infer publication from source changes or a local build. The
[hose implementation record](docs/research/HOSE_RIG_AND_PHYSICS.md),
[September 8 tester record](docs/testing/2026-09-08_TESTER_RESULTS.md), and
[September 12 candidate record](docs/testing/2026-09-12_TEST_CANDIDATE.md)
remain historical evidence, not current test gates. Public alpha is unchanged.
