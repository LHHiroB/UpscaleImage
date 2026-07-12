# Decision Log

Tài liệu này ghi lại các quyết định kỹ thuật quan trọng trong suốt quá trình nghiên cứu và phát triển dự án.

---

## 2026-07-11

### Decision 1: Sử dụng Python 3.11

**Reason**

- Tương thích tốt với hệ sinh thái AI hiện tại.
- Được hầu hết các framework như PyTorch, ONNX Runtime và OpenCV hỗ trợ ổn định.

---

### Decision 2: Phát triển dưới dạng CLI

**Reason**

- Tập trung vào nghiên cứu và benchmark AI trước.
- Giảm thời gian phát triển giao diện.
- Dễ dàng tự động hóa quá trình benchmark và kiểm thử.

---

## 2026-07-12

### Decision 3: Lựa chọn các mô hình để benchmark

**Selected Models**

- Real-ESRGAN
- SwinIR
- HAT

**Reason**

- Đại diện cho nhiều hướng tiếp cận khác nhau trong bài toán Super Resolution.
- Có cộng đồng sử dụng lớn và nhiều tài liệu tham khảo.
- Có pretrained model để thử nghiệm nhanh.
- Có paper chính thức và kết quả nghiên cứu đáng tin cậy.

**Next**

- Benchmark Real-ESRGAN.
- Benchmark SwinIR.
- Benchmark HAT.
- So sánh chất lượng, tốc độ và mức sử dụng tài nguyên trước khi đưa ra quyết định cuối cùng.