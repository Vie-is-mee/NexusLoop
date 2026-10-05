# Third-party components · NexusLoop V1.2

NexusLoop Core do đội phát triển; các thư viện và dịch vụ dưới đây chỉ là hạ tầng hoặc provider tùy chọn.

| Thành phần | Vai trò |
|---|---|
| FastAPI | API/backend web |
| Pydantic | schema + validation |
| Uvicorn | ASGI server |
| PyPDF | đọc text PDF trong demo |
| python-dotenv | nạp cấu hình `.env` |
| httpx | HTTP client; dùng cho Anthropic/Gemini/Ollama adapters và test |
| OpenAI Python SDK | OpenAI API + generic OpenAI-compatible adapter |
| LLM provider bên ngoài | Tùy chọn; chỉ dùng cho semantic extraction và evidence planning |

## Provider Layer

V1.2 có adapter cho:

- OpenAI;
- Anthropic Claude;
- Google Gemini;
- OpenAI-compatible endpoint;
- Ollama/local model.

Không provider nào sở hữu business logic cốt lõi của NexusLoop.

## Team-built

- hồ sơ tài nguyên A và nhu cầu B;
- compatibility engine;
- dependency/hard-gate logic;
- safe candidate generation;
- Minimum Evidence Path planner;
- output validator / whitelist;
- deterministic fallback ranking;
- human override + approval boundary;
- audit trail;
- Decision Pack;
- Multi-LLM router + provider adapters;
- UI/UX demo.

## Safety boundary

LLM không phải nguồn chân lý pháp lý/kỹ thuật. Model chỉ được:

1. đọc/tóm tắt/trích xuất thông tin có trong tài liệu;
2. chọn một candidate đã được Core đánh dấu là khả dụng;
3. giải thích quyết định.

Model không được tự tạo PASS/STOP pháp lý, tự phê duyệt Pilot hoặc ghi đè hard gate. Nếu output sai schema, chọn candidate ngoài whitelist hoặc API lỗi, output bị loại và cơ chế fallback tiếp quản.
