# Backpack hose physics and chimney smoke

Research/implementation snapshot: **2026-09-10**. Development only.

## Decisions and tracking

- [#3: hose secondary physics](https://github.com/Ensrick/doomrocket-private/issues/3)
  remains **open**. Native examples exist, but a safe, editable two-ended
  constraint authoring/export contract is missing. No hose was added, rigged,
  simulated, or restored as a rigid attachment in this pass.
- [#4: chimney smoke](https://github.com/Ensrick/doomrocket-private/issues/4)
  remains **open**. The model and native particle API provide enough evidence
  for a measured prototype in **unpublished v0.1.66-dev**. Offline validation
  is not an in-game visual or safety pass.
- The already-published TEST v0.1.65-dev has a separate
  [relocation crash #14](https://github.com/Ensrick/doomrocket-private/issues/14).
  This work does not fix that crash and must not be uploaded on top of it
  before it is corrected and verified. No Workshop publication is part of
  this pass. Public v0.1.56-alpha is unchanged.

## Inputs and reproducible evidence

The artist scene is available at
`D:\Game Mods\Vermintide 2 modding\Projects\3D\xud4soo5fg7g8qd4.blend`.
It was inspected read-only in Blender 5.2 with automatic script execution
disabled; the original scene was not saved or altered. No Rigify changes
were attempted.

| Input | SHA-256 |
| --- | --- |
| Artist `.blend` | `ab6ebc9ef45cea6e402bbd0415c2d40716824552c2ab514947902d1eac06c1b2` |
| Shipping body FBX | `cb2eba0224d1eff044a30b1bf0269d1a10395e8db9244af5c011e5c0ba0bd0bc` |
| Compiled body unit payload | `ed74ddc662e2a0d43601476f520ed4349b2517114b0875f92c2c0772451b03d7` |
| Native Warpfire weapon unit | `d59174856385d2e0818e53e00dd91d08f7e8c475644f12e95790c277da9d5df4` |
| Native backpack smoke particle | `3534fe7bbf3416783ac239c4857b91f73fa0ab9cfee71ca952363aaa25e866b6` |

The canonical measurements, inverse bind and asset identity are in
[`warlock_chimney_anchor.json`](../../tools/fixtures/warlock_chimney_anchor.json).
The particle hash is recorded from the extracted resource; the mod references
the native effect rather than distributing it.

```powershell
py -3 tools/tests/test_doomrocket_chimney_anchor.py
py -3 tools/tests/test_doomrocket_backpack_smoke.py
```

The anchor test reads the actual shipping FBX positions and skin weights.
When a compiled package exists, it also checks the body payload hash, inverse
bind, quantized rim positions/weights, and packaged Lua profile. It deliberately
rejects a stale compiled package without the new profile. CI can run source
checks without Blender, the SDK, donor files, or a game install. Controller
tests execute Lua 5.1 against instrumented native API doubles; they are not
engine integration tests.

Full local inspection scripts, decoded reports and annotated geometry renders
remain in ignored `.build/hose_smoke_research/`. They are diagnostic evidence,
not release inputs. Do not commit game-derived donor payloads or copied
animation controllers. Reinspect the artist scene if geometry changes;
changing fixture hashes to silence a failure is not remeasurement.

## What the native Warpfire hose proves

Native weapon: `units/weapons/enemy/wpn_skaven_warpfiregun/wpn_skaven_warpfiregun`.
Its inventory mapping attaches separate endpoints:

| Character source node | Weapon target node |
| --- | --- |
| `j_leftweaponattach` | weapon root and `j_hose_start` |
| `j_ammo_attach` | `j_hose_end` |

See the game's
[attachment mapping](https://github.com/Aussiemon/Vermintide-2-Source-Code/blob/c5e4968b1fbb00c49884e56d640ef990a9c04dd0/scripts/settings/attachment_node_linking.lua#L6477)
and [inventory templates](https://github.com/Aussiemon/Vermintide-2-Source-Code/blob/c5e4968b1fbb00c49884e56d640ef990a9c04dd0/scripts/settings/ai_inventory_templates.lua#L662).
Inventory linking preserves/restores the original local hierarchy during
wield/unwield rather than permanently rewriting the skeleton.

The decoded weapon has two endpoint skin bones (scene nodes 5 and 6), with
fractional endpoint weights in all four skins. Fractionally weighted vertices:
3,321/4,142; 1,487/2,078; 899/1,237; and 307/391. There is one `rp_dropped`
actor, no weapon animation controller, no joint descriptors, and no APEX or
embedded PhysX payload in this unit. This establishes endpoint-driven
deformation. It does **not** establish inertial dangling physics.

### Actual secondary-motion examples and the remaining gap

The extracted Beastmen Gor flail
`units/weapons/enemy/wpn_bm_gor_set_01/wpn_bm_gor_flail_01` has 12 articulated
link bones and a controller containing 1,388 constraint bytes. Its default
`idle_const` state enables constraint index 0; `idle_anim` uses the same rest
animation with no constraints. The player `wpn_emp_flail_01_3p` independently
shows a 10-link chain and the same state distinction, with 1,196 constraint
bytes. This is evidence for native constrained secondary motion, not an
engine limitation.

Gor unit SHA-256:
`100add496290f6065244c0f2e5260aa86a9f6b385ac953fe6e49693a9f602845`.
Gor controller SHA-256:
`d388ee94e41e8450363041ed18aff4bedac088aed3cb20401be655290e874158`.

Our Bitsquid state-machine reader retains those constraint descriptors as
opaque bytes. We lack a verified editable schema, export path, or two-ended
tether configuration. Copying flail bytes would also copy unknown bone
indices, rest geometry and solver parameters from a one-ended chain.
An IK helper alone is not an inertial simulation.

The artist's long launcher hose is unparented and has no vertex groups,
armature modifier, or constraints. The full launcher has 4,916 vertices;
the current rigid export intentionally retains 3,308, excluding 1,608 hose
vertices in 13 disconnected sections. A separate 198-vertex `Tube` object is
a short weapon conduit, not the long backpack tether, and is also unrigged.
Neither should be reintroduced under the rigid rocket/launcher physics root.

Before attempting real hose physics we need:

1. Reviewed backpack/weapon endpoint transforms and local orientations.
2. Hose bones, weights, rest lengths and an explicit treatment of its
   disconnected sections.
3. A verified authorable two-ended solver: decoded/exportable native
   constraints, or a separately validated custom simulation.
4. Defined wield/stow, teleport, death/drop and teardown behavior preserving
   the single dropped-weapon actor and rigidly attached loaded warhead.
5. Compiler inspection plus host/client lifecycle tests.

The installed SDK's historical `vermintide.chm` physics guide describes
PhysX DCC XML exported alongside geometry as `.physx`; current compiler
compatibility is not yet demonstrated. Autodesk's
[APEX workflow](https://help.autodesk.com/cloudhelp/ENU/Stingray-Help/stingray_help/creating_effects/enable_apex_cloth.html)
requires authored `.apx` data and mesh binding. Runtime cloth calls do not
make an arbitrary unrigged mesh into cloth. A bounded search of the extracted
asset tree found no standalone authoring files of those types; that does not
rule out embedded data. Neither alternative was attempted here.

## Measured chimney attachment

The actual smoke outlet is the annular top lip on
`SM_Skaven_WarlockBombardier_Backpack`, not its four taller decorative spikes
or the lower recess. The chimney component spans source vertices 3668–4628.
Its lip has 32 vertices: 16 inner and 16 outer, with mean radii 0.0665114 m
and 0.0784704 m.

In source mesh centimetres its centroid is
`(3.58953065425, 73.37848830228, 198.318695068)`.
The decorative spikes reach 206.511566 cm; the floor is at 192.317599 cm.
Those are deliberately not used as emitter origins.

All 32 lip vertices are weighted **100% to `j_backpack`** in the artist scene,
shipping FBX and compiled skin. Shipping indices equal source indices plus
12,846; FBX correspondence is within 0.93 micrometres. Compiled half-precision
vertices match within 0.323 mm. The fixture retains the exact indices.

Compiled `j_backpack` is scene node 25, under node 24, with a scale-100
wrapper. The profile uses the **compiled skin inverse bind**, not the inverse
of a currently posed bone multiplied by unposed mesh positions.
In column-vector notation:

```text
local_anchor = inverse_bind(j_backpack) * Translation(lip_centroid_metres)
world_anchor = current_world_pose(j_backpack) * local_anchor
```

This is the same equation that moves the rigidly weighted chimney vertices.
The Lua profile's `x_axis`, `y_axis`, `z_axis` arrays are basis columns; their
lengths are 0.01. They cancel the skeleton's scale 100, giving approximately
unit world scale. Normalizing them would make a 100-times-scaled effect.
Multiplying the local translation by 100 would move it far from the opening.
Both mistakes, and a transposed basis, are rejected mutations in the tests.

The effect's local +Z maps to the outlet's outward normal. No model, bone,
skin weight, actor, ragdoll, or weapon attachment was changed.

## Native smoke and ownership contract

Effect: `fx/chr_warp_fire_backpack_smoke_01` (2,840-byte extracted resource).
It contains two continuous billboard clouds; its main velocity cone points
along local +Z. Membership in
`resource_packages/breeds/skaven_warpfire_thrower` was verified in the native
package table (entry 124, byte offset 1988 of the 237-resource package).

The controller uses the native
[ScriptWorld linked-particle helper](https://github.com/Aussiemon/Vermintide-2-Source-Code/blob/c5e4968b1fbb00c49884e56d640ef990a9c04dd0/foundation/scripts/util/script_world.lua#L550).
The [engine API contract](https://help.autodesk.com/cloudhelp/ENU/Stingray-Help/lua_ref/obj_stingray_World.html)
allows a node-relative local pose and a `destroy` orphan policy. That policy
is selected so deletion of the visible outfit also destroys its emitter.

Implementation:

- Load anchor, controller, then hooks. Require the exact custom outfit, live
  owner, real `j_backpack`, and matching active `level_world`. There is no
  root/node-0 fallback and no dedicated server emitter.
- Start after inventory attachment/material setup on each peer. One strong
  owner/outfit record owns one emitter; repeated setup cannot duplicate it.
  The cosmetic effect needs no custom RPC.
- Load the native package synchronously with a dedicated
  `doomrocket_backpack_smoke` reference; never unload another consumer's
  reference. Cache across individual deaths and release only at a safe reset.
- Stop before death handoff and inventory freeze/destroy. Remove ownership
  before native cleanup. Never query a potentially recycled particle ID after
  its linked outfit has died.
- Treat disabled/paused worlds as still alive. Forget handles before
  `Application.release_world`; defer package unloading until that world is no
  longer managed. If a world vanishes without release notification, retain
  the package reference and reject duplicate creation there rather than
  touching an unproven native handle.
- Update catches removed owners/outfits. Runtime reset and Lua reload also
  clear owned records. No particle handle is networked or treated as a unit.

Entry points: `_start_warlock_backpack_smoke`, `_stop_warlock_backpack_smoke`,
`_update_warlock_backpack_smoke`, `_reset_warlock_backpack_smoke`, and
`_release_warlock_smoke_world`. Logs use `[doomrocket:SMOKE] phase=start/stop`.
A start proves a creation call, not correct visible placement. Unknown-world
package retention is an exceptional safety fallback, not a passed leak test.

## Offline validation record

Validated 2026-09-10 at 05:39 UTC from clean source commit
`b7538d42cb647bb198b6e68aa8743c9dd6839c3f`:

- `Invoke-DoomrocketRelease.ps1` without `-Upload` or `-Deploy`: success.
  Clean SDK build, all five verified material splices, **216 Python tests**,
  and the PowerShell ragdoll regression suite passed.
- Includes 14 anchor tests and 29 smoke tests: 21 controller tests, six
  executable shipping-callback tests, and two explicitly structural hook
  ordering checks. The rebuilt package now contains the anchor profile;
  its body payload, inverse bind, rim weights and weapon contracts pass.
- [Source CI run 34441823725](https://github.com/Ensrick/doomrocket-private/actions/runs/34441823725)
  passed for the same commit.
- Five local bundles plus the mod manifest total **95,660,541 bytes**.
  These are unpublished local artifacts, not a Steam content handle.
  Both source worktrees were clean after the build; public was untouched.

| Local artifact | SHA-256 after material splice |
| --- | --- |
| `209fb8c3c0a8c3a4.mod_bundle` | `b242782bc46ea2646616d9d25a51f87701c49b989537b347b6e1b7d0bed801ec` |
| `4e6a9317aab221e1.mod_bundle` | `5c7bf2f4dd484ffa20ea5971068037e1b5db1b5eb25530dfe664209532ff1da8` |
| `ac226cc769a897ae.mod_bundle` | `e3ab07b2fdef0161425a61467b1384efa67ce449324925c75e09311f54b2093b` |
| `e7852992f40eb619.mod_bundle` | `e1a04e500f8255ebedcaffb4e35e829adbd99ebf46c2b8b4cd89d26dca4735e2` |
| `f5283f9585ea8355.mod_bundle` | `a3fa4dbbf3f7000e36c47ebfae5f970b67b998958b8ce3a5faa74463a2835f8f` |
| `doomrocket.mod` | `dbf17c3e8ed109834bbcf56e4bdf7700bff937e6b699fd63d7e11e571f3165d2` |

These passing checks do not cover the known #14 runtime/network crash and
do not establish smoke visibility or native engine safety. No deployment,
Workshop upload, release tag, or GitHub prerelease was made.

## Runtime smoke acceptance

**Not ready on published TEST v0.1.65-dev.** Correct #14 and publish a validated
replacement first. Confirm the actual loaded banner on every peer; do not
assume a source version is available on Steam.

| Check | Required observation |
| --- | --- |
| Placement/scale | Smoke starts inside the tallest chimney rim, goes outward, and has native-scale density; not at the feet, backpack centre or spike tips |
| Motion/persistence | Follows walking, turning, aiming, firing, reloading and shoving without detaching; the native loop persists during a prolonged idle |
| Host/client/hot join | Exactly one plume per living Engineer in both views, including joining an existing game |
| Multiple units/repeated setup | Independent emitters, no doubles or cross-unit cleanup |
| Death and inventory freeze | Emitter ends before corpse/weapon handoff; existing body, warhead and weapon physics remain unchanged |
| Removal/disable/re-enable | Despawn and mod lifecycle remove owned emitters; no stale ID destroys another effect |
| Pause and world transition | No duplicate after resume, no orphan plume or crash on return to Keep/next map |
| Resource lifetime | Native Warpfire enemies still work; repeated spawn/death and map cycles show no unbounded package/emitter accumulation |
| Existing regressions | Retain #7/#8 explosion/removal checks and combat/ragdoll tests; smoke success cannot close those issues |

Capture host/client logs plus a short visible clip of the chimney. Keep #4
open until these observations are supplied. Keep #3 open independently;
smoke implementation is not progress on a physics solver.
