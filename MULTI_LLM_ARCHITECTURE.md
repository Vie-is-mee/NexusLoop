# Kiến trúc Multi‑LLM của NexusLoop

```text
                    ┌──────────────────────┐
A/B documents ─────▶│   NexusLoop Core     │
                    │ parse / state / rules│
                    └─────────┬────────────┘
                              │ safe candidates only
                              ▼
                    ┌──────────────────────┐
                    │     LLM Router       │
                    └───┬────┬────┬────┬──┘
                        │    │    │    │
                 OpenAI │ Claude Gemini │ OpenAI-compatible
                        │              │
                        └──── Ollama/local
                              │
                              ▼
                    structured JSON answer
                              │
                              ▼
                    ┌──────────────────────┐
                    │ Output Validator     │
                    │ schema + whitelist   │
                    └─────────┬────────────┘
                              │
                     valid ───┴─── invalid/API fail
                       │                 │
                       ▼                 ▼
                 use LLM plan      deterministic fallback
                       │                 │
                       └────────┬────────┘
                                ▼
                         human can review/
                         edit plan + evidence
```

## Mục tiêu thiết kế

- Không khóa vendor.
- Thay model mà không sửa `engine.py` hay business rules.
- Cho phép local model khi dữ liệu nhạy cảm.
- Provider failover không làm hỏng demo.
- Một provider không bao giờ trở thành nguồn chân lý pháp lý/kỹ thuật.
