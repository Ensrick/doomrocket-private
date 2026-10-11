# Warlock Engineer ballistic aim and rocket clearance

Issue [#6](https://github.com/Ensrick/doomrocket-private/issues/6) remains open
until a corrective TEST build receives an in-game verdict. Crunch's near-range
ground-shot report is accepted. A solo written observation is sufficient; a
matching complete console log helps identify the version and trajectory.

## Corrective candidate

The current source accounts for the existing rocket's convex hull. The shipped
mesh is 1.2803 m long, with local forward extent 0.540586 m, rear extent
0.739722 m and maximum radial extent 0.126553 m. The former endpoint at the
player root plus 0.25 m treated this hull as a point: a descending nose could
intersect the target's floor before the actor origin reached that endpoint.

`doomrocket_ballistics.lua` rounds those extents outward and calculates the
rocket's lower support along its incoming tangent. It raises the target origin
only when needed for that support plus 0.025 m of clearance, evaluated with
the decoded velocity. If moving the ideal endpoint within a quantizer bin would
leave physics unchanged, it crosses the next Z bin before checking again. Both
the visible aim and projectile use that endpoint and the same decoded muzzle position.
The target's horizontal position and flight-time curve remain unchanged.

The native physics extension receives the decoded launch tangent as its initial
rotation and zero angular velocity. It formerly received the Engineer's flat
yaw and the spinning globe's angular launch velocity. The projectile constructor
aligns and records the actor path immediately. This retains the existing contact,
velocity-deviation and stopped-actor detonation, including shooter exclusions.
It does not alter rocket art, blast damage, or accepted knockback.

These are measured geometry and initialization defects, but the latest v0.1.84
log contains no shots below 8 m. It cannot isolate which defect caused Crunch's
near-range observation. Source checks and a successful build therefore establish
a corrective candidate, not in-game acceptance.

## Shared source contract

The helper owns the trajectory equation:

```text
delta = corrected_target - decoded_muzzle_position
flight_time = clamp(length(flat(delta)) * 0.13, 0.4, 3.4)
velocity = (delta.x / flight_time,
            delta.y / flight_time,
            delta.z / flight_time + 0.5 * 9.82 * flight_time)
```

The launch point remains `p_fx` backed up 0.25 m along the direct aiming
direction, then round-tripped through the native position quantizer. The helper
rejects invalid vectors and speeds at or below 0.1 m/s. Both pose and physics
round-trip the velocity through the same 0.1 m/s quantizer.

Direct `shoot_direction_box` continues to own target selection, facing and view
cone checks. `ballistic_aim_direction_box` owns only the visual tangent. A normal
completed shot retains it for 0.2 s across the behavior transition; interruption,
realignment and expiry clear it. The existing replicated `aim_target` field
carries the pose. No new network schema or model-space rotation is required.

Every launch prints `[doomrocket:AIM]` with range, flat range, flight time,
desired pitch, pose and muzzle errors, corrected target height, predicted hull
clearance at the decoded endpoint, initial clearance relative to the shooter
root, spawn/target Z, and decoded velocity. Impact records carry the shooter ID
and actor/target positions so an early near-range contact can be matched to
its launch. `pose_error_deg` compares the
supplied pose direction with the actual launch velocity. `muzzle_error_deg`
samples the prior evaluated weapon pose in AISystem, so it is diagnostic and
has no numeric acceptance threshold. Written visual observations establish
rendered alignment; a clean pose record alone cannot establish that.

## Offline checks

```powershell
py -3 tools/tests/test_doomrocket_hull_clearance.py
py -3 tools/tests/test_doomrocket_ballistic_aim.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Test-WarlockPipeline.ps1
```

The hull tests execute the actual Lua helper, enclose every shipped mesh vertex,
reproduce the old close-range floor intersection, and check corrected near,
medium, long, elevated and depressed endpoints. They also protect time-clamp
continuity, quantized near-range clearance and initial physics orientation.
The existing suite checks shared pose/launch inputs and compiled-resource
freshness. Terrain between shooter and target can still block a rocket.

## Solo acceptance

Use the corrective TEST build after its verified publication, with exactly one
Warlock Engineer item enabled. Restart the game after Workshop synchronization
and check the current `[doomrocket:LOAD]` banner. GitHub #6 records the published
candidate version and current result; an older protocol banner is not a test gate.

On clear ground, let it fire while outside shove range at near, short, medium
and long distances, then with elevated and lower targets. Near-range shots are
the priority: the full rocket should clear the muzzle/floor, follow its visible
launch tangent and reach the target area. Medium/long shots should retain a
readable arc and normal impacts, damage, reload and knockback. A wall or railing
that physically obstructs the rocket is a valid contact, not a clearance pass.

After a shove or stagger, allow another fire/reload/fire cycle. The next shot
must use a fresh tangent and recover without a snap to the previous target or
script error. Normal play is sufficient; no video, arranged multiplayer session,
second observer, or fixed shot-count matrix is required.

Report what happened in words and attach the matching log if available. If a
single-frame detail cannot be judged during play, leave it unassessed. Do not
repeat the old build to dispute a reported failure.
