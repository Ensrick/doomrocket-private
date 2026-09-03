# Warprocket Bombardier ballistic-aim protocol

This is the source contract and runtime acceptance gate for the Bombardier's
launcher pose. The launcher must point along the rocket's initial ballistic
velocity, not along the straight line from the enemy to the target.

Status: **v0.1.63-dev is a test candidate, not a runtime-accepted build.** Its
offline checks can prove the solver and its call sites agree, but host and
remote-client video are still required to prove that the animation constraint
actually places the launcher on the visible trajectory.

## Source-of-truth contract

`scripts/mods/doomrocket/utils/doomrocket_ballistics.lua` owns the only copy of
the trajectory constants and the primitive solver. Given a world-space launch
point `start` and endpoint `target`, it calculates:

```text
delta = target - start
horizontal_range = length(flat(delta))
flight_time = clamp(horizontal_range * 0.13, 0.4, 3.4)

velocity.x = delta.x / flight_time
velocity.y = delta.y / flight_time
velocity.z = delta.z / flight_time + 0.5 * 9.82 * flight_time
```

Stingray applies gravity in the negative Z direction, so the positive gravity
compensation in `velocity.z` makes the projectile arrive at `target` after
`flight_time`. `solve_launch_velocity(start, target)` returns that velocity and
flight time. It returns `nil, nil` if either input or the result is not a valid
finite vector. A launch speed at or below 0.1 m/s is also rejected: although
finite, it can become a zero vector in the engine's 0.1 m/s network quantizer
and cannot safely be normalized. The visual path falls back safely and the
firing path aborts before network encoding.

The 0.4-second lower bound is intentionally later than
`ProjectileRocket.update`'s 0.35-second muzzle-clear/impact-arm delay. For a
trajectory with total time `T`, its maximum bow above the straight start/end
chord is `9.82 * T^2 / 8`. The old 1.7-second floor therefore imposed a 3.55 m
ridge on every shot inside 13.08 m. The new floor limits the closest level
shots to 0.20 m; 5 m produces 0.52 m, 10 m produces 2.07 m, and the established
curve is unchanged from 13.08 m onward.

Both consumers must call this same solver exactly once using the same helpers:

- launch point: the weapon's world-space `p_fx` node, backed up 0.25 m using
  the existing muzzle-clearance rule;
- endpoint: the current target unit's root position plus 0.25 m on world Z;
- visual consumer: normalizes the solved, network-round-tripped velocity and
  uses it as the animation-constraint direction;
- projectile consumer: encodes the solved velocity for the physics projectile.

Do not duplicate the equation or its tuning in the behavior action, aim
template, projectile extension, or an asset script. A tuning change is one
intentional change to the shared helper followed by new numerical and runtime
evidence.

## Line of sight is not ballistic aim

The behavior deliberately retains two independent directions:

| State | Meaning | Allowed consumers |
| --- | --- | --- |
| `aim_position_box` / `shoot_direction_box` | Smoothed direct line of sight | Ratling target selection and view cone, facing, raycast preparation, legacy muzzle backstep, and safe visual fallback |
| `ballistic_aim_direction_box` | Initial tangent of the solved rocket arc after a velocity quantizer round trip | Owner launcher/upper-body animation constraint only |

Never feed `ballistic_aim_direction_box` into target selection. A high lob can
exceed the Ratling donor's view cone even while the player remains directly in
front, causing target loss or oscillation. Conversely, never use the direct
line-of-sight box as the normal launcher pose during the ready/fire phase; that
is the original defect.

The active `ballistic_aim_direction_box` belongs to the current attack-pattern
data. It is initialized when alignment ends, refreshed while aiming, and
cleared on realignment and behavior exit so one target's tangent cannot leak
into the next attack. A normally completed shot copies that tangent to
`doomrocket_ballistic_aim_hold_direction_box` on the unit blackboard for a
bounded 0.2 s. This is necessary because the next behavior-tree child replaces
`attack_pattern_data` in the same AI tick, before the AimSystem evaluates the
launch-frame pose. Only `reason == "done"`, at least one fired shot, and a live
action may create the hold. Abort, destruction, and realignment clear it, and
the owner aim template clears it at expiry.

If active and held directions are both absent or invalid, the aim template uses
the direct direction and then the unit's forward direction as safe fallbacks.
The constraint remains suppressed during `doomrocket_reload_start`, as before.

