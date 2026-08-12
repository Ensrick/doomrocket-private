# Warlock ragdoll runtime test protocol

This protocol is the acceptance gate for the native-ratling-physics/custom-
Warlock-visual handoff. A stable ratling corpse is a failure, not a fallback.
Static tests prove only that known-dangerous mechanisms are absent; video is
required to prove the visible model identity.

Recorded status: uploaded v0.1.50 passed an 11-corpse, five-second host
telemetry baseline on 2026-08-12. That build ended pose driving at monitor
completion and logged only the callback gap adjacent to each sample. The later
persistent sleep/wake driver, game-time monitor, worst-gap accumulator,
calibration preflight, and visibility hard block have static coverage but no
runtime pass yet. Visual signoff and remote-client `source=husk` coverage also
remain required.

## Before launching

1. Run from the repository root:

       powershell -NoProfile -File tools/tests/Test-WarlockRagdollRegressions.ps1
       powershell -NoProfile -File tools/Test-WarlockPipeline.ps1

2. Build, splice, validate, deploy, and upload in that order. Never use
   `vmblauncher all`; it can publish the unspliced material bundle.
3. Restart Steam and Vermintide 2 after the Workshop item finishes syncing.
4. Disable **Less Corpses** and any other corpse/physics replacement mod. Use a
   corpse limit of at least 70 for the test.
5. Confirm the console contains the exact hardened candidate banner and record
   its Workshop manifest ID:

       [doomrocket:LOAD] v0.1.51-dev

   `[doomrocket:LOAD] v0.1.50-dev` identifies the uploaded baseline, not the
   persistent-driver candidate, and makes the run invalid.

## Capture matrix

Use non-gibbing attacks. Do not use the Doomrocket backpack/`aux` explosion as
the killing blow. Record the corpse continuously for at least 10 seconds, with
the full body in frame.

| Lane | Scenario | Minimum observations |
|---|---|---|
| Host | Low-impulse melee torso kill | One corpse on level ground |
| Host | Ranged headshot | One corpse; embedded projectile may remain |
| Host | Terrain | One torso kill on stairs or a slope |
| Host | Concurrency | Five Doomrockets killed rapidly in the same view |
| Host | Pause | Pause before 2 s, wait at least 5 wall-clock seconds, resume; game-time checkpoints must continue rather than jump to completion |
| Host | Post-monitor wake | Let one non-gibbed corpse settle past 5 s, then wake/move it with an ordinary physics interaction; the Warlock visual must resume with the carrier |
| Host | Cleanup/reload | Observe normal corpse deletion, then leave and re-enter `StateIngame`; no stale callback or reload error |
| Remote client | Repeat melee and ranged cases | Client log must report `source=husk` |
| Remote client | Post-monitor wake and cleanup | Visual stays attached after wake; no stale husk driver after deletion or level exit |

For each single-corpse case, retain fixed-camera frames at approximately
0.5 s, 2 s, 5 s, and after the post-monitor wake. Do not count an accidental
spawn or a unit killed before it finishes spawning.

Run the pause lane in a separate console capture. Its intentional wall-clock
gap is expected to exceed the 250 ms performance limit even though game-time
checkpoints correctly do not advance; do not include that trace in the main
analyzer acceptance log. The non-paused host/client captures must independently
pass the wall-gap threshold.

## Visual pass criteria

- The corpse is recognizably the Warlock Engineer/Bombardier: body, armor, and
  backpack remain visible.
- No native ratling body or gunner outfit appears.
- No disappearance, stick figure, stretched limbs, roof launch, or exploding
  body parts.
- Nearby physics objects remain stable and there is no sustained frame-rate
  collapse or multi-frame kill freeze.
- A settled corpse still carries the Warlock visual when woken after five
  seconds; `monitor_complete` must not freeze it in the old pose.
- Ordinary corpse cleanup still occurs after the game's configured lifetime.

Any visual failure rejects the build even when the log analyzer passes.

## Log pass criteria

Each corpse produces `phase=begin`, game-time `phase=sample`, and
`phase=stop` records with one unique `id=unit-NNNN` or `id=husk-NNNN`.
There must be exactly one sample at 0, 100, 250, 500, 1000, 2000, and 5000 ms,
followed by `reason=monitor_complete`. That stop closes telemetry only; the
internal pose driver must remain registered until deletion/reset. Samples must
satisfy all of the following:

- `owner_alive=true`, `outfit_alive=true` through the observation window;
- `nodes=90` at every checkpoint;
- `custom_actors=0`, `carrier_reveals=0`, and `parent_mismatch=0`;
- `scale_mutations=0` and `nonhips_translation_mutations=0`;
- calibrated `hips_drift <= 0.25` m;
- absolute `hips_delta <= 0.25` m;
- `root_delta <= 0.25` m, `named_root_drift <= 0.25` m, and
  `anchor_max_drift <= 0.5` m;
- `bounds_ratio` and `max_bone_radius_ratio` each remain within 0.5–2.0×;
- `wall_gap_ms <= 250` ms. This is the maximum callback gap observed since
  the previous checkpoint, not merely the frame immediately before logging.

`carrier_reveals=0` covers tracked Lua calls through both
`Unit.set_mesh_visibility` and `Unit.set_unit_visibility`. A mesh reveal attempt
is forced to `false`; a whole-unit reveal attempt is synchronously followed by
a complete carrier-mesh re-hide. Either incident still rejects the run. These
hooks cannot observe an engine-internal visibility or culling change, so the
recorded video remains the authoritative carrier-identity check.

Analyze a captured console log with:

    py -3 tools/analyze_warlock_ragdoll_log.py "C:\path\to\console.log"

The analyzer must print `[ragdoll-log] OK`. Attach the original console log and
the corresponding video to the issue; do not paste only selected lines because
concurrent corpse IDs and load/version evidence must remain auditable.

## Failure triage

- `carrier_reveal` or a visible ratling: reject immediately; this is the
  v0.1.49 substitution failure.
- Large `hips_drift`, bounds ratio, or bone-radius ratio: reject as a retarget
  failure; do not compensate by revealing the carrier.
- Bounded telemetry but no visible Warlock: run a separate culling-only A/B
  build. Do not change physics, pose transfer, materials, and culling together.
- Host passes but client/husk fails: treat it as a lifecycle/network-lane bug;
  a host-only result is not acceptance.
- The Warlock detaches only after 5 s or after the wake interaction: reject the
  persistent-driver/sleep-wake lane even if the analyzer reports OK. The compact
  five-second schema cannot prove behavior after `monitor_complete`.
- Checkpoints complete while paused: reject the game-time monitor lane.
- An observed hitch is absent from `wall_gap_ms`: reject worst-gap
  accumulation; do not treat the adjacent-frame value as interval evidence.
- Reload/level exit emits a stale callback error: reject teardown cleanup.
