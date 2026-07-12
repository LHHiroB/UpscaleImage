# AI Upscale Models Research

## Objective

Khảo sát các mô hình AI Upscale phổ biến nhằm lựa chọn mô hình phù hợp để benchmark và triển khai trong dự án.

---

## Candidate Models

| Model | Status | Notes |
|---------|--------|-------|
| Real-ESRGAN | ⭐⭐⭐⭐⭐ | Được cộng đồng sử dụng rộng rãi |
| ESRGAN | ⭐⭐⭐ | Phiên bản cũ |
| SwinIR | ⭐⭐⭐⭐⭐ | Chất lượng rất cao |
| HAT | ⭐⭐⭐⭐ | Phục hồi chi tiết tốt |
| DAT | ⭐⭐⭐⭐ | Transformer-based |
| OmniSR | ⭐⭐⭐⭐ | Nhẹ, nhanh |

---

## Initial Evaluation

### Real-ESRGAN

Ưu điểm

- Open Source
- Community lớn
- Dễ chạy
- Có model pretrained

Nhược điểm

- Có thể oversharpen
- Không phải model mới nhất

Đánh giá

★★★★★

---

### SwinIR

Ưu điểm

- Chất lượng rất cao
- Paper mạnh

Nhược điểm

- Chậm
- Yêu cầu VRAM cao

Đánh giá

★★★★★

---

### HAT

Ưu điểm

- Khôi phục texture tốt

Nhược điểm

- Nặng

Đánh giá

★★★★☆

---

### DAT

Ưu điểm

- Transformer
- Hiệu quả

Nhược điểm

- Ít tài liệu

Đánh giá

★★★★☆

---

### OmniSR

Ưu điểm

- Nhẹ
- Nhanh

Nhược điểm

- Chưa phổ biến

Đánh giá

★★★★☆

---

## Preliminary Conclusion

Các model sẽ benchmark:

- Real-ESRGAN
- SwinIR
- HAT

Model dự phòng

- DAT
- OmniSR