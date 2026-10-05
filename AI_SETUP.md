# NexusLoop V1.2 — cấu hình Multi‑LLM

NexusLoop **không khóa vào GPT**. Lõi sản phẩm tách thành hai phần:

1. **NexusLoop Core**: đối chiếu A↔B, trạng thái dự án, dependency, hard gate, quyền con người, audit log, kiểm tra output và fallback.
2. **LLM Provider Layer**: đọc tài liệu phi cấu trúc và chọn/giải thích bước bằng chứng tiếp theo trong **tập phương án đã được Core cho phép**.

Nếu không có key, provider lỗi, model trả JSON sai hoặc trả candidate ngoài tập an toàn, demo vẫn chạy bằng **cơ chế dự phòng xác định**.

## 1. Tạo `.env`

Windows Miniconda Prompt:

```bat
copy .env.example .env
notepad .env
```

Không commit `.env` lên GitHub.

## 2. Chọn provider

### Tự động

```env
NEXUSLOOP_AI_PROVIDER=auto
NEXUSLOOP_PROVIDER_PRIORITY=openai,anthropic,gemini,openai_compatible,ollama
```

NexusLoop chọn provider đầu tiên đã có đủ cấu hình. Nếu provider đó lỗi và `NEXUSLOOP_LLM_FAILOVER=true`, hệ thống thử provider cấu hình tiếp theo trước khi rơi về fallback.

### OpenAI

```env
NEXUSLOOP_AI_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=your_model_id
```

### Anthropic Claude

```env
NEXUSLOOP_AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key
ANTHROPIC_MODEL=your_model_id
```

### Google Gemini

```env
NEXUSLOOP_AI_PROVIDER=gemini
GEMINI_API_KEY=your_key
GEMINI_MODEL=your_model_id
```

`GOOGLE_API_KEY` cũng được chấp nhận nếu `GEMINI_API_KEY` trống.

### DeepSeek / Qwen / Mistral / gateway tương thích OpenAI

Dùng adapter `openai_compatible` **chỉ khi dịch vụ bạn dùng có endpoint tương thích OpenAI**:

```env
NEXUSLOOP_AI_PROVIDER=openai_compatible
OPENAI_COMPATIBLE_API_KEY=your_key
OPENAI_COMPATIBLE_BASE_URL=https://your-provider.example/v1
OPENAI_COMPATIBLE_MODEL=your_model_id
```

Endpoint/model cụ thể phải lấy từ tài liệu của nhà cung cấp bạn đang dùng.

### Ollama / model local

Khởi động Ollama và model trước, sau đó:

```env
NEXUSLOOP_AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=your_local_model
```

## 3. Chế độ fallback bắt buộc

Muốn quay demo hoàn toàn không phụ thuộc Internet/API:

```env
NEXUSLOOP_AI_MODE=fallback
```

Core vẫn thực hiện:

- đối chiếu A↔B;
- kiểm tra dependency;
- hard gate;
- xếp hạng bằng chứng theo mức bất định, mức bắt buộc, số bước phụ thuộc, chi phí và thời gian;
- re-plan sau bằng chứng mới;
- human override;
- audit log;
- Decision Pack.

## 4. Kiểm tra provider đang dùng

Chạy server rồi mở:

```text
http://localhost:8000/api/ai/status
```

Danh sách toàn bộ provider:

```text
http://localhost:8000/api/ai/providers
```

Không endpoint nào trả API key ra ngoài.

## 5. Ranh giới an toàn

LLM **không được**:

- tự tuyên bố exchange hợp pháp;
- chứng nhận an toàn kỹ thuật;
- ghi đè hard gate;
- tự tạo candidate ngoài danh sách cho phép;
- tự biến UNKNOWN thành PASS;
- tự phê duyệt Pilot.

LLM chỉ được chọn một `candidate_id` trong tập mà NexusLoop Core đã xác nhận là khả dụng. Output sai schema hoặc ngoài whitelist bị bỏ và fallback tiếp quản.
