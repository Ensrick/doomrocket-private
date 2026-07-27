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
| v0.1.21/22 | CORRECT deformation | Own-ASM driving works; per-bone link driving was the actual stick-figure cause | A DCC-compiled unit's skin follows only its own animation system |
| v0.1.23 | Stick figure again (bridge retry with bone-mode calls) | Confirms: scene-graph link driving never reaches the skin, with or without "transform" bone mode | Per-bone bridges are game-compiled-unit territory (plague monk) |
| v0.1.24 | CRASH ~0.2s after spawn, `AnimationBlender Layer 0 / LayerState 1`, no Lua stack | Vanilla state machine on a mod-compiled skeleton: `Unit.set_animation_state_machine` SUCCEEDS, then the blender asserts on evaluation - pcall cannot catch it | NEVER point a mod skeleton at a vanilla state machine |
| v0.1.25 | CRASH in aim_system update, Lua stack ends in our `animation_set_constraint_target` mirror (index 0, aim-target Vector3) | Raw variable/constraint indices are only meaningful within ONE compiled state machine; forwarding them to a unit on a different SM is an engine assert - the pcall wrapper caught nothing | Mirror animation state by NAME only (events gated on `has_animation_event`); never by raw index |
| v0.1.27 | CRASH at spawn, stack in the event mirror: vanilla `_setup_configuration` fires `anim_state_event "idle"` on the rat, mirror forwards to the outfit | Firing an animation event into a DISABLED state machine is an engine assert; bridge mode disables the outfit ASM but left the mirror registered | Event mirroring exists only for the enabled-own-SM mode; bridge mode never registers the outfit |
| v0.1.28 | Bridge DRIVES the model but limbs stretch compounding with chain depth | Donor was the RATLING body; Crunch's rig is stormvermin-family - differently-proportioned skeleton driving a mismatched bind | The donor's skeleton family must match the rig (stormvermin) |
| v0.1.29 | Same compile invisible under its own idle | Blender re-export of Dalo's armature scale conventions double-converts for self-evaluation (renders ~1/100) | Bridge-driven use only for the Dalo-convention compile |
| v0.1.31 | CRASH: `generic_hit_reaction_extension.lua:218`, nil health_extension on the donor | Breed `hit_zones` name UNIT ACTORS; the ratling clone's zones didn't match the new stormvermin body, health-extension init failed | Body-coupled breed tables (hit_zones, hitbox_ragdoll_translation, ragdoll_actor_thickness) must come from the donor body's breed |

## Uncatchable crash classes (pcall is useless)

- Boot-flushing a spliced child material (`PatchedResourcePackage::flush`).
- Vanilla state machine / clips evaluated against a mod-compiled skeleton
  (`AnimationBlender` assert, delayed ~1 frame after a successful-looking call).
- `Unit.animation_set_variable` / `animation_set_constraint_target` with an
  index from a DIFFERENT state machine (indices are per-compiled-SM; the
  pcall wrapper around the call catches nothing).
- `Unit.node()` on a missing node (why the old bridge pruned via
  `Unit.has_node`).

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
  vs VT2 `_nm`/`_s` conventions, wb_skin still on a flat normal.
- Launcher/rocket/tube props still placeholders (exports staged in
  `_warlock_bombardier_art/`).
