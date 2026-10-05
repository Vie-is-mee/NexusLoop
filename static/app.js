const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const num = (v, digits=0) => (v == null || Number.isNaN(Number(v))) ? '—' : Number(v).toLocaleString('vi-VN',{maximumFractionDigits:digits});
const fmtTime = (iso) => { try { return new Date(iso).toLocaleString('vi-VN',{hour:'2-digit',minute:'2-digit',day:'2-digit',month:'2-digit'}); } catch { return iso || '—'; } };
const STATUS_LABEL = {INTAKE:'Tiếp nhận',INVESTIGATING:'Đang xác minh',WAITING_HUMAN:'Chờ phê duyệt',PILOT_READY:'Sẵn sàng Pilot',HOLD:'Tạm giữ',STOP:'Dừng'};
const FIT_LABEL = {MATCH:'Phù hợp',GAP:'Còn thiếu',CONFLICT:'Xung đột',UNKNOWN:'Chưa đủ dữ liệu'};
const GATE_LABEL = {PASS:'PASS',HOLD:'HOLD',STOP:'STOP',UNKNOWN:'CHƯA XÁC MINH'};

const state = {
  view:'scan', filter:'ALL', cases:[], overview:null, health:null, ai:null, providers:null,
  currentId:null, current:null, obs:null, selectedFlowId:null, workspacePane:'evidence',
  guidedIndex:0, replayTimers:[], simulator:null,
};

async function api(path, options={}) {
  const opts = {...options};
  if (opts.body && !(opts.body instanceof FormData) && !opts.headers) opts.headers = {'Content-Type':'application/json'};
  const res = await fetch(path, opts);
  let payload = null;
  const type = res.headers.get('content-type') || '';
  if (type.includes('application/json')) payload = await res.json(); else payload = await res.text();
  if (!res.ok) {
    const message = payload?.detail || payload?.message || (typeof payload === 'string' ? payload : `HTTP ${res.status}`);
    const err = new Error(message); err.status = res.status; throw err;
  }
  return payload;
}

function toast(message) {
  const el = $('toast'); el.textContent = message; el.classList.add('show'); clearTimeout(toast._t);
  toast._t = setTimeout(()=>el.classList.remove('show'), 3200);
}
function setBusy(show, title='Đang xử lý…', detail='Dữ liệu đang được chuyển qua các lớp xử lý thật của hệ thống.') {
  $('operationOverlay').hidden = !show; $('operationTitle').textContent = title; $('operationDetail').textContent = detail;
}
function statusChip(status) { return `<span class="status-chip status-${esc(status)}">${esc(STATUS_LABEL[status] || status)}</span>`; }
function percentBar(label, value, hint='') { const v=Math.max(0,Math.min(100,Number(value)||0)); return `<div class="metric-card"><div class="metric-top"><div><small>${esc(label)}</small>${hint?`<div class="metric-hint">${esc(hint)}</div>`:''}</div><b>${v}%</b></div><div class="bar"><i style="width:${v}%"></i></div></div>`; }

function setView(view) {
  state.view = view;
  document.querySelectorAll('.app-view').forEach(el=>el.classList.remove('is-visible'));
  const target = $('view'+view[0].toUpperCase()+view.slice(1)); if (target) target.classList.add('is-visible');
  document.querySelectorAll('#mainNav button').forEach(b=>b.classList.toggle('is-active', b.dataset.view===view));
  if (view === 'decision') renderDecision();
  if (view === 'command') renderCommand();
  window.scrollTo({top:0,behavior:'smooth'});
}

async function boot() {
  try {
    const [health, ai, providers, overview, cases] = await Promise.all([
      api('/api/health'), api('/api/ai/status'), api('/api/ai/providers'), api('/api/overview'), api('/api/cases')
    ]);
    state.health=health; state.ai=ai; state.providers=providers; state.overview=overview; state.cases=cases;
    state.currentId = cases[0]?.id || null;
    await loadCurrent(false);
    renderHeader(); renderScan(); renderCommand();
  } catch (e) {
    document.querySelector('.app-shell').innerHTML = `<section class="surface-card"><p class="eyebrow">Startup error</p><h1>NexusLoop không thể khởi động</h1><p>${esc(e.message)}</p><p>Hãy chắc chắn backend FastAPI đang chạy và mở website từ cùng server.</p></section>`;
  }
}

async function refreshTopLevel() {
  const [health, ai, providers, overview, cases] = await Promise.all([
    api('/api/health'), api('/api/ai/status'), api('/api/ai/providers'), api('/api/overview'), api('/api/cases')
  ]);
  Object.assign(state,{health,ai,providers,overview,cases});
  renderHeader(); renderScan();
}

async function loadCurrent(render=true) {
  if (!state.currentId) return;
  const [current, obs] = await Promise.all([
    api(`/api/cases/${state.currentId}`), api(`/api/cases/${state.currentId}/observability`)
  ]);
  state.current=current; state.obs=obs;
  if (!state.selectedFlowId) state.selectedFlowId = obs.flow.find(x=>x.status==='active')?.id || obs.flow[0]?.id || null;
  if (render) { renderWorkspace(); renderDecision(); renderCommand(); }
}

