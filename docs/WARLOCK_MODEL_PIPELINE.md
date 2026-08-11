# Warlock Bombardier model pipeline

How Crunch's Warlock Engineer model ships as the doomrocket enemy, what broke
along the way, and the invariants that keep it working. Companion tooling:
`tools/splice_warlock_materials.ps1`, `tools/Test-WarlockPipeline.ps1`.
The current native-ragdoll visual-handoff research and its still-untested
candidate are recorded in `docs/research/RAGDOLL_VISUAL_HANDOFF.md`.

## The proven living-visual contract (v0.1.22 baseline, user-confirmed in-game)

1. **Mesh**: 4 meshes joined (`g_body_lod0`, `g_fur_lod0`,
   `SM_Skaven_WarlockBombardier_Armor`, `_Backpack`; 29,123 verts), 5 material
   slots, on the 138-bone `armature object.008` rig. The rig was authored to
   fit the gun rat's existing animation set.
   `g_stormvermin_armor_lod0` is donor-scene scaffolding - never export it.
   The current `warlock_bombardier_3p.bones` contains exactly 138 names. The
   old `units/bombadier/bombadier.bones` contains 139; its only additional name
   is `camera_attach`. This is not evidence of Blender inventing bones.
2. **FBX for the DCC importer** must:
   - come from the `prepare_pusfume_fbx.py` round-trip (weights pruned to 4
     deform influences, renormalized to 1.0);
   - have the mesh object transform APPLIED (donor meshes are cm-space data
     with 0.01 object scale; the armature is meters - Stingray bind matrices
     cannot straddle the two spaces);
   - carry a BAKED animation take (`bake_anim=True`, all bones) - a bind-pose
     FBX compiles without the animated character activation group and renders
     rigid forever.
3. **Unit sources**: same-name `.unit` (own `animation_state_machine` path) +
   `.bones` + `.dcc_asset` + `.state_machine` (bones = own unit path) +
   `anims/*.fbx` clips with `.animation` sidecars (bones = own unit path).
4. **Materials**: the five boot-package `materials/warlock_bombardier/wb_*`
   are SDK compiles and render RIGID and dark - they are placeholders. The
   real bindings are game child-material payloads spliced over
   `child_materials/warlock_bombardier/wb_*_child` in
   `resource_packages/doomrocket/warlock_child.package`, which is absent from
   `doomrocket.mod`'s packages list and loaded at runtime via
   `mod:load_package` after the Globadier donor package is resident.
   `hooks.lua` swaps each slot via `Unit.set_material` per spawn.
5. **Living driving**: root-only link (`AttachmentNodeLinking.doomrocket_warlock_root`)
   + `Unit.set_animation_bone_mode("transform")` + `Unit.set_bones_lod(0)` +
   own state machine enabled + explicit `idle` event. The rat's
   name-based `Unit.animation_event` calls are mirrored onto the outfit
   (`mod._warlock_outfits`); events the outfit's state machine lacks are
   skipped. Raw variable and constraint indices are deliberately **not**
   mirrored because indices are state-machine-local and forwarding them caused
   native animation assertions in earlier builds.
6. **Carrier identity**: the gameplay unit is a native **ratling gunner** clone
   (`Breeds.skaven_doomrocket = table.clone(Breeds.skaven_ratling_gunner)`).
   Its render meshes are hidden while alive, but its native unit, actors,
   animation controller, and ragdoll remain the authoritative gameplay and
   physics carrier. The separate 138-bone Warlock unit is the visible overlay.
   References to a "stormvermin donor" elsewhere in the history describe rig
   ancestry or an abandoned v0.1.31-35 experiment, not the current carrier.

## Ship procedure

`VMBLauncher build` -> `tools/splice_warlock_materials.ps1` ->
`tools/Test-WarlockPipeline.ps1` -> `deploy` -> `upload` -> git commit+push.
NEVER `vmblauncher all` (it would upload the unspliced bundle).

## Failure ledger

