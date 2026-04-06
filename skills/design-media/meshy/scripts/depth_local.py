#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["onnxruntime", "numpy", "Pillow", "requests"]
# ///
"""
Local Depth — free, offline depth estimation and mesh generation.

Uses ONNX depth models (Depth Anything V3, MiDaS, Depth Pro) to generate
depth maps and 3D meshes from images. No API key required. Runs on-device.

Ported from waydeeper (https://github.com/EdenQwQ/waydeeper) — MIT License.

Subcommands:
  depth     Generate depth map as grayscale PNG
  mesh      Generate PLY mesh from depth (simple projection, no inpainting)
  download  Download an ONNX depth model from HuggingFace
  models    List available and installed models

Usage:
  uv run depth_local.py depth ./photo.png --output ./output
  uv run depth_local.py mesh ./photo.png --output ./output --fov 60
  uv run depth_local.py download depth-anything-v3-base
  uv run depth_local.py models
"""

import argparse
import hashlib
import json
import math
import struct
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import requests
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from _provider_base import download_file, log_event

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROVIDER = "depth-local"
MODELS_DIR = Path.home() / ".local" / "share" / "depth-local" / "models"
CACHE_DIR = Path.home() / ".cache" / "depth-local"

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# ---------------------------------------------------------------------------
# Model registry (same as waydeeper)
# ---------------------------------------------------------------------------

MODELS: dict[str, dict[str, Any]] = {
    "depth-anything-v3-base": {
        "description": "Balanced quality and speed — good default (~100 MB)",
        "url": "https://huggingface.co/onnx-community/depth-anything-v3-base/resolve/main/onnx/model.onnx",
        "extra_files": [
            ("model.onnx_data", "https://huggingface.co/onnx-community/depth-anything-v3-base/resolve/main/onnx/model.onnx_data"),
        ],
        "layout": "directory",  # stored as models/depth-anything-v3-base/model.onnx
    },
    "midas-small": {
        "description": "Lightweight and fast, lower quality (~16 MB zip)",
        "url": "https://github.com/rocksdanister/lively-ml-models/releases/download/v1.0.0.0/midas_small.zip",
        "layout": "zip",  # extract model.onnx from zip
    },
    "depth-pro-q4": {
        "description": "Apple Depth Pro (4-bit quantized) — high quality, large, slow",
        "url": "https://huggingface.co/onnx-community/DepthPro-ONNX/resolve/main/onnx/model_q4.onnx",
        "layout": "file",  # stored as models/depth-pro-q4.onnx
    },
}

DEFAULT_MODEL = "depth-anything-v3-base"

# ---------------------------------------------------------------------------
# Model management
# ---------------------------------------------------------------------------

def get_model_path(name: str) -> Path:
    """Resolve a model name to its ONNX file path."""
    info = MODELS.get(name)
    if not info:
        # Try as a direct path
        p = Path(name)
        if p.exists():
            return p if p.is_file() else p / "model.onnx"
        raise FileNotFoundError(
            f"Unknown model '{name}'. Available: {', '.join(MODELS)}"
        )

    if info["layout"] == "directory":
        return MODELS_DIR / name / "model.onnx"
    elif info["layout"] == "zip":
        return MODELS_DIR / f"{name}.onnx"
    else:
        return MODELS_DIR / f"{name}.onnx"


def is_model_installed(name: str) -> bool:
    try:
        return get_model_path(name).exists()
    except FileNotFoundError:
        return False


def download_model(name: str, force: bool = False) -> Path:
    """Download an ONNX depth model from HuggingFace."""
    if name not in MODELS:
        print(f"Error: Unknown model '{name}'. Available: {', '.join(MODELS)}", file=sys.stderr)
        sys.exit(1)

    info = MODELS[name]
    target = get_model_path(name)

    if target.exists() and not force:
        print(f"  Model already installed: {target}")
        return target

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading {name}...")
    print(f"  {info['description']}")
    log_event({"action": "depth_download_start", "model": name})

    if info["layout"] == "directory":
        model_dir = MODELS_DIR / name
        model_dir.mkdir(parents=True, exist_ok=True)
        _download_with_progress(info["url"], model_dir / "model.onnx")
        for extra_name, extra_url in info.get("extra_files", []):
            _download_with_progress(extra_url, model_dir / extra_name)

    elif info["layout"] == "zip":
        import io
        import zipfile
        print("  Downloading zip...")
        resp = requests.get(info["url"], stream=True, timeout=300)
        resp.raise_for_status()
        data = io.BytesIO(resp.content)
        with zipfile.ZipFile(data) as zf:
            onnx_names = [n for n in zf.namelist() if n.endswith(".onnx")]
            if not onnx_names:
                raise RuntimeError("No .onnx file found in zip")
            with open(target, "wb") as f:
                f.write(zf.read(onnx_names[0]))
        print(f"  Extracted: {target.name}")

    else:
        _download_with_progress(info["url"], target)

    size_mb = target.stat().st_size / (1024 * 1024)
    print(f"  Installed: {target} ({size_mb:.1f} MB)")
    log_event({"action": "depth_download_complete", "model": name, "size_mb": round(size_mb, 1)})
    return target


