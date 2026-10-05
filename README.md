# NexusLoop Ultimate · Industrial Decision OS

NexusLoop là lớp điều phối bằng chứng cho bài toán cộng sinh công nghiệp A → B. Bản Ultimate giữ nguyên lõi quyết định có thể kiểm toán của dự án gốc, nhưng nâng giao diện thành một **phòng điều khiển quyết định**: người dùng có thể nhìn thấy dữ liệu đi vào, cách hệ thống đối chiếu, AI lập kế hoạch, rule/hard gate kiểm soát, bằng chứng quay về, phê duyệt con người và Decision Pack được tạo ra như thế nào.

> Dữ liệu đi kèm repo là dữ liệu mô phỏng. NexusLoop không thay thế cơ quan quản lý, luật sư, phòng thử nghiệm hoặc kỹ sư chuyên môn.

## Chạy nhanh

### Windows

```bat
run_nexusloop.bat
```

Hoặc chạy thủ công:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

Mở: `http://localhost:8000`

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

Mở: `http://localhost:8000`

Giao diện Ultimate được FastAPI phục vụ trực tiếp, **không cần chạy thêm Vite/Node**.

## 4 không gian chính

### 1. Opportunity Scan
- danh mục case thật từ backend;
- trạng thái INVESTIGATING / WAITING HUMAN / PILOT READY / STOP;
- readiness được tính từ compatibility, evidence, gate và approval;
- activity feed lấy từ audit/run thật;
- trạng thái AI provider hiện tại.

### 2. Live Workspace
- dòng vật lý A → B;
- **NexusLoop Live Flow** 9 bước có thể bấm để kiểm tra;
- Inspector cho từng bước;
- Execution Timeline + Replay Run;
- evidence queue và reason/ranking;
- nộp PASS/HOLD/STOP;
- human plan override;
- chỉnh hồ sơ A/B;
- upload JSON / CSV / TXT / PDF;
- custom constraints;
- approvals;
- compatibility matrix;
- dữ liệu thay đổi sẽ làm toàn bộ case recompute thật.

### 3. Decision Studio
- Decision Pack sống;
- Decision Graph;
- Data Lineage: công thức + nguồn tạo ra các con số;
- open risks;
- What-if Simulator chỉ mô phỏng trên UI, không sửa dữ liệu thật;
- mở report để in/lưu PDF.

### 4. Command Center
- system health;
- AI provider/router/fallback;
- execution history;
- Failure Map;
- recovery suggestions;
- autonomy boundary: đâu là việc AI tự động, đâu là việc con người phải xác nhận.

## Luồng quan sát được

```text
Documents / Profiles
        ↓
Read & normalize
        ↓
Compare A ↔ B
        ↓
AI evidence planner
        ↓
Rules & hard gates
        ↓
Generate available actions
        ↓
Rank evidence value
        ↓
Choose next action
        ↓
Human / external evidence
        ↺
Decision Pack
```

Mỗi mutation quan trọng tạo một `RunRecord` có:
- `run_id`;
- action;
- before metrics;
- after metrics;
- duration;
- flow snapshot;
- error component + recovery hint nếu thất bại.

API quan sát mới:

```text
GET /api/overview
GET /api/cases/{case_id}/observability
GET /api/cases/{case_id}/runs
GET /api/runs/{run_id}
```

## Multi‑LLM + fallback

Cấu hình trong `.env` / `.env.example`.

Hỗ trợ:
- Google Gemini;
- OpenAI;
- Anthropic Claude;
- OpenAI-compatible API;
- Ollama/local model;
- deterministic fallback.

LLM chỉ tham gia các phần được phép như đọc tài liệu phi cấu trúc và chọn/giải thích bước bằng chứng trong tập phương án hợp lệ. Hard gate, dependency, state transition và quyền phê duyệt của con người nằm trong NexusLoop Core.

## Kiểm thử

```bash
pytest -q
```

Bản Ultimate hiện có **27 bài kiểm thử** bao phủ lõi cũ và lớp quan sát mới: hard stop, replanning, human override, profile editing, document ingestion, provider routing, report, Live Flow, provenance, replayable run và failure history.

## Cấu trúc quan trọng

```text
main.py                         FastAPI + API + report + Ultimate UI
nexusloop/
  engine.py                     decision engine
  models.py                     domain models
  store.py                      case state + actions
  ai_runtime.py                 multi-LLM + fallback
  observability.py              metrics, lineage, Live Flow, run history
static/
  index.html                    NexusLoop Ultimate UI
  styles.css                    product design system
  app.js                        UI logic + real API integration
nexusloop-source/               React concept gốc được giữ làm tài liệu tham khảo thiết kế
tests/
  test_ultimate_observability.py
```

## Nguyên tắc UI của bản Ultimate

1. Animation chỉ biểu diễn trạng thái thật hoặc replay lịch sử thật.
2. Không hiển thị chuỗi suy nghĩ nội bộ của LLM; chỉ hiển thị input/output có thể kiểm chứng.
3. Không dùng số KPI viết cứng cho dữ liệu nghiệp vụ.
4. Lỗi phải chỉ ra component và hướng khôi phục.
5. Kết quả cuối phải lần ngược được về dữ liệu và phép tính.
6. Human-in-the-loop phải nhìn thấy trên UI, không chỉ ghi trong tài liệu.

Xem thêm: `docs/ultimate-ui-architecture.md` và `ULTIMATE_CHANGELOG.md`.
