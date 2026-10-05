# NexusLoop Demo V1 — kịch bản 100–120 giây

## 0–12s · Đầu vào A → B
Mở **Hồ sơ đầu vào**.

Voice:
> “Nhà máy A có khoảng 600 m³ nước sau xử lý mỗi ngày. Nhà máy B cần khoảng 450 m³ nước kỹ thuật. Nhưng A còn thiếu hai chỉ tiêu chất lượng và dự án chưa có xác minh pháp lý.”

Chỉ A profile, B profile, bảng quality.

## 12–28s · AI đối chiếu
Mở **AI đối chiếu**.

Voice:
> “NexusLoop đọc hồ sơ hai bên, chuẩn hóa dữ liệu và chia kết quả thành: phù hợp, còn thiếu hoặc xung đột. AI không tự điền số đo còn thiếu.”

Chỉ trace 7 bước và compatibility matrix.

## 28–48s · AI chọn bằng chứng
Mở **Kế hoạch AI**.

Voice:
> “Có ba việc có thể làm ngay: kiểm tra pháp lý, xét nghiệm bổ sung và kiểm tra độ ổn định nguồn. Agent chọn pháp lý trước vì đây là điều kiện có thể dừng toàn bộ dự án, ảnh hưởng nhiều bước phía sau nhưng có chi phí xác minh thấp.”

Chỉ phần factors + phương án không chọn.

## 48–62s · Con người có quyền sửa kế hoạch
Chọn `Đối chiếu 30 ngày lưu lượng` và nhập lý do.

Voice:
> “Người vận hành không chỉ có nút đồng ý. Họ có thể chọn một bước khác, sửa dữ liệu hoặc thêm điều kiện; mọi thay đổi đều được ghi lại.”

Sau đó bấm **Để AI tự chọn lại**.

## 62–82s · Evidence → re-plan
Mở **Thực hiện & bằng chứng** → legal PASS.

Voice:
> “Khi bằng chứng quay về, NexusLoop gắn kết quả vào đúng điều kiện, mở khóa dependency và tính lại toàn bộ kế hoạch.”

Cho banner: legal → water lab.

## 82–100s · Output cho B
Chuyển **Kết quả**.

Voice:
> “Đầu ra không chỉ là một nhãn Pilot hay Stop. Bên B nhận được mức nguồn có thể sử dụng, điều kiện còn thiếu, yêu cầu kỹ thuật và một bộ hồ sơ quyết định có thể truy vết.”

Mở Decision Pack.

## 100–115s · Responsible AI
Chọn case **Demo STOP an toàn**.

Voice:
> “Nếu hard gate đã được xác minh là không đạt, cả AI lẫn người dùng đều không có nút ghi đè trực tiếp. Chỉ bằng chứng mới hoặc người có thẩm quyền mới có thể mở lại đường triển khai.”

End frame:
**NexusLoop — kiểm tra đúng bằng chứng tiếp theo trước khi trả tiền cho câu hỏi chưa cần thiết.**

---

## Gợi ý bổ sung cho V1.2 Multi‑LLM

Trước khi quay, cấu hình một provider thật hoặc để fallback. Chỉ vào badge trên header trong 2–3 giây:

- Có provider: hiển thị `Tên provider · model`.
- Không key/API lỗi: hiển thị `AI dự phòng · không cần key`.

Nếu BGK hỏi vendor lock‑in: mở `/api/ai/providers` hoặc `AI_SETUP.md` và giải thích rằng OpenAI/Claude/Gemini/OpenAI-compatible/Ollama cùng đi qua một router; hard gate và fallback không phụ thuộc model.
