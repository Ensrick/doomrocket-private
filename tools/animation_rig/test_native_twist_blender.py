"""Check every advertised twist against native joints and evaluated skin.

Run on the generated blend with background Blender and ``-- --output <json>``.
There are exactly two existing weighted roll channels. Inherited Rigify DEF
tweaks do not feed the shipping ORG bridge and must remain hidden, while their
bones/action paths remain intact. The test never saves over the input blend.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix


def main(options):
    rig = bpy.data.objects['WARLOCK_CTRL']
    game = bpy.data.objects['WARLOCK_GAME']
    body = next(o for o in bpy.data.objects if o.type == 'MESH' and
                any(m.type == 'ARMATURE' and m.object == game for m in o.modifiers))
    defaults = json.loads(rig['warlock_control_defaults'])
    manifest = json.loads(rig['warlock_control_manifest'])
    input_path = Path(bpy.data.filepath)
    before_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()
    tests = []
    original_action = rig.animation_data.action if rig.animation_data else None
    # Fcurve pointers and serialized key handles are both retained across tests.
    def action_keys():
        return [(a.name, [(fc.data_path, fc.array_index,
                 [(tuple(k.co), tuple(k.handle_left), tuple(k.handle_right), k.interpolation)
                  for k in fc.keyframe_points])
                for layer in a.layers for strip in layer.strips
                for bag in getattr(strip, 'channelbags', ()) for fc in bag.fcurves])
                for a in bpy.data.actions]
    actions_before = action_keys()
    skeleton_before = [(b.name, b.parent.name if b.parent else None,
                        [list(row) for row in b.matrix_local]) for b in game.data.bones]

    def check(name, condition, **evidence):
        tests.append({'name': name, 'passed': bool(condition), **evidence})
        print(('PASS ' if condition else 'FAIL ') + name, json.dumps(evidence), flush=True)

    def update():
        rig.update_tag()
        bpy.context.view_layer.update()

    def reset():
        if rig.animation_data:
            rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.matrix_basis = Matrix.Identity(4)
            for key, value in defaults.get(pb.name, {}).items():
                pb[key] = value
        update()

    def sample():
        update()
        dg = bpy.context.evaluated_depsgraph_get()
        eg, em = game.evaluated_get(dg), body.evaluated_get(dg)
        mesh = em.to_mesh()
        vertices = [em.matrix_world @ v.co for v in mesh.vertices]
        em.to_mesh_clear()
        return {'bones': {pb.name: (eg.matrix_world @ pb.matrix).copy() for pb in eg.pose.bones},
                'vertices': vertices}

    def rotation(before, after, name):
        angle = before['bones'][name].to_quaternion().rotation_difference(
            after['bones'][name].to_quaternion()).angle
        return math.degrees(min(angle, 2 * math.pi - angle))

    def skin_delta(before, after, ids):
        return max((after['vertices'][i] - before['vertices'][i]).length for i in ids)

    expected = {'CTRL-forearm-twist-left', 'CTRL-forearm-twist-right'}
    actual = set(manifest['groups']['Twist'])
    check('advertised_twist_group_contains_exactly_real_native_controls', actual == expected,
          controls=sorted(actual))
    weighted = {g.name for g in body.vertex_groups if any(
        i.group == g.index and i.weight > .001 for v in body.data.vertices for i in v.groups)}
    rolls = {b.name for b in game.data.bones if 'roll' in b.name}
    check('two_existing_weighted_roll_channels_are_the_supported_scope',
          rolls == {'j_leftforearmroll', 'j_rightforearmroll'} and rolls <= weighted,
          existing_roll_channels=sorted(rolls))

    obsolete = [f'j_{side}{part}_ctrl_tweak{suffix}' for side in ('left', 'right')
                for part, suffixes in (('arm', ('', '.001')), ('forearm', ('',)),
                                       ('upleg', ('', '.001')), ('leg', ('', '.001')))
                for suffix in suffixes]
    check('all_14_inert_predecessor_controls_are_hidden_but_retained',
          len(obsolete) == 14 and all(name in rig.pose.bones and
              rig.pose.bones[name].bone.hide and rig.pose.bones[name].bone.hide_select and
              rig.pose.bones[name].custom_shape is None and name not in actual for name in obsolete),
          controls=obsolete)
    check('obsolete_control_action_paths_remain_resolvable', all(
        rig.path_resolve('pose.bones[' + json.dumps(name) + '].rotation_euler') is not None
        for name in obsolete))

    reset()
    neutral = sample()
    for side in ('left', 'right'):
        control = rig.pose.bones['CTRL-forearm-twist-' + side]
        roll, wrist = 'j_' + side + 'forearmroll', 'j_' + side + 'hand'
        group = body.vertex_groups[roll].index
        ids = [v.index for v in body.data.vertices if any(g.group == group and g.weight > .05 for g in v.groups)]
        outside = [v.index for v in body.data.vertices if not any(g.group == group and g.weight > 1e-5 for g in v.groups)]
        check(side + '_twist_has_real_weighted_vertices', len(ids) > 0, vertices=len(ids))
        for degrees in (-20, 20):
            reset()
            control.rotation_mode = 'XYZ'
            control.rotation_euler[1] = math.radians(degrees)
            posed = sample()
            angle = rotation(neutral, posed, roll)
            skin = skin_delta(neutral, posed, ids)
            other_skin = skin_delta(neutral, posed, outside)
            wrist_move = (neutral['bones'][wrist].translation - posed['bones'][wrist].translation).length
            check(side + '_manual_' + str(degrees) + '_twist_changes_native_roll_and_skin',
                  abs(angle - 20) < .1 and skin > .001 and other_skin < 2e-5 and wrist_move < 1e-5,
                  native_roll_rotation_deg=angle, weighted_skin_max_m=skin,
                  unrelated_skin_max_m=other_skin, wrist_translation_m=wrist_move)
        reset()
        rig.pose.bones['j_' + side + 'arm_ctrl_parent']['IK_FK'] = 1.
        hand = rig.pose.bones['j_' + side + 'hand_ctrl_fk']
        hand.rotation_mode = 'XYZ'
        hand.rotation_euler[1] = math.radians(60)
        samples = {}
        for share in (0., .5, 1.):
            control['auto_twist'] = share
            samples[share] = sample()
        half = rotation(samples[0.], samples[.5], roll)
        full = rotation(samples[0.], samples[1.], roll)
        skin = skin_delta(samples[0.], samples[.5], ids)
        wrist_drift = max((samples[0.]['bones'][wrist].translation -
                          samples[s]['bones'][wrist].translation).length for s in (.5, 1.))
        wrist_angle = max(rotation(samples[0.], samples[s], wrist) for s in (.5, 1.))
        check(side + '_automatic_twist_distributes_wrist_rotation_to_native_skin',
              full > 20 and full < 90 and abs(half - full * .5) < .1 and skin > .001 and
              wrist_drift < 1e-5 and wrist_angle < .1,
              half_share_rotation_deg=half, full_share_rotation_deg=full,
              weighted_skin_max_m=skin, wrist_translation_m=wrist_drift,
              wrist_rotation_drift_deg=wrist_angle)

    reset()
    returned = sample()
    error = skin_delta(neutral, returned, range(len(body.data.vertices)))
    check('neutral_skin_is_recovered_after_manual_and_auto_twist', error < 1e-5,
          maximum_vertex_error_m=error)
    check('existing_artist_animation_keys_are_unchanged', action_keys() == actions_before,
          actions=len(actions_before))
    skeleton_after = [(b.name, b.parent.name if b.parent else None,
                       [list(row) for row in b.matrix_local]) for b in game.data.bones]
    check('exact_native_138_bone_skeleton_is_unchanged',
          len(skeleton_after) == 138 and skeleton_after == skeleton_before)
    check('input_blend_was_not_modified', hashlib.sha256(input_path.read_bytes()).hexdigest() == before_hash,
          sha256=before_hash)
    if rig.animation_data:
        rig.animation_data.action = original_action
    report = {'schema': 1, 'passed': all(t['passed'] for t in tests), 'tests': tests,
              'source_blend': str(input_path), 'sha256': before_hash, 'blender': bpy.app.version_string,
              'scope': 'Only existing forearm roll channels; upper-arm/thigh roll requires artist-weighted source channels.',
              'limitation': 'Native Blender joint/skin behavior, not a rendered game acceptance.'}
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('WARLOCK_NATIVE_TWIST_TESTS', json.dumps({'passed': report['passed'], 'checks': len(tests)}))
    if not report['passed']:
        raise RuntimeError('Native twist behavior failed; inspect ' + str(options.output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    main(parser.parse_args(argv))
