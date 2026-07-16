# Báo cáo Day 4 — So sánh Models: Real-ESRGAN vs SwinIR vs HAT

> **Ngày thực hiện:** 16/07/2026  
> **Người thực hiện:** HiroB  
> **Thiết bị:** NVIDIA RTX Laptop GPU, Windows, Python 3.11, CUDA  
> **Dataset:** 20 ảnh đa dạng (Portrait, Landscape, Anime, Low-light…), kích thước gốc từ 380×675 đến 1200×2133

---

## 1. Mục tiêu

Theo Roadmap Day 4, mục tiêu chính là **so sánh hiệu năng và chất lượng giữa 3 mô hình AI Upscale** đã được lựa chọn từ Day 2:

- **Real-ESRGAN** (kiến trúc RRDB / CNN)
- **SwinIR** (kiến trúc Swin Transformer)
- **HAT** (kiến trúc Hybrid Attention Transformer)

Cả 3 model đều upscale ×4 trên cùng dataset 20 ảnh, sử dụng kỹ thuật **Tiling** (tile=256, pad=10) để giữ VRAM ở mức an toàn cho Laptop.

---

## 2. Kết quả Benchmark tổng hợp

| Chỉ số | Real-ESRGAN | SwinIR | HAT |
|--------|-------------|--------|-----|
| **Kiến trúc** | RRDB (CNN) | Swin Transformer | Hybrid Attention Transformer |
| **Precision** | FP16 | Autocast FP16 | FP32 (bắt buộc) |
| **Avg Time / ảnh** | **7.9s** | 34.2s | 58.2s |
| **Min Time** | 1.9s | 7.8s | 10.3s |
| **Max Time** | 18.8s | 84.5s | 147.3s |
| **Peak VRAM** | **2,846 MB** | 4,842 MB | 8,418 MB |
| **Đánh giá** | ★★★★☆ | ★★★★★ | ★★★★★ |

---

## 3. Phân tích chi tiết từng Model

### 3.1. Real-ESRGAN (x4plus)

**Ưu điểm:**
- Nhanh nhất trong 3 model, trung bình chỉ **7.9 giây/ảnh**.
- VRAM thấp nhất: đỉnh chỉ **2.8 GB**, chạy thoải mái trên mọi GPU rời.
- Hỗ trợ FP16 gốc, không phát sinh lỗi số.
- Ảnh nhỏ (380×675) xử lý chỉ trong **~2 giây**.

**Nhược điểm:**
- Có xu hướng **over-sharpen** — các chi tiết nhỏ đôi khi bị cứng, mất tự nhiên.
- Ảnh lớn (1200×2133) vẫn mất tới **~19 giây**, khoảng cách với ảnh nhỏ khá lớn (tỷ lệ ~10:1).

**Kết luận:** Phù hợp làm **Fast Mode** — xử lý hàng loạt, batch lớn, hoặc trên máy yếu.

---

### 3.2. SwinIR (RealSR-L x4 GAN)

**Ưu điểm:**
- Chất lượng phục hồi chi tiết **rất tự nhiên**, ít artifact.
- VRAM ở mức trung bình: **4.8 GB**, vẫn khả thi cho đa số Laptop gaming.
- Tương thích với `torch.autocast(FP16)` — tăng tốc mà không bị lỗi số.

**Nhược điểm:**
- Chậm hơn Real-ESRGAN **~4.3 lần** (34.2s vs 7.9s trung bình).
- Ảnh lớn (1200×2133) mất tới **~85 giây**, gần sát ngưỡng 90 giây của yêu cầu dự án.

**Kết luận:** Cân bằng tốt nhất giữa chất lượng và hiệu năng. Phù hợp làm **Default Mode**.

---

### 3.3. HAT (Real_HAT_GAN x4)

**Ưu điểm:**
- Texture và chi tiết phục hồi **tốt nhất** trong 3 model — đặc biệt trên da người, lông tóc, và cỏ cây.
- Ảnh nhỏ (380×675) vẫn nằm trong ngưỡng chấp nhận: **~10 giây**.

**Nhược điểm:**
- Chậm nhất: trung bình **58.2 giây/ảnh**, ảnh lớn lên tới **147 giây** (vượt xa ngưỡng 90s).
- VRAM rất cao: đỉnh **8.4 GB** — yêu cầu tối thiểu GPU 8 GB.
- **Không hỗ trợ FP16/Autocast** — khi ép Half-Precision, mô hình sinh ra giá trị NaN → ảnh đầu ra toàn màu đen. Bắt buộc phải chạy FP32 (flag `--no-half`).

**Kết luận:** Phù hợp làm **Quality Mode** — khi người dùng có GPU mạnh (≥8 GB VRAM) và ưu tiên chất lượng tuyệt đối hơn tốc độ.

---

## 4. Bảng chi tiết thời gian xử lý từng ảnh

### Real-ESRGAN

| Ảnh | Kích thước gốc | Kích thước output | Thời gian |
|-----|-----------------|-------------------|-----------|
| 1.jpg | 1200×675 | 4800×2700 | 6.1s |
| 10.jpg | 1200×675 | 4800×2700 | 5.1s |
| 11.jpg | 648×1152 | 2592×4608 | 4.7s |
| 12.jpg | 1000×1500 | 4000×6000 | 10.4s |
| 13.jpg | 380×675 | 1520×2700 | **1.9s** |
| 14.jpg | 1086×1932 | 4344×7728 | 14.9s |
| 15.jpg | 851×1512 | 3404×6048 | 9.4s |
| 16.jpg | 563×1000 | 2252×4000 | 3.9s |
| 17.jpg | 1200×2133 | 4800×8532 | 18.2s |
| 18.jpg | 1200×2133 | 4800×8532 | **18.8s** |

