"""Numerical control-display checks, independent of runtime acceptance.

Run Blender 5.2 --background --factory-startup --disable-autoexec --python
test_widgets_blender.py -- --rig candidate.blend --output widgets.json.
No source scene is saved, no image is rendered, and no pose is changed.
"""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from control_widgets import COLORS, apply_widgets


def shape_points(rig, bone):
    frame = rig.matrix_world @ bone.bone.matrix_local
    return [frame @ v.co for v in bone.custom_shape.data.vertices]


def clearance(rig, bone, tree):
    points = shape_points(rig, bone)
    lower_bound = float('inf')
    for edge in bone.custom_shape.data.edges:
        a, b = (points[i] for i in edge.vertices)
        distances = [tree.find_nearest(a.lerp(b, t / 16))[3] for t in range(17)]
        lower_bound = min(lower_bound, min(distances) - (b - a).length / 32)
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
    bpy.ops.wm.open_mainfile(filepath=str(args.rig.resolve()), use_scripts=False)
    rig, game = (bpy.data.objects[n] for n in ('WARLOCK_CTRL', 'WARLOCK_GAME'))
    mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and len(o.data.vertices) == 29123)
    if args.decorate:
        groups = json.loads(rig['warlock_control_manifest'])['groups']
        collection = bpy.data.collections.new('Widget isolated verification')
        bpy.context.scene.collection.children.link(collection)
        apply_widgets(rig, game, mesh, groups, collection)
    manifest = json.loads(rig['warlock_widget_manifest'])
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
        owned = set().union(*(indices.get(n, set()) for n in fit['sources']))
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

    for item in manifest['body_rings']:
        pb = rig.pose.bones[item['control']]
        center = Vector(item['center']); rx, ry = item['radii']
        owned = [vertices[i] for i in indices[item['source']]]
        section = [p for p in owned if abs(p.z - center.z) < item['section_half_height']] or owned
        normalized_max = max(math.sqrt(((p.x - center.x) / rx) ** 2 + ((p.y - center.y) / ry) ** 2) for p in section)
        radius_error = max(abs(math.sqrt(((p.x - center.x) / rx) ** 2 + ((p.y - center.y) / ry) ** 2) - 1)
                           for p in shape_points(rig, pb))
        check(pb.name + ' encloses its torso or hip cross-section',
              normalized_max < .95 and radius_error < 1e-5,
              source_max_normalized_radius=normalized_max, curve_radius_error=radius_error,
              scope=item['clearance_scope'])

    for item in manifest['belt_arcs']:
        pb = rig.pose.bones[item['control']]
        points = shape_points(rig, pb); center = Vector(item['center']); rx, ry = item['radii']
        radial_error = max(abs(((p.x - center.x) / rx) ** 2 + ((p.y - center.y) / ry) ** 2 - 1) for p in points)
        margin = clearance(rig, pb, all_tree)
        check(pb.name + ' wraps the belt outside the skin', radial_error < 1e-5 and margin > .005,
              ellipse_error=radial_error, full_body_clearance_bound_m=margin)

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
    for side in ('left', 'right'):
        pb = rig.pose.bones['ORG-j_' + side + 'shoulder']
        margin = clearance(rig, pb, all_tree)
        check(side + ' shoulder crescent is usable and clear', pb.custom_shape and
              pb.get('warlock_widget_kind') == 'shoulder_crescent' and
              not all(pb.lock_rotation) and margin >= .004, full_body_clearance_bound_m=margin)
    lips = [n for n in indices if n.startswith('j_lip_')]
    check('all weighted existing lips, eyelids, brows, ears and nose have usable rounded controls',
          all('ORG-' + n in rig.pose.bones and rig.pose.bones['ORG-' + n].custom_shape and
              not all(rig.pose.bones['ORG-' + n].lock_rotation) for n in manifest['face_channels']) and
          set(lips).issubset(manifest['face_channels']), supported_channels=manifest['face_channels'])
    head = shape_points(rig, rig.pose.bones['ORG-j_head'])
    top = max(vertices[i].z for i in indices['j_head'])
    check('four-arrow head cross sits above the head', len(head) == 64 and min(p.z for p in head) >= top + .039,
          minimum_height_m=min(p.z for p in head) - top)
    check('no unsupported tongue or new GAME bones invented', len(game.data.bones) == 138 and
          not any('tongue' in b.name for b in game.data.bones) and
          any(x['request'] == 'tongue' for x in manifest['unsupported_face_requests']))
    result = {'schema': 1, 'status': 'PASS' if all(t['passed'] for t in tests) else 'FAIL',
              'blender': bpy.app.version_string, 'source': str(args.rig.resolve()), 'tests': tests,
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
    main(parser.parse_args(sys.argv[sys.argv.index('--') + 1:]))
