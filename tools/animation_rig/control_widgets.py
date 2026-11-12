"""Artist-facing shapes for the existing Warlock control rig.

Widgets are edge meshes, as expected by Blender custom bone shapes.  Their
vertices are calibrated in the neutral model's world frame, then converted to
each controller's local frame.  Imported FBX bone Y axes are not anatomical
finger/foot directions, so simply rotating a unit circle is insufficient.
This module changes display/selection only; it never edits GAME bones, skin,
constraints, drivers, or animation keys.
"""
from __future__ import annotations

import json
import math

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


COLORS = {
    'left': (0.16, 0.48, 1.0),
    'right': (1.0, 0.22, 0.16),
    'center': (0.95, 0.68, 0.10),
    'technical': (0.68, 0.28, 0.92),
}
SIDES = ('left', 'right')
DIGITS = ('thumb', 'index', 'middle', 'ring', 'pinky')


def _bounds(points):
    if not points:
        raise ValueError('Cannot fit a control to an empty set of vertices')
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    return low, high


def _circle(center, u, v, radius_u, radius_v=None, count=48):
    radius_v = radius_u if radius_v is None else radius_v
    return [center + u * (radius_u * math.cos(i * math.tau / count))
            + v * (radius_v * math.sin(i * math.tau / count)) for i in range(count)]


def _frame(axis):
    axis = axis.normalized()
    ref = Vector((0, 0, 1)) if abs(axis.z) < .8 else Vector((1, 0, 0))
    u = axis.cross(ref).normalized()
    return u, axis.cross(u).normalized()


def _shape(rig, widgets, name, paths, kind, closed=True):
    """Create one selectable shape, without changing the controller's frame."""
    pb = rig.pose.bones[name]
    inverse = (rig.matrix_world @ pb.bone.matrix_local).inverted()
    points, edges = [], []
    for path in paths:
        start = len(points)
        points.extend(inverse @ p for p in path)
        edges.extend((start + i, start + i + 1) for i in range(len(path) - 1))
        if closed and len(path) > 2:
            edges.append((len(points) - 1, start))
    data = bpy.data.meshes.new('WGT-Warlock-' + name)
    data.from_pydata(points, edges, [])
    obj = bpy.data.objects.new(data.name, data)
    widgets.objects.link(obj)
    obj.hide_render = True
    pb.custom_shape = obj
    pb.use_custom_shape_bone_size = False
    pb.custom_shape_scale_xyz = (1, 1, 1)
    pb.custom_shape_translation = (0, 0, 0)
    pb.custom_shape_rotation_euler = (0, 0, 0)
    pb.custom_shape_transform = None
    pb['warlock_widget_kind'] = kind
    pb['warlock_widget_world_bounds'] = json.dumps([list(p) for p in _bounds([p for path in paths for p in path])])
    return pb


def _extrude(profile, axis, depth):
    """A closed silhouette on both faces plus ribs: a genuinely 3D box."""
    a = [p - axis * depth / 2 for p in profile]
    b = [p + axis * depth / 2 for p in profile]
    return [a, b] + [[x, y] for x, y in zip(a, b)]


def _box(center, axes, low, high):
    corners = [center + sum((axes[k] * (high[k] if i & (1 << k) else low[k]) for k in range(3)), Vector())
               for i in range(8)]
    return [[corners[i], corners[i ^ (1 << k)]] for i in range(8) for k in range(3) if not i & (1 << k)]


def _box_fit(pb, center, axes, low, high, sources, profile_count=0):
    pb['warlock_widget_box_fit'] = json.dumps({'center': list(center), 'axes': [list(a) for a in axes],
        'low': list(low), 'high': list(high), 'sources': sources, 'profile_count': profile_count})


def _group_points(mesh):
    names = {g.index: g.name for g in mesh.vertex_groups}
    groups = {}
    for v in mesh.data.vertices:
        p = mesh.matrix_world @ v.co
        for g in v.groups:
            if g.weight > .05:
                groups.setdefault(names[g.group], []).append(p)
    return groups


