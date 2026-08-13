"""Render source and normalized launcher geometry from one fixed camera.

This is a visual companion to the exporter's sub-millimetre vertex-distance
check. Run in Blender 5.2 with Crunch's source blend already open.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def args() -> argparse.Namespace:
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--source-output", type=Path, required=True)
    parser.add_argument("--candidate-output", type=Path, required=True)
    return parser.parse_args(values)


def import_candidate(path: Path) -> list[bpy.types.Object]:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(path.resolve()), use_anim=False)
    return [obj for obj in bpy.data.objects if obj not in before]


def world_points(objects: list[bpy.types.Object]) -> list[Vector]:
    return [obj.matrix_world @ vertex.co for obj in objects for vertex in obj.data.vertices]


def render(path: Path, visible: set[bpy.types.Object]) -> None:
    for obj in bpy.context.scene.objects:
        obj.hide_render = obj not in visible and obj.type != "CAMERA"
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(path.resolve())
    bpy.ops.render.render(write_still=True)


def main() -> None:
    options = args()
    source_armature = bpy.data.objects["armature object.008"]
    source = [
        bpy.data.objects["SM_Skaven_WarlockBombardier_RcoketLauncher"],
        bpy.data.objects["SM_Skaven_WarlockBombardier_Rocket"],
    ]
    imported = import_candidate(options.candidate)
    rigs = [
        obj
        for obj in imported
        if obj.type == "ARMATURE"
        and {"root_point", "handle", "p_fx", "a_barrel"}.issubset(
            {bone.name for bone in obj.data.bones}
        )
    ]
    if len(rigs) != 1:
        raise RuntimeError("candidate weapon rig not found")
    rigs[0].matrix_world = (
        source_armature.matrix_world
        @ source_armature.data.bones["j_leftweaponattach"].matrix_local
    )
    candidate = [obj for obj in imported if obj.type == "MESH"]
    bpy.context.view_layer.update()

    points = world_points(source)
    minimum = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    maximum = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    center = (minimum + maximum) * 0.5

    camera_data = bpy.data.cameras.new("weapon_alignment_camera")
    camera = bpy.data.objects.new("weapon_alignment_camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = center + Vector((3.5, -4.5, 2.4))
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = max(maximum - minimum) * 1.35

    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "SINGLE"
    scene.display.shading.single_color = (0.62, 0.62, 0.62)
    scene.display.shading.show_shadows = False
    scene.display.shading.show_cavity = False
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100

    render(options.source_output, set(source))
    render(options.candidate_output, set(candidate))
    print(f"[weapon-render] source={options.source_output}")
    print(f"[weapon-render] candidate={options.candidate_output}")


if __name__ == "__main__":
    main()
