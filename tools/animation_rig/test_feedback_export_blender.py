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
import test_feedback_preservation_blender as preservation


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def action_payload(action):
    """Keys, handles, modifiers, groups and markers, excluding volatile ID data."""
    return next(item for item in preservation.action_payload() if item["name"] == action.name)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def exercise_nla_export(rig, game, output):
    """Export a live, visibly effective NLA strip without flattening its data."""
    animation = rig.animation_data
    require(animation is not None and animation.action is None and not animation.nla_tracks,
            "NLA fixture requires the separate fresh handoff scene")
    scene = bpy.context.scene
    frame, subframe = scene.frame_current, scene.frame_subframe
    start, end = scene.frame_start, scene.frame_end
    original_pose = export_animation.authoring_pose_state(scene)
    original_use_nla = animation.use_nla
    control = rig.pose.bones["ORG-j_backpack"]
    basis = control.matrix_basis.copy()
    action = bpy.data.actions.new("WARLOCK_NLA_EXPORT_DIAGNOSTIC_ONLY")
    track = None
    try:
        animation.action = action
        for key_frame, displacement in ((1, 0.), (3, .012), (5, 0.)):
            scene.frame_set(key_frame)
            control.matrix_basis = basis
            control.location.x += displacement
            control.keyframe_insert("location", index=0, frame=key_frame,
                                    group="Existing backpack custom pose")
        action.pose_markers.new("NLA custom pose").frame = 3
        slot = animation.action_slot
        for layer in action.layers:
            for strip in layer.strips:
                bag = strip.channelbag(slot, ensure=False)
                if bag:
                    for curve in bag.fcurves:
                        curve.modifiers.new("CYCLES")
        animation.action = None
        animation.use_nla = True
        control.matrix_basis = basis
        track = animation.nla_tracks.new()
        track.name = "WARLOCK_NLA_EXPORT_DIAGNOSTIC_ONLY"
        strip = track.strips.new("Preserve timing influence and custom pose", 1, action)
        if hasattr(strip, "action_slot"):
            strip.action_slot = slot
        strip.blend_type = "REPLACE"
        strip.extrapolation = "NOTHING"
        strip.influence = .8
        scene.frame_start, scene.frame_end = 1, 5
        scene.frame_set(3)
        rig.update_tag()
        bpy.context.view_layer.update()
        graph = bpy.context.evaluated_depsgraph_get()
        native = game.evaluated_get(graph)
        posed = (native.matrix_world @ native.pose.bones["j_backpack"].matrix).translation.copy()
        track.mute = True
        control.matrix_basis = basis
        scene.frame_set(3)
        rig.update_tag()
        bpy.context.view_layer.update()
        native = game.evaluated_get(bpy.context.evaluated_depsgraph_get())
        unlayered = (native.matrix_world @ native.pose.bones["j_backpack"].matrix).translation.copy()
        moved = (posed - unlayered).length
        require(moved > .005, "NLA fixture did not affect the actual GAME pose: " + str(moved))
        track.mute = False
        scene.frame_set(3)
        rig.update_tag()
        bpy.context.view_layer.update()
        # A manual edit of a currently animated channel must survive export,
        # together with a fractional timeline position and a numeric pose option.
        scene.frame_set(2, subframe=.25)
        control.location.x += .004
        settings = rig.pose.bones["CTRL-hand-settings-left"]
        settings["curl_middle"] = .17
        rig.update_tag()
        bpy.context.view_layer.update()
        custom_basis = control.matrix_basis.copy()
        native = game.evaluated_get(bpy.context.evaluated_depsgraph_get())
        custom_worlds = {bone.name: (native.matrix_world @ bone.matrix).copy()
                         for bone in native.pose.bones}
        before_actions = preservation.action_payload()
        before_bindings = preservation.animation_bindings()
        clip = output / "warlock_nla_preservation_diagnostic.fbx"
        receipt = export_animation.export_animation(SimpleNamespace(
            rig=None, output=clip, start=1, end=5, game_armature=game.name,
            source_fbx=export_animation.SOURCE_FBX, tolerance=5e-5))
        require(receipt["status"] == "fbx-roundtrip-passed", "Live NLA FBX export failed")
        require(preservation.action_payload() == before_actions,
                "Exporter changed NLA action keys/groups/modifiers/markers")
        require(preservation.animation_bindings() == before_bindings,
                "Exporter changed NLA strips, timing, influence or bindings")
        require(scene.frame_current == 2 and abs(scene.frame_subframe - .25) < 1e-8,
                "Exporter changed the posed subframe")
        require(export_animation.matrix_error(control.matrix_basis, custom_basis) < 1e-7
                and settings["curl_middle"] == .17,
                "Exporter discarded an unkeyed transform or custom numeric pose")
        native = game.evaluated_get(bpy.context.evaluated_depsgraph_get())
        pose_error = max(export_animation.matrix_error(custom_worlds[bone.name],
                            native.matrix_world @ bone.matrix) for bone in native.pose.bones)
        require(pose_error < 2e-5, "Exporter changed the displayed GAME custom pose")
        return {"status": "live-nla-fbx-roundtrip-passed", "frames": 5,
            "game_backpack_displacement_m": moved,
            "actions_keys_modifiers_markers_preserved": True,
            "nla_strips_timing_influence_bindings_preserved": True,
            "posed_subframe_restored": 2.25, "unkeyed_transform_and_numeric_pose_preserved": True,
            "maximum_restored_game_matrix_error": pose_error,
            "fbx_sha256": digest(clip), "export_report": str(clip.with_suffix(".export.json"))}
    finally:
        animation.action = None
        animation.use_nla = original_use_nla
        if track is not None:
            animation.nla_tracks.remove(track)
        bpy.data.actions.remove(action)
        scene.frame_start, scene.frame_end = start, end
        scene.frame_set(frame, subframe=subframe)
        export_animation.restore_authoring_pose(original_pose)