def _download_with_progress(url: str, dest: Path) -> None:
    """Download a file with a simple progress indicator."""
    resp = requests.get(url, stream=True, timeout=300)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    downloaded = 0

    with open(dest, "wb") as f:
        for chunk in resp.iter_content(65536):
            f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                pct = downloaded * 100 // total
                mb = downloaded / (1024 * 1024)
                print(f"\r  {dest.name}: {mb:.1f} MB ({pct}%)", end="", flush=True)
    print()


# ---------------------------------------------------------------------------
# Depth estimation (ported from waydeeper src/depth_estimator.rs)
# ---------------------------------------------------------------------------

def estimate_depth(image_path: str, model_path: Path) -> tuple[np.ndarray, tuple[int, int]]:
    """
    Run ONNX depth estimation on an image.

    Returns (depth_map, (width, height)) where depth_map is a float32 array
    of shape [H, W] with values normalized to [0, 1]. Closer = higher value.
    """
    import onnxruntime as ort

    img = Image.open(image_path).convert("RGB")
    original_w, original_h = img.size

    session = ort.InferenceSession(str(model_path))
    input_info = session.get_inputs()[0]
    input_shape = list(input_info.shape)

    # Detect input layout and size (ported from waydeeper's Rust logic)
    channels_first = True
    input_h, input_w = 256, 256
    is_5d = False
    ndim = len(input_shape)

    if ndim >= 4:
        for i in range(ndim):
            dim_val = input_shape[i]
            if isinstance(dim_val, int) and dim_val == 3:
                if i == 1 and ndim == 4:
                    # [N, C, H, W]
                    channels_first = True
                    input_h = input_shape[2] if isinstance(input_shape[2], int) and input_shape[2] > 0 else 256
                    input_w = input_shape[3] if isinstance(input_shape[3], int) and input_shape[3] > 0 else 256
                elif i == 3 and ndim == 4:
                    # [N, H, W, C]
                    channels_first = False
                    input_h = input_shape[1] if isinstance(input_shape[1], int) and input_shape[1] > 0 else 256
                    input_w = input_shape[2] if isinstance(input_shape[2], int) and input_shape[2] > 0 else 256
                elif i == 2 and ndim >= 5:
                    # [N, V, C, H, W]
                    channels_first = True
                    input_h = input_shape[-2] if isinstance(input_shape[-2], int) and input_shape[-2] > 0 else 256
                    input_w = input_shape[-1] if isinstance(input_shape[-1], int) and input_shape[-1] > 0 else 256
                    is_5d = True
                break

    # Resize and normalize
    resized = img.resize((input_w, input_h), Image.LANCZOS)
    pixels = np.array(resized, dtype=np.float32) / 255.0  # [H, W, 3]
    normalized = (pixels - IMAGENET_MEAN) / IMAGENET_STD

    if channels_first:
        # [H, W, 3] → [3, H, W]
        tensor = normalized.transpose(2, 0, 1)
        if is_5d:
            tensor = tensor.reshape(1, 1, 3, input_h, input_w)
        else:
            tensor = tensor.reshape(1, 3, input_h, input_w)
    else:
        tensor = normalized.reshape(1, input_h, input_w, 3)

    tensor = tensor.astype(np.float32)

    # Inference
    input_name = input_info.name
    outputs = session.run(None, {input_name: tensor})
    output = outputs[0]

    # Extract spatial dimensions from output
    out_shape = output.shape
    out_h = out_shape[-2]
    out_w = out_shape[-1]
    depth_flat = output.reshape(-1)

    # Post-process: percentile normalization + inversion (from waydeeper)
    depth = _postprocess_depth(depth_flat, (out_w, out_h), (original_w, original_h))

    return depth, (original_w, original_h)


