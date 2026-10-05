from __future__ import annotations

from html import escape
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from nexusloop.models import (
    ApprovalSubmission,
    ConstraintSubmission,
    EvidenceSubmission,
    PlanOverrideSubmission,
    ProfileUpdate,
)
from nexusloop.observability import RunTracker, case_metrics, live_flow, provenance
from nexusloop.store import CaseStore

BASE = Path(__file__).resolve().parent
store = CaseStore(BASE / "data" / "demo_cases.json")
runs = RunTracker()

app = FastAPI(title="NexusLoop Ultimate", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep legacy static assets available for compatibility and documentation.
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.get("/api/health")
def health():
    ai = store.ai_runtime.status()
    # `version` stays backward compatible with the original API test contract.
    return {
        "status": "ok",
        "mode": "auditable-multi-llm-demo",
        "version": "1.2.0",
        "product_version": "2.0.0-ultimate",
        "ai_active": ai.active,
        "ai_provider": ai.provider,
        "ai_provider_label": ai.provider_label,
        "ai_model": ai.model,
    }


@app.get("/api/ai/status")
def ai_status():
    return store.ai_runtime.status().__dict__


@app.get("/api/ai/providers")
def ai_providers():
    status = store.ai_runtime.status()
    return {
        "requested_provider": status.requested_provider,
        "active_provider": status.provider,
        "active_provider_label": status.provider_label,
        "active_model": status.model,
        "mode": status.mode,
        "providers": status.providers or [],
        "fallback_available": True,
    }


@app.get("/api/sample-input")
def sample_input():
    return FileResponse(
        BASE / "data" / "sample_inputs" / "NexusLoop_demo_input_standard.json",
        media_type="application/json",
        filename="NexusLoop_demo_input_standard.json",
    )


@app.get("/api/overview")
def overview():
    cases = store.list()
    metrics = [case_metrics(c) for c in cases]
    ai = store.ai_runtime.status()
    return {
        "cases": len(cases),
        "pilot_ready": sum(1 for c in cases if c.agent and c.agent.status.value == "PILOT_READY"),
        "investigating": sum(1 for c in cases if c.agent and c.agent.status.value == "INVESTIGATING"),
        "waiting_human": sum(1 for c in cases if c.agent and c.agent.status.value == "WAITING_HUMAN"),
        "stopped": sum(1 for c in cases if c.agent and c.agent.status.value == "STOP"),
        "documents": sum(m["documents"] for m in metrics),
        "avg_readiness": round(sum(m["readiness"] for m in metrics) / max(1, len(metrics))),
        "unresolved": sum(m["unresolved_compatibility"] for m in metrics),
        "ai": {
            "active": ai.active,
            "provider": ai.provider,
            "provider_label": ai.provider_label,
            "model": ai.model,
            "mode": ai.mode,
            "last_error": ai.last_error,
        },
        "recent_runs": runs.list()[:6],
    }


@app.get("/api/cases")
def cases():
    return [
        {
            "id": c.id,
            "title": c.title,
            "short_title": c.short_title,
            "resource": c.resource,
            "supplier": c.supplier,
            "receiver": c.receiver,
            "status": c.agent.status if c.agent else "INTAKE",
            "scenario_label": c.scenario_label,
            "metrics": case_metrics(c),
        }
        for c in store.list()
    ]


@app.get("/api/cases/{case_id}")
def case_detail(case_id: str):
    try:
        return store.get(case_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Case not found")


@app.get("/api/cases/{case_id}/observability")
def case_observability(case_id: str):
    try:
        case = store.get(case_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Case not found")
    ai = store.ai_runtime.status()
    return {
        "case_id": case_id,
        "metrics": case_metrics(case),
        "flow": live_flow(case, ai),
        "provenance": provenance(case),
        "runs": runs.list(case_id)[:12],
        "ai": ai.__dict__,
        "failures": [
            {
                "component": "AI Provider",
                "message": ai.last_error,
                "recoverable": True,
                "suggested_actions": ["Thử lại", "Dùng provider dự phòng", "Tiếp tục bằng deterministic fallback"],
            }
        ] if ai.last_error else [],
    }


@app.get("/api/cases/{case_id}/runs")
def case_runs(case_id: str):
    try:
        store.get(case_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Case not found")
    return runs.list(case_id)


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    run = runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


def _start(case_id: str, action: str, label: str, actor: str = "Người vận hành"):
    try:
        case = store.get(case_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Case not found")
    return runs.start(case, action, label, actor)


def _done(run, case):
    runs.complete(run, case, store.ai_runtime.status())
    return case


@app.post("/api/cases/{case_id}/evidence")
def submit_evidence(case_id: str, payload: EvidenceSubmission):
    run = _start(case_id, "evidence", "Ghi nhận bằng chứng mới", payload.submitted_by)
    try:
        return _done(run, store.submit_evidence(case_id, payload))
    except ValueError as exc:
        runs.fail(run, exc, "Evidence Validator")
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/cases/{case_id}/approvals")
def update_approval(case_id: str, payload: ApprovalSubmission):
    run = _start(case_id, "approval", "Cập nhật phê duyệt con người", payload.approved_by)
    try:
        return _done(run, store.approve(case_id, payload))
    except ValueError as exc:
        runs.fail(run, exc, "Human Approval Gate")
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/cases/{case_id}/profile")
def update_profile(case_id: str, payload: ProfileUpdate):
    run = _start(case_id, "profile", "Chỉnh dữ liệu hồ sơ", payload.edited_by)
    try:
        return _done(run, store.update_profile(case_id, payload))
    except ValueError as exc:
        runs.fail(run, exc, "Profile Validator")
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/cases/{case_id}/plan")
def override_plan(case_id: str, payload: PlanOverrideSubmission):
    run = _start(case_id, "plan", "Lập lại kế hoạch bằng chứng", payload.actor)
    try:
        return _done(run, store.override_plan(case_id, payload))
    except ValueError as exc:
        runs.fail(run, exc, "Evidence Planner")
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/cases/{case_id}/constraints")
def add_constraint(case_id: str, payload: ConstraintSubmission):
    run = _start(case_id, "constraint", "Thêm điều kiện vận hành", payload.actor)
    try:
        return _done(run, store.add_constraint(case_id, payload))
    except ValueError as exc:
        runs.fail(run, exc, "Constraint Engine")
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/cases/{case_id}/documents")
async def upload_document(case_id: str, owner: str = Form(...), file: UploadFile = File(...)):
    run = _start(case_id, "document", f"Đọc tài liệu: {file.filename or 'document'}", "Người tải tài liệu")
    try:
        content = await file.read()
        if len(content) > 5_000_000:
            exc = ValueError("Demo giới hạn file 5 MB")
            runs.fail(run, exc, "Document Ingestion")
            raise HTTPException(status_code=413, detail=str(exc))
        case = store.ingest_document(case_id, owner, file.filename or "document.txt", content)
        return _done(run, case)
    except HTTPException:
        raise
    except ValueError as exc:
        runs.fail(run, exc, "Document Ingestion")
        raise HTTPException(status_code=400, detail=str(exc))


# Backward-compatible alias used by older demo code.
@app.post("/api/cases/{case_id}/upload")
async def upload_document_alias(case_id: str, owner: str = Form("shared"), file: UploadFile = File(...)):
    return await upload_document(case_id, owner, file)


@app.get("/api/cases/{case_id}/decision-pack")
def decision_pack(case_id: str):
    try:
        return store.get(case_id).decision_pack
    except KeyError:
        raise HTTPException(status_code=404, detail="Case not found")


@app.get("/api/cases/{case_id}/proposal")
def get_proposal(case_id: str):
    try:
        case = store.get(case_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Case not found")
    return {
        "title": case.title,
        "summary": case.short_title,
        "status": case.agent.status.value if case.agent else "INTAKE",
        "audit_trail": [a.model_dump() for a in case.audit],
        "supplier": case.supplier,
        "receiver": case.receiver,
        "decision_pack": case.decision_pack,
        "metrics": case_metrics(case),
    }


@app.post("/api/cases/{case_id}/reset")
def reset_case(case_id: str):
    try:
        case = store.reset(case_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Case not found")
    runs.clear_case(case_id)
    run = runs.start(case, "reset", "Đặt lại hồ sơ demo", "System")
    return _done(run, case)


@app.get("/api/cases/{case_id}/report", response_class=HTMLResponse)
def report(case_id: str):
    try:
        case = store.get(case_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Case not found")
    pack = case.decision_pack
    metrics = case_metrics(case)
    compat_rows = "".join(
        f"<tr><td>{escape(x.label)}</td><td><span class='pill {escape(x.status.value.lower())}'>{escape(x.status.value)}</span></td><td>{escape(x.explanation)}</td></tr>"
        for x in case.compatibility
    )
    audit_rows = "".join(
        f"<li><time>{escape(a.ts)}</time><b>{escape(a.event)}</b><span>{escape(a.detail)}</span></li>" for a in case.audit[:12]
    )
    return HTMLResponse(f"""<!doctype html><html lang='vi'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>NexusLoop Decision Pack</title>
    <style>
      :root{{--ink:#15231e;--muted:#66746e;--line:#dde5e1;--green:#0d6b4d;--soft:#f4f8f6;--amber:#a46716}}
      *{{box-sizing:border-box}}body{{font-family:Inter,Arial,sans-serif;max-width:1020px;margin:0 auto;padding:42px;color:var(--ink);line-height:1.5;background:#fbfdfc}}
      header{{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;border-bottom:1px solid var(--line);padding-bottom:24px}}h1{{font-size:30px;margin:0}}h2{{font-size:18px;margin-top:30px}}.eyebrow{{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--green);font-weight:800}}
      .box{{border:1px solid var(--line);background:white;border-radius:18px;padding:22px;margin:22px 0;box-shadow:0 18px 50px -42px #0d6b4d}}.decision{{font-size:26px;color:var(--green);font-weight:800}}
      .metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:18px 0}}.metric{{padding:14px;border-radius:12px;background:var(--soft)}}.metric b{{font-size:22px;display:block}}.metric small{{color:var(--muted)}}
      table{{border-collapse:collapse;width:100%;background:white;border:1px solid var(--line);border-radius:14px;overflow:hidden}}td,th{{border-bottom:1px solid var(--line);padding:11px;text-align:left;vertical-align:top}}th{{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}}.pill{{font-size:10px;font-weight:800;padding:4px 7px;border-radius:999px;background:var(--soft)}}.match,.pass{{color:var(--green)}}.conflict,.stop{{color:#a33}}.gap,.unknown,.hold{{color:var(--amber)}}
      ul.timeline{{list-style:none;padding:0}}.timeline li{{display:grid;grid-template-columns:150px 180px 1fr;gap:12px;padding:10px 0;border-bottom:1px solid var(--line)}}time{{font-size:11px;color:var(--muted)}}button{{border:0;background:var(--green);color:white;padding:10px 14px;border-radius:10px;font-weight:700}}@media(max-width:700px){{body{{padding:22px}}.metrics{{grid-template-columns:repeat(2,1fr)}}.timeline li{{grid-template-columns:1fr}}}}@media print{{button{{display:none}}body{{background:white;padding:0}}}}
    </style></head><body>
    <header><div><div class='eyebrow'>NexusLoop · Decision intelligence</div><h1>Bộ hồ sơ quyết định</h1><p>{escape(case.title)}</p></div><button onclick='window.print()'>In / lưu PDF</button></header>
    <div class='box'><div class='eyebrow'>Kết luận hiện tại</div><div class='decision'>{escape(pack.decision)}</div><h2>{escape(pack.headline)}</h2><p>{escape(pack.summary)}</p></div>
    <div class='metrics'><div class='metric'><b>{metrics['readiness']}%</b><small>Mức sẵn sàng</small></div><div class='metric'><b>{metrics['compatibility']}%</b><small>Tương thích</small></div><div class='metric'><b>{metrics['evidence']}%</b><small>Bằng chứng</small></div><div class='metric'><b>{metrics['approvals']}%</b><small>Phê duyệt</small></div></div>
    <h2>Đầu vào A → B</h2><div class='box'><p><b>A:</b> {escape(str(case.supplier_profile.quantity_per_day))} {escape(case.supplier_profile.quantity_unit)} &nbsp; → &nbsp; <b>B cần:</b> {escape(str(case.receiver_profile.demand_per_day))} {escape(case.receiver_profile.demand_unit)}</p><p><b>Lưu lượng ghép được:</b> {escape(str(pack.matched_volume_per_day))} {escape(case.supplier_profile.quantity_unit)}</p></div>
    <h2>Kết quả đối chiếu</h2><table><tr><th>Nhóm</th><th>Trạng thái</th><th>Giải thích</th></tr>{compat_rows}</table>
    <h2>Đầu ra cho bên B</h2><ul>{''.join('<li>'+escape(x)+'</li>' for x in pack.receiver_output)}</ul>
    <h2>Điều kiện / rủi ro còn mở</h2><ul>{''.join('<li>'+escape(x)+'</li>' for x in (pack.open_risks or pack.conditions_for_pilot))}</ul>
    <h2>Nhật ký quyết định gần nhất</h2><ul class='timeline'>{audit_rows}</ul>
    <p><small>{escape(pack.disclaimer)}</small></p></body></html>""")


# NexusLoop Ultimate is deliberately served by the same FastAPI process.
# This avoids a second frontend server in demos and ensures /api always shares the same origin.
@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")
