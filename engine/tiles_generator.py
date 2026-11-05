"""Quantized Mesh / 3D tile header generator for WebGPU terrain viewports."""
from __future__ import annotations

import os
import struct


def generate_quantized_mesh_tile(
    tile_x: int,
    tile_y: int,
    zoom: int,
    min_height: float,
    max_height: float,
) -> bytes:
    """Binary Quantized Mesh header (empty vertex payload)."""
    center_x = 0.0
    center_y = 0.0
    center_z = (min_height + max_height) / 2.0
    radius = 1000.0

    header = struct.pack(
        "<dddffdddd",
        center_x,
        center_y,
        center_z,
        min_height,
        max_height,
        center_x,
        center_y,
        center_z,
        radius,
    )
    vertex_count = struct.pack("<I", 0)
    return header + vertex_count


if __name__ == "__main__":
    tile_bytes = generate_quantized_mesh_tile(
        tile_x=1024, tile_y=2048, zoom=12, min_height=320.0, max_height=385.0
    )
    out_dir = "dist/tiles/12/1024"
    os.makedirs(out_dir, exist_ok=True)
    out_path = f"{out_dir}/2048.terrain"
    with open(out_path, "wb") as f:
        f.write(tile_bytes)
    print(f"Exported Quantized Mesh tile: {out_path}")
