# The scale-bone finding (v0.1.36)

Two independent research tracks converged on one mechanism for every
"stretched abomination" build (v0.1.28, v0.1.35) and the user's own Blender
observation (recovered ratling looks CRUSHED, Crunch's model looked STRETCHED
in-game - the same factor applied in opposite directions).

## Historical mechanism

No segment-scale-compensation or inherit-scale field was found in the Stingray
SDK documentation or recovered scene-graph resource. VT2's row-vector Lua
usage composes `world = local * parent_world`
(`../Vermintide-2-Source-Code/scripts/flow/flow_callbacks.lua:827-830`) and
derives `local = world * inverse(parent_world)`
(`../Vermintide-2-Source-Code/scripts/unit_extensions/generic/tentacle_spline_extension.lua:1049-1053`).
The observed failures are consistent with parent scale propagating through
that composition.

Maya joints default to
[Segment Scale Compensate](https://help.autodesk.com/cloudhelp/2025/ENU/Maya-CharacterAnimation/files/GUID-8CE29E9D-F1C5-42A3-A657-33E32887380A.htm),
and Blender exposes per-bone
[Inherit Scale modes](https://docs.blender.org/manual/en/latest/animation/armatures/bones/properties/relations.html).
No corresponding compensation field was found in the parsed Stingray scene
graph; the custom wrapper and rest transforms described below are what the
compiled engine resource actually contains.

Fatshark's answer: dedicated `j_*_scale` bones at the top of every limb/spine
chain, explicitly ANIMATED (this is how one skaven rest skeleton serves clan
rat, stormvermin, and ratling proportions) and explicitly LINKED on outfit
overlays. The vanilla skaven body-outfit table `ai_outfit_body_scale_w_tail`
(scripts/settings/attachment_node_linking.lua) links exactly six:

    j_leftarm_scale, j_leftupleg_scale, j_rightarm_scale,
    j_rightupleg_scale, j_spine_scale, j_tail1_scale

The warlock rig has exactly those six. Dalo's `doomrocket_armor` bridge
commented out three of them and never listed the other three, so the bridge
drove every ORDINARY bone from the donor while the six scale bones held their
spawn-time pose - every vertex below a scale bone diverges, compounding with
chain depth. That is the stretch.

## Consequences

- The v0.1.28 -> v0.1.31 "ratling proportions vs stormvermin proportions"
  theory was incomplete. The proportion difference between rat breeds uses
  the scale bones, so a ratling is the correct native gameplay and ragdoll
  carrier. This did **not** prove that raw local transforms from the native
  ratling and the separately compiled, wrapped Warlock rig share one rest
  space.
- The v0.1.23 ledger line "scene-graph link driving never reaches the skin"
  was FALSE (v0.1.28 visibly disproved it) and is struck.
- `Unit.set_animation_bone_mode` is documented by Autodesk. `transform` (the
  default) transfers animation position, rotation, and scale to bone nodes;
  `ignore` prevents animation from affecting bone nodes. No calls were found
  among the recovered VT2 Lua outfit links, but that source search is not an
  API limitation. See the official [Unit Lua API](https://help.autodesk.com/cloudhelp/2019/ENU/Max-Interactive-Help/lua_ref/obj_stingray_Unit.html).

## Linking contract (SDK World.link_unit, verbatim highlights)

- "After this call, the child object will slave after the parent object."
- Linking "automatically resets the local transform of the child node."
- Multi-node linking is the documented mechanism "to link up a piece of
  clothing to multiple skin bones."
- A unit can only link to ONE parent unit; unlink does NOT restore prior
  scene-graph parents (vanilla snapshots them first - our
  store_scene_graph_data path).

Official reference: [World Lua API](https://help.autodesk.com/cloudhelp/2019/ENU/Max-Interactive-Help/lua_ref/obj_stingray_World.html).

## 2026 compiled bone audit: no importer-created extra bones

The current source lists and compiled artifacts reject the hypothesis that the
Bitsquid Blender tools invented extra Warlock bones:

- `units/warlock_bombardier/warlock_bombardier_3p.bones` declares 138 bones
  (`lod_levels[0] = 138`). `units/bombadier/bombadier.bones` declares 139; the
  only additional name in that older list is `camera_attach`.
- The current compiled custom unit
  `.build/ragdoll-analysis/custom/C58A3743D12FF52F.unit` contains 142 scene
  nodes, but its `.bones` resource contains 138 state-machine bones. Scene
  nodes and state-machine bones are not synonymous: the recovered parser says
  explicitly that `.bones` contains only bones selected for the state machine
  and a mesh may use more (`../_bitsquid_blender_tools/bitsquid/bones/import_compiled.py:12-18`).
- The importer validates `.bones` names against already-existing unit scene
  nodes (`../_bitsquid_blender_tools/bitsquid/unit/shared.py:61-105`), selects
  those nodes (`shared.py:109-157`), and creates one Blender edit bone for each
  selected joint index (`shared.py:275-285`). It does not synthesize scene
  nodes. The Pusfume FBX preparation also exports with
  `add_leaf_bones=False` (`../vt2-pusfume/tools/prepare_pusfume_fbx.py:95-107`).
- All 138 custom bone names already exist in the extracted native ratling
  scene graph. The 32 names beyond the ratling's 106 state-machine `.bones`
  are six intentional `*_scale` bones plus native accessory/helper nodes, not
  Blender additions.

This audit does not claim that every weight, inverse bind matrix, or non-bone
scene node is correct. It establishes only that an unexplained extra-bone count
is not the current failure.

## Wrapper scale and rest-space mismatch

Read-only parsing of the current compiled custom unit and the extracted native
ratling unit found structurally compatible names but incompatible coordinate
spaces:

- custom: three wrapper nodes; armature at scene-node index 3 with world scale
  `(100, 100, 100)`; `root_point` at index 4 under that wrapper;
- ratling: `root_point` is top-level index 0 with scale 1;
- custom `j_hips` local position is approximately
  `(-0.001730, 0.007580, 0.000036)` under the scale-100 wrapper, while native
  `j_hips` local position is approximately `(-0.851529, -0.176265, 0)`;
- among 106 common state-machine bones, 83 local rest matrices differ and all
  106 world rest matrices differ.

Consequently, a same-name match does not authorize raw `Unit.local_pose`,
local position, or local scale copying. The v0.1.47 giant stretch was the
runtime manifestation of that mistake. Rotation-only copying removed the most
dangerous scale/translation compounding, but it did not solve animation write
order or the wrapper-relative hips conversion.

The current **untested** candidate instead calibrates source and target world
poses at handoff. In VT2's row-vector convention, for source calibration `S0`,
current source `St`, target calibration `T0`, and desired target parent world
pose `PdesiredW`:

    D = inverse(rigid(S0)) * rigid(St)
    TdesiredW = T0 * D
    Ldesired = TdesiredW * inverse(PdesiredW)

`rigid()` removes source scale. Child bones retain their calibrated target
local translation and scale and take only the rotation from `Ldesired`; the
hips receives the required position derived through its target parent's world
inverse. The current bridge list is not parent-first, so any implementation
that depends on desired parent poses must topologically order the nodes or
look up the separately computed desired parent world pose. This candidate is
not a proven fix until runtime visual and post-animation log acceptance pass.

Full agent reports: see the session record; key paths -
attachment_node_linking.lua (vanilla link tables incl. 75 _scale entries),
attachment_utils.lua:66-79 (link loop), ai_inventory_extension.lua:26-46.