def _postprocess_depth(
    raw: np.ndarray,
    output_size: tuple[int, int],
    target_size: tuple[int, int],
) -> np.ndarray:
    """Normalize, invert, resize, and blur the raw depth output."""
    depth = raw.copy()

    # Percentile normalization (1st-99th)
    sorted_vals = np.sort(depth)
    low_idx = int(len(sorted_vals) * 0.01)
    high_idx = int(len(sorted_vals) * 0.99)
    low = sorted_vals[low_idx]
    high = sorted_vals[high_idx]
    rng = high - low + 1e-8
    depth = np.clip((depth - low) / rng, 0.0, 1.0)

    # Invert: closer objects = higher values
    depth = 1.0 - depth

    # Reshape to spatial dims
    out_w, out_h = output_size
    depth_2d = depth.reshape(out_h, out_w)

    # Convert to uint8 for resizing
    depth_u8 = (depth_2d * 255).astype(np.uint8)
    depth_img = Image.fromarray(depth_u8, mode="L")

    # Resize to original image dimensions
    target_w, target_h = target_size
    depth_img = depth_img.resize((target_w, target_h), Image.LANCZOS)

    # Light gaussian blur (sigma ~0.785, kernel 3x3)
    from PIL import ImageFilter
    depth_img = depth_img.filter(ImageFilter.GaussianBlur(radius=1))

    return np.array(depth_img, dtype=np.float32) / 255.0


# ---------------------------------------------------------------------------
# Depth map caching
# ---------------------------------------------------------------------------

def _cache_key(image_path: str, model_name: str) -> str:
    """Generate a cache key from image path + model name."""
    h = hashlib.blake2b(digest_size=16)
    h.update(Path(image_path).resolve().as_posix().encode())
    h.update(model_name.encode())
    # Include file modification time for cache invalidation
    try:
        mtime = str(Path(image_path).stat().st_mtime)
        h.update(mtime.encode())
    except OSError:
        pass
    return h.hexdigest()


def get_cached_depth(image_path: str, model_name: str) -> np.ndarray | None:
    """Load cached depth map if available."""
    key = _cache_key(image_path, model_name)
    cache_file = CACHE_DIR / "depth" / f"{key}.npy"
    if cache_file.exists():
        return np.load(cache_file)
    return None


def save_cached_depth(image_path: str, model_name: str, depth: np.ndarray) -> None:
    """Save depth map to cache."""
    key = _cache_key(image_path, model_name)
    cache_dir = CACHE_DIR / "depth"
    cache_dir.mkdir(parents=True, exist_ok=True)
    np.save(cache_dir / f"{key}.npy", depth)


# ---------------------------------------------------------------------------
# Depth map output
# ---------------------------------------------------------------------------

def save_depth_png(depth: np.ndarray, output_path: Path) -> None:
    """Save depth map as grayscale PNG."""
    depth_u8 = (depth * 255).astype(np.uint8)
    img = Image.fromarray(depth_u8, mode="L")
    img.save(output_path)


# ---------------------------------------------------------------------------
# Mesh generation (simple depth projection, no inpainting)
# ---------------------------------------------------------------------------

