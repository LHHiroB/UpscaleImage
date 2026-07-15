from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import cv2
import torch
import torchvision.transforms.functional as TF
from spandrel import ModelLoader, ImageModelDescriptor

import math

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]

def path_or_str(path: Path, start: Path) -> str:
    try:
        return str(path.relative_to(start))
    except ValueError:
        return str(path)

def file_uri(path: Path) -> str:
    return path.resolve().as_uri()

def collect_images(input_dir: Path, limit: int) -> list[Path]:
    images = [
        path for path in sorted(input_dir.rglob("*"))
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return images[:limit] if limit > 0 else images

def load_manifest_template(template_path: Path) -> str:
    return template_path.read_text(encoding="utf-8")

def render_preview_html(template_text: str, preview_data: dict[str, Any]) -> str:
    payload = json.dumps(preview_data, ensure_ascii=False).replace("</", "<\\/")
    return template_text.replace("__PREVIEW_DATA__", payload)

def tile_process(img_tensor: torch.Tensor, model, tile_size: int, tile_pad: int, scale: int) -> torch.Tensor:
    batch, channel, height, width = img_tensor.shape
    output_height = height * scale
    output_width = width * scale
    output_tensor = torch.zeros((batch, channel, output_height, output_width), device=img_tensor.device, dtype=img_tensor.dtype)
    
    tiles_x = math.ceil(width / tile_size)
    tiles_y = math.ceil(height / tile_size)
    
    for y in range(tiles_y):
        for x in range(tiles_x):
            ofs_x = x * tile_size
            ofs_y = y * tile_size
            
            input_start_x = max(0, ofs_x - tile_pad)
            input_start_y = max(0, ofs_y - tile_pad)
            input_end_x = min(width, ofs_x + tile_size + tile_pad)
            input_end_y = min(height, ofs_y + tile_size + tile_pad)
            
            input_tile = img_tensor[:, :, input_start_y:input_end_y, input_start_x:input_end_x]
            
            with torch.no_grad():
                output_tile = model(input_tile)
                
            output_start_x = ofs_x * scale
            output_start_y = ofs_y * scale
            output_end_x = min(output_width, (ofs_x + tile_size) * scale)
            output_end_y = min(output_height, (ofs_y + tile_size) * scale)
            
            tile_start_x = (ofs_x - input_start_x) * scale
            tile_start_y = (ofs_y - input_start_y) * scale
            tile_end_x = tile_start_x + (output_end_x - output_start_x)
            tile_end_y = tile_start_y + (output_end_y - output_start_y)
            
            output_tensor[:, :, output_start_y:output_end_y, output_start_x:output_end_x] = \
                output_tile[:, :, tile_start_y:tile_end_y, tile_start_x:tile_end_x]
                
    return output_tensor

def run_benchmark(args: argparse.Namespace) -> int:
    project_root = repo_root()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    weight_path = args.model_path.resolve()
    
    if not weight_path.exists():
        print(f"Model weight not found: {weight_path}", file=sys.stderr)
        return 1

    if not input_dir.exists():
        print(f"Input directory not found: {input_dir}", file=sys.stderr)
        return 1
        
    image_paths = collect_images(input_dir, args.limit)
    if not image_paths:
        print(f"No supported images found in {input_dir}.", file=sys.stderr)
        return 1

    device_name = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device_name)
    use_half = (device_name == "cuda" and not args.no_half)

    print(f"Loading model with Spandrel: {weight_path.name} on {device_name} (Autocast: {use_half})")
    model = ModelLoader().load_from_file(str(weight_path))
    if not isinstance(model, ImageModelDescriptor):
         print("Error: loaded model is not an ImageModelDescriptor", file=sys.stderr)
         return 1
         
    model.eval().to(device)
    scale = model.scale

    run_name = time.strftime("%Y%m%d-%H%M%S") + f"_{weight_path.stem}"
    run_dir = output_dir / run_name
    outputs_dir = run_dir / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    if device_name == "cuda":
        torch.cuda.reset_peak_memory_stats()

    entries: list[dict[str, Any]] = []
    timings_ms: list[float] = []

    for index, image_path in enumerate(image_paths, start=1):
        img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if img is None:
            continue
            
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        input_tensor = TF.to_tensor(img).unsqueeze(0).to(device)

        if device_name == "cuda":
            torch.cuda.synchronize()
        start = time.perf_counter()
        
        with torch.no_grad():
            if use_half:
                with torch.autocast(device_type="cuda", dtype=torch.float16):
                    if args.tile > 0:
                        output_tensor = tile_process(input_tensor, model, args.tile, args.tile_pad, scale)
                    else:
                        output_tensor = model(input_tensor)
            else:
                if args.tile > 0:
                    output_tensor = tile_process(input_tensor, model, args.tile, args.tile_pad, scale)
                else:
                    output_tensor = model(input_tensor)
            
        if device_name == "cuda":
            torch.cuda.synchronize()
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        timings_ms.append(elapsed_ms)

        output_tensor = output_tensor.squeeze(0).clamp(0, 1).float()
        output_img = TF.to_pil_image(output_tensor)
        
        # fix the deprecation warning by directly converting PIL to BGR array
        import numpy as np
        output_img_bgr = cv2.cvtColor(np.array(output_img), cv2.COLOR_RGB2BGR)

        output_name = f"{image_path.stem}_out.png"
        output_path = outputs_dir / output_name
        cv2.imwrite(str(output_path), output_img_bgr)

        before_h, before_w = img.shape[:2]
        after_w, after_h = output_img.size

        entry = {
            "index": index,
            "name": image_path.name,
            "input_path": path_or_str(image_path, project_root),
            "output_path": path_or_str(output_path, project_root),
            "input_url": file_uri(image_path),
            "output_url": file_uri(output_path),
            "input_size": [before_w, before_h],
            "output_size": [after_w, after_h],
            "elapsed_ms": round(elapsed_ms, 3),
        }
        entries.append(entry)

    peak_vram_mb = None
    if device_name == "cuda":
        peak_vram_mb = round(torch.cuda.max_memory_reserved() / (1024 * 1024), 2)

    summary = {
        "project": "UpscaleImage",
        "model_key": weight_path.stem,
        "weight_path": path_or_str(weight_path, project_root),
        "device": device_name,
        "input_dir": str(input_dir),
        "output_dir": path_or_str(run_dir, project_root),
        "image_count": len(entries),
        "avg_ms": round(statistics.mean(timings_ms), 3) if timings_ms else None,
        "peak_vram_mb": peak_vram_mb,
    }

    manifest = {"summary": summary, "entries": entries}

    manifest_path = run_dir / "manifest.json"
    preview_data_path = run_dir / "preview-data.json"
    preview_html_path = run_dir / "preview.html"
    template_path = repo_root() / "src" / "realesrgan_preview.html"

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    preview_data_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    if template_path.exists():
        template_text = load_manifest_template(template_path)
        preview_html = render_preview_html(template_text, manifest)
        preview_html_path.write_text(preview_html, encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=repo_root() / "datasets" / "inputs")
    parser.add_argument("--output-dir", type=Path, default=repo_root() / "output" / "unified")
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--tile", type=int, default=256, help="Tile size, 0 for no tile")
    parser.add_argument("--tile-pad", type=int, default=10, help="Tile padding")
    parser.add_argument("--no-half", action="store_true", help="Disable autocast FP16")
    args = parser.parse_args()
    sys.exit(run_benchmark(args))