function renderHeader() {
  const ai=state.ai||{}; const badge=$('aiBadge');
  badge.classList.toggle('is-live', !!ai.active); badge.classList.toggle('is-error', !!ai.last_error);
  badge.querySelector('span').textContent = ai.active ? `${ai.provider_label || ai.provider} · ${ai.model || 'model'}` : (ai.last_error ? 'AI fallback đang hoạt động' : 'Deterministic fallback');
  $('systemHealth').textContent = state.health?.status === 'ok' ? 'Healthy' : 'Needs attention';
  $('productVersion').textContent = state.health?.product_version || 'Ultimate';
}

function renderScan() {
  const o=state.overview||{};
  $('overviewKpis').innerHTML = [
    [o.cases??0,'Cơ hội đang theo dõi','Portfolio'], [o.avg_readiness??0+'%','Mức sẵn sàng TB','Tính từ trạng thái thật'],
    [o.documents??0,'Tài liệu đã đọc','Nguồn dữ liệu'], [o.unresolved??0,'Khoảng trống còn mở','Cần làm rõ']
  ].map(([v,l,e])=>`<div class="mini-kpi"><b>${esc(v)}</b><span>${esc(l)}</span><em>${esc(e)}</em></div>`).join('');

  const filtered = state.cases.filter(c=>state.filter==='ALL' || String(c.status)===state.filter);
  $('caseBoard').innerHTML = filtered.length ? filtered.map(c=>{
    const m=c.metrics||{}; const status=String(c.status);
    return `<button class="case-card" data-case="${esc(c.id)}"><div><div class="case-id">${esc(c.id)}</div><h3>${esc(c.short_title||c.title)}</h3><div class="case-pair">${esc(c.supplier)} → ${esc(c.receiver)}</div><p>${esc(c.scenario_label||c.resource)}</p></div><div class="readiness-num"><b>${esc(m.readiness??0)}%</b><span>Readiness</span></div><div>${statusChip(status)}</div><div class="case-arrow">›</div></button>`;
  }).join('') : `<div class="surface-card"><p>Không có case phù hợp bộ lọc.</p></div>`;
  document.querySelectorAll('.case-card').forEach(b=>b.onclick=()=>openCase(b.dataset.case));

  const activity = (state.current?.audit||[]).slice(0,5);
  const runs=(state.overview?.recent_runs||[]).slice(0,3);
  const merged = runs.length ? runs.map(r=>({event:r.label,detail:`${r.status==='completed'?'Hoàn tất':'Lỗi'} · ${r.duration_ms??0} ms`,ts:r.ended_at||r.started_at,severity:r.status==='failed'?'critical':'info'})) : activity;
  $('globalActivity').innerHTML = merged.length ? merged.map(x=>`<div class="activity-item"><i style="background:${x.severity==='critical'?'var(--danger)':'var(--primary)'}"></i><div><b>${esc(x.event)}</b><p>${esc(x.detail)}</p><time>${esc(fmtTime(x.ts))}</time></div></div>`).join('') : `<div class="activity-item"><i></i><div><b>Hệ thống đã sẵn sàng</b><p>Chưa có hành động mới trong phiên này.</p></div></div>`;
  const ai=state.ai||{};
  $('aiRoutingMini').innerHTML = `<div class="ai-route-mini"><strong>${esc(ai.active ? ai.provider_label : 'Deterministic fallback')}</strong><small>${esc(ai.active ? (ai.model||'') : 'Logic lõi vẫn chạy khi không có LLM.')}</small></div>`;
}

async function openCase(id) {
  state.currentId=id; state.selectedFlowId=null; state.simulator=null;
  setBusy(true,'Đang mở workspace','NexusLoop đang đồng bộ hồ sơ, luồng quyết định và lịch sử thực thi.');
  try { await loadCurrent(false); renderWorkspace(); renderDecision(); renderCommand(); setView('workspace'); }
  finally { setBusy(false); }
}

function renderWorkspace() {
  const c=state.current, obs=state.obs; if(!c||!obs)return;
  $('workspaceKicker').textContent=`${c.id} · ${c.scenario_label}`;
  $('workspaceTitle').textContent=c.title; $('workspaceDesc').textContent=c.description;
  $('workspaceStatus').innerHTML=statusChip(c.agent?.status||'INTAKE');
  renderResourceMap(); renderLiveFlow(); renderMetrics(); renderEvidence(); renderCompatibility(); renderData(); renderApprovals(); renderInspector();
}

function renderResourceMap() {
  const c=state.current; const p=c.supplier_profile, r=c.receiver_profile, pack=c.decision_pack||{};
  $('resourceMap').innerHTML = `<div class="resource-node"><small>Source A</small><b>${esc(c.supplier)}</b><p>${esc(p.resource_name)} · ${num(p.quantity_per_day,1)} ${esc(p.quantity_unit)}</p></div><div class="resource-arrow"><i></i></div><div class="resource-node"><small>NexusLoop candidate flow</small><b>${num(pack.matched_volume_per_day,1)} ${esc(p.quantity_unit)}</b><p>Khớp theo nguồn khả dụng và nhu cầu khai báo.</p></div><div class="resource-arrow"><i></i></div><div class="resource-node target"><small>Demand B</small><b>${esc(c.receiver)}</b><p>${num(r.demand_per_day,1)} ${esc(r.demand_unit)} · ${esc(r.intended_use)}</p></div>`;
}

