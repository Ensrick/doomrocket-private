# Warlock Bombardier model pipeline

How Crunch's Warlock Engineer model ships as the doomrocket enemy, what broke
along the way, and the invariants that keep it working. Companion tooling:
`tools/splice_warlock_materials.ps1`, `tools/Test-WarlockPipeline.ps1`.

## The proven contract (v0.1.22 baseline, user-confirmed in-game)

1. **Mesh**: 4 meshes joined (`g_body_lod0`, `g_fur_lod0`,
   `SM_Skaven_WarlockBombardier_Armor`, `_Backpack`; 29,123 verts), 5 material
   slots, on the 138-bone `armature object.008` rig. The rig was authored to
   fit the gun rat's existing animation set.
   `g_stormvermin_armor_lod0` is donor-scene scaffolding - never export it.
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
5. **Driving**: root-only link (`AttachmentNodeLinking.doomrocket_warlock_root`)
   + `Unit.set_animation_bone_mode("transform")` + `Unit.set_bones_lod(0)` +
   own state machine enabled + explicit `idle` event. The rat's
   `Unit.animation_event` / `animation_set_variable` /
   `animation_set_constraint_target` calls are mirrored onto the outfit
   (`mod._warlock_outfits`); events the outfit's state machine lacks are
   skipped, so each new clip/state starts working the moment it ships.

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

## Uncatchable crash classes (pcall is useless)

- Boot-flushing a spliced child material (`PatchedResourcePackage::flush`).
- Vanilla state machine / clips evaluated against a mod-compiled skeleton
  (`AnimationBlender` assert, delayed ~1 frame after a successful-looking call).
- `Unit.animation_set_variable` / `animation_set_constraint_target` with an
  index from a DIFFERENT state machine (indices are per-compiled-SM; the
  pcall wrapper around the call catches nothing).
- `Unit.node()` on a missing node (why the old bridge pruned via
  `Unit.has_node`).

## MILESTONE - v0.1.39 USER-CONFIRMED IN-GAME (2026-07-27)

"This seems to work... it works." Crunch's model, gun-rat animation set,
self-animated on its own skeleton, driven by mirrored AI events. The full
recipe: extract compiled clips -> Bitsquid PARSER only -> custom
parent-relative applier (basis = rest_local^-1 @ engine_local) -> strip
scale/helper/weapon-bone curves, keep root_point -> bake to Crunch's rig ->
render-verify -> export via the proven FBX pipeline -> state machine over the
ratling event vocabulary -> event mirror at runtime.

Remaining from that test: no ragdoll on death (shipped v0.1.40, below,
[untested]), and the texture pass (Crunch's full material masters - 4 sets of
BC/NR/MASE/E incl. warpstone emissive - arrived 2026-07-26; current spliced
setup predates them).

## Ragdoll (v0.1.40-dev, [untested]) - authored PhysX scene, no Maya

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
- Ragdoll tuning once v0.1.40 is user-verified: joint limits are first-pass
  guesses; collision filter words are 0 (engine may override via shape
  templates - watch for corpse blocking players or falling through floors).
- Launcher/rocket/tube props still placeholders (exports staged in
  `_warlock_bombardier_art/`).
