# Two-ended hose: production integration and research

Updated **2026-09-23**. [Issue #3 remains open](https://github.com/Ensrick/doomrocket-private/issues/3).
Crunch confirmed the published v0.1.77-dev hose is visible and has physics;
its resting shape needs more rigidity. The 0.1.78-dev source candidate doubles
the rest-shape spring stiffness while preserving motion. The visual effect of
that change still needs an in-game verdict. The September 12 record below
documents the original controller and its offline evidence.

## Production implementation — September 12

The source keeps the reviewed FBX as
`units/warlock_hose/warlock_hose.fbx`, separate from the untouched body/weapon.
The Lua profile records both live endpoint frames, all 29 authored control
frames, unequal lengths and the compiled control-to-bone transforms below.
There are **zero physics actors**, no foreign animation controller and no
per-bone linking into the character or launcher skeleton.

The runtime uses the actual `j_backpack` and `pRocketLauncher` world poses.
Only its own cosmetic hose bones are written in the safe animation callback;
the mesh root moves with the backpack. Imported rest-bound culling is disabled
using the SDK's authored `culling = "disabled"` policy (also used by its
`core/units/cubemap_probe.unit`): live deformation can leave that static bound.
The explicit nearest-eight/40 m runtime budget controls visibility instead.
The material is hidden until the delayed, verified native-skinned
`wb_hose_child` can be assigned. It uses the weapon's unchanged base/normal
maps plus a new `MASE_Fix.rgb + MASE.a` packed map. The hose is non-emitting.
The sixth material splice does not alter the accepted five body materials.

### Semi-rigid motion, not a loose rope

Distributed springs preserve Crunch's measured rest curve. Reset initializes
from that curve rather than the lab's generic circle; subsequent frames retain
real inertia and integrate gravity, not forced positions or a canned animation.
The v0.1.78-dev candidate uses **200 s^-2** stiffness (v0.1.77-dev used 100),
restoring acceleration is capped at **40 m/s²**, and
the controller supplies exponential velocity damping **5 s^-1**.
The existing 120 Hz fixed step/eight-substep maximum and 2% length-error guard
remain. No segment rest length is stretched to accommodate an impossible span.

Near full extension, an unchanged curved target would contradict the length
constraints. The target bend therefore scales by
`sqrt((length² - span²) / (length² - rest_span²))`, capped at one, with a zero
lower bound. Crunch's curve is unchanged at its authored span and relaxes
smoothly under tension. This fixed an actual 99.99%-extension reset loop;
the regression forbids resets rather than accepting them as success.

Frame transport preserves the original dense-curve tangent offset at each
control and follows owner rotation before transporting along the new tangent.
It avoids `Quaternion.look` poles and checks the resulting frame before native
writes. Numerical tests cover full independent endpoint rotations as well as
rigid-motion covariance and finite, right-handed frames.

### Ownership and deliberate limits

- A local cosmetic unit follows the exact current owner/outfit/launcher on
  each viewing peer, with no custom hose RPC or networked physics.
- Only the nearest **eight** eligible hoses within **40 m** are active. This
  limits cosmetic cost, not the number of spawned Engineers.
- There is **no body, wall or self-collision**. Clipping is a known initial
  limitation; collision must not be claimed from the absence of physics actors.
- Death, drop, inventory freeze/destruction and world teardown remove the
  hose before the existing corpse/weapon handoff. The hose does not remain
  physically attached to dead/dropped objects. Pause/teleport and module reset
  have explicit handling; unknown worlds are not probed through stale handles.

Run the production gates with:

```powershell
py -3 tools/tests/test_doomrocket_hose_assets.py
py -3 tools/tests/test_doomrocket_hose_dynamics.py
py -3 tools/tests/test_doomrocket_hose_lifecycle.py
py -3 tools/tests/test_doomrocket_hose_dynamics.py --metrics
py -3 tools/tests/test_doomrocket_hose_dynamics.py --benchmark
```

The v0.1.78-dev offline measurements show unchanged authored geometry at zero
gravity, approximately 5.9 cm maximum settled gravity deflection (11 cm in
v0.1.77-dev), and actual residual
motion after the weapon stops. Twelve production dynamics tests and all 21
earlier solver regressions pass; the numeric modules allocate no new tables
over 2,000 warmed-up frames. A 20-hose physics-plus-frame run measured roughly
7.4 ms mean / 11 ms maximum per 60 Hz frame, **excluding native bone writes and
rendering**. These are not live performance or visual acceptance claims.

Crunch's matching v0.1.77-dev host log and written observation establish visible
physics. The remaining #3 question is whether the new resting shape looks right
in game. Public alpha is unchanged; an offline solver pass cannot answer that
visual question.

## September 10 offline lab record — historical

The sections below retain the evidence that preceded production integration.
Their prototype-only statements and original remaining-work list describe
September 10, not the current source candidate.

### Practical result at the end of the lab

The hose is now rigged, exported and exercised with a real two-ended inertial
simulation in Blender. The separate skinned asset also compiles through the
installed VT2 SDK. It has **no physics actors** and does not replace or edit
the accepted body or weapon.

