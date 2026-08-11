# Warlock ragdoll runtime test protocol

This protocol is the acceptance gate for the native-ratling-physics/custom-
Warlock-visual handoff. A stable ratling corpse is a failure, not a fallback.
Static tests prove only that known-dangerous mechanisms are absent; video is
required to prove the visible model identity.

## Before launching

1. Run from the repository root:

       powershell -NoProfile -File tools/tests/Test-WarlockRagdollRegressions.ps1
       powershell -NoProfile -File tools/Test-WarlockPipeline.ps1

2. Build, splice, validate, deploy, and upload in that order. Never use
   `vmblauncher all`; it can publish the unspliced material bundle.
3. Restart Steam and Vermintide 2 after the Workshop item finishes syncing.
4. Disable **Less Corpses** and any other corpse/physics replacement mod. Use a
   corpse limit of at least 70 for the test.
5. Confirm the console contains the exact candidate banner, currently:

       [doomrocket:LOAD] v0.1.50-dev

   A different banner makes the run invalid.

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
| Remote client | Repeat melee and ranged cases | Client log must report `source=husk` |

For each single-corpse case, retain fixed-camera frames at approximately
0.5 s, 2 s, and 5 s. Do not count an accidental spawn or a unit killed before
it finishes spawning.

## Visual pass criteria

- The corpse is recognizably the Warlock Engineer/Bombardier: body, armor, and
  backpack remain visible.
- No native ratling body or gunner outfit appears.
- No disappearance, stick figure, stretched limbs, roof launch, or exploding
  body parts.
- Nearby physics objects remain stable and there is no sustained frame-rate
  collapse or multi-frame kill freeze.
- Ordinary corpse cleanup still occurs after the game's configured lifetime.

Any visual failure rejects the build even when the log analyzer passes.

## Log pass criteria

Each corpse produces `phase=begin`, time-based `phase=sample`, and
`phase=stop` records with one unique `id=unit-NNNN` or `id=husk-NNNN`.
Samples must reach the 5000 ms checkpoint and satisfy all of the following:

- `owner_alive=true`, `outfit_alive=true` through the observation window;
- `custom_actors=0`, `carrier_reveals=0`, and `parent_mismatch=0`;
- `scale_mutations=0` and `nonhips_translation_mutations=0`;
- calibrated `hips_drift <= 0.25` m;
- `bounds_ratio <= 2` and `max_bone_radius_ratio <= 2`;
- `wall_gap_ms <= 250` ms.

`carrier_reveals=0` covers Lua calls through `Unit.set_mesh_visibility`; it
cannot observe an engine-internal visibility change or a whole-unit visibility
write. The recorded video remains the authoritative carrier-identity check.

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