### SwinIR

| Ảnh | Kích thước gốc | Kích thước output | Thời gian |
|-----|-----------------|-------------------|-----------|
| 1.jpg | 1200×675 | 4800×2700 | 24.1s |
| 10.jpg | 1200×675 | 4800×2700 | 23.4s |
| 11.jpg | 648×1152 | 2592×4608 | 20.6s |
| 12.jpg | 1000×1500 | 4000×6000 | 41.1s |
| 13.jpg | 380×675 | 1520×2700 | **7.8s** |
| 14.jpg | 1086×1932 | 4344×7728 | 60.7s |
| 15.jpg | 851×1512 | 3404×6048 | 38.6s |
| 16.jpg | 563×1000 | 2252×4000 | 16.4s |
| 17.jpg | 1200×2133 | 4800×8532 | **84.5s** |
| 18.jpg | 1200×2133 | 4800×8532 | 84.2s |

### HAT

| Ảnh | Kích thước gốc | Kích thước output | Thời gian |
|-----|-----------------|-------------------|-----------|
| 1.jpg | 1200×675 | 4800×2700 | 39.6s |
| 10.jpg | 1200×675 | 4800×2700 | 38.5s |
| 11.jpg | 648×1152 | 2592×4608 | 36.4s |
| 12.jpg | 1000×1500 | 4000×6000 | 77.4s |
| 13.jpg | 380×675 | 1520×2700 | **10.3s** |
| 14.jpg | 1086×1932 | 4344×7728 | 121.8s |
| 15.jpg | 851×1512 | 3404×6048 | 68.4s |
| 16.jpg | 563×1000 | 2252×4000 | 26.9s |
| 17.jpg | 1200×2133 | 4800×8532 | 146.2s |
| 18.jpg | 1200×2133 | 4800×8532 | **147.3s** |

---

## 5. Bài học kỹ thuật rút ra

| Vấn đề | Giải pháp đã áp dụng |
|--------|----------------------|
| Transformer models rất tốn VRAM khi xử lý nguyên ảnh | Áp dụng **Tiling** (256×256) — chia ảnh thành các grid nhỏ, xử lý từng ô rồi ghép lại. |
| SwinIR không hỗ trợ `model.half()` qua Spandrel | Sử dụng `torch.autocast(dtype=float16)` thay vì ép kiểu trực tiếp — giữ nguyên trọng số FP32 nhưng tính toán ở FP16 khi an toàn. |
| HAT sinh NaN khi chạy FP16 → ảnh ra màu đen | Phát hiện HAT không tương thích với bất kỳ dạng Half-Precision nào → thêm flag `--no-half` bắt buộc chạy FP32. |
| Thư viện `spandrel` giúp load đa dạng kiến trúc | Thay vì viết script riêng cho từng model, `spandrel.ModelLoader` tự nhận diện kiến trúc từ file `.pth` → 1 script chung cho tất cả. |

---

## 6. Kết luận & Đề xuất cho Pipeline

Dựa trên toàn bộ dữ liệu benchmark thực tế, đề xuất hệ thống **3 chế độ** cho Inference Pipeline (Day 5):

| Chế độ | Model | Đối tượng | Yêu cầu GPU |
|--------|-------|-----------|-------------|
| ⚡ **Fast** | Real-ESRGAN | Batch lớn, máy yếu, cần tốc độ | ≥ 3 GB VRAM |
| ⚖️ **Balanced** (Default) | SwinIR | Cân bằng chất lượng – tốc độ | ≥ 5 GB VRAM |
| 💎 **Quality** | HAT | Ưu tiên chất lượng tuyệt đối | ≥ 8 GB VRAM |

> **Lưu ý quan trọng:** Với ảnh có kích thước gốc lớn hơn 1200×1900, cả SwinIR và HAT đều có thể vượt ngưỡng 90 giây. Cần cân nhắc thêm cơ chế cảnh báo hoặc tự động giảm kích thước đầu vào trong Pipeline.

---

## Kế hoạch Day 5: Thiết kế Inference Pipeline

Dựa vào kinh nghiệm và bài học kỹ thuật từ Day 4, hệ thống Inference Pipeline sẽ được thiết kế theo hướng **Modular** với 3 module chính:

### A. Model Loader (Sử dụng Spandrel)
- Load bất kỳ file `.pth` nào, tự động nhận diện kiến trúc (Real-ESRGAN, SwinIR, HAT…).
- Tự động chọn device (`cuda` / `cpu`).
- Tự động bật Autocast FP16 cho models hỗ trợ, disable cho models nhạy cảm (HAT).

### B. Pre/Post-processing
- Đọc ảnh → chuyển BGR→RGB → normalize [0,1] → Tensor.
- Sau inference: clamp [0,1] → denormalize → RGB→BGR → lưu file PNG.

### C. Inference Engine (Core)
- **Tile Processor** tự động chia grid (256×256, pad=10) khi ảnh vượt ngưỡng.
- Bọc forward pass trong `torch.no_grad()` + `torch.autocast` (khi phù hợp).
- Hỗ trợ 3 chế độ: Fast / Balanced / Quality.