"""Animator-only launcher/rocket spaces; never alter the GAME skeleton or actions.

The original left-hand attachment is evaluated independently of new overrides.
Controls append native local TRS on existing GAME channels. Rigid references
and the optional right IK grip follow the normalized actual GAME result, using
the runtime quaternion convention. All dependencies run left-hand -> weapon
-> right-hand, not a mutually following grip.
"""
from __future__ import annotations

import json
import math

import bpy
from mathutils import Matrix, Vector


CHANNELS = {
    "weapon_follow": ("CTRL-hand-settings-left", "weapon_follow", "CTRL-weapon"),
    "rocket_follow": ("CTRL-hand-settings-left", "rocket_follow", "CTRL-rocket"),
    "right_hand_follow": ("CTRL-hand-settings-right", "right_hand_follow_weapon",
                          "j_righthand_ctrl_ik"),
}
CONSTRAINT = "Warlock matched follow"
SOURCE_BONE = "MCH-warlock-left-attachment-frame"
ACTUAL_WEAPON = "MCH-warlock-weapon-actual-frame"
ACTUAL_ROCKET = "MCH-warlock-rocket-actual-frame"
DELTA_WEAPON = "MCH-warlock-weapon-local-delta"
DELTA_ROCKET = "MCH-warlock-rocket-local-delta"
MANIFEST_KEY = "warlock_weapon_follow_manifest"
EXPORT_BINDINGS = {"CTRL-weapon": "j_leftweaponattach", "CTRL-rocket": "j_leftweaponcomponent2"}


def _driver(owner, field, expression, variables, index=None):
    curve = owner.driver_add(field) if index is None else owner.driver_add(field, index)
    driver = curve.driver
    driver.type = "SCRIPTED"
    driver.expression = expression
    for name, target, path in variables:
        variable = driver.variables.new()
        variable.name = name
        variable.type = "SINGLE_PROP"
        variable.targets[0].id = target
        variable.targets[0].data_path = path
    return driver


def _normalized_rotation(game, bone_name="j_leftweaponattach", prefix="WARLOCK_ATTACHMENT_SOURCE"):
    """Build ordinary scalar-expression drivers, usable with autoexec disabled."""
    helpers = []
    for suffix in ("WORLD", "AXES", "QUATERNION"):
        obj = bpy.data.objects.new(prefix + "_" + suffix, None)
        bpy.context.scene.collection.objects.link(obj)
        obj["authoring_reference_only"] = True
        obj.hide_render = True
        obj.hide_set(True)
        helpers.append(obj)
    world, axes, quaternion = helpers
    bone = 'pose.bones["%s"].matrix' % bone_name
    for row in range(3):
        for column in range(3):
            key = "m%d%d" % (row, column)
            world[key] = 0.0
            variables = []
            for k in range(4):
                variables.extend(((chr(97 + 2*k), game,
                                   "matrix_world[%d][%d]" % (k, row)),
                                  (chr(98 + 2*k), game,
                                   bone + "[%d][%d]" % (column, k))))
            _driver(world, '["' + key + '"]', "a*b+c*d+e*f+g*h", variables)
            axes[key] = 0.0
            _driver(axes, '["' + key + '"]', "a/sqrt(a*a+b*b+c*c)",
                    [(name, world, '["m%d%d"]' % (r, column))
                     for name, r in zip("abc", (row, (row+1) % 3, (row+2) % 3))])
    variables = [(name, axes, '["m%d%d"]' % cell)
                 for name, cell in zip("abcdefghi",
                     ((0,0),(1,1),(2,2),(2,1),(1,2),(0,2),(2,0),(1,0),(0,1)))]
    expressions = (
        "sqrt(1+a+b+c)/2 if a+b+c>0 else (d-e)/(2*sqrt(1+a-b-c)) if a>b and a>c else (f-g)/(2*sqrt(1+b-a-c)) if b>c else (h-i)/(2*sqrt(1+c-a-b))",
        "(d-e)/(2*sqrt(1+a+b+c)) if a+b+c>0 else sqrt(1+a-b-c)/2 if a>b and a>c else (i+h)/(2*sqrt(1+b-a-c)) if b>c else (f+g)/(2*sqrt(1+c-a-b))",
        "(f-g)/(2*sqrt(1+a+b+c)) if a+b+c>0 else (i+h)/(2*sqrt(1+a-b-c)) if a>b and a>c else sqrt(1+b-a-c)/2 if b>c else (d+e)/(2*sqrt(1+c-a-b))",
        "(h-i)/(2*sqrt(1+a+b+c)) if a+b+c>0 else (f+g)/(2*sqrt(1+a-b-c)) if a>b and a>c else (d+e)/(2*sqrt(1+b-a-c)) if b>c else sqrt(1+c-a-b)/2",
    )
    for component, expression in zip("wxyz", expressions):
        quaternion[component] = 0.0
        _driver(quaternion, '["' + component + '"]', expression, variables)
    quaternion.rotation_mode = "QUATERNION"
    for index, component in enumerate("wxyz"):
        _driver(quaternion, "rotation_quaternion", component + "/sqrt(w*w+x*x+y*y+z*z)",
                [(name, quaternion, '["' + name + '"]') for name in "wxyz"], index)
    return quaternion, helpers


