# Benchmark Plan

## Objective

So sánh chất lượng và hiệu năng giữa các mô hình AI Upscale.

---

## Dataset

Ảnh sẽ được chia thành

- Portrait
- Landscape
- Anime
- Text
- Low-light
- Noisy

---

## Evaluation Metrics

### Performance

- Inference Time
- GPU Usage
- VRAM

### Quality

- PSNR
- SSIM

### Visual

Đánh giá bằng mắt

- Sharpness
- Detail
- Artifact
- Noise

---

## Benchmark Result

| Model | Avg Time | Min Time | Max Time | Peak VRAM | Scale | Precision | Rating |
|-------|----------|----------|----------|-----------|-------|-----------|--------|
| Real-ESRGAN (x4plus) | 7.9s | 1.9s | 18.8s | 2,846 MB | x4 | FP16 | ★★★★☆ |
| SwinIR (RealSR-L)    | 34.2s | 7.8s | 84.5s | 4,842 MB | x4 | Autocast FP16 | ★★★★★ |
| HAT (Real_HAT_GAN)   | 58.2s | 10.3s | 147.3s | 8,418 MB | x4 | FP32 (bắt buộc) | ★★★★★ |

> Chú thích: Tile size = 256, Tile padding = 10, Dataset = 20 ảnh đa dạng, GPU = NVIDIA RTX Laptop.