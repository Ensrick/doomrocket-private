# The scale-bone finding (v0.1.36)

Two independent research tracks converged on one mechanism for every
"stretched abomination" build (v0.1.28, v0.1.35) and the user's own Blender
observation (recovered ratling looks CRUSHED, Crunch's model looked STRETCHED
in-game - the same factor applied in opposite directions).

## Mechanism

Stingray has NO scale compensation. The SDK documentation set contains zero
hits for segment-scale-compensate or inherit-scale. The scene graph is
`world = parent_world * local` with scale propagating multiplicatively.

Maya joints default to segmentScaleCompensate (children cancel parent scale);
Blender bones have per-bone Inherit Scale. Neither concept survives export.

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
  theory was WRONG; the proportion difference between rat breeds lives in the
  scale bones themselves, so a scale-linked bridge makes the RATLING a valid
  donor - which restores the gun rat's full animation set, native behavior,
  and aim constraint with zero state-machine swaps.
- The v0.1.23 ledger line "scene-graph link driving never reaches the skin"
  was FALSE (v0.1.28 visibly disproved it) and is struck.
- `Unit.set_animation_bone_mode` exists but is undocumented and unused by
  vanilla (~4,462 bone links in vanilla never touch it); vanilla skinned
  overlays simply have no animation extension at all.

## Linking contract (SDK World.link_unit, verbatim highlights)

- "After this call, the child object will slave after the parent object."
- Linking "automatically resets the local transform of the child node."
- Multi-node linking is the documented mechanism "to link up a piece of
  clothing to multiple skin bones."
- A unit can only link to ONE parent unit; unlink does NOT restore prior
  scene-graph parents (vanilla snapshots them first - our
  store_scene_graph_data path).

Full agent reports: see the session record; key paths -
attachment_node_linking.lua (vanilla link tables incl. 75 _scale entries),
attachment_utils.lua:66-79 (link loop), ai_inventory_extension.lua:26-46.