def _property(bone, name, value, description):
    bone[name] = float(value)
    bone.id_properties_ui(name).update(min=0., max=1., soft_min=0., soft_max=1.,
        default=float(value), description=description)


def _native_attachment_reference(game):
    """Reproduce the pre-control native attachment without a feedback loop.

    Retain the existing ORG/local-reference animation and real inherited native
    hand scale. A two-bone authoring reference supplies the original attachment
    after GAME's attachment is driven by the animator's new control.
    """
    data = bpy.data.armatures.new("WARLOCK_WEAPON_NATIVE_REFERENCE_DATA")
    obj = bpy.data.objects.new("WARLOCK_WEAPON_NATIVE_REFERENCE", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = game.matrix_world.copy()
    obj["authoring_reference_only"] = True
    obj.hide_render = True
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    mapping = {"j_lefthand": "j_lefthand", "j_leftweaponattach": "j_leftweaponattach"}
    for name, native_name in mapping.items():
        original = game.data.bones[native_name]
        bone = data.edit_bones.new(name)
        bone.length = original.length
        bone.matrix = original.matrix_local
        bone.inherit_scale = original.inherit_scale
        bone.use_deform = False
    data.edit_bones["j_leftweaponattach"].parent = data.edit_bones["j_lefthand"]
    bpy.ops.object.mode_set(mode="OBJECT")
    constraint = obj.pose.bones["j_lefthand"].constraints.new("COPY_TRANSFORMS")
    constraint.target = game
    constraint.subtarget = "j_lefthand"
    constraint.owner_space = constraint.target_space = "WORLD"
    source = game.pose.bones["j_leftweaponattach"].constraints
    if len(source) != 1 or source[0].type != "COPY_TRANSFORMS" or source[0].owner_space != "LOCAL":
        raise ValueError("Unrecognized pre-control GAME attachment; refusing to discard existing animation")
    constraint = obj.pose.bones["j_leftweaponattach"].constraints.new("COPY_TRANSFORMS")
    constraint.target = source[0].target
    constraint.subtarget = source[0].subtarget
    constraint.owner_space = constraint.target_space = "LOCAL"
    obj.hide_set(True)
    bpy.context.view_layer.update()
    return obj


def _new_bone(rig, name, world, collection):
    bone = rig.data.edit_bones.new(name)
    bone.length = .12
    bone.matrix = rig.matrix_world.inverted() @ world
    bone.use_deform = False
    collection.assign(bone)
    return bone


def _box_widget(name, mesh, reference, widgets):
    """A real three-dimensional box around the approved reference geometry."""
    transform = reference.matrix_world.inverted() @ mesh.matrix_world
    points = [transform @ Vector(corner) for corner in mesh.bound_box]
    lower = Vector(tuple(min(point[axis] for point in points) - .025 for axis in range(3)))
    upper = Vector(tuple(max(point[axis] for point in points) + .025 for axis in range(3)))
    vertices = [(x, y, z) for x in (lower.x, upper.x)
                for y in (lower.y, upper.y) for z in (lower.z, upper.z)]
    edges = [(a, b) for a in range(8) for b in range(a+1, 8)
             if (a ^ b) in (1, 2, 4)]
    data = bpy.data.meshes.new("WGT-" + name)
    data.from_pydata(vertices, edges, [])
    shape = bpy.data.objects.new(data.name, data)
    widgets.objects.link(shape)
    shape.hide_render = True
    return shape


def _follow_constraint(rig, owner, target, inverse, setting, prop):
    constraint = owner.constraints.new("CHILD_OF")
    constraint.name = CONSTRAINT
    constraint.target = rig
    constraint.subtarget = target
    constraint.owner_space = "WORLD"
    constraint.target_space = "WORLD"
    constraint.inverse_matrix = inverse
    constraint.use_scale_x = constraint.use_scale_y = constraint.use_scale_z = False
    _driver(constraint, "influence", "follow",
            [("follow", rig, 'pose.bones["%s"]["%s"]' % (setting, prop))])
    return constraint


def build_weapon_controls(rig, game, weapon_rig, weapon_objects, groups, widgets):
    """Add authoring controls to a freshly built or older unmodified handoff.

    Call after importing the reference FBX, instead of its old Child Of and
    weapon_reference_rotation setup. Repeated calls are a no-op; artist actions
    and native bones are never cleared or regenerated here.
    """
    if rig.get(MANIFEST_KEY):
        return json.loads(rig[MANIFEST_KEY])
    for name in (SOURCE_BONE, ACTUAL_WEAPON, ACTUAL_ROCKET, DELTA_WEAPON, DELTA_ROCKET,
                 "CTRL-weapon", "CTRL-rocket"):
        if name in rig.data.bones:
            raise ValueError("Refusing an unrecognized existing control: " + name)
    launcher = next(obj for obj in weapon_objects
                    if obj.type == "MESH" and obj.name.split(".")[0] == "pRocketLauncher")
    rocket = next(obj for obj in weapon_objects
                  if obj.type == "MESH" and obj.name.split(".")[0] == "pRocket")
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    native = game.evaluated_get(dg)
    frame = native.matrix_world @ native.pose.bones["j_leftweaponattach"].matrix
    # Preserve each mesh's original import-relative coordinates. The preview
    # reference object is identity immediately after import in build_rig.py;
    # it already follows the hand when upgrading an older delivered blend.
    reference_frame = weapon_rig.evaluated_get(dg).matrix_world.copy()
    rocket_local = reference_frame.inverted() @ rocket.evaluated_get(dg).matrix_world
    launcher_widget = _box_widget("CTRL-weapon", launcher, weapon_rig, widgets)
    rocket_widget = _box_widget("CTRL-rocket", rocket, weapon_rig, widgets)
    native_reference = _native_attachment_reference(game)
    quaternion, helpers = _normalized_rotation(native_reference)
    bpy.context.view_layer.update()
    rotation = quaternion.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.to_quaternion()
    neutral = Matrix.LocRotScale(frame.translation, rotation, Vector((1, 1, 1)))

    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = rig
    rig.hide_set(False)
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    controls = rig.data.collections.get("Warlock additions") or rig.data.collections.new("Warlock additions")
    mechanisms = (rig.data.collections.get("Warlock extra mechanisms") or
                  rig.data.collections.new("Warlock extra mechanisms"))
    _new_bone(rig, SOURCE_BONE, neutral, mechanisms)
    _new_bone(rig, ACTUAL_WEAPON, neutral, mechanisms)
    _new_bone(rig, ACTUAL_ROCKET, neutral, mechanisms)
    for name, parent in ((DELTA_WEAPON, SOURCE_BONE), (DELTA_ROCKET, ACTUAL_WEAPON)):
        bone = _new_bone(rig, name, neutral, mechanisms)
        bone.parent = rig.data.edit_bones[parent]
    for name in ("CTRL-weapon", "CTRL-rocket"):
        _new_bone(rig, name, neutral, controls)
    bpy.ops.object.mode_set(mode="OBJECT")
    mechanisms.is_visible = False

    source = rig.pose.bones[SOURCE_BONE]
    constraint = source.constraints.new("COPY_LOCATION")
    constraint.target = native_reference
    constraint.subtarget = "j_leftweaponattach"
    constraint.owner_space = constraint.target_space = "WORLD"
    constraint = source.constraints.new("COPY_ROTATION")
    constraint.target = quaternion
    constraint.owner_space = constraint.target_space = "WORLD"
    left = rig.pose.bones["CTRL-hand-settings-left"]
    right = rig.pose.bones["CTRL-hand-settings-right"]
    _property(left, "weapon_follow", 1, "Launcher follows the left hand; use matched switches to avoid a pose jump")
    _property(left, "rocket_follow", 1, "Rocket follows the left hand independently of the launcher")
    _property(right, "right_hand_follow_weapon", 0,
              "Right IK hand follows the launcher; matched switch enters IK without replacing existing keys")
    for name, shape in (("CTRL-weapon", launcher_widget), ("CTRL-rocket", rocket_widget)):
        control = rig.pose.bones[name]
        control.rotation_mode = "QUATERNION"
        control.lock_scale = (True, True, True)
        control.custom_shape = shape
        control.use_custom_shape_bone_size = False
        control["warlock_widget_kind"] = "weapon_box"
        if name not in groups.setdefault("Accessories", []):
            groups["Accessories"].append(name)
    _follow_constraint(rig, rig.pose.bones["CTRL-weapon"], SOURCE_BONE, neutral.inverted(),
                       left.name, "weapon_follow")
    _follow_constraint(rig, rig.pose.bones["CTRL-rocket"], SOURCE_BONE, neutral.inverted(),
                       left.name, "rocket_follow")
    _follow_constraint(rig, rig.pose.bones["j_righthand_ctrl_ik"], ACTUAL_WEAPON, neutral.inverted(),
                       right.name, "right_hand_follow_weapon")

    # Resolve rigid edits relative to the original normalized attachment (or
    # the actual current weapon for the rocket). Append a native local TRS
    # delta; at identity the original animation remains exactly unchanged.
    # A rigid WORLD override would
    # require unexportable compensating shear under anatomical nonuniform scale.
    # The actual native result is shown below, not falsely presented as an exact
    # arbitrary rigid-world solution under an anisotropic parent metric.
    for control, native_bone, target in (("CTRL-weapon", "j_leftweaponattach", DELTA_WEAPON),
                                         ("CTRL-rocket", "j_leftweaponcomponent2", DELTA_ROCKET)):
        constraint = rig.pose.bones[target].constraints.new("COPY_TRANSFORMS")
        constraint.target = rig
        constraint.subtarget = control
        constraint.owner_space = constraint.target_space = "WORLD"
        constraint = game.pose.bones[native_bone].constraints.new("COPY_TRANSFORMS")
        constraint.name = "Warlock authored " + control + " local TRS"
        constraint.target = rig
        constraint.subtarget = target
        constraint.owner_space = constraint.target_space = "LOCAL"
        constraint.mix_mode = "AFTER_SPLIT"
        constraint = game.pose.bones[native_bone].constraints.new("COPY_LOCATION")
        constraint.name = "Warlock authored " + control + " world location"
        constraint.target = rig
        constraint.subtarget = control
        constraint.owner_space = constraint.target_space = "WORLD"

    preview_frames = {}
    for native_bone, actual, prefix in (("j_leftweaponattach", ACTUAL_WEAPON, "WARLOCK_WEAPON_ACTUAL"),
                                       ("j_leftweaponcomponent2", ACTUAL_ROCKET, "WARLOCK_ROCKET_ACTUAL")):
        actual_quaternion, actual_helpers = _normalized_rotation(game, native_bone, prefix)
        helpers.extend(actual_helpers)
        pose = rig.pose.bones[actual]
        constraint = pose.constraints.new("COPY_LOCATION")
        constraint.target = game
        constraint.subtarget = native_bone
        constraint.owner_space = constraint.target_space = "WORLD"
        constraint = pose.constraints.new("COPY_ROTATION")
        constraint.target = actual_quaternion
        constraint.owner_space = constraint.target_space = "WORLD"
        preview_frames[native_bone] = actual
    rig.pose.bones["CTRL-weapon"].custom_shape_transform = rig.pose.bones[ACTUAL_WEAPON]
    rig.pose.bones["CTRL-rocket"].custom_shape_transform = rig.pose.bones[ACTUAL_ROCKET]

    for constraint in list(weapon_rig.constraints):
        weapon_rig.constraints.remove(constraint)
    if weapon_rig.animation_data:
        for curve in list(weapon_rig.animation_data.drivers):
            weapon_rig.driver_remove(curve.data_path, curve.array_index)
    for obj in list(bpy.data.objects):
        if obj.name.startswith("WARLOCK_WEAPON_REFERENCE_") and obj.get("authoring_reference_only"):
            bpy.data.objects.remove(obj, do_unlink=True)
    weapon_rig.matrix_world = Matrix.Identity(4)
    constraint = weapon_rig.constraints.new("COPY_TRANSFORMS")
    constraint.target = rig
    constraint.subtarget = ACTUAL_WEAPON
    constraint.owner_space = constraint.target_space = "WORLD"
    rocket.parent = None
    rocket.matrix_parent_inverse = Matrix.Identity(4)
    rocket.matrix_world = rocket_local
    constraint = rocket.constraints.new("CHILD_OF")
    constraint.target = rig
    constraint.subtarget = ACTUAL_ROCKET
    constraint.owner_space = constraint.target_space = "WORLD"
    constraint.inverse_matrix = Matrix.Identity(4)
    for obj in weapon_objects:
        obj["authoring_reference_only"] = True
    manifest = {"schema": 1, "controls": ["CTRL-weapon", "CTRL-rocket"],
        "source": native_reference.name + ":j_leftweaponattach", "source_bone": SOURCE_BONE,
        "rotation_policy": "normalized-axis-quaternion-v1", "right_hand_mode": "IK",
        "right_hand_target": "j_righthand_ctrl_ik", "reference_objects_only": True,
        "controls_bake_to_native_tracks": True,
        "channels": {key: list(value) for key, value in CHANNELS.items()},
        "helper_objects": [obj.name for obj in helpers],
        "export_bindings": EXPORT_BINDINGS,
        "rocket_capability": "independent-loaded-rocket-v1",
        "transform_policy": "native-local-trs-v1", "preview_policy": "normalized-actual-game-v1",
        "export_transform_policy": "native-local-trs-v1",
        "preview_objects": {"CTRL-weapon": weapon_rig.name, "CTRL-rocket": rocket.name},
        "preview_local_frames": {"CTRL-weapon": [list(row) for row in Matrix.Identity(4)],
                                 "CTRL-rocket": [list(row) for row in rocket_local]},
        "preview_frames": preview_frames,
        "native_reference": native_reference.name,
        "rocket_reference_object": rocket.name,
        "rocket_reference_local_matrix": [list(row) for row in rocket_local],
        "alignment": "Existing left attachment frame; no semantic finger-contact claim"}
    rig[MANIFEST_KEY] = json.dumps(manifest)
    rig.update_tag()
    bpy.context.view_layer.update()
    return manifest


def _world(rig, name):
    evaluated = rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return evaluated.matrix_world @ evaluated.pose.bones[name].matrix


def _matrix_error(a, b):
    return max(abs(a[row][column] - b[row][column]) for row in range(4) for column in range(4))


def switch_follow(rig, channel, enabled, *, keyframe=False):
    """Match then switch one follow space without rewriting existing actions.

    With keyframe=False this changes only the current editable pose and setting.
    With keyframe=True it inserts keys for the changed control and switch at the
    current frame, leaving all other keys, tracks and custom poses alone.
    The UI performs its already-tested FK->IK snap before enabling right follow.
    """
    if channel not in CHANNELS:
        raise ValueError("Unknown attachment-follow channel: " + str(channel))
    setting_name, prop, control_name = CHANNELS[channel]
    if channel == "right_hand_follow" and enabled and rig.pose.bones["j_rightarm_ctrl_parent"].get("IK_FK", 0.) > 1e-6:
        raise ValueError("Match the right arm to IK before enabling right-hand weapon follow")
    setting = rig.pose.bones[setting_name]
    control = rig.pose.bones[control_name]
    constraint = control.constraints.get(CONSTRAINT)
    if not constraint:
        raise ValueError("This rig does not contain the revised weapon-follow controls")
    bpy.context.view_layer.update()
    desired = _world(rig, control_name)
    old_value, old_basis = setting[prop], control.matrix_basis.copy()
    try:
        setting[prop] = float(bool(enabled))
        rig.update_tag()
        bpy.context.view_layer.update()
        before_constraint = desired
        if enabled:
            delta = _world(rig, constraint.subtarget) @ constraint.inverse_matrix
            before_constraint = delta.inverted() @ desired
        control.matrix = rig.matrix_world.inverted() @ before_constraint
        rig.update_tag()
        bpy.context.view_layer.update()
        error = _matrix_error(desired, _world(rig, control_name))
        if not math.isfinite(error) or error > 3e-5:
            raise RuntimeError("Follow switch could not preserve the current pose (matrix error %.8g)" % error)
    except Exception:
        setting[prop] = old_value
        control.matrix_basis = old_basis
        rig.update_tag()
        bpy.context.view_layer.update()
        raise
    if keyframe:
        setting.keyframe_insert('["' + prop + '"]', group=setting_name)
        control.keyframe_insert("location", group=control_name)
        rotation = "rotation_quaternion" if control.rotation_mode == "QUATERNION" else "rotation_euler"
        control.keyframe_insert(rotation, group=control_name)
    return error
