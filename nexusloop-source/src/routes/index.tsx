import { createFileRoute } from "@tanstack/react-router";
import {
  ArrowRight,
  Bot,
  Check,
  ChevronRight,
  CircleCheck,
  Clock3,
  FileCheck2,
  FileText,
  Leaf,
  Network,
  Search,
  Send,
  ShieldCheck,
  Sparkle,
  Target,
  X,
  Zap,
} from "lucide-react";
import { useMemo, useState, useEffect } from "react";

import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "NexusLoop — Industrial Symbiosis Decision Agent" },
      {
        name: "description",
        content:
          "NexusLoop helps eco-industrial park teams validate symbiosis opportunities and move them to PILOT, HOLD, or STOP.",
      },
      { property: "og:title", content: "NexusLoop — Industrial Symbiosis Decision Agent" },
      {
        property: "og:description",
        content: "Evidence-led decisions for industrial symbiosis opportunities.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: NexusLoop,
});

type Tab = "scan" | "workspace" | "proposal" | "agent";
type Status = "PILOT" | "HOLD" | "STOP";

const opportunities = [
  {
    id: "NX-024",
    title: "Hơi thải lò hơi → sấy nông sản",
    pair: "VinaSteam → AgriDry",
    description: "Khớp nguồn hơi dư 18 t/h với phụ tải sấy ổn định 14 t/h, cách nhau 2,1 km.",
    score: 82,
    status: "PILOT" as Status,
    impact: "4.820 tCO₂e/năm",
    evidence: "12/15",
    next: "Xác nhận CAPEX đường ống",
  },
  {
    id: "NX-031",
    title: "Bã rượu → thức ăn chăn nuôi",
    pair: "Mekong Spirits → GreenFeed",
    description: "Tái sử dụng 340 tấn phụ phẩm mỗi tháng, đã đạt chỉ tiêu dinh dưỡng và an toàn.",
    score: 74,
    status: "PILOT" as Status,
    impact: "2.140 tCO₂e/năm",
    evidence: "9/12",
    next: "Ký biên bản chạy thử",
  },
  {
    id: "NX-018",
    title: "Nước tái sử dụng → tháp làm mát",
    pair: "AquaPark → SteelForm",
    description: "Nguồn nước sau xử lý phù hợp về lưu lượng nhưng thiếu chuỗi dữ liệu độ dẫn điện.",
    score: 57,
    status: "HOLD" as Status,
    impact: "186.000 m³/năm",
    evidence: "6/11",
    next: "Thu thập log 30 ngày",
  },
  {
    id: "NX-009",
    title: "Bùn thải → đồng xử lý xi măng",
    pair: "BioCare → VietCem",
    description: "Hàm lượng clo vượt ngưỡng đầu vào và chi phí tiền xử lý làm mất hiệu quả kinh tế.",
    score: 28,
    status: "STOP" as Status,
    impact: "—",
    evidence: "8/9",
    next: "Lưu lý do dừng",
  },
];

const API_BASE = "/api";

const proposalSections = [
  ["01", "Project Snapshot", "Hoàn tất", 100],
  ["02", "Problem & Impact", "Hoàn tất", 100],
  ["03", "Solution & Innovation", "Đang rà soát", 86],
  ["04", "Agentic AI", "Đang soạn", 68],
  ["05", "Responsible AI", "Cần bổ sung", 42],
  ["06", "MVP & Feasibility", "Bản nháp", 55],
];

