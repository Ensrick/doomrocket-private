# September 8 reload acceptance and reposition follow-up

## Capture provenance

[Crunch's September 7 follow-up on #12](https://github.com/Ensrick/doomrocket-private/issues/12#issuecomment-5576183365)
confirms that the Engineer no longer reloads twice after a kick, and reports
long idle periods between kicks. The audited
[original console log](https://github.com/user-attachments/files/31929650/console-2026-09-07-22.14.44-608cedb9-7dbb-4f1b-ae53-989d88757c2d.log)
has session `608cedb9-7dbb-4f1b-ae53-989d88757c2d`, 3,518 lines, and SHA-256
`9983A35BFE0881178F1F16842038DA047FEA5FAF3CCAD70221CD00010738B8A9`.
Line numbers below refer to that complete attachment.

- Line 1111 loads **v0.1.64-dev**, the published reload/portrait update.
- Line 2309 confirms `self.is_server = true`.
- The sole `peer=client` record, at line 1160, is startup audio configuration
  before hosting. It is not remote-client gameplay evidence.

This is a different capture from the September 7 morning log, which still
loaded v0.1.63. See the [publication record](2026-09-07_TESTER_RESULTS.md).

## Confirmed host behavior

| Check | Log evidence | Result |
| --- | --- | --- |
| Initial loaded rocket survives shoves | Six kicks at lines 3013-3050 before the first shot, with no `reload_begin` | Host pass, consistent with the reporter's visible result |
| Completed reload survives repeated shoves | `reload_complete loaded=true` at 3149; kicks at 3151, 3157, and 3163; firing at 3172 without another reload | Host pass |
| An unfinished reload remains unfinished | Reload starts at 3142, is interrupted by a shove at 3145 with `remaining_s=2.540 loaded=false`, restarts at 3148, and completes at 3149 | Host pass for this early interruption |
| Real shots consume the load | Shots at 3172 and 3193 are followed by reload starts at 3174 and 3195, then completions at 3176 and 3197 | Host pass for these cycles |
| Repeated shove remains functional | 14 selections, 14 starts, and 14 applied impacts | No lost or duplicate impact in this capture |
| Close-range launch protection | Nine in-progress aborts and three initial rejections with `reason=target_too_close` | Guard exercised |
| Bot attack notification cleanup | 14 starts and 14 matching ends | No outstanding notification in the recorded sequence |

There are six reload starts, three completions, and three interruptions. Two
interruptions coincide with enemy deaths at lines 3082 and 3116; the third is
the shove at 3145. Those interrupted cycles are not extra completed reloads.

The capture contains five launch audio records and five impact-template
dispatches. It also records two active combat-voice stops before death
playback (3079 before 3081, and 3114 before 3115), with nonzero playing IDs.
These are useful additional host regressions, not substitutes for the
dedicated explosion and multiplayer acceptance matrices.

## What remains unconfirmed

- Remote-client reload, weapon visibility, shove response, and audio behavior.
- Reload interruption during its final second, and the complete stagger,
  target-loss, and career-switch matrix for this version.
- The new kill-feed portrait's visible colors, native size, and orientation.
  The comment does not report a portrait result and the log cannot establish it.
- Exactly one damage/VFX explosion per rocket, physical rocket removal,
  shoot-down behavior, and remote replication for #7/#8. The aggregate impact
  count alone cannot establish these properties.

The original reload defect now has both a matching host log and visual
confirmation. Keep the outstanding runtime cases explicit when updating #12;
do not describe this capture as full host/client acceptance.

## Long pause between kicks

Repeated kick starts occur about 7.5 seconds apart, with reported cooldown
values from 7.500 to 7.507 seconds. The action lasts 1.20 seconds, leaving
roughly 6.3 seconds before another kick can start. This matches the unchanged
cooldown and Crunch's report of the Engineer doing nothing between kicks;
it is not evidence that the reload fix failed.

The user selected **repositioning** as the response on September 8, tracked in
[issue #13](https://github.com/Ensrick/doomrocket-private/issues/13). The
intended follow-up is movement to create space after a successful shove,
while retaining the 7.5-second shove cooldown, existing shove force, loaded
rocket state, and 1.8-metre point-blank launch protection. This baseline capture
does not test the subsequent reposition implementation.
Use the [reposition test matrix](WARLOCK_COMBAT_TEST_PROTOCOL.md#reposition-after-a-shove)
for the candidate's runtime review.

## Error and shutdown classification

No `[Script Error]`, `[Engine Error]`, access violation, prior attack assertion,
or `[Stale Vector3]` signature occurs. The user chooses Quit Game and the log
records normal shutdown at line 3275.

Line 3404 reports an unrelated **Crosshair Kill Confirmation** unload error
when its `world` field is nil. The capture also contains profiler stalls and
the game's MusicManager warning at 3263. Do not call the entire log
error-free or classify these unrelated messages as a Doomrocket crash.

## v0.1.65 implementation and verification

The candidate implements one bounded reposition request after a completed
kick. The inner selector is shove, reposition, close-range idle fallback,
then the existing ranged sequence. Death/stagger and native smartobject
handling retain their higher priority. A request belongs to the same live
target and is consumed on entry; another kick is required for another attempt.
An empty weapon can finish its genuine reload before using the request.

`BreedActions.skaven_doomrocket.reposition` owns the tuning: 4 m target radius,
3.5 m completion separation, 2.5 s maximum duration, two plans at most,
0.75 s replan checks, 0.3 m arrival tolerance, 0.15 m minimum progress, and
0.5 m maximum vertical nav projection. It uses the donor's ordinary walk
speed and `move_fwd` event. No new animation or physics payload was added.

The action tries rear directions 0, +45, -45, +60, and -60 degrees. Native
`LocomotionUtils.ray_can_go_on_mesh` projects and validates the segment with
the unit's traversal logic; candidates must initially move away from the
target. Goals and progress positions persist only as `Vector3Box` values.
Each accepted plan submits one navigation destination, not a request every
frame. Progress and the native resettable failed-attempt counter govern the
single allowed replan; stale `blackboard.no_path_found` is not authoritative.

Reaching clearance, timeout, blocked path, target replacement/loss, reload
need, or a target crossing behind the remaining route ends movement. Cleanup
stops navigation and restores normal speed only while the unit and navigation
handle are live. `traverse_logic()` is cleared by native navbot release/freeze,
so it guards engine calls that are not safe on a released handle. Aborted
actions do not inject idle animations over stagger/death. A cornered Engineer
may deliberately return to idle; escape is not guaranteed through obstacles.

The new action never writes `reloaded_rocket` or `attack_pattern_data`, and
does not change the kick cooldown/force or the launch action. Existing
portrait, material, weapon, ragdoll and audio assets are unchanged.

Pre-build verification: 22 executable Lua 5.1 reposition tests and all nine
existing reload lifecycle tests pass. The navigation harness supplies native
boundary outcomes, not a simulated engine: movement, animation, avoidance,
and replication still need visible host/client playtests. A compiled-resource
contract rejects the old v0.1.64 package as expected until a clean rebuild;
the new Lua resource and bootstrap/tree/config markers must all be present.

Publication and full package gate results will be recorded below after the
guarded release completes. No v0.1.65 runtime pass is claimed.
