from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from PIL import Image


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def path_or_str(path: Path, start: Path) -> str:
    try:
        return str(path.relative_to(start))
    except ValueError:
        return str(path)


def file_uri(path: Path) -> str:
    return path.resolve().as_uri()


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def render(template_text: str, payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return template_text.replace("__PAGE_DATA__", encoded).replace("__PREVIEW_DATA__", encoded)


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")
    return cleaned or "image"


def read_image_size(path: Path) -> list[int] | None:
    try:
        with Image.open(path) as img:
            return [int(img.width), int(img.height)]
    except Exception:
        return None


def resolve_source_image(input_dir: Path, entry: dict[str, Any]) -> Path | None:
    candidates: list[Path] = []

    stored = entry.get("input_path")
    if stored:
        stored_path = Path(stored)
        stored_abs = (repo_root() / stored_path).resolve() if not stored_path.is_absolute() else stored_path
        candidates.append(stored_abs)

    base_name = Path(entry.get("name", "")).stem
    if base_name:
        for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"]:
            candidates.append(input_dir / f"{base_name}{ext}")

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return None


def load_existing_manifest(run_dir: Path) -> dict[str, Any]:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"Manifest not found: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def build_index_html(summary: dict[str, Any], entries: list[dict[str, Any]]) -> str:
    cards = []
    for entry in entries:
        page_name = entry["page_name"]
        elapsed_text = f'{entry["elapsed_ms"]:.2f} ms' if entry.get("elapsed_ms") is not None else "n/a"
        input_size = entry.get("input_size")
        output_size = entry.get("output_size")
        input_size_text = f"{input_size[0]} x {input_size[1]}" if input_size else "n/a"
        output_size_text = f"{output_size[0]} x {output_size[1]}" if output_size else "n/a"
        input_name = entry.get("input_name") or entry.get("name") or "n/a"
        cards.append(
            f"""
            <a class="card" href="{page_name}">
              <div class="card-head">
                <div>
                  <div class="title">{entry["index"]}. {input_name}</div>
                  <div class="meta">{entry["input_path"]}</div>
                </div>
                <div class="badge">{elapsed_text}</div>
              </div>
              <div class="row">
                <span>Original</span>
                <span>{input_size_text}</span>
              </div>
              <div class="row">
                <span>Upscaled</span>
                <span>{output_size_text}</span>
              </div>
            </a>
            """
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Real-ESRGAN Index</title>
  <style>
    body {{
      margin: 0;
      font-family: "Segoe UI", "Aptos", sans-serif;
      background: #07101f;
      color: #eef2ff;
    }}
    .shell {{ width: min(1320px, calc(100vw - 28px)); margin: 0 auto; padding: 20px 0 32px; }}
    .hero, .card {{
      background: rgba(17, 24, 45, 0.92);
      border: 1px solid rgba(145, 167, 255, 0.18);
      border-radius: 18px;
      box-shadow: 0 24px 90px rgba(0,0,0,.35);
    }}
    .hero {{ padding: 20px 22px; margin-bottom: 16px; }}
    h1 {{ margin: 0 0 8px; font-size: clamp(28px, 4vw, 46px); }}
    .muted {{ color: #a8b3d7; line-height: 1.55; }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }}
    .stat {{ padding: 14px; background: rgba(25,34,61,.9); border-radius: 16px; border: 1px solid rgba(145,167,255,.16); }}
    .stat .label {{ font-size: 12px; text-transform: uppercase; letter-spacing: .12em; color: #a8b3d7; margin-bottom: 6px; }}
    .stat .value {{ font-size: 20px; font-weight: 800; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }}
    a.card {{ color: inherit; text-decoration: none; padding: 14px; }}
    .card-head {{ display: flex; justify-content: space-between; gap: 10px; margin-bottom: 10px; }}
    .title {{ font-weight: 800; line-height: 1.3; }}
    .meta {{ color: #a8b3d7; font-size: 13px; margin-top: 4px; word-break: break-all; }}
    .badge {{ padding: 6px 10px; border-radius: 999px; background: rgba(104,214,255,.14); color: #68d6ff; font-size: 12px; font-weight: 800; white-space: nowrap; height: fit-content; }}
    .row {{ display: flex; justify-content: space-between; gap: 10px; margin-top: 8px; color: #a8b3d7; font-size: 13px; }}
    @media (max-width: 980px) {{ .summary {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
    @media (max-width: 640px) {{ .summary {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <h1>Real-ESRGAN previews</h1>
      <p class="muted">
        Click any image card below to open a dedicated page where the original is on the left,
        the upscaled result is on the right, and benchmark info is shown for that specific image.
      </p>
    </section>

    <section class="summary">
      <div class="stat"><div class="label">Images</div><div class="value">{summary.get("image_count", 0)}</div></div>
      <div class="stat"><div class="label">Model</div><div class="value">{summary.get("model_name", "-")}</div></div>
      <div class="stat"><div class="label">Device</div><div class="value">{summary.get("device", "-")}</div></div>
      <div class="stat"><div class="label">Peak VRAM</div><div class="value">{summary.get("peak_vram_mb", "n/a")} MB</div></div>
    </section>

    <section class="grid">
      {''.join(cards)}
    </section>
  </main>
</body>
</html>
"""


def build_page_html(payload: dict[str, Any]) -> str:
    template = load_text(repo_root() / "src" / "realesrgan_single_image_preview.html")
    return render(template, payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild lightweight Real-ESRGAN previews for an existing run.")
    parser.add_argument("--run-dir", type=Path, required=True, help="Run folder under output/realesrgan/<timestamp>.")
    parser.add_argument("--input-dir", type=Path, default=repo_root() / "datasets" / "inputs", help="Original input image folder.")
    parser.add_argument("--model-key", type=str, default="x4plus", help="Model key used in output filenames.")
    parser.add_argument("--outscale", type=int, default=4, help="Output scale used in output filenames.")
    args = parser.parse_args()

    run_dir = args.run_dir.resolve()
    input_dir = args.input_dir.resolve()
    if not run_dir.exists():
        raise SystemExit(f"Run dir not found: {run_dir}")

    manifest_data = load_existing_manifest(run_dir)
    entries = list(manifest_data.get("entries", []))
    summary = dict(manifest_data.get("summary", {}))
    for entry in entries:
        input_abs = resolve_source_image(input_dir, entry)
        output_path = Path(entry["output_path"])
        output_abs = (repo_root() / output_path).resolve() if not output_path.is_absolute() else output_path
        if input_abs is not None:
            entry["name"] = input_abs.name
            entry["input_name"] = input_abs.name
            entry["input_path"] = path_or_str(input_abs, repo_root())
            entry["input_url"] = file_uri(input_abs)
            entry["input_size"] = entry.get("input_size") or read_image_size(input_abs)
        else:
            entry["input_name"] = entry.get("name")
            entry["input_url"] = ""
            entry["input_size"] = entry.get("input_size")
        entry["output_url"] = file_uri(output_abs)
        entry["output_size"] = entry.get("output_size") or read_image_size(output_abs)
    summary.update(
        {
            "input_dir": str(input_dir),
            "output_dir": path_or_str(run_dir, repo_root()),
            "image_count": len(entries),
            "outscale": args.outscale,
        }
    )
    summary.setdefault("model_key", args.model_key)
    summary.setdefault("model_name", f"RealESRGAN_{args.model_key}")
    manifest = {"summary": summary, "entries": entries}

    manifest_path = run_dir / "manifest.json"
    preview_data_path = run_dir / "preview-data.json"
    preview_index_path = run_dir / "preview.html"
    pages_dir = run_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    for stale_page in pages_dir.glob("*.html"):
        stale_page.unlink()

    for entry in entries:
        page_slug = f"image-{entry['index']:02d}-{slugify(entry.get('input_name') or entry['name'])}.html"
        entry["page_name"] = f"pages/{page_slug}"
        page_payload = {"summary": summary, "entry": entry}
        page_html = build_page_html(page_payload)
        write_text(pages_dir / page_slug, page_html)

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    preview_data_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    write_text(preview_index_path, build_index_html(summary, entries))

    print(f"Rebuilt: {manifest_path}")
    print(f"Rebuilt: {preview_index_path}")
    print(f"Rebuilt: {preview_data_path}")
    print(f"Rebuilt pages: {pages_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