At the end of that lab it was **not enabled in TEST or public**. No game process, deployment or
Workshop upload was used for this investigation. The tools live under
[`tools/hose_lab`](../../tools/hose_lab/); generated models and demonstrations
remain under ignored `.build`. Engine integration, lifecycle, collision,
frame/twist continuity and runtime performance still need acceptance.

## What was established about native physics

We recovered an authorable `type="chain"` constraint using the existing SDK,
without an Autodesk Stingray editor or copied flail controller bytes. Nine
source-generated fixtures compile and produce the expected independently
decoded descriptor changes. The same reader also understands the two native
flail descriptors inspected earlier.

Important compiler traps are now reproducible: scalar settings such as mass
must be **expression strings**; a numeric value can silently become a default.
Guessed pin/target fields compile but leave the descriptor byte-identical.

The investigated SDK implementation fixes its first particle and integrates
the others, with a synthetic free tip. It does not establish a second moving
endpoint. Zero mass is **not** a safe pin: runtime inspection found an
unchecked reciprocal of that mass. Zero-mass fixtures are compile-only and
must never be attached to a runnable unit.

The exact schema, SDK hash, offsets, controlled mutations and limitations are
in the [native-chain lab](../../tools/hose_lab/native_chain/README.md).
Its empty-animation fixtures prove compilation only, not an in-game chain
simulation. This native route may be useful for future one-ended props; it
was not forced onto the two-ended hose.

## Authored rig and attachment choice

The source is still Crunch's SHA-pinned
`xud4soo5fg7g8qd4.blend`, now on D:. It was opened with embedded script
execution disabled and was never overwritten.

The 1,608-vertex hose consists of **seven flexible tubes and six closed
collars**, not thirteen interchangeable bones. Each tube has fifteen
twelve-vertex rings. Shared section boundaries form a 99-ring centreline.

- 29 deform controls, `j_hose_00` through `j_hose_28`, are flat siblings under
  a separate `hose_root`. No existing character bone was added or changed.
- Flexible rings use at most two weights, based on measured arc length.
  Each metal collar is rigidly weighted to its section join. Coincident seam
  vertices have identical weights.
- The source geometry, polygons, UVs, material identity and bind shape are
  retained. A new pose bends the hose; the source mesh is not baked into a
  deformed weapon.
- The dense centreline is 2.32813285 m; the 28 unequal simulation intervals
  total **2.32380619 m**. The earlier approximately 2.265 m dimension was not
  the actual chain rest length.

The backpack connection is directly supported by geometry: its endpoint
matches cap vertex 5426, weighted entirely to `j_backpack`, within 0.23 µm.
The corresponding shipping-body vertex and compiled bind frame were checked.

The weapon end was not attached to the detached launcher in the artist scene.
For this prototype, the lower cylindrical grip-base cap is the inlet:
its roughly 37.603 mm skirt radius accommodates the 34.302 mm hose radius,
and the opposed axes agree within 1.623°. The end is inserted 1 mm inside the
skirt. **This inlet is inferred from fit and visible geometry, not confirmed
by Crunch.** No weapon cap is removed. The much smaller separate short
conduit is not substituted for this connection.

The [rig lab](../../tools/hose_lab/rig/README.md) contains the complete
reproduction steps and compact measured contract. Generated handoff files:

```text
.build/hose_rig_probe/warlock_hose_rig.blend
.build/hose_rig_probe/warlock_hose.fbx
.build/hose_rig_probe/warlock_hose_pose_preview.blend
.build/hose_rig_probe/offline_hose_physics_demo.gif
```

The compressed rig and preview are approximately 12–13 MB each. The GIF is
explicitly labelled **offline**, with moving and stationary weapon phases.

## Compiler validation and scale correction

The reviewed FBX is SHA-256
`23d91cb22b5ccf2526c88330e0d8ddc27562b5410296ade59e766eaa3df7838c`.
An isolated unit with a diagnostic material compiled successfully:

| Measurement | Result |
| --- | --- |
| Compiled unit SHA-256 | `03d91dee6a2fd4ff06dab2d5bd02db6fafb8b797490cea0514decc310abed667` |
| Physics actors | 0 |
| Deform controls | All 29 retained, under one parent |
| Skin palette | 29 controls plus the exporter-retained unused root entry |
| Compiled vertices | 1,893 after render-vertex splitting |
| Mesh coverage | All 1,608 source polygons and 3,024 triangles retained with correct winding; coincident seams weld to 1,536 positions |
| Maximum position quantization difference | 0.441475 mm in world metres |
| Maximum weight quantization difference | 0.000242; positive bone assignments match |
| Source-versus-compiled weighted deformation | Three per-bone pose sets: maximum 0.618823 mm difference, below the 2 mm quantization gate |

This FBX does **not** have the same bind-scale arrangement as the existing
body/chimney. Its metre-valued vertices sit under a scale-100 mesh node; the
compiled geometry stream is scaled by 0.01. A future driver must include the
compiled mesh bind transform, in column-vector notation:

```text
W_bone = W_control * inverse(rest_control) * mesh_bind_world * inverse(compiled_inverse_bind)
```

