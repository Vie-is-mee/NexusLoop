from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nexusloop.models import ApprovalSubmission, EvidenceSubmission, PlanOverrideSubmission
from nexusloop.store import CaseStore

root = ROOT
store = CaseStore(root / 'data' / 'demo_cases.json')
case = store.get('water-reuse-ab')
print('START:', case.agent.status, '->', case.agent.next_evidence_label)
print('COMPAT:', [(x.label, x.status.value) for x in case.compatibility])

# Human intervention example
case = store.override_plan('water-reuse-ab', PlanOverrideSubmission(candidate_id='continuity-check', reason='Tuần tới lịch sản xuất thay đổi, muốn xác minh nguồn trước'))
print('HUMAN PLAN:', case.agent.next_evidence_label, case.agent.human_override_active)
case = store.override_plan('water-reuse-ab', PlanOverrideSubmission(candidate_id=None, reason='Return control to AI'))
print('AI REPLAN:', case.agent.next_evidence_label)

for eid in ['legal-review','water-lab','continuity-check','engineering-survey']:
    case = store.submit_evidence('water-reuse-ab', EvidenceSubmission(evidence_id=eid, outcome='PASS', source='Synthetic demo evidence'))
    print('AFTER', eid, ':', case.agent.status, '->', case.agent.next_evidence_label)

for role in ['environmental_officer','process_engineer']:
    case = store.approve('water-reuse-ab', ApprovalSubmission(role=role, approved=True, approved_by='Demo reviewer'))

print('FINAL:', case.agent.status)
print('PACK:', case.decision_pack.model_dump())
