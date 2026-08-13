"""Export Crunch's launcher and rocket without changing VT2 node contracts.

Run with Blender 5.2 while opening Crunch's source scene::

    blender.exe --background xud4soo5fg7g8qd4.blend \
      --python tools/prepare_warlock_weapon_fbx.py -- \
      --launcher-output .build/weapon_candidate/pRocketLauncher.fbx \
      --projectile-output .build/weapon_candidate/SM_Rocket.fbx

The launcher is a rigid MVP.  It is transformed from the source character's
world/rest pose into ``j_leftweaponattach`` rest space.  The legacy four-node
weapon armature remains authoritative, so Lua attachment links and the muzzle
lookup keep resolving.  The separate projectile is mapped into the legacy
``pRocket`` mesh frame and keeps that node's transform/forward convention.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree


SOURCE_SHA256 = "AB6EBC9EF45CEA6E402BBD0415C2D40716824552C2AB514947902D1EAC06C1B2"
SOURCE_LAUNCHER = "SM_Skaven_WarlockBombardier_RcoketLauncher"  # authored typo
SOURCE_ROCKET = "SM_Skaven_WarlockBombardier_Rocket"
SOURCE_ARMATURE = "armature object.008"
ATTACH_BONE = "j_leftweaponattach"
EXPECTED_WEAPON_BONES = {"root_point", "handle", "p_fx", "a_barrel"}
LEGACY_BASELINES = {
    "launcher": {
        "blob": "4afd3ff155889b44760ff41500bca7e1bf6ccafa",
        "sha256": "80CAF376BA9210B83DED30587F9D2A3663F6614D4B624513307D06DEC0E64D5F",
        "filename": "pRocketLauncher.fbx",
    },
    "projectile": {
        "blob": "445636e36fc62a8aef8883d2f59ed85eaa6707a0",
        "sha256": "AFF853DC8C420B7FD94F7273166025E1BAF49C9828274B05CCD5647AB43294C7",
        "filename": "SM_Rocket.fbx",
    },
}


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--legacy-launcher",
        type=Path,
        help="optional immutable Dalo baseline; SHA-256 is enforced",
    )
    parser.add_argument(
        "--legacy-projectile",
        type=Path,
        help="optional immutable Dalo baseline; SHA-256 is enforced",
    )
    parser.add_argument("--launcher-output", type=Path, required=True)
    parser.add_argument("--projectile-output", type=Path, required=True)
    return parser.parse_args(argv)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def source_path() -> Path:
    path = Path(bpy.data.filepath).resolve()
    if not path.is_file() or sha256(path) != SOURCE_SHA256:
        raise RuntimeError(
            "open Crunch's exact xud4soo5fg7g8qd4.blend source; "
            f"expected SHA-256 {SOURCE_SHA256}"
        )
    return path


def immutable_legacy(
    supplied: Path | None, key: str, temporary_root: Path
) -> Path:
    baseline = LEGACY_BASELINES[key]
    if supplied is not None:
        path = supplied.resolve()
    else:
        repo_root = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            ["git", "-C", str(repo_root), "cat-file", "blob", baseline["blob"]],
            check=True,
            capture_output=True,
        )
        path = temporary_root / baseline["filename"]
        path.write_bytes(result.stdout)
    if sha256(path) != baseline["sha256"]:
        raise RuntimeError(
            f"{key} legacy baseline changed; expected SHA-256 {baseline['sha256']}"
        )
    return path


def copy_transformed_mesh(source: bpy.types.Object, transform: Matrix) -> bpy.types.Mesh:
    if source.type != "MESH":
        raise RuntimeError(f"{source.name} is not a mesh")
    mesh = source.data.copy()
    mesh.transform(transform)
    return mesh


def require_material(mesh: bpy.types.Mesh, expected: str) -> None:
    names = [material.name if material else None for material in mesh.materials]
    normalized = [name.rsplit(".", 1)[0] if name and name.rsplit(".", 1)[-1].isdigit() else name for name in names]
    if normalized != [expected]:
        raise RuntimeError(f"expected material [{expected}], got {names}")


def import_fbx(path: Path) -> list[bpy.types.Object]:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(path.resolve()), use_anim=False)
    return [obj for obj in bpy.data.objects if obj not in before]


def reserve_exact_names(names: set[str]) -> None:
    """Remove source-scene IDs that would force Blender's .001 suffixes.

    Crunch's full-character scene contains helper empties named root_point,
    p_fx, and a_barrel.  They are not exported, but Blender's global ID
    namespace still renames identically named legacy imports.  Stingray node
    lookups are string contracts, so clear those dormant IDs before import.
    """
    for obj in list(bpy.data.objects):
        if obj.name in names:
            bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.name in names:
            bpy.data.meshes.remove(mesh)
    for armature in list(bpy.data.armatures):
        if armature.name in names:
            bpy.data.armatures.remove(armature)


def force_exact_id_name(obj: bpy.types.Object, name: str) -> None:
    obj.name = name
    if obj.data is not None:
        obj.data.name = name
    if obj.name != name or (obj.data is not None and obj.data.name != name):
        raise RuntimeError(f"could not reserve exact Blender ID name {name}")


def export_selected(path: Path, objects: list[bpy.types.Object]) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.hide_set(False)
        obj.hide_viewport = False
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=str(path.resolve()),
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        add_leaf_bones=False,
        bake_anim=False,
        use_armature_deform_only=False,
        axis_forward="Y",
        axis_up="Z",
    )


def mesh_bounds(mesh: bpy.types.Mesh) -> tuple[Vector, Vector]:
    return (
        Vector(tuple(min(vertex.co[axis] for vertex in mesh.vertices) for axis in range(3))),
        Vector(tuple(max(vertex.co[axis] for vertex in mesh.vertices) for axis in range(3))),
    )


def build_launcher(
    source_launcher: bpy.types.Object,
    source_rocket: bpy.types.Object,
    source_armature: bpy.types.Object,
    legacy_path: Path,
    output_path: Path,
) -> None:
    reserve_exact_names(EXPECTED_WEAPON_BONES | {"pRocketLauncher", "pRocket"})
    imported = import_fbx(legacy_path)
    weapon_rigs = [
        obj
        for obj in imported
        if obj.type == "ARMATURE"
        and EXPECTED_WEAPON_BONES.issubset({bone.name for bone in obj.data.bones})
    ]
    if len(weapon_rigs) != 1:
        raise RuntimeError(f"expected one legacy weapon armature, got {len(weapon_rigs)}")
    weapon_rig = weapon_rigs[0]
    for obj in imported:
        if obj is not weapon_rig:
            old_data = obj.data if obj.type == "MESH" else None
            bpy.data.objects.remove(obj, do_unlink=True)
            if old_data is not None and old_data.users == 0:
                bpy.data.meshes.remove(old_data)
    force_exact_id_name(weapon_rig, "root_point")

    attach_bone = source_armature.data.bones.get(ATTACH_BONE)
    if attach_bone is None:
        raise RuntimeError(f"source armature has no {ATTACH_BONE}")
    # This is the critical placement equation.  Source props are in the full
    # character's world/rest pose; weapon-unit coordinates begin at the hand.
    hand_inverse = (source_armature.matrix_world @ attach_bone.matrix_local).inverted()

    launcher_mesh = copy_transformed_mesh(
        source_launcher, hand_inverse @ source_launcher.matrix_world
    )
    rocket_mesh = copy_transformed_mesh(source_rocket, hand_inverse @ source_rocket.matrix_world)
    require_material(launcher_mesh, "DoomRocket_Weapon")
    require_material(rocket_mesh, "DoomRocket_Rocket")

    launcher = bpy.data.objects.new("pRocketLauncher", launcher_mesh)
    loaded_rocket = bpy.data.objects.new("pRocket", rocket_mesh)
    force_exact_id_name(launcher, "pRocketLauncher")
    force_exact_id_name(loaded_rocket, "pRocket")
    bpy.context.scene.collection.objects.link(launcher)
    bpy.context.scene.collection.objects.link(loaded_rocket)
    for obj in (launcher, loaded_rocket):
        obj.parent = weapon_rig
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_local = Matrix.Identity(4)

    export_selected(output_path, [weapon_rig, launcher, loaded_rocket])

    # The standalone projectile must be allowed to claim pRocket exactly.
    for obj in (launcher, loaded_rocket, weapon_rig):
        bpy.data.objects.remove(obj, do_unlink=True)


def build_projectile(
    source_rocket: bpy.types.Object,
    source_armature: bpy.types.Object,
    legacy_path: Path,
    output_path: Path,
) -> None:
    reserve_exact_names({"pRocket"})
    imported = import_fbx(legacy_path)
    legacy_meshes = [
        obj
        for obj in imported
        if obj.type == "MESH"
        and (obj.name == "pRocket" or obj.name.startswith("pRocket."))
    ]
    if len(legacy_meshes) != 1:
        raise RuntimeError(f"expected one legacy pRocket mesh, got {len(legacy_meshes)}")
    legacy = legacy_meshes[0]

    attach_bone = source_armature.data.bones[ATTACH_BONE]
    hand_inverse = (source_armature.matrix_world @ attach_bone.matrix_local).inverted()
    source_to_hand = hand_inverse @ source_rocket.matrix_world

    # Derive from the same hand/rest frame as the loaded rocket, then map its
    # authored nose direction into the legacy mesh-local +Y forward axis.  The
    # old pRocket node transform itself remains byte-for-byte equivalent after
    # FBX round-trip; only geometry inside that frame changes.
    source_forward_hand = (hand_inverse.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized()
    hand_to_legacy_rotation = source_forward_hand.rotation_difference(Vector((0.0, 1.0, 0.0))).to_matrix().to_4x4()
    projectile_mesh = copy_transformed_mesh(
        source_rocket, hand_to_legacy_rotation @ source_to_hand
    )
    source_min, source_max = mesh_bounds(projectile_mesh)
    legacy_min, legacy_max = mesh_bounds(legacy.data)
    source_center = (source_min + source_max) * 0.5
    legacy_center = (legacy_min + legacy_max) * 0.5
    projectile_mesh.transform(Matrix.Translation(legacy_center - source_center))
    projectile_mesh.materials.clear()
    projectile_mesh.materials.append(bpy.data.materials["DoomRocket_Rocket"])
    require_material(projectile_mesh, "DoomRocket_Rocket")

    new_min, new_max = mesh_bounds(projectile_mesh)
    dimensions = new_max - new_min
    if dimensions.y < 1.20 or dimensions.y > 1.30 or max(dimensions.x, dimensions.z) > 0.50:
        raise RuntimeError(f"projectile normalization changed its forward axis: {tuple(dimensions)}")

    # Reuse the legacy object: its node transform is the runtime convention.
    # Replacing its mesh avoids creating a competing pRocket Blender ID.
    old_legacy_mesh = legacy.data
    legacy.data = projectile_mesh
    if old_legacy_mesh.users == 0:
        bpy.data.meshes.remove(old_legacy_mesh)
    projectile = legacy
    force_exact_id_name(projectile, "pRocket")
    export_selected(output_path, [projectile])


def expected_named_object(
    imported: list[bpy.types.Object], expected: str, object_type: str
) -> bpy.types.Object:
    matches = [
        obj
        for obj in imported
        if obj.type == object_type
        and obj.name == expected
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected one imported {object_type} {expected}, got {matches}")
    return matches[0]


def verify_reimport(path: Path, expected_meshes: dict[str, tuple[int, str]], expected_bones: set[str]) -> list[bpy.types.Object]:
    reserve_exact_names(set(expected_meshes) | expected_bones)
    imported = import_fbx(path)
    for name, (vertex_count, material) in expected_meshes.items():
        obj = expected_named_object(imported, name, "MESH")
        if len(obj.data.vertices) != vertex_count:
            raise RuntimeError(f"{path.name}:{name}: vertex count changed")
        require_material(obj.data, material)
    bones = {
        bone.name
        for obj in imported
        if obj.type == "ARMATURE"
        for bone in obj.data.bones
    }
    if expected_bones and not expected_bones.issubset(bones):
        raise RuntimeError(f"{path.name}: missing attachment nodes {expected_bones - bones}")
    if len([obj for obj in imported if obj.type == "MESH"]) != len(expected_meshes):
        raise RuntimeError(f"{path.name}: unexpected extra render meshes")
    return imported


def maximum_position_error(
    expected: bpy.types.Object, actual: bpy.types.Object
) -> float:
    expected_positions = [expected.matrix_world @ vertex.co for vertex in expected.data.vertices]
    tree = KDTree(len(expected_positions))
    for index, position in enumerate(expected_positions):
        tree.insert(position, index)
    tree.balance()
    return max(
        tree.find(actual.matrix_world @ vertex.co)[2]
        for vertex in actual.data.vertices
    )


def verify_launcher_alignment(
    imported: list[bpy.types.Object],
    source_armature: bpy.types.Object,
    source_launcher: bpy.types.Object,
    source_rocket: bpy.types.Object,
) -> None:
    rigs = [
        obj
        for obj in imported
        if obj.type == "ARMATURE"
        and EXPECTED_WEAPON_BONES.issubset({bone.name for bone in obj.data.bones})
    ]
    if len(rigs) != 1:
        raise RuntimeError("could not identify reimported weapon armature")
    attach_world = source_armature.matrix_world @ source_armature.data.bones[ATTACH_BONE].matrix_local
    rigs[0].matrix_world = attach_world
    bpy.context.view_layer.update()
    checks = (
        (source_launcher, expected_named_object(imported, "pRocketLauncher", "MESH")),
        (source_rocket, expected_named_object(imported, "pRocket", "MESH")),
    )
    for expected, actual in checks:
        error = maximum_position_error(expected, actual)
        if error > 0.0001:
            raise RuntimeError(
                f"{actual.name}: hand-space round-trip placement error {error:.8f} m"
            )
        print(f"[weapon-export] alignment {actual.name} max_error={error:.8f}m")


def main() -> None:
    args = parse_args()
    opened_source = source_path()
    source_launcher = bpy.data.objects.get(SOURCE_LAUNCHER)
    source_rocket = bpy.data.objects.get(SOURCE_ROCKET)
    source_armature = bpy.data.objects.get(SOURCE_ARMATURE)
    if None in (source_launcher, source_rocket, source_armature):
        raise RuntimeError("Crunch launcher, rocket, or armature is missing from the source scene")
    if len(source_launcher.data.vertices) != 4916 or len(source_rocket.data.vertices) != 622:
        raise RuntimeError("Crunch source mesh vertex baseline changed")

    if args.legacy_launcher and args.legacy_launcher.resolve() == args.launcher_output.resolve():
        raise RuntimeError("legacy launcher input must not be overwritten")
    if args.legacy_projectile and args.legacy_projectile.resolve() == args.projectile_output.resolve():
        raise RuntimeError("legacy projectile input must not be overwritten")
    with tempfile.TemporaryDirectory(prefix="warlock_weapon_legacy_") as temporary:
        temporary_root = Path(temporary)
        legacy_launcher = immutable_legacy(args.legacy_launcher, "launcher", temporary_root)
        legacy_projectile = immutable_legacy(
            args.legacy_projectile, "projectile", temporary_root
        )
        build_launcher(
            source_launcher,
            source_rocket,
            source_armature,
            legacy_launcher,
            args.launcher_output,
        )
        build_projectile(
            source_rocket,
            source_armature,
            legacy_projectile,
            args.projectile_output,
        )
    launcher_import = verify_reimport(
        args.launcher_output,
        {
            "pRocketLauncher": (4916, "DoomRocket_Weapon"),
            "pRocket": (622, "DoomRocket_Rocket"),
        },
        EXPECTED_WEAPON_BONES,
    )
    verify_launcher_alignment(
        launcher_import, source_armature, source_launcher, source_rocket
    )
    verify_reimport(
        args.projectile_output,
        {"pRocket": (622, "DoomRocket_Rocket")},
        set(),
    )
    print(f"[weapon-export] source={opened_source} sha256={SOURCE_SHA256}")
    print(f"[weapon-export] launcher={args.launcher_output} sha256={sha256(args.launcher_output)}")
    print(f"[weapon-export] projectile={args.projectile_output} sha256={sha256(args.projectile_output)}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