def _head(game, name):
    return game.matrix_world @ game.data.bones[name].head_local


def _promote(rig, groups, name, group):
    pb = rig.pose.bones[name]
    col = rig.data.collections.get('Warlock additions') or rig.data.collections.new('Warlock additions')
    col.assign(pb.bone)
    pb.bone.hide = False
    pb.bone.hide_select = False
    pb.lock_location = (True, True, True)
    pb.lock_rotation = (False, False, False)
    pb.lock_scale = (True, True, True)
    pb.lock_rotation_w = False
    pb.lock_rotations_4d = False
    if name not in groups.setdefault(group, []):
        groups[group].append(name)
    return pb


def _finger_names(side, digit):
    return ([f'j_{side}inhandthumb', f'j_{side}handthumb1', f'j_{side}handthumb2'] if digit == 'thumb'
            else [f'j_{side}hand{digit}{i}' for i in range(1, 4)])


def _mesh_tree(mesh):
    return BVHTree.FromPolygons([mesh.matrix_world @ v.co for v in mesh.data.vertices],
        [tuple(p.vertices) for p in mesh.data.polygons])


def _surface_clearance(paths, tree, closed=True):
    nearest, signed = float('inf'), float('inf')
    for path in paths:
        spans = list(zip(path, path[1:]))
        if closed and len(path) > 2:
            spans.append((path[-1], path[0]))
        for a, b in spans:
            edge_bound = float('inf')
            for step in range(5):
                p = a.lerp(b, step / 4)
                hit, normal, _, distance = tree.find_nearest(p)
                edge_bound = min(edge_bound, distance)
                signed = min(signed, (p - hit).dot(normal))
            # Nearest-surface distance is 1-Lipschitz.  Half the sampling gap
            # gives a conservative lower bound for the entire edge, including
            # intersections between samples on long body-control segments.
            nearest = min(nearest, edge_bound - (b - a).length / 8)
    return nearest, signed


def _finger_rings(rig, game, points, widgets, report, tree):
    from finger_controls import anatomical_frames
    frames = anatomical_frames(rig)
    for side in SIDES:
        for digit in DIGITS:
            names = _finger_names(side, digit)
            heads = [_head(game, name) for name in names]
            for i, name in enumerate(names):
                axis = (rig.matrix_world.to_3x3() @ Vector(frames['ORG-' + name]['longitudinal_axis'])).normalized()
                length = ((heads[i + 1] - heads[i]).length if i < 2 else (heads[i] - heads[i - 1]).length * .65)
                owned = points.get(name, [])
                u, v = _frame(axis)
                # Fit the actual skin cross-section, then check every edge
                # against the complete body (including neighboring digits).
                # A vertex-only radius cannot detect triangles crossing the
                # ring between vertices, or the adjoining finger's surface.
                best = None
                for fraction in (.45, .65, .85, .95, 1.1, 1.3):
                    center = heads[i] + axis * (length * fraction)
                    section = [p for p in owned if abs((p - center).dot(axis)) < .007 and
                        ((p - center) - axis * (p - center).dot(axis)).length < .05]
                    hit, normal, _, _ = tree.find_nearest(center)
                    if (center - hit).dot(normal) > .0005:
                        continue
                    for step in range(92):
                        radius = .009 + step * .001
                        if best and radius >= best[0]:
                            break
                        path = _circle(center, u, v, radius)
                        clearance, signed = _surface_clearance([path], tree)
                        if clearance >= .0025 and signed >= .002:
                            best = (radius, center.copy(), path, len(section), clearance)
                            break
                if best is None:
                    raise ValueError('No clear finger ring could be fitted: ' + name)
                radius, center, path, count, clearance = best
                _shape(rig, widgets, 'ORG-' + name, [path], 'finger_ring')
                report['finger_rings'].append({'control': 'ORG-' + name, 'center': list(center),
                    'axis': list(axis), 'radius': radius, 'sample_count': count,
                    'measured_body_surface_clearance': clearance})


