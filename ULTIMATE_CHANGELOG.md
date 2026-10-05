# NexusLoop Ultimate · Changelog

## UI
- Giữ ngôn ngữ giao diện thương mại của concept `nexusloop-source` nhưng tái cấu trúc thành 4 không gian sản phẩm.
- Opportunity Scan lấy toàn bộ số liệu từ backend.
- Live Workspace có Resource Flow + Live Decision Flow + Inspector.
- Thêm Execution Timeline và Replay Run.
- Thêm Decision Studio, Decision Graph, Data Lineage và What-if Simulator.
- Thêm Command Center, AI Router, Failure Map và Autonomy Boundary.
- Responsive layout cho desktop/mobile.
- Bỏ KPI viết cứng và nút trạng thái giả.

## Backend
- Thêm `nexusloop/observability.py`.
- Thêm readiness/data completeness metrics có công thức minh bạch.
- Thêm provenance cho Decision Pack.
- Thêm RunTracker ghi before/after, duration, flow và error component.
- Thêm `/api/overview`.
- Thêm `/api/cases/{id}/observability`.
- Thêm `/api/cases/{id}/runs` và `/api/runs/{run_id}`.
- Dọn endpoint upload bị trùng trong source cũ.
- Giữ contract API cũ để toàn bộ test gốc tiếp tục chạy.

## Logic được giữ nguyên
- Compatibility Engine.
- Hard gate precedence.
- Candidate ranking.
- Human override.
- Human approvals.
- Multi-LLM router + deterministic fallback.
- Document ingestion.
- Decision Pack.
- Audit trail.

## Validation
- 23/23 test gốc vẫn pass.
- Thêm 4 test cho observability/Ultimate UI.
- Tổng: 27/27 tests pass.
