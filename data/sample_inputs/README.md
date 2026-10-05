# File đầu vào chuẩn để test NexusLoop

File: `NexusLoop_demo_input_standard.json`

Cách test trên giao diện:
1. Mở **01 · Hồ sơ đầu vào**.
2. Ở **Thêm tài liệu**, chọn **Hồ sơ cặp A ↔ B**.
3. Chọn file `NexusLoop_demo_input_standard.json`.
4. Bấm **Đọc tài liệu**.
5. Sang **02 · AI đối chiếu** để xem hệ thống so sánh A ↔ B.
6. Sang **03 · Kế hoạch AI** để xem bước tiếp theo.

Nếu `OPENAI_API_KEY` có trong `.env`, bộ lập kế hoạch sẽ gọi OpenAI API để chọn và giải thích bước tiếp theo trong tập phương án đã qua quy tắc an toàn. Nếu không có key, cơ chế dự phòng cố định vẫn chạy đầy đủ.
