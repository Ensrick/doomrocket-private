"""Numerical control-display checks, independent of runtime acceptance.

Run Blender 5.2 --background --factory-startup --disable-autoexec --python
test_widgets_blender.py -- --rig candidate.blend --output widgets.json.
No source scene is saved, no image is rendered, and no pose is changed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from control_widgets import BASELINE_KEY, COLORS, FIRST_DISPLAY_SHA256, apply_widgets, capture_original_widgets


def shape_points(rig, bone):
    frame = rig.matrix_world @ (bone.custom_shape_transform or bone).bone.matrix_local
    scale = Vector(bone.custom_shape_scale_xyz)
    if bone.use_custom_shape_bone_size:
        scale *= bone.bone.length
    frame = frame @ Matrix.Translation(bone.custom_shape_translation) @ Euler(bone.custom_shape_rotation_euler).to_matrix().to_4x4() @ Matrix.Diagonal((*scale, 1))
    return [frame @ v.co for v in bone.custom_shape.data.vertices]


def clearance(rig, bone, tree):
    points = shape_points(rig, bone)
    lower_bound = float('inf')
    for edge in bone.custom_shape.data.edges:
        a, b = (points[i] for i in edge.vertices)
        steps = max(16, math.ceil((b - a).length / .008))
        distances = [tree.find_nearest(a.lerp(b, t / steps))[3] for t in range(steps + 1)]
        lower_bound = min(lower_bound, min(distances) - (b - a).length / (2 * steps))
    return lower_bound


def point_edge_distance(p, a, b):
    span = b - a
    t = max(0, min(1, (p - a).dot(span) / span.length_squared))
    return (p - (a + span * t)).length


def polygon_contains(p, polygon):
    inside = False
    for i, a in enumerate(polygon):
        b = polygon[(i + 1) % len(polygon)]
        if (a.y > p.y) != (b.y > p.y) and p.x < (b.x - a.x) * (p.y - a.y) / (b.y - a.y) + a.x:
            inside = not inside
    return inside


def main(args):
    source_sha256 = hashlib.sha256(args.rig.read_bytes()).hexdigest()
    first = None
    if args.first:
        bpy.ops.wm.open_mainfile(filepath=str(args.first.resolve()), use_scripts=False)
        first = capture_original_widgets(bpy.data.objects['WARLOCK_CTRL'])
    bpy.ops.wm.open_mainfile(filepath=str(args.rig.resolve()), use_scripts=False)
    rig, game = (bpy.data.objects[n] for n in ('WARLOCK_CTRL', 'WARLOCK_GAME'))
    mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and len(o.data.vertices) == 29123)
    if args.decorate:
        groups = json.loads(rig['warlock_control_manifest'])['groups']
        collection = bpy.data.collections.new('Widget isolated verification')
        bpy.context.scene.collection.children.link(collection)
        apply_widgets(rig, game, mesh, groups, collection, first_widgets=first)
    manifest = json.loads(rig['warlock_widget_manifest'])
    baseline = json.loads(rig[BASELINE_KEY])
    vertices = [mesh.matrix_world @ v.co for v in mesh.data.vertices]
    all_tree = BVHTree.FromPolygons(vertices, [tuple(p.vertices) for p in mesh.data.polygons])
    group_names = {g.index: g.name for g in mesh.vertex_groups}
    indices = {}
    for v in mesh.data.vertices:
        for g in v.groups:
            if g.weight > .05:
                indices.setdefault(group_names[g.group], set()).add(v.index)
    tests = []

    def check(name, passed, **evidence):
        tests.append({'name': name, 'passed': bool(passed), **evidence})
        print(('PASS ' if passed else 'FAIL ') + name, json.dumps(evidence))

    # Color all inherited controls too, rather than only newly promoted bones.
    color_errors = []
    for pb in rig.pose.bones:
        if pb.custom_shape and not pb.name.startswith(('MCH-', 'DEF-')):
            category = pb.get('warlock_color_category')
            if category not in COLORS or pb.color.palette != 'CUSTOM' or max(
                    abs(pb.color.custom.normal[i] - round(COLORS.get(category, (0, 0, 0))[i] * 255) / 255)
                    for i in range(3)) > 1e-5:
                color_errors.append(pb.name)
    check('all inherited and added controls use the four-category palette', not color_errors, errors=color_errors)
    check('left is red, right blue, center yellow and settings lilac',
          COLORS['left'][0] > .9 and COLORS['left'][2] < .3 and
          COLORS['right'][2] > .9 and COLORS['right'][0] < .3 and
          COLORS['center'][0] > .9 and COLORS['center'][1] > .75 and
          COLORS['technical'][0] > .6 and COLORS['technical'][2] > .8)
    first_digest = hashlib.sha256(json.dumps(baseline['controls'], sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()
    check('first October display baseline is independently pinned',
          first_digest == FIRST_DISPLAY_SHA256 and len(baseline['controls']) == 145,
          source_sha256=baseline['source_sha256'], display_sha256=first_digest,
          original_shapes=len(baseline['controls']))

    for item in manifest['finger_rings']:
        pb = rig.pose.bones[item['control']]
        points = shape_points(rig, pb)
        center = sum(points, Vector()) / len(points)
        normal = (points[1] - points[0]).cross(points[2] - points[1]).normalized()
        native = pb.name.removeprefix('ORG-')
        segment = int(native[-1]) if native[-1].isdigit() else 0
        if native.endswith('thumb2') or native.endswith(('index3', 'middle3', 'ring3', 'pinky3')):
            anatomical = (game.matrix_world @ game.data.bones[native].matrix_local).col[0].xyz.normalized()
        else:
            next_name = native.replace('inhandthumb', 'handthumb1') if 'inhandthumb' in native else native[:-1] + str(segment + 1)
            anatomical = (game.matrix_world @ game.data.bones[next_name].head_local -
                          game.matrix_world @ game.data.bones[native].head_local).normalized()
        radii = [(p - center).length for p in points]
        plane_error = max(abs((p - center).dot(normal)) for p in points)
        margin = clearance(rig, pb, all_tree)
        check(item['control'] + ' is a circular anatomical ring clear of all body triangles',
              len(points) == 48 and abs(normal.dot(anatomical)) > .9999 and plane_error < 1e-5 and
              max(radii) - min(radii) < 1e-5 and margin >= .0024,
              axis_alignment=abs(normal.dot(anatomical)), plane_error_m=plane_error,
              radius_m=sum(radii) / len(radii), full_body_clearance_bound_m=margin)
    check('all thirty digit segments have a ring', len(manifest['finger_rings']) == 30)

    for pb in rig.pose.bones:
        if 'warlock_widget_box_fit' not in pb:
            continue
        fit = json.loads(pb['warlock_widget_box_fit'])
        center = Vector(fit['center']); axes = [Vector(v) for v in fit['axes']]
        project = lambda p: Vector(tuple((p - center).dot(a) for a in axes))
        low, high = Vector(fit['low']), Vector(fit['high'])
        owned = set(fit['vertex_indices']) if 'vertex_indices' in fit else set().union(*(indices.get(n, set()) for n in fit['sources']))
        source = [project(vertices[i]) for i in owned]
        actual = [project(p) for p in shape_points(rig, pb)]
        margin = min(min(p[a] - low[a], high[a] - p[a]) for p in source for a in range(3))
        n = fit['profile_count']
        profile_errors, profile_margin = 0, float('inf')
        if n:
            polygon = [p.xy for p in actual[:n]]
            for p in source:
                if not polygon_contains(p.xy, polygon):
                    profile_errors += 1
                profile_margin = min(profile_margin, min(point_edge_distance(p.xy, a, polygon[(i + 1) % n])
                    for i, a in enumerate(polygon)))
        faces = [tuple(p.vertices) for p in mesh.data.polygons if all(i in owned for i in p.vertices)]
        own_tree = BVHTree.FromPolygons(vertices, faces)
        own_margin = clearance(rig, pb, own_tree)
        check(pb.name + ' is a 3D box enclosing its weighted part',
              len(source) > 0 and margin >= .01 and not profile_errors and own_margin >= .004 and
              all(max(p[a] for p in actual) - min(p[a] for p in actual) > .025 for a in range(3)),
              source_vertices=len(source), fitted_margin_m=margin, silhouette_errors=profile_errors,
              silhouette_margin_m=profile_margin if n else None,
              weighted_part_surface_clearance_bound_m=own_margin,
              scope='Own weighted hand/foot/backpack triangles; adjacent limbs may meet its box plane.')

    for name, adjustment in manifest['original_adjustments'].items():
        pb = rig.pose.bones[name]; original = baseline['controls'][name]
        geometry_unchanged = [list(v.co) for v in pb.custom_shape.data.vertices] == original['vertices'] and \
            [list(e.vertices) for e in pb.custom_shape.data.edges] == original['edges']
        scale_error = max(abs(pb.custom_shape_scale_xyz[i] - original['scale'][i] * adjustment['scale_multiplier']) for i in range(3))
        size_mode_same = pb.use_custom_shape_bone_size == original['size_by_bone']
        delta = Vector(pb.custom_shape_translation) - Vector(original['translation'])
        world_delta = (rig.matrix_world @ pb.bone.matrix_local).to_3x3() @ delta
        angle = math.degrees(Euler(original['rotation']).to_quaternion().rotation_difference(
            Euler(pb.custom_shape_rotation_euler).to_quaternion()).angle)
        if 'hand_ctrl_' in name:
            valid = scale_error < 1e-6 and 0 < angle <= 6.001 and abs(world_delta.length - .012) < 1e-6
        elif 'foot_ctrl_' in name:
            valid = scale_error < 1e-6 and angle < .001 and abs(world_delta.length - .025) < 1e-6
        else:
            valid = scale_error < 1e-6 and angle < .001 and world_delta.length < 1e-6
        check(name + ' keeps the original silhouette and only the requested adjustment',
              geometry_unchanged and size_mode_same and valid,
              original_vertices=len(original['vertices']), scale_multiplier=adjustment['scale_multiplier'],
              scale_error=scale_error, translation_m=world_delta.length, rotation_delta_degrees=angle)
        if 'foot_ctrl_' in name:
            axis = Vector(adjustment['toe_projection_axis'])
            source_name = 'j_lefttoebase' if 'left' in name else 'j_righttoebase'
            toes = [vertices[i].dot(axis) for i in indices[source_name]]
            original_scale = Vector(original['scale']) * (pb.bone.length if original['size_by_bone'] else 1)
            first_frame = rig.matrix_world @ pb.bone.matrix_local @ Matrix.Translation(original['translation']) @ \
                Euler(original['rotation']).to_matrix().to_4x4() @ Matrix.Diagonal((*original_scale, 1))
            before = [first_frame @ Vector(v) for v in original['vertices']]
            def uncovered(polygon):
                low, high = min(p.dot(axis) for p in polygon), max(p.dot(axis) for p in polygon)
                return sum(max(0, low - value, value - high) for value in toes) / len(toes)
            old_loss, new_loss = uncovered(before), uncovered(shape_points(rig, pb))
            check(name + ' actually improves toe enclosure without rescaling', new_loss < old_loss - 1e-6,
                  old_mean_longitudinal_uncovered_m=old_loss, new_mean_longitudinal_uncovered_m=new_loss,
                  scope='Weighted toe vertices projected along the paw length; visual fit remains an artist verdict.')
    body_controls = [p.name for p in rig.pose.bones if p.get('warlock_widget_kind') == 'original_body_slight_resize']
    check('torso and hip control count and silhouettes remain original', len(body_controls) == 6 and
          all(n in baseline['controls'] for n in body_controls), controls=body_controls)

    for item in manifest['hand_settings']:
        pb = rig.pose.bones[item['control']]; points = shape_points(rig, pb)
        areas = [(points[i + 1] - points[i]).cross(points[i + 2] - points[i]).length / 2 for i in range(0, len(points), 3)]
        wrist = Vector(item['wrist'])
        margin = clearance(rig, pb, all_tree)
        check(pb.name + ' has five small triangular handles near the wrist', len(points) == 15 and
              len(pb.custom_shape.data.edges) == 15 and all(a > 1e-5 for a in areas) and
              max((p - wrist).length for p in points) < .12 and
              margin > .0015 and
              all('curl_' + d in pb for d in ('thumb', 'index', 'middle', 'ring', 'pinky')),
              triangle_areas_m2=areas, maximum_wrist_distance_m=max((p - wrist).length for p in points),
              full_body_clearance_bound_m=margin)

    pack = manifest['backpack']; pack_fit = json.loads(rig.pose.bones['ORG-j_backpack']['warlock_widget_box_fit'])
    selected = set(pack_fit['vertex_indices'])
    pack_group = mesh.vertex_groups['j_backpack'].index
    rigid_weights = all(any(g.group == pack_group and g.weight >= .999 for g in mesh.data.vertices[i].groups) for i in selected)
    excluded_known_straps = {13350, 13452, 13531}.issubset(pack['excluded_strap_components'])
    check('backpack fit excludes articulated strap islands', rigid_weights and excluded_known_straps and
          not any(i in selected for i in (13350, 13452, 13531)) and pack['margin_m'] <= .012,
          included_vertices=len(selected), excluded_strap_components=pack['excluded_strap_components'])

    for item in manifest['belt_arcs']:
        pb = rig.pose.bones[item['control']]
        points = shape_points(rig, pb); center = Vector(item['center']); rx, ry = item['radii']
        midline = [(points[i] + points[-1 - i]) / 2 for i in range(len(points) // 2)]
        radial_error = max(abs(((p.x - center.x) / rx) ** 2 + ((p.y - center.y) / ry) ** 2 - 1) for p in midline)
        margin = clearance(rig, pb, all_tree)
        z_span = max(p.z for p in points) - min(p.z for p in points)
        check(pb.name + ' sits outside and perpendicular to the waist surface',
              radial_error < 1e-5 and margin > .0025 and z_span < 1e-6,
              ellipse_error=radial_error, plane_z_span_m=z_span, full_body_clearance_bound_m=margin)

    for name in manifest['twist_spheres']:
        pb = rig.pose.bones[name]; points = shape_points(rig, pb)
        center = rig.matrix_world @ pb.bone.head_local
        radii = [(p - center).length for p in points]
        plane_counts = [sum(abs((p - center)[axis]) < 1e-5 for p in points) for axis in range(3)]
        check(name + ' has one three-great-circle sphere', len(points) == 96 and
              max(radii) - min(radii) < 1e-5 and all(n >= 32 for n in plane_counts), plane_vertex_counts=plane_counts)
    for name in manifest['hidden_duplicate_widgets']:
        pb = rig.pose.bones[name]
        check(name + ' duplicate is unselectable and its mechanism retained',
              pb.custom_shape is None and pb.bone.hide and pb.bone.hide_select)
    inert = [p for p in rig.pose.bones if p.name.startswith('j_') and '_ctrl_tweak' in p.name and
             any(word in p.name for word in ('arm', 'leg'))]
    check('all sixteen DEF-only Rigify tweaks are hidden while their channels remain',
          len(inert) == 16 and all(p.custom_shape is None and p.bone.hide and p.bone.hide_select for p in inert),
          retained_channels=[p.name for p in inert])
    check('twist sphere list contains actual native controls only',
          bool(manifest['twist_spheres']) and all(n.startswith(('CTRL-forearm-twist-', 'CTRL-native-twist-'))
              for n in manifest['twist_spheres']), controls=manifest['twist_spheres'])
    for item in manifest['shoulders']:
        pb = rig.pose.bones[item['control']]
        margin = clearance(rig, pb, all_tree)
        points = shape_points(rig, pb)
        check(pb.name + ' is a small folded circle above its shoulder plate', pb.custom_shape and
              pb.get('warlock_widget_kind') == 'shoulder_folded_circle' and len(points) == 48 and
              not all(pb.lock_rotation) and margin >= .0024 and max(item['radii']) <= .09 and
              max(p.z for p in points) - min(p.z for p in points) > .02,
              plate_first_vertex=item['plate_first_vertex'], radii_m=item['radii'], full_body_clearance_bound_m=margin)
    lips = [n for n in indices if n.startswith('j_lip_')]
    check('all weighted existing lips, eyelids, brows, ears and nose have usable rounded controls',
          all('ORG-' + n in rig.pose.bones and rig.pose.bones['ORG-' + n].custom_shape and
              not all(rig.pose.bones['ORG-' + n].lock_rotation) for n in manifest['face_channels']) and
          set(lips).issubset(manifest['face_channels']), supported_channels=manifest['face_channels'])
    head = shape_points(rig, rig.pose.bones['ORG-j_head'])
    top = max(vertices[i].z for i in indices['j_head'])
    reference = baseline['controls']['j_tail1_ctrl_master']; head_spec = manifest['head_reference']
    expected_head = [Vector(head_spec['center']) + Vector((v[0], v[2], v[1] - head_spec['minimum_source_y'])) * head_spec['scale']
                     for v in reference['vertices']]
    head_error = max((a - b).length for a, b in zip(head, expected_head))
    check('curved four-arrow head cross uses the original tail-master shape', len(head) == 52 and
          min(p.z for p in head) >= top + .024 and head_error < 1e-5 and
          [list(e.vertices) for e in rig.pose.bones['ORG-j_head'].custom_shape.data.edges] == reference['edges'],
          minimum_height_m=min(p.z for p in head) - top, reference_geometry_error_m=head_error)
    check('no unsupported tongue or new GAME bones invented', len(game.data.bones) == 138 and
          not any('tongue' in b.name for b in game.data.bones) and
          any(x['request'] == 'tongue' for x in manifest['unsupported_face_requests']))
    after_sha256 = hashlib.sha256(args.rig.read_bytes()).hexdigest()
    result = {'schema': 1, 'status': 'PASS' if all(t['passed'] for t in tests) and source_sha256 == after_sha256 else 'FAIL',
              'blender': bpy.app.version_string, 'source': str(args.rig.resolve()), 'tests': tests,
              'source_blend_sha256': source_sha256, 'source_blend_sha256_after': after_sha256,
              'source_bytes_unmodified': source_sha256 == after_sha256,
              'scope': 'Neutral Blender control shape geometry only; not a rendered/game/custom-export verdict.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('WARLOCK_WIDGET_TESTS', result['status'], sum(t['passed'] for t in tests), '/', len(tests))
    if result['status'] != 'PASS':
        raise RuntimeError('Widget geometry checks failed; see ' + str(args.output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rig', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--decorate', action='store_true', help='Decorate an old reference in memory; never save it')
    parser.add_argument('--first', type=Path, help='Original October rig; captured before loading the target')
    main(parser.parse_args(sys.argv[sys.argv.index('--') + 1:]))
