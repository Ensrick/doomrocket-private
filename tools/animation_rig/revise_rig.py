"""Revise the delivered 1.1 scene without regenerating its animation rig.

Blender 5.2 --background --factory-startup --disable-autoexec --python-exit-code 1
  --python revise_rig.py -- --rig <delivered-1.1.blend>
  --first-rig <October-11.blend> --output <new-owned-directory>

The source pins deliberately reject arbitrary animator working scenes. Their
actions and custom poses must never be replaced by a generated handoff. Display
geometry comes from the first delivery; functioning mechanisms and actions come
from the delivered 1.1 scene. Source files are read-only and output must be new.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
CURRENT_SHA = "46b6971772af15fabc841eac450001988b70d29c0a2f758ef45442774777afb6"
FIRST_SHA = "e2b73978f1e2f9018212422ceb7bbea6244ae3c1e007540d64975d2114e06ffb"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main(options):
    from control_widgets import capture_original_widgets, apply_widgets
    from weapon_controls import upgrade_existing_weapon_controls
    from test_feedback_preservation_blender import (
        action_payload, digest, snapshot, scene_state, baseline_differences, evaluated_errors)

    source, first, output = (p.resolve() for p in
                             (options.rig, options.first_rig, options.output))
    require(sha(source) == CURRENT_SHA, "Revision input is not the delivered 1.1 scene")
    require(sha(first) == FIRST_SHA, "Display input is not the verified first delivery")
    require(not any(p.casefold() == "units" for p in output.parts),
            "Authoring output cannot be a production units directory")
    require(output not in (source.parent, first.parent), "Output must be separate from originals")
    require(not output.exists() or not any(output.iterdir()),
            "Use a new output directory; never replace saved animation work")

    bpy.ops.wm.open_mainfile(filepath=str(first), use_scripts=False)
    first_widgets = capture_original_widgets(bpy.data.objects["WARLOCK_CTRL"])
    first_widgets["source_sha256"] = FIRST_SHA
    bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
    rig, game = (bpy.data.objects[name] for name in ("WARLOCK_CTRL", "WARLOCK_GAME"))
    mesh = next(o for o in bpy.data.objects if o.type == "MESH" and any(
        mod.type == "ARMATURE" and mod.object == game for mod in o.modifiers))
    original = snapshot(rig, game, mesh)
    original_state = scene_state(rig, game, mesh)
    original_mode = bpy.context.mode
    original_active = bpy.context.view_layer.objects.active
    original_selection = {o.name for o in bpy.context.selected_objects}
    actions_before = digest(action_payload())
    manifest = json.loads(rig["warlock_control_manifest"])
    groups = manifest["groups"]
    widgets = bpy.data.collections["Warlock custom curve widgets"]

    weapon = upgrade_existing_weapon_controls(rig, game)
    display = apply_widgets(rig, game, mesh, groups, widgets, first_widgets=first_widgets)
    require(digest(action_payload()) == actions_before, "Revision changed original animation data")
    current = snapshot(rig, game, mesh)
    for field in ("game_skeleton", "game_basis", "body_geometry_weights", "actions"):
        require(current[field] == original[field], "Revision changed protected data: " + field)
    revised_state = scene_state(rig, game, mesh)
    # Moving a real pivot changes only this unkeyed authoring control's basis.
    # The guard refuses keyed rocket inputs and independently bounds all GAME
    # matrices and actual prop vertices; no action or custom property exception.
    differences = baseline_differences(original_state, revised_state, allow_rocket_pivot=True)
    require(not differences, "Revision changed existing actions, bindings or control poses: " + repr(differences))

    manifest.update(version="1.2", widgets=display, weapon_controls=weapon)
    manifest["revision_inputs"] = {
        "functional_scene_sha256": CURRENT_SHA,
        "first_display_scene_sha256": FIRST_SHA,
        "functional_scene_tools_sha256": dict(manifest["sources"]["tools_sha256"]),
        "preserves_existing_actions": True,
        "source_working_scenes_unchanged": True,
    }
    manifest["reference_playback"] = {
        "library": "reference/warlock_animation_reference.blend",
        "module": "reference_playback.py",
        "isolated_from_artist_actions": True,
        "native_state_machine_emulation": False,
    }
    names = set(manifest["sources"]["tools_sha256"]) | {
        "revise_rig.py", "control_widgets.py", "weapon_controls.py",
        "warlock_rig_ui.py", "reference_playback.py", "export_animation.py",
        "export_body.py", "test_feedback_preservation_blender.py"}
    for name in sorted(names):
        manifest["sources"]["tools_sha256"][name] = sha(TOOLS / name)
    rig["warlock_rig_version"] = "1.2"
    rig["warlock_tools_directory"] = str(output)
    rig["warlock_control_manifest"] = json.dumps(manifest)
    ui = bpy.data.texts.get("warlock_rig_ui.py") or bpy.data.texts.new("warlock_rig_ui.py")
    ui.clear()
    ui.write((TOOLS / "warlock_rig_ui.py").read_text(encoding="utf-8"))
    ui.use_module = False
    readme = bpy.data.texts.get("START HERE - Warlock animation rig")
    if readme:
        original_readme = readme.as_string()
        readme.clear()
        readme.write(original_readme + "\nRig 1.2: first-delivery control shapes, left red/right blue, "
                     "center yellow/settings lilac. Reference clips use a separate model "
                     "and independent clock; they never replace your actions.\n")
    # Editing helper frames may leave an invisible mechanism active. Restore
    # the delivered working context so the file opens on its animator controls.
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.context.view_layer.objects:
        obj.select_set(obj.name in original_selection)
    bpy.context.view_layer.objects.active = original_active
    if original_active and original_mode == "POSE":
        bpy.ops.object.mode_set(mode="POSE")
    output.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    destination = output / "WarlockEngineer_AnimationRig.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(destination), check_existing=False, compress=True)
    (output / "rig_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (output / "revision_receipt.json").write_text(json.dumps({
        "schema": 1, "rig_sha256": sha(destination), "rig_bytes": destination.stat().st_size,
        "functional_scene_sha256": CURRENT_SHA, "first_display_scene_sha256": FIRST_SHA,
        "first_widgets_sha256": first_widgets.get("display_sha256"),
        "actions_sha256": actions_before, "protected_before": original,
        "protected_after": current, "original_lane_differences": differences,
        "evaluated_pose_errors": evaluated_errors(original_state, revised_state),
        "native_game_acceptance": False,
        "control_context_restored": bpy.context.mode == original_mode and
            bpy.context.view_layer.objects.active == original_active,
        "sources_unchanged": sha(source) == CURRENT_SHA and sha(first) == FIRST_SHA,
    }, indent=2) + "\n", encoding="utf-8")
    print("WARLOCK_RIG_REVISED", str(destination), sha(destination), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rig", type=Path, required=True)
    parser.add_argument("--first-rig", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(parser.parse_args(argv))