def _hand_boxes(rig, game, points, widgets):
    for side in SIDES:
        wrist = _head(game, 'j_' + side + 'hand')
        index = _head(game, 'j_' + side + 'handindex1')
        pinky = _head(game, 'j_' + side + 'handpinky1')
        middle = _head(game, 'j_' + side + 'handmiddle1')
        y = (middle - wrist).normalized()
        x = index - pinky
        x = (x - y * x.dot(y)).normalized()
        z = x.cross(y).normalized()
        palm = list(points.get('j_' + side + 'hand', []))
        for digit in DIGITS:
            for native in _finger_names(side, digit):
                palm += points.get(native, [])
        local = [Vector(((p - wrist).dot(x), (p - wrist).dot(y), (p - wrist).dot(z))) for p in palm]
        low, high = _bounds(local)
        low -= Vector((.015, .018, .012)); high += Vector((.015, .018, .012))
        # The thumb notch gives the box a recognisable hand/mitten silhouette.
        width, length = high.x - low.x, high.y - low.y
        profile = [(low.x, low.y), (high.x, low.y),
                   (high.x, low.y + length * .25),
                   (high.x + width * .20, low.y + length * .43),
                   (high.x + width * .20, low.y + length * .66),
                   (high.x, low.y + length * .7), (high.x, high.y),
                   (low.x, high.y)]
        mid = (low.z + high.z) * .5
        path = [wrist + x * a + y * b + z * mid for a, b in profile]
        for suffix in ('fk', 'ik'):
            name = f'j_{side}hand_ctrl_{suffix}'
            if name in rig.pose.bones:
                pb = _shape(rig, widgets, name, _extrude(path, z, high.z - low.z), 'hand_box')
                sources = ['j_' + side + 'hand'] + [n for digit in DIGITS for n in _finger_names(side, digit)]
                _box_fit(pb, wrist, [x, y, z], low, high, sources, len(profile))
        settings = 'CTRL-hand-settings-' + side
        if settings in rig.pose.bones:
            center = wrist + z * (high.z + .06)
            u, v = _frame(z)
            _shape(rig, widgets, settings, [_circle(center, u, v, .035)], 'hand_options')


def _foot_boxes(rig, game, points, widgets):
    for side in SIDES:
        ankle = _head(game, 'j_' + side + 'foot')
        toe = _head(game, 'j_' + side + 'toebase')
        y = toe - ankle; y.z = 0; y.normalize()
        z = Vector((0, 0, 1)); x = y.cross(z).normalized()
        owned = points.get('j_' + side + 'foot', []) + points.get('j_' + side + 'toebase', [])
        local = [Vector(((p - ankle).dot(x), (p - ankle).dot(y), (p - ankle).dot(z))) for p in owned]
        low, high = _bounds(local)
        low -= Vector((.04, .03, .02)); high += Vector((.04, .03, .02))
        width, length = high.x - low.x, high.y - low.y
        profile = [(low.x + .1 * width, low.y), (high.x - .1 * width, low.y),
                   (high.x, low.y + .65 * length), (high.x - .1 * width, high.y),
                   (low.x + .1 * width, high.y), (low.x, low.y + .65 * length)]
        mid = (low.z + high.z) * .5
        path = [ankle + x * a + y * b + z * mid for a, b in profile]
        for suffix in ('fk', 'ik'):
            name = f'j_{side}foot_ctrl_{suffix}'
            if name in rig.pose.bones:
                pb = _shape(rig, widgets, name, _extrude(path, z, high.z - low.z), 'foot_box')
                _box_fit(pb, ankle, [x, y, z], low, high,
                         ['j_' + side + 'foot', 'j_' + side + 'toebase'], len(profile))


