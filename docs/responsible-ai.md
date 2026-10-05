# Responsible AI boundary

NexusLoop là **agent điều phối bằng chứng và hỗ trợ quyết định**, không phải cơ quan quản lý, luật sư, phòng lab hay kỹ sư ký duyệt.

## Quyền của AI

- đọc và cấu trúc tài liệu;
- so sánh hồ sơ Nhà máy A với yêu cầu Nhà máy B;
- phát hiện khoảng trống dữ liệu;
- đề xuất/xếp hạng bước thu bằng chứng;
- tạo task;
- re-plan khi evidence thay đổi;
- giải thích lý do chọn và không chọn;
- tạo decision pack.

## Quyền của con người

- sửa dữ liệu AI trích;
- thay đổi nhu cầu/giả định;
- chọn một kế hoạch khả dụng khác;
- thêm constraint mới;
- cung cấp evidence;
- phê duyệt chuyên môn.

## Quyền mà cả AI và người vận hành thông thường đều không có

- nhấn một nút để override hard gate đã được xác minh là STOP;
- biến dữ liệu thiếu thành PASS;
- tự cấp permit;
- tự tuyên bố compliance;
- certify safety;
- authorize physical transfer.

Muốn mở lại hard gate phải có **bằng chứng mới** hoặc **review từ người có thẩm quyền**, và thay đổi đó phải được lưu dấu vết.

## Fail-safe

1. Missing measurement = UNKNOWN/GAP.
2. Conflicting evidence = HOLD.
3. Hard STOP = stop current path.
4. PILOT READY = all required gates PASS + human approvals.
5. Every edit, evidence submission, plan override and approval is logged.
6. Demo chỉ dùng synthetic data.
