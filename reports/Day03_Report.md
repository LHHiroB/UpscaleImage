# Day 03 Report - Real-ESRGAN Benchmark and Preview

**Project:** UpscaleImage  
**Date:** 2026-07-14  
**Phase:** Real-ESRGAN Benchmark

---

# Objective

Chạy benchmark thực tế cho Real-ESRGAN trên bộ ảnh đầu vào, tạo preview để review từng ảnh, và xác định cấu hình GPU NVIDIA phù hợp cho dự án theo các mức giá thấp - vừa - cao.

---

# What I Completed

## 1. Benchmark Real-ESRGAN on 20 images

Mình đã chạy benchmark Real-ESRGAN `x4plus` trên 20 ảnh `.jpg` trong `datasets/inputs`.

Môi trường chạy:

- Python 3.11.9
- NVIDIA RTX 3070 Laptop GPU
- CUDA mode
- Half precision enabled
- Tile size: 256

Kết quả benchmark:

- Số ảnh xử lý: 20
- Average inference time: `7911.173 ms/image`
- Fastest image: `1960.823 ms`
- Slowest image: `18860.508 ms`
- Peak VRAM recorded: `2846.0 MB`

Nhận xét nhanh:

- RTX 3070 Laptop GPU chạy được Real-ESRGAN ổn định.
- Với `tile=256`, VRAM vẫn an toàn cho bộ test này.
- Thời gian xử lý dao động khá mạnh theo độ lớn và độ phức tạp của ảnh.

## 2. Build preview for review

Mình đã dựng lại hệ thống preview theo kiểu:

- 1 ảnh = 1 trang preview riêng
- Bên trái: ảnh gốc
- Bên phải: ảnh upscale
- Cột bên cạnh: benchmark info của đúng ảnh đó

Các file chính:

- `output/realesrgan/20260714-125802/preview.html`
- `output/realesrgan/20260714-125802/preview-data.json`
- `output/realesrgan/20260714-125802/pages/*.jpg.html`

## 3. Fix data flow so benchmark fields show up in preview

Mình đã chỉnh lại luồng dữ liệu để preview lấy đúng các thông số benchmark từ file JSON, bao gồm:

- per-image `elapsed_ms`
- `avg_ms`
- `min_ms`
- `max_ms`
- `peak_vram_mb`
- `tile`
- `tile_pad`
- `pre_pad`
- `outscale`
- `device`
- `half_precision`

---

# Benchmark Summary

## Run configuration

- Model: `RealESRGAN_x4plus`
- Input format: `.jpg`
- Output scale: `4x`
- Inference mode: `cuda`
- Tile: `256`
- Half precision: `true`

## Observed result

| Metric | Value |
|---|---:|
| Images | 20 |
| Avg time | 7911.173 ms |
| Min time | 1960.823 ms |
| Max time | 18860.508 ms |
| Peak VRAM | 2846.0 MB |

## Interpretation

- Đây là mức hiệu năng phù hợp cho nghiên cứu và benchmark offline.
- VRAM không phải nút thắt lớn ở cấu hình này khi dùng tile.
- Nếu bỏ tile hoặc dùng ảnh lớn hơn nhiều, card 8GB sẽ dễ chạm giới hạn hơn.

---

# How To Use

## 1. Put images into input folder

Đặt ảnh vào:

```text
datasets/inputs/
```

## 2. Run benchmark

```powershell
py -3.11 src\realesrgan_benchmark.py --input-dir datasets\inputs --limit 20 --model x4plus --tile 256 --device cuda
```

## 3. Open preview

Mở file:

```text
output/realesrgan/<timestamp>/preview.html
```

Trong preview:

- Trang index cho xem toàn bộ ảnh
- Bấm vào từng ảnh để vào trang riêng
- Trang riêng có original bên trái, upscale bên phải
- Benchmark info được hiển thị ngay trên trang

## 4. Review từng ảnh

Nên review theo thứ tự:

1. Nhìn tổng thể ảnh gốc và ảnh upscale
2. So chi tiết nhỏ như tóc, viền, chữ, texture
3. Kiểm tra artifact, oversharpen, halo, blur giả
4. So timing của ảnh đó với các ảnh còn lại

---

# GPU Recommendation by Rental Price

## Kết luận ngắn

Nếu chỉ chọn **1 GPU NVIDIA đáng tiền nhất cho dự án này dưới dạng thuê theo giờ**, mình khuyên:

**RTX 4090 24GB**

Lý do:

- Tốc độ mạnh và ổn định cho benchmark Real-ESRGAN
- 24GB VRAM đủ rộng để xử lý ảnh lớn và batch nặng thoải mái hơn
- Giá thuê theo giờ vẫn còn hợp lý so với các GPU cao cấp hơn

## Three-tier recommendation

| Tier | GPU | Why it fits this project |
|---|---|---|
| Low | RTX A5000 24GB | `~$0.27/hr` on Runpod Pods. Rẻ, VRAM đủ rộng cho benchmark và inference ổn định. |
| Mid | RTX 4090 24GB | `~$0.69/hr` on Runpod Pods. Điểm cân bằng tốt nhất giữa tốc độ, VRAM và cost/performance. |
| High | A100 PCIe 80GB | `~$1.39/hr` on Runpod Pods. Hợp khi muốn chạy batch lớn, ảnh lớn, hoặc nhiều job song song. |

## Rental context

Mốc thuê tham khảo theo giờ trên Runpod Pods:

- RTX A5000: `$0.27/hr`
- RTX 4090: `$0.69/hr`
- A100 PCIe 80GB: `$1.39/hr`

Lưu ý:

- Đây là giá thuê theo giờ, không phải giá mua.
- Giá thực tế có thể thay đổi theo khu vực, thời điểm, và loại instance.
- Với tác vụ upscale ảnh, VRAM thường quan trọng hơn nhiều so với chỉ số FPS game.
- Card 24GB là mức rất thoải mái cho Real-ESRGAN batch lớn.
- Nếu muốn tiết kiệm nhất cho benchmark nhỏ, RTX A5000 là điểm khởi đầu tốt.

---

# Deliverables

- Benchmark Real-ESRGAN 20 ảnh hoàn tất
- Preview theo từng ảnh hoàn tất
- Summary file và page riêng cho từng ảnh hoàn tất
- Khuyến nghị GPU theo 3 mức giá được xác định

---

# Notes

- RTX 3070 Laptop GPU hiện tại vẫn đủ để tiếp tục research và prototype.
- Nếu mục tiêu là giảm thời gian benchmark và xử lý ảnh lớn hơn, nâng lên 12GB VRAM là bước hợp lý nhất.

---

# Next Steps

- Benchmark thêm `x2plus` để so sánh tốc độ với `x4plus`
- So sánh chất lượng giữa các nhóm ảnh khó
- Tối ưu preview thành report markdown tự động
- Thiết kế pipeline inference ổn định hơn cho production