def _body_rings(rig, game, points, widgets, report):
    for name, source in [('torso', 'j_spine'), ('hips', 'j_hips'), ('chest', 'j_spine1'),
                         ('j_hips_ctrl_fk', 'j_hips'), ('j_spine_ctrl_fk', 'j_spine'),
                         ('j_spine1_ctrl_fk', 'j_spine1')]:
        if name not in rig.pose.bones:
            continue
        center = rig.matrix_world @ rig.data.bones[name].head_local
        owned = points.get(source, [])
        section = [p for p in owned if abs(p.z - center.z) < .06] or owned
        low, high = _bounds(section)
        c = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, center.z))
        rx, ry = max((high.x - low.x) / 2, .05), max((high.y - low.y) / 2, .05)
        fit = max(math.sqrt(((p.x - c.x) / rx) ** 2 + ((p.y - c.y) / ry) ** 2) for p in section)
        path = _circle(c, Vector((1, 0, 0)), Vector((0, 1, 0)), rx * fit + .035, ry * fit + .035, count=96)
        _shape(rig, widgets, name, [path], 'body_ring')
        report['body_rings'].append({'control': name, 'source': source, 'center': list(c),
            'radii': [rx * fit + .035, ry * fit + .035], 'section_half_height': .06,
            'minimum_axis_margin': .035,
            'clearance_scope': 'Encloses its trunk/hip cross-section; tail, pack and limbs may cross the loop plane.'})


def _shoulders(rig, game, points, widgets, groups, tree):
    for side in SIDES:
        native = 'j_' + side + 'shoulder'
        name = 'ORG-' + native
        if name not in rig.pose.bones:
            continue
        low, high = _bounds(points[native])
        x = low.x - .035 if side == 'left' else high.x + .035
        center = Vector((x, (low.y + high.y) / 2, (low.z + high.z) / 2))
        ry, rz = (high.y - low.y) / 2 + .035, (high.z - low.z) / 2 + .035
        for offset in range(100):
            c = center + Vector(((-1 if side == 'left' else 1) * offset * .005, 0, 0))
            outer, inner = [], []
            for i in range(41):
                t = math.radians(35 + 290 * i / 40)
                outer.append(c + Vector((0, ry * math.cos(t), rz * math.sin(t))))
                inner.append(c + Vector((0, .035 + (ry - .045) * math.cos(t), (rz - .045) * math.sin(t))))
            path = outer + inner[::-1]
            clearance, signed = _surface_clearance([path], tree)
            if clearance >= .004:
                break
        else:
            raise ValueError('No clear shoulder crescent could be fitted: ' + name)
        _promote(rig, groups, name, 'Shoulders')
        _shape(rig, widgets, name, [path], 'shoulder_crescent')


def _face(rig, game, points, widgets, groups, report):
    names = ['j_jaw', 'j_nose', 'j_leftear', 'j_rightear']
    names += [f'j_{side}eyelid{part}' for side in SIDES for part in ('top', 'bottom')]
    names += [f'j_{side}eyebrow{i}' for side in SIDES for i in (1, 2, 3)]
    names += [b.name for b in game.data.bones if b.name.startswith('j_lip_')]
    for native in names:
        name = 'ORG-' + native
        if name not in rig.pose.bones:
            continue
        owned = points.get(native, [])
        if not owned:
            report['unweighted_face_channels'].append(native)
            continue
        low, high = _bounds(owned)
        center = Vector(((low.x + high.x) / 2, high.y + .015, (low.z + high.z) / 2))
        rx, rz = max((high.x - low.x) / 2 + .012, .014), max((high.z - low.z) / 2 + .01, .012)
        if 'eyebrow' in native:
            # Arc at the brow, rather than a circle obscuring the eye.
            path = [center + Vector((rx * math.cos(math.pi * i / 24), 0,
                                    rz * .35 * math.sin(math.pi * i / 24))) for i in range(25)]
            paths, closed, kind = [path], False, 'eyebrow_arc'
        else:
            paths = [_circle(center, Vector((1, 0, 0)), Vector((0, 0, 1)), rx, rz)]
            closed, kind = True, 'mouth_oval' if native == 'j_jaw' else 'face_oval'
        _promote(rig, groups, name, 'Face')
        _shape(rig, widgets, name, paths, kind, closed)
        report['face_channels'].append(native)
    top = max(p.z for p in points['j_head']) + .07
    center = _head(game, 'j_head'); center.z = top
    paths = []
    for i in range(4):
        u = Vector((math.cos(i * math.pi / 2), math.sin(i * math.pi / 2), 0))
        v = Vector((-u.y, u.x, 0))
        stem = [center + u * (.02 + .17 * j / 12) - Vector((0, 0, .018 * (j / 12) ** 2)) for j in range(13)]
        tip = stem[-1] + u * .055 - Vector((0, 0, .012))
        paths += [stem, [stem[-1] + v * .035, tip, stem[-1] - v * .035]]
    _shape(rig, widgets, 'ORG-j_head', paths, 'head_arrow_cross', False)
    report['unsupported_face_requests'] = [
        {'request': 'tongue', 'reason': 'No tongue channel exists in the preserved 138-bone GAME skeleton.'}]


