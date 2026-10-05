# NexusLoop V1.2 — Multi‑LLM upgrade

## Thay đổi chính so với V1.1

- Tách LLM khỏi NexusLoop Core bằng `LLMRouter`.
- Hỗ trợ OpenAI, Anthropic Claude, Google Gemini, OpenAI-compatible API và Ollama/local model.
- Có `auto` provider selection theo thứ tự ưu tiên cấu hình.
- Có provider failover: API chính lỗi → thử provider kế tiếp → cuối cùng mới deterministic fallback.
- Planner metadata lưu cả provider + model thay vì hard-code OpenAI.
- Document audit ghi provider đã dùng.
- Thêm `/api/ai/providers` để kiểm tra provider cấu hình/đang hoạt động mà không lộ key.
- Giữ nguyên hard gate, dependency, human control và deterministic fallback độc lập với model.
- Thêm test cho router/provider selection.

## Không thay đổi

- LLM không được quyết định tính hợp pháp/an toàn.
- LLM chỉ chọn trong safe candidate set.
- Human vẫn có thể chỉnh kế hoạch khả dụng.
- Hard STOP không có nút override trực tiếp.
- Không API key vẫn demo được.
