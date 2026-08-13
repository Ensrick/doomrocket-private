#!/usr/bin/env python3
"""Deterministic source regressions for Crunch's launcher and rocket.

The weapon used to be the old Dalo placeholder even after the Warlock body art
was updated.  These tests identify the *mesh data*, not merely the stable unit
filenames, and pin the authored set-03/set-04 texture channel contract.  The
small binary-FBX reader is deliberately local and dependency-free: Blender is
not required to prove which mesh was packaged.
"""

from __future__ import annotations

import hashlib
import re
import struct
import subprocess
import sys
import unittest
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit("Pillow is required for Warlock weapon regressions") from exc


REPO_ROOT = Path(__file__).resolve().parents[2]
ART_ROOT = REPO_ROOT.parent / "_warlock_bombardier_art"
CRUNCH_TEXTURES = ART_ROOT / "crunch_textures"
ROCKET_UNIT_DIR = REPO_ROOT / "units" / "rocket"
ROCKET_TEXTURE_DIR = REPO_ROOT / "textures" / "rocket"
BUNDLE_ROOT = REPO_ROOT / "bundleV2"

sys.path.insert(0, str(REPO_ROOT / "tools"))
from splice_bundle_resource import walk as walk_bundle  # noqa: E402
from strip_bundle_resource import murmur64a, read_bundle  # noqa: E402


# Immutable provenance.  The .blend and ZIP are the exact files Crunch sent;
# the two FBXs are the isolated mesh exports derived from that scene.  Shipping
# FBXs acquire attachment nodes, so their whole-file hashes are intentionally
# *not* expected to equal the isolated exports.
SOURCE_SHA256 = {
    "blend": "ab6ebc9ef45cea6e402bbd0415c2d40716824552c2ab514947902d1eac06c1b2",
    "texture_zip": "551852ee9a9fa99995921e4b6b5cf898d4c17b51486e22fe7772d980f92c2187",
    "launcher_fbx": "1682ecd2979ed988c2254dbabfd20e1d2e5c7d4869ad39b3727872f914f9df69",
    "rocket_fbx": "968539eca60f065b90ed5899195f1eb2dfd6ed2b77ed87a8958ca976dcc0e0ea",
}

# Decoded RGBA baselines for the authored images.  PNG container metadata or
# recompression may change without weakening the actual pixel assertion.
EXPECTED_RGBA = {
    "wb_weapon_df": "f3deef111b8e80eba59e1c2be1efb0a85baaa3f23616dc6d1486b4848d3d1a6f",
    "wb_weapon_nm": "21021c6045dea9e25424bd891031b5be771454678e436ab2e9cd9467055c1a4f",
    "wb_weapon_e": "9185fd2e492d2daf1f826ee37ff67f4a58deeb6888484a408c636f14902471de",
    "wb_weapon_r": "867c1561aafa6234021ae4d938eb28162c0eb5c2cb9f475e5f9fdbd1a3f421a4",
    "wb_weapon_m": "b39d91cb5bc15a9bc973d72a1d3efc847afe02f77ad45c978a635348ebe455bd",
    "wb_weapon_ao": "49b667da7ac6e6bf74cfb21dbde6551fdad7db06d8dc127d401e1d4956cc9e88",
    "wb_rocket_df": "0f2454d2bfd2f20d52dbe1bbe4abb4582f1dde78ae59af9580cf2c374f460b08",
    "wb_rocket_nm": "26b8f5db6b2e1338f22b1a6b2c8fe52f6736b1e783e4c9a563da42bd92b9cbe7",
    "wb_rocket_e": "c1809da6f7c209278c8d701f4040d98064e8d5dadb28c0294702124c19f36f33",
    "wb_rocket_r": "2b21589b36f6a3fe2395ae5d6354cb4b814895b2550dda7c860369011b2215a5",
    "wb_rocket_m": "191aba7b48c52f2fdfe32a331ca076dd468e98de150017df82cb0ca9a017af29",
    "wb_rocket_ao": "e899520017d02889b68152c1972ae271ea888a160c57549f0ce0799e514d63ed",
}

OLD_DALO_FBX_SHA256 = {
    "pRocketLauncher.fbx": "80caf376ba9210b83ded30587f9d2a3663f6614d4b624513307d06dec0e64d5f",
    "SM_Rocket.fbx": "aff853dc8c420b7fd94f7273166025e1baf49c9828274b05ccd5647ab43294c7",
}

CRUNCH_EXPORT_GEOMETRY = {
    "launcher": (4916, 9118, "c4f65cea8b2546cd5e75ca80c505cf67b0737387f873e14e1007f10d0dd901e3"),
    "rocket": (622, 1240, "ef545765bcbb4b88b075e953630b2142f184abf9cb523abf01932358e11815cd"),
}

# Blender rebuilds the source scene's original polygons (the isolated FBXs
# above are triangulated), but keeps all vertices and surfaces.  Pin the final
# polygon streams as well as comparing a scale/rotation/translation-invariant
# shape profile to Crunch's isolated exports.
SHIPPING_GEOMETRY = {
    "launcher": (4916, 4973, "050ff6bd3b279896f860002b1217f1abde57f2d634d53c6a7007a11851644267"),
    "rocket": (622, 672, "6830f43335bfe9fc008137f986af2dc57de44cea3ff16d651ac10faed808876e"),
}

CRUNCH_UV_SHA256 = {
    "launcher": "db3c98bf11a8c4025476e0215ee29c5ecf043833482d87913bb8b16958a7001f",
    "rocket": "a0639c19b8347aac26b54aa283f42fd3e8cb16c07aed56ea6eab824f2d4f79cb",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes())


