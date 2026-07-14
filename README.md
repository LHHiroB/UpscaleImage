# UpscaleImage

Research and benchmark project for offline AI image upscaling on Windows/Python.

## Current Focus

- Real-ESRGAN benchmark first
- Batch upscaling for up to 20 images
- HTML preview with before/after slider per image
- GPU and VRAM profiling for laptop-class hardware

## Quick Start

Put test images in `datasets/input`, then run:

```powershell
python src/realesrgan_benchmark.py --input-dir datasets/input --limit 20 --model x4plus
```

The run folder will be created under `output/realesrgan/<timestamp>/`.

## Preview

- Open `output/realesrgan/<timestamp>/preview.html`
- Or load `output/realesrgan/<timestamp>/preview-data.json` in the preview page

## Model Notes

- `x4plus` is the default general-purpose preset.
- `x2plus` is lighter and better for lower VRAM.
- `anime6b` is tuned for anime-style images.

## GPU Guidance

- RTX 3070 laptop GPUs should run Real-ESRGAN comfortably for this benchmark.
- If VRAM is tight, lower `--tile` to `256` or `128`.
- For very large images, tile-based inference is safer than full-frame inference.

## Environment

- Python 3.11+
- Windows
- CUDA-capable NVIDIA GPU recommended

