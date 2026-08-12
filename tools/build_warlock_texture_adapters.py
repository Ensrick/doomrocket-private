#!/usr/bin/env python3
"""Build VT2-native Warlock texture inputs from Crunch's authored masters.

The source material uses BC, NR, MASE_Fix, and a separate emissive image.
VT2's selected skinned Ratling parent consumes three textures:

* base color (BC);
* tangent normal with roughness in alpha (NR);
* packed metallic/AO/feature/emission-mask data.

MASE_Fix contains the artist's final RGB response but, as an RGB PNG, has no
emission alpha. The original MASE alpha is the spatial mask from which the
separate emissive texture was authored. The adapter therefore combines
``MASE_Fix.rgb + MASE.a`` without resampling or flipping any channel.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from PIL import Image


SETS = {
    "armor": ("01", "2048"),
    "backpack": ("02", "2048"),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def open_rgba(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return image.convert("RGBA")


def require_mode(path: Path, expected: str) -> None:
    with Image.open(path) as image:
        if image.mode != expected:
            raise ValueError(
                f"{path.name}: expected source mode {expected}, got {image.mode}"
            )


def save_rgba(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=False, compress_level=9)


def build(source_root: Path, output_root: Path) -> None:
    for target, (index, resolution) in SETS.items():
        source_dir = source_root / resolution
        prefix = f"T_Skaven_WarlockBombardier_"
        bc_path = source_dir / f"{prefix}BC_{index}.png"
        nr_path = source_dir / f"{prefix}NR_{index}.png"
        mase_path = source_dir / f"{prefix}MASE_{index}.png"
        mase_fix_path = source_dir / f"{prefix}MASE_{index}_Fix.png"
        require_mode(bc_path, "RGBA")
        require_mode(nr_path, "RGBA")
        require_mode(mase_path, "RGBA")
        require_mode(mase_fix_path, "RGB")
        bc = open_rgba(bc_path)
        nr = open_rgba(nr_path)
        mase = open_rgba(mase_path)
        mase_fix = open_rgba(mase_fix_path)

        sizes = {bc.size, nr.size, mase.size, mase_fix.size}
        if len(sizes) != 1:
            raise ValueError(f"{target}: source image sizes differ: {sorted(sizes)}")

        mask = Image.merge(
            "RGBA",
            (
                mase_fix.getchannel("R"),
                mase_fix.getchannel("G"),
                mase_fix.getchannel("B"),
                mase.getchannel("A"),
            ),
        )

        if target == "armor" and mask.getchannel("A").getextrema() != (0, 0):
            raise ValueError("armor: expected a zero emission mask")
        if target == "backpack":
            alpha_min, alpha_max = mask.getchannel("A").getextrema()
            if alpha_min != 0 or alpha_max <= 0:
                raise ValueError(
                    "backpack: localized emission alpha must contain zero and "
                    "non-zero pixels"
                )
        save_rgba(bc, output_root / f"wb_{target}_df.png")
        save_rgba(nr, output_root / f"wb_{target}_nm.png")
        save_rgba(mask, output_root / f"wb_{target}_ma.png")

    for name in SETS:
        for suffix in ("df", "nm", "ma"):
            path = output_root / f"wb_{name}_{suffix}.png"
            print(f"[texture-adapter] {path.name} sha256={digest(path)}")


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root",
        type=Path,
        default=repo_root.parent / "_warlock_bombardier_art" / "crunch_textures",
        help="directory containing the 2048/1024/512 source folders",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=repo_root / "textures" / "warlock_bombardier",
    )
    args = parser.parse_args()
    build(args.source_root.resolve(), args.output_root.resolve())


if __name__ == "__main__":
    main()
