# NexusLoop Ultimate · UI/UX Architecture

## Mục tiêu

Giao diện không đóng vai trò “dashboard trang trí”. Nó là một lớp quan sát trực tiếp lên decision engine. Người dùng phải trả lời được 5 câu hỏi ngay trên UI:

1. Dữ liệu nào vừa đi vào?
2. Hệ thống đang ở bước nào?
3. Bước này nhận gì và tạo ra gì?
4. Vì sao kết quả thay đổi?
5. Nếu lỗi, lỗi nằm ở component nào và nên xử lý tiếp ra sao?

## 5 trụ cột

### Live Flow
`agent.trace` của Core được mở rộng thành 9 node trực quan. Node có trạng thái `done`, `active`, `waiting`, `blocked`; UI không tự bịa trạng thái.

### Traceability
Decision Pack có provenance cho các đại lượng có thể tính trực tiếp, ví dụ matched volume, supplier utilization và receiver coverage.

### Failure Map
Mutation nghiệp vụ được bọc bởi `RunTracker`. ValueError của domain được ghi component, message, recoverability và recovery hints.

### Interactive Decision
Người dùng có thể đưa evidence, chỉnh profile, thêm constraint, override plan, approve và dùng What-if Simulator. Chỉ simulator là sandbox không ghi dữ liệu.

### Human Control
AI không được xác nhận chuyên môn hoặc ghi đè hard gate STOP. Boundary này được thể hiện công khai trong Command Center.

## Run model

Run history là in-memory để phù hợp demo, không thay đổi decision state.

```text
start(action)
  → snapshot before
  → real store action
  → NexusAgent.recompute
  → snapshot after
  → capture flow
  → completed / failed
```

Nếu phát triển thành production, thay in-memory RunTracker bằng bảng dữ liệu/event store nhưng giữ contract API hiện tại.
