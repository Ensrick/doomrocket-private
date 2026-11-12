"""Directional, independent-space and no-pop tests on the actual Blender rig.

Run Blender 5.2 --background --factory-startup --disable-autoexec --python-exit-code 1
 --python test_weapon_controls_blender.py -- --rig <handoff.blend> --report <report.json>
Optional --upgrade tests adding controls to the original delivered handoff in memory.
No source blend is saved or artist action rewritten.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    args = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--rig", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--upgrade", action="store_true")
    options = parser.parse_args(args)
    tools = Path(__file__).resolve().parent
    controls = load_module("warlock_weapon_controls_tested", tools / "weapon_controls.py")
    oracle = load_module("warlock_weapon_oracle", tools / "test_weapon_reference_blender.py")
    bpy.ops.wm.open_mainfile(filepath=str(options.rig), use_scripts=False)
    rig, game, reference = [bpy.data.objects[name] for name in
        ("WARLOCK_CTRL", "WARLOCK_GAME", "WARLOCK_LAUNCHER_REFERENCE")]
    preserved = oracle.protected(game)
    dg = bpy.context.evaluated_depsgraph_get()
    neutral_reference = reference.evaluated_get(dg).matrix_world.copy()
    if options.upgrade:
        groups = json.loads(rig["warlock_control_manifest"])["groups"]
        objects = [obj for obj in bpy.data.objects if obj == reference or obj.type == "MESH"
                   and obj.get("authoring_reference_only")]
        widgets = bpy.data.collections["Warlock custom curve widgets"]
        controls.build_weapon_controls(rig, game, reference, objects, groups, widgets)
    assert rig.get(controls.MANIFEST_KEY), "Revised follow controls missing"
    initial = {bone.name: (bone.matrix_basis.copy(),
               {prop: bone[prop] for prop in bone.keys() if isinstance(bone[prop], (int, float, bool))})
               for bone in rig.pose.bones}
    checks = []

    def update():
        rig.update_tag()
        bpy.context.view_layer.update()

    def world(name):
        return controls._world(rig, name)

    def object_world(name):
        obj = bpy.data.objects[name]
        return obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.copy()

    def native_world(name):
        native = game.evaluated_get(bpy.context.evaluated_depsgraph_get())
        return native.matrix_world @ native.pose.bones[name].matrix

    def check(label, condition, **evidence):
        assert condition, (label, evidence)
        checks.append({"check": label, **evidence})

    def reset():
        for name, (matrix, props) in initial.items():
            bone = rig.pose.bones[name]
            bone.matrix_basis = matrix
            for prop, value in props.items():
                bone[prop] = value
        update()

    def movement(name, matrix):
        return (world(name).translation - matrix.translation).length

    update()
    check("native GAME skeleton, skin, pose basis and artist actions preserved during construction",
          oracle.protected(game) == preserved, protected=preserved)
    check("default launcher frame preserves delivered attachment",
          controls._matrix_error(neutral_reference, object_world(reference.name)) < 2e-5,
          matrix_error=controls._matrix_error(neutral_reference, object_world(reference.name)))
    # The source pipeline independently pins the semantic pistol-grip cap to
    # (0, 1.108044386 cm, 0) at this root. The old 'handle' helper is 42 cm away
    # and is intentionally not used to shift the approved mesh.
    grip = object_world(reference.name) @ Vector((.00000002565, .01108044386, 0.))
    gap = (grip - native_world("j_lefthand").translation).length
    check("calibrated semantic grip stays at the starting hand", .010 < gap < .012,
          cap_to_wrist_m=gap, legacy_handle_shift_applied=False)
    count = len(rig.data.bones)
    controls.build_weapon_controls(rig, game, reference, [], {}, None)
    check("repeat setup does not duplicate controls", len(rig.data.bones) == count)
    for name in ("CTRL-weapon", "CTRL-rocket"):
        shape = rig.pose.bones[name].custom_shape
        check(name + " uses a selectable 3D bounds box", shape and len(shape.data.vertices) == 8
              and len(shape.data.edges) == 12,
              vertices=len(shape.data.vertices), edges=len(shape.data.edges))

    # Target native frame at real stretches/squashes and rotated torso, not just
    # an unposed neutral chain. The oracle independently implements SDK math.
    for length in (.75, 1., 1.35):
        reset()
        rig.pose.bones["CTRL-shape-j_leftarm_scale"]["length"] = length
        rig.pose.bones["chest"].rotation_euler.z = .17
        update()
        native_reference = bpy.data.objects[json.loads(rig[controls.MANIFEST_KEY])["native_reference"]]
        original = native_reference.evaluated_get(bpy.context.evaluated_depsgraph_get())
        original_frame = original.matrix_world @ original.pose.bones["j_leftweaponattach"].matrix
        baseline_error = controls._matrix_error(original_frame, native_world("j_leftweaponattach"))
        check("existing native attachment pose preserved at length %.2f" % length,
              baseline_error < 3e-6, matrix_error=baseline_error)
        sample = oracle.sample(game, reference, [bpy.data.objects["pRocketLauncher"]])
        check("native normalized-axis attachment under length %.2f" % length,
              sample["axis_endpoint_error_mm_at_1m"] < .003,
              **sample)
        check("launcher is rigid under native scaling %.2f" % length,
              max(abs(value - 1) for value in sample["reference_scale"]) < 3e-6)
        evaluated_game = game.evaluated_get(bpy.context.evaluated_depsgraph_get())
        for native_name in controls.EXPORT_BINDINGS.values():
            bone = evaluated_game.pose.bones[native_name]
            local = bone.parent.matrix.inverted() @ bone.matrix if bone.parent else bone.matrix
            axes = [local.to_3x3().col[i].normalized() for i in range(3)]
            shear = max(abs(axes[a].dot(axes[b])) for a, b in ((0, 1), (0, 2), (1, 2)))
            check(native_name + " has representable local TRS at length %.2f" % length,
                  shear < 2e-5, normalized_axis_dot=shear)
        rig.pose.bones["CTRL-weapon"].rotation_quaternion = Quaternion(Vector((.3, .6, .7)).normalized(), .34)
        rig.pose.bones["CTRL-weapon"].location.x += .045
        rig.pose.bones["CTRL-rocket"].rotation_quaternion = Quaternion(Vector((.7, .1, .3)).normalized(), -.27)
        update()
        for channel in ("weapon_follow", "rocket_follow"):
            bone_name = controls.EXPORT_BINDINGS[controls.CHANNELS[channel][2]]
            before = native_world(bone_name)
            for enabled in (False, True):
                controls.switch_follow(rig, channel, enabled)
                error = controls._matrix_error(before, native_world(bone_name))
                check("native custom pose no-pop %s=%s length%.2f" % (channel, enabled, length),
                      error < 6e-6, matrix_error=error)
            bone = game.evaluated_get(bpy.context.evaluated_depsgraph_get()).pose.bones[bone_name]
            local = bone.parent.matrix.inverted() @ bone.matrix
            axes = [local.to_3x3().col[i].normalized() for i in range(3)]
            shear = max(abs(axes[a].dot(axes[b])) for a, b in ((0, 1), (0, 2), (1, 2)))
            check("edited %s remains native TRS length%.2f" % (bone_name, length),
                  shear < 2e-5, normalized_axis_dot=shear)
            location_error = (native_world(bone_name).translation - world(controls.CHANNELS[channel][2]).translation).length
            check("edited %s has exact control position length%.2f" % (bone_name, length),
                  location_error < 2e-6, position_error=location_error)

    # Both controls follow the same hand by default but their state and free
    # animation are independent. Detaching one must not detach the other.
    for detached, other in (("weapon_follow", "CTRL-rocket"), ("rocket_follow", "CTRL-weapon")):
        reset()
        name = controls.CHANNELS[detached][2]
        rig.pose.bones["j_lefthand_ctrl_ik"].location.x += .07
        update()
        before = world(name)
        other_before = world(other)
        reference_name = reference.name if name == "CTRL-weapon" else "pRocket"
        actual_before = object_world(reference_name)
        error = controls.switch_follow(rig, detached, False)
        check(detached + " off switch preserves current pose", error < 3e-5, matrix_error=error)
        rig.pose.bones["j_lefthand_ctrl_ik"].location.x += .10
        update()
        check(detached + " detached control stays in world space", movement(name, before) < 2e-5,
              position_error=movement(name, before))
        actual_error = controls._matrix_error(actual_before, object_world(reference_name))
        check(detached + " detached actual prop stays fixed under ordinary hand movement",
              actual_error < 3e-5, matrix_error=actual_error)
        check(detached + " does not disable the other reference", movement(other, other_before) > .04,
              distance=movement(other, other_before))
        error = controls.switch_follow(rig, detached, True)
        check(detached + " on switch preserves detached custom pose", error < 3e-5, matrix_error=error)
        before = world(name)
        rig.pose.bones["j_lefthand_ctrl_ik"].location.x += .06
        update()
        check(detached + " reattached control follows the hand", movement(name, before) > .03,
              distance=movement(name, before))

    reset()
    rocket_before = object_world("pRocket")
    rig.pose.bones["CTRL-weapon"].location.x += .06
    rig.pose.bones["CTRL-weapon"].rotation_quaternion = Quaternion(Vector((.2, .5, .7)).normalized(), .29)
    update()
    error = controls._matrix_error(rocket_before, object_world("pRocket"))
    check("actual rocket is independent of launcher translation and rotation",
          error < 3e-5, matrix_error=error)
    weapon_before = object_world(reference.name)
    rig.pose.bones["CTRL-rocket"].location.y += .075
    rig.pose.bones["CTRL-rocket"].rotation_quaternion = Quaternion(Vector((.5, .1, .3)).normalized(), -.32)
    update()
    error = controls._matrix_error(weapon_before, object_world(reference.name))
    check("actual launcher is independent of rocket translation and rotation",
          error < 3e-5, matrix_error=error)

    reset()
    rig.pose.bones["j_righthand_ctrl_ik"].location.y += .045
    rig.pose.bones["j_righthand_ctrl_ik"].rotation_euler.z += .15
    rig.pose.bones["CTRL-weapon"].location.z += .09
    update()
    error = controls.switch_follow(rig, "right_hand_follow", True)
    check("right hand on switch preserves its current custom pose", error < 3e-5, matrix_error=error)
    before = world("j_righthand_ctrl_ik")
    weapon_before = world("CTRL-weapon")
    rig.pose.bones["CTRL-weapon"].location.x += .04
    update()
    displacement = world("CTRL-weapon").translation - weapon_before.translation
    error = (world("j_righthand_ctrl_ik").translation - before.translation - displacement).length
    check("right IK follows independently animated launcher", error < 2e-5, position_error=error)
    error = controls.switch_follow(rig, "right_hand_follow", False)
    check("right hand off switch preserves its current pose", error < 3e-5, matrix_error=error)
    before = world("j_righthand_ctrl_ik")
    rig.pose.bones["CTRL-weapon"].location.x += .05
    update()
    check("detached right hand stays fixed", movement("j_righthand_ctrl_ik", before) < 2e-5)
    reset()
    rig.pose.bones["j_rightarm_ctrl_parent"]["IK_FK"] = 1.
    update()
    try:
        controls.switch_follow(rig, "right_hand_follow", True)
    except ValueError as error:
        check("standalone FK switch refuses silent ineffective follow", "IK" in str(error))
    else:
        raise AssertionError("Enabling right hand follow while FK must require a no-pop IK match")
    reset()
    check("no-key switches preserve all existing actions/tracks/custom keys",
          oracle.protected(game)["actions_sha256"] == preserved["actions_sha256"])
    check("native skeleton/skin/action protected identities remain exact after tests",
          oracle.protected(game) == preserved)
    # Explicit keying may create the new control action, while retaining every
    # pre-existing artist action as an exact digest.
    action_before = {item["name"]: oracle.digest(item) for item in oracle.actions()}
    controls.switch_follow(rig, "weapon_follow", False, keyframe=True)
    action_after = {item["name"]: oracle.digest(item) for item in oracle.actions()}
    check("explicit keying retains existing artist action payloads",
          all(action_after[name] == value for name, value in action_before.items()))
    report = {"schema": 1, "source_blend": str(options.rig), "checks": checks,
              "passed": len(checks), "source_saved": False,
              "native_game_acceptance": False}
    options.report.parent.mkdir(parents=True, exist_ok=True)
    options.report.write_text(json.dumps(report, indent=2) + "\n")
    print("WARLOCK_WEAPON_CONTROLS_PASS", len(checks), str(options.report))


if __name__ == "__main__":
    main()
