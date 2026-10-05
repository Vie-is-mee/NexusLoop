# Minimum Evidence Path — cơ chế ra quyết định của demo

NexusLoop không buộc mọi bước kiểm tra phải đi theo một checklist cố định. Ở mỗi trạng thái, hệ thống:

1. đọc trạng thái hiện tại của hồ sơ A/B;
2. xác định các điều kiện còn thiếu hoặc xung đột;
3. tìm các hành động **có thể thực hiện ngay**;
4. so sánh chúng theo các yếu tố có thể kiểm tra;
5. đề xuất bước tiếp theo;
6. cho phép con người chọn một bước khả dụng khác;
7. lập lại kế hoạch khi bằng chứng mới xuất hiện.

## Các yếu tố xếp hạng trong MVP

Demo không hiển thị một “AI score 87/100” bí ẩn. Mỗi phương án được giải thích bằng:

- mức độ bất định hiện tại;
- có phải điều kiện bắt buộc hay không;
- số bước phía sau phụ thuộc vào kết quả;
- chi phí tương đối để lấy bằng chứng;
- thời gian dự kiến.

Backend dùng một heuristic minh bạch để xếp hạng. Đây là **cơ chế demo**, không phải tuyên bố tối ưu khoa học.

## Ví dụ hero case

Ở trạng thái đầu, ba hành động đều có thể làm ngay:

- xác minh đường pháp lý;
- bổ sung xét nghiệm nước;
- đối chiếu 30 ngày lưu lượng.

AI thường chọn **xác minh pháp lý** vì nếu không đạt thì toàn bộ đường A→B dừng, nó ảnh hưởng nhiều bước phía sau, trong khi chi phí xác minh tương đối thấp.

Con người vẫn có thể chọn xét nghiệm hoặc continuity trước nếu có lý do vận hành. Việc override được ghi vào audit trail và không làm mất quyền re-plan của AI sau evidence mới.

Detailed engineering chỉ mở khi legal + quality + continuity đều đã PASS.

## Future direction

Một sản phẩm production có thể thay heuristic bằng formal Value of Information, Bayesian updating, cost-sensitive active learning hoặc learned policy. Demo V1 ưu tiên khả năng giải thích và kiểm tra cơ chế trước.