def depth_to_ply(
    image_path: str,
    depth: np.ndarray,
    output_path: Path,
    fov_y_deg: float = 60.0,
    depth_edge_threshold: float = 0.08,
) -> None:
    """
    Generate a PLY mesh by projecting image pixels to 3D using depth.

    Uses a pinhole camera model: each pixel (u, v) with depth d maps to
    3D point (x, y, z) where z = -d (OpenGL convention, camera at origin).

    Triangles spanning large depth discontinuities are skipped to avoid
    stretchy artifacts at object boundaries.
    """
    img = Image.open(image_path).convert("RGB")
    rgb = np.array(img)
    h, w = depth.shape

    # Compute focal length from FoV
    fov_y_rad = math.radians(fov_y_deg)
    focal = (h / 2.0) / math.tan(fov_y_rad / 2.0)
    cx, cy = w / 2.0, h / 2.0

    # Generate 3D vertices: [H, W, 3] for (x, y, z)
    uu, vv = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    z = -depth  # camera looks down -Z
    x = (uu - cx) / focal * depth
    y = -(vv - cy) / focal * depth  # flip Y (image row 0 = top = +Y)

    vertices = np.stack([x, y, z], axis=-1).reshape(-1, 3)  # [H*W, 3]
    colors = rgb.reshape(-1, 3)  # [H*W, 3]

    # Build triangle faces on a grid, skipping depth discontinuities
    # Each quad (r,c)-(r,c+1)-(r+1,c)-(r+1,c+1) → 2 triangles
    faces = []
    for r in range(h - 1):
        for c in range(w - 1):
            i00 = r * w + c
            i01 = r * w + c + 1
            i10 = (r + 1) * w + c
            i11 = (r + 1) * w + c + 1

            d00, d01, d10, d11 = depth[r, c], depth[r, c + 1], depth[r + 1, c], depth[r + 1, c + 1]

            # Skip faces where any edge spans a large depth jump
            max_d = max(d00, d01, d10, d11)
            min_d = min(d00, d01, d10, d11)
            if max_d - min_d > depth_edge_threshold:
                continue
            # Skip zero-depth vertices
            if min_d < 1e-4:
                continue

            faces.append((i00, i10, i01))
            faces.append((i01, i10, i11))

    # Write binary PLY
    n_verts = len(vertices)
    n_faces = len(faces)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        header = (
            f"ply\n"
            f"format binary_little_endian 1.0\n"
            f"comment fov_y_deg {fov_y_deg}\n"
            f"comment generated by depth_local.py (meshy skill)\n"
            f"element vertex {n_verts}\n"
            f"property float x\n"
            f"property float y\n"
            f"property float z\n"
            f"property uchar red\n"
            f"property uchar green\n"
            f"property uchar blue\n"
            f"element face {n_faces}\n"
            f"property list uchar int vertex_indices\n"
            f"end_header\n"
        )
        f.write(header.encode("ascii"))

        # Vertex data: x y z r g b
        for i in range(n_verts):
            vx, vy, vz = vertices[i]
            r, g, b = colors[i]
            f.write(struct.pack("<fffBBB", vx, vy, vz, r, g, b))

        # Face data: count i0 i1 i2
        for i0, i1, i2 in faces:
            f.write(struct.pack("<Biii", 3, i0, i1, i2))

    print(f"  PLY: {n_verts} vertices, {n_faces} faces")


def ply_to_glb(ply_path: Path, glb_path: Path) -> None:
    """Convert PLY to GLB using trimesh. Requires: pip install trimesh."""
    try:
        import trimesh
    except ImportError:
        print(
            "Error: trimesh not installed. Install with:\n"
            "  uv pip install trimesh\n"
            "Or use PLY output directly (--format ply).",
            file=sys.stderr,
        )
        sys.exit(1)

    mesh = trimesh.load(str(ply_path), process=False)
    mesh.export(str(glb_path), file_type="glb")
    print(f"  Converted: {glb_path}")


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_depth(args: argparse.Namespace) -> None:
    """Generate depth map as grayscale PNG."""
    model_name = args.model
    model_path = get_model_path(model_name)

    if not model_path.exists():
        print(f"  Model not installed. Downloading {model_name}...")
        download_model(model_name)

    # Check cache
    if not args.no_cache:
        cached = get_cached_depth(args.image, model_name)
        if cached is not None:
            print("  Using cached depth map")
            depth = cached
            original_size = (cached.shape[1], cached.shape[0])
        else:
            cached = None

    if args.no_cache or cached is None:
        t0 = time.time()
        print(f"  Model: {model_name}")
        print(f"  Image: {args.image}")
        depth, original_size = estimate_depth(args.image, model_path)
        elapsed = time.time() - t0
        print(f"  Inference: {elapsed:.2f}s")

        if not args.no_cache:
            save_cached_depth(args.image, model_name, depth)

    # Output
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.filename or Path(args.image).stem
    output_path = output_dir / f"{stem}_depth.png"
    save_depth_png(depth, output_path)

    log_event({"action": "depth_estimate", "model": model_name, "image": args.image})

    if args.json:
        print(json.dumps({"depth_map": str(output_path), "size": list(original_size)}))
    else:
        print(f"\n  Depth map: {output_path}")