def _backpack(rig, points, widgets):
    owned = points['j_backpack']
    center = sum(owned, Vector()) / len(owned)
    yy = sum((p.y - center.y) ** 2 for p in owned)
    zz = sum((p.z - center.z) ** 2 for p in owned)
    yz = sum((p.y - center.y) * (p.z - center.z) for p in owned)
    angle = .5 * math.atan2(2 * yz, zz - yy)
    z = Vector((0, math.sin(angle), math.cos(angle)))
    x = Vector((1, 0, 0)); y = z.cross(x)
    axes = [x, y, z]
    local = [Vector(tuple((p - center).dot(axis) for axis in axes)) for p in owned]
    low, high = _bounds(local)
    low -= Vector((.025, .025, .025)); high += Vector((.025, .025, .025))
    pb = _shape(rig, widgets, 'ORG-j_backpack', _box(center, axes, low, high), 'backpack_box')
    _box_fit(pb, center, axes, low, high, ['j_backpack'])


def _belt_arcs(rig, points, widgets, groups, report):
    all_points = [p for i in range(1, 6) for p in points.get('j_loot_sack_component' + str(i), [])]
    if not all_points:
        return
    low, high = _bounds(all_points)
    center = (low + high) / 2
    rx, ry = (high.x - low.x) / 2, (high.y - low.y) / 2
    fit = max(math.sqrt(((p.x - center.x) / rx) ** 2 + ((p.y - center.y) / ry) ** 2) for p in all_points)
    rx, ry = rx * fit + .025, ry * fit + .025
    for name in groups.get('Belt corrections', []):
        pivot = rig.matrix_world @ rig.data.bones[name].head_local
        angle = math.atan2((pivot.y - center.y) / ry, (pivot.x - center.x) / rx)
        top, bottom = [], []
        for i in range(25):
            t = angle - .36 + .72 * i / 24
            p = Vector((center.x + rx * math.cos(t), center.y + ry * math.sin(t), pivot.z))
            top.append(p + Vector((0, 0, .009)))
            bottom.append(p - Vector((0, 0, .009)))
        _shape(rig, widgets, name, [top + bottom[::-1]], 'belt_surface_arc')
        report['belt_arcs'].append({'control': name, 'center': list(center), 'radii': [rx, ry],
                                   'source_bounds': [list(low), list(high)], 'radial_margin': .025})


