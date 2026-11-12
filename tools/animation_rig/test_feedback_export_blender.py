"""Exercise the feedback controls through the existing verified FBX boundary.

Blender 5.2 --background --factory-startup --disable-autoexec --python-exit-code 1
  --python test_feedback_export_blender.py -- --rig candidate.blend
  --output-dir <owned diagnostic directory>

Makes a separate 65-frame diagnostic, never a production clip.  Every original
action and the input blend remain untouched.  The exported track inventory is
the existing GAME skeleton; prop widgets and their preview meshes stay out.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_animation
import weapon_controls


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def action_payload(action):
    """All key/handle/sample data, not just a count or an action name."""
    return [[layer.name, [[strip.type, [
        [bag.slot_handle, [[curve.data_path, curve.array_index,
            curve.extrapolation, [
                [list(key.co), list(key.handle_left), list(key.handle_right),
                 key.handle_left_type, key.handle_right_type, key.interpolation,
                 key.easing, key.amplitude, key.back, key.period]
                for key in curve.keyframe_points],
            [list(point.co) for point in curve.sampled_points]]
            for curve in bag.fcurves]]
        for bag in getattr(strip, "channelbags", ())]] for strip in layer.strips]]
        for layer in action.layers]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main(args):
    source = args.rig.resolve()
    source_sha = digest(source)
    output = args.output_dir.resolve()
    require(not any(part.casefold() == "units" for part in output.parts),
            "Diagnostics must stay outside production units")
    output.mkdir(parents=True, exist_ok=True)
    diagnostic = output / "WarlockEngineer_Feedback_Diagnostic.blend"
    clip = output / "warlock_feedback_diagnostic.fbx"
    require(source != diagnostic, "Diagnostic cannot overwrite the source")
    (output / "feedback_export_report.json").write_text(json.dumps({
        "schema": 1, "status": "started-not-validated", "source_rig": str(source),
        "source_sha256": source_sha}) + "\n", encoding="utf-8")
    bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
    rig = bpy.data.objects["WARLOCK_CTRL"]
    game = bpy.data.objects["WARLOCK_GAME"]
    manifest = json.loads(rig["warlock_control_manifest"])
    defaults = json.loads(rig["warlock_control_defaults"])
    controls = sorted({name for group in manifest["groups"].values() for name in group})
    required = {"CTRL-weapon", "CTRL-rocket", "ORG-j_leftshoulder",
                "ORG-j_rightshoulder", "ORG-j_lefteyebrow3",
                "ORG-j_righteyelidbottom"}
    require(required <= set(controls), "Feedback controls missing: " + str(required - set(controls)))
    original_actions = {action.name: action_payload(action) for action in bpy.data.actions}
    skeleton = [(bone.name, bone.parent.name if bone.parent else None,
                 [list(row) for row in bone.matrix_local]) for bone in game.data.bones]
    require(len(skeleton) == 138, "Expected the existing 138 GAME bones")
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    require(not rig.animation_data.nla_tracks,
            "Use the fresh handoff candidate; do not flatten an artist's existing NLA")
    action = bpy.data.actions.new("WARLOCK_FEEDBACK_DIAGNOSTIC_ONLY")
    rig.animation_data.action = action
    scene = bpy.context.scene
    scene.render.fps = 60
    scene.frame_start, scene.frame_end = 1, 65

    def update():
        rig.update_tag()
        bpy.context.view_layer.update()

    def reset():
        for name in controls:
            bone = rig.pose.bones[name]
            bone.matrix_basis = Matrix.Identity(4)
            for prop, value in defaults.get(name, {}).items():
                bone[prop] = value
        update()

    def rotate(name, axis, value):
        bone = rig.pose.bones[name]
        # Preserve the control's established rotation representation.
        if bone.rotation_mode == "QUATERNION":
            from mathutils import Quaternion
            vector = Vector((0., 0., 0.))
            vector[axis] = 1
            bone.rotation_quaternion = Quaternion(vector, value)
        else:
            bone.rotation_euler[axis] = value

    def prop(name, key, value):
        rig.pose.bones[name][key] = value

    def key_all(frame):
        for name in controls:
            bone = rig.pose.bones[name]
            for path in ("location", "scale", "rotation_quaternion"
                         if bone.rotation_mode == "QUATERNION" else "rotation_euler"):
                bone.keyframe_insert(path, frame=frame, group=name)
            for key in bone.keys():
                if not key.startswith("_") and isinstance(bone[key], (int, float, bool)):
                    bone.keyframe_insert("[" + json.dumps(key) + "]", frame=frame, group=name)

    poses = []
    for frame in range(1, 66, 8):
        scene.frame_set(frame)
        reset()
        label = "neutral"
        if frame == 9:
            label = "anatomical fingers"
            for side in ("left", "right"):
                prop("CTRL-hand-settings-" + side, "curl", .65)
                prop("CTRL-hand-settings-" + side, "spread", .4)
            rotate("ORG-j_lefthandindex2", 1, .1)
        elif frame == 17:
            label = "shoulders and full existing face"
            rotate("ORG-j_leftshoulder", 0, .12)
            rotate("ORG-j_rightshoulder", 0, -.10)
            for name in controls:
                if any(part in name for part in ("eyebrow", "eyelid", "ear", "nose", "jaw")):
                    rotate(name, 2, .10 if "jaw" in name else .04)
        elif frame == 25:
            label = "outfit backpack and anatomical scale"
            rig.pose.bones["ORG-j_backpack"].location.x = .012
            for name in manifest["groups"].get("Belt corrections", []):
                rig.pose.bones[name].location.x = .008
            for name in manifest["groups"].get("Cloth", []):
                rig.pose.bones[name].location.y = .008
            prop("CTRL-shape-j_spine_scale", "length", 1.08)
            prop("CTRL-shape-j_spine_scale", "volume", .7)
        elif frame == 33:
            label = "automatic and corrective twist"
            for side in ("left", "right"):
                prop("j_" + side + "arm_ctrl_parent", "IK_FK", 1.)
                rotate("j_" + side + "hand_ctrl_fk", 1, .35)
                rotate("CTRL-forearm-twist-" + side, 1, .10)
        elif frame == 41:
            label = "independent launcher and rocket"
            weapon_controls.switch_follow(rig, "weapon_follow", False)
            rig.pose.bones["CTRL-weapon"].location.x += .02
            rotate("CTRL-weapon", 2, .12)
            weapon_controls.switch_follow(rig, "rocket_follow", False)
            rig.pose.bones["CTRL-rocket"].location.z += .03
            rotate("CTRL-rocket", 0, .18)
        elif frame == 49:
            label = "right hand follows launcher"
            prop("j_rightarm_ctrl_parent", "IK_FK", 0.)
            update()
            weapon_controls.switch_follow(rig, "right_hand_follow", True)
            rig.pose.bones["CTRL-weapon"].location.x += .015
        elif frame == 57:
            label = "direct custom segment and face pose"
            rotate("ORG-j_lefthandmiddle2", 2, .18)
            rotate("ORG-j_righthandindex2", 1, .14)
            rotate("ORG-j_lefteyebrow2", 0, .08)
            rotate("ORG-j_righteyelidbottom", 2, .05)
        update()
        key_all(frame)
        evaluated = game.evaluated_get(bpy.context.evaluated_depsgraph_get())
        poses.append({"frame": frame, "label": label, "game_heads": {
            bone.name: list((evaluated.matrix_world @ bone.matrix).translation)
            for bone in evaluated.pose.bones}})
    for layer in action.layers:
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", ()):
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = "LINEAR"
    scene.frame_set(1)
    update()
    for frame in range(1, 66):
        scene.frame_set(frame)
        update()
        evaluated = game.evaluated_get(bpy.context.evaluated_depsgraph_get())
        require(all(math.isfinite(float(value)) for bone in evaluated.pose.bones
                    for row in bone.matrix for value in row), "Nonfinite GAME pose")
    require(all(name in bpy.data.actions and action_payload(bpy.data.actions[name]) == payload
                for name, payload in original_actions.items()), "An existing action changed")
    require(skeleton == [(bone.name, bone.parent.name if bone.parent else None,
                           [list(row) for row in bone.matrix_local])
                          for bone in game.data.bones], "GAME rest/hierarchy changed")
    scene.frame_set(1)
    update()
    evaluated = game.evaluated_get(bpy.context.evaluated_depsgraph_get())
    capability_sample = [{"frame": 1, "bones": {
        bone.name: (evaluated.matrix_world @ bone.matrix).copy() for bone in evaluated.pose.bones}}]
    capability = export_animation.authoring_capabilities(scene, game, capability_sample)
    require(capability and capability["weapon_control_policy"] == "independent-props-v1",
            "New prop controls lack verified exported GAME mappings")
    rejected = []
    for channel in export_animation.INDEPENDENT_PROP_BINDINGS.values():
        final = game.pose.bones[channel].constraints[-1]
        original_mute = final.mute
        try:
            final.mute = True
            update()
            try:
                export_animation.authoring_capabilities(scene, game, capability_sample)
            except ValueError:
                rejected.append(channel)
            else:
                raise RuntimeError("Exporter accepted viewport-only prop mutation for " + channel)
        finally:
            final.mute = original_mute
            update()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(diagnostic), compress=True, check_existing=False)
    authored_payload = action_payload(action)
    report = export_animation.export_animation(SimpleNamespace(
        rig=None, output=clip, start=1, end=65, game_armature=game.name,
        source_fbx=export_animation.SOURCE_FBX, tolerance=5e-5))
    require(report["status"] == "fbx-roundtrip-passed", "Verified FBX export failed")
    require(action_payload(action) == authored_payload,
            "Exporter changed the authored diagnostic keys/custom poses")
    require(all(name in bpy.data.actions and action_payload(bpy.data.actions[name]) == payload
                for name, payload in original_actions.items()), "Exporter changed an existing action")
    require(digest(source) == source_sha, "Input artist rig changed on disk")
    summary = {"schema": 1, "status": "feedback-diagnostic-fbx-roundtrip-passed",
        "source_rig": str(source), "source_sha256": source_sha,
        "diagnostic_blend": str(diagnostic), "diagnostic_sha256": digest(diagnostic),
        "animation_fbx": str(clip), "fbx_sha256": digest(clip),
        "frames": 65, "bones": 138, "poses": poses,
        "original_actions_preserved": sorted(original_actions),
        "viewport_only_mutations_rejected": rejected,
        "authoring_capabilities": report["authoring_capabilities"],
        "game_rest_preserved": True, "source_file_preserved": True,
        "limitation": "Offline custom diagnostic only; no production animation or in-game acceptance"}
    (output / "feedback_export_report.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("WARLOCK_FEEDBACK_EXPORT", json.dumps({key: value for key, value in summary.items() if key != "poses"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rig", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    main(parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []))
