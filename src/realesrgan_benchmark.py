from __future__ import annotations

import argparse
import base64
import json
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


@dataclass(frozen=True)
class ModelConfig:
    key: str
    label: str
    scale: int
    weight_path: str
    num_in_ch: int = 3
    num_out_ch: int = 3
    num_feat: int = 64
    num_block: int = 23
    num_grow_ch: int = 32


MODEL_CONFIGS: dict[str, ModelConfig] = {
    "x4plus": ModelConfig(
        key="x4plus",
        label="RealESRGAN_x4plus",
        scale=4,
        weight_path="models/RealESRGAN/RealESRGAN_x4plus.pth",
    ),
    "x2plus": ModelConfig(
        key="x2plus",
        label="RealESRGAN_x2plus",
        scale=2,
        weight_path="models/RealESRGAN/RealESRGAN_x2plus.pth",
        num_block=23,
    ),
    "anime6b": ModelConfig(
        key="anime6b",
        label="RealESRGAN_x4plus_anime_6B",
        scale=4,
        weight_path="models/RealESRGAN/RealESRGAN_x4plus_anime_6B.pth",
        num_block=6,
    ),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def path_or_str(path: Path, start: Path) -> str:
    try:
        return str(path.relative_to(start))
    except ValueError:
        return str(path)


def default_input_dir() -> Path:
    return repo_root() / "datasets" / "input"


def default_output_dir() -> Path:
    return repo_root() / "output" / "realesrgan"


def read_binary_data_url(path: Path) -> str:
    mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
    }.get(path.suffix.lower(), "application/octet-stream")
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def collect_images(input_dir: Path, limit: int) -> list[Path]:
    images = [
        path
        for path in sorted(input_dir.rglob("*"))
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return images[:limit] if limit > 0 else images


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_manifest_template(template_path: Path) -> str:
    return template_path.read_text(encoding="utf-8")


def render_preview_html(template_text: str, preview_data: dict[str, Any]) -> str:
    payload = json.dumps(preview_data, ensure_ascii=False).replace("</", "<\\/")
    return template_text.replace("__PREVIEW_DATA__", payload)


def run_benchmark(args: argparse.Namespace) -> int:
    try:
        import cv2
        import torch
        from basicsr.archs.rrdbnet_arch import RRDBNet
        from realesrgan import RealESRGANer
    except Exception as exc:  # pragma: no cover - import guard
        print(
            "Missing dependencies. Install requirements first, then rerun.\n"
            f"Import error: {exc}",
            file=sys.stderr,
        )
        return 2

    project_root = repo_root()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    run_name = time.strftime("%Y%m%d-%H%M%S")
    run_dir = output_dir / run_name
    outputs_dir = run_dir / "outputs"
    ensure_parent(outputs_dir / "dummy.txt")
    outputs_dir.mkdir(parents=True, exist_ok=True)

    model = MODEL_CONFIGS[args.model]
    weight_path = (project_root / model.weight_path).resolve()
    if not weight_path.exists():
        print(f"Model weight not found: {weight_path}", file=sys.stderr)
        return 1

    if not input_dir.exists():
        print(f"Input directory not found: {input_dir}", file=sys.stderr)
        return 1

    image_paths = collect_images(input_dir, args.limit)
    if not image_paths:
        print(
            f"No supported images found in {input_dir}. "
            "Add jpg/png/webp/bmp/tif files and rerun.",
            file=sys.stderr,
        )
        return 1

    if args.device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device
    use_half = device.startswith("cuda") and not args.no_half

    if device.startswith("cuda") and not torch.cuda.is_available():
        print("CUDA was requested but is not available. Falling back to CPU.", file=sys.stderr)
        device = "cpu"
        use_half = False

    net = RRDBNet(
        num_in_ch=model.num_in_ch,
        num_out_ch=model.num_out_ch,
        num_feat=model.num_feat,
        num_block=model.num_block,
        num_grow_ch=model.num_grow_ch,
        scale=model.scale,
    )

    upsampler = RealESRGANer(
        scale=model.scale,
        model_path=str(weight_path),
        model=net,
        tile=args.tile,
        tile_pad=args.tile_pad,
        pre_pad=args.pre_pad,
        half=use_half,
        device=device,
    )

    if device.startswith("cuda"):
        torch.cuda.reset_peak_memory_stats()

    entries: list[dict[str, Any]] = []
    timings_ms: list[float] = []

    for index, image_path in enumerate(image_paths, start=1):
        img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if img is None:
            print(f"Skipping unreadable image: {image_path}", file=sys.stderr)
            continue

        if device.startswith("cuda"):
            torch.cuda.synchronize()
        start = time.perf_counter()
        output, _ = upsampler.enhance(img, outscale=args.outscale or model.scale)
        if device.startswith("cuda"):
            torch.cuda.synchronize()
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        timings_ms.append(elapsed_ms)

        output_name = f"{image_path.stem}_{model.key}_x{args.outscale or model.scale}.png"
        output_path = outputs_dir / output_name
        cv2.imwrite(str(output_path), output)

        before_h, before_w = img.shape[:2]
        after_h, after_w = output.shape[:2]

        entry = {
            "index": index,
            "name": image_path.name,
            "input_path": path_or_str(image_path, project_root),
            "output_path": path_or_str(output_path, project_root),
            "input_size": [before_w, before_h],
            "output_size": [after_w, after_h],
            "elapsed_ms": round(elapsed_ms, 3),
            "input_data_url": read_binary_data_url(image_path),
            "output_data_url": read_binary_data_url(output_path),
        }
        entries.append(entry)

    peak_vram_mb = None
    if device.startswith("cuda"):
        peak_vram_mb = round(torch.cuda.max_memory_reserved() / (1024 * 1024), 2)

    summary = {
        "project": "UpscaleImage",
        "model_key": model.key,
        "model_name": model.label,
        "weight_path": path_or_str(weight_path, project_root),
        "device": device,
        "half_precision": use_half,
        "tile": args.tile,
        "tile_pad": args.tile_pad,
        "pre_pad": args.pre_pad,
        "outscale": args.outscale or model.scale,
        "input_dir": str(input_dir),
        "output_dir": path_or_str(run_dir, project_root),
        "image_count": len(entries),
        "avg_ms": round(statistics.mean(timings_ms), 3) if timings_ms else None,
        "min_ms": round(min(timings_ms), 3) if timings_ms else None,
        "max_ms": round(max(timings_ms), 3) if timings_ms else None,
        "peak_vram_mb": peak_vram_mb,
    }

    manifest = {
        "summary": summary,
        "entries": entries,
    }

    manifest_path = run_dir / "manifest.json"
    preview_data_path = run_dir / "preview-data.json"
    preview_html_path = run_dir / "preview.html"
    template_path = repo_root() / "src" / "realesrgan_preview.html"

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    preview_data_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    template_text = load_manifest_template(template_path)
    preview_html = render_preview_html(template_text, manifest)
    preview_html_path.write_text(preview_html, encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\nManifest: {manifest_path}")
    print(f"Preview : {preview_html_path}")
    print(f"Data    : {preview_data_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark and preview Real-ESRGAN on a batch of images.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=default_input_dir(),
        help="Folder containing source images.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir(),
        help="Folder where benchmark outputs will be written.",
    )
    parser.add_argument(
        "--model",
        choices=sorted(MODEL_CONFIGS.keys()),
        default="x4plus",
        help="Real-ESRGAN preset to use.",
    )
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of images to process.")
    parser.add_argument("--tile", type=int, default=0, help="Tile size. Use 0 for full-frame inference.")
    parser.add_argument("--tile-pad", type=int, default=10, help="Tile padding used during inference.")
    parser.add_argument("--pre-pad", type=int, default=0, help="Pre padding before inference.")
    parser.add_argument(
        "--outscale",
        type=int,
        default=0,
        help="Final output scale. Defaults to the model scale.",
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default="auto",
        help="Device to use for inference.",
    )
    parser.add_argument(
        "--no-half",
        action="store_true",
        help="Disable half precision on CUDA.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return run_benchmark(args)


if __name__ == "__main__":
    raise SystemExit(main())