def _twists(rig, widgets, groups, report):
    groups['Twist'] = []
    # The dedicated roll output replaces the inherited distal forearm tweak
    # widget, not its solver bone or any stored animation channels.
    for side in SIDES:
        for old in ('ORG-j_' + side + 'forearmroll', 'j_' + side + 'forearm_ctrl_tweak.001'):
            if old in rig.pose.bones:
                rig.pose.bones[old].custom_shape = None
                rig.pose.bones[old].bone.hide = True
                rig.pose.bones[old].bone.hide_select = True
                report['hidden_duplicate_widgets'].append(old)
                for names in groups.values():
                    if old in names:
                        names.remove(old)
    if 'CTRL-weapon' in rig.pose.bones and 'ORG-j_leftweaponattach' in rig.pose.bones:
        old = rig.pose.bones['ORG-j_leftweaponattach']
        old.custom_shape = None
        old.bone.hide = True
        old.bone.hide_select = True
        report['hidden_duplicate_widgets'].append(old.name)
        for names in groups.values():
            if old.name in names:
                names.remove(old.name)
    for pb in rig.pose.bones:
        if (pb.name.startswith('j_') and '_ctrl_tweak' in pb.name and any(word in pb.name for word in ('arm', 'leg'))):
            # Rigify's DEF-only tweaks do not feed the preserved native ORG
            # output. Never advertise an inert control as a working twist.
            pb.custom_shape = None
            pb.bone.hide = True
            pb.bone.hide_select = True
            if pb.name not in report['hidden_duplicate_widgets']:
                report['hidden_inert_widgets'].append(pb.name)
            for names in groups.values():
                if pb.name in names:
                    names.remove(pb.name)
    for pb in rig.pose.bones:
        if not pb.custom_shape or pb.bone.hide:
            continue
        if pb.name.startswith(('CTRL-forearm-twist-', 'CTRL-native-twist-')):
            center = rig.matrix_world @ pb.bone.head_local
            radius = .045 if pb.name.startswith('CTRL-forearm') else .035
            axes = [Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))]
            _shape(rig, widgets, pb.name,
                   [_circle(center, axes[a], axes[b], radius, count=32) for a, b in ((0, 1), (1, 2), (2, 0))],
                   'twist_sphere')
            if pb.name not in groups.setdefault('Twist', []):
                groups['Twist'].append(pb.name)
            report['twist_spheres'].append(pb.name)


def _color(pb):
    technical = pb.name.startswith(('CTRL-hand-settings-', 'CTRL-shape-')) or (
        all(pb.lock_location) and all(pb.lock_rotation) and any(not k.startswith('_') for k in pb.keys()))
    category = ('technical' if technical else 'left' if 'left' in pb.name.lower()
                else 'right' if 'right' in pb.name.lower() else 'center')
    pb.color.palette = 'CUSTOM'
    pb.color.custom.normal = COLORS[category]
    pb.color.custom.select = tuple(min(1, c * .55 + .45) for c in COLORS[category])
    pb.color.custom.active = tuple(min(1, c * .3 + .7) for c in COLORS[category])
    pb['warlock_color_category'] = category
    return category


def apply_widgets(rig, game, mesh, groups, widgets):
    """Fit all requested controls; return a source-measured display manifest.

    Run once after other controls (including weapon controls) have been added,
    before serializing the rig manifest.  No action, rest frame or deform data
    is changed.  Existing action paths remain valid when a duplicate widget is
    suppressed; its underlying mechanism is deliberately preserved.
    """
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    points = _group_points(mesh)
    tree = _mesh_tree(mesh)
    report = {'schema': 1, 'finger_rings': [], 'body_rings': [], 'belt_arcs': [], 'face_channels': [],
              'unweighted_face_channels': [], 'hidden_duplicate_widgets': [], 'twist_spheres': [],
              'hidden_inert_widgets': [],
              'color_scheme': {k: list(v) for k, v in COLORS.items()}}
    _finger_rings(rig, game, points, widgets, report, tree)
    _hand_boxes(rig, game, points, widgets)
    _foot_boxes(rig, game, points, widgets)
    _body_rings(rig, game, points, widgets, report)
    _shoulders(rig, game, points, widgets, groups, tree)
    _face(rig, game, points, widgets, groups, report)
    _backpack(rig, points, widgets)
    _belt_arcs(rig, points, widgets, groups, report)
    _twists(rig, widgets, groups, report)
    report['controls'] = {}
    for pb in rig.pose.bones:
        if pb.custom_shape and not pb.name.startswith(('DEF-', 'MCH-')):
            category = _color(pb)
            report['controls'][pb.name] = {'color': category, 'kind': pb.get('warlock_widget_kind', 'rigify_original'),
                                          'hidden': pb.bone.hide}
    rig['warlock_widget_manifest'] = json.dumps(report)
    return report
