"""Isolated original-clip reference playback; never pose an animator's rig.

The adjacent library contains resampled, decoded original SDK animations, not
an engine state-machine emulator. Its armature and meshes are appended into a
separate collection. A private clock evaluates only those reference bones;
the artist scene's frame, FPS, actions, NLA and custom poses are left alone.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import time

import bpy

COLLECTION = "WARLOCK_REFERENCE_LIBRARY"
ACTION_PREFIX = "WARLOCK_REFERENCE::"
_CHANNEL = re.compile(r'^pose\.bones\[("(?:[^"\\]|\\.)*")\]\.(location|rotation_quaternion|scale)$')
_TIMERS = {}
_CURVES = {}
_IMPORT_IDS = ("objects", "collections", "actions", "armatures", "meshes",
               "curves", "materials", "node_groups", "textures", "images")


def discard_failed_import(before):
    """Remove only IDs allocated by this synchronous append operation."""
    for kind in _IMPORT_IDS:
        pool = getattr(bpy.data, kind)
        for item in tuple(pool):
            if item in before[kind]:
                continue
            # These are owned new IDs, never pre-existing artist actions.
            if hasattr(item, "use_fake_user"):
                item.use_fake_user = False
            if kind in {"objects", "collections"}:
                pool.remove(item, do_unlink=True)
            elif item.users == 0:
                pool.remove(item)


def manifest(collection):
    result = json.loads(collection.get("warlock_reference_manifest", "{}"))
    if result.get("schema") != 1 or len(result.get("bone_names", [])) != 138:
        raise ValueError("Reference library has no verified 138-bone manifest")
    clips = result.get("clips", [])
    if len(clips) != 13 or len({clip["id"] for clip in clips}) != 13:
        raise ValueError("Reference library must contain the thirteen original clips")
    return result


def collection_for(scene, owner):
    if not owner:
        return None
    matches = [collection for collection in scene.collection.children_recursive
               if collection.get("warlock_reference_owner") == owner]
    if len(matches) > 1:
        raise ValueError("Multiple reference libraries belong to this rig; keep one")
    return matches[0] if matches else None


def armature_for(collection):
    matches = [obj for obj in collection.all_objects
               if obj.type == "ARMATURE" and obj.get("warlock_reference_only")]
    if len(matches) != 1:
        raise ValueError("Reference library needs exactly one isolated armature")
    return matches[0]


def load_reference(scene, owner, library_path):
    """Append curated reference-only IDs, preserving active object and mode."""
    existing = collection_for(scene, owner)
    if existing:
        manifest(existing)
        return existing
    path = Path(library_path).resolve()
    if not path.is_file():
        raise FileNotFoundError("Keep reference/warlock_animation_reference.blend beside the handoff")
    before = {kind: set(getattr(bpy.data, kind)) for kind in _IMPORT_IDS}
    try:
        # Only collection/action IDs are appended. No Text datablock is requested
        # or executed, and this operation does not enable script auto-execution.
        with bpy.data.libraries.load(str(path), link=False) as (source, target):
            if COLLECTION not in source.collections:
                raise ValueError("This file is not the Warlock original-animation reference library")
            action_names = [name for name in source.actions if name.startswith(ACTION_PREFIX)]
            if len(action_names) != 13:
                raise ValueError("Reference library is missing original clip actions")
            target.collections = [COLLECTION]
            target.actions = sorted(action_names)
        collection = target.collections[0]
        info = manifest(collection)
        action_map = dict(zip(sorted(action_names), target.actions))
        for clip in info["clips"]:
            action = action_map.get(clip["action"])
            if action is None:
                raise ValueError("Reference action is missing: " + clip["id"])
            action.use_fake_user = True
            clip["action"] = action.name
        armature = armature_for(collection)
        if list(armature.data.bones.keys()) != info["bone_names"]:
            raise ValueError("Reference skeleton does not match the library manifest")
        # A loader must never retain references into the artist's armature.
        if any(obj.get("warlock_control_manifest") for obj in collection.all_objects):
            raise ValueError("A control rig cannot be used as an original-clip reference")
        armature.animation_data_clear()
        root = bpy.data.objects.new("WARLOCK_REFERENCE_DISPLAY_OFFSET", None)
        collection.objects.link(root)
        root["warlock_reference_only"] = True
        for obj in tuple(collection.all_objects):
            obj["warlock_reference_only"] = True
            obj["authoring_reference_only"] = True
            obj.hide_render = True
            obj.hide_select = True
            if obj != root and obj.parent is None:
                original_world = obj.matrix_world.copy()
                obj.parent = root
                obj.matrix_world = original_world
        root.location.x = 2.0
        collection.hide_render = True
        collection["warlock_reference_owner"] = owner
        collection["warlock_reference_library_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        collection["warlock_reference_manifest"] = json.dumps(info, separators=(",", ":"))
        collection["warlock_reference_clip"] = info["clips"][0]["id"]
        collection["warlock_reference_frame"] = 1.0
        scene.collection.children.link(collection)
        set_frame(collection, 1.0)
        return collection
    except Exception:
        _CURVES.clear()
        discard_failed_import(before)
        raise


def clip_for(collection, identifier=None):
    identifier = identifier or collection.get("warlock_reference_clip")
    return next((clip for clip in manifest(collection)["clips"] if clip["id"] == identifier), None)


def action_curves(action, armature):
    """Resolve only location/quaternion/scale paths on reference pose bones."""
    key = (action.as_pointer(), armature.as_pointer())
    if key in _CURVES:
        return _CURVES[key]
    curves = []
    channels = set()
    for layer in action.layers:
        for strip in layer.strips:
            if not hasattr(strip, "channelbag"):
                continue
            for slot in action.slots:
                bag = strip.channelbag(slot)
                if bag is None:
                    continue
                for curve in bag.fcurves:
                    match = _CHANNEL.fullmatch(curve.data_path)
                    if not match:
                        raise ValueError("Unexpected reference channel: " + curve.data_path)
                    name, field = json.loads(match[1]), match[2]
                    bone = armature.pose.bones.get(name)
                    if bone is None or not 0 <= curve.array_index < (4 if field == "rotation_quaternion" else 3):
                        raise ValueError("Reference channel does not belong to its skeleton")
                    channel = (name, field, curve.array_index)
                    if channel in channels:
                        raise ValueError("Reference action has duplicate channels")
                    channels.add(channel)
                    curves.append((curve, bone, field, curve.array_index))
    if len(curves) != 1380:
        raise ValueError("Reference action must contain all ten native channels for all 138 bones")
    _CURVES[key] = curves
    return curves


def set_clip(collection, identifier):
    stop(collection)
    clip = clip_for(collection, identifier)
    if clip is None:
        raise ValueError("Unknown original reference clip")
    collection["warlock_reference_clip"] = identifier
    set_frame(collection, float(clip.get("start", 1.0)))
    return clip


def set_frame(collection, frame):
    """Evaluate a reference frame without changing the scene clock or actions."""
    if not math.isfinite(frame):
        raise ValueError("Reference frame must be finite")
    clip = clip_for(collection)
    if clip is None:
        raise ValueError("Select an original reference clip first")
    frame = min(float(clip["end"]), max(float(clip.get("start", 1)), float(frame)))
    armature = armature_for(collection)
    action = bpy.data.actions.get(clip["action"])
    if action is None or armature.animation_data is not None:
        raise ValueError("Reference action is missing or an external animation is driving the reference")
    for curve, bone, field, index in action_curves(action, armature):
        getattr(bone, field)[index] = curve.evaluate(frame)
    armature.update_tag()
    collection["warlock_reference_frame"] = frame
    return frame


def advance(collection, seconds, speed=1.0, loop=True):
    clip = clip_for(collection)
    if clip is None or not all(math.isfinite(value) for value in (seconds, speed)):
        raise ValueError("Reference clock is invalid")
    start, end = float(clip.get("start", 1)), float(clip["end"])
    frame = float(collection.get("warlock_reference_frame", start)) + seconds * clip["fps"] * speed
    if frame > end:
        if loop and end > start:
            frame = start + (frame - start) % (end - start)
        else:
            frame = end
    return set_frame(collection, frame)


def playing(collection):
    record = _TIMERS.get(collection.as_pointer())
    return bool(record and bpy.app.timers.is_registered(record["callback"]))


def start(collection, speed=1.0, loop=True):
    """Start Blender's application timer, leaving the artist timeline frozen."""
    stop(collection)
    if clip_for(collection) is None:
        raise ValueError("Select an original reference clip first")
    pointer = collection.as_pointer()
    record = {"last": time.monotonic(), "callback": None}

    def tick():
        try:
            now = time.monotonic()
            advance(collection, min(now - record["last"], .25), speed, loop)
            record["last"] = now
            if not loop and collection["warlock_reference_frame"] >= clip_for(collection)["end"]:
                _TIMERS.pop(pointer, None)
                return None
            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == "VIEW_3D":
                        area.tag_redraw()
            return 1 / 60
        except (ReferenceError, RuntimeError, ValueError):
            _TIMERS.pop(pointer, None)
            return None

    record["callback"] = tick
    _TIMERS[pointer] = record
    bpy.app.timers.register(tick, first_interval=1 / 60, persistent=False)


def stop(collection):
    record = _TIMERS.pop(collection.as_pointer(), None)
    if record and bpy.app.timers.is_registered(record["callback"]):
        bpy.app.timers.unregister(record["callback"])


def stop_all():
    for record in tuple(_TIMERS.values()):
        if bpy.app.timers.is_registered(record["callback"]):
            bpy.app.timers.unregister(record["callback"])
    _TIMERS.clear()
    _CURVES.clear()