function StatusBadge({ status }: { status: Status }) {
  const styles = {
    PILOT: "bg-success/10 text-success ring-success/20",
    HOLD: "bg-warning/10 text-warning ring-warning/25",
    STOP: "bg-destructive/10 text-destructive ring-destructive/20",
  };
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold ring-1 ${styles[status]}`}>
      <span className="size-1.5 rounded-full bg-current" /> {status}
    </span>
  );
}

function Logo() {
  return (
    <div className="flex items-center gap-2.5">
      <span className="relative grid size-9 place-items-center overflow-hidden rounded-lg bg-primary text-primary-foreground shadow-sm">
        <Network className="size-5" />
        <span className="absolute bottom-1 right-1 size-1.5 rounded-full bg-success ring-2 ring-primary" />
      </span>
      <div>
        <div className="font-display text-lg font-semibold leading-none">NexusLoop</div>
        <div className="mt-1 text-[9px] font-bold uppercase tracking-[0.18em] text-muted-foreground">Decision intelligence</div>
      </div>
    </div>
  );
}

function NexusLoop() {
  const [tab, setTab] = useState<Tab>("scan");
  const [selectedId, setSelectedId] = useState("NX-024");
  const [statusFilter, setStatusFilter] = useState<Status | "ALL">("ALL");
  const [notice, setNotice] = useState<string | null>(null);
  
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [selectedCaseData, setSelectedCaseData] = useState<any>(null);
  const [aiThinking, setAiThinking] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/cases`)
      .then(r => r.json())
      .then(data => {
        const mapped = data.map((c: any) => ({
          id: c.id,
          title: c.title,
          pair: `${c.supplier} → ${c.receiver}`,
          description: c.scenario_label || c.short_title,
          score: c.status === 'PILOT' ? 85 : c.status === 'STOP' ? 20 : 60,
          status: c.status,
          impact: 'N/A',
          evidence: c.status === 'INVESTIGATING' ? 'Đang chờ' : 'Hoàn tất',
          next: 'Xem chi tiết'
        }));
        setOpportunities(mapped);
      })
      .catch(e => console.error("Fetch cases error", e));
  }, []);

  const fetchSelectedCase = (id: string) => {
    fetch(`${API_BASE}/cases/${id}`)
      .then(r => r.json())
      .then(data => setSelectedCaseData(data))
      .catch(e => console.error("Fetch case error", e));
  };

  useEffect(() => {
    if (tab === 'workspace' && selectedId) {
      fetchSelectedCase(selectedId);
    }
  }, [tab, selectedId]);

  const handleAction = async (endpoint: string, payload: any, noticeMsg: string) => {
    setAiThinking(true);
    setNotice('Hệ thống đang xử lý yêu cầu...');
    try {
      await fetch(`${API_BASE}/cases/${selectedId}/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      fetchSelectedCase(selectedId);
      setNotice(noticeMsg);
    } catch (e) {
      setNotice('Lỗi khi gửi yêu cầu');
    }
    setAiThinking(false);
  };

  const selected = opportunities.find((item) => item.id === selectedId) ?? (opportunities.length > 0 ? opportunities[0] : null);
  const filtered = useMemo(
    () => opportunities.filter((item) => statusFilter === "ALL" || item.status === statusFilter),
    [statusFilter],
  );

  const navigate = (next: Tab) => {
    setTab(next);
    setNotice(null);
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-30 border-b border-border/70 bg-background/75 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-[1440px] items-center gap-8 px-4 sm:px-6 lg:px-8">
          <Logo />
          <nav className="hidden items-center gap-1 md:flex" aria-label="Điều hướng chính">
            {([
              ["scan", "Opportunity Scan"],
              ["workspace", "Workspace"],
              ["proposal", "Proposal Studio"],
              ["agent", "Agent Console"],
            ] as const).map(([value, label]) => (
              <Button key={value} variant="ghost" size="sm" onClick={() => navigate(value)} className={tab === value ? "bg-surface text-foreground shadow-sm" : "text-muted-foreground"}>
                {label}
              </Button>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <span className="hidden items-center gap-2 rounded-full border border-success/25 bg-success/10 px-3 py-1.5 text-xs font-semibold text-success sm:inline-flex">
              <span className="size-1.5 animate-pulse rounded-full bg-success" /> EIP Zone 7 · Live
            </span>
            <span className="grid size-9 place-items-center rounded-full bg-secondary text-xs font-bold">HM</span>
          </div>
        </div>
        <div className="flex gap-1 overflow-x-auto px-4 pb-2 md:hidden">
          {(["scan", "workspace", "proposal", "agent"] as Tab[]).map((value) => (
            <Button key={value} size="sm" variant={tab === value ? "secondary" : "ghost"} onClick={() => navigate(value)}>{value}</Button>
          ))}
        </div>
      </header>

      <main className="mx-auto max-w-[1440px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        {notice && (
          <div className="mb-5 flex items-center gap-3 rounded-lg border border-success/20 bg-success/10 px-4 py-3 text-sm text-success">
            <CircleCheck className="size-4" /> <span className="flex-1 font-medium">{notice}</span>
            <Button variant="ghost" size="icon" className="size-7 text-success" onClick={() => setNotice(null)} aria-label="Đóng thông báo"><X /></Button>
          </div>
        )}

        {tab === "scan" && (
          <>
            <section className="frost-panel overflow-hidden p-6 sm:p-8">
              <div className="flex flex-col justify-between gap-8 lg:flex-row lg:items-end">
                <div className="max-w-2xl">
                  <div className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-[0.16em] text-primary"><Sparkle className="size-3.5" /> AI evidence loop · vòng 04</div>
                  <h1 className="font-display text-3xl font-semibold leading-tight sm:text-4xl">Biến cơ hội cộng sinh thành quyết định có thể hành động.</h1>
                  <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-muted-foreground">NexusLoop xác định bằng chứng quan trọng nhất cần kiểm tra tiếp theo, phát hiện sớm điểm chặn và đưa từng cơ hội về PILOT, HOLD hoặc STOP.</p>
                </div>
                <div className="grid grid-cols-3 gap-3 sm:gap-6">
                  {[['24','Cơ hội mở'],['08','Sẵn sàng pilot'],['7.1k','tCO₂e/năm']].map(([value,label], index)=>(
                    <div key={label} className="min-w-0 text-right"><div className={`font-display text-2xl font-semibold sm:text-3xl ${index === 1 ? 'text-success' : 'text-primary'}`}>{value}</div><div className="mt-1 text-[11px] text-muted-foreground sm:text-xs">{label}</div></div>
                  ))}
                </div>
              </div>
            </section>

            <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
              <section className="frost-panel p-5 sm:p-6">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div><h2 className="font-display text-xl font-semibold">Danh mục cơ hội</h2><p className="mt-1 text-sm text-muted-foreground">Xếp hạng theo giá trị của bằng chứng kế tiếp</p></div>
                  <div className="flex flex-wrap gap-2">
                    {(["ALL", "PILOT", "HOLD", "STOP"] as const).map((value) => <Button key={value} size="sm" variant={statusFilter === value ? "default" : "outline"} onClick={() => setStatusFilter(value)}>{value}</Button>)}
                  </div>
                </div>
                <div className="mt-5 space-y-3">
                  {filtered.map((item) => (
                    <button key={item.id} onClick={() => { setSelectedId(item.id); setTab("workspace"); }} className="group grid w-full gap-4 rounded-lg border border-border/70 bg-card/75 p-4 text-left transition hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-md sm:grid-cols-[minmax(0,1fr)_84px_90px_24px] sm:items-center">
                      <div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><span className="font-display font-semibold">{item.title}</span><span className="text-[10px] font-bold text-muted-foreground">{item.id}</span></div><div className="mt-1 text-xs font-medium text-primary">{item.pair}</div><p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{item.description}</p></div>
                      <div><div className="font-display text-2xl font-semibold">{item.score}</div><div className="text-[10px] uppercase tracking-wider text-muted-foreground">readiness</div></div>
                      <StatusBadge status={item.status} />
                      <ChevronRight className="hidden size-5 text-muted-foreground transition group-hover:translate-x-1 group-hover:text-primary sm:block" />
                    </button>
                  ))}
                </div>
              </section>
              <AgentPanel onAction={(message) => setNotice(message)} onOpen={() => setTab("agent")} />
            </div>
          </>
        )}

        {tab === "workspace" && selected && <Workspace opportunity={selected} caseData={selectedCaseData} onAction={handleAction} onBack={() => setTab("scan")} onStatus={(value) => setNotice(`Đã ghi nhận đề xuất ${value}. Đang chờ người phụ trách phê duyệt.`)} />}
        {tab === "proposal" && <ProposalStudio onNotice={setNotice} caseData={selectedCaseData} />}
        {tab === "agent" && <AgentConsole onNotice={setNotice} caseData={selectedCaseData} />}
      </main>
    </div>
  );
}

function AgentPanel({ onAction, onOpen }: { onAction: (message: string) => void; onOpen: () => void }) {
  return (
    <aside className="space-y-4">
      <section className="frost-panel p-5">
        <div className="flex items-center justify-between"><div className="flex items-center gap-2"><span className="grid size-8 place-items-center rounded-lg bg-primary/10 text-primary"><Bot className="size-4" /></span><div><h3 className="font-display text-sm font-semibold">Agent Console</h3><p className="text-[10px] text-muted-foreground">Evidence Scout · đang chạy</p></div></div><span className="size-2 animate-pulse rounded-full bg-success" /></div>
        <div className="mt-4 space-y-3">
          <div className="rounded-lg bg-primary/8 p-3"><div className="flex items-center gap-2 text-xs font-semibold text-primary"><Search className="size-3.5" /> Đang truy tìm bằng chứng</div><p className="mt-2 text-sm leading-relaxed text-muted-foreground">CAPEX đường ống là biến số có giá trị thông tin cao nhất cho cơ hội NX-024.</p></div>
          <div className="rounded-lg bg-success/8 p-3"><div className="flex items-center gap-2 text-xs font-semibold text-success"><FileCheck2 className="size-3.5" /> Vừa xác minh</div><p className="mt-2 text-sm leading-relaxed text-muted-foreground">Biên độ cung — cầu hơi ổn định trong 92% thời gian vận hành.</p></div>
        </div>
        <Button className="mt-4 w-full" onClick={() => onAction("Đã gửi yêu cầu báo giá CAPEX tới đơn vị vận hành để phê duyệt.")}><Send /> Gửi yêu cầu bằng chứng</Button>
        <Button variant="ghost" className="mt-1 w-full text-muted-foreground" onClick={onOpen}>Mở toàn bộ hoạt động <ArrowRight /></Button>
      </section>
      <section className="frost-panel p-5">
        <div className="flex items-center gap-2"><ShieldCheck className="size-4 text-success" /><h3 className="font-display text-sm font-semibold">Responsible AI</h3></div>
        <div className="mt-4 space-y-3 text-xs">{[["Truy vết nguồn dữ liệu","Đạt"],["Giải trình xếp hạng","Đạt"],["Phê duyệt của con người","Bắt buộc"]].map(([label,value])=><div key={label} className="flex justify-between gap-4"><span className="text-muted-foreground">{label}</span><span className="font-semibold text-success">{value}</span></div>)}</div>
      </section>
    </aside>
  );
}

function Workspace({ opportunity, caseData, onAction, onBack, onStatus }: { opportunity: any; caseData: any; onAction: any; onBack: () => void; onStatus: (status: Status) => void }) {
  const [evidenceOutcome, setEvidenceOutcome] = useState('pass');
  if (!caseData || !opportunity) return <div className="p-10 text-center">Loading Data...</div>;

  return (
    <div>
      <Button variant="ghost" className="mb-4 -ml-3 text-muted-foreground" onClick={onBack}>← Danh mục cơ hội</Button>
      <section className="frost-panel p-6 sm:p-8">
        <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div><div className="text-xs font-bold uppercase tracking-[0.16em] text-primary">{opportunity.id} · Opportunity workspace</div><h1 className="mt-2 font-display text-3xl font-semibold">{opportunity.title}</h1><p className="mt-2 max-w-2xl text-muted-foreground">{opportunity.description}</p></div>
          <div className="flex items-center gap-3"><StatusBadge status={opportunity.status} /><div className="rounded-lg bg-secondary px-4 py-2"><span className="font-display text-2xl font-semibold">{opportunity.score}%</span><span className="ml-2 text-xs text-muted-foreground">sẵn sàng</span></div></div>
        </div>
      </section>
      <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <section className="frost-panel p-6"><div className="flex items-center justify-between"><div><h2 className="font-display text-lg font-semibold">Bản đồ dòng tài nguyên</h2><p className="text-sm text-muted-foreground">Quan hệ nguồn — hạ tầng — bên tiếp nhận</p></div><Network className="text-primary" /></div>
            <div className="material-grid mt-5 overflow-hidden rounded-lg border border-primary/10 p-5"><div className="grid items-center gap-3 md:grid-cols-[1fr_56px_1fr_56px_1fr]">
              {[[caseData?.supplier || 'Nguồn', 'Bên cung cấp'], ['Cơ sở hạ tầng', 'Truyền tải'], [caseData?.receiver || 'Nhu cầu', 'Bên tiếp nhận']].map(([name,meta], index)=><div key={name} className="contents"><div className={`rounded-lg border p-4 ${index === 2 ? 'border-success/30 bg-success/10' : 'border-border bg-card/85'}`}><div className="font-display font-semibold">{name}</div><div className="mt-1 text-xs text-muted-foreground">{meta}</div></div>{index < 2 && <div className="resource-line hidden md:block"><ArrowRight className="mx-auto size-5 text-primary" /></div>}</div>)}
            </div></div>
          </section>
          <section className="frost-panel p-6">
  <div className="flex justify-between items-center">
    <h2 className="font-display text-lg font-semibold">Bằng chứng ưu tiên kế tiếp</h2>
    <Button size="sm" onClick={() => onAction('plan', { candidate_id: caseData?.candidates?.[0]?.id, reason: 'Yêu cầu đánh giá lại', actor: 'User' }, 'Đã yêu cầu AI phân tích lại lộ trình.')}><Bot className="size-4 mr-2"/> Cập nhật lộ trình</Button>
  </div>
  <div className="mt-4 divide-y divide-border">
    {(caseData?.candidates || []).map((c: any, index: number) => (
      <div key={c.id} className="flex items-center gap-4 py-4">
        <span className={`grid size-9 place-items-center rounded-lg text-xs font-bold ${index === 0 ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'}`}>
          P{index + 1}
        </span>
        <div className="flex-1">
          <div className="font-medium">{c.label}</div>
          <div className="text-xs text-muted-foreground">{c.description}</div>
        </div>
        {index === 0 && (
           <div className="flex gap-2 items-center">
             <select value={evidenceOutcome} onChange={e => setEvidenceOutcome(e.target.value)} className="bg-transparent border border-border rounded text-sm p-1">
               <option value="pass">PASS</option>
               <option value="fail">FAIL</option>
               <option value="partial">PARTIAL</option>
             </select>
             <Button size="sm" variant="outline" onClick={() => onAction('evidence', { evidence_id: c.id, outcome: evidenceOutcome, source: 'Lab/Expert', note: 'UI Submit', submitted_by: 'User' }, 'Đã gửi bằng chứng mới vào hệ thống.')}>Nộp KQ</Button>
           </div>
        )}
      </div>
    ))}
  </div>
  <div className="mt-8 border-t pt-6 border-border">
    <h3 className="font-display text-sm font-semibold mb-3">Phân tích tài liệu bằng AI (Tự động cập nhật hồ sơ)</h3>
    <div className="flex items-center gap-3">
       <input type="file" id="file_upload" className="text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20" onChange={(e) => {
         const file = e.target.files?.[0];
         if (!file) return;
         const fd = new FormData();
         fd.append('file', file);
         fd.append('owner', 'shared');
         
         const btn = document.getElementById('file_upload') as HTMLInputElement;
         if(btn) btn.disabled = true;

         fetch(`${API_BASE}/cases/${caseData.id}/documents`, {
           method: 'POST',
           body: fd
         }).then(async r => {
           if (!r.ok) {
             const text = await r.text();
             throw new Error(text);
           }
           return r.json();
         }).then(data => {
           if(btn) { btn.disabled = false; btn.value = ''; }
           onAction('plan', { candidate_id: null, reason: 'Tài liệu mới, yêu cầu phân tích lại', actor: 'System' }, 'Tài liệu đã được tải lên và AI đã cập nhật trạng thái/lộ trình.');
         }).catch((e) => { 
           if(btn) btn.disabled = false;
           alert("Lỗi tải lên: " + e.message);
         });
       }} />
    </div>
  </div>
</section>
        </div>
        <aside className="space-y-6">
          <section className="frost-panel p-5"><div className="text-xs font-bold uppercase tracking-[0.14em] text-muted-foreground">Cổng quyết định</div><h3 className="mt-2 font-display text-lg font-semibold">Cần phê duyệt của con người</h3><p className="mt-2 text-sm text-muted-foreground">Agent chỉ đề xuất. Người phụ trách EIP quyết định trạng thái cuối.</p><div className="mt-4 grid grid-cols-3 gap-2">{(["PILOT","HOLD","STOP"] as Status[]).map(value=><Button key={value} size="sm" variant={value === opportunity.status ? "default" : "outline"} onClick={()=>onStatus(value)}>{value}</Button>)}</div></section>
          <section className="frost-panel p-5"><h3 className="font-display font-semibold">Timeline thẩm định</h3><div className="mt-5 space-y-5 border-l border-border pl-5">{(caseData?.audit || []).slice(0, 4).map((a: any, i: number)=><div key={i} className="relative"><span className={`absolute -left-[25px] top-1 size-2.5 rounded-full ring-4 ring-card ${i === 0 ? 'bg-primary' : 'bg-success'}`} /><div className="text-xs text-muted-foreground">{new Date(a.ts).toLocaleDateString()}</div><div className="text-sm font-medium">{a.event}</div></div>)}</div></section>
          <section className="frost-panel p-5"><div className="flex items-center gap-2 text-primary"><Bot className="size-4"/><span className="text-xs font-bold uppercase tracking-wider">Agent nhận định</span></div><div className="mt-3 text-sm leading-relaxed text-muted-foreground">{caseData?.decision_pack?.summary || caseData?.agent?.rationale?.[0] || "Đang chờ thêm bằng chứng để đưa ra phân tích."}</div></section>
        </aside>
      </div>
    </div>
  );
}

