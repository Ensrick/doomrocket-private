# Warlock visual handoff onto the native ratling ragdoll

Status: **offline research confirmed; offset-corrected runtime candidate
untested as of 2026-08-11**.

This note separates three things that previous builds conflated:

1. the native unit that owns gameplay and ragdoll physics;
2. the custom skinned unit that must remain visibly Warlock-shaped; and
3. the coordinate- and frame-order conversion that makes the visual follow the
   native corpse.

Passing physics while drawing a ratling corpse is not acceptance.

## Confirmed unit roles

The current carrier is a native **ratling gunner**, not a stormvermin:

- `scripts/mods/doomrocket/breeds/skaven_doomrocket.lua:36-65` clones
  `Breeds.skaven_ratling_gunner` and preserves its native unit template.
- The carrier's meshes are hidden while alive, but the unit keeps its native
  animation, hit actors, and ragdoll. The 138-bone Warlock unit is a separate
  `ai_outfit_unit` visual attached root-only.
- VT2 deliberately keeps `ai_outfit_unit`, `ai_skin_unit`, and helmet units
  attached instead of dropping them on death
  (`Vermintide-2-Source-Code/scripts/entity_system/systems/ai/ai_inventory_extension.lua:378-427`).
- Autodesk's Actor API exposes the scene-graph node in, and the `Unit` that
  owns, each actor. The recovered unit resource likewise stores actors and
  physics-scene data inside the unit. There is no documented runtime operation
  that transfers a ragdoll's actors to another unit. The supported design is a
  native physics owner plus a following visual, not an actor transplant.

Autodesk documents repeated `World.link_unit()` calls as the supported way to
attach clothing to multiple skin bones, but every call resets that child
node's local position, rotation, and scale to the parent node. `unlink_unit()`
does not restore the child's previous internal parent. VT2 therefore snapshots
each linked node's parent and local pose before linking and restores both on
unlink (`Vermintide-2-Source-Code/scripts/entity_system/systems/ai/ai_inventory_extension.lua:5-45`).
The complete internally parented Warlock armature is not a native link-authored
outfit; its v0.1.44 stick figure is consistent with replacing those internal
relationships one bone at a time. The current lane remains root-only.

Official references:

