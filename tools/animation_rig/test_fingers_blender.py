"""Directional/per-digit regressions for the animator's reported hand failures.

Open the candidate in background Blender, then run this script with
``-- --output <report.json>``. It changes only the unsaved testing session.
Unlike displacement-only tests, these distinguish palm closing, axial twist,
and a rigid fan of all five digits, and check bilateral mirror behavior.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

DIGITS = ('thumb', 'index', 'middle', 'ring', 'pinky')


def names(side, digit):
    p = 'ORG-j_' + side
    return ([p + 'inhandthumb', p + 'handthumb1', p + 'handthumb2'] if digit == 'thumb'
            else [p + 'hand' + digit + str(i) for i in (1, 2, 3)])


def action_payload():
    payload = []
    for action in bpy.data.actions:
        curves = []
        for layer in action.layers:
            for strip in layer.strips:
                for bag in getattr(strip, 'channelbags', ()):
                    for fc in bag.fcurves:
                        curves.append((fc.data_path, fc.array_index,
                            [(tuple(k.co), tuple(k.handle_left), tuple(k.handle_right),
                              k.interpolation) for k in fc.keyframe_points]))
        payload.append((action.name, curves))
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def main(options):
    rig = bpy.data.objects['WARLOCK_CTRL']
    game = bpy.data.objects['WARLOCK_GAME']
    path = Path(bpy.data.filepath)
    input_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    actions_before = action_payload()
    skeleton_before = [(b.name, b.parent.name if b.parent else None,
                        [list(row) for row in b.matrix_local]) for b in game.data.bones]
    defaults = json.loads(rig['warlock_control_defaults'])
    tests = []

    def check(name, condition, **evidence):
        tests.append({'name': name, 'passed': bool(condition), **evidence})
        print(('PASS ' if condition else 'FAIL ') + name, json.dumps(evidence), flush=True)

    def update():
        rig.update_tag()
        bpy.context.view_layer.update()

    def reset():
        if rig.animation_data:
            rig.animation_data.action = None
        for bone in rig.pose.bones:
            bone.matrix_basis = Matrix.Identity(4)
            for prop, value in defaults.get(bone.name, {}).items():
                bone[prop] = value
        update()

    def sample():
        update()
        evaluated = rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
        return {pb.name: (evaluated.matrix_world @ pb.matrix).copy() for pb in evaluated.pose.bones}

    def palm(pose, side):
        wrist = pose['ORG-j_' + side + 'hand'].translation
        knuckles = sum((pose[names(side, d)[0]].translation for d in DIGITS[1:]), Vector()) / 4
        return (wrist + knuckles) / 2

    def set_prop(side, prop, value):
        rig.pose.bones['CTRL-hand-settings-' + side][prop] = value
        return sample()

    reset()
    neutral = sample()
    cases = {}
    for side in ('left', 'right'):
        for prop, value in (('curl', -.7), ('curl', .2), ('curl', .7), ('curl', 1.),
                            ('spread', -.7), ('spread', .7)):
            reset()
            cases[side, prop, value] = set_prop(side, prop, value)
        wrist = neutral['ORG-j_' + side + 'hand'].translation
        knuckles = [neutral[names(side, d)[0]].translation for d in DIGITS[1:]]
        palm_normal = ((sum(knuckles, Vector()) / 4 - wrist).cross(knuckles[0] - knuckles[-1])).normalized()
        for digit in DIGITS:
            chain = names(side, digit)
            tip = chain[-1]
            distances = [(cases[side, 'curl', v][tip].translation -
                          palm(cases[side, 'curl', v], side)).length for v in (-.7, .2, .7, 1.)]
            base_distance = (neutral[tip].translation - palm(neutral, side)).length
            check(side + '_' + digit + '_curl_closes_toward_palm',
                  distances[0] > base_distance + .003 and
                  base_distance > distances[1] > distances[2] > distances[3] and
                  base_distance - distances[3] > .025,
                  neutral_m=base_distance, open_and_close_distances_m=distances)

            # Remove proximal joint motion before measuring intrinsic rotation.
            # The measured joint-to-child direction is the longitudinal axis;
            # no axis metadata from the driver builder is used by this test.
            for i, name in enumerate(chain):
                parent = chain[i - 1] if i else 'ORG-j_' + side + 'hand'
                rest_relative = neutral[parent].inverted() @ neutral[name]
                posed = cases[side, 'curl', .7]
                posed_relative = posed[parent].inverted() @ posed[name]
                delta = rest_relative.to_quaternion().rotation_difference(posed_relative.to_quaternion())
                direction = ((neutral[chain[i + 1]].translation - neutral[name].translation)
                             if i < 2 else neutral[name].to_3x3().col[0])
                local_long = (neutral[name].to_3x3().inverted() @ direction).normalized()
                axial_dot = abs(delta.axis.normalized().dot(local_long))
                check(name + '_curl_is_transverse_not_axial_twist', axial_dot < .002,
                      rotation_deg=math.degrees(delta.angle), axial_axis_dot=axial_dot)

            fan = cases[side, 'spread', .7]
            root = chain[0]
            direction_before = neutral[chain[1]].translation - neutral[root].translation
            direction_after = fan[chain[1]].translation - fan[root].translation
            # Read the root's delta rotation: its axis must be the palm normal,
            # and thumb/index/middle must fan opposite to ring/little fingers.
            delta = neutral[root].to_quaternion().rotation_difference(fan[root].to_quaternion())
            axis_world = neutral[root].to_quaternion() @ delta.axis
            signed = delta.angle * axis_world.dot(palm_normal)
            expected_sign = 1 if digit in ('thumb', 'index', 'middle') else -1
            intrinsic_error = 0.
            for i in (1, 2):
                before = neutral[chain[i - 1]].inverted() @ neutral[chain[i]]
                after = fan[chain[i - 1]].inverted() @ fan[chain[i]]
                intrinsic_error = max(intrinsic_error,
                    max(abs(before[r][c] - after[r][c]) for r in range(4) for c in range(4)))
            normal_axis_dot = abs(axis_world.normalized().dot(palm_normal))
            check(side + '_' + digit + '_spread_fans_without_curling',
                  signed * expected_sign > .025 and normal_axis_dot > .999
                  and intrinsic_error < 2e-5 and (direction_after - direction_before).length > .001,
                  signed_fan_deg=math.degrees(signed), palm_normal_axis_dot=normal_axis_dot,
                  intrinsic_segment_matrix_error=intrinsic_error)

            # Each individual curl must work alone without moving another digit.
            reset()
            individual = set_prop(side, 'curl_' + digit, .7)
            tip_move = (individual[tip].translation - neutral[tip].translation).length
            other_move = max((individual[names(side, d)[-1]].translation -
                              neutral[names(side, d)[-1]].translation).length
                             for d in DIGITS if d != digit)
            check(side + '_' + digit + '_individual_curl_isolated',
                  tip_move > .02 and other_move < 2e-5,
                  tip_displacement_m=tip_move, other_digit_max_m=other_move)

        reset()
        native = rig.pose.bones[names(side, 'index')[1]]
        native.rotation_mode = 'XYZ'
        native.rotation_euler[2] = .12
        saved_basis = native.matrix_basis.copy()
        set_prop(side, 'curl', .7)
        set_prop(side, 'spread', .4)
        check(side + '_native_custom_pose_remains_additive',
              max(abs(saved_basis[r][c] - native.matrix_basis[r][c])
                  for r in range(4) for c in range(4)) < 1e-7)

    mirror_error = 0.
    for prop, value in (('curl', -.7), ('curl', .2), ('curl', .7), ('curl', 1.),
                        ('spread', -.7), ('spread', .7)):
        for digit in DIGITS:
            for left, right in zip(names('left', digit), names('right', digit)):
                p = cases['left', prop, value][left].translation.copy()
                p.x = -p.x
                mirror_error = max(mirror_error, (p - cases['right', prop, value][right].translation).length)
    check('all_five_digits_mirror_across_both_hands', mirror_error < 3e-5,
          maximum_joint_position_error_m=mirror_error)
    reset()
    returned = sample()
    error = max(abs(neutral[name][r][c] - returned[name][r][c])
                for name in neutral for r in range(4) for c in range(4))
    check('neutral_is_recoverable', error < 1e-6, maximum_matrix_error=error)
    check('all_existing_action_keys_are_unchanged', action_payload() == actions_before,
          actions_sha256=actions_before, actions=len(bpy.data.actions))
    skeleton_after = [(b.name, b.parent.name if b.parent else None,
                       [list(row) for row in b.matrix_local]) for b in game.data.bones]
    check('exact_138_game_skeleton_unchanged', len(skeleton_after) == 138 and skeleton_after == skeleton_before)
    check('input_blend_is_unchanged', hashlib.sha256(path.read_bytes()).hexdigest() == input_hash,
          sha256=input_hash)
    report = {'schema': 1, 'passed': all(t['passed'] for t in tests), 'tests': tests,
              'blender': bpy.app.version_string, 'input': str(path), 'sha256': input_hash,
              'limitation': 'Directional Blender checks; no native engine or artist visual acceptance.'}
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('WARLOCK_FINGER_TESTS', json.dumps({'passed': report['passed'], 'checks': len(tests)}))
    if not report['passed']:
        raise RuntimeError('Finger direction tests failed; inspect ' + str(options.output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    main(parser.parse_args(argv))
