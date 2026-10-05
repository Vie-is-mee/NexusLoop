import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BrainCircuit, Play, FileText, CheckCircle, Activity, 
  ShieldCheck, History, UploadCloud,
  Factory, GitCompare, FlaskConical, PieChart, Droplet, Recycle, Check, X, Loader2
} from 'lucide-react';

function AIOverlay({ active, lines }: { active: boolean, lines: string[] }) {
  return (
    <AnimatePresence>
      {active && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm"
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 10 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 10 }}
            className="w-[500px] max-w-[90vw] overflow-hidden rounded-2xl bg-white shadow-2xl border border-slate-100"
          >
            <div className="flex items-center gap-3 border-b border-slate-100 bg-slate-50 px-5 py-4">
              <Loader2 className="animate-spin text-emerald-600" size={20} />
              <span className="text-sm font-semibold text-slate-700">Hệ thống đang xử lý dữ liệu...</span>
            </div>
            <div className="flex flex-col gap-3 p-6 text-sm text-slate-600 bg-white">
              {lines.map((line, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.5 }}
                  className="flex items-start gap-2"
                >
                  <Check size={16} className="text-emerald-500 mt-0.5 shrink-0" />
                  <span className="leading-relaxed font-medium">{line}</span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default function App() {
  const [activeStep, setActiveStep] = useState(1);
  const [aiThinking, setAiThinking] = useState(false);
  const [aiLines, setAiLines] = useState<string[]>([]);
  const [data, setData] = useState<any>(null);
  const [evidenceOutcome, setEvidenceOutcome] = useState('pass');

  const formatObject = (v: any) => {
    if (typeof v !== 'object' || v === null) return String(v);
    if (Array.isArray(v)) return `${v.length} mục dữ liệu`;
    return JSON.stringify(v).replace(/["{}]/g, '').replace(/,/g, ', ').replace(/:/g, ': ');
  };

  const fetchCase = async () => {
    try {
      const res = await fetch('/api/cases/water-reuse-ab');
      const d = await res.json();
      setData(d);
    } catch (e) {
      console.error('Fetch error:', e);
    }
  };

  useEffect(() => {
    fetchCase();
  }, []);

  const triggerAI = async (lines: string[], actionPromise: Promise<any>) => {
    setAiThinking(true);
    setAiLines(lines);
    try {
      await actionPromise;
    } catch (e) {}
    setTimeout(() => {
      fetchCase();
      setAiThinking(false);
    }, 2500);
  };

  const handleUploadDoc = () => {
    triggerAI([
      'Đang tải tài liệu lên hệ thống...', 
      'Trích xuất dữ liệu vận hành...', 
      'Cập nhật hồ sơ nhà máy...', 
      'Tái lập kế hoạch kiểm tra...'
    ], Promise.resolve());
  };

  const handleReplan = () => {
    triggerAI([
      'Tiếp nhận yêu cầu đánh giá lại...', 
      'Phân tích đồ thị điều kiện bắt buộc...', 
      'Đánh giá lại các phương án kiểm tra...', 
      'Hoàn tất kế hoạch lộ trình mới.'
    ], Promise.resolve());
  };

  const handleSubmitEvidence = async (candidateId: string) => {
    const action = fetch(`/api/cases/water-reuse-ab/evidence`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        evidence_id: candidateId,
        outcome: evidenceOutcome,
        source: "Lab Test / Expert",
        note: "Submitted via React UI",
        submitted_by: "Admin"
      })
    });
    
    triggerAI([
      'Đã ghi nhận kết quả kiểm định/bằng chứng...', 
      'Cập nhật kho dữ liệu bằng chứng...', 
      'Tính toán lại đồ thị phụ thuộc toàn hệ thống...',
      'Xuất lộ trình kiểm tra tiếp theo.'
    ], action);
  };

  if (!data) return <div className="flex h-screen items-center justify-center bg-slate-50 text-slate-500 font-medium">Đang tải dữ liệu NexusLoop...</div>;

  const steps = [
    { id: 1, name: 'Hồ sơ đầu vào', icon: <Factory size={18} /> },
    { id: 2, name: 'Đối chiếu thông số', icon: <GitCompare size={18} /> },
    { id: 3, name: 'Kế hoạch kiểm tra', icon: <BrainCircuit size={18} /> },
    { id: 4, name: 'Thực hiện & Bằng chứng', icon: <FlaskConical size={18} /> },
    { id: 5, name: 'Kết quả đánh giá', icon: <PieChart size={18} /> },
    { id: 6, name: 'Phê duyệt & An toàn', icon: <ShieldCheck size={18} /> },
    { id: 7, name: 'Lịch sử quyết định', icon: <History size={18} /> }
  ];

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-800 font-sans">
      <AIOverlay active={aiThinking} lines={aiLines} />
      
      {/* Sidebar */}
      <aside className="w-72 border-r border-slate-200 bg-white p-6 hidden md:flex flex-col shadow-[2px_0_10px_rgba(0,0,0,0.02)] z-10">
        <div className="mb-10 flex items-center gap-3 text-emerald-600">
          <div className="p-2 bg-emerald-50 rounded-lg">
            <Recycle size={28} />
          </div>
          <div>
            <span className="block text-xl font-black tracking-tight text-slate-800 leading-tight">NexusLoop</span>
            <span className="text-[10.5px] font-bold uppercase tracking-widest text-slate-400">Platform</span>
          </div>
        </div>
        
        <div className="space-y-1 relative flex-1">
          <div className="absolute left-[19px] top-6 bottom-6 w-px bg-slate-100" />
          {steps.map(step => (
            <button
              key={step.id}
              onClick={() => setActiveStep(step.id)}
              className={`relative flex w-full items-center gap-4 rounded-xl px-4 py-3.5 text-left transition-all ${
                activeStep === step.id 
                ? 'bg-emerald-50/80 text-emerald-700 shadow-sm border border-emerald-100' 
                : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800 border border-transparent'
              }`}
            >
              <div className={`relative z-10 flex h-7 w-7 shrink-0 items-center justify-center rounded-full transition-colors ${
                activeStep === step.id ? 'bg-emerald-600 text-white shadow-md shadow-emerald-200' : 'bg-slate-100 text-slate-400'
              }`}>
                <span className="scale-75">{step.icon}</span>
              </div>
              <span className="font-semibold text-sm">{step.name}</span>
            </button>
          ))}
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto bg-slate-50">
        <div className="max-w-6xl mx-auto p-8 md:p-12">
          <header className="mb-10 flex flex-col md:flex-row md:items-end justify-between border-b border-slate-200 pb-6 gap-6">
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-emerald-600 mb-1.5">Dự án mô phỏng</p>
              <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Tái sử dụng nước sau xử lý: Nhà máy A → B</h1>
              <div className="mt-3 flex items-center gap-2">
                <span className="text-sm font-medium text-slate-500">Trạng thái hồ sơ:</span> 
                <span className={`px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wide ${data.agent.status === 'PILOT' ? 'bg-emerald-100 text-emerald-700' : data.agent.status === 'STOP' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>
                  {data.agent.status}
                </span>
              </div>
            </div>
            <div className="flex gap-3">
              <button 
                onClick={handleUploadDoc}
                className="flex items-center gap-2 rounded-lg bg-white border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 transition-all hover:bg-slate-50 hover:border-slate-300 shadow-sm"
              >
                <UploadCloud size={16} className="text-slate-400" />
                Tải tài liệu PDF
              </button>
              <button 
                onClick={handleReplan}
                className="flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-bold text-white shadow-md shadow-emerald-200 transition-all hover:bg-emerald-700 active:scale-95"
              >
                <Play size={16} className="fill-white" />
                Cập nhật lộ trình
              </button>
            </div>
          </header>

          <AnimatePresence mode="wait">
            <motion.div
              key={activeStep}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {/* STEP 1: Hồ sơ đầu vào */}
              {activeStep === 1 && (
                <div className="grid gap-6 md:grid-cols-2">
                  <div className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm hover:shadow-md transition-shadow">
                    <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                      <Droplet size={28} />
                    </div>
                    <h3 className="mb-6 text-xl font-bold text-slate-900">{data.supplier_profile.company} <span className="text-slate-400 font-medium text-base ml-1">(Bên cấp)</span></h3>
                    <div className="space-y-4">
                      {Object.entries(data.supplier_profile).filter(([k]) => k !== 'company').map(([k, v]: any) => (
                        <div key={k} className="flex justify-between border-b border-slate-100 pb-3">
                          <span className="text-slate-500 text-sm font-medium capitalize">{k.replace('_', ' ')}</span>
                          <span className="font-semibold text-slate-800 text-sm text-right max-w-[60%]">
                            {formatObject(v)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm hover:shadow-md transition-shadow">
                    <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600">
                      <Recycle size={28} />
                    </div>
                    <h3 className="mb-6 text-xl font-bold text-slate-900">{data.receiver_profile.company} <span className="text-slate-400 font-medium text-base ml-1">(Bên nhận)</span></h3>
                    <div className="space-y-4">
                      {Object.entries(data.receiver_profile).filter(([k]) => k !== 'company').map(([k, v]: any) => (
                        <div key={k} className="flex justify-between border-b border-slate-100 pb-3">
                          <span className="text-slate-500 text-sm font-medium capitalize">{k.replace('_', ' ')}</span>
                          <span className="font-semibold text-slate-800 text-sm text-right max-w-[60%]">
                            {formatObject(v)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 2: Đối chiếu */}
              {activeStep === 2 && (
                <div className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
                  <h3 className="mb-6 text-xl font-bold text-slate-900 flex items-center gap-2">
                    <GitCompare className="text-emerald-600" />
                    Kết quả đối chiếu thông số
                  </h3>
                  <div className="space-y-3">
                    {data.compatibility.map((item: any, idx: number) => (
                      <div key={idx} className="flex items-center justify-between rounded-xl bg-slate-50 p-4 border border-slate-100">
                        <div className="flex flex-col">
                          <span className="font-bold text-slate-800">{item.factor}</span>
                          <span className="text-sm font-medium text-slate-500 mt-1">{item.detail}</span>
                        </div>
                        <span className={`px-3 py-1 rounded-md text-xs font-bold uppercase tracking-wide border ${
                          item.status === 'match' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                          item.status === 'conflict' ? 'bg-red-50 text-red-700 border-red-200' :
                          'bg-amber-50 text-amber-700 border-amber-200'
                        }`}>
                          {item.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* STEP 3: Kế hoạch */}
              {activeStep === 3 && (
                <div className="space-y-6">
                  <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-8 shadow-sm">
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-emerald-700 flex items-center gap-2">
                      <BrainCircuit size={18} /> Đề xuất kiểm tra ưu tiên
                    </h3>
                    <p className="text-2xl font-black text-slate-900 mb-4">{data.agent.next_evidence_label}</p>
                    <p className="text-slate-600 font-medium leading-relaxed bg-white/60 p-4 rounded-xl border border-emerald-100/50">{data.agent.rationale}</p>
                  </div>
                  
                  <h4 className="text-lg font-bold text-slate-800 mt-8 mb-4">Các bằng chứng có thể thu thập (Đã xếp hạng)</h4>
                  <div className="grid gap-4">
                    {data.candidates.map((c: any) => (
                      <div key={c.id} className="rounded-xl border border-slate-200 bg-white p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm hover:shadow-md transition-shadow">
                        <div>
                          <div className="flex items-center gap-3 mb-2">
                            <span className="font-bold text-slate-900 text-lg">{c.label}</span>
                            <span className="px-2.5 py-1 rounded-md bg-slate-100 text-xs font-bold text-slate-600 border border-slate-200">Ưu tiên: {c.priority_score.toFixed(1)}</span>
                          </div>
                          <p className="text-sm font-medium text-slate-500 mb-2">Chi phí: {c.cost_est} • Thời gian: {c.time_est} • Rủi ro DL: {c.data_risk}</p>
                          <p className="text-sm font-medium text-slate-700"><span className="text-slate-400">Blocker giải quyết:</span> {c.addressed_blocker}</p>
                        </div>
                        <div className="flex shrink-0">
                          <button className="px-5 py-2.5 rounded-lg bg-white border border-slate-300 text-sm font-bold text-slate-700 hover:bg-slate-50 hover:text-slate-900 shadow-sm transition-colors">
                            Ghi đè thủ công
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* STEP 4: Thực hiện */}
              {activeStep === 4 && (
                <div className="rounded-2xl border border-slate-200 bg-white p-10 shadow-sm max-w-2xl mx-auto mt-4">
                  <div className="mb-10 text-center">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 mb-5">
                      <FlaskConical size={32} />
                    </div>
                    <h3 className="text-2xl font-black text-slate-900 mb-2">Nhiệm vụ đang chờ kết quả</h3>
                    <p className="text-emerald-700 font-bold text-lg bg-emerald-50 inline-block px-4 py-1.5 rounded-lg border border-emerald-100 mt-2">{data.agent.next_evidence_label}</p>
                  </div>
                  
                  <div className="space-y-6 bg-slate-50 p-7 rounded-2xl border border-slate-200">
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-2">Kết quả thực tế từ Lab / Cán bộ chuyên môn</label>
                      <select 
                        value={evidenceOutcome}
                        onChange={(e) => setEvidenceOutcome(e.target.value)}
                        className="w-full bg-white border border-slate-300 rounded-xl p-3.5 text-slate-900 font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 shadow-sm"
                      >
                        <option value="pass">ĐẠT YÊU CẦU (Pass)</option>
                        <option value="fail">KHÔNG ĐẠT (Fail)</option>
                        <option value="partial">ĐẠT MỘT PHẦN (Cần thêm xử lý)</option>
                      </select>
                    </div>
                    
                    <button 
                      onClick={() => handleSubmitEvidence(data.candidates[0]?.id || 'tech_01')}
                      className="w-full rounded-xl bg-emerald-600 py-3.5 font-bold text-white shadow-md shadow-emerald-200 transition-all hover:bg-emerald-700 active:scale-95 flex items-center justify-center gap-2"
                    >
                      <CheckCircle size={20} />
                      Cập nhật vào hệ thống
                    </button>
                  </div>
                </div>
              )}

              {/* STEP 5: Kết quả */}
              {activeStep === 5 && (
                <div className="rounded-2xl border border-slate-200 bg-white p-10 shadow-sm">
                  <div className="text-center mb-12">
                    <h2 className="text-4xl font-black tracking-tight text-slate-900 mb-4">
                      {data.decision_pack.headline}
                    </h2>
                    <p className="text-lg font-medium text-slate-500 max-w-2xl mx-auto">{data.decision_pack.summary}</p>
                  </div>
                  
                  <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                    <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 text-center">
                      <p className="text-sm font-bold text-slate-500 mb-2 uppercase tracking-wide">Khả dụng / Nhu cầu</p>
                      <p className="text-3xl font-black text-slate-900">{data.decision_pack.supplier_available_per_day} <span className="text-xl text-slate-400 font-semibold">/</span> {data.decision_pack.receiver_demand_per_day}</p>
                    </div>
                    <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 text-center">
                      <p className="text-sm font-bold text-slate-500 mb-2 uppercase tracking-wide">Tái sử dụng (Match)</p>
                      <p className="text-3xl font-black text-emerald-600">{data.decision_pack.matched_volume_per_day} <span className="text-lg">m³</span></p>
                    </div>
                    <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 text-center">
                      <p className="text-sm font-bold text-slate-500 mb-2 uppercase tracking-wide">Tỷ lệ tận dụng (A)</p>
                      <p className="text-3xl font-black text-blue-600">{data.decision_pack.supplier_utilization_pct}%</p>
                    </div>
                    <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 text-center">
                      <p className="text-sm font-bold text-slate-500 mb-2 uppercase tracking-wide">Tỷ lệ đáp ứng (B)</p>
                      <p className="text-3xl font-black text-purple-600">{data.decision_pack.receiver_coverage_pct}%</p>
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 6 & 7 */}
              {activeStep === 6 && (
                <div className="space-y-6">
                  <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
                    <h3 className="mb-6 text-xl font-bold text-slate-900 flex items-center gap-2">
                      <ShieldCheck className="text-emerald-600" />
                      Điều kiện an toàn (Gates)
                    </h3>
                    <div className="grid gap-3">
                      {data.gates.map((g: any, i: number) => (
                        <div key={i} className="flex items-center justify-between p-4 rounded-xl border border-slate-100 bg-slate-50">
                          <div>
                            <p className="font-bold text-slate-800">{g.label}</p>
                            <p className="text-sm font-medium text-slate-500 mt-0.5">{g.note || 'Chưa đánh giá / Đang chờ'}</p>
                          </div>
                          <span className={`px-3.5 py-1.5 rounded-lg text-xs font-bold tracking-wide uppercase border ${
                            g.status === 'PASS' ? 'bg-emerald-100 text-emerald-700 border-emerald-200' :
                            g.status === 'FAIL' ? 'bg-red-100 text-red-700 border-red-200' :
                            'bg-slate-200 text-slate-600 border-slate-300'
                          }`}>{g.status}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
                    <h3 className="mb-6 text-xl font-bold text-slate-900">Phê duyệt nhân sự (Human Approval)</h3>
                    <div className="space-y-4">
                      {data.approvals.map((a: any, i: number) => (
                        <div key={i} className="flex items-center gap-4 bg-slate-50 p-4 rounded-xl border border-slate-100">
                          <div className={`p-3 rounded-full ${a.approved ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-200 text-slate-400'}`}>
                            <ShieldCheck size={20} />
                          </div>
                          <div>
                            <p className="font-bold text-slate-800 text-base">{a.label}</p>
                            <p className="text-sm font-medium text-slate-500 mt-0.5">Trạng thái: <span className={a.approved ? 'text-emerald-600 font-bold' : ''}>{a.approved ? 'Đã phê duyệt' : 'Chưa phê duyệt'}</span></p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {activeStep === 7 && (
                <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm max-w-3xl mx-auto">
                  <h3 className="mb-8 text-2xl font-black text-slate-900 flex items-center gap-3 border-b border-slate-100 pb-4">
                    <History className="text-emerald-600" size={28} />
                    Lịch sử hệ thống (Audit Trail)
                  </h3>
                  <div className="space-y-6">
                    {data.audit.map((a: any, i: number) => (
                      <div key={i} className="relative flex gap-6 pb-2">
                        {/* Timeline line */}
                        {i !== data.audit.length - 1 && (
                          <div className="absolute left-3.5 top-8 bottom-[-24px] w-0.5 bg-slate-100"></div>
                        )}
                        <div className="relative z-10 flex-shrink-0 mt-1">
                          <div className="w-7 h-7 rounded-full bg-emerald-100 border-4 border-white flex items-center justify-center">
                            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500"></div>
                          </div>
                        </div>
                        <div className="flex-1 bg-slate-50 p-5 rounded-2xl border border-slate-100 hover:shadow-md transition-shadow">
                          <p className="text-xs font-bold text-slate-400 mb-1.5 uppercase tracking-wider">{new Date(a.ts).toLocaleString('vi-VN')}</p>
                          <p className="font-black text-slate-800 text-lg mb-1">{a.event}</p>
                          <p className="text-sm font-medium text-slate-600 leading-relaxed">{a.detail}</p>
                          <div className="mt-3 pt-3 border-t border-slate-200/60 inline-block">
                            <p className="text-xs font-bold text-slate-500 bg-white px-2 py-1 rounded border border-slate-200">Tác nhân: {a.actor}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
