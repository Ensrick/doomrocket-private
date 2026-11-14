"""Exercise actual portable reference playback without saving the artist file.

Blender --background --factory-startup --disable-autoexec --python-exit-code 1
 --python test_reference_playback_blender.py -- --rig <handoff.blend>
 --tools <portable folder containing UI/helper/reference library> --output <json>
"""
import argparse
from array import array
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

import bpy
from mathutils import Matrix, Vector


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def action_payload(action):
    # Stream numeric buffers instead of materializing millions of Python key
    # tuples from the reference library. Memory stays bounded to one curve.
    result = hashlib.sha256()
    result.update(json.dumps((action.name, action.use_fake_user, numeric_props(action)), sort_keys=True).encode())
    result.update(json.dumps([(marker.name, marker.frame) for marker in action.pose_markers]).encode())
    for layer in action.layers:
        for strip in layer.strips:
            if not hasattr(strip, "channelbag"):
                continue
            for slot in action.slots:
                bag = strip.channelbag(slot)
                if bag is not None:
                    for curve in bag.fcurves:
                        result.update(json.dumps((slot.identifier, curve.data_path, curve.array_index,
                            curve.group.name if curve.group else None, curve.extrapolation,
                            curve.mute, curve.lock)).encode())
                        for field in ("co", "handle_left", "handle_right"):
                            values = array("f", [0]) * (len(curve.keyframe_points) * 2)
                            curve.keyframe_points.foreach_get(field, values)
                            result.update(values.tobytes())
                        for field in ("interpolation", "handle_left_type", "handle_right_type", "type", "easing"):
                            values = array("i", [0]) * len(curve.keyframe_points)
                            curve.keyframe_points.foreach_get(field, values)
                            result.update(values.tobytes())
                        for modifier in curve.modifiers:
                            fields = {}
                            for prop in modifier.bl_rna.properties:
                                if prop.identifier == "rna_type":
                                    continue
                                value = getattr(modifier, prop.identifier)
                                if isinstance(value, (int, float, str, bool)):
                                    fields[prop.identifier] = value
                                elif prop.is_array:
                                    fields[prop.identifier] = list(value)
                            result.update(json.dumps(fields, sort_keys=True).encode())
    return result.hexdigest()


def numeric_props(owner):
    return {key: value for key, value in owner.items() if isinstance(value, (int, float, bool, str))}