## Network parity

The physics launch velocity crosses `AiAnimUtils.velocity_network_scale` before
the projectile receives it. The owner visual path therefore encodes and decodes
its solved velocity through that same quantizer before taking the direction.
This prevents the pose from following a slightly different, unquantized vector
than the physics actor.

The owner aim template converts the preferred direction into a five-metre
world-space `aim_target`, applies the existing `aim_target` animation
constraint, and writes the existing game-object `aim_target` field. The field
uses the network `position` type (0.01 m tolerance); the husk reads that field
and applies the same constraint. The active and held ballistic boxes are not
added to the network schema and no new ballistic RPC is required. The owner
alone consumes the 0.2 s hold; the husk continues to consume the already
replicated `aim_target` position.

At projectile release the host prints one record:

```text
[doomrocket:AIM] source=unit go_id=<id> range=<m> flat_range=<m> flight_time=<s> desired_pitch_deg=<deg> pose_error_deg=<deg> muzzle_error_deg=<deg>
```

`pose_error_deg` compares the latest visual direction with the newly solved,
decoded launch velocity. `-1` means a missing, zero-length, or invalid vector
and is a failure. Small pose error can arise if the target or muzzle moved
between the last aim update and the release frame.

`muzzle_error_deg` compares the weapon's `p_fx` forward vector with the same
velocity, but it is sampled in AISystem before that tick's AimSystem and
animation evaluation. It therefore observes the previously evaluated weapon
pose, not necessarily the rendered release pose. Preserve it for diagnostics
and trend comparisons; do not impose a numeric release threshold on it.
Side-view release-frame video is authoritative for visible muzzle alignment.

## No Blender/Maya correction in Lua

Every solver input and output is already in Stingray world space. Do not add a
Blender-to-Maya axis swap, handedness conversion, Euler rotation, `+/-90`
degree correction, or model-space bake to this Lua path. Such a correction
would rotate the mathematical trajectory and break projectile/pose parity.

If `pose_error_deg` passes but `muzzle_error_deg` and the visible barrel fail,
investigate the `p_fx` locator, weapon hierarchy, animation constraint, or
exported asset orientation as a separate asset change. Do not compensate for
that evidence by altering the shared world-space velocity.

## Offline gate

From the repository root, run:

```powershell
py -3 tools/tests/test_doomrocket_ballistic_aim.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Test-WarlockPipeline.ps1
git diff --check
```

The focused suite numerically covers minimum-time, range-scaled, maximum-time,
elevated, depressed, and degenerate solutions. Its source checks protect the
shared start/endpoint helpers, separate LOS and ballistic state, lifecycle
cleanup, existing owner/husk replication, quantizer round trip, invalid-vector
guards, and compiled-bundle freshness. Passing it does not replace in-game
testing.

## Runtime setup

1. Clean-build, splice, run the full pipeline, and deploy the candidate through
   the documented headless VMB workflow. Do not use `vmblauncher all`.
2. Do not upload the public Workshop item merely to perform a local host test.
   For a multiplayer test, every participant must run the exact same built
   artifact.
3. Restart Vermintide 2 after deployment or Workshop synchronization. Preserve
   the complete host log and at least one remote-client log.
4. Confirm both logs contain the exact banner:

       [doomrocket:LOAD] v0.1.63-dev

5. Disable mods that replace enemy targeting, animation, projectiles, time
   scale, or network behavior. Use an open area with a clear side view of the
   launcher and the first half of the rocket arc.
6. Use a stationary player for the measurement shots. Measure horizontal range
   from approximately the launcher muzzle to the target; record the actual
   telemetry `flat_range` rather than claiming exact placement from floor
   markers. `range` remains the full three-dimensional diagnostic distance.

## Host/client capture matrix

Record at least three complete shots in every lane. Capture the final aim pose,
release frame, muzzle exit, early arc, and impact in one continuous video.

