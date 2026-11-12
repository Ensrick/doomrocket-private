"""Calibrate finger mechanisms from joint geometry, never assumed FBX axes.

The imported Warlock digit joints run along local X although Blender displays
their bones along Y. Rotating X therefore twists a digit; its curl axis must be
recovered from the anatomical chain. Only authoring MCH drivers are installed.
The native controls remain available for additive corrections and keyframes.
"""
from __future__ import annotations

import json
from mathutils import Vector

DIGITS = ('thumb', 'index', 'middle', 'ring', 'pinky')
# Positive fan spreads toward the thumb side of the palm; negative fan toward
# the little finger. Keep a small middle-finger response rather than an inert
# zero multiplier. The two palms' mirrored frames determine the world sign.
FAN_RADIANS = {'thumb': .45, 'index': .28, 'middle': .07, 'ring': -.16, 'pinky': -.35}
CURL_RADIANS = {'thumb': (.45, .65, .65), 'finger': (.55, .75, .65)}


def digit_names(side, digit):
    prefix = 'ORG-j_' + side
    return ([prefix + 'inhandthumb', prefix + 'handthumb1', prefix + 'handthumb2']
            if digit == 'thumb' else [prefix + 'hand' + digit + str(i) for i in (1, 2, 3)])


def _unit(vector, description):
    if vector.length < 1e-7:
        raise ValueError('Degenerate finger calibration: ' + description)
    return vector.normalized()


def anatomical_frames(rig):
    """Return bone-local curl axes and palm-normal fan axes in rig rest space.

    Curl follows the existing natural bend, measured between the first two
    joint-to-child directions. Every segment's axis is projected transverse to
    that segment so there is no axial roll. Fan is about the palm plane's normal.
    Neither native bone display tails nor axis letters define the anatomy.
    """
    frames = {}
    for side in ('left', 'right'):
        joints = {digit: [rig.data.bones[name] for name in digit_names(side, digit)]
                  for digit in DIGITS}
        wrist = rig.data.bones['ORG-j_' + side + 'hand'].head_local
        bases = [joints[digit][0].head_local for digit in DIGITS[1:]]
        knuckles = sum((point.copy() for point in bases), Vector()) / len(bases)
        forward = _unit(knuckles - wrist, side + ' palm forward')
        across = _unit(bases[0] - bases[-1], side + ' knuckle width')
        fan_normal = _unit(forward.cross(across), side + ' palm plane')
        for digit, bones in joints.items():
            directions = [_unit(bones[i + 1].head_local - bones[i].head_local,
                                side + ' ' + digit + ' joint span') for i in (0, 1)]
            # The final segment has no following deforming joint. Its native
            # longitudinal axis agrees with both measured proximal spans; use
            # that geometric agreement to select a rest-frame axis, not its name.
            longitudinal_index = max(range(3), key=lambda axis: sum(
                abs(bones[i].matrix_local.col[axis].xyz.normalized().dot(directions[i]))
                for i in (0, 1)))
            signs = [bones[i].matrix_local.col[longitudinal_index].xyz.dot(directions[i])
                     for i in (0, 1)]
            distal = bones[-1].matrix_local.col[longitudinal_index].xyz.normalized()
            if sum(signs) < 0:
                distal = -distal
            directions.append(distal)
            bend = directions[0].cross(directions[1])
            if bend.length < 1e-5:
                # Straight chains still bend toward the palm rather than twist.
                bend = directions[0].cross(fan_normal)
            bend = _unit(bend, side + ' ' + digit + ' bend plane')
            for segment, (bone, direction) in enumerate(zip(bones, directions)):
                transverse = _unit(bend - direction * bend.dot(direction),
                                   bone.name + ' transverse curl')
                inverse = bone.matrix_local.to_3x3().normalized().inverted()
                curl_axis = _unit(inverse @ transverse, bone.name + ' local curl')
                spread_axis = _unit(inverse @ fan_normal, bone.name + ' local fan')
                frames[bone.name] = {'side': side, 'digit': digit, 'segment': segment,
                    'curl_axis': list(curl_axis), 'spread_axis': list(spread_axis),
                    'curl_radians': CURL_RADIANS['thumb' if digit == 'thumb' else 'finger'][segment],
                    'spread_radians': FAN_RADIANS[digit] if segment == 0 else 0.,
                    'longitudinal_axis': list(direction), 'palm_normal': list(fan_normal)}
    return frames


def _quaternion_driver(rig, bone, index, expression, settings, digit):
    curve = bone.driver_add('rotation_quaternion', index)
    driver = curve.driver
    driver.type = 'SCRIPTED'
    driver.expression = expression
    for name, prop in (('c', 'curl'), ('i', 'curl_' + digit), ('s', 'spread')):
        var = driver.variables.new()
        var.name = name
        var.type = 'SINGLE_PROP'
        var.targets[0].id = rig
        var.targets[0].data_path = 'pose.bones[' + json.dumps(settings) + '][' + json.dumps(prop) + ']'


def install_finger_drivers(rig, finger_records):
    """Replace the old MCH Euler-axis assumption with calibrated quaternion TRS.

    Call after the MCH insertion, settings properties and native control curves
    exist. ``finger_records`` is the builder's (side, digit, segment, native,
    mechanism, settings) sequence. No action, NLA track or native key is edited.
    """
    frames = anatomical_frames(rig)
    for side, digit, segment, native, mechanism, settings in finger_records:
        frame = frames[native]
        bone = rig.pose.bones[mechanism]
        for field in ('rotation_euler', 'rotation_quaternion'):
            bone.driver_remove(field)
        bone.rotation_mode = 'QUATERNION'
        a = Vector(frame['spread_axis'])
        b = Vector(frame['curl_axis'])
        # q_fan * q_curl: fan is in the proximal palm plane and curl remains in
        # the digit's anatomical bend plane, including combined animated poses.
        p = f'(s*{frame["spread_radians"] / 2:.10g})'
        q = f'((c+i)*{frame["curl_radians"] / 2:.10g})'
        dot = a.dot(b)
        expressions = [f'cos({p})*cos({q})-({dot:.10g})*sin({p})*sin({q})']
        cross = a.cross(b)
        for axis in range(3):
            expressions.append(f'({a[axis]:.10g})*sin({p})*cos({q})'
                f'+({b[axis]:.10g})*sin({q})*cos({p})'
                f'+({cross[axis]:.10g})*sin({p})*sin({q})')
        for index, expression in enumerate(expressions):
            _quaternion_driver(rig, bone, index, expression, settings, digit)
        bone['warlock_finger_calibration'] = json.dumps(frame)
    rig['warlock_finger_calibration'] = json.dumps(frames)
    rig.update_tag()
    return frames