class PlaybackTests:
    def __init__(self, args):
        self.args = args
        self.source_sha = digest(args.rig)
        bpy.ops.wm.open_mainfile(filepath=str(args.rig.resolve()), use_scripts=False)
        path = args.tools.resolve() / "warlock_rig_ui.py"
        spec = importlib.util.spec_from_file_location("warlock_reference_ui_tests", path)
        self.ui = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.ui)
        self.ui.register()
        self.ui.register()
        self.rig = bpy.data.objects["WARLOCK_CTRL"]
        self.game = bpy.data.objects[self.rig["warlock_game_armature"]]
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        for obj in bpy.context.view_layer.objects:
            obj.select_set(False)
        self.rig.hide_set(False)
        self.rig.select_set(True)
        bpy.context.view_layer.objects.active = self.rig
        bpy.ops.object.mode_set(mode="POSE")
        # A genuine active keyed action plus live NLA and a separate unkeyed
        # custom pose expose the destructive importer behavior being prevented.
        scene = bpy.context.scene
        scene.frame_start, scene.frame_end = 7, 219
        scene.render.fps, scene.render.fps_base = 48, 1.0
        scene.use_preview_range = True
        scene.frame_preview_start, scene.frame_preview_end = 13, 83
        scene.frame_set(33, subframe=.25)
        action = bpy.data.actions.new("ARTIST_CUSTOM_POSE_PRESERVATION_FIXTURE")
        self.rig.animation_data_create().action = action
        self.rig.pose.bones["root"].location.x = .137
        self.rig.pose.bones["root"].keyframe_insert("location", frame=33.25)
        self.rig.pose.bones["root"].location.x = .219
        self.rig.pose.bones["root"].keyframe_insert("location", frame=55)
        action.pose_markers.new("Saved artist custom pose").frame = 33
        for layer in action.layers:
            for action_strip in layer.strips:
                for bag in action_strip.channelbags:
                    for curve in bag.fcurves:
                        curve.modifiers.new("CYCLES")
        track = self.rig.animation_data.nla_tracks.new()
        track.name = "ARTIST_NLA_PRESERVATION_FIXTURE"
        strip = track.strips.new("Saved artist strip", 1, action)
        strip.blend_type = "ADD"
        strip.influence = .35
        track.mute = False
        # Change an unkeyed control and a numeric setting in addition to keys.
        self.rig.pose.bones["j_lefthand_ctrl_ik"].location.y += .031
        self.rig.pose.bones["CTRL-hand-settings-left"]["curl"] = .07
        self.rig.data.bones.active = self.rig.data.bones["j_lefthand_ctrl_ik"]
        self.rig.pose.bones["j_lefthand_ctrl_ik"].select = True
        scene.frame_set(33, subframe=.25)
        bpy.context.view_layer.update()
        self.protected_actions = tuple(bpy.data.actions)
        self.protected_objects = tuple(bpy.context.scene.objects)
        self.before = self.snapshot()
        self.collection = None
        self.helper = self.ui.reference_module(self.rig)
        self.results = {"rig_sha256": self.source_sha,
                        "ui_sha256": digest(path),
                        "helper_sha256": digest(args.tools / "reference_playback.py"),
                        "blender": bpy.app.version_string, "tests": [], "failures": [],
                        "native_game_playback_claimed": False}

    def snapshot(self):
        scene = bpy.context.scene
        state = {"timeline": (scene.frame_current, scene.frame_subframe, scene.frame_start,
            scene.frame_end, scene.render.fps, scene.render.fps_base, scene.use_preview_range,
            scene.frame_preview_start, scene.frame_preview_end),
            "active": bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None,
            "mode": bpy.context.mode,
            "selection": sorted(obj.name for obj in self.protected_objects if obj.select_get()),
            "pose_selection": sorted(bone.name for bone in self.rig.pose.bones if bone.select),
            "active_bone": self.rig.data.bones.active.name if self.rig.data.bones.active else None,
            "actions": {action.name: action_payload(action) for action in self.protected_actions},
            "objects": {}, "game_pose": {name: [list(row) for row in matrix]
                for name, matrix in self.ui.game_pose(self.rig).items()}}
        for obj in self.protected_objects:
            entry = {"matrix_basis": [list(row) for row in obj.matrix_basis],
                     "data": obj.data.name if obj.data else None,
                     "parent": obj.parent.name if obj.parent else None,
                     "visibility": (obj.hide_select, obj.hide_viewport, obj.hide_render, obj.hide_get()),
                     "properties": numeric_props(obj)}
            data = obj.animation_data
            if data:
                entry["animation"] = {"action": data.action.name if data.action else None,
                    "action_slot": data.action_slot.identifier if data.action_slot else None,
                    "use_nla": data.use_nla,
                    "nla": [(track.name, track.mute, track.is_solo,
                        [(strip.name, strip.action.name if strip.action else None,
                          strip.frame_start, strip.frame_end, strip.action_frame_start,
                          strip.action_frame_end, strip.scale, strip.repeat, strip.influence,
                          strip.blend_type, strip.extrapolation, strip.mute)
                         for strip in track.strips]) for track in data.nla_tracks]}
            if obj.type == "ARMATURE":
                entry["bones"] = {bone.name: {"basis": [list(row) for row in bone.matrix_basis],
                    "properties": numeric_props(bone), "rotation_mode": bone.rotation_mode}
                    for bone in obj.pose.bones}
            state["objects"][obj.name] = entry
        return state

    def assert_preserved(self):
        bpy.context.view_layer.update()
        after = self.snapshot()
        differences = []
        def compare(a, b, path):
            if len(differences) >= 8 or a == b:
                return
            if isinstance(a, dict) and isinstance(b, dict) and a.keys() == b.keys():
                for key in a:
                    compare(a[key], b[key], path + "/" + str(key))
            elif isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)) and len(a) == len(b):
                for index, (x, y) in enumerate(zip(a, b)):
                    compare(x, y, path + "/" + str(index))
            else:
                differences.append({"path": path, "before": str(a)[:160], "after": str(b)[:160]})
        compare(self.before, after, "artist")
        assert not differences, "Reference playback changed protected artist state: " + json.dumps(differences)
        assert digest(self.args.rig) == self.source_sha, "Source blend was changed"

    def run(self, name, function):
        try:
            detail = function()
            self.assert_preserved()
            record = {"name": name, "passed": True, "detail": detail}
        except Exception as error:
            record = {"name": name, "passed": False, "error": str(error)}
            self.results["failures"].append(name)
        self.results["tests"].append(record)
        print("WARLOCK_REFERENCE_TEST", json.dumps(record))

    def load(self):
        assert bpy.ops.warlock.reference_load() == {"FINISHED"}
        self.collection = self.helper.collection_for(bpy.context.scene, self.rig.name)
        assert self.collection is not None
        info = self.helper.manifest(self.collection)
        assert len(info["clips"]) == 13
        assert sum(bool(clip["asm_referenced"]) for clip in info["clips"]) == 12
        assert self.collection.hide_render
        assert self.helper.armature_for(self.collection).data != self.game.data
        assert all(obj.get("warlock_reference_only") and obj.hide_select
                   for obj in self.collection.all_objects)
        assert self.helper.armature_for(self.collection).animation_data is None
        return {"clips": 13, "shipping_asm_referenced": 12, "isolated": True,
                "preserved_artist_action_nla_custom_pose_selection_timeline": True}

    def idempotent_load(self):
        ids = {obj.as_pointer() for obj in self.collection.all_objects}
        actions = tuple(bpy.data.actions)
        assert bpy.ops.warlock.reference_load() == {"FINISHED"}
        assert ids == {obj.as_pointer() for obj in self.collection.all_objects}
        assert actions == tuple(bpy.data.actions)
        return {"no_duplicate_library_or_actions": True}

    def every_clip(self):
        rig = self.helper.armature_for(self.collection)
        measurements = []
        settings = bpy.context.scene.warlock_reference_settings
        for clip in self.helper.manifest(self.collection)["clips"]:
            settings.clip = clip["id"]
            before = {bone.name: bone.matrix.copy() for bone in rig.pose.bones}
            settings.frame = (clip["start"] + clip["end"]) / 2
            bpy.context.view_layer.update()
            delta = max(max(abs(a - b) for row_a, row_b in zip(before[bone.name], bone.matrix)
                            for a, b in zip(row_a, row_b)) for bone in rig.pose.bones)
            assert delta > 1e-6, "Reference clip has no measurable motion: " + clip["id"]
            assert all(math.isfinite(value) for bone in rig.pose.bones
                       for row in bone.matrix for value in row)
            measurements.append({"clip": clip["id"], "pose_delta": delta})
        return {"all_thirteen_real_clips_move": measurements}

    def private_clock(self):
        settings = bpy.context.scene.warlock_reference_settings
        settings.clip = "combat_walk"
        settings.frame = 1
        frame = self.helper.advance(self.collection, .1, 1.0, False)
        assert abs(frame - 7) < 1e-6
        clip = self.helper.clip_for(self.collection)
        self.helper.advance(self.collection, 100, 1.0, True)
        assert clip["start"] <= self.collection["warlock_reference_frame"] < clip["end"]
        self.helper.advance(self.collection, 100, 1.0, False)
        assert self.collection["warlock_reference_frame"] == clip["end"]
        return {"reference_advances_60_frames_per_second": True,
                "loop_and_nonloop_endpoints": True, "artist_clock_frozen": True}

    def private_clock_matches_native_blender_action(self):
        """Compare manual reference evaluation to Blender's own Action evaluator.

        The oracle lives in another scene containing only a copied reference
        armature, so even this test never changes the artist scene's clock.
        """
        reference = self.helper.armature_for(self.collection)
        oracle = reference.copy()
        oracle.data = reference.data.copy()
        oracle.name = "REFERENCE_ACTION_EVALUATOR_TEST_ONLY"
        oracle.parent = None
        oracle.matrix_world = reference.matrix_world.copy()
        oracle_scene = bpy.data.scenes.new("REFERENCE_ACTION_EVALUATOR_TEST_ONLY")
        oracle_scene.collection.objects.link(oracle)
        records = []
        try:
            settings = bpy.context.scene.warlock_reference_settings
            for clip in self.helper.manifest(self.collection)["clips"]:
                settings.clip = clip["id"]
                action = bpy.data.actions[clip["action"]]
                animation = oracle.animation_data_create()
                animation.action = action
                animation.action_slot = action.slots[0]
                error = 0.0
                for frame in (clip["start"], (clip["start"] + clip["end"]) / 2, clip["end"]):
                    settings.frame = frame
                    effective_frame = self.collection["warlock_reference_frame"]
                    bpy.context.view_layer.update()
                    evaluated = reference.evaluated_get(bpy.context.evaluated_depsgraph_get())
                    expected = {bone.name: (evaluated.matrix_world @ bone.matrix).copy()
                                for bone in evaluated.pose.bones}
                    with bpy.context.temp_override(scene=oracle_scene, view_layer=oracle_scene.view_layers[0]):
                        oracle_scene.frame_set(math.floor(effective_frame), subframe=effective_frame % 1)
                        native = oracle.evaluated_get(bpy.context.evaluated_depsgraph_get())
                        actual = {bone.name: (native.matrix_world @ bone.matrix).copy()
                                  for bone in native.pose.bones}
                    error = max(error, self.ui.pose_error(expected, actual))
                assert error < 5e-6, "Private reference clock differs from Blender Action: " + clip["id"] + " " + str(error)
                records.append({"clip": clip["id"], "world_probe_error_m": error, "poses": 3})
        finally:
            oracle.animation_data_clear()
            armature_data = oracle.data
            bpy.data.objects.remove(oracle, do_unlink=True)
            bpy.data.armatures.remove(armature_data)
            bpy.data.scenes.remove(oracle_scene)
        return {"all_thirteen_private_clips_match_native_blender_action_evaluator": records,
                "tolerance_m": 5e-6, "artist_scene_clock_never_changed": True,
                "native_game_unit_capture": False}

    def transport(self):
        settings = bpy.context.scene.warlock_reference_settings
        settings.clip = "combat_walk"
        assert bpy.ops.warlock.reference_transport(command="FIRST") == {"FINISHED"}
        assert bpy.ops.warlock.reference_transport(command="PLAY") == {"FINISHED"}
        assert self.helper.playing(self.collection)
        record = self.helper._TIMERS[self.collection.as_pointer()]
        record["last"] -= .1
        assert record["callback"]() == 1 / 60
        assert self.collection["warlock_reference_frame"] > 6.9
        assert bpy.ops.warlock.reference_transport(command="STOP") == {"FINISHED"}
        assert not self.helper.playing(self.collection)
        assert abs(settings.frame - self.collection["warlock_reference_frame"]) < 1e-5
        return {"actual_bpy_application_timer_registered_and_unregistered": True,
                "registered_timer_callback_exercised_directly_in_background": True,
                "no_interactive_graphics_input_test": True, "no_artist_timeline_playback": True}

    def scrub_stops(self):
        settings = bpy.context.scene.warlock_reference_settings
        self.helper.start(self.collection)
        settings.frame = 4.5
        assert not self.helper.playing(self.collection)
        assert self.collection["warlock_reference_frame"] == 4.5
        return {"subframe_scrub_stops_timer": True}

    def isolation(self):
        ref = self.helper.armature_for(self.collection)
        assert not self.ui.is_control_rig(ref)
        assert self.ui.available_rigs(bpy.context) == [self.rig]
        assert self.rig["warlock_game_armature"] == self.game.name
        assert self.game != ref and self.game.data != ref.data
        artist_meshes = {obj.data for obj in self.protected_objects if obj.type == "MESH"}
        assert all(obj.data not in artist_meshes for obj in self.collection.all_objects if obj.type == "MESH")
        self.collection.hide_viewport = True
        self.collection.hide_viewport = False
        return {"not_discoverable_as_artist_rig": True, "game_export_target_unchanged": True,
                "independent_armature_and_mesh_data": True}

    def missing_and_invalid_input(self):
        try:
            self.helper.load_reference(bpy.context.scene, "missing-library-fixture",
                                       self.args.tools / "missing-never-created.blend")
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Missing library silently accepted")
        for frame in (float("nan"), float("inf")):
            try:
                self.helper.set_frame(self.collection, frame)
            except ValueError:
                pass
            else:
                raise AssertionError("Nonfinite reference frame accepted")
        return {"missing_library_actionable_error": True, "nonfinite_clock_rejected": True}

    def late_load_failure_cleanup(self):
        """Fail after fake-user actions/root were appended, not before import."""
        before = {kind: set(getattr(bpy.data, kind)) for kind in self.helper._IMPORT_IDS}
        original = self.helper.set_frame
        def fail_after_append(*args, **kwargs):
            raise RuntimeError("PLANTED_LATE_REFERENCE_VALIDATION_FAILURE")
        self.helper.set_frame = fail_after_append
        try:
            try:
                self.helper.load_reference(bpy.context.scene, "PLANTED_LATE_REFERENCE_OWNER",
                    self.args.tools / "reference/warlock_animation_reference.blend")
            except RuntimeError as error:
                assert "PLANTED_LATE_REFERENCE_VALIDATION_FAILURE" in str(error)
            else:
                raise AssertionError("Planted late library failure was ignored")
        finally:
            self.helper.set_frame = original
        for kind in before:
            assert set(getattr(bpy.data, kind)) == before[kind], "Failed library import leaked or removed IDs: " + kind
        assert self.helper.collection_for(bpy.context.scene, self.rig.name) == self.collection
        return {"late_failure_after_fake_user_actions_and_root": True,
                "all_preexisting_identities_retained": True,
                "all_owned_appended_actions_meshes_armatures_collections_removed": True}

    def repeated_registration(self):
        self.helper.start(self.collection)
        self.ui.register()
        assert not self.helper.playing(self.collection)
        self.ui.register()
        self.ui.unregister()
        self.ui.unregister()
        assert not hasattr(bpy.types.Scene, "warlock_reference_settings")
        self.ui.register()
        return {"repeat_register_and_unregister": True, "no_timer_left_running": True}

    def export_with_reference(self, planted_failure=False):
        """Exercise the real FBX boundary with artist NLA/custom pose intact."""
        path = self.args.tools / "export_animation.py"
        spec = importlib.util.spec_from_file_location("warlock_reference_verified_exporter", path)
        exporter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(exporter)
        self.helper.stop(self.collection)
        references = {clip["action"]: action_payload(bpy.data.actions[clip["action"]])
                      for clip in self.helper.manifest(self.collection)["clips"]}
        reference_pose = {bone.name: [list(row) for row in bone.matrix_basis]
                          for bone in self.helper.armature_for(self.collection).pose.bones}
        output = self.args.output.parent / "loaded-export/reference_loaded_diagnostic.fbx"
        scene = bpy.context.scene
        fps, fps_base = scene.render.fps, scene.render.fps_base
        scene.render.fps, scene.render.fps_base = 60, 1.0
        arguments = SimpleNamespace(rig=None, output=output, start=33, end=35,
            game_armature=self.game.name, source_fbx=self.args.tools / "reference/shipping_body.fbx",
            tolerance=5e-5)
        known = {suffix: digest(output.with_suffix(suffix))
                 for suffix in (".fbx", ".animation", ".export.json")
                 if output.with_suffix(suffix).is_file()}
        if planted_failure:
            assert len(known) == 3, "Establish a successful export before testing rollback"
            def fail_after_roundtrip(*args, **kwargs):
                raise RuntimeError("PLANTED_REFERENCE_ROUNDTRIP_FAILURE")
            exporter.compare_roundtrip = fail_after_roundtrip
        try:
            if planted_failure:
                try:
                    exporter.export_animation(arguments)
                except RuntimeError as error:
                    assert "PLANTED_REFERENCE_ROUNDTRIP_FAILURE" in str(error)
                else:
                    raise AssertionError("Planted roundtrip failure was ignored")
                assert all(digest(output.with_suffix(suffix)) == value for suffix, value in known.items())
                detail = {"planted_roundtrip_failure_restores_artist_and_reference_pose": True,
                          "previous_successful_bundle_preserved": True}
            else:
                result = exporter.export_animation(arguments)
                assert result["status"] == "fbx-roundtrip-passed"
                assert len(result["bone_names"]) == 138
                assert result["bone_names"] == list(self.game.data.bones.keys())
                assert all(not name.startswith(("CTRL-", "WARLOCK_REFERENCE")) for name in result["bone_names"])
                detail = {"actual_three_frame_fbx_roundtrip_passed": True,
                          "only_138_shipping_bones_exported": True,
                          "manifest_sha256": digest(output.with_suffix(".export.json"))}
        finally:
            scene.render.fps, scene.render.fps_base = fps, fps_base
        assert references == {name: action_payload(bpy.data.actions[name]) for name in references}
        assert reference_pose == {bone.name: [list(row) for row in bone.matrix_basis]
                                   for bone in self.helper.armature_for(self.collection).pose.bones}
        return detail

    def execute(self):
        self.run("actual_load_preserves_active_artist_action_nla_custom_pose_and_selection", self.load)
        if self.collection is not None:
            self.run("load_is_idempotent", self.idempotent_load)
            self.run("all_original_clips_move_on_isolated_reference", self.every_clip)
            self.run("private_clock_does_not_change_artist_timeline", self.private_clock)
            self.run("private_reference_clock_matches_blender_action_without_artist_retiming",
                     self.private_clock_matches_native_blender_action)
            self.run("actual_play_stop_first_operators", self.transport)
            self.run("scrubbing_stops_only_reference_clock", self.scrub_stops)
            self.run("reference_data_excluded_from_artist_rig_and_export_target", self.isolation)
            self.run("missing_library_and_invalid_clock_fail_safely", self.missing_and_invalid_input)
            self.run("late_library_validation_failure_cleans_owned_ids_and_preserves_artist_data",
                     self.late_load_failure_cleanup)
            if self.args.require_export:
                self.run("actual_verified_export_with_loaded_reference_preserves_artist_tracks_and_pose",
                         self.export_with_reference)
                self.run("failed_verified_export_with_loaded_reference_preserves_artist_tracks_and_pose",
                         lambda: self.export_with_reference(True))
            self.run("repeated_script_registration_and_unregister_stop_timers", self.repeated_registration)
        self.helper.stop_all()
        self.ui.unregister()
        self.results["passed"] = not self.results["failures"]
        self.results["source_blend_sha256_after"] = digest(self.args.rig)
        return self.results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rig", type=Path, required=True)
    parser.add_argument("--tools", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-export", action="store_true",
                        help="Also exercise the adjacent verified FBX exporter and its failure rollback")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    result = PlaybackTests(args).execute()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("WARLOCK_REFERENCE_TEST_REPORT", args.output, result["passed"])
    if not result["passed"]:
        raise RuntimeError("Reference playback tests failed: " + ", ".join(result["failures"]))


if __name__ == "__main__":
    main()