| Build | Symptom | Root cause | Rule derived |
|---|---|---|---|
| v0.1.9-13 | Floating armor, no wearer | Name-filtered export dropped 3 of 5 rig meshes; model is self-contained | Export the full rig mesh set |
| v0.1.15 | Vanilla stormvermin armor clipping Crunch's armor | `g_stormvermin_armor_lod0` is donor-scene scenery, wrongly joined in | 4 meshes, never the scaffold |
| <=v0.1.15 | Rigid mesh + uniform darkness | Mod SDK cannot compile the character-skinning shader permutation; static FBX lacked the animated activation group | Splice game child materials; bake a take into the FBX |
| v0.1.16 | CRASH at boot, `PatchedResourcePackage::flush`, first spliced material | Spliced children rode the boot-flushed main package | Spliced children live ONLY in the runtime-loaded child package |
| v0.1.18 | Animated stick figure | (compound; see .19/.20 - and ultimately .21) | - |
| v0.1.19 | Stick figure persists | Weight theory (normalize across non-deform groups) fixed a real defect but was not the operative cause | Animated export starts from the cleaned round-trip FBX regardless |
| v0.1.20 | Stick figure persists | Scale theory (cm mesh / m armature) fixed a real defect but was not the operative cause | transform_apply the mesh before export regardless |
| v0.1.21/22 | CORRECT deformation | Own-ASM driving works | Self-animation is a valid mode |
| v0.1.23 | Stick figure again (bridge retry with bone-mode calls) | ~~"link driving never reaches the skin"~~ STRUCK - disproven by v0.1.28. Retro-diagnosis: unlinked scale bones + possible weight/scale defects of that era's compile | Link driving works; see the v0.1.36 scale-bone finding (docs/research/SCALE_BONES_FINDING.md) |
| v0.1.24 | CRASH ~0.2s after spawn, `AnimationBlender Layer 0 / LayerState 1`, no Lua stack | Vanilla state machine on a mod-compiled skeleton: `Unit.set_animation_state_machine` SUCCEEDS, then the blender asserts on evaluation - pcall cannot catch it | NEVER point a mod skeleton at a vanilla state machine |
| v0.1.25 | CRASH in aim_system update, Lua stack ends in our `animation_set_constraint_target` mirror (index 0, aim-target Vector3) | Raw variable/constraint indices are only meaningful within ONE compiled state machine; forwarding them to a unit on a different SM is an engine assert - the pcall wrapper caught nothing | Mirror animation state by NAME only (events gated on `has_animation_event`); never by raw index |
| v0.1.27 | CRASH at spawn, stack in the event mirror: vanilla `_setup_configuration` fires `anim_state_event "idle"` on the rat, mirror forwards to the outfit | Firing an animation event into a DISABLED state machine is an engine assert; bridge mode disables the outfit ASM but left the mirror registered | Event mirroring exists only for the enabled-own-SM mode; bridge mode never registers the outfit |
| v0.1.28 | Bridge DRIVES the model but limbs stretch compounding with chain depth | Donor was the RATLING body; Crunch's rig is stormvermin-family - differently-proportioned skeleton driving a mismatched bind | The donor's skeleton family must match the rig (stormvermin) |
| v0.1.29 | Same compile invisible under its own idle | Blender re-export of Dalo's armature scale conventions double-converts for self-evaluation (renders ~1/100) | Bridge-driven use only for the Dalo-convention compile |
| v0.1.31 | CRASH: `generic_hit_reaction_extension.lua:218`, nil health_extension on the donor | Breed `hit_zones` name UNIT ACTORS; the ratling clone's zones didn't match the new stormvermin body, health-extension init failed | Body-coupled breed tables (hit_zones, hitbox_ragdoll_translation, ragdoll_actor_thickness) must come from the donor body's breed |
| v0.1.32 | CRASH at spawn in GenericUnitAimExtension init | `Unit.animation_find_constraint_target(unit, "aim_target")` asserts on the stormvermin machine (no aim constraint - stormvermin never aim) | Aim template must not touch constraints unless the machine has them |
| v0.1.33 | Pile of bare idle-posed stormvermin ("million copies") | `hooks.lua:164` called a file-local declared BELOW the hook -> nil global -> every spawn attempt errored, et quarantined the tick, director retried forever | Fully qualify engine calls or declare locals above every use (late-local lint class) |
| v0.1.34 | Raw NATIVE crash (no Error Context, no Lua stack) moments after spawn | Ratling state machine bound to the stormvermin skeleton - clips animate gun bones the skeleton lacks | Cross-skeleton SM binding is fatal in EVERY direction (v0.1.24 mod->vanilla, v0.1.34 vanilla->vanilla). Machines only ever run on the skeleton they were compiled against |
| v0.1.35 | Deformed abomination (stormvermin donor, own SM) | cm-convention compile under bridge driving | (see v0.1.36 close-out) |
| v0.1.36 | STILL deformed with all six scale bones linked + ratling donor | Ran on the cm compile (v0.1.29-proven internally inconsistent); but this completes the matrix: 2 compiles x 2 donors x scale-links on/off - every cell deformed | **BRIDGE LANE CLOSED.** The engine's linked-skinning bind space is not producible from Blender FBX export. Self-anim (v0.1.22, the only user-confirmed-correct config) is the architecture; gun-rat clips arrive via the Bitsquid compiled-animation importer onto OUR skeleton |
| v0.1.40 | Ragdoll deformed terribly, stretched wildly, FPS < 1 | Physics solver explosion. Suspects, in order: scene actors dynamic AT SPAWN fighting the animation (serialized eKINEMATIC possibly not honored on instantiation); near-zero inertia tensors on small bones (tails ~8e-5) destabilizing the joint chain; no joint projection so error compounds unboundedly (giant polygons = fill-rate death) | v0.1.41 counters all three: spawn audit force-kinematics all 29 actors (+ prints [doomrocket:RAGDOLL] found/created), inertia floor 0.01 + heavier extremity masses, D6 ePROJECTION 0.05m/0.5rad, solver 16/4. Await the audit line from the next run |
| v0.1.43 | Kinematic-at-spawn held while alive, but death still corrupted the skeleton with a 1-1.6 s physics stall | The owner's death event was mirrored into the outfit BEFORE the delayed handoff; the outfit's SM ragdoll state flipped its actors dynamic internally, so the custom scene still fought the engine at death | v0.1.44 removes the custom PhysX scene and the SM ragdoll layer entirely - the authored-scene lane is closed for ragdoll |
| v0.1.44 | Native-carrier attempt: linking the 97 target bones independently with World.link_unit recreated the "stick figure" | Per-bone World.link_unit destroys this Blender-built mesh's local scene-graph hierarchy (same class as the closed bridge lane) | Keep the root-only attachment and intact custom hierarchy; never independently re-link its bones. Later builds also proved raw local-pose copying invalid |
| v0.1.45/46 | (design, [untested]) | Death handoff = vanilla-carrier pose copy: `_prepare_warlock_death` runs BEFORE ai_extension:die, removes the mirror entry, disables the outfit ASM, builds owner->outfit node pairs from `AttachmentNodeLinking.doomrocket_warlock_bridge` (skipping root); the death reaction copies each carrier LOCAL pose per frame (`_update_warlock_death_pose`) while the OWNER'S native ratling ragdoll does the physics. Diagnostics: `[doomrocket:RAGDOLL] <src> pre-event local-pose carrier active: nodes=N custom_physics=absent` | This is the runtime analogue of the parent-relative retarget that made v0.1.39's living animations work |
| v0.1.47 (tested) | Ragdoll = giant stretched mess flying skyward, but NO framerate loss (2026-08-04, host + client logs agree; carrier armed cleanly, nodes=96, both peers) | The v0.1.45 raw `Unit.local_pose` copy is the closed v0.1.28 bridge failure resurrected at death: the ratling carrier's local matrices carry ITS bone translations and its animated proportion SCALE (the bridge maps the `*_scale` bones), compounding multiplicatively down every chain on Crunch's hierarchy. No fps loss because no physics is involved - pure render deformation | v0.1.48: ROTATION-ONLY retarget (`Unit.set_local_rotation` per mapped bone - bone lengths/proportions stay at Crunch's bind, stretch impossible by construction), j_hips alone also copies local translation (root-relative, no chain) so the corpse falls; `*_scale` + `aim_target` excluded. Diagnostic line now `rotation carrier active: nodes=N scale/aim_excluded=K` |
| v0.1.48 (tested) | Six clean deaths with Less Corpses absent and corpse limit 70: the visible Warlock outfit vanished, while embedded longbow arrows remained suspended on the native carrier corpse; no FPS or solver failure | Raw native hips local position was copied under the custom scale-100 parent. Compiled-rest composition places the custom hips about 86.899 m from its valid rest position, fully explaining an out-of-view/bounds skin without deletion. ASM disable may also affect the experimental render path, but is not needed for this displacement | Never copy source-local translations across these rigs. Convert calibrated world motion back through the target parent's inverse; test culling separately only if bounded pose telemetry passes |
| v0.1.49 (tested, 2026-08-11) | The corpse looked like a ratling gunner because the build deliberately revealed all 24 native carrier meshes on all 11 deaths. Physics stayed stable, but the Warlock overlay did not follow: `root_delta` stayed 0 while mean/max `hips_delta` grew from 0.04/0.07 m at frame 1 to 1.32/1.683 m at frame 64 | The visible corpse was a fallback underlay, not the Warlock model. The pose driver wrote during entity update, before the same frame's world animation evaluation; the still-enabled outfit ASM in `transform` mode could write the bones afterward. Direct carrier/outfit local transforms are also not interchangeable because the compiled custom rig has a scale-100 wrapper and different rest matrices | Never expose the carrier as a substitute corpse. Drive the custom visual after animation evaluation, block animation bone writes, and convert through calibrated world/rest space. This replacement is a candidate until runtime video **and** post-animation logs pass. Tested ManifestID: `8847975153665526573` |
| v0.1.50 (candidate, uploaded 2026-08-11) | Hidden native ratling remains the sole physics owner; custom outfit captures its final living world/rest calibration in death `pre_start`, switches to bone mode `ignore`, and receives a topology-ordered world-delta/local-parent conversion once per carrier-world animation frame. Five-second per-corpse telemetry now has unique unit/husk IDs | Corrects the v0.1.47 raw full-pose error, v0.1.48 raw hips-local/scale-100 error, v0.1.49 double-writer and ratling-underlay errors, and the first candidate's multi-world callback self-rescheduling hazard. Mutation fixtures use inert `.fixture.txt` suffixes so VMB cannot compile test failures into shipping bundles | Do not call this fixed until `docs/testing/WARLOCK_RAGDOLL_TEST_PROTOCOL.md` passes on host and remote client with both video and analyzer output. Workshop item `3771657344`, upload-confirmed ManifestID `2137195637454965122` |
| v0.1.47 | User report "No ragdoll" (2026-08-03) was a STALE BUILD: the 22:21 session log shows `[doomrocket:LOAD] v0.1.41-dev` + the v0.1.41 spawn-audit line | v0.1.42-46 were deployed locally but NEVER uploaded; the user's Steam restart (pulling an unrelated gt update) re-synced item 3771657344 back to the 07-27 v0.1.41 manifest - the exact clobber class in `feedback_local_deploy_clobbered_must_upload` | v0.1.47-dev republishes the current tree (identical code to v0.1.46 + version/title bump), upload log-confirmed ManifestID 3747860009260434476. NOTE: launcher v0.5.7+ refuses direct `upload` (publication receipt required); the out-of-monorepo doomrocket flow uses the v0.5.6 baseline binary `vmb-launcher-baseline-056-20260726` |

## Uncatchable crash classes (pcall is useless)

- Boot-flushing a spliced child material (`PatchedResourcePackage::flush`).
- Vanilla state machine / clips evaluated against a mod-compiled skeleton
  (`AnimationBlender` assert, delayed ~1 frame after a successful-looking call).
- `Unit.animation_set_variable` / `animation_set_constraint_target` with an
  index from a DIFFERENT state machine (indices are per-compiled-SM; the
  pcall wrapper around the call catches nothing).
- `Unit.node()` on a missing node (why the old bridge pruned via
  `Unit.has_node`).

## Current native-carrier visual handoff (researched; runtime result pending)

The stable physics architecture is now fixed: the hidden native ratling unit
owns the ragdoll, and the custom Warlock unit owns no physics. The remaining
problem is transferring the carrier's final ragdoll pose into a differently
wrapped visual skeleton. Offline parsing of the current compiled resources
found:

- custom: 142 scene nodes, 138 state-machine bones, 1 skin, 0 actors and no
  physics scene;
- native ratling: 235 scene nodes, 106 state-machine bones, 17 skins, 32
  actors and a 125,620-byte native physics scene;
- all 138 custom bone names already exist in the ratling scene graph, so name
  absence and importer-created bones are not the issue;
- the custom unit has three wrapper nodes, then an armature node at index 3
  with world scale `(100, 100, 100)`, then `root_point` at index 4. Native
  `root_point` is top-level index 0 at scale 1. Of 106 common state-machine
  bones, 83 local rest matrices differ and all 106 world rest matrices differ.

The candidate therefore does **not** copy raw source-local matrices. It keeps
the carrier hidden, leaves the outfit ASM enabled but changes its animation
bone mode to `ignore`, schedules the copy with
`AnimationSystem.add_safe_animation_callback()` (after world animation and
before scene update), applies calibrated world-space rotation deltas, and
derives the desired hips local pose through the inverse desired target-parent
world pose. It remains **UNTESTED** until the visible corpse is the Warlock in
runtime footage and post-animation telemetry stays within the documented
limits. See `docs/research/RAGDOLL_VISUAL_HANDOFF.md` for formulas, source
trace, Autodesk references, and acceptance gates.

AnimationSystem's safe-callback queue is global, while ScriptWorld drains it
for every active world. The callback is therefore one-shot and never queues
itself. Hooks on both `World.update_animations` variants enqueue it only after
the carrier's own `Unit.world` animation pass, producing one transfer/sample
per carrier-world frame before that world's scene update.

## MILESTONE - v0.1.39 USER-CONFIRMED IN-GAME (2026-07-27)

"This seems to work... it works." Crunch's model, gun-rat animation set,
self-animated on its own skeleton, driven by mirrored AI events. The full
recipe: extract compiled clips -> Bitsquid PARSER only -> custom
parent-relative applier (basis = rest_local^-1 @ engine_local) -> strip
scale/helper/weapon-bone curves, keep root_point -> bake to Crunch's rig ->
render-verify -> export via the proven FBX pipeline -> state machine over the
ratling event vocabulary -> event mirror at runtime.

Remaining at that milestone: no ragdoll on death (the later v0.1.40 authored
physics lane failed and was removed), and the texture pass (Crunch's full material masters - 4 sets of
BC/NR/MASE/E incl. warpstone emissive - arrived 2026-07-26; current spliced
setup predates them).

## Historical ragdoll experiment (v0.1.40-dev) - authored PhysX scene, no Maya

Vanilla character ragdolls are NOT unit-editor actors: the ratling's 32
ActorResource entries are c_* hit capsules (template keyframed_no_collision);
the ragdoll bodies are j_*-named rigid dynamics inside the unit's
`physics_scene_data` (cooked PhysX 4.1.1 SEBD binary, 125 KB), which the SDK
docs say comes from a Maya-exported PhysX XML renamed `<unit>.physx` next to
the .unit. The SM references those actors by bone name in a `ragdolls` block;
ragdoll states live on their own layer.

What shipped (all offline-verified against the compiled bundle):

1. `warlock_bombardier_3p.physx` - GENERATED RepX XML
   (scratchpad gen_physx.py): 29 kinematic PxRigidDynamic named j_hips ...
   j_backpack (capsules along +X = the Stingray bone axis, radii transferred
   from the ratling's same-suffix hit capsules, lengths from OUR bind pose,
   bind poses in world METERS from the compiled unit's scene graph -
   decompose rotation+translation ONLY, the cm-convention compile bakes
   scale=100 into every node matrix) + 28 PxD6Joints (linear locked,
   twist/swing eLIMITED per joint category, joint X = child bone axis).
   The mod SDK compiler cooks it automatically when the file sits next to
   the .unit (RepXCompiler + core/physx_metadata, PhysX 4.1.1): compiled
   unit gained a 57 KB SEBD physics_scene_data.
2. `.state_machine` additions - SOURCE SYNTAX (discovered empirically, the
   compiler silently ignores wrong keys):
   `ragdolls = { ragdoll = { actors = [ "j_hips" ... ] keyframed = [] } }`
   ("actors" is the dynamic list key - "dynamic" is silently dropped), plus
   a second layer: default `ragdolls/empty` (state_type "empty", transition
   on event "ragdoll") -> `ragdolls/ragdoll` (state_type "ragdoll",
   `ragdoll = "ragdoll"` config ref, no animations). Compiled verification:
   ragdoll config [0] dynamic_actors == the 29 bone hashes; layer 1 has
   EMPTY_STATE + RAGDOLL_STATE(ragdoll=0). Mirrors the vanilla ratling
   layout exactly (its ragdoll layer: reset_scale / ragdoll(cfg 0) /
   ragdoll_torso(cfg 7) / empty).
3. Runtime: no new code - the existing name-gated event mirror already
   forwards the AI's "ragdoll" event; the base layer still plays death_shot
   while the ragdoll layer flips the 29 actors dynamic.

Verification tooling: scratchpad extract_bundle_payload.py (pull any
resource out of a built bundle) + verify_ragdoll_build.py (parse compiled
unit/SM via the Bitsquid tools). Test gate now cross-checks .physx actor
names == SM ragdolls block == .bones entries and joints == actors-1.

## Open work

- **Gun-rat animation set as mod clips** - the blocking asset. The idle
  (`skaven_stormvermin/anims/passive_idle_3.003`) proves the path: a vanilla
  clip imported as a Blender action on this rig compiles and plays perfectly.
  Need the same for the ratling set (locomotion, attack_shoot, wind_up/reload,
  death) via whatever toolchain produced that idle action - ask Crunch.
  Dalokraff's `doomrocket_reload.fbx` is a bundle-recovery artifact (hashed
  bone names, 2-frame take) and is not transferable.
- State machine states named for the ratling event vocabulary
  (`attack_shoot_align`, `attack_shoot_start`, `wind_up_start`,
  `wind_up_loop`, locomotion events) as clips land - mirroring then drives
  them with zero new runtime code.
- Armor/backpack texture mapping partly wrong + map set incomplete (user
  observation, deferred until animations are done): NR/MASE channel packing
  vs VT2 `_nm`/`_s` conventions, wb_skin still on a flat normal. Crunch's
  full masters are in Downloads\zxnu2hjyuovl4rhx.zip (4 sets of BC/NR/MASE/E
  at 2048/1024/512 + warpstone emissive) - NEXT UP.
- **Native-carrier visual handoff**: run the acceptance matrix in
  `docs/research/RAGDOLL_VISUAL_HANDOFF.md`. The offset-corrected,
  post-animation candidate is not a fix until both runtime visuals and its
  post-animation telemetry pass; do not reveal the native ratling meshes as a
  fallback.
- Launcher/rocket/tube props still placeholders (exports staged in
  `_warlock_bombardier_art/`).