def exercise_centered_rocket(rig, game):
    """Require the real mesh to rotate about the new gizmo, including stretch."""
    raw = rig["warlock_weapon_follow_manifest"]
    manifest = json.loads(raw)
    require(manifest.get("rocket_pivot", {}).get("policy") == "centered-native-frame-v1",
            "This revision requires the real centered rocket pivot")
    center = Vector(manifest["rocket_pivot"]["local_center"])
    original_pose = export_animation.authoring_pose_state(bpy.context.scene)
    settings = rig.pose.bones["CTRL-shape-j_leftarm_scale"]
    control = rig.pose.bones["CTRL-rocket"]
    maximum_center_error = 0.
    minimum_origin_orbit = math.inf
    cases = []

    def sample():
        rig.update_tag()
        bpy.context.view_layer.update()
        graph = bpy.context.evaluated_depsgraph_get()
        native = game.evaluated_get(graph)
        controls = rig.evaluated_get(graph)
        native_world = native.matrix_world @ native.pose.bones["j_leftweaponcomponent2"].matrix
        rigid = Matrix.LocRotScale(native_world.translation,
            export_animation.normalized_native_rotation(native_world), Vector((1, 1, 1)))
        pivot = (controls.matrix_world @ controls.pose.bones["CTRL-rocket"].matrix).translation.copy()
        return rigid, pivot

    try:
        weapon_controls.switch_follow(rig, "rocket_follow", False)
        for length in (.75, 1., 1.35):
            settings["length"], settings["volume"] = length, 1.
            before, pivot = sample()
            basis = control.matrix_basis.copy()
            for axis in range(3):
                from mathutils import Quaternion
                direction = Vector((0., 0., 0.))
                direction[axis] = 1.
                control.rotation_quaternion = control.rotation_quaternion @ Quaternion(direction, .2)
                after, moved_pivot = sample()
                error = max((before @ center - pivot).length,
                            (after @ center - moved_pivot).length,
                            (moved_pivot - pivot).length)
                orbit = (after.translation - before.translation).length
                maximum_center_error = max(maximum_center_error, error)
                minimum_origin_orbit = min(minimum_origin_orbit, orbit)
                require(error < 5e-5 and orbit > .001,
                        "Rocket rotation used its native origin instead of the actual mesh center")
                cases.append({"arm_length": length, "axis": axis,
                              "mesh_center_error_m": error, "native_origin_orbit_m": orbit})
                control.matrix_basis = basis
                sample()
        # A visually plausible declared center must not bypass its actual
        # geometry/calibration check in the exporter.
        altered = json.loads(raw)
        altered["rocket_pivot"]["local_center"][0] += .01
        rig["warlock_weapon_follow_manifest"] = json.dumps(altered)
        native = game.evaluated_get(bpy.context.evaluated_depsgraph_get())
        samples = [{"frame": bpy.context.scene.frame_current, "bones": {
            bone.name: (native.matrix_world @ bone.matrix).copy() for bone in native.pose.bones}}]
        try:
            export_animation.authoring_capabilities(bpy.context.scene, game, samples)
        except ValueError:
            pass
        else:
            raise RuntimeError("Exporter accepted a false declared rocket center")
        return {"status": "centered-native-pivot-passed", "cases": cases,
            "maximum_mesh_center_error_m": maximum_center_error,
            "minimum_native_origin_orbit_m": minimum_origin_orbit,
            "false_center_manifest_rejected": True}
    finally:
        rig["warlock_weapon_follow_manifest"] = raw
        export_animation.restore_authoring_pose(original_pose)


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
    centered_rocket = exercise_centered_rocket(rig, game)
    nla_export = exercise_nla_export(rig, game, output)
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
            prop("CTRL-shape-j_leftarm_scale", "length", 1.18)
            prop("CTRL-shape-j_leftarm_scale", "volume", .8)
            update()
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
        "live_nla_export": nla_export,
        "centered_rocket": centered_rocket,
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
