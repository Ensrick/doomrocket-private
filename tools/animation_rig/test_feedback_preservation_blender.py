"""Independent skeleton/source and non-destructive UI/widget checks.

Blender --background --factory-startup --disable-autoexec --python-exit-code 1
  --python test_feedback_preservation_blender.py -- --rig <candidate.blend>
  --output <report.json> [--exercise-widgets]

The input blend and shipping sources are read-only. This is an authoring check,
not evidence of engine playback or a rendered in-game verdict.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import subprocess
import sys

import bpy
from mathutils import Matrix


ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent
# Blender does not add the --python script directory to sys.path. Display
# modules share anatomical calibration helpers with the builder.
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False,
                                     separators=(",", ":")).encode()).hexdigest()


def matrix_rows(value):
    return [list(row) for row in value]


def skeleton(armature):
    return [{"name": b.name, "parent": b.parent.name if b.parent else None,
             "rest": matrix_rows(b.matrix_local), "inherit_scale": b.inherit_scale,
             "deform": b.use_deform, "connected": b.use_connect}
            for b in armature.data.bones]


def scalar_rna(value):
    """Stable scalar/array RNA including key modifiers and NLA timing flags."""
    result = {}
    for prop in value.bl_rna.properties:
        name = prop.identifier
        if name in {"rna_type", "users", "session_uid", "is_updated", "is_updated_data",
                    "is_evaluated", "is_editable", "is_library_indirect", "tag"} or prop.type not in {
                        "BOOLEAN", "INT", "FLOAT", "STRING", "ENUM"}:
            continue
        item = getattr(value, name)
        if getattr(prop, "is_array", False):
            item = list(item)
        elif isinstance(item, set):
            item = sorted(item)
        result[name] = item
    return result


def curve_payload(curve):
    return {"path": curve.data_path, "index": curve.array_index,
        "extrapolation": curve.extrapolation, "mute": curve.mute,
        "lock": curve.lock, "hide": curve.hide, "color": list(curve.color),
        "color_mode": curve.color_mode, "auto_smoothing": curve.auto_smoothing,
        "group": curve.group.name if curve.group else None,
        "keys": [{"co": list(k.co), "left": list(k.handle_left),
                  "right": list(k.handle_right), "left_type": k.handle_left_type,
                  "right_type": k.handle_right_type, "interpolation": k.interpolation,
                  "easing": k.easing, "amplitude": k.amplitude, "back": k.back,
                  "period": k.period, "type": k.type} for k in curve.keyframe_points],
        "samples": [list(p.co) for p in curve.sampled_points],
        "modifiers": [{"settings": scalar_rna(m),
                       "control_points": [scalar_rna(p) for p in getattr(m, "control_points", ())]}
                      for m in curve.modifiers]}


def action_payload():
    result = []
    for action in sorted(bpy.data.actions, key=lambda a: a.name):
        layers = []
        for layer in action.layers:
            strips = []
            for strip in layer.strips:
                bags = []
                for bag in getattr(strip, "channelbags", ()):
                    bags.append({"slot": bag.slot_handle,
                        "groups": [{"name": g.name, "settings": scalar_rna(g)} for g in bag.groups],
                        "curves": [curve_payload(c) for c in bag.fcurves]})
                strips.append({"type": strip.type, "bags": bags})
            layers.append({"name": layer.name, "strips": strips})
        result.append({"name": action.name,
            "slots": [(s.identifier, s.handle, s.target_id_type) for s in action.slots],
            "settings": scalar_rna(action), "fake_user": action.use_fake_user,
            "markers": [(m.name, m.frame) for m in action.pose_markers], "layers": layers})
    return result


def nla_strip_payload(strip):
    return {"settings": scalar_rna(strip),
            "action": strip.action.name if strip.action else None,
            "slot": getattr(getattr(strip, "action_slot", None), "identifier", None),
            "fcurves": [curve_payload(c) for c in strip.fcurves],
            "modifiers": [{"settings": scalar_rna(m),
                           "control_points": [scalar_rna(p) for p in getattr(m, "control_points", ())]}
                          for m in strip.modifiers],
            "strips": [nla_strip_payload(s) for s in strip.strips]}


def animation_bindings():
    result = {}
    owners = {}
    for obj in bpy.data.objects:
        owners["OBJECT:" + obj.name] = obj
        if obj.data:
            owners[type(obj.data).__name__ + ":" + obj.data.name] = obj.data
        if obj.type == "MESH" and obj.data.shape_keys:
            owners["KEY:" + obj.data.shape_keys.name] = obj.data.shape_keys
    for name, owner in owners.items():
        ad = owner.animation_data
        if ad is None:
            # Disposable widget mesh/object IDs are intentionally replaced by
            # display edits. Keep every animated owner and the export-lane
            # armatures even when their source binding is empty.
            if name in {"OBJECT:WARLOCK_CTRL", "OBJECT:WARLOCK_GAME"}:
                result[name] = None
            continue
        result[name] = {"settings": scalar_rna(ad),
            "action": ad.action.name if ad.action else None,
            "slot": getattr(getattr(ad, "action_slot", None), "identifier", None),
            "tracks": [{"settings": scalar_rna(track),
                        "strips": [nla_strip_payload(strip) for strip in track.strips]}
                       for track in ad.nla_tracks]}
    return result


def numeric_properties(bone):
    result = {}
    for key in bone.keys():
        value = bone[key]
        if isinstance(value, (float, int, bool)):
            result[key] = value
        elif hasattr(value, "to_list"):
            values = value.to_list()
            if all(isinstance(v, (float, int, bool)) for v in values):
                result[key] = values
    return result


def pose_payload(armature):
    return {b.name: {"basis": matrix_rows(b.matrix_basis), "rotation_mode": b.rotation_mode,
                     "properties": numeric_properties(b)} for b in armature.pose.bones}


def driver_payload(owner):
    ad = owner.animation_data
    if ad is None:
        return {}
    return {f"{fc.data_path}:{fc.array_index}": {"curve": curve_payload(fc),
        "expression": fc.driver.expression,
        "type": fc.driver.type, "use_self": fc.driver.use_self,
        "mute": fc.mute, "variables": [{"name": v.name, "type": v.type,
            "targets": [{"settings": scalar_rna(t), "id": t.id.name if t.id else None, "id_type": t.id_type,
                         "data_path": t.data_path, "bone_target": t.bone_target,
                         "transform_type": t.transform_type,
                         "transform_space": t.transform_space,
                         "rotation_mode": t.rotation_mode} for t in v.targets]}
            for v in fc.driver.variables]} for fc in ad.drivers}


def scene_state(rig=None, game=None, mesh=None):
    """Reusable immutable-source comparison for upgrade functions, not a saver.

    Existing action/binding/pose entries must remain exact; added reference-only
    actions and objects can be separately approved without weakening those pins.
    """
    rig = rig or bpy.data.objects["WARLOCK_CTRL"]
    game = game or bpy.data.objects["WARLOCK_GAME"]
    mesh = mesh or next(o for o in bpy.data.objects if o.type == "MESH" and
                       any(m.type == "ARMATURE" and m.object == game for m in o.modifiers))
    actions = action_payload()
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    native = game.evaluated_get(graph)
    prop_points = {}
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.get("authoring_reference_only"):
            continue
        evaluated = obj.evaluated_get(graph)
        temporary = evaluated.to_mesh()
        prop_points[obj.name] = [list(evaluated.matrix_world @ v.co) for v in temporary.vertices]
        evaluated.to_mesh_clear()
    keyed_rocket = [f"{a['name']}:{c['path']}:{c['index']}" for a in actions for layer in a["layers"]
                   for strip in layer["strips"] for bag in strip["bags"] for c in bag["curves"]
                   if 'pose.bones["CTRL-rocket"]' in c["path"]]
    return {"actions": {a["name"]: digest(a) for a in actions},
            "action_counts": {a["name"]: {"curves": sum(len(b["curves"]) for l in a["layers"]
                for s in l["strips"] for b in s["bags"]), "fake_user": a["fake_user"]} for a in actions},
            "bindings": animation_bindings(), "control_pose": pose_payload(rig),
            "game_pose": pose_payload(game), "control_drivers": driver_payload(rig),
            "game_skeleton": digest(skeleton(game)),
            "body_geometry_weights": snapshot(rig, game, mesh)["body_geometry_weights"],
            "object_transforms": {o.name: matrix_rows(o.matrix_world) for o in (rig, game, mesh)},
            "scene_frame": bpy.context.scene.frame_current,
            "evaluated_game_world": {b.name: matrix_rows(native.matrix_world @ b.matrix)
                                     for b in native.pose.bones},
            "evaluated_prop_points": prop_points, "keyed_rocket_channels": keyed_rocket}


def evaluated_errors(before, after):
    bones = before["evaluated_game_world"]
    candidate = after["evaluated_game_world"]
    if any(name not in candidate for name in bones):
        return {"game_world_matrix_error": 1e30, "prop_world_error_m": 1e30}
    game_error = max((abs(m[r][c] - candidate[name][r][c]) for name, m in bones.items()
                      for r in range(4) for c in range(4)), default=0.0)
    prop_error = 0.0
    for name, points in before["evaluated_prop_points"].items():
        other = after["evaluated_prop_points"].get(name)
        if other is None or len(points) != len(other):
            return {"game_world_matrix_error": game_error, "prop_world_error_m": 1e30}
        prop_error = max(prop_error, max((math.dist(a, b) for a, b in zip(points, other)), default=0.0))
    return {"game_world_matrix_error": game_error, "prop_world_error_m": prop_error}


def active_source_animation(state):
    return [name for name, lane in state["bindings"].items()
            if lane and (lane["action"] is not None or lane["tracks"])]


def baseline_differences(before, after, allow_rocket_pivot=False):
    """Return every altered or missing original lane, allowing added lanes."""
    differences = {}
    errors = evaluated_errors(before, after)
    for field in ("actions", "bindings", "control_drivers", "control_pose", "game_pose", "object_transforms"):
        altered = []
        for name, value in before[field].items():
            candidate = after[field].get(name)
            if field in ("control_pose", "game_pose") and candidate is not None:
                # New options are allowed; existing animated properties and TRS
                # must remain byte-for-byte equal to the source scene.
                same = (candidate["basis"] == value["basis"] and
                        candidate["rotation_mode"] == value["rotation_mode"] and
                        all(candidate["properties"].get(k) == v for k, v in value["properties"].items()))
                if (not same and allow_rocket_pivot and field == "control_pose" and name == "CTRL-rocket"
                        and not before["keyed_rocket_channels"]
                        and not active_source_animation(before)
                        and candidate["rotation_mode"] == value["rotation_mode"]
                        and all(candidate["properties"].get(k) == v for k, v in value["properties"].items())
                        and max(errors.values()) <= 2e-5):
                    # The sole allowed TRS change is a rest-pivot relocation on
                    # an unkeyed rocket control, independently proven to retain
                    # every native pose and evaluated launcher/rocket vertex.
                    same = True
            else:
                same = name in after[field] and candidate == value
            if not same:
                altered.append(name)
        if altered:
            differences[field] = altered
    for field in ("game_skeleton", "body_geometry_weights", "scene_frame"):
        if before[field] != after[field]:
            differences[field] = {"before": before[field], "after": after[field]}
    if max(errors.values()) > 2e-5:
        differences["evaluated_pose"] = errors
    return differences


def snapshot(rig, game, mesh):
    return {
        "game_skeleton": digest(skeleton(game)),
        "game_basis": digest([(b.name, matrix_rows(b.matrix_basis), b.rotation_mode)
                               for b in game.pose.bones]),
        "control_basis": digest([(b.name, matrix_rows(b.matrix_basis), b.rotation_mode,
                                   {k: b[k] for k in b.keys()
                                    if isinstance(b[k], (float, int, bool))})
                                  for b in rig.pose.bones]),
        "body_geometry_weights": digest({"matrix": matrix_rows(mesh.matrix_world),
            "vertices": [(list(v.co), [(g.group, g.weight) for g in v.groups])
                         for v in mesh.data.vertices],
            "groups": [g.name for g in mesh.vertex_groups],
            "polygons": [list(p.vertices) for p in mesh.data.polygons]}),
        "actions": digest(action_payload()),
        "animation_bindings": digest(animation_bindings()),
        "object_transforms": digest({o.name: matrix_rows(o.matrix_world) for o in (rig, game, mesh)}),
    }


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evaluated_pose(game, mesh):
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    evaluated_game, evaluated_mesh = game.evaluated_get(graph), mesh.evaluated_get(graph)
    temporary = evaluated_mesh.to_mesh()
    points = [(evaluated_mesh.matrix_world @ v.co).copy() for v in temporary.vertices]
    evaluated_mesh.to_mesh_clear()
    return {b.name: (evaluated_game.matrix_world @ b.matrix).copy()
            for b in evaluated_game.pose.bones}, points


def production_hashes():
    process = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    names = process.stdout.decode("utf-8").split("\0")
    # Every tracked runtime or native production input, not a hand-picked sample.
    roots = {"units", "scripts", "resource_packages", "fx", "materials", "child_materials",
             "textures", "animation", "animations", "wwise", "audio_src", "dialogue",
             "sound", "breed", "ai", "lua", "lua_preprocessor_defines.config"}
    result = {}
    for name in names:
        if not name:
            continue
        path = Path(name)
        if (path.parts[0] in roots or path.suffix in {".lua", ".mod", ".bones",
                ".animation", ".animation_state_machine", ".unit", ".fbx", ".timpani_bank"}):
            result[name] = sha(ROOT / name)
    return result


def capture_scene_baseline(source):
    source = Path(source).resolve()
    source_hash = sha(source)
    bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
    state = scene_state()
    if sha(source) != source_hash:
        raise AssertionError("Baseline input changed while reading")
    return {"source": str(source), "source_sha256": source_hash,
            "state_sha256": digest(state), "state": state}


def run(options):
    source = options.rig.resolve()
    input_hash = sha(source)
    production_before = production_hashes()
    if options.capture_baseline:
        baseline = capture_scene_baseline(source)
        baseline["schema"] = 2
        baseline["production_sources"] = production_before
        if options.output.exists():
            if json.loads(options.output.read_text(encoding="utf-8")) != baseline:
                raise FileExistsError("Refusing to overwrite a different immutable baseline")
        else:
            options.output.parent.mkdir(parents=True, exist_ok=True)
            options.output.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
        print("WARLOCK_PRESERVATION_BASELINE", str(options.output), baseline["state_sha256"])
        return
    prior_baseline = capture_scene_baseline(options.baseline_rig) if options.baseline_rig else None
    bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
    rig, game = (bpy.data.objects[n] for n in ("WARLOCK_CTRL", "WARLOCK_GAME"))
    mesh = next(o for o in bpy.data.objects if o.type == "MESH" and
                any(m.type == "ARMATURE" and m.object == game for m in o.modifiers))
    original = snapshot(rig, game, mesh)
    manifest = json.loads(rig["warlock_control_manifest"])
    checks = []

    def check(name, passed, **details):
        checks.append({"name": name, "passed": bool(passed), **details})
        print(("PASS " if passed else "FAIL ") + name)

    if prior_baseline:
        saved_state = scene_state(rig, game, mesh)
        differences = baseline_differences(prior_baseline["state"], saved_state,
                                           allow_rocket_pivot=options.allow_rocket_pivot_migration)
        check("saved_candidate_preserves_original_actions_nla_poses_skin_and_game_rest",
              not differences, baseline_source=prior_baseline["source"],
              baseline_sha256=prior_baseline["source_sha256"],
              baseline_state_sha256=prior_baseline["state_sha256"], differences=differences,
              preserved_actions=prior_baseline["state"]["actions"],
              preserved_control_driver_count=len(prior_baseline["state"]["control_drivers"]))
        if options.allow_rocket_pivot_migration:
            errors = evaluated_errors(prior_baseline["state"], saved_state)
            check("unkeyed_rocket_pivot_migration_retains_all_native_and_prop_world_poses",
                  not prior_baseline["state"]["keyed_rocket_channels"] and
                  not active_source_animation(prior_baseline["state"]) and max(errors.values()) <= 2e-5,
                  source_keyed_rocket_channels=prior_baseline["state"]["keyed_rocket_channels"],
                  source_active_animation_bindings=active_source_animation(prior_baseline["state"]),
                  **errors)

    baseline_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout.decode().strip()
    original_names = [n for n in production_before if n.startswith("units/")]
    baseline_native = {name: hashlib.sha256(subprocess.run(
        ["git", "show", f"{baseline_commit}:{name}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout).hexdigest()
        for name in original_names}
    original_clips = [name for name in original_names if
        name.startswith("units/warlock_bombardier/anims/") and name.endswith(".fbx")]
    check("original_13_clip_pairs_match_reviewed_git_head_exactly",
        len(original_clips) == 13 and all(production_before[n] == baseline_native[n]
            for clip in original_clips for n in (clip, str(Path(clip).with_suffix(".animation")).replace("\\", "/"))),
        reference_commit=baseline_commit, clips=len(original_clips),
        sidecars=len(original_clips), baseline_sha256=digest(baseline_native))
    check("all_native_model_skeleton_controller_sources_match_reviewed_git_head",
        all(production_before[n] == value for n, value in baseline_native.items()),
        reference_commit=baseline_commit, checked_native_files=len(baseline_native),
        changed=[n for n, value in baseline_native.items() if production_before[n] != value])

    shipping = ROOT / "units/warlock_bombardier/warlock_bombardier_3p.fbx"
    check("body_source_matches_manifest", sha(shipping) == manifest["sources"]["body_sha256"])
    # Import into a disposable scene copy and compare original FBX rest values;
    # no builder-calculated signature is accepted as the reference oracle.
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    prior = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(shipping), use_anim=False,
        automatic_bone_orientation=False, ignore_leaf_bones=False)
    imported = [o for o in bpy.data.objects if o not in prior]
    shipping_game = next(o for o in imported if o.type == "ARMATURE")
    expected = skeleton(shipping_game)
    actual = skeleton(game)
    check("138_ordered_game_rest_bones_match_shipping_exactly", len(actual) == 138 and actual == expected,
          game_bones=len(actual), shipping_bones=len(expected),
          game_signature=digest(actual), shipping_signature=digest(expected))
    check("body_topology_unchanged", len(mesh.data.vertices) == 29123,
          vertices=len(mesh.data.vertices))

    weighted = {g.name: set() for g in mesh.vertex_groups}
    for v in mesh.data.vertices:
        for influence in v.groups:
            if influence.weight > 1e-8:
                weighted[mesh.vertex_groups[influence.group].name].add(v.index)
    face = {b.name: len(weighted.get(b.name, ())) for b in game.data.bones
            if re.search(r"^j_(?:left|right)?(?:tongue|jaw|mouth|nose|ear|eyebrow|eyelid|eye)",
                         b.name.lower())}
    tongue = [n for n in face if "tongue" in n.lower()]
    for obj in imported:
        bpy.data.objects.remove(obj, do_unlink=True)
    check("reference_import_does_not_modify_candidate", snapshot(rig, game, mesh) == original)

    # Give the scene real custom keys and an unkeyed correction pose; decorators
    # must retain these complete action payloads, not merely their action count.
    rig.animation_data_create()
    fixture = bpy.data.actions.new("WarlockPreservationCustomPoseFixture")
    fixture.use_fake_user = True
    rig.animation_data.action = fixture
    ctrl = rig.pose.bones["ORG-j_lefthandindex1"]
    ctrl.rotation_euler[0] = .123
    ctrl.keyframe_insert(data_path="rotation_euler", frame=1, group="Preserved custom correction")
    ctrl.rotation_euler[0] = .234
    ctrl.keyframe_insert(data_path="rotation_euler", frame=9, group="Preserved custom correction")
    ctrl.rotation_euler[1] = .035
    fixture.pose_markers.new("Retained custom pose marker").frame = 5
    fixture_curves = [c for layer in fixture.layers for strip in layer.strips
                      for bag in strip.channelbags for c in bag.fcurves]
    fixture_curves[0].modifiers.new("CYCLES")
    nla_fixture = fixture.copy()
    nla_fixture.name = "WarlockPreservationNlaFixture"
    track = rig.animation_data.nla_tracks.new()
    track.name = "Retained artist correction layer"
    strip = track.strips.new("Retained additive custom pose", 1, nla_fixture)
    strip.blend_type = "ADD"
    strip.influence = .2
    strip.use_animated_influence = False
    strip.scale = 1.25
    check("bound_action_and_unmuted_nla_fixture_include_keys_modifier_group_and_marker",
          rig.animation_data.action == fixture and not track.mute and not strip.mute and
          strip.action == nla_fixture and len(fixture.pose_markers) == 1 and
          bool(fixture_curves[0].modifiers) and fixture_curves[0].group is not None)
    rig.update_tag()
    bpy.context.view_layer.update()
    with_custom_pose = snapshot(rig, game, mesh)

    ui = load_module("warlock_preservation_ui", Path(__file__).with_name("warlock_rig_ui.py"))
    ui.register()
    ui.register()
    ui.unregister()
    after_ui = snapshot(rig, game, mesh)
    check("ui_repeat_registration_preserves_custom_tracks_and_pose",
          after_ui == with_custom_pose, before=with_custom_pose, after=after_ui)

    if options.exercise_widgets:
        widget_module = load_module("warlock_preservation_widgets",
                                    Path(__file__).with_name("control_widgets.py"))
        collection = bpy.data.collections.get("Warlock custom curve widgets")
        assert collection is not None
        groups = manifest["groups"]
        before_widgets = snapshot(rig, game, mesh)
        widget_module.apply_widgets(rig, game, mesh, groups, collection)
        after_widgets = snapshot(rig, game, mesh)
        # UI geometry must not alter a posed controller or its existing keys.
        check("widget_revision_preserves_existing_tracks_game_and_skin",
              after_widgets == before_widgets,
              before=before_widgets, after=after_widgets)

        widget_report = json.loads(rig["warlock_widget_manifest"])
        expected_twists = ["CTRL-forearm-twist-left", "CTRL-forearm-twist-right"]
        visible_twists = sorted(n for n in widget_report["twist_spheres"]
                                if not rig.pose.bones[n].bone.hide)
        supported_roll_bones = sorted(b.name for b in game.data.bones if "roll" in b.name)
        check("only_native_supported_twist_spheres_exposed", visible_twists == expected_twists,
              visible_controls=visible_twists, native_roll_channels=supported_roll_bones)
        for side in ("left", "right"):
            name = "CTRL-forearm-twist-" + side
            pb = rig.pose.bones[name]
            basis = pb.matrix_basis.copy()
            rig.update_tag()
            before_bones, before_points = evaluated_pose(game, mesh)
            pb.matrix_basis = basis @ Matrix.Rotation(math.radians(20), 4, "Y")
            rig.update_tag()
            after_bones, after_points = evaluated_pose(game, mesh)
            displacement = max((b - a).length for a, b in zip(before_points, after_points))
            hand = "j_" + side + "hand"
            wrist_motion = (after_bones[hand].translation - before_bones[hand].translation).length
            changed = [n for n in before_bones if max(
                abs(before_bones[n][r][c] - after_bones[n][r][c])
                for r in range(4) for c in range(4)) > 1e-5]
            pb.matrix_basis = basis
            rig.update_tag()
            evaluated_pose(game, mesh)
            check(side + "_native_twist_moves_weighted_skin_without_moving_hand",
                  displacement > .001 and wrist_motion < 1e-5 and
                  changed == ["j_" + side + "forearmroll"],
                  skin_max_displacement_m=displacement, wrist_translation_m=wrist_motion,
                  changed_game_bones=changed)
        check("twist_measurements_restore_existing_custom_pose_and_keys",
              snapshot(rig, game, mesh) == after_widgets)

    production_after = production_hashes()
    check("all_runtime_and_native_source_bytes_unchanged", production_before == production_after,
          checked_files=len(production_before), source_manifest_sha256=digest(production_before))
    check("input_artist_blend_unchanged", sha(source) == input_hash, sha256=input_hash)
    if prior_baseline:
        check("original_baseline_blend_unchanged", sha(prior_baseline["source"]) ==
              prior_baseline["source_sha256"], sha256=prior_baseline["source_sha256"])
    report = {"schema": 1, "scope": "Blender authoring preservation; zero game/native playback samples",
        "source": str(source), "source_sha256": input_hash,
        "production_sources": production_before, "face_channels": face,
        "reviewed_native_source_reference": {"commit": baseline_commit, "sources": baseline_native},
        "tongue_support": "existing channel" if tongue else
            "No existing tongue bone; independent tongue deformation needs artist source support.",
        "checks": checks, "passed": all(c["passed"] for c in checks)}
    if prior_baseline:
        report["original_artist_baseline"] = {k: v for k, v in prior_baseline.items() if k != "state"}
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["passed"]:
        raise AssertionError("Preservation checks failed: inspect report")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rig", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--exercise-widgets", action="store_true")
    parser.add_argument("--baseline-rig", type=Path,
                        help="Require preservation of all existing actions, NLA, poses and native data from this blend")
    parser.add_argument("--capture-baseline", action="store_true",
                        help="Read only: write an immutable compact source scene fingerprint instead of running fixtures")
    parser.add_argument("--allow-rocket-pivot-migration", action="store_true",
                        help="Permit only an unkeyed CTRL-rocket basis change with <=20um native/prop pose proof")
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    run(parser.parse_args(args))