function renderLiveFlow() {
  const flow=state.obs?.flow||[];
  $('liveFlow').innerHTML = flow.map((s,i)=>`${i?'<div class="flow-connector"></div>':''}<button class="flow-node node-${esc(s.status)} node-${esc(s.layer)} ${state.selectedFlowId===s.id?'is-selected':''}" data-flow-id="${esc(s.id)}"><span class="node-status"></span><small>${esc(s.layer)}</small><b>${esc(s.label)}</b><p>${esc(s.summary)}</p></button>`).join('');
  document.querySelectorAll('.flow-node').forEach(b=>b.onclick=()=>{state.selectedFlowId=b.dataset.flowId;renderLiveFlow();renderInspector();});
  const runs=state.obs?.runs||[];
  $('flowRunBadge').textContent = runs[0] ? `${runs[0].id} · ${runs[0].duration_ms??0} ms` : 'Current state';
  $('executionRail').innerHTML = runs.slice(0,4).map(r=>`<button class="rail-run" data-run="${esc(r.id)}"><b>${esc(r.label)}</b><span>${esc(r.id)} · ${esc(r.status)} · ${r.duration_ms??0} ms</span></button>`).join('') || `<div class="rail-run"><b>Chưa có run trong phiên</b><span>Hành động tiếp theo sẽ xuất hiện ở đây.</span></div>`;
  document.querySelectorAll('.rail-run[data-run]').forEach(b=>b.onclick=()=>replayById(b.dataset.run));
}

function renderMetrics() {
  const m=state.obs?.metrics||{};
  $('decisionMetrics').innerHTML = percentBar('Mức sẵn sàng',m.readiness,'Tổng hợp minh bạch') + percentBar('Tương thích',m.compatibility,`${m.matches||0} nhóm phù hợp`) + percentBar('Bằng chứng',m.evidence,'Gate đã có kết quả') + percentBar('Điều kiện',m.gates,`${m.passed_gates||0} gate PASS`) + percentBar('Phê duyệt',m.approvals,`${m.approved||0}/${m.required_approvals||0}`);
}

function assessmentMap() { return Object.fromEntries((state.current?.agent?.candidate_assessments||[]).map(x=>[x.candidate_id,x])); }
function renderEvidence() {
  const c=state.current, map=assessmentMap();
  $('nextEvidenceTag').textContent = c.agent?.next_evidence_label ? `AI: ${c.agent.priority_band || 'ưu tiên'}` : 'Không có bước mới';
  $('evidenceQueue').innerHTML=(c.candidates||[]).map((cand,index)=>{
    const a=map[cand.id]||{}; const gate=c.gates.find(g=>g.id===cand.gate_id); const selected=c.agent?.next_evidence_id===cand.id;
    const resolved=gate && gate.status!=='UNKNOWN';
    return `<div class="evidence-card ${selected?'is-selected':''}"><div class="priority-box">${selected?'NEXT':'P'+(index+1)}</div><div><h4>${esc(cand.label)}</h4><p>${esc(cand.description)}</p><div class="evidence-meta"><span>${esc(a.priority_band||'—')}</span><span>${esc(cand.cost_label)}</span><span>${esc(cand.time_label)}</span><span>${cand.hard_gate?'HARD GATE':'SOFT GATE'}</span>${gate?`<span>${esc(GATE_LABEL[gate.status]||gate.status)}</span>`:''}</div></div><div class="evidence-actions">${resolved?`<span class="fit-chip fit-${gate.status==='PASS'?'MATCH':gate.status==='STOP'?'CONFLICT':'GAP'}">${esc(gate.status)}</span>`:`<button class="btn ${a.available?'primary':'ghost'} small evidence-submit" data-candidate="${esc(cand.id)}" ${a.available?'':'disabled'}>Ghi kết quả</button>`}</div></div>`;
  }).join('');
  document.querySelectorAll('.evidence-submit').forEach(b=>b.onclick=()=>openEvidence(b.dataset.candidate));
  const available=(c.agent?.candidate_assessments||[]).filter(x=>x.available);
  $('overrideCandidate').innerHTML = available.map(x=>`<option value="${esc(x.candidate_id)}" ${x.candidate_id===c.agent?.next_evidence_id?'selected':''}>${esc(x.label)}</option>`).join('') || '<option value="">Không có phương án khả dụng</option>';
}

function renderCompatibility() {
  $('compatibilityMatrix').innerHTML=(state.current?.compatibility||[]).map(x=>`<div class="compat-row"><div><h4>${esc(x.label)}</h4><span class="fit-chip fit-${esc(x.status)}">${esc(FIT_LABEL[x.status]||x.status)}</span></div><div><p><b>A:</b> ${esc(x.supplier_value)}</p><p><b>B:</b> ${esc(x.receiver_requirement)}</p></div><div><p>${esc(x.explanation)}</p>${x.missing_evidence?`<p><b>Cần:</b> ${esc(x.missing_evidence)}</p>`:''}</div></div>`).join('');
}