def cmd_mesh(args: argparse.Namespace) -> None:
    """Generate PLY/GLB mesh from depth."""
    model_name = args.model
    model_path = get_model_path(model_name)

    if not model_path.exists():
        print(f"  Model not installed. Downloading {model_name}...")
        download_model(model_name)

    # Depth estimation (with cache)
    cached = None if args.no_cache else get_cached_depth(args.image, model_name)
    if cached is not None:
        print("  Using cached depth map")
        depth = cached
    else:
        t0 = time.time()
        print(f"  Model: {model_name}")
        print(f"  Image: {args.image}")
        depth, _ = estimate_depth(args.image, model_path)
        elapsed = time.time() - t0
        print(f"  Inference: {elapsed:.2f}s")
        if not args.no_cache:
            save_cached_depth(args.image, model_name, depth)

    # Mesh generation
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.filename or Path(args.image).stem

    fmt = args.format.lower()
    ply_path = output_dir / f"{stem}.ply"

    print("  Generating mesh...")
    t0 = time.time()
    depth_to_ply(args.image, depth, ply_path, fov_y_deg=args.fov, depth_edge_threshold=args.edge_threshold)
    elapsed = time.time() - t0
    print(f"  Mesh generation: {elapsed:.2f}s")

    log_event({"action": "depth_mesh", "model": model_name, "image": args.image, "format": fmt})

    if fmt == "glb":
        glb_path = output_dir / f"{stem}.glb"
        ply_to_glb(ply_path, glb_path)
        ply_path.unlink()  # remove intermediate PLY
        final_path = glb_path
    else:
        final_path = ply_path

    if args.json:
        print(json.dumps({"mesh": str(final_path)}))
    else:
        size_kb = final_path.stat().st_size / 1024
        print(f"\n  Mesh: {final_path} ({size_kb:.0f} KB)")


def cmd_download(args: argparse.Namespace) -> None:
    """Download an ONNX depth model."""
    name = args.model_name or DEFAULT_MODEL
    download_model(name, force=args.force)


def cmd_models(args: argparse.Namespace) -> None:
    """List available and installed models."""
    print("Available depth estimation models:")
    print("-" * 60)
    for name, info in MODELS.items():
        installed = " (installed)" if is_model_installed(name) else ""
        default = " [default]" if name == DEFAULT_MODEL else ""
        print(f"  {name}{default}{installed}")
        print(f"    {info['description']}")
    print("-" * 60)
    print(f"\nModels directory: {MODELS_DIR}")
    print(f"Cache directory:  {CACHE_DIR}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Local Depth — free, offline depth estimation and mesh generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- depth --
    p_depth = sub.add_parser("depth", help="Generate depth map as grayscale PNG")
    p_depth.add_argument("image", help="Input image path")
    p_depth.add_argument("--model", default=DEFAULT_MODEL, help=f"Depth model (default: {DEFAULT_MODEL})")
    p_depth.add_argument("--output", default="./output", help="Output directory")
    p_depth.add_argument("--filename", default="", help="Output filename stem (default: input name)")
    p_depth.add_argument("--no-cache", action="store_true", help="Skip depth cache")
    p_depth.add_argument("--json", action="store_true", help="JSON output")

    # -- mesh --
    p_mesh = sub.add_parser("mesh", help="Generate PLY/GLB mesh from depth")
    p_mesh.add_argument("image", help="Input image path")
    p_mesh.add_argument("--model", default=DEFAULT_MODEL, help=f"Depth model (default: {DEFAULT_MODEL})")
    p_mesh.add_argument("--output", default="./output", help="Output directory")
    p_mesh.add_argument("--filename", default="", help="Output filename stem")
    p_mesh.add_argument("--format", default="ply", choices=["ply", "glb"], help="Output format (default: ply)")
    p_mesh.add_argument("--fov", type=float, default=60.0, help="Vertical FoV in degrees (default: 60)")
    p_mesh.add_argument("--edge-threshold", type=float, default=0.08, help="Depth discontinuity threshold for face culling")
    p_mesh.add_argument("--no-cache", action="store_true", help="Skip depth cache")
    p_mesh.add_argument("--json", action="store_true", help="JSON output")

    # -- download --
    p_dl = sub.add_parser("download", help="Download an ONNX depth model")
    p_dl.add_argument("model_name", nargs="?", default=None, help=f"Model name (default: {DEFAULT_MODEL})")
    p_dl.add_argument("--force", action="store_true", help="Re-download even if installed")

    # -- models --
    sub.add_parser("models", help="List available and installed models")

    args = parser.parse_args()

    if args.command == "depth":
        cmd_depth(args)
    elif args.command == "mesh":
        cmd_mesh(args)
    elif args.command == "download":
        cmd_download(args)
    elif args.command == "models":
        cmd_models(args)


if __name__ == "__main__":
    main()