function ProposalStudio({ onNotice, caseData }: { onNotice: (value: string) => void, caseData?: any }) {
  const [active, setActive] = useState(3);
  const current = proposalSections[active] ?? proposalSections[0];
  if (!current) return null;
  return <div className="grid gap-6 xl:grid-cols-[300px_minmax(0,1fr)_300px]">
    <aside className="frost-panel p-5"><div className="flex items-center gap-2 text-primary"><FileText className="size-5"/><h1 className="font-display text-lg font-semibold">Proposal Studio</h1></div><p className="mt-2 text-sm text-muted-foreground">VJAI Hackathon 2026 · tối đa 03 trang A4</p><div className="mt-5 space-y-2">{proposalSections.map((item,index)=><button key={item[0]} onClick={()=>setActive(index)} className={`w-full rounded-lg border p-3 text-left ${active === index ? 'border-primary/30 bg-primary/8' : 'border-transparent hover:bg-secondary/60'}`}><div className="flex gap-3"><span className="text-xs font-bold text-primary">{item[0]}</span><div><div className="text-sm font-medium">{item[1]}</div><div className="mt-1 text-[10px] text-muted-foreground">{item[2]}</div></div></div></button>)}</div></aside>
    <section className="paper-sheet min-h-[720px] p-6 sm:p-10"><div className="border-b border-border pb-5"><div className="text-xs font-bold uppercase tracking-[0.16em] text-primary">Section {current[0]}</div><h2 className="mt-2 font-display text-3xl font-semibold">{current[1]}</h2></div><div className="mt-7 space-y-6 text-[15px] leading-7 text-foreground/80">
      {active === 3 ? <><div><h3 className="font-display text-lg font-semibold text-foreground">4.1. Agent Flow</h3><div className="mt-4 grid gap-3 sm:grid-cols-5">{[["Goal","Đưa cơ hội tới quyết định"],["Context","Dữ liệu kỹ thuật & thương mại"],["Decision","Chọn bằng chứng giá trị nhất"],["Action","Yêu cầu và xác minh"],["Result","PILOT · HOLD · STOP"]].map(([title,text])=><div key={title} className="rounded-lg bg-secondary/70 p-3"><div className="text-xs font-bold text-primary">{title}</div><div className="mt-2 text-xs leading-5">{text}</div></div>)}</div></div><div><h3 className="font-display text-lg font-semibold text-foreground">4.2. Nhật ký Audit Trail (Tự động tạo)</h3><ul className="mt-2 text-sm list-disc pl-5">{(caseData?.audit || []).slice(-5).map((a: any, i: number) => <li key={i}><strong>{a.actor}</strong>: {a.event}</li>)}</ul></div><div><h3 className="font-display text-lg font-semibold text-foreground">4.3. Quyết định AI</h3><p className="mt-2">Dự án <strong>{caseData?.title || 'Chưa chọn'}</strong> hiện tại đang ở trạng thái <strong>{caseData?.status || 'N/A'}</strong>. Dựa trên bằng chứng, hệ thống đề xuất các bước kiểm thử kế tiếp.</p></div></> : <><p>Báo cáo tự động được tạo ra từ dữ liệu của {caseData?.supplier || 'Nhà máy A'} và {caseData?.receiver || 'Nhà máy B'}.</p><p>Hệ thống ưu tiên đúng điểm chưa chắc chắn cần kiểm tra, giảm chi phí thẩm định và phát hiện sớm các điểm chặn kỹ thuật, pháp lý hoặc thương mại.</p><div className="rounded-lg border border-primary/15 bg-primary/5 p-5"><div className="text-xs font-bold uppercase tracking-wider text-primary">Trạng thái</div><p className="mt-2 text-sm font-semibold">{caseData?.status === 'PILOT' ? '✅ Đủ điều kiện Pilot' : caseData?.status === 'STOP' ? '❌ Dừng dự án do xung đột' : '⏳ Cần thêm bằng chứng'}</p></div></>}
    </div></section>
    <aside className="space-y-5"><section className="frost-panel p-5"><div className="flex items-center justify-between"><h3 className="font-display font-semibold">Giới hạn tài liệu</h3><span className="font-display text-xl font-semibold text-success">2.6/3</span></div><div className="mt-3 h-2 overflow-hidden rounded-full bg-secondary"><div className="h-full w-[87%] rounded-full bg-success" /></div><p className="mt-2 text-xs text-muted-foreground">Còn khoảng 180 từ trước khi vượt giới hạn.</p></section><section className="frost-panel p-5"><h3 className="font-display font-semibold">Quality checks</h3><div className="mt-4 space-y-3">{[["Đủ 6 phần","Đạt"],["Agentic loop rõ ràng","Đạt"],["Dữ liệu thực tế", caseData ? "Đạt" : "Trống"],["Chỉ số impact","2/3"]].map(([label,value])=><div key={label} className="flex items-center justify-between gap-3 text-xs"><span className="text-muted-foreground">{label}</span><span className={value==='Đạt'?'font-semibold text-success':'font-semibold text-warning'}>{value}</span></div>)}</div></section><Button className="w-full" onClick={()=>window.print()}><Check /> In Proposal (PDF)</Button></aside>
  </div>;
}