| Lane | Placement | Expected evidence |
| --- | --- | --- |
| Level close | 2 m horizontal | Minimum 0.4 s flight-time clamp; crest is about 0.20 m above the start/end chord, not the old 3.55 m ridge |
| Level short | 5 m horizontal | Range-scaled flight time near 0.65 s and crest near 0.52 m |
| Level medium | 15 m horizontal | Range-scaled flight time near 1.95 s; barrel, rocket tangent, and side-view arc agree |
| Level long | 30 m horizontal | Maximum 3.4 s flight-time clamp; no return to direct-line aim at long range |
| Elevated | 15 m horizontal and at least 3 m above the muzzle | Launch tangent remains above the direct line and the rocket reaches the elevated endpoint |
| Depressed | 15 m horizontal and at least 3 m below the muzzle | Launcher follows the solved tangent rather than pitching directly down at the target |

Run the complete matrix while hosting. A remote client should then observe at
least the 2 m, 5 m, 15 m, 30 m, one elevated, and one depressed shot. Keep the
client camera side-on; host-only correctness is not multiplayer acceptance.

After the stationary matrix, add one strafing target at approximately 15 m.
This is a stability check, not a promise of predictive leading: the pose may
track the current endpoint, but it must not jitter between the direct line and
the ballistic tangent.

## Interruption and stale-state checks

Perform each case once on the host and repeat at least one on a remote client:

1. Step behind the Bombardier during alignment, then return in front. The
   realigned launcher must use the current target's tangent, never the old one.
2. Stagger or damage it during wind-up, allow it to recover, and observe the
   next shot. There must be no stuck constraint, invalid-vector record, or snap
   to a previous arc.
3. Trigger its close-range shove, retreat to ranged distance, and let it fire.
   The shove must not leave stale ballistic state or prevent normal targeting.
4. Kill or otherwise invalidate the target during wind-up. The action must
   leave cleanly without an assertion or nil-index error.
5. Observe a full fire/reload/fire cycle. The constraint may be suppressed
   during reload, but the next ready pose must reacquire the new launch tangent.
6. Change targets between attacks. The feet may turn on the direct horizontal
   bearing while the launcher elevates along the new ballistic tangent; neither
   should retain the previous target's direction.

## Acceptance criteria

The candidate passes only when all of the following are true:

- the focused test, full offline pipeline, clean build, and compiled-resource
  freshness checks pass;
- both peers prove `[doomrocket:LOAD] v0.1.63-dev`, with no script error,
  assertion, invalid vector, or missing animation-constraint error;
- every host release record has finite range, flat range, flight time, desired pitch, and
  `pose_error_deg <= 0.25`; `pose_error_deg == -1` rejects the shot;
- `muzzle_error_deg` is retained and compared across repetitions, but is not a
  numeric release gate because it samples the prior evaluated pose;
- frame-by-frame side-view video shows that the rendered launcher points along
  the rocket's initial tangent and holds that tangent through the release-frame
  behavior transition, without a direct-line snap;
- the 2 m, 5 m, 15 m, and 30 m shots demonstrate the minimum, short-range,
  established range-scaled, and maximum flight-time regimes; elevated and
  depressed targets both work;
- the remote client sees the same launch orientation and arc as the host,
  without a one-frame direct-line snap at release;
- line-of-sight target acquisition, facing, obstacle/raycast behavior, rocket
  origin, arc, impact location, damage, reload, and close shove show no
  regression;
- every interruption recovers and the next attack uses fresh aim state.

A clean `pose_error_deg` proves that Lua supplied the right tangent to the
constraint, not that the animation graph rendered it. A large or invalid
`muzzle_error_deg` is a triage signal, but must be interpreted with its one-tick
sampling limitation and the video. A plausible-looking launcher without the
version banner and complete host log is not auditable evidence.

## Test report

Attach both original logs and the continuous videos. Record the results without
rounding away failures:

| Peer | Scenario | Shots | Telemetry flat/full range(s) | Flight time(s) | Max pose error | Max muzzle error | Visual result | Errors |
| --- | --- | ---: | --- | --- | ---: | ---: | --- | --- |
| Host | 2 m |  |  |  |  |  |  |  |
| Host | 5 m |  |  |  |  |  |  |  |
| Host | 15 m |  |  |  |  |  |  |  |
| Host | 30 m |  |  |  |  |  |  |  |
| Host | Elevated |  |  |  |  |  |  |  |
| Host | Depressed |  |  |  |  |  |  |  |
| Client | Required subset |  |  |  |  |  |  |  |
| Host/client | Interruptions |  |  |  |  |  |  |  |
