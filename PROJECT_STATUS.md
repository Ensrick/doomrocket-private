# Project status

Updated 2026-10-14 (America/Chicago). [GitHub Issues](https://github.com/Ensrick/doomrocket-private/issues)
is the live work queue; this page is a short re-entry map.

| Question | Current answer |
| --- | --- |
| Stable player build | [Public alpha v0.1.59-alpha](https://steamcommunity.com/sharedfiles/filedetails/?id=3771657344) |
| Published experimental build | [Warlock Engineer TEST v0.1.90-dev](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730), verified 2026-10-14 10:03:32 UTC (96,148,698 bytes; content handle `8005821270151446939`). [Release record](https://github.com/Ensrick/doomrocket-private/releases/tag/v0.1.90-dev); [reviewed source](https://github.com/Ensrick/doomrocket-private/commit/b805a418e2ccd00818f1ad674eb7f2394b6f9b37) ([PR #57](https://github.com/Ensrick/doomrocket-private/pull/57)). |
| Animator handoff | [START_HERE.md](https://github.com/Ensrick/doomrocket-private/releases/download/v0.1.87-dev/WarlockEngineer_AnimationRig_Blends_2026-10-11_START_HERE.md), [complete ZIP](https://github.com/Ensrick/doomrocket-private/releases/download/v0.1.87-dev/WarlockEngineer_AnimationRig_Blends_2026-10-11.zip), and [verification receipt](https://github.com/Ensrick/doomrocket-private/releases/download/v0.1.87-dev/WarlockEngineer_AnimationRig_Blends_2026-10-11.zip.verify.json). Anonymous complete downloads verified 2026-10-11 09:15 UTC. |
| Latest TEST changes | Published v0.1.90-dev combines the gem/audio/hose changes prepared for the unpublished v0.1.89-dev with guarded aiming and facing diagnostics [#55](https://github.com/Ensrick/doomrocket-private/issues/55), plus the sampler parent-frame and teardown fixes [#53](https://github.com/Ensrick/doomrocket-private/issues/53). Publication provides candidates for written in-game verdicts; no alpha promotion has occurred. |
| Remaining work | Six published TEST checks: small hose tune [#3](https://github.com/Ensrick/doomrocket-private/issues/3), near-range clearance [#6](https://github.com/Ensrick/doomrocket-private/issues/6), launcher/hand alignment [#28](https://github.com/Ensrick/doomrocket-private/issues/28), Dutch Spice waves [#35](https://github.com/Ensrick/doomrocket-private/issues/35), lingering audio [#44](https://github.com/Ensrick/doomrocket-private/issues/44), and ordinary-play facing observations [#55](https://github.com/Ensrick/doomrocket-private/issues/55). The 30% audio reduction [#5](https://github.com/Ensrick/doomrocket-private/issues/5) also accepts normal-play feedback, but the full sound pass remains blocked on aiming take/trigger selection and flight/reload sources. Small flame [#15](https://github.com/Ensrick/doomrocket-private/issues/15), staged native animation [#53](https://github.com/Ensrick/doomrocket-private/issues/53), head readability [#56](https://github.com/Ensrick/doomrocket-private/issues/56), and alpha crash [#34](https://github.com/Ensrick/doomrocket-private/issues/34) retain their specific prerequisites. |
| Development reports | [Development issue chooser](https://github.com/Ensrick/doomrocket-private/issues/new/choose) |
| Public-alpha reports | [Public issue chooser](https://github.com/Ensrick/doomrocket-public/issues/new/choose) |
| Can both builds be enabled? | No. They share an internal mod identity; enable exactly one. |

## Current evidence and work

Published TEST v0.1.90-dev corrects demonstrated aiming edge cases: a held ballistic direction
survives attack-data teardown, and missing/non-finite replicated targets never
reach either native constraint. Bounded `FACING` records capture version, role,
network identity, aim source/target, carrier/outfit roots and animation phase.
Host/client agreement remains an in-game question; no root-rotation correction
or new multiplayer test requirement is invented.

The authored sampler now uses the carrier's checked `root_point`, matching the
visible outfit's parent frame. Inventory destruction clears its original
event-mirroring pair without disturbing a replacement pair or ragdoll driver.
The current shipping ASM already has its initial idle self-edge. Native hidden
sampler evaluation, clocks and oracle APIs in #53 remain unverified; historical
numerical receipts do not become fresh acceptance of these changes. The animation
measurements below retain their original v0.1.86-v0.1.88 evidence scope; the
v0.1.90 publication does not turn them into fresh native pose captures.

The old flame command clamped small inputs to 0.010; this is not an engine
minimum. The effect stays disabled, and experimental diagnostics no longer
promise a rendered size in metres. The five material bindings and approved
skin/fur/whisker payloads match published v0.1.88; head readability does not
justify a speculative tint, texture or hitbox change.

Arnaud's October 13 feedback was relayed by the user: the latest patch is mostly
stable, the gem particle still does not resize even at `.0001`, custom audio
should be about 30% quieter, and the hose needs only a slight adjustment to its
resting curve. The relayed written report remains accepted. His later
[#35 startup report](https://github.com/Ensrick/doomrocket-private/issues/35#issuecomment-6158706396)
loads TEST v0.1.88-dev but records PlayFab `verifyCareerLoadouts` HTTP 500/error
1110 in `StateTitleScreenLoadSave`, backend popup 510/1110, then `button_quit`,
cleanup and `[Log end]`. It has no script-error block or arena-specific stack.
This does not establish a Warlock cause or arena pass; v0.1.90 does not target
that backend failure. The proposed public-alpha update remains separate.

Published v0.1.90-dev includes the changes prepared for the unpublished
v0.1.89-dev: it temporarily disables the gem particle while preserving the
crystal and artist assets, and packages all twelve approved
recordings at 70% of v0.1.88-dev's amplitude (0.4949 of the unchanged WAV masters).
Hose stiffness changes from 200 to 240 s^-2, preserving all other physics
parameters, endpoints and rig assets. Actual-Lua measurements show settled
deflection decreasing from 58.55 to 49.01 mm while residual secondary motion
remains 4.93 mm. v0.1.90-dev retains these changes. The original v0.1.89-dev
normalized output and receipt are preserved locally under
`.build/queued/v0.1.89-dev`. These measurements do not establish the in-game appearance.

The separate [Blender animation authoring guide](docs/ANIMATION_AUTHORING.md)
covers Arnaud's local control rig, portable exporter, and isolated integration
staging. Verified TEST v0.1.87-dev published the integration runtime and tooling
reviewed in [PR #49](https://github.com/Ensrick/doomrocket-private/pull/49).
Verified TEST v0.1.88-dev ([PR #51](https://github.com/Ensrick/doomrocket-private/pull/51))
fixes review findings on those paths: launcher relink after reset or error,
sampler re-arm after a clock failure, VT2-only matrix/quaternion calls,
audio record cleanup at despawn, and non-recursive rig-tool cleanup. The default playable
package retains the shipping body, all thirteen original compiled animations,
and all 138 tracks; no authored or localized profile is active. The localized
coat/belt body, diagnostic clips, and generated artist handoff remain external
to Git and the Workshop package. In the v0.1.86-dev staged integrations, authored
poses own their body/accessory/speed channels and the launcher follows their
attachment frames. Authored/legacy boundaries use immediate transitions;
blends within either owner remain intact. Death retains its original clip and
physics handoff; authored death replacement is rejected.

The v0.1.87-dev staged workflow replaces those mixed cuts with `snapshot-blend-v1`.
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
The corrected final `snapshot_blend_acceptance_v87_final.json` joins and rechecks
the complete SDK, package, numerical, and source identities; its SHA-256 is
`11eb2be169774513db107407ef92df9f1ee901f6fa9640bc7eecca11048cb9e5`.

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
outfit/launcher appearance still require an in-game written verdict. Publication
skipped local game deployment because the game is not installed here.

The updated external handoff is
`D:\Game Mods\Vermintide 2 modding\Projects\3D\WarlockEngineer_AnimationRig_Blends_2026-10-11`.
The previous authoring and v0.1.86-dev integration archives remain byte-exact.
All three hosted assets linked above were downloaded anonymously in full and
matched these identities; the ZIP also passed a complete 239-entry readback.

| Delivered asset | Bytes | SHA-256 |
| --- | ---: | --- |
| Complete ZIP | 296,863,810 | `74f40b2033ddfd0ea345aa835bf5b465b42464e0f5bcfa373a214841d7baaf23` |
| START_HERE.md | 5,714 | `70a9dcb831ba98f3d6ed9901c10523ce6ba5a731a63a892c46a3fc3cd5418c44` |
| Verification receipt | 138,288 | `14a9996bf305617d29ead94340b35ce1fc80d12e8a3fcd092d0b380d84ad3517` |

Crunch (`crunch612`) was sent both download/instruction links and the handoff
instructions by Discord DM on 2026-10-11 at 04:16 America/Chicago. The outgoing
message was confirmed in the conversation; recipient reading or acceptance is
not established. The Workshop default still uses the shipping body and an empty
profile manifest, with all thirteen original clips and 138 tracks retained.
The Workshop package does not activate the localized body or diagnostic clips.

Crunch's October 8-10 replies accept the v0.1.84 balance plan, including the
flailing throw with movable camera and prompt rocket impacts. [#33](https://github.com/Ensrick/doomrocket-private/issues/33)
is closed; the 2 s aim (#16) and portrait frame (#30) are also closed. No repeat
acceptance request is needed for those changes.

The new lingering sound report (#44) is accepted. v0.1.85 tracks and stops exact
playing IDs, verifies silence, and covers retained corpses and inventory/world
teardown. Published v0.1.90-dev packages the existing approved audio at 70%
of v0.1.88-dev's amplitude (about 3.10 dB additional attenuation), without
changing its masters. Two supplied aiming takes await Arnaud's choice and
trigger; flight and reload assets remain absent and belong to Arnaud.

v0.1.85 corrects measured rocket hull/initialization defects and quantized floor
clearance (#6); current logs do not isolate the reported near-range shot, so a
new solo verdict remains necessary. Its native attachment-scale particle
candidate (#15) still failed Arnaud's latest visual test. Published v0.1.90-dev
omits the effect using the change prepared for unpublished v0.1.89-dev;
restoring a suitable small flame remains open. A read-only dependency audit
identifies an unactivated small pickup-torch prototype; its rendered size and
colour remain unverified. See [the investigation](docs/research/WEAPON_CRYSTAL_FIRE.md).

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

The verified `v0.1.90-dev` release tag and publication receipt remain bound to
reviewed source `b805a418e2ccd00818f1ad674eb7f2394b6f9b37` ([PR #57](https://github.com/Ensrick/doomrocket-private/pull/57)).
This metadata-only publication journal follows [PR #52](https://github.com/Ensrick/doomrocket-private/pull/52):
it does not move the release tag, rebind the receipt, rebuild or republish.
The preceding [TEST v0.1.88-dev publication](https://github.com/Ensrick/doomrocket-private/releases/tag/v0.1.88-dev)
was verified 2026-10-12 00:46:21 UTC: 96,252,675 bytes, content handle
`5232463954926459657`. Its historical tag remains at
`d9282f8799b7b53ad99e2cd48fcf164a2fadee29`, `v0.1.87-dev` at
`080278425ea2a90da17ae9febcb37039c884326a` and `v0.1.86-dev` at
`d8bee540f134e7468d23b3582dd1d148cb88a356`.
Workshop verification confirms delivery, not an in-game pass.

The TEST and public channels remain separate. Use the established
[build, upload and release process](docs/RELEASE_CHANNELS.md) for the next TEST
candidate; do not infer publication from source changes or a local build. The
[hose implementation record](docs/research/HOSE_RIG_AND_PHYSICS.md),
[September 8 tester record](docs/testing/2026-09-08_TESTER_RESULTS.md), and
[September 12 candidate record](docs/testing/2026-09-12_TEST_CANDIDATE.md)
remain historical evidence, not current test gates. Public alpha is unchanged.