def rgba(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return image.convert("RGBA")


@dataclass(frozen=True)
class FbxNode:
    name: str
    properties: tuple[Any, ...]
    children: tuple["FbxNode", ...]

    def descendants(self, name: str | None = None) -> Iterator["FbxNode"]:
        for child in self.children:
            if name is None or child.name == name:
                yield child
            yield from child.descendants(name)

    def child(self, name: str) -> "FbxNode":
        matches = [child for child in self.children if child.name == name]
        if len(matches) != 1:
            raise AssertionError(
                f"FBX node {self.name!r} expected one {name!r} child, got {len(matches)}"
            )
        return matches[0]


class BinaryFbx:
    MAGIC = b"Kaydara FBX Binary  \x00\x1a\x00"

    def __init__(self, path: Path):
        self.path = path
        self.data = path.read_bytes()
        if not self.data.startswith(self.MAGIC):
            raise AssertionError(f"{path}: expected a binary FBX")
        self.version = struct.unpack_from("<I", self.data, len(self.MAGIC))[0]
        self.wide = self.version >= 7500
        self.null_size = 25 if self.wide else 13
        self.nodes, offset = self._nodes(len(self.MAGIC) + 4, len(self.data))
        if offset > len(self.data):
            raise AssertionError(f"{path}: FBX node table overran file")

    def _uint(self, offset: int) -> tuple[int, int]:
        code = "<Q" if self.wide else "<I"
        size = 8 if self.wide else 4
        return struct.unpack_from(code, self.data, offset)[0], offset + size

    def _property(self, offset: int) -> tuple[Any, int]:
        kind = chr(self.data[offset])
        offset += 1
        scalar = {
            "Y": ("<h", 2),
            "C": ("<?", 1),
            "I": ("<i", 4),
            "F": ("<f", 4),
            "D": ("<d", 8),
            "L": ("<q", 8),
        }
        if kind in scalar:
            code, size = scalar[kind]
            return struct.unpack_from(code, self.data, offset)[0], offset + size
        if kind in "SR":
            size = struct.unpack_from("<I", self.data, offset)[0]
            offset += 4
            raw = self.data[offset : offset + size]
            if kind == "S":
                return raw.decode("utf-8", errors="strict"), offset + size
            return raw, offset + size
        arrays = {
            "f": ("f", 4),
            "d": ("d", 8),
            "l": ("q", 8),
            "i": ("i", 4),
            "b": ("?", 1),
            "c": ("b", 1),
        }
        if kind in arrays:
            count, encoding, byte_count = struct.unpack_from("<III", self.data, offset)
            offset += 12
            raw = self.data[offset : offset + byte_count]
            if encoding == 1:
                raw = zlib.decompress(raw)
            elif encoding != 0:
                raise AssertionError(f"{self.path}: unsupported FBX array encoding {encoding}")
            code, item_size = arrays[kind]
            expected = count * item_size
            if len(raw) != expected:
                raise AssertionError(
                    f"{self.path}: {kind} array expected {expected} bytes, got {len(raw)}"
                )
            return tuple(value[0] for value in struct.iter_unpack("<" + code, raw)), offset + byte_count
        raise AssertionError(f"{self.path}: unsupported FBX property type {kind!r}")

    def _nodes(self, offset: int, limit: int) -> tuple[tuple[FbxNode, ...], int]:
        nodes: list[FbxNode] = []
        while offset + self.null_size <= limit:
            if self.data[offset : offset + self.null_size] == bytes(self.null_size):
                return tuple(nodes), offset + self.null_size
            start = offset
            end_offset, offset = self._uint(offset)
            property_count, offset = self._uint(offset)
            property_bytes, offset = self._uint(offset)
            name_size = self.data[offset]
            offset += 1
            name = self.data[offset : offset + name_size].decode("utf-8", errors="strict")
            offset += name_size
            properties: list[Any] = []
            property_start = offset
            for _ in range(property_count):
                value, offset = self._property(offset)
                properties.append(value)
            if offset - property_start != property_bytes:
                raise AssertionError(
                    f"{self.path}: property length mismatch in {name!r} at {start}"
                )
            children: tuple[FbxNode, ...] = ()
            child_limit = end_offset - self.null_size
            if offset < child_limit:
                children, offset = self._nodes(offset, end_offset)
            if offset < end_offset:
                # Empty child lists still include their null record.
                offset = end_offset
            if offset != end_offset:
                raise AssertionError(
                    f"{self.path}: node {name!r} ended at {offset}, expected {end_offset}"
                )
            nodes.append(FbxNode(name, tuple(properties), children))
        return tuple(nodes), offset

    def descendants(self, name: str | None = None) -> Iterator[FbxNode]:
        for node in self.nodes:
            if name is None or node.name == name:
                yield node
            yield from node.descendants(name)

    def object_nodes(self, kind: str) -> list[FbxNode]:
        return [
            node
            for node in self.descendants(kind)
            if len(node.properties) >= 3 and isinstance(node.properties[0], int)
        ]


def clean_fbx_name(value: str) -> str:
    """Return the artist-visible part of ``Model::foo\x00\x01Model``."""
    value = value.split("\x00", 1)[0]
    # FBX producers disagree on whether the type prefix is ``Model::foo`` or
    # simply ``Modelfoo``; normalize both without stripping legitimate names.
    value = value.split("::", 1)[-1]
    return value.removeprefix("Model::").removeprefix("Model")


def polygon_count(indices: tuple[int, ...]) -> int:
    return sum(index < 0 for index in indices)


def geometry_signature(node: FbxNode) -> tuple[int, int, str]:
    vertices = node.child("Vertices").properties[0]
    polygons = node.child("PolygonVertexIndex").properties[0]
    # Connectivity is invariant under FBX float precision/version changes and
    # sharply distinguishes the 2024 Dalo meshes from Crunch's final meshes.
    topology = struct.pack(f"<{len(polygons)}q", *polygons)
    return len(vertices) // 3, polygon_count(polygons), sha256(topology)


def geometry_manifest(fbx: BinaryFbx) -> dict[str, tuple[int, int, str]]:
    return {
        clean_fbx_name(node.properties[1]): geometry_signature(node)
        for node in fbx.object_nodes("Geometry")
        if node.properties[2] == "Mesh"
    }


def geometry_by_vertex_count(fbx: BinaryFbx, count: int) -> FbxNode:
    matches = [
        node
        for node in fbx.object_nodes("Geometry")
        if node.properties[2] == "Mesh"
        and len(node.child("Vertices").properties[0]) // 3 == count
    ]
    if len(matches) != 1:
        raise AssertionError(f"{fbx.path}: expected one {count}-vertex mesh, got {len(matches)}")
    return matches[0]


def shape_profile(node: FbxNode) -> tuple[float, ...]:
    """Sorted normalized radius squared for every vertex.

    This remains unchanged by the rigid placement and centimetre-to-metre
    conversion applied to the source weapon.  Comparing every element catches
    geometry substitution while tolerating only FBX float round-off.
    """
    values = node.child("Vertices").properties[0]
    points = tuple(zip(values[0::3], values[1::3], values[2::3]))
    centroid = tuple(
        sum(point[axis] for point in points) / len(points) for axis in range(3)
    )
    radii = [
        sum((point[axis] - centroid[axis]) ** 2 for axis in range(3))
        for point in points
    ]
    mean_radius = sum(radii) / len(radii)
    return tuple(sorted(radius / mean_radius for radius in radii))


def uv_signature(node: FbxNode) -> tuple[int, str]:
    layers = [child for child in node.children if child.name == "LayerElementUV"]
    if len(layers) != 1:
        raise AssertionError(f"{node.properties[1]!r}: expected one UV layer, got {len(layers)}")
    fields = {child.name: child.properties[0] for child in layers[0].children if child.properties}
    if fields.get("Name") != "UVMap":
        raise AssertionError(f"{node.properties[1]!r}: expected UVMap, got {fields.get('Name')!r}")
    if fields.get("MappingInformationType") != "ByPolygonVertex":
        raise AssertionError(f"{node.properties[1]!r}: UVs must map ByPolygonVertex")
    if fields.get("ReferenceInformationType") != "IndexToDirect":
        raise AssertionError(f"{node.properties[1]!r}: UVs must use IndexToDirect")
    values = fields["UV"]
    return len(values), sha256(struct.pack(f"<{len(values)}d", *values))


def model_names(fbx: BinaryFbx) -> set[str]:
    return {
        clean_fbx_name(node.properties[1])
        for node in fbx.object_nodes("Model")
    }


def model_node(fbx: BinaryFbx, name: str, kind: str | None = None) -> FbxNode:
    matches = [
        node
        for node in fbx.object_nodes("Model")
        if clean_fbx_name(node.properties[1]) == name
        and (kind is None or node.properties[2] == kind)
    ]
    if len(matches) != 1:
        raise AssertionError(f"{fbx.path}: expected one Model {name!r}/{kind}, got {len(matches)}")
    return matches[0]


def model_parent_ids(fbx: BinaryFbx) -> dict[int, int]:
    result: dict[int, int] = {}
    for connection in fbx.descendants("C"):
        if (
            len(connection.properties) >= 3
            and connection.properties[0] == "OO"
            and isinstance(connection.properties[1], int)
            and isinstance(connection.properties[2], int)
        ):
            result[connection.properties[1]] = connection.properties[2]
    return result


def require_loaded_rocket_actor_hierarchy(
    fbx: BinaryFbx, parents: dict[int, int] | None = None
) -> None:
    """Require the loaded warhead to inherit the launcher's dropped actor.

    VT2's AIInventoryExtension unlinks a death-dropped inventory unit and
    creates only its ``rp_dropped`` actor.  Doomrocket binds that actor to the
    ``pRocketLauncher`` node, so a sibling ``pRocket`` freezes at the unlink
    pose instead of following physics.
    """
    launcher = model_node(fbx, "pRocketLauncher", "Mesh")
    loaded_rocket = model_node(fbx, "pRocket", "Mesh")
    parents = model_parent_ids(fbx) if parents is None else parents
    if parents.get(loaded_rocket.properties[0]) != launcher.properties[0]:
        raise AssertionError(
            "loaded pRocket must be a direct child of actor-owned pRocketLauncher"
        )


def local_translation(node: FbxNode) -> tuple[float, float, float]:
    blocks = [child for child in node.children if child.name == "Properties70"]
    if len(blocks) != 1:
        raise AssertionError(f"Model {node.properties[1]!r} has no unique Properties70")
    translations = [
        child.properties[-3:]
        for child in blocks[0].children
        if child.name == "P" and child.properties[0] == "Lcl Translation"
    ]
    return tuple(translations[0]) if translations else (0.0, 0.0, 0.0)


def material_names(fbx: BinaryFbx) -> set[str]:
    return {
        clean_fbx_name(node.properties[1])
        for node in fbx.object_nodes("Material")
    }


def without_comments(source: str) -> str:
    return re.sub(r"//[^\r\n]*", "", source)


def descriptor_field(source: str, name: str) -> str:
    match = re.search(
        rf'\b{re.escape(name)}\s*=\s*(?:"([^"]+)"|([^\s\}}]+))',
        source,
    )
    if not match:
        raise AssertionError(f"texture descriptor has no {name!r} field")
    return match.group(1) or match.group(2)


def named_block(source: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}\s*=\s*\{{", source)
    if not match:
        raise AssertionError(f"missing {name} block")
    start = match.end()
    depth = 1
    in_string = False
    escaped = False
    for offset, character in enumerate(source[start:], start):
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        elif character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return source[start:offset]
    raise AssertionError(f"unterminated {name} block")


def named_array(source: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}\s*=\s*\[", source)
    if not match:
        raise AssertionError(f"missing {name} array")
    start = match.end()
    depth = 1
    in_string = False
    escaped = False
    for offset, character in enumerate(source[start:], start):
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        elif character == '"':
            in_string = True
        elif character == "[":
            depth += 1
        elif character == "]":
            depth -= 1
            if depth == 0:
                return source[start:offset]
    raise AssertionError(f"unterminated {name} array")


def anonymous_blocks(source: str) -> list[str]:
    """Return top-level anonymous table entries from a named array body."""
    result: list[str] = []
    depth = 0
    start: int | None = None
    in_string = False
    escaped = False
    for offset, character in enumerate(source):
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        elif character == '"':
            in_string = True
        elif character == "{":
            if depth == 0:
                start = offset + 1
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0 and start is not None:
                result.append(source[start:offset])
                start = None
            elif depth < 0:
                raise AssertionError("unbalanced anonymous table")
    if depth != 0:
        raise AssertionError("unterminated anonymous table")
    return result


@dataclass(frozen=True)
class CompiledSceneNode:
    parent_type: int
    parent_index: int
    name_hash: int


@dataclass(frozen=True)
class CompiledUnitStructure:
    nodes: tuple[CompiledSceneNode, ...]
    mesh_node_indices: tuple[int, ...]
    actors: tuple[tuple[int, int], ...]  # (name hash, node hash)


class PackedCursor:
    """Small dependency-free cursor for the VT2 v189 unit prefix."""

    def __init__(self, payload: bytes):
        self.payload = payload
        self.offset = 0

    def skip(self, size: int) -> None:
        if size < 0 or self.offset + size > len(self.payload):
            raise AssertionError("compiled unit prefix overrun")
        self.offset += size

    def u8(self) -> int:
        value = struct.unpack_from("<B", self.payload, self.offset)[0]
        self.skip(1)
        return value

    def u16(self) -> int:
        value = struct.unpack_from("<H", self.payload, self.offset)[0]
        self.skip(2)
        return value

    def u32(self) -> int:
        value = struct.unpack_from("<I", self.payload, self.offset)[0]
        self.skip(4)
        return value

    def byte_array(self) -> None:
        self.skip(self.u32())

    def u32_array(self) -> None:
        self.skip(self.u32() * 4)


def compiled_unit_structure(payload: bytes) -> CompiledUnitStructure:
    """Parse scene graph, renderables and actors from a VT2 v189 unit.

    This is the same packed prefix consumed by Bitsquid Blender Tools'
    UnitResourceVT2 parser, kept local so this regression runs under ordinary
    Python without importing Blender's ``bpy``/``mathutils`` modules.
    """
    cursor = PackedCursor(payload)
    version = cursor.u32()
    if version != 189:
        raise AssertionError(f"compiled unit version must be 189, got {version}")

    for _ in range(cursor.u32()):  # MeshGeometryVT2[]
        for _ in range(cursor.u32()):  # streams
            cursor.byte_array()
            cursor.skip(16)  # validity, stream type, vertex count, stride
        cursor.skip(cursor.u32() * 17)  # vertex declaration channels
        cursor.skip(16)  # index stream header
        cursor.byte_array()
        cursor.skip(cursor.u32() * 16)  # batch ranges
        cursor.skip(28)  # bounding volume
        cursor.skip(cursor.u32() * 4)  # material IDString32s

    for _ in range(cursor.u32()):  # SkinData[]
        cursor.skip(cursor.u32() * 64)  # inverse bind matrices
        cursor.u32_array()  # node indices
        for _ in range(cursor.u32()):
            cursor.u32_array()  # matrix index set

    cursor.byte_array()  # simple animation
    for _ in range(cursor.u32()):  # simple animation groups
        cursor.skip(4)  # name IDString32
        cursor.u32_array()

    node_count = cursor.u32()
    cursor.skip(node_count * 60)  # local rotation, position, scale
    cursor.skip(node_count * 64)  # world matrices
    parent_data = [(cursor.u16(), cursor.u16()) for _ in range(node_count)]
    nodes = tuple(
        CompiledSceneNode(parent_type, parent_index, cursor.u32())
        for parent_type, parent_index in parent_data
    )

    mesh_node_indices: list[int] = []
    for _ in range(cursor.u32()):  # MeshObject[]
        cursor.skip(4)  # renderable name hash
        mesh_node_indices.append(cursor.u32())
        cursor.skip(12)  # geometry index, skin index, flags
        cursor.skip(28)  # bounding volume

    actors: list[tuple[int, int]] = []
    shape_extra_sizes = {0: 4, 1: 12, 2: 8, 3: 0, 4: 0, 5: 21, 6: 12}
    for _ in range(cursor.u32()):  # ActorResource[]
        actor_name = cursor.u32()
        cursor.skip(4)  # actor template
        actor_node = cursor.u32()
        cursor.skip(4)  # mass
        for _ in range(cursor.u32()):
            shape_type = cursor.u32()
            if shape_type not in shape_extra_sizes:
                raise AssertionError(f"unknown compiled actor shape {shape_type}")
            cursor.skip(8 + 64)  # material, template, local matrix
            cursor.byte_array()
            cursor.skip(4 + shape_extra_sizes[shape_type])  # shape node + data
        cursor.skip(24)  # touch/trigger events
        if cursor.u8() not in (0, 1):
            raise AssertionError("compiled actor enabled flag is not boolean")
        actors.append((actor_name, actor_node))

    return CompiledUnitStructure(nodes, tuple(mesh_node_indices), tuple(actors))


def idstring32(value: str) -> int:
    return murmur64a(value.encode()) >> 32


def compiled_node_index(structure: CompiledUnitStructure, name: str) -> int:
    expected = idstring32(name)
    matches = [index for index, node in enumerate(structure.nodes) if node.name_hash == expected]
    if len(matches) != 1:
        raise AssertionError(f"compiled unit expected one scene node {name!r}, got {matches}")
    return matches[0]


def node_inherits(nodes: tuple[CompiledSceneNode, ...], node: int, ancestor: int) -> bool:
    visited: set[int] = set()
    while node not in visited and 0 <= node < len(nodes):
        if node == ancestor:
            return True
        visited.add(node)
        parent = nodes[node]
        if parent.parent_type != 1:  # ParentType.INTERNAL
            return False
        node = parent.parent_index
    return False


def compiled_bundle_resources() -> dict[tuple[int, int], list[tuple[Path, bytes]]]:
    """Index every compiled resource without extracting or mutating bundles."""
    resources: dict[tuple[int, int], list[tuple[Path, bytes]]] = {}
    for bundle in sorted(BUNDLE_ROOT.glob("*.mod_bundle")):
        bundle_format, _, data = read_bundle(bundle)
        _, _, records = walk_bundle(data, bundle_format)
        for record in records:
            for version in record["versions"]:
                start = version["payload_offset"]
                end = start + version["size"]
                resources.setdefault((record["type"], record["name"]), []).append(
                    (bundle, data[start:end])
                )
    return resources


def resource_key(resource_type: str, resource_name: str) -> tuple[int, int]:
    return murmur64a(resource_type.encode()), murmur64a(resource_name.encode())


def compiled_material_pairs(payload: bytes) -> set[tuple[int, int]]:
    """Read the unit's terminal slot->material map using the VT2 v189 layout.

    The complete UnitResource parser established that the final fields are
    default_material_resource:u64, count:u32, then count*(slot:u32,
    material:u64), followed by apex byte array, vehicle count, and skeleton.
    Search from the end for the unique tail that consumes the whole payload;
    this keeps the regression dependency-free while still parsing structure,
    rather than accepting arbitrary hash occurrences in geometry data.
    """
    candidates: list[set[tuple[int, int]]] = []
    for offset in range(max(0, len(payload) - 512), len(payload) - 24):
        count = struct.unpack_from("<I", payload, offset + 8)[0]
        if count > 32:
            continue
        cursor = offset + 12 + count * 12
        if cursor + 16 > len(payload):
            continue
        apex_size = struct.unpack_from("<I", payload, cursor)[0]
        cursor += 4 + apex_size
        if cursor + 12 != len(payload):
            continue
        vehicle_count = struct.unpack_from("<I", payload, cursor)[0]
        if vehicle_count != 0:
            continue
        pairs = {
            struct.unpack_from("<IQ", payload, offset + 12 + index * 12)
            for index in range(count)
        }
        if any(slot == 0 or material == 0 for slot, material in pairs):
            continue
        candidates.append(pairs)
    if len(candidates) != 1:
        raise AssertionError(
            f"compiled unit expected one terminal material table, got {len(candidates)}"
        )
    return candidates[0]


class CrunchWeaponProvenanceTests(unittest.TestCase):
    def test_authoritative_local_sources_have_reviewed_hashes(self) -> None:
        sources = {
            "blend": Path.home() / "Downloads" / "xud4soo5fg7g8qd4.blend",
            "texture_zip": Path.home() / "Downloads" / "zxnu2hjyuovl4rhx.zip",
            "launcher_fbx": ART_ROOT / "warlock_rocketlauncher.fbx",
            "rocket_fbx": ART_ROOT / "warlock_rocket.fbx",
        }
        for name, path in sources.items():
            with self.subTest(source=name):
                if not path.is_file():
                    continue
                self.assertEqual(file_sha256(path), SOURCE_SHA256[name])

    def test_isolated_exports_have_expected_mesh_and_material_identity(self) -> None:
        expected = {
            "launcher_fbx": (ART_ROOT / "warlock_rocketlauncher.fbx", 4916, 9118, "DoomRocket_Weapon"),
            "rocket_fbx": (ART_ROOT / "warlock_rocket.fbx", 622, 1240, "DoomRocket_Rocket"),
        }
        for name, (path, vertex_count, face_count, material) in expected.items():
            with self.subTest(source=name):
                if not path.is_file():
                    continue
                fbx = BinaryFbx(path)
                meshes = geometry_manifest(fbx)
                self.assertEqual(len(meshes), 1)
                signature = next(iter(meshes.values()))
                self.assertEqual(signature[:2], (vertex_count, face_count))
                self.assertEqual(signature, CRUNCH_EXPORT_GEOMETRY["launcher" if name == "launcher_fbx" else "rocket"])
                self.assertEqual(material_names(fbx), {material})

    def test_exporter_pins_crunch_source_and_immutable_legacy_blobs(self) -> None:
        source = (REPO_ROOT / "tools" / "prepare_warlock_weapon_fbx.py").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            f'SOURCE_SHA256 = "{SOURCE_SHA256["blend"].upper()}"',
            source,
        )
        expected = {
            "4afd3ff155889b44760ff41500bca7e1bf6ccafa": OLD_DALO_FBX_SHA256[
                "pRocketLauncher.fbx"
            ],
            "445636e36fc62a8aef8883d2f59ed85eaa6707a0": OLD_DALO_FBX_SHA256[
                "SM_Rocket.fbx"
            ],
        }
        for blob, expected_sha in expected.items():
            with self.subTest(blob=blob):
                self.assertIn(f'"blob": "{blob}"', source)
                self.assertIn(f'"sha256": "{expected_sha.upper()}"', source)
                payload = subprocess.run(
                    ["git", "-C", str(REPO_ROOT), "cat-file", "blob", blob],
                    check=True,
                    capture_output=True,
                ).stdout
                self.assertEqual(sha256(payload), expected_sha)
        self.assertIn("legacy launcher input must not be overwritten", source)
        self.assertIn("legacy projectile input must not be overwritten", source)
        self.assertIn("loaded_rocket.parent = launcher", source)


class CrunchWeaponFbxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.launcher = BinaryFbx(ROCKET_UNIT_DIR / "pRocketLauncher.fbx")
        cls.projectile = BinaryFbx(ROCKET_UNIT_DIR / "SM_Rocket.fbx")

    def test_launcher_contains_crunch_launcher_and_loaded_rocket_meshes(self) -> None:
        signatures = set(geometry_manifest(self.launcher).values())
        self.assertEqual(signatures, set(SHIPPING_GEOMETRY.values()))

    def test_standalone_projectile_is_crunch_rocket_mesh(self) -> None:
        signatures = list(geometry_manifest(self.projectile).values())
        self.assertEqual(len(signatures), 1)
        self.assertEqual(signatures[0], SHIPPING_GEOMETRY["rocket"])

    @unittest.skipUnless(ART_ROOT.is_dir(), "Crunch isolated mesh exports are not present")
    def test_shipping_shapes_match_crunch_exports_after_rigid_placement(self) -> None:
        sources = {
            "launcher": BinaryFbx(ART_ROOT / "warlock_rocketlauncher.fbx"),
            "rocket": BinaryFbx(ART_ROOT / "warlock_rocket.fbx"),
        }
        shipping = {
            "launcher": (self.launcher, 4916),
            "rocket_loaded": (self.launcher, 622),
            "rocket_projectile": (self.projectile, 622),
        }
        for name, (fbx, count) in shipping.items():
            source_name = "launcher" if name == "launcher" else "rocket"
            expected = shape_profile(geometry_by_vertex_count(sources[source_name], count))
            actual = shape_profile(geometry_by_vertex_count(fbx, count))
            self.assertEqual(len(actual), len(expected))
            self.assertLess(
                max(abs(left - right) for left, right in zip(actual, expected)),
                2e-6,
                f"{name}: vertex shape differs from Crunch's authoritative mesh",
            )

    def test_crunch_uv_coordinate_banks_are_preserved_exactly(self) -> None:
        launcher_uv = uv_signature(geometry_by_vertex_count(self.launcher, 4916))
        loaded_uv = uv_signature(geometry_by_vertex_count(self.launcher, 622))
        projectile_uv = uv_signature(geometry_by_vertex_count(self.projectile, 622))
        self.assertEqual(launcher_uv, (12668, CRUNCH_UV_SHA256["launcher"]))
        self.assertEqual(loaded_uv, (1744, CRUNCH_UV_SHA256["rocket"]))
        self.assertEqual(projectile_uv, loaded_uv)

    def test_launcher_preserves_all_runtime_attachment_nodes(self) -> None:
        required = {"root_point", "handle", "p_fx", "a_barrel"}
        self.assertEqual(required - model_names(self.launcher), set())

    def test_raw_fbx_model_names_exactly_match_runtime_string_contracts(self) -> None:
        launcher_models = [
            (clean_fbx_name(node.properties[1]), node.properties[2])
            for node in self.launcher.object_nodes("Model")
        ]
        self.assertEqual(
            {name for name, kind in launcher_models if kind == "Mesh"},
            {"pRocketLauncher", "pRocket"},
        )
        self.assertIn(("root_point", "Null"), launcher_models)
        for bone in ("root_point", "handle", "p_fx", "a_barrel"):
            self.assertIn((bone, "LimbNode"), launcher_models)
        projectile_models = [
            (clean_fbx_name(node.properties[1]), node.properties[2])
            for node in self.projectile.object_nodes("Model")
        ]
        self.assertEqual(projectile_models, [("pRocket", "Mesh")])
        for name, _kind in launcher_models + projectile_models:
            self.assertNotRegex(name, r"\.\d{3}$")

    def test_runtime_renderable_and_actor_node_names_are_exact(self) -> None:
        launcher_names = model_names(self.launcher)
        projectile_names = model_names(self.projectile)
        self.assertEqual({"pRocketLauncher", "pRocket"} - launcher_names, set())
        self.assertIn("pRocket", projectile_names)
        model_node(self.launcher, "root_point", "Null")
        model_node(self.launcher, "pRocketLauncher", "Mesh")
        model_node(self.launcher, "pRocket", "Mesh")
        model_node(self.projectile, "pRocket", "Mesh")
        # A Blender collision suffix changes the Stingray node name and leaves
        # the .unit renderable/.physics actor pointing at nothing.
        for name in launcher_names | projectile_names:
            self.assertNotRegex(name, r"^(?:pRocketLauncher|pRocket|root_point)\.\d+$")

    def test_attachment_node_rest_transforms_are_preserved(self) -> None:
        expected = {
            "root_point": (0.0, 0.0, 0.0),
            "handle": (0.0, -0.42, 0.05),
            "p_fx": (0.0, 0.85, 0.06),
            "a_barrel": (0.17, 0.40, 0.06),
        }
        for name, translation in expected.items():
            with self.subTest(node=name):
                actual = local_translation(model_node(self.launcher, name, "LimbNode"))
                for actual_axis, expected_axis in zip(actual, translation):
                    self.assertAlmostEqual(actual_axis, expected_axis, places=5)

    def test_loaded_warhead_is_rigid_child_of_actor_owned_launcher(self) -> None:
        require_loaded_rocket_actor_hierarchy(self.launcher)

    def test_hierarchy_guard_rejects_historical_sibling_warhead(self) -> None:
        launcher = model_node(self.launcher, "pRocketLauncher", "Mesh")
        loaded_rocket = model_node(self.launcher, "pRocket", "Mesh")
        root = model_node(self.launcher, "root_point", "Null")
        parents = model_parent_ids(self.launcher)
        self.assertEqual(parents[loaded_rocket.properties[0]], launcher.properties[0])

        # Recreate the v0.1.53 failure in memory: both meshes are siblings under
        # root_point, while rp_dropped drives only pRocketLauncher.
        historical_sibling = dict(parents)
        historical_sibling[loaded_rocket.properties[0]] = root.properties[0]
        with self.assertRaisesRegex(AssertionError, "direct child of actor-owned"):
            require_loaded_rocket_actor_hierarchy(self.launcher, historical_sibling)

    def test_launcher_and_attachment_nodes_keep_one_weapon_root(self) -> None:
        root = model_node(self.launcher, "root_point", "Null")
        parents = model_parent_ids(self.launcher)
        for name, kind in (
            ("pRocketLauncher", "Mesh"),
            ("root_point", "LimbNode"),
            ("handle", "LimbNode"),
            ("p_fx", "LimbNode"),
            ("a_barrel", "LimbNode"),
        ):
            with self.subTest(node=name, kind=kind):
                node = model_node(self.launcher, name, kind)
                self.assertEqual(parents.get(node.properties[0]), root.properties[0])

    def test_fbx_material_identities_are_final_not_lambert(self) -> None:
        self.assertEqual(
            material_names(self.launcher),
            {"DoomRocket_Weapon", "DoomRocket_Rocket"},
        )
        self.assertEqual(material_names(self.projectile), {"DoomRocket_Rocket"})
        for fbx in (self.launcher, self.projectile):
            for material in material_names(fbx):
                self.assertNotRegex(material, r"(?i)^lambert\d*$")

    def test_whole_files_are_not_the_old_dalo_placeholders(self) -> None:
        for filename, rejected in OLD_DALO_FBX_SHA256.items():
            with self.subTest(fbx=filename):
                self.assertNotEqual(file_sha256(ROCKET_UNIT_DIR / filename), rejected)


class CrunchWeaponTextureTests(unittest.TestCase):
    # These names form the runtime contract; descriptors and materials must not
    # silently fall back to body set-01/02 or the old solid-color placeholders.
    TARGETS = {
        "weapon": ("03", (1024, 1024)),
        "rocket": ("04", (512, 512)),
    }

    def test_committed_adapters_match_authored_set_03_and_04_pixels(self) -> None:
        for target, (index, size) in self.TARGETS.items():
            source_dir = CRUNCH_TEXTURES / str(size[0])
            prefix = "T_Skaven_WarlockBombardier_"
            paths = {
                "df": source_dir / f"{prefix}BC_{index}.png",
                "nm": source_dir / f"{prefix}NR_{index}.png",
                "mase": source_dir / f"{prefix}MASE_{index}.png",
                "fix": source_dir / f"{prefix}MASE_{index}_Fix.png",
            }
            output = {
                suffix: ROCKET_TEXTURE_DIR / f"wb_{target}_{suffix}.png"
                for suffix in ("df", "nm", "e", "r", "m", "ao")
            }
            for path in output.values():
                self.assertTrue(path.is_file(), f"missing runtime texture {path}")
            for path in output.values():
                self.assertEqual(rgba(path).size, size)
                self.assertEqual(
                    sha256(rgba(path).tobytes()),
                    EXPECTED_RGBA[path.stem],
                    f"{path.name}: decoded pixels differ from the reviewed Crunch master",
                )
            if all(path.is_file() for path in paths.values()):
                self.assertEqual(rgba(output["df"]).tobytes(), rgba(paths["df"]).tobytes())
                self.assertEqual(rgba(output["nm"]).tobytes(), rgba(paths["nm"]).tobytes())
            self.assertFalse(
                (ROCKET_TEXTURE_DIR / f"wb_{target}_ma.png").exists(),
                "packed prop map is not consumed by the standard material",
            )

    def test_texture_descriptors_preserve_color_space_and_alpha_channels(self) -> None:
        expected_srgb = {
            "df": "true",
            "nm": "false",
            "e": "true",
            "r": "false",
            "m": "false",
            "ao": "false",
        }
        for target in self.TARGETS:
            for suffix, srgb in expected_srgb.items():
                with self.subTest(texture=f"{target}_{suffix}"):
                    path = ROCKET_TEXTURE_DIR / f"wb_{target}_{suffix}.texture"
                    source = path.read_text(encoding="utf-8")
                    filenames = re.findall(r'\bfilename\s*=\s*"([^"]+)"', source)
                    self.assertEqual(filenames, [f"textures/rocket/wb_{target}_{suffix}"])
                    self.assertEqual(descriptor_field(source, "format"), "BC7")
                    self.assertEqual(descriptor_field(source, "srgb"), srgb)
                    self.assertEqual(descriptor_field(source, "apply_processing"), "true")
                    self.assertEqual(
                        descriptor_field(source, "enable_cut_alpha_threshold"),
                        "false",
                    )
                    self.assertEqual(descriptor_field(source, "streamable"), "true")

    def test_split_scalar_maps_are_exact_authored_channels(self) -> None:
        channels = {"r": ("nm", "A"), "m": ("fix", "R"), "ao": ("fix", "G")}
        for target, (index, size) in self.TARGETS.items():
            source_dir = CRUNCH_TEXTURES / str(size[0])
            prefix = "T_Skaven_WarlockBombardier_"
            sources = {
                "nm": rgba(source_dir / f"{prefix}NR_{index}.png"),
                "fix": rgba(source_dir / f"{prefix}MASE_{index}_Fix.png"),
            }
            for suffix, (source_name, channel) in channels.items():
                with self.subTest(texture=f"{target}_{suffix}"):
                    expected = sources[source_name].getchannel(channel)
                    actual = rgba(ROCKET_TEXTURE_DIR / f"wb_{target}_{suffix}.png")
                    for output_channel in "RGB":
                        self.assertEqual(actual.getchannel(output_channel).tobytes(), expected.tobytes())
            emissive = rgba(source_dir / f"{prefix}E_{index}.png").convert("RGB")
            self.assertEqual(
                rgba(ROCKET_TEXTURE_DIR / f"wb_{target}_e.png").convert("RGB").tobytes(),
                emissive.tobytes(),
            )


class CrunchWeaponUnitContractTests(unittest.TestCase):
    EXPECTED = {
        "pRocketLauncher.unit": {
            "slots": {"DoomRocket_Weapon", "DoomRocket_Rocket"},
            "renderables": {"pRocketLauncher", "pRocket"},
        },
        "SM_Rocket.unit": {
            "slots": {"DoomRocket_Rocket"},
            "renderables": {"pRocket"},
        },
    }

    def test_unit_material_slots_cover_every_final_fbx_slot(self) -> None:
        for filename, expected in self.EXPECTED.items():
            with self.subTest(unit=filename):
                source = without_comments((ROCKET_UNIT_DIR / filename).read_text(encoding="utf-8"))
                materials = dict(re.findall(r'(\w+)\s*=\s*"([^"]+)"', named_block(source, "materials")))
                slots = set(re.findall(r'\bslot\d+\s*=\s*"([^"]+)"', named_block(source, "mat_slots")))
                renderables = set(re.findall(r"(?m)^\s*(\w+)\s*=\s*\{", named_block(source, "renderables")))
                self.assertEqual(slots, expected["slots"])
                self.assertEqual(slots - materials.keys(), set())
                self.assertEqual(renderables, expected["renderables"])
                for slot, material in materials.items():
                    self.assertNotRegex(slot, r"(?i)^lambert\d*$")
                    self.assertRegex(material, r"^materials/rocket/")
                    self.assertTrue((REPO_ROOT / f"{material}.material").is_file())

    def test_rigid_materials_bind_every_authored_sampler(self) -> None:
        materials = {
            "materials/rocket/rocket_neutral.material": "weapon",
            "materials/rocket/rocket_red.material": "rocket",
        }
        for relative, target in materials.items():
            with self.subTest(material=relative):
                source = without_comments((REPO_ROOT / relative).read_text(encoding="utf-8"))
                self.assertRegex(
                    source,
                    r'(?m)^\s*parent_material\s*=\s*"core/stingray_renderer/shader_import/standard"',
                )
                block = named_block(source, "textures")
                bindings = dict(re.findall(r'(\w+)\s*=\s*"([^"]+)"', block))
                self.assertEqual(
                    bindings,
                    {
                        "color_map": f"textures/rocket/wb_{target}_df",
                        "normal_map": f"textures/rocket/wb_{target}_nm",
                        "roughness_map": f"textures/rocket/wb_{target}_r",
                        "metallic_map": f"textures/rocket/wb_{target}_m",
                        "ao_map": f"textures/rocket/wb_{target}_ao",
                        "emissive_map": f"textures/rocket/wb_{target}_e",
                    },
                )
                variables = named_block(source, "variables")
                # These are the exact controls exported by the VT2 SDK's
                # core/stingray_renderer/shader_import/standard parent.  A
                # bound sampler with its use flag left at zero renders as the
                # fallback scalar/color and recreates the placeholder bug.
                for variable in (
                    "use_color_map",
                    "use_normal_map",
                    "use_roughness_map",
                    "use_metallic_map",
                    "use_ao_map",
                    "use_emissive_map",
                ):
                    with self.subTest(material=relative, variable=variable):
                        block = named_block(variables, variable)
                        self.assertEqual(descriptor_field(block, "type"), "scalar")
                        self.assertEqual(descriptor_field(block, "value"), "1")

    def test_units_have_no_lambert_or_old_placeholder_references(self) -> None:
        # The two historical material *paths* were safely repurposed; reject
        # the actual placeholder mechanisms rather than their filenames.
        rejected = re.compile(r"(?i)lambert\d*|textures/default_(?:col|normal)")
        for filename in self.EXPECTED:
            with self.subTest(unit=filename):
                source = without_comments((ROCKET_UNIT_DIR / filename).read_text(encoding="utf-8"))
                self.assertIsNone(rejected.search(source))

    def test_projectile_unit_and_physics_keep_the_runtime_pRocket_contract(self) -> None:
        unit = without_comments((ROCKET_UNIT_DIR / "SM_Rocket.unit").read_text(encoding="utf-8"))
        physics = without_comments((ROCKET_UNIT_DIR / "SM_Rocket.physics").read_text(encoding="utf-8"))
        self.assertIn('unit_template = "explosive_pickup_projectile_unit"', unit)
        self.assertEqual(set(re.findall(r'\b(?:node|shape)\s*=\s*"([^"]+)"', physics)), {"pRocket"})
        self.assertIn('name = "throw"', physics)
        self.assertIn('template = "projectile_physics"', physics)
        self.assertIn('template = "projectile"', physics)

    def test_launcher_physics_keeps_exact_final_mesh_node(self) -> None:
        physics = without_comments(
            (ROCKET_UNIT_DIR / "pRocketLauncher.physics").read_text(encoding="utf-8")
        )
        self.assertEqual(
            set(re.findall(r'\b(?:node|shape)\s*=\s*"([^"]+)"', physics)),
            {"pRocketLauncher"},
        )
        self.assertIn('name = "rp_dropped"', physics)
        self.assertIn('template = "pickup"', physics)

    def test_death_drop_actor_drives_every_launcher_renderable(self) -> None:
        inventory = without_comments((
            REPO_ROOT / "scripts" / "mods" / "doomrocket" / "breeds" /
            "skaven_doomrocket_inventory.lua"
        ).read_text(encoding="utf-8"))
        weapon_item = named_block(inventory, "rocket_glaive_1")
        self.assertRegex(named_block(weapon_item, "drop_reasons"), r"\bdeath\s*=\s*true\b")

        physics = without_comments(
            (ROCKET_UNIT_DIR / "pRocketLauncher.physics").read_text(encoding="utf-8")
        )
        actor_matches = [
            block for block in anonymous_blocks(named_array(physics, "actors"))
            if re.search(r'\bname\s*=\s*"rp_dropped"', block)
        ]
        self.assertEqual(len(actor_matches), 1)
        actor_nodes = re.findall(r'\bnode\s*=\s*"([^"]+)"', actor_matches[0])
        self.assertEqual(actor_nodes, ["pRocketLauncher"])

        unit = without_comments(
            (ROCKET_UNIT_DIR / "pRocketLauncher.unit").read_text(encoding="utf-8")
        )
        renderables = set(re.findall(
            r"(?m)^\s*(\w+)\s*=\s*\{", named_block(unit, "renderables")
        ))
        self.assertEqual(renderables, {"pRocketLauncher", "pRocket"})
        launcher_fbx = BinaryFbx(ROCKET_UNIT_DIR / "pRocketLauncher.fbx")
        require_loaded_rocket_actor_hierarchy(launcher_fbx)
        parents = model_parent_ids(launcher_fbx)
        actor = model_node(launcher_fbx, actor_nodes[0], "Mesh")
        for renderable in renderables:
            node = model_node(launcher_fbx, renderable, "Mesh")
            current = node.properties[0]
            visited: set[int] = set()
            while current != actor.properties[0] and current not in visited:
                visited.add(current)
                current = parents.get(current, -1)
            self.assertEqual(
                current, actor.properties[0],
                f"{renderable} does not inherit the only death-drop actor",
            )

    def test_behavior_and_network_paths_stay_on_stable_units(self) -> None:
        inventory = (
            REPO_ROOT / "scripts" / "mods" / "doomrocket" / "breeds" / "skaven_doomrocket_inventory.lua"
        ).read_text(encoding="utf-8")
        launch = (
            REPO_ROOT / "scripts" / "mods" / "doomrocket" / "behavior" / "nodes" /
            "skaven_doomrocket" / "bt_doomrocket_launch_action.lua"
        ).read_text(encoding="utf-8")
        bootstrap = (
            REPO_ROOT / "scripts" / "mods" / "doomrocket" / "doomrocket.lua"
        ).read_text(encoding="utf-8")
        self.assertIn('unit_name = "units/rocket/pRocketLauncher"', inventory)
        self.assertIn('local unit_name = "units/rocket/SM_Rocket"', launch)
        self.assertIn('"units/rocket/SM_Rocket"', bootstrap)


@unittest.skipUnless(BUNDLE_ROOT.is_dir(), "compiled bundleV2 is not present")
class CrunchWeaponCompiledBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.resources = compiled_bundle_resources()

    def require_one(self, resource_type: str, resource_name: str) -> bytes:
        hits = self.resources.get(resource_key(resource_type, resource_name), [])
        self.assertEqual(
            len(hits),
            1,
            f"compiled {resource_type} {resource_name} must occur exactly once",
        )
        payload = hits[0][1]
        self.assertGreater(len(payload), 0)
        return payload

    def test_all_final_weapon_resources_are_compiled_exactly_once(self) -> None:
        expected = [
            ("unit", "units/rocket/pRocketLauncher"),
            ("unit", "units/rocket/SM_Rocket"),
            ("material", "materials/rocket/rocket_neutral"),
            ("material", "materials/rocket/rocket_red"),
        ]
        for target in ("weapon", "rocket"):
            for suffix in ("df", "nm", "e", "r", "m", "ao"):
                expected.append(("texture", f"textures/rocket/wb_{target}_{suffix}"))
        for resource_type, resource_name in expected:
            with self.subTest(type=resource_type, name=resource_name):
                self.require_one(resource_type, resource_name)

    def test_compiled_unit_material_tables_match_final_mesh_slots(self) -> None:
        launcher = self.require_one("unit", "units/rocket/pRocketLauncher")
        projectile = self.require_one("unit", "units/rocket/SM_Rocket")
        weapon_pair = (
            murmur64a(b"DoomRocket_Weapon") >> 32,
            murmur64a(b"materials/rocket/rocket_neutral"),
        )
        rocket_pair = (
            murmur64a(b"DoomRocket_Rocket") >> 32,
            murmur64a(b"materials/rocket/rocket_red"),
        )
        self.assertEqual(compiled_material_pairs(launcher), {weapon_pair, rocket_pair})
        self.assertEqual(compiled_material_pairs(projectile), {rocket_pair})

        for payload in (launcher, projectile):
            for old_slot in ("lambert2", "lambert3", "lambert4"):
                old_short = murmur64a(old_slot.encode()) >> 32
                self.assertNotIn(struct.pack("<I", old_short), payload)

    def test_compiled_loaded_warhead_inherits_rp_dropped_actor(self) -> None:
        launcher = self.require_one("unit", "units/rocket/pRocketLauncher")
        structure = compiled_unit_structure(launcher)
        launcher_node = compiled_node_index(structure, "pRocketLauncher")
        rocket_node = compiled_node_index(structure, "pRocket")
        self.assertEqual(
            structure.nodes[rocket_node].parent_index,
            launcher_node,
            "compiled loaded pRocket must be a direct child of pRocketLauncher",
        )
        self.assertEqual(structure.nodes[rocket_node].parent_type, 1)
        self.assertEqual(set(structure.mesh_node_indices), {launcher_node, rocket_node})
        rp_dropped = [
            node_hash for name_hash, node_hash in structure.actors
            if name_hash == idstring32("rp_dropped")
        ]
        self.assertEqual(rp_dropped, [idstring32("pRocketLauncher")])
        for renderable_node in structure.mesh_node_indices:
            self.assertTrue(node_inherits(structure.nodes, renderable_node, launcher_node))


if __name__ == "__main__":
    unittest.main(verbosity=2)