function AgentConsole({ onNotice, caseData }: { onNotice: (value: string) => void, caseData?: any }) {
  return <div><section className="frost-panel p-6 sm:p-8"><div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.16em] text-primary"><Bot className="size-4"/> Nexus Agent Runtime</div><h1 className="mt-2 font-display text-3xl font-semibold">Agent đang điều phối cơ hội {caseData?.id || ''}</h1><p className="mt-2 max-w-2xl text-muted-foreground">Mỗi hành động đều có nguồn dữ liệu, lý do và ranh giới phê duyệt rõ ràng.</p></div><Button onClick={()=>onNotice("Đã tạm dừng agent. Không có hành động mới nào được thực hiện.")}>Tạm dừng Agent</Button></div></section><div className="mt-6 grid gap-6 lg:grid-cols-3">
    <section className="frost-panel p-5 lg:col-span-2"><h2 className="font-display text-lg font-semibold">Hoạt động gần đây (Audit Trail)</h2><div className="mt-5 space-y-3">{(caseData?.audit && caseData.audit.length > 0) ? caseData.audit.map((a: any, index: number) => <div key={index} className="flex gap-4 rounded-lg border border-border/70 bg-card/70 p-4"><span className="grid size-9 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary"><Search className="size-4"/></span><div className="flex-1"><div className="font-medium">{a.actor}</div><div className="mt-1 text-sm text-muted-foreground">{a.event}</div></div><div className="text-[10px] text-muted-foreground">{new Date(a.ts).toLocaleTimeString()}</div></div>) : [[Search,"Đã phân tích 8 báo giá vận chuyển","Tìm thấy chênh lệch 14% giữa hai phương án tuyến.","2 phút trước"],[Target,"Đã đổi ưu tiên bằng chứng NX-018","Log độ dẫn điện có giá trị thông tin cao hơn báo giá bơm.","8 phút trước"],[FileCheck2,"Đã xác minh báo cáo phòng lab","Chữ ký số và thời hạn hiệu lực hợp lệ.","21 phút trước"],[Clock3,"Đang chờ phê duyệt","Gửi yêu cầu CAPEX tới VinaSteam.","34 phút trước"]].map(([Icon,title,body,time])=>{const ActivityIcon=Icon as typeof Search; return <div key={String(title)} className="flex gap-4 rounded-lg border border-border/70 bg-card/70 p-4"><span className="grid size-9 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary"><ActivityIcon className="size-4"/></span><div className="flex-1"><div className="font-medium">{String(title)}</div><div className="mt-1 text-sm text-muted-foreground">{String(body)}</div></div><div className="text-[10px] text-muted-foreground">{String(time)}</div></div>})}</div></section>
    <aside className="space-y-6"><section className="frost-panel p-5"><h3 className="font-display font-semibold">Quyền tự chủ</h3><div className="mt-4 space-y-4">{[["Phân tích dữ liệu",true],["Xếp hạng bằng chứng",true],["Soạn yêu cầu",true],["Gửi ra bên ngoài",false],["Đổi trạng thái",false]].map(([label,enabled])=><div key={String(label)} className="flex items-center justify-between text-sm"><span className="text-muted-foreground">{String(label)}</span><span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${enabled?'bg-success/10 text-success':'bg-warning/10 text-warning'}`}>{enabled?'TỰ ĐỘNG':'PHÊ DUYỆT'}</span></div>)}</div></section><section className="frost-panel p-5"><h3 className="font-display font-semibold">Hiệu suất vòng này</h3><div className="mt-4 grid grid-cols-2 gap-3">{[["38","tệp đọc"],["11","giả thuyết"],["04","đề xuất"],["0","hành động lỗi"]].map(([value,label])=><div key={label} className="rounded-lg bg-secondary/70 p-3"><div className="font-display text-2xl font-semibold text-primary">{value}</div><div className="text-[10px] text-muted-foreground">{label}</div></div>)}</div></section></aside>
  </div></div>;
}