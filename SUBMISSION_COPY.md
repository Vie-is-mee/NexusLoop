# Hackathon4U submission copy

## Project Title
NexusLoop

## Track
3. Môi trường & Phát triển bền vững

## Project Description
NexusLoop là tác nhân AI giúp một dự án cộng sinh công nghiệp đi từ “Nhà máy A có nguồn tài nguyên này” và “Nhà máy B cần đầu vào kia” tới một quyết định triển khai có bằng chứng. Hệ thống đọc và chuẩn hóa hồ sơ hai bên, đối chiếu số lượng, chất lượng, lịch vận hành, hạ tầng, điều kiện pháp lý và kinh tế; sau đó xác định bằng chứng nào nên được kiểm tra tiếp theo vì có khả năng thay đổi quyết định lớn nhất với chi phí/thời gian hợp lý.

Khác với checklist cố định, Agent duy trì trạng thái dự án và lập lại kế hoạch sau mỗi bằng chứng mới. Giao diện giải thích vì sao một bước được chọn, vì sao phương án khác chưa được ưu tiên, đồng thời cho phép con người sửa dữ liệu, chọn một kế hoạch khả dụng khác và thêm điều kiện mới. Các hard gate pháp lý/kỹ thuật đã được xác minh là STOP không thể bị AI hoặc người vận hành ghi đè trực tiếp; quyết định pilot cuối cùng vẫn cần người có chuyên môn phê duyệt.

MVP dùng dữ liệu mô phỏng để chứng minh trọn vòng Input A/B → AI đối chiếu → Minimum Evidence Path → human intervention → evidence → re-plan → Pilot/Hold/Stop → Decision Pack cho bên nhận.

## Tech Stack Tags
Python, FastAPI, Pydantic, JavaScript, HTML, CSS, Agentic AI, AI Workflow, Decision Support, Rule Engine, Docker

## GitHub About
Agentic Evidence-to-Pilot layer for industrial symbiosis: compare A→B, choose decision-critical evidence, replan when it arrives, and preserve human authority over hard gates.

## Video title
NexusLoop Demo V1 — From A→B data to an evidence-backed pilot decision
