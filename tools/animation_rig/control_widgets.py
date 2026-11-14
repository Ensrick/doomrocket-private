"""Artist-facing shapes for the existing Warlock control rig.

Widgets are edge meshes, as expected by Blender custom bone shapes.  Their
vertices are calibrated in the neutral model's world frame, then converted to
each controller's local frame.  Imported FBX bone Y axes are not anatomical
finger/foot directions, so simply rotating a unit circle is insufficient.
This module changes display/selection only; it never edits GAME bones, skin,
constraints, drivers, or animation keys.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree


COLORS = {
    'left': (1.0, 0.22, 0.16),
    'right': (0.16, 0.48, 1.0),
    'center': (1.0, 0.82, 0.10),
    'technical': (0.73, 0.51, 0.88),
}
SIDES = ('left', 'right')
DIGITS = ('thumb', 'index', 'middle', 'ring', 'pinky')
BASELINE_KEY = 'warlock_original_widget_baseline'
FIRST_DISPLAY_SHA256 = '3e5e2ee48909c6dd5234747fabd43d35e00fc27e41964034388304cee602609d'
ORIGINAL_GEOMETRY_SHA256 = {
    'root': 'b833a6a8222c17c2ea427b1815f91bba75ee4a8ef391de75d90c4991171dd1f0',
    'torso': '19d2f68a4ef2a9c19322ed8a32476b68e8b4fcf93d2972d626e7f3502fc05ee5',
    'hips': '78ad966848e0349a6f4b6dce28743038b4c0474e9dd4f794c3325fe15a5a31e3',
    'chest': '78ad966848e0349a6f4b6dce28743038b4c0474e9dd4f794c3325fe15a5a31e3',
    'j_hips_ctrl_fk': '1be23a21159eb382ba567c532383da8926b28639319141def36c4b37b9f48051',
    'j_spine_ctrl_fk': '1be23a21159eb382ba567c532383da8926b28639319141def36c4b37b9f48051',
    'j_spine1_ctrl_fk': '2ceb2779d643b8421853cc46a8ebab85f6aa299f47c31d562dfebae0d3bcf64e',
    'j_tail1_ctrl_master': 'df051d2c52d15ef928fd1e4a004f774ce05190a60e55fbb83fc2881a3dc22328',
}
for _side in SIDES:
    ORIGINAL_GEOMETRY_SHA256[f'j_{_side}hand_ctrl_ik'] = '3953b519df5461202ce40ca1fa3a747f407f3434ed7b7126901b0e3677dc0e16'
    ORIGINAL_GEOMETRY_SHA256[f'j_{_side}foot_ctrl_ik'] = '8d0eb4dc4256dacc55ca4c9decebd419820fb508cf2ff266cef0dd080ff0ad40'
    for _part in ('hand', 'foot'):
        ORIGINAL_GEOMETRY_SHA256[f'j_{_side}{_part}_ctrl_fk'] = 'd17d611cd8cfd88fbf08947f569d2b4583c0992922abf337122316149c7959fe'


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _display_record(pb):
    obj = pb.custom_shape
    if not obj or obj.type != 'MESH':
        raise ValueError('Expected an original edge-mesh widget: ' + pb.name)
    return {'type': obj.type, 'object_matrix': [list(row) for row in obj.matrix_world],
        'scale': list(pb.custom_shape_scale_xyz), 'translation': list(pb.custom_shape_translation),
        'rotation': list(pb.custom_shape_rotation_euler), 'size_by_bone': pb.use_custom_shape_bone_size,
        'transform': pb.custom_shape_transform.name if pb.custom_shape_transform else None,
        'vertices': [list(v.co) for v in obj.data.vertices], 'edges': [list(e.vertices) for e in obj.data.edges]}


def _validate_original_widgets(records):
    rows = records['controls']
    for name, expected in ORIGINAL_GEOMETRY_SHA256.items():
        row = rows.get(name)
        if row is None or _digest({k: row[k] for k in ('vertices', 'edges')}) != expected:
            raise ValueError('First-version display baseline mismatch: ' + name)
    if _digest(rows) != records['display_sha256']:
        raise ValueError('First-version display records failed their content hash')


def capture_original_widgets(rig):
    """Capture the OPENED original scene as plain data before loading a target.

    October 10 and October 11 share all 145 shape records exactly. No Blender
    datablock reference escapes this function, so a caller can then open 1.1
    without losing this baseline. Fresh builders also pass the pinned inherited
    geometry check; new functional helper controls do not change that geometry.
    """
    rows = {pb.name: _display_record(pb) for pb in rig.pose.bones if pb.custom_shape}
    source = Path(bpy.data.filepath)
    records = {'schema': 1, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest()
               if source.is_file() else None, 'display_sha256': _digest(rows), 'controls': rows}
    _validate_original_widgets(records)
    return records


def restore_original_widgets(rig, widgets, records):
    """Restore display only; never replace a bone, action, driver or constraint."""
    _validate_original_widgets(records)
    for name, row in records['controls'].items():
        if name not in rig.pose.bones:
            raise ValueError('Original control channel is missing: ' + name)
        pb = rig.pose.bones[name]
        data = bpy.data.meshes.new('WGT-Warlock-original-' + name)
        data.from_pydata(row['vertices'], row['edges'], [])
        obj = bpy.data.objects.new(data.name, data)
        widgets.objects.link(obj)
        obj.matrix_world = Matrix(row['object_matrix'])
        obj.hide_render = True
        pb.custom_shape = obj
        pb.custom_shape_scale_xyz = row['scale']
        pb.custom_shape_translation = row['translation']
        pb.custom_shape_rotation_euler = row['rotation']
        pb.use_custom_shape_bone_size = row['size_by_bone']
        pb.custom_shape_transform = rig.pose.bones.get(row['transform']) if row['transform'] else None
        for key in ('warlock_widget_box_fit', 'warlock_widget_world_bounds', 'warlock_widget_kind'):
            if key in pb:
                del pb[key]
    rig[BASELINE_KEY] = json.dumps(records)


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


def _edge_shape(rig, widgets, name, points, edges, kind):
    pb = rig.pose.bones[name]
    inverse = (rig.matrix_world @ pb.bone.matrix_local).inverted()
    data = bpy.data.meshes.new('WGT-Warlock-' + name)
    data.from_pydata([inverse @ p for p in points], edges, [])
    obj = bpy.data.objects.new(data.name, data); widgets.objects.link(obj)
    obj.hide_render = True
    pb.custom_shape = obj; pb.use_custom_shape_bone_size = False
    pb.custom_shape_scale_xyz = (1, 1, 1); pb.custom_shape_translation = (0, 0, 0)
    pb.custom_shape_rotation_euler = (0, 0, 0); pb.custom_shape_transform = None
    pb['warlock_widget_kind'] = kind
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


def _mesh_components(mesh):
    """Geometric islands distinguish rigid pack hardware from flexible straps."""
    parents = list(range(len(mesh.data.vertices)))
    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]; i = parents[i]
        return i
    for edge in mesh.data.edges:
        a, b = map(find, edge.vertices); parents[b] = a
    names = {g.index: g.name for g in mesh.vertex_groups}
    parts = {}
    for vertex in mesh.data.vertices:
        row = parts.setdefault(find(vertex.index), {'indices': [], 'materials': set(), 'weights': {}, 'rigid_pack': True})
        row['indices'].append(vertex.index)
        weights = {names[g.group]: g.weight for g in vertex.groups}
        row['rigid_pack'] &= weights.get('j_backpack', 0) >= .999
        for name, weight in weights.items():
            row['weights'][name] = row['weights'].get(name, 0) + weight
    for poly in mesh.data.polygons:
        parts[find(poly.vertices[0])]['materials'].add(mesh.data.materials[poly.material_index].name)
    return list(parts.values())


def _display_frame(rig, pb):
    frame = rig.matrix_world @ (pb.custom_shape_transform or pb).bone.matrix_local
    scale = Vector(pb.custom_shape_scale_xyz)
    if pb.use_custom_shape_bone_size:
        scale *= pb.bone.length
    return frame @ Matrix.Translation(pb.custom_shape_translation) @ Euler(pb.custom_shape_rotation_euler).to_matrix().to_4x4() @ Matrix.Diagonal((*scale, 1))


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


def _hands_and_settings(rig, game, widgets, report):
    for side in SIDES:
        wrist = _head(game, 'j_' + side + 'hand')
        index = _head(game, 'j_' + side + 'handindex1')
        pinky = _head(game, 'j_' + side + 'handpinky1')
        middle = _head(game, 'j_' + side + 'handmiddle1')
        forward = (middle - wrist).normalized()
        across = (index - pinky).normalized()
        across = (across - forward * across.dot(forward)).normalized()
        normal = forward.cross(across).normalized()
        if normal.z < 0:
            normal = -normal
        for suffix in ('fk', 'ik'):
            name = f'j_{side}hand_ctrl_{suffix}'
            if name in rig.pose.bones:
                pb = rig.pose.bones[name]
                bone_rotation = (rig.matrix_world @ pb.bone.matrix_local).to_quaternion()
                original = Euler(pb.custom_shape_rotation_euler).to_quaternion()
                old_forward = bone_rotation @ original @ Vector((0, 1, 0))
                turn = old_forward.rotation_difference(forward)
                amount = min(1, math.radians(6) / max(turn.angle, 1e-8))
                turn = Quaternion().slerp(turn, amount)
                adjusted = bone_rotation.inverted() @ turn @ bone_rotation @ original
                pb.custom_shape_rotation_euler = adjusted.to_euler('XYZ')
                offset = (rig.matrix_world @ pb.bone.matrix_local).to_3x3().inverted() @ (forward * .012)
                pb.custom_shape_translation = Vector(pb.custom_shape_translation) + offset
                pb['warlock_widget_kind'] = 'original_hand_adjusted'
                report['original_adjustments'][name] = {'translation_world': list(forward * .012),
                    'maximum_rotation_degrees': 6, 'scale_multiplier': 1.}
        settings = 'CTRL-hand-settings-' + side
        if settings in rig.pose.bones:
            # Five discrete triangle silhouettes on the existing settings bone.
            # Every triangle selects that same Item panel/per-digit properties;
            # no duplicate animated settings path is introduced.
            center = wrist + forward * .012 + normal * .045
            paths = []
            for digit in DIGITS:
                ray = _head(game, _finger_names(side, digit)[0]) - wrist
                ray -= normal * ray.dot(normal); ray.normalize()
                tip = center + ray * .052
                base = center + ray * .035
                transverse = normal.cross(ray).normalized() * .005
                paths.append([base - transverse, tip, base + transverse])
            _shape(rig, widgets, settings, paths, 'hand_options_five_triangles')
            report['hand_settings'].append({'control': settings, 'triangles': 5,
                'wrist': list(wrist), 'center': list(center), 'normal': list(normal),
                'selection': 'All five handles select the existing hand settings and its per-digit properties.'})


def _feet(rig, game, points, report):
    for side in SIDES:
        ankle = _head(game, 'j_' + side + 'foot')
        toe = _head(game, 'j_' + side + 'toebase')
        forward = toe - ankle; forward.z = 0; forward.normalize()
        for suffix in ('fk', 'ik'):
            name = f'j_{side}foot_ctrl_{suffix}'
            if name in rig.pose.bones:
                pb = rig.pose.bones[name]
                frame = _display_frame(rig, pb)
                original = [frame @ v.co for v in pb.custom_shape.data.vertices]
                low = min(p.dot(forward) for p in original)
                high = max(p.dot(forward) for p in original)
                toes = [p.dot(forward) for p in points['j_' + side + 'toebase']]
                uncovered = lambda distance: sum(max(0, low + distance - p, p - high - distance) for p in toes) / len(toes)
                # Rat paws do not align with the generated human-foot box's
                # center. Fit the direction from actual toe skin, not merely
                # the ankle-to-toebase joint vector. Keep the adjustment small
                # and leave the original scale, silhouette and pose untouched.
                distance = min((-.025, 0., .025), key=lambda d: (uncovered(d), abs(d)))
                world_offset = forward * distance
                offset = (rig.matrix_world @ pb.bone.matrix_local).to_3x3().inverted() @ world_offset
                pb.custom_shape_translation = Vector(pb.custom_shape_translation) + offset
                pb['warlock_widget_kind'] = 'original_foot_translated'
                report['original_adjustments'][name] = {'translation_world': list(world_offset),
                    'scale_multiplier': 1., 'rotation_delta_degrees': 0., 'toe_projection_axis': list(forward),
                    'toe_uncovered_before_m': uncovered(0), 'toe_uncovered_after_m': uncovered(distance),
                    'fit_scope': 'Mean weighted-toe vertex distance outside the longitudinal display interval.'}


def _body_and_root(rig, report):
    for name in ('torso', 'hips', 'chest', 'j_hips_ctrl_fk', 'j_spine_ctrl_fk', 'j_spine1_ctrl_fk'):
        if name not in rig.pose.bones:
            continue
        pb = rig.pose.bones[name]
        pb.custom_shape_scale_xyz = Vector(pb.custom_shape_scale_xyz) * 1.04
        pb['warlock_widget_kind'] = 'original_body_slight_resize'
        report['original_adjustments'][name] = {'scale_multiplier': 1.04,
            'shape_and_count_unchanged': True, 'translation_delta': [0, 0, 0], 'rotation_delta_degrees': 0.}
    root = rig.pose.bones['root']
    root.custom_shape_scale_xyz = Vector(root.custom_shape_scale_xyz) * .5
    root['warlock_widget_kind'] = 'original_root_half_size'
    report['original_adjustments']['root'] = {'scale_multiplier': .5}


def _shoulders(rig, mesh, components, widgets, groups, report, tree):
    for side in SIDES:
        native = 'j_' + side + 'shoulder'
        name = 'ORG-' + native
        if name not in rig.pose.bones:
            continue
        plates = [c for c in components if c['weights'].get(native, 0) / len(c['indices']) > .6 and
                  any(m.startswith('DoomRocket_Armor') for m in c['materials'])]
        if not plates:
            raise ValueError('No shoulder-plate island matched: ' + side)
        plate = max(plates, key=lambda c: len(c['indices']))
        owned = [mesh.matrix_world @ mesh.data.vertices[i].co for i in plate['indices']]
        low, high = _bounds(owned)
        center = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, high.z + .025))
        rx, ry = min((high.x - low.x) * .36, .07), min((high.y - low.y) * .30, .09)
        for offset in range(16):
            c = center + Vector((0, 0, offset * .003))
            # A saddle-shaped folded circle, not a large side-facing crescent.
            path = [c + Vector((rx * math.cos(i * math.tau / 48),
                    ry * math.sin(i * math.tau / 48), .012 * math.cos(i * math.tau / 24))) for i in range(48)]
            clearance, signed = _surface_clearance([path], tree)
            if clearance >= .0025:
                break
        else:
            raise ValueError('No clear folded shoulder circle could be fitted: ' + name)
        _promote(rig, groups, name, 'Shoulders')
        _shape(rig, widgets, name, [path], 'shoulder_folded_circle')
        report['shoulders'].append({'control': name, 'plate_first_vertex': min(plate['indices']),
            'plate_vertices': len(plate['indices']), 'plate_bounds': [list(low), list(high)],
            'center': list(c), 'radii': [rx, ry], 'fold_amplitude': .012,
            'full_body_clearance_bound_m': clearance})


def _face(rig, game, points, widgets, groups, report, original):
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
        center = Vector(((low.x + high.x) / 2, high.y + .009, (low.z + high.z) / 2))
        if native == 'j_jaw':
            rx, rz = .04, .018
        elif 'ear' in native:
            rx, rz = .022, .03
        elif native == 'j_nose':
            rx, rz = .018, .012
        elif 'lip_' in native:
            rx, rz = .010, .007
        else:
            rx, rz = .016, .009
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
    top = max(p.z for p in points['j_head']) + .025
    center = _head(game, 'j_head'); center.z = top; center.y += .03
    reference = original['controls']['j_tail1_ctrl_master']
    minimum_y = min(v[1] for v in reference['vertices'])
    shape_scale = .42
    head_points = [center + Vector((v[0], v[2], v[1] - minimum_y)) * shape_scale for v in reference['vertices']]
    _edge_shape(rig, widgets, 'ORG-j_head', head_points, reference['edges'], 'head_tailmaster_cross')
    report['head_reference'] = {'source': 'j_tail1_ctrl_master', 'source_geometry_sha256':
        ORIGINAL_GEOMETRY_SHA256['j_tail1_ctrl_master'], 'scale': shape_scale, 'center': list(center),
        'minimum_source_y': minimum_y}
    report['unsupported_face_requests'] = [
        {'request': 'tongue', 'reason': 'No tongue channel exists in the preserved 138-bone GAME skeleton.'}]


def _backpack(rig, mesh, components, widgets, report):
    hardware = [c for c in components if c['rigid_pack'] and
                any(m.startswith('DoomRocket_Backpack') for m in c['materials'])]
    straps = [c for c in components if not c['rigid_pack'] and
              any(m.startswith('DoomRocket_Backpack') for m in c['materials'])]
    selected = sorted(i for c in hardware for i in c['indices'])
    if not selected or not straps:
        raise ValueError('Expected separate rigid pack hardware and articulated strap islands')
    owned = [mesh.matrix_world @ mesh.data.vertices[i].co for i in selected]
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
    low -= Vector((.012, .012, .012)); high += Vector((.012, .012, .012))
    pb = _shape(rig, widgets, 'ORG-j_backpack', _box(center, axes, low, high), 'backpack_box')
    _box_fit(pb, center, axes, low, high, ['j_backpack'])
    fit = json.loads(pb['warlock_widget_box_fit']); fit['mask'] = 'rigid_pack_components_without_straps'
    fit['vertex_indices'] = selected; pb['warlock_widget_box_fit'] = json.dumps(fit)
    report['backpack'] = {'included_vertices': len(selected), 'rigid_components': len(hardware),
        'excluded_strap_components': [min(c['indices']) for c in straps],
        'selected_indices_sha256': _digest(selected), 'margin_m': .012,
        'scope': 'Only wholly j_backpack-weighted Backpack-material islands; mixed shoulder/spine strap islands excluded.'}


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
        outer, inner = [], []
        for i in range(25):
            t = angle - .17 + .34 * i / 24
            p = Vector((center.x + rx * math.cos(t), center.y + ry * math.sin(t), pivot.z))
            radial = Vector((math.cos(t), math.sin(t), 0))
            outer.append(p + radial * .004)
            inner.append(p - radial * .004)
        _shape(rig, widgets, name, [outer + inner[::-1]], 'belt_perpendicular_arc')
        report['belt_arcs'].append({'control': name, 'center': list(center), 'radii': [rx, ry],
            'source_bounds': [list(low), list(high)], 'radial_margin': .025,
            'plane_normal': [0, 0, 1], 'perpendicular_to': 'vertical waist/belt surface', 'radial_half_width': .004})


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


def apply_widgets(rig, game, mesh, groups, widgets, *, first_widgets=None):
    """Fit all requested controls; return a source-measured display manifest.

    Run once after other controls (including weapon controls) have been added,
    before serializing the rig manifest.  No action, rest frame or deform data
    is changed.  Existing action paths remain valid when a duplicate widget is
    suppressed; its underlying mechanism is deliberately preserved.
    """
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    if first_widgets is None:
        stored = rig.get(BASELINE_KEY)
        first_widgets = json.loads(stored) if stored else capture_original_widgets(rig)
    restore_original_widgets(rig, widgets, first_widgets)
    points = _group_points(mesh)
    components = _mesh_components(mesh)
    tree = _mesh_tree(mesh)
    report = {'schema': 2, 'finger_rings': [], 'body_rings': [], 'belt_arcs': [], 'face_channels': [],
              'unweighted_face_channels': [], 'hidden_duplicate_widgets': [], 'twist_spheres': [],
              'hidden_inert_widgets': [], 'original_adjustments': {}, 'hand_settings': [], 'shoulders': [],
              'first_display_source_sha256': first_widgets['source_sha256'],
              'first_display_sha256': first_widgets['display_sha256'],
              'first_display_shape_count': len(first_widgets['controls']),
              'color_scheme': {k: list(v) for k, v in COLORS.items()}}
    _finger_rings(rig, game, points, widgets, report, tree)
    _hands_and_settings(rig, game, widgets, report)
    _feet(rig, game, points, report)
    _body_and_root(rig, report)
    _shoulders(rig, mesh, components, widgets, groups, report, tree)
    _face(rig, game, points, widgets, groups, report, first_widgets)
    _backpack(rig, mesh, components, widgets, report)
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