- [Actor Lua API](https://help.autodesk.com/cloudhelp/2021/CHS/Max-Interactive-Help/lua_ref/obj_stingray_Actor.html)
- [Create and control a ragdoll](https://help.autodesk.com/cloudhelp/2021/ENU/Max-Interactive-Help/interactive_help/creating_gameplay/physics/create_import_ragdoll.html)
- [`World.link_unit`, `unlink_unit`, and `update_unit`](https://help.autodesk.com/cloudhelp/2019/ENU/Max-Interactive-Help/lua_ref/obj_stingray_World.html)

## Compiled artifact comparison

The comparison used the current built custom resource
`.build/ragdoll-analysis/custom/C58A3743D12FF52F.unit`, the extracted native
ratling resource at
`../_warlock_bombardier_art/vt2_extract_tree/units/beings/enemies/skaven_ratlinggunner/chr_skaven_ratlinggunner.unit`,
and the Bitsquid parser loaded by
`../vt2-pusfume/.build/compare_compiled_hierarchy.py`.

| Property | Custom Warlock visual | Native ratling carrier |
|---|---:|---:|
| Scene nodes | 142 | 235 |
| State-machine `.bones` | 138 | 106 |
| Skins | 1 | 17 |
| Unit actors | 0 | 32 |
| Physics-scene payload | 0 | 125,620 bytes |
| `root_point` | index 4, below wrappers | index 0, top-level |

All 138 custom `.bones` names already exist somewhere in the native ratling
scene graph. The custom visual therefore does not have unexplained
Bitsquid-created bones. The apparent 32-name difference over the ratling's 106
state-machine bones consists of the six intentional `*_scale` bones plus
native accessory/helper nodes. A `.bones` resource is only the subset selected
for a state machine; it is not the full scene graph
(`../_bitsquid_blender_tools/bitsquid/bones/import_compiled.py:12-18`).

The important incompatibility is rest space:

- custom scene nodes 0-2 are wrappers;
- its armature node is index 3 with world scale `(100, 100, 100)`;
- the current custom FBX has a 138-bone `armature object.008` and mesh object
  scale `0.01`;
- native `root_point` has scale 1 and no parent;
- custom `j_hips` local position is about
  `(-0.001730, 0.007580, 0.000036)`, while native `j_hips` local position is
  about `(-0.851529, -0.176265, 0)`;
- of 106 common state-machine bones, 83 local rest matrices differ and all 106
  world rest matrices differ.

Name equality is therefore necessary but insufficient. Raw source-local pose,
position, or scale copying crosses incompatible spaces.

This is also a quantitative explanation for v0.1.48, not just a qualitative
warning. The compiled custom `j_hips` rest position is approximately
`(-0.001730, 0.007580, 0.000036)` beneath the scale-100 parent. Copying the
native local hips position `(-0.851529, -0.176265, 0)` into that slot composes
to approximately `(-85.1532, -17.6268, -0.0003)` in world space: about
86.899 m away from the valid custom rest hips. That is sufficient to move the
skin out of view/bounds while arrows remain on the native carrier; deletion or
Less Corpses is not needed to explain the observation.

## What v0.1.49 proved

The `console-2026-08-11-18.18.25-aaa52359-6b5c-47f3-92da-ecff08edc1d8.log`
session loaded `v0.1.49-dev` and recorded 11 deaths:

- the build deliberately emitted `donor fallback visibility=true
  meshes=24/24 reason=death-underlay` on all 11 deaths;
- the visible ratling corpse was therefore the revealed native carrier, not a
  successful custom-model ragdoll;
- no solver explosion, sustained FPS collapse, or pose-driver lifetime stop
  was reported;
- `root_delta` stayed exactly 0, confirming only the existing root link;
- hips divergence was systematic:

| Checkpoint | Mean `hips_delta` | Maximum `hips_delta` |
|---:|---:|---:|
| frame 1 | 0.04 m | 0.07 m |
| frame 16 | 0.12 m | 0.19 m |
| frame 32 | 0.52 m | 0.71 m |
| frame 64 | 1.32 m | 1.683 m |

The old 5 m escape alarm was too permissive to detect this repeatable failure.
This build is a **physics pass / visual identity and pose fail**.

## Why the old telemetry observed the wrong phase

The old driver ran from the death reaction's entity update
(`scripts/mods/doomrocket/extensions/death_reactions.lua:658-660` and
`:686-688`). VT2 then performs the following order:

1. `StateIngame` runs entity systems
   (`Vermintide-2-Source-Code/scripts/game_state/state_ingame.lua:974-978`).
2. Boot subsequently calls `Managers.world:update`
   (`Vermintide-2-Source-Code/scripts/boot.lua:786-789`).
3. `ScriptWorld.update` evaluates world animations, runs safe animation
   callbacks, and then updates the scene
   (`Vermintide-2-Source-Code/foundation/scripts/util/script_world.lua:316-334`).

The outfit ASM was still enabled in animation bone mode `transform`.
Autodesk defines that mode as applying animation position, rotation, and scale
to bone nodes. The manual writes and their samples therefore occurred before a
later same-frame animation writer could replace them. Autodesk also states
that skinning and animation have no direct connection and that a skinned object
can exist without animation. Keeping the ASM active is not, by itself, proof
that a skin or its bounds will update.

Relevant primary documentation:

- [`Unit.set_animation_bone_mode`, state-machine enable/disable, bone LOD, and local transforms](https://help.autodesk.com/cloudhelp/2019/ENU/Max-Interactive-Help/lua_ref/obj_stingray_Unit.html)
- [Basic animation concepts: animation and skinning are independent](https://help.autodesk.com/cloudhelp/2019/ENU/Max-Interactive-Help/interactive_help/animation/basic_anim_concepts.html)

The native extensible place for this experiment is
`AnimationSystem.add_safe_animation_callback()`
(`Vermintide-2-Source-Code/scripts/entity_system/systems/animation/animation_system.lua:487-503`),
which `ScriptWorld` runs after animation evaluation and before scene update.
The callback queue is global, however, while `WorldManager` updates every
active world. A callback must not enqueue its successor from inside itself: it
could be drained again by another world in the same rendered frame. The
candidate instead hooks both `World.update_animations` variants, checks that
the updated world is exactly `Unit.world(carrier)`, and then enqueues one
one-shot callback for that owner's immediately following safe-callback phase.

## Offset-corrected post-animation candidate — UNTESTED

The candidate must keep these controls fixed:

- native ratling physics only; custom unit has no actors or physics scene;
- root-only inter-unit link; no per-bone `World.link_unit` calls;
- native carrier meshes remain hidden through death;
- outfit ASM remains enabled to hold that v0.1.49 variable constant, while
  `Unit.set_animation_bone_mode(outfit, "ignore")` prevents it from writing
  bone nodes. This is an experimental control, not a claim that the ASM is
  required for skin rendering;
- all pose application and diagnostic sampling occur in a safe animation
  callback, after the carrier's specific world animation evaluation; the
  callback never self-reschedules;
- no raw source `local_pose`, local scale, or local position is copied into the
  custom hierarchy.

The conversion calibrates each common source/target pair in world space. With
VT2's row-vector multiplication convention, let `S0` be the rigid source world
pose at calibration, `St` the current rigid source world pose, `T0` the target
world pose at calibration, and `PdesiredW` the target parent's desired world
pose:

    D = inverse(rigid(S0)) * rigid(St)
    TdesiredW = T0 * D
    Ldesired = TdesiredW * inverse(PdesiredW)

The row-vector convention is demonstrated by
`Vermintide-2-Source-Code/scripts/flow/flow_callbacks.lua:827-830`; VT2's own
world-to-local conversion is at
`scripts/unit_extensions/generic/tentacle_spline_extension.lua:1049-1053`.

`rigid()` removes source scale. The implementation stores `S0` and `T0` in
`Matrix4x4Box` values rather than retaining temporary engine matrices. For
child bones, it preserves the calibrated custom local translation and scale
and applies only the rotation derived from `Ldesired`. The hips position is
derived through the inverse desired target-parent world pose, so the inverse
parent cancels the custom scale-100 wrapper. No target scale is written;
ordinary child bones remain rotation-only.

The existing bridge array is not parent-first: for example, arm scale entries
precede their arm parents and tail scale precedes appended tail nodes
(`scripts/mods/doomrocket/breeds/skaven_doomrocket_inventory.lua:37-45` and
`:83-154`). An implementation must topologically order mapped nodes or compute
all desired parent world poses independently. Array order is not a hierarchy.

This is an engineering candidate, not a result. Do not describe it as fixed or
deploy it as accepted until the gates below pass.

## Runtime acceptance gates

Use a fresh game restart and a build banner that identifies the candidate.
Accept only when both runtime visuals and post-animation logs agree:

- at least 10 valid non-gibbing deaths, including single deaths, multiple rapid
  deaths, and sloped/stair geometry;
- every visible corpse retains the Warlock body, armor, and backpack; a ratling
  corpse is an automatic failure even if physics is stable;
- carrier mesh visibility remains false and the custom outfit remains alive
  and visible;
- telemetry includes a unique driver id and `unit`/`husk` source so concurrent
  corpses cannot be mixed;
- post-animation samples at 0, 100, 250, 500, 1000, 2000, and 5000 ms remain
  finite and monotonically attributable to the same corpse id;
- hips drift from its calibrated beginning remains at or below 0.25 m and does
  not trend upward across checkpoints;
- no driver stops while both units are alive;
- no stick figure, extreme scale, roof launch, unrelated-physics corruption,
  or sustained FPS collapse;
- ordinary corpse cleanup still occurs.

Video confirms visual identity and pose. Logs confirm writer timing, unit
lifetime, visibility, and bounded error. Neither evidence class substitutes
for the other.

## Secondary culling experiment

The custom unit currently uses `culling = "bounding_volume"`
(`units/warlock_bombardier/warlock_bombardier_3p.unit:9-18`). Autodesk documents
mesh-bounds culling and a disabled mode in the
[Unit Editor](https://help.autodesk.com/cloudhelp/2021/ENU/Max-Interactive-Help/interactive_help/getting_started/common_windows/unit_editor.html).
The recovered compiled mesh resource contains an authored bounding volume.

No source proves that the outfit ASM updates that bound, or that culling caused
the v0.1.48 disappearance. If the post-animation candidate produces bounded,
correct pose telemetry but remains visually absent, make a separate build that
changes only culling. Do not mix that A/B test with pose, physics, material, or
visibility changes.