Here `mesh_bind_world` is `diag(100, 100, 100, 1)` for the reviewed asset. Omitting it produces a
100-fold size error. The verifier checks the native rest skin against the mesh
bind and compares source and decoded compiled weighted vertices at three
independent per-bone pose sets. Either legal quad diagonal is accepted, but
missing geometry, changed winding, invalid weights (including unused NaN slots)
and actor-bearing units are rejected. Acceptance checks remain enabled under
optimized Python. Do not
copy the chimney's local matrix or normalize the new bone matrices.

The [isolated asset lab](../../tools/hose_lab/compiled/README.md) stages its own
files, compiles hidden and verifies the result. It does not build or publish
the playable mod. The diagnostic material is not a claim of final in-game
hose texture acceptance.

## Two-ended inertial simulation

The separate Lua 5.1 prototype pins both ends and evolves the interior using
gravity, velocity and compliant distance constraints. It uses the actual 28
unequal lengths. It is not a prerecorded animation, endpoint-only stretch,
or a body/weapon physics actor.

The first sequential solver was rejected: it was too costly at full rig
size and sometimes masked convergence failures with resets. The replacement
solves the chain's coupled tridiagonal constraint system with a four-iteration
cap and residual early exit. This is based on
[XPBD's compliant constraint formulation](https://mmacklin.com/xpbd.pdf), with
a coupled chain solve rather than independent per-link relaxation.

The implementation has a fixed 120 Hz timestep, at most eight substeps,
interpolated anchor samples, exact current-frame render endpoints, finite
guards, and explicit teleport/long-frame resets. Impossible spans beyond
authored length hide the prototype rather than stretching its rest lengths.
Finite compliance permits bounded extension; the error guard is 2%, not a
claim of perfectly inextensible material.

Twenty-one executable tests include motion, sag, damping, timestep parity,
invalid inputs, unequal lengths, allocation bounds, and near-taut cases that
explicitly forbid reset-masked failures. A real boundary bug was found and
fixed: a separate zero-compliance render projection was inconsistent with
the compliant simulation. Both now use the same compliance. A second regression
rotates fully stretched endpoints for 600 frames without hiding or resetting:
floating-point roundoff is tolerated at machine precision, while genuine
overstretch is still rejected. Rest lengths are never redefined to fit.

The reviewed 20-hose Lua-only benchmark measured approximately **2.62 ms/frame
mean, 3.95 ms maximum** at ordinary two-substep/60 Hz updates. At the eight-
substep cap it measured **9.12 ms mean, 12.95 ms maximum**. These figures exclude
engine bone writes, rendering, collision and other mod work; dense scenes
still need a cosmetic budget and real profiling. See the
[solver lab](../../tools/hose_lab/solver/README.md) for exact runs and commands.

## What the demonstration proves—and what it does not

The actual Lua solver trajectory was applied to the actual exported rig,
including all 1,608 skinned vertices over 60 frames. The weapon first moves,
then stops while the hose retains inertia. Numerical checks cover both ends,
seams, rigid collar dimensions and the skinning equation throughout.

This establishes a working **offline rig + physics prototype** and a compiled
asset path. It does not establish native game integration or collision.
Both endpoints in the demonstration are prescribed test transforms, not
captured game animations. The preview's frame construction also needs
continuity tests for large rotations before being used as a runtime driver.

The local source-only lab run covered 80 tests: 79 passed; one file-symlink
fixture was skipped because Windows did not grant symlink-creation privilege.
Actual junction and hard-link rejection tests passed. Ten source/FBX checks,
the Blender round-trip deformation checks, both guarded SDK compiler probes,
and the existing source/weapon/ragdoll regression suites also passed. These
are offline results, not substitutes for a game session.
The first clean-environment run exposed Windows short-path aliases in its
temporary directory. The path preflight now canonicalizes only the known
repository prefix, retaining redirect checks on every output descendant;
actual 8.3-path and non-bypass regressions cover this portability fix.

## September 10 integration plan — superseded by the implementation above

This original plan is retained for traceability. The candidate now implements
the driver, frame transport, budget and lifecycle; collision remains explicitly
absent, and visible game acceptance is still outstanding.

1. Implement a separate cosmetic-unit driver using the verified compiled
   profile, reading actual live backpack and weapon transforms. Never write
   the character or launcher bones/actors from the solver.
2. Handle frame/twist continuity, moving-unit culling and a bounded per-frame
   cosmetic budget. Define body/world collision or document the initial
   collision limitation; none is implemented in the current solver.
3. Wire exact owner/outfit/weapon lifetimes, host/husk creation, pause and
   teleport behavior, and pre-death/inventory/world cleanup. The safe initial
   death policy is removal before the independent corpse/weapon handoff,
   not physically pulling those actors together.
4. Confirm the chosen inlet with Crunch or visually approve it in the final
   pose; verify wield/stow, aim/reload, corners, long frames and multiple units.
5. Correct and verify the separate TEST relocation crash #14 before a TEST
   Workshop upload. Keep public v0.1.56-alpha unchanged.

This September 10 plan is historical. Current #3 acceptance is the rest-shape
visual verdict on a published TEST build; no two-player gate remains.
