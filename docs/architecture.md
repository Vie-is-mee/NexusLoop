# Kiến trúc NexusLoop V1.2

```text
Documents / structured input
          ↓
A profile + B requirements
          ↓
Compatibility Engine
          ↓
Hard gates + dependencies
          ↓
Safe candidate set
          ↓
      LLM Router
   ↙   ↓   ↓   ↓   ↘
OpenAI Claude Gemini Compatible Ollama
          ↓
JSON output validator
       ↙      ↘
    hợp lệ    lỗi / ngoài whitelist
       ↓             ↓
   LLM plan   deterministic fallback
       └──────┬──────┘
              ↓
      Human review / edit
              ↓
Evidence result → re-plan
              ↓
Decision Pack + Audit Trail
```

Điểm quan trọng: provider chỉ là **khối suy luận có thể thay thế**. Hard gate, dependency, state machine, quyền con người, validation và fallback đều nằm trong NexusLoop Core.
