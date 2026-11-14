"""Build a portable, isolated Blender library of the original compiled clips.

Ordinary Python prepares decoded native samples, then Blender creates the
reference-only library. Neither stage edits the artist rig or game sources.
The clip browser is an authoring reference, not a native state-machine emulator.
"""
from __future__ import annotations

import argparse
from array import array
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
UNIT = "units/warlock_bombardier/warlock_bombardier_3p"
COLLECTION = "WARLOCK_REFERENCE_LIBRARY"
ARMATURE = "WARLOCK_REFERENCE_GAME"
PREFIX = "WARLOCK_REFERENCE::"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def prepare(args):
    sys.path.insert(0, str(ROOT / "tools/animation_rig"))
    sys.path.insert(0, str(ROOT / "tools/tests"))
    from verify_compiled_animation import decode_animation, compiled_world, SDK_BINARY_SHA256
    from test_warlock_weapon_pipeline import compiled_unit_structure, compiled_node_index
    from compile_paths import indexed_resources, validate_probe

    probe = args.probe.resolve()
    validate_probe(ROOT, probe)
    validate_probe(ROOT, args.output.parent.resolve())
    receipt = json.loads((probe / "input_receipt.json").read_text(encoding="utf8"))
    require(receipt["sdk_executable_sha256"] == SDK_BINARY_SHA256 and
            sha(receipt["sdk_executable_path"]) == SDK_BINARY_SHA256,
            "Compiled reference does not bind the independently audited SDK")
    hashes = receipt["production_source_sha256"]
    for name, digest in hashes.items():
        require(sha(ROOT / name) == digest, "Compiled reference source changed: " + name)
    require("Compile resulted in success!" in
            (probe / "reference/compiler.stdout.log").read_text(encoding="utf8"),
            "Original reference compile did not succeed")
    unit_path = indexed_resources(ROOT, probe, probe / "reference/data", [UNIT + ".unit"])[0]
    unit = compiled_unit_structure(unit_path.read_bytes())
    names = re.findall(r'"([^"\n]+)"', (ROOT / (UNIT + ".bones")).read_text(encoding="utf8"))
    require(len(names) == len(set(names)) == 138, "Original skeleton is not 138 ordered bones")
    asm = (ROOT / (UNIT + ".state_machine")).read_text(encoding="utf8")
    referenced = set(re.findall(r'"units/warlock_bombardier/anims/([^"\n]+)"', asm))
    inventory = json.loads((probe / "original-clips.json").read_text(encoding="utf8"))["clips"]
    require(len(inventory) == 13 and len(referenced) == 12,
            "Original clip/state-machine inventory changed")
    result = {"schema": 1, "purpose": "reference-only-original-compiled-clips",
        "sampling": "decoded binary-proven SDK Hermite; no native Unit pose captures",
        "native_unit_pose_captures": 0, "fps": 60, "key_sample_fps": 240,
        "bone_names": names, "source_hashes": hashes,
        "compiled_unit_sha256": sha(unit_path), "clips": [],
        "sdk_executable_sha256": SDK_BINARY_SHA256,
        "input_receipt_sha256": sha(probe / "input_receipt.json"),
        "decoder_sha256": sha(Path(__file__).with_name("verify_compiled_animation.py")),
        "unit_nodes": [{"parent_type": node.parent_type, "parent_index": node.parent_index,
                        "world_transform": node.world_transform} for node in unit.nodes],
        "bone_node_indices": [compiled_node_index(unit, name) for name in names]}
    for entry in inventory:
        stem = Path(entry["clip"]).stem
        resource = "units/warlock_bombardier/anims/" + stem
        path = indexed_resources(ROOT, probe, probe / "reference/data", [resource + ".animation"])[0]
        animation = decode_animation(path.read_bytes())
        require(animation["bones"] == 138, "Compiled clip uses another skeleton")
        require(sha(ROOT / (resource + ".fbx")) == entry["fbx_sha256"] and
                sha(ROOT / (resource + ".animation")) == entry["sidecar_sha256"],
                "Original source pair changed: " + stem)
        duration = animation["duration"]
        record = {"id": stem, "action": PREFIX + stem,
            "duration": duration, "fps": 60, "start": 1, "end": 1 + duration * 60,
            "asm_referenced": stem in referenced, "animation": animation,
            "compiled_animation_sha256": sha(path), "source_fbx_sha256": entry["fbx_sha256"],
            "source_sidecar_sha256": entry["sidecar_sha256"]}
        # Independently bind the compact hierarchy serializer to the established
        # decoded reconstruction before Blender consumes it.
        for time in (0, duration * .271, duration * .679, duration):
            actual = reference_world(result, record, time)
            expected = compiled_world(unit, names, animation, time)
            for name, matrix in zip(names, actual):
                require(max(abs(matrix[r][c] - expected[name][r][c] *
                                (.01 if r < 3 and c < 3 else 1))
                            for r in range(4) for c in range(4)) < 1e-12,
                        "Compact reference reconstruction differs from audited decoder")
        result["clips"].append(record)
        print("WARLOCK_REFERENCE_DECODED", stem, duration, flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(args.output, "wt", encoding="utf8", compresslevel=6) as stream:
        json.dump(result, stream, separators=(",", ":"), allow_nan=False)
    print("WARLOCK_REFERENCE_SAMPLES", args.output, sha(args.output), flush=True)


def reference_world(samples, clip, time):
    """Reconstruct the audited decoder hierarchy from compact serialized data."""
    from verify_compiled_animation import sample_compiled, transform, matrix_multiply
    names = samples["bone_names"]
    indices = {node: i for i, node in enumerate(samples["bone_node_indices"])}
    memo = {}
    def visit(index):
        if index in memo:
            return memo[index]
        node = samples["unit_nodes"][index]
        if index in indices:
            tracks = clip["animation"]["tracks"][indices[index]]
            local = transform(sample_compiled(tracks["position"], time),
                              sample_compiled(tracks["rotation"], time, True),
                              sample_compiled(tracks["scale"], time))
            parent = visit(node["parent_index"]) if node["parent_type"] == 1 else (
                (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))
            world = matrix_multiply(parent, local)
        else:
            world = node["world_transform"]
        memo[index] = world
        return world
    return [[list(float(cell) * (.01 if r < 3 and c < 3 else 1)
                  for c, cell in enumerate(row)) for r, row in enumerate(visit(index))]
            for index in samples["bone_node_indices"]]


def build(args):
    import bpy
    from mathutils import Matrix, Vector

    sys.path.insert(0, str(ROOT / "tools/animation_rig"))
    sys.path.insert(0, str(ROOT / "tools/hose_lab"))
    from export_animation import independent_import, select_scene
    from compile_paths import validate_probe

    require(bpy.app.background, "Build the reference library in a separate background Blender process")
    args.output = args.output.resolve()
    args.samples = args.samples.resolve()
    validate_probe(ROOT, args.output.parent.resolve())
    require(not args.output.exists(), "Refuse to overwrite an existing reference library")
    # Blender's library writer interprets a relative path differently from
    # pathlib. Prove the absolute destination before the expensive bake.
    from uuid import uuid4
    args.output.parent.mkdir(parents=True, exist_ok=True)
    trial = args.output.parent / ("write-preflight-" + uuid4().hex + ".blend")
    probe_collection = bpy.data.collections.new("WARLOCK_REFERENCE_WRITE_PREFLIGHT")
    try:
        bpy.data.libraries.write(str(trial), {probe_collection}, compress=True)
        require(trial.is_file() and trial.stat().st_size > 0, "Library output preflight failed")
    finally:
        if trial.exists():
            trial.unlink()
        bpy.data.collections.remove(probe_collection)
    print("WARLOCK_REFERENCE_WRITE_PREFLIGHT", str(args.output), flush=True)
    with gzip.open(args.samples, "rt", encoding="utf8") as stream:
        samples = json.load(stream)
    require(samples["schema"] == 1 and len(samples["clips"]) == 13, "Invalid reference samples")
    for clip in samples["clips"]:
        for track in clip["animation"]["tracks"]:
            for channel, keys in track.items():
                track[channel] = [(time, tuple(value)) for time, value in keys]
    for name, digest in samples["source_hashes"].items():
        require(sha(ROOT / name) == digest, "Reference source changed before library build: " + name)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene, objects, armature = independent_import(ROOT / (UNIT + ".fbx"), animation=False)
    select_scene(scene)
    names = samples["bone_names"]
    require(set(armature.data.bones) and [bone.name for bone in armature.data.bones] == names,
            "Imported body has a different ordered skeleton")
    armature.name = ARMATURE
    collection = bpy.data.collections.new(COLLECTION)
    scene.collection.children.link(collection)
    for obj in objects:
        for old in list(obj.users_collection):
            old.objects.unlink(obj)
        collection.objects.link(obj)
        obj["warlock_reference_only"] = True
        obj.hide_select = True
        obj.hide_render = True
        if obj.type == "MESH":
            # Geometry and weights remain the approved source. A neutral preview
            # avoids any external texture paths in this portable library.
            obj.data.materials.clear()
    for image in list(bpy.data.images):
        if image.users == 0:
            bpy.data.images.remove(image)
    armature.hide_select = True
    armature.show_in_front = False
    armature.data.display_type = "STICK"
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.context.view_layer.update()
    inverses = {name: armature.matrix_world.inverted() for name in names}
    ordered = sorted(armature.pose.bones, key=lambda b: len(b.parent_recursive))
    inverse_rest = {bone.name: (armature.matrix_world @ bone.matrix_local).inverted()
                    for bone in armature.data.bones}
    skin = []
    for mesh in (obj for obj in objects if obj.type == "MESH"):
        group_names = {group.index: group.name for group in mesh.vertex_groups}
        vertices = []
        for vertex in mesh.data.vertices:
            influences = [(group_names[group.group], group.weight) for group in vertex.groups
                          if group_names[group.group] in inverse_rest and group.weight > 0]
            total = sum(weight for _, weight in influences)
            require(abs(total - 1) < 1e-4, "Reference vertex weights are not normalized")
            vertices.append((mesh.matrix_world @ vertex.co,
                             [(name, weight / total) for name, weight in influences]))
        skin.append((mesh, vertices))
    manifest = {key: value for key, value in samples.items()
                if key not in {"clips", "unit_nodes", "bone_node_indices"}}
    manifest.update({"collection": COLLECTION, "armature": ARMATURE,
        "reference_only": True, "scene_fps": 60, "clips": [],
        "body_geometry_and_weights": "approved original shipping FBX, unchanged",
        "artist_actions_modified": False, "native_state_machine_emulation": False,
        "samples_sha256": sha(args.samples)})
    report = {"schema": 1, "status": "pending", "clips": [], "native_unit_pose_captures": 0,
              "blender": bpy.app.version_string, "script_sha256": sha(__file__),
              "samples_sha256": sha(args.samples), "world_head_tolerance_m": .0005,
              "world_axis_tolerance_m": .0005, "weighted_skin_tolerance_m": .0005}
    scene.render.fps = 60
    scene.render.fps_base = 1
    scene.frame_start = 1
    if armature.animation_data:
        armature.animation_data_clear()
    for clip in samples["clips"]:
        # Quarter-frame keys and independent eighth-frame interpolation checks.
        # The compact decoded channels avoid retaining a multi-gigabyte corpus
        # of world-matrix JSON for all clips.
        times = [i / 480 for i in range(math.floor(clip["duration"] * 480) + 1)]
        if clip["duration"] - times[-1] > 1e-7:
            times.append(clip["duration"])
        frames = [{"frame": 1 + time * 60, "key": i % 2 == 0 or i == len(times) - 1,
                   "world": reference_world(samples, clip, time)}
                  for i, time in enumerate(times)]
        action = bpy.data.actions.new(clip["action"])
        action.use_fake_user = True
        action["warlock_reference_only"] = True
        action["warlock_reference_clip"] = clip["id"]
        animation_data = armature.animation_data_create()
        animation_data.action = action
        slot = action.slots.new("OBJECT", armature.name)
        animation_data.action_slot = slot
        layer = action.layers.new("Reference motion")
        strip = layer.strips.new(type="KEYFRAME")
        bag = strip.channelbag(slot, ensure=True)
        # Each saved key is derived from the decoded WORLD pose, converted via
        # Blender's original rest hierarchy; native local TRS is not copied as
        # Blender pose basis.
        previous = {}
        channels = ("location", "rotation_quaternion", "scale")
        values = {bone.name: {channel: [] for channel in channels} for bone in ordered}
        curves = {bone.name: {channel: [] for channel in channels} for bone in ordered}
        def pose_values(snapshot, initial=False):
            world = {name: Matrix(matrix) for name, matrix in zip(names, snapshot["world"])}
            result = {}
            for bone in ordered:
                preceding = previous.get(bone.name) if initial else __import__("mathutils").Quaternion(
                    tuple(curve.evaluate(snapshot["frame"])
                          for curve in curves[bone.name]["rotation_quaternion"]))
                bone.rotation_mode = "QUATERNION"
                kwargs = {"invert": True}
                if bone.parent:
                    kwargs.update(parent_matrix=inverses[bone.name] @ world[bone.parent.name],
                                  parent_matrix_local=bone.parent.bone.matrix_local)
                bone.matrix_basis = bone.bone.convert_local_to_pose(
                    inverses[bone.name] @ world[bone.name], bone.bone.matrix_local, **kwargs)
                if preceding is not None:
                    bone.rotation_quaternion.make_compatible(preceding)
                previous[bone.name] = bone.rotation_quaternion.copy()
                result[bone.name] = {channel: tuple(getattr(bone, channel)) for channel in channels}
            return result
        for snapshot in frames:
            if snapshot["key"]:
                for name, record in pose_values(snapshot, initial=True).items():
                    for channel, vector in record.items():
                        values[name][channel].append((snapshot["frame"], vector))
        linear = bpy.types.Keyframe.bl_rna.properties["interpolation"].enum_items["LINEAR"].value
        for bone in ordered:
            for channel in channels:
                records = values[bone.name][channel]
                for index in range(4 if channel == "rotation_quaternion" else 3):
                    curve = bag.fcurves.new(bone.path_from_id(channel), index=index, group_name=bone.name)
                    curve.keyframe_points.add(len(records))
                    coordinates = array("f", (value for frame, vector in records for value in (frame, vector[index])))
                    curve.keyframe_points.foreach_set("co", coordinates)
                    curve.keyframe_points.foreach_set("interpolation", array("i", [linear] * len(records)))
                    curve.extrapolation = "CONSTANT"
                    curve.update()
                    curves[bone.name][channel].append(curve)
        del values
        adaptive_keys = 0
        for refinement in range(8):
            head_error = axis_error = 0.0
            worst_axis = None
            key_head = check_head = 0.0
            skin_error = 0.0
            skin_comparisons = 0
            comparisons = 0
            bad = []
            for snapshot_index, snapshot in enumerate(frames):
                scene.frame_set(math.floor(snapshot["frame"]), subframe=snapshot["frame"] % 1)
                graph = bpy.context.evaluated_depsgraph_get()
                evaluated = armature.evaluated_get(graph)
                frame_head = frame_axis = 0.0
                for name, matrix in zip(names, snapshot["world"]):
                    expected = Matrix(matrix)
                    actual = evaluated.matrix_world @ evaluated.pose.bones[name].matrix
                    h = (actual.translation - expected.translation).length
                    a = max((actual @ Vector(tuple(.1 if i == axis else 0 for i in range(3))) -
                             expected @ Vector(tuple(.1 if i == axis else 0 for i in range(3)))).length
                            for axis in range(3))
                    frame_head = max(frame_head, h)
                    frame_axis = max(frame_axis, a)
                    head_error = max(head_error, h)
                    if a > axis_error:
                        axis_error = a
                        worst_axis = {"bone": name, "frame": snapshot["frame"], "key": snapshot["key"]}
                    if snapshot["key"]:
                        key_head = max(key_head, h)
                    else:
                        check_head = max(check_head, h)
                    comparisons += 1
                if (frame_head >= report["world_head_tolerance_m"] or
                        frame_axis >= report["world_axis_tolerance_m"]):
                    require(not snapshot["key"], "Native decoded reference does not fit Blender local TRS")
                    bad.append(snapshot)
                if snapshot_index in {0, len(frames) // 2, len(frames) - 1}:
                    matrices = {name: Matrix(matrix) @ inverse_rest[name]
                                for name, matrix in zip(names, snapshot["world"])}
                    for mesh, vertices in skin:
                        result = mesh.evaluated_get(graph)
                        evaluated_mesh = result.to_mesh()
                        try:
                            require(len(evaluated_mesh.vertices) == len(vertices),
                                    "Reference modifier changed source vertex count")
                            for vertex, (point, weights) in zip(evaluated_mesh.vertices, vertices):
                                expected = sum((matrices[name] @ point * weight for name, weight in weights),
                                               Vector((0, 0, 0)))
                                actual = result.matrix_world @ vertex.co
                                skin_error = max(skin_error, (actual - expected).length)
                                skin_comparisons += 1
                        finally:
                            result.to_mesh_clear()
            if not bad:
                break
            require(refinement < 7, "Adaptive reference refinement exceeded its bounded depth")
            old_keys = sorted(snapshot["frame"] for snapshot in frames if snapshot["key"])
            new_checks = {}
            inserts = []
            import bisect
            for snapshot in bad:
                index = bisect.bisect_left(old_keys, snapshot["frame"])
                require(0 < index < len(old_keys), "Invalid reference refinement interval")
                for frame in ((old_keys[index-1] + snapshot["frame"]) / 2,
                              (old_keys[index] + snapshot["frame"]) / 2):
                    new_checks[frame] = {"frame": frame, "key": False,
                        "world": reference_world(samples, clip, (frame - 1) / 60)}
                snapshot["key"] = True
                inserts.append((snapshot["frame"], pose_values(snapshot)))
                adaptive_keys += 1
            for frame, record in inserts:
                for name, channels_record in record.items():
                    for channel, vector in channels_record.items():
                        for curve, value in zip(curves[name][channel], vector):
                            key = curve.keyframe_points.insert(frame, value, options={"FAST"})
                            key.interpolation = "LINEAR"
            for curve in bag.fcurves:
                curve.update()
            frames.extend(new_checks.values())
            frames.sort(key=lambda snapshot: snapshot["frame"])
            print("WARLOCK_REFERENCE_REFINE", clip["id"], refinement + 1, len(bad), flush=True)
        require(head_error < report["world_head_tolerance_m"] and
                axis_error < report["world_axis_tolerance_m"] and
                skin_error < report["weighted_skin_tolerance_m"],
                f"Reference pose mismatch {clip['id']}: head {head_error}, axis {axis_error}, skin {skin_error}, "
                f"key head {key_head}, interpolation head {check_head}, worst axis {worst_axis}")
        record = {key: value for key, value in clip.items() if key != "animation"}
        record.update({"world_bone_comparisons": comparisons, "head_error_m": head_error,
                       "axis_error_m": axis_error, "key_head_error_m": key_head,
                       "interpolated_head_error_m": check_head,
                       "adaptive_keys_added": adaptive_keys,
                       "initial_key_sample_fps": 240, "initial_validation_sample_fps": 480,
                       "weighted_skin_error_m": skin_error, "weighted_skin_comparisons": skin_comparisons})
        record["worst_axis"] = worst_axis
        manifest["clips"].append(record)
        report["clips"].append(record)
        print("WARLOCK_REFERENCE_ACTION", json.dumps(record), flush=True)
    armature.animation_data.action = bpy.data.actions[manifest["clips"][0]["action"]]
    scene.frame_set(1)
    scene.frame_end = math.ceil(manifest["clips"][0]["end"])
    collection["warlock_reference_manifest"] = json.dumps(manifest, separators=(",", ":"))
    text = bpy.data.texts.new("WARLOCK_REFERENCE_MANIFEST.json")
    text.write(json.dumps(manifest, indent=2))
    text.use_module = False
    # A library write includes only the reviewed collection, its dependencies
    # and all reference actions; unrelated factory scene/datablocks are excluded.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    require(not args.output.exists(), "Refuse to overwrite an existing reference library")
    bpy.data.libraries.write(str(args.output), {collection, text, *bpy.data.actions},
                             fake_user=True, compress=True)
    report.update({"status": "reference-library-verified", "library_sha256": sha(args.output),
        "library_bytes": args.output.stat().st_size, "original_source_hashes": samples["source_hashes"],
        "total_world_bone_comparisons": sum(c["world_bone_comparisons"] for c in report["clips"]),
        "max_head_error_m": max(c["head_error_m"] for c in report["clips"]),
        "max_axis_error_m": max(c["axis_error_m"] for c in report["clips"]),
        "max_weighted_skin_error_m": max(c["weighted_skin_error_m"] for c in report["clips"]),
        "total_weighted_skin_comparisons": sum(c["weighted_skin_comparisons"] for c in report["clips"])})
    args.output.with_suffix(".json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf8")
    args.output.with_suffix(".verify.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    print("WARLOCK_REFERENCE_LIBRARY_VERIFIED", args.output, report["library_sha256"], flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--probe", type=Path)
    parser.add_argument("--samples", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None)
    if args.prepare:
        require(args.probe is not None, "--prepare requires --probe")
        prepare(args)
    else:
        require(args.samples is not None, "Blender build requires --samples")
        build(args)


if __name__ == "__main__":
    main()
