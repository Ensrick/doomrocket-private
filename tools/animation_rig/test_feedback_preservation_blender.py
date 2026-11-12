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


def action_payload():
    result = []
    for action in sorted(bpy.data.actions, key=lambda a: a.name):
        layers = []
        for layer in action.layers:
            strips = []
            for strip in layer.strips:
                bags = []
                for bag in getattr(strip, "channelbags", ()):
                    curves = []
                    for curve in bag.fcurves:
                        curves.append({"path": curve.data_path, "index": curve.array_index,
                            "extrapolation": curve.extrapolation,
                            "keys": [{"co": list(k.co), "left": list(k.handle_left),
                                      "right": list(k.handle_right),
                                      "left_type": k.handle_left_type,
                                      "right_type": k.handle_right_type,
                                      "interpolation": k.interpolation, "easing": k.easing,
                                      "amplitude": k.amplitude, "back": k.back,
                                      "period": k.period} for k in curve.keyframe_points],
                            "samples": [list(p.co) for p in curve.sampled_points]})
                    bags.append({"slot": bag.slot_handle, "curves": curves})
                strips.append({"type": strip.type, "bags": bags})
            layers.append({"name": layer.name, "strips": strips})
        result.append({"name": action.name,
            "slots": [(s.identifier, s.handle) for s in action.slots], "layers": layers})
    return result


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


def run(options):
    source = options.rig.resolve()
    input_hash = sha(source)
    production_before = production_hashes()
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
    ctrl = rig.pose.bones["ORG-j_lefthandindex1"]
    ctrl.rotation_euler[0] = .123
    ctrl.keyframe_insert(data_path="rotation_euler", frame=1)
    ctrl.rotation_euler[0] = .234
    ctrl.keyframe_insert(data_path="rotation_euler", frame=9)
    ctrl.rotation_euler[1] = .035
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
    report = {"schema": 1, "scope": "Blender authoring preservation; zero game/native playback samples",
        "source": str(source), "source_sha256": input_hash,
        "production_sources": production_before, "face_channels": face,
        "reviewed_native_source_reference": {"commit": baseline_commit, "sources": baseline_native},
        "tongue_support": "existing channel" if tongue else
            "No existing tongue bone; independent tongue deformation needs artist source support.",
        "checks": checks, "passed": all(c["passed"] for c in checks)}
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["passed"]:
        raise AssertionError("Preservation checks failed: inspect report")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rig", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--exercise-widgets", action="store_true")
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    run(parser.parse_args(args))