function profileRows(side) {
  const p=side==='supplier'?state.current.supplier_profile:state.current.receiver_profile;
  const fields=side==='supplier' ? [['resource_name','Tài nguyên'],['process_source','Nguồn phát sinh'],['quantity_per_day','Lưu lượng/ngày'],['schedule','Lịch vận hành'],['stability','Độ ổn định'],['current_route','Tuyến hiện tại'],['location','Vị trí']] : [['intended_use','Mục đích sử dụng'],['demand_per_day','Nhu cầu/ngày'],['schedule','Lịch nhu cầu'],['continuity_requirement','Yêu cầu liên tục'],['location','Vị trí']];
  return fields.map(([k,l])=>`<div class="profile-row"><span>${esc(l)}</span><b>${esc(p[k]??'Chưa có')}</b></div>`).join('');
}
function renderData() {
  const c=state.current;
  $('supplierName').textContent=c.supplier; $('receiverName').textContent=c.receiver;
  $('supplierProfile').innerHTML=profileRows('supplier'); $('receiverProfile').innerHTML=profileRows('receiver');
  $('documentCount').textContent=`${c.documents.length} tệp`;
  $('documentList').innerHTML=c.documents.map(d=>`<div class="document-item"><b>${esc(d.filename)}</b><p>${esc(d.summary)}</p><span>${esc(d.analysis_method)} · ${esc(d.owner)}</span></div>`).join('') || '<p>Chưa có tài liệu.</p>';
}
function renderApprovals() {
  const c=state.current; const candidateGateIds=new Set(c.candidates.map(x=>x.gate_id));
  const gatesReady=c.gates.filter(g=>candidateGateIds.has(g.id)).every(g=>g.status==='PASS');
  $('approvalList').innerHTML=c.approvals.map(a=>`<div class="approval-row"><div><b>${esc(a.label)}</b><p>${a.approved?`Đã xác nhận bởi ${esc(a.approved_by||'người duyệt')}.`:gatesReady?'Các bước kiểm tra đã PASS; có thể xác nhận.':'Chờ các bước kiểm tra trước đó đạt.'}</p></div><div><span class="approval-state ${a.approved?'ok':''}">${a.approved?'ĐÃ DUYỆT':gatesReady?'CHỜ DUYỆT':'CHƯA MỞ'}</span><button class="btn ${a.approved?'ghost':'primary'} small approval-btn" data-role="${esc(a.role)}" data-approved="${a.approved}" ${(!gatesReady&&!a.approved)?'disabled':''}>${a.approved?'Thu hồi':'Xác nhận'}</button></div></div>`).join('');
  document.querySelectorAll('.approval-btn').forEach(b=>b.onclick=()=>toggleApproval(b.dataset.role,b.dataset.approved==='true'));
  const cc=c.custom_constraints||[];
  $('constraintList').innerHTML=cc.length?cc.map(x=>`<div class="constraint-row"><div><b>${esc(x.label)} ${x.hard?'· HARD':''}</b><p>${esc(x.description)}</p></div><span class="fit-chip fit-${x.status==='PASS'?'MATCH':x.status==='STOP'?'CONFLICT':'UNKNOWN'}">${esc(x.status)}</span></div>`).join(''):'<p style="font-size:10px;color:var(--muted)">Chưa có điều kiện tùy chỉnh.</p>';
}

function flowInspectData(id) {
  const c=state.current, obs=state.obs, step=obs.flow.find(x=>x.id===id);
  if(!step)return null;
  const out={...step, sections:[]};
  if(id==='ingest') out.sections=[{t:'Input',p:`${c.documents.length} tài liệu · hồ sơ ${c.supplier} và ${c.receiver}`},{t:'Documents',list:c.documents.map(d=>`${d.filename} · ${d.analysis_method}`)}];
  else if(id==='compare') out.sections=[{t:'Input',p:'Supplier profile + receiver requirements'},{t:'Output',list:c.compatibility.map(x=>`${x.label}: ${x.status}`)}];
  else if(id==='ai') out.sections=[{t:'Provider',p:`${obs.ai.active?obs.ai.provider_label:'Deterministic fallback'} · ${obs.ai.model||'rule-based'}`},{t:'Planner output',list:(c.agent?.rationale||[]).slice(0,5)},{t:'Mode',p:c.agent?.planner_mode||'—'}];
  else if(id==='rules') out.sections=[{t:'Gates',list:c.gates.map(g=>`${g.label}: ${g.status}${g.hard_gate?' · HARD':''}`)}];
  else if(id==='options'||id==='rank') out.sections=[{t:'Candidates',list:(c.agent?.candidate_assessments||[]).map(a=>`${a.label}: ${a.priority_band} · score ${a.score}`)}];
  else if(id==='decide') out.sections=[{t:'Selected',p:c.agent?.next_evidence_label||c.agent?.blocked_reason||'Chờ phê duyệt'},{t:'Why',list:(c.agent?.rationale||[]).slice(0,6)}];
  else if(id==='act') { const cand=c.candidates.find(x=>x.id===c.agent?.next_evidence_id); out.sections=[{t:'Owner',p:cand?.action_owner||'Không có nhiệm vụ mới'},{t:'Expected evidence',p:cand?.source_hint||'—'}]; }
  else if(id==='pack') out.sections=[{t:'Decision',p:c.decision_pack?.decision||'—'},{t:'Summary',p:c.decision_pack?.summary||'—'},{t:'Open risks',list:c.decision_pack?.open_risks||[]}];
  return out;
}
function renderInspector() {
  const data=flowInspectData(state.selectedFlowId); if(!data)return;
  $('inspectorTitle').textContent=data.label; $('inspectorState').style.background = data.status==='blocked'?'var(--danger)':data.status==='active'?'var(--primary2)':data.status==='done'?'var(--success)':'#bdc7c2';
  let html=`<div class="inspect-section"><small>Status</small><p><b>${esc(data.status.toUpperCase())}</b> · ${esc(data.summary)}</p></div>`;
  (data.sections||[]).forEach(s=>{html+=`<div class="inspect-section"><small>${esc(s.t)}</small>${s.p?`<p>${esc(s.p)}</p>`:''}${s.list?.length?`<ul class="inspect-list">${s.list.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`:''}</div>`;});
  const failure=(state.obs?.failures||[]).find(f=>data.id==='ai');
  if(failure) html+=`<div class="inspect-section"><small>Failure</small><div class="error-box"><b>${esc(failure.component)}</b><p>${esc(failure.message)}</p></div><div class="recovery-list"><button class="btn ghost small" onclick="requestReplan()">Chạy lại bằng fallback / provider khả dụng</button></div></div>`;
  $('inspectorBody').innerHTML=html;
}

function renderDecision() {
  const c=state.current, obs=state.obs; if(!c||!obs)return; const p=c.decision_pack||{},m=obs.metrics||{};
  $('decisionHero').innerHTML=`<div><p class="eyebrow">Current recommendation</p><h2>${esc(p.headline||'Decision Pack')}</h2><p>${esc(p.summary||'')}</p><div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:14px">${statusChip(c.agent?.status||'INTAKE')}<span class="muted-tag">Readiness ${m.readiness||0}%</span><span class="muted-tag">Evidence ${m.evidence||0}%</span></div></div><div class="decision-pill"><small>Decision</small><b>${esc(p.decision||c.agent?.status||'—')}</b></div>`;
  $('decisionGraph').innerHTML=`<div class="graph-inputs"><div class="graph-node"><small>Tương thích</small><b>${m.compatibility||0}%</b></div><div class="graph-node"><small>Bằng chứng</small><b>${m.evidence||0}%</b></div><div class="graph-node"><small>Điều kiện</small><b>${m.gates||0}%</b></div><div class="graph-node"><small>Phê duyệt</small><b>${m.approvals||0}%</b></div></div><div class="graph-join">→</div><div class="graph-decision"><small>NexusLoop Core</small><b>${esc(p.decision||'—')}</b><small style="margin-top:7px">Hard gate luôn có quyền chặn</small></div>`;
  $('provenanceList').innerHTML=(obs.provenance||[]).map(x=>`<button class="provenance-item"><div><h4>${esc(x.label)}</h4><p>${esc(x.formula)}</p><div class="prov-detail" hidden>${x.sources.map(s=>`${esc(s.label)} = ${esc(s.value)} · ${esc(s.source)}`).join('<br>')}</div></div><div class="provenance-value">${num(x.value,1)} ${esc(x.unit||'')}</div></button>`).join('') || '<p>Chưa có dữ liệu truy nguyên.</p>';
  document.querySelectorAll('.provenance-item').forEach(b=>b.onclick=()=>{const d=b.querySelector('.prov-detail');d.hidden=!d.hidden;});
  const risks=p.open_risks?.length?p.open_risks:p.conditions_for_pilot||[];
  $('openRisks').innerHTML=risks.length?risks.map(r=>`<div class="risk-item"><i></i><span>${esc(r)}</span></div>`).join(''):`<div class="risk-empty">Không còn rủi ro mở trong Decision Pack hiện tại.</div>`;
  renderSimulator();
}

function renderSimulator() {
  const c=state.current;if(!c)return; const s=c.supplier_profile.quantity_per_day||0,d=c.receiver_profile.demand_per_day||0;
  if(!state.simulator) state.simulator={supply:s,demand:d};
  const sim=state.simulator, matched=Math.min(sim.supply,sim.demand), coverage=sim.demand?Math.min(100,matched/sim.demand*100):0,util=sim.supply?Math.min(100,matched/sim.supply*100):0;
  $('simulator').innerHTML=`<div class="sim-row"><label><span>Nguồn A</span><b>${num(sim.supply)} m³/ngày</b></label><input id="simSupply" type="range" min="0" max="${Math.max(1000,s*2,d*2)}" step="10" value="${sim.supply}"></div><div class="sim-row"><label><span>Nhu cầu B</span><b>${num(sim.demand)} m³/ngày</b></label><input id="simDemand" type="range" min="0" max="${Math.max(1000,s*2,d*2)}" step="10" value="${sim.demand}"></div><div class="sim-output"><div><b>${num(matched)}</b><span>m³/ngày ghép được</span></div><div><b>${num(coverage)}%</b><span>đáp ứng nhu cầu B</span></div><div><b>${num(util)}%</b><span>sử dụng nguồn A</span></div><div><b>${sim.supply>=sim.demand?'MATCH':'GAP'}</b><span>đánh giá lượng</span></div></div><p style="font-size:9px;color:var(--muted);line-height:1.5;margin:13px 0 0">Mô phỏng này chỉ thay đổi bản xem trước; không ghi vào hồ sơ. Muốn áp dụng thật, hãy chỉnh hồ sơ A/B trong Workspace.</p>`;
  $('simSupply').oninput=e=>{state.simulator.supply=Number(e.target.value);renderSimulator();}; $('simDemand').oninput=e=>{state.simulator.demand=Number(e.target.value);renderSimulator();};
}

function renderCommand() {
  const o=state.overview||{},obs=state.obs||{},ai=state.ai||{},runs=obs.runs||[];
  const completed=runs.filter(r=>r.status==='completed'), avg=completed.length?Math.round(completed.reduce((a,r)=>a+(r.duration_ms||0),0)/completed.length):0;
  $('commandKpis').innerHTML=[['System',state.health?.status==='ok'?'HEALTHY':'CHECK','Backend'],['AI',ai.active?'ONLINE':'FALLBACK',ai.provider_label||'Deterministic'],['Runs',runs.length,'Case hiện tại'],['Avg run',avg+' ms','Phiên hiện tại'],['Errors',runs.filter(r=>r.status==='failed').length,'Run lỗi']].map(([l,v,h])=>`<div class="command-kpi"><small>${esc(l)}</small><b>${esc(v)}</b><span style="font-size:8px;color:var(--muted)">${esc(h)}</span></div>`).join('');
  $('commandAiStatus').textContent=ai.active?'ONLINE':'FALLBACK'; $('commandAiStatus').style.background=ai.active?'var(--success-soft)':'var(--warning-soft)'; $('commandAiStatus').style.color=ai.active?'var(--success)':'var(--warning)';
  const ps=state.providers?.providers||[];
  $('providerFlow').innerHTML = ps.length ? ps.map((p,i)=>`${i?'<div class="provider-arrow">→</div>':''}<div class="provider-node ${p.id===state.providers.active_provider?'active':''} ${p.last_error?'error':''}"><small>${p.id===state.providers.active_provider?'Active':'Available'}</small><b>${esc(p.label||p.id)}</b><p>${esc(p.model||'')}${p.configured===false?' · chưa cấu hình':''}</p></div>`).join('') : `<div class="provider-node active"><small>Active</small><b>${esc(ai.active?ai.provider_label:'Deterministic fallback')}</b><p>${esc(ai.model||'NexusLoop Core')}</p></div>`;
  $('runHistory').innerHTML=runs.length?runs.map(r=>`<div class="run-row"><code>${esc(r.id)}</code><div><b>${esc(r.label)}</b><small>${esc(fmtTime(r.started_at))}</small></div><span class="run-status run-${esc(r.status)}">${esc(r.status)}</span><small>${r.duration_ms??0} ms</small><button class="text-btn run-replay" data-run="${esc(r.id)}">Replay</button></div>`).join(''):`<p style="font-size:10px;color:var(--muted)">Chưa có run nào trong phiên. Hãy chỉnh dữ liệu, nộp bằng chứng hoặc tải tài liệu.</p>`;
  document.querySelectorAll('.run-replay').forEach(b=>b.onclick=()=>replayById(b.dataset.run));
  const failures=[...(obs.failures||[]),...runs.filter(r=>r.status==='failed'&&r.error).map(r=>r.error)];
  $('failureMap').innerHTML=failures.length?failures.map(f=>`<div class="failure-card"><b>${esc(f.component||'Unknown component')}</b><p>${esc(f.message||'Unknown error')}</p>${f.suggested_actions?.length?`<ul>${f.suggested_actions.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`:''}</div>`).join(''):`<div class="failure-good"><b>✓ Không có lỗi đang mở</b><br>Provider, Core và các bước quyết định hiện không báo lỗi trong case này.</div>`;
}

async function runMutation({path,method='POST',body,title,detail,success}) {
  setBusy(true,title,detail);
  try {
    const result=await api(path,{method,body});
    await Promise.all([loadCurrent(false), refreshTopLevel()]);
    renderWorkspace();renderDecision();renderCommand();
    setBusy(false); toast(success||'Đã cập nhật hệ thống.');
    const latest=state.obs?.runs?.[0]; if(latest?.status==='completed') setTimeout(()=>replayRun(latest,false),120);
    return result;
  } catch(e) {
    setBusy(false); await loadCurrent(false).catch(()=>{}); renderWorkspace();renderCommand(); toast(`Lỗi: ${e.message}`); setView('command'); return null;
  }
}

function openEvidence(candidateId) {
  const c=state.current.candidates.find(x=>x.id===candidateId); if(!c)return;
  $('evidenceId').value=c.id; $('evidenceDialogTitle').textContent=c.label; $('evidenceDialogDesc').textContent=c.description; $('evidenceSource').value=c.source_hint||'Xác nhận chuyên gia'; $('evidenceNote').value=''; document.querySelector('input[name=evidenceOutcome][value=PASS]').checked=true; $('evidenceDialog').showModal();
}
async function submitEvidence() {
  const outcome=document.querySelector('input[name=evidenceOutcome]:checked').value;
  await runMutation({path:`/api/cases/${state.currentId}/evidence`,body:JSON.stringify({evidence_id:$('evidenceId').value,outcome,source:$('evidenceSource').value,note:$('evidenceNote').value,submitted_by:'Người vận hành'}),title:'Đang ghi nhận bằng chứng',detail:'Gate được cập nhật → Compatibility chạy lại → Evidence Planner lập kế hoạch mới.',success:'Bằng chứng đã được ghi nhận và NexusLoop đã lập lại kế hoạch.'});
  $('evidenceDialog').close();
}
function openProfile(side) {
  const p=side==='supplier'?state.current.supplier_profile:state.current.receiver_profile;
  const fields=side==='supplier'?[['quantity_per_day','Lưu lượng/ngày'],['schedule','Lịch phát sinh'],['stability','Độ ổn định'],['current_route','Tuyến hiện tại'],['location','Vị trí']]:[['demand_per_day','Nhu cầu/ngày'],['schedule','Lịch nhu cầu'],['continuity_requirement','Yêu cầu liên tục'],['intended_use','Mục đích sử dụng'],['location','Vị trí']];
  $('profileSide').value=side;$('profileDialogTitle').textContent=side==='supplier'?'Chỉnh hồ sơ bên A':'Chỉnh yêu cầu bên B';$('profileField').innerHTML=fields.map(([v,l])=>`<option value="${v}">${l}</option>`).join('');
  const sync=()=>{$('profileValue').value=p[$('profileField').value]??''};$('profileField').onchange=sync;sync();$('profileDialog').showModal();
}
async function saveProfile() {
  let value=$('profileValue').value; const field=$('profileField').value;if(['quantity_per_day','demand_per_day'].includes(field)) value=Number(value);
  await runMutation({path:`/api/cases/${state.currentId}/profile`,body:JSON.stringify({side:$('profileSide').value,field,value,edited_by:'Người vận hành',reason:$('profileReason').value}),title:'Đang cập nhật hồ sơ',detail:'Dữ liệu mới sẽ đi lại qua Compatibility Engine, gates và Decision Pack.',success:'Hồ sơ đã được cập nhật và tính lại.'}); $('profileDialog').close();state.simulator=null;
}
async function requestReplan() { await runMutation({path:`/api/cases/${state.currentId}/plan`,body:JSON.stringify({candidate_id:null,reason:'Yêu cầu hệ thống lập lại kế hoạch',actor:'Người vận hành'}),title:'AI đang lập lại kế hoạch',detail:'Các phương án hợp lệ được xếp hạng lại; hard gate vẫn do NexusLoop Core kiểm soát.',success:'Đã lập lại kế hoạch bằng chứng.'}); }
window.requestReplan=requestReplan;
async function overridePlan() { const id=$('overrideCandidate').value,reason=$('overrideReason').value.trim();if(!id)return toast('Không có phương án khả dụng.');if(!reason)return toast('Cần nhập lý do để bảo đảm truy vết.');await runMutation({path:`/api/cases/${state.currentId}/plan`,body:JSON.stringify({candidate_id:id,reason,actor:'Người vận hành'}),title:'Đang áp dụng Human Override',detail:'NexusLoop ghi lại lý do và kiểm tra phương án có hợp lệ với dependency/gate hay không.',success:'Đã chuyển sang kế hoạch do người vận hành chọn.'}); }
async function toggleApproval(role,approved) { await runMutation({path:`/api/cases/${state.currentId}/approvals`,body:JSON.stringify({role,approved:!approved,approved_by:'Người duyệt',note:'Phê duyệt từ NexusLoop Ultimate UI'}),title:'Đang cập nhật phê duyệt',detail:'Quyền quyết định cuối vẫn thuộc người chịu trách nhiệm; hệ thống chỉ tính lại trạng thái sau phê duyệt.',success:'Trạng thái phê duyệt đã được cập nhật.'}); }
async function saveConstraint() { const label=$('constraintLabel').value.trim(),description=$('constraintDescription').value.trim();if(!label||!description)return toast('Cần nhập tên và mô tả điều kiện.');await runMutation({path:`/api/cases/${state.currentId}/constraints`,body:JSON.stringify({label,description,hard:$('constraintHard').checked,actor:'Người vận hành'}),title:'Đang thêm điều kiện mới',detail:'Điều kiện sẽ trở thành một gate và một bước bằng chứng có thể truy vết.',success:'Điều kiện mới đã được đưa vào bản đồ quyết định.'});$('constraintDialog').close();}
async function uploadDocument(e) { e.preventDefault();const file=$('documentFile').files[0];if(!file)return toast('Hãy chọn tệp cần đọc.');const fd=new FormData();fd.append('owner',$('documentOwner').value);fd.append('file',file);await runMutation({path:`/api/cases/${state.currentId}/documents`,body:fd,title:'Đang đọc tài liệu',detail:'Tệp → trích xuất → cập nhật hồ sơ → đối chiếu → lập lại kế hoạch → Decision Pack.',success:'Tài liệu đã được đọc và toàn bộ case đã được tính lại.'});$('documentFile').value='';}

function clearReplayTimers(){state.replayTimers.forEach(clearTimeout);state.replayTimers=[];document.querySelectorAll('.flow-node').forEach(n=>n.classList.remove('is-replaying'));}
function replayRun(run, switchView=true) {
  if(!run)return; clearReplayTimers(); if(switchView)setView('workspace');
  const steps=run.steps?.length?run.steps:(state.obs?.flow||[]);
  steps.forEach((s,i)=>{state.replayTimers.push(setTimeout(()=>{const node=document.querySelector(`.flow-node[data-flow-id="${CSS.escape(s.id)}"]`);if(node){document.querySelectorAll('.flow-node').forEach(n=>n.classList.remove('is-replaying'));node.classList.add('is-replaying');state.selectedFlowId=s.id;renderInspector();node.scrollIntoView({behavior:'smooth',inline:'center',block:'nearest'});}if(i===steps.length-1)setTimeout(()=>node?.classList.remove('is-replaying'),700);},i*520));});
}
function replayById(id){const run=(state.obs?.runs||[]).find(r=>r.id===id);if(run)replayRun(run,true);}

const guidedSteps=[
  {view:'scan',title:'1. Bắt đầu từ danh mục cơ hội',text:'Opportunity Scan cho biết case nào đang xác minh, case nào sẵn sàng pilot và case nào đã bị hard gate chặn.',visual:['Portfolio','Readiness','Status']},
  {view:'workspace',title:'2. Dữ liệu đi vào Live Workspace',text:'Nguồn A, nhu cầu B và tài liệu được đọc thành hồ sơ cấu trúc. Không có số đo nào được tự bịa khi còn thiếu.',visual:['Documents','Profiles','Validation']},
  {view:'workspace',title:'3. Live Flow cho thấy logic đang vận hành',text:'Từng node tương ứng một lớp thật: đọc hồ sơ, đối chiếu, AI planner, rules, xếp hạng bằng chứng và Decision Pack.',visual:['Input','Compare','AI','Rules','Decision']},
  {view:'workspace',title:'4. Con người đưa bằng chứng trở lại',text:'PASS, HOLD hoặc STOP cập nhật gate. Sau đó toàn bộ nhánh phụ thuộc được tính lại và kế hoạch thay đổi ngay trên giao diện.',visual:['Evidence','Gate','Re-plan']},
  {view:'decision',title:'5. Kết quả luôn truy nguyên được',text:'Decision Studio cho phép bấm vào con số để xem công thức và nguồn dữ liệu tạo ra nó; không có “AI nói vậy” mà không có dấu vết.',visual:['Source','Formula','Decision']},
  {view:'command',title:'6. Khi lỗi, biết chính xác lỗi ở đâu',text:'Command Center hiển thị provider, fallback, run history và Failure Map để người vận hành biết bước nào hỏng và cách khôi phục.',visual:['Provider','Failure','Recovery']},
];
function openGuided(){state.guidedIndex=0;renderGuided();$('guidedDialog').showModal();}
function renderGuided(){const s=guidedSteps[state.guidedIndex];$('guidedProgress').style.width=`${((state.guidedIndex+1)/guidedSteps.length)*100}%`;$('guidedTitle').textContent=s.title;$('guidedText').textContent=s.text;$('guidedPrev').disabled=state.guidedIndex===0;$('guidedNext').textContent=state.guidedIndex===guidedSteps.length-1?'Hoàn tất':'Tiếp theo →';$('guidedVisual').innerHTML=`<div class="guided-flow">${s.visual.map((x,i)=>`${i?'<span class="guided-arrow">→</span>':''}<span class="guided-node">${esc(x)}</span>`).join('')}</div>`;setView(s.view);}
function guidedNext(){if(state.guidedIndex>=guidedSteps.length-1){$('guidedDialog').close();return;}state.guidedIndex++;renderGuided();}
function guidedPrev(){if(state.guidedIndex>0){state.guidedIndex--;renderGuided();}}

// Navigation & one-time bindings
$('mainNav').querySelectorAll('button').forEach(b=>b.onclick=()=>setView(b.dataset.view));
$('brandBtn').onclick=()=>setView('scan');$('backToScan').onclick=()=>setView('scan');$('openCommand').onclick=()=>setView('command');$('openPrimaryCase').onclick=()=>state.cases[0]&&openCase(state.cases[0].id);
$('caseFilters').querySelectorAll('button').forEach(b=>b.onclick=()=>{state.filter=b.dataset.filter;document.querySelectorAll('#caseFilters button').forEach(x=>x.classList.toggle('is-active',x===b));renderScan();});
$('workspaceTabs').querySelectorAll('button').forEach(b=>b.onclick=()=>{state.workspacePane=b.dataset.pane;document.querySelectorAll('#workspaceTabs button').forEach(x=>x.classList.toggle('is-active',x===b));document.querySelectorAll('.workspace-pane').forEach(x=>x.classList.remove('is-visible'));$('pane'+b.dataset.pane[0].toUpperCase()+b.dataset.pane.slice(1)).classList.add('is-visible');});
$('replayBtn').onclick=()=>{const r=state.obs?.runs?.[0];if(r)replayRun(r,false);else replayRun({steps:state.obs?.flow||[]},false);};
$('replanBtn').onclick=requestReplan;$('overrideBtn').onclick=overridePlan;$('addConstraintBtn').onclick=()=>{$('constraintDialog').showModal();};$('addConstraintBtn2').onclick=()=>{$('constraintDialog').showModal();};
$('submitEvidenceBtn').onclick=submitEvidence;$('saveProfileBtn').onclick=saveProfile;$('saveConstraintBtn').onclick=saveConstraint;$('uploadForm').onsubmit=uploadDocument;
document.addEventListener('click',e=>{const b=e.target.closest('.profile-edit');if(b)openProfile(b.dataset.side);});
$('openReportBtn').onclick=()=>window.open(`/api/cases/${state.currentId}/report`,'_blank');$('decisionReportBtn').onclick=()=>window.open(`/api/cases/${state.currentId}/report`,'_blank');
$('refreshRunsBtn').onclick=async()=>{await loadCurrent(false);renderCommand();toast('Đã làm mới lịch sử thực thi.');};
$('resetBtn').onclick=async()=>{if(!state.currentId)return;await runMutation({path:`/api/cases/${state.currentId}/reset`,title:'Đang đặt lại case',detail:'Khôi phục dữ liệu seed và tính lại toàn bộ NexusLoop Core.',success:'Case đã trở về trạng thái demo ban đầu.'});state.simulator=null;};
$('guidedDemoBtn').onclick=openGuided;$('closeGuided').onclick=()=>$('guidedDialog').close();$('guidedNext').onclick=guidedNext;$('guidedPrev').onclick=guidedPrev;

boot();
