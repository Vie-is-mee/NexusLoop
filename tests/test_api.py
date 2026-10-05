from fastapi.testclient import TestClient
from main import app, store

client = TestClient(app)

def setup_function():
    store.reset_all()


def test_health_case_list_and_detail():
    assert client.get('/api/health').json()['version'] == '1.2.0'
    cases = client.get('/api/cases').json()
    assert len(cases) == 2
    detail = client.get('/api/cases/water-reuse-ab').json()
    assert detail['supplier_profile']['quantity_per_day'] == 600
    assert detail['receiver_profile']['demand_per_day'] == 450


def test_evidence_api_replans():
    response = client.post('/api/cases/water-reuse-ab/evidence', json={
        'evidence_id': 'legal-review', 'outcome': 'PASS', 'source': 'Synthetic legal memo', 'note': 'test', 'submitted_by': 'Reviewer'
    })
    assert response.status_code == 200
    assert response.json()['agent']['next_evidence_id'] == 'water-lab'


def test_profile_edit_endpoint():
    res = client.post('/api/cases/water-reuse-ab/profile', json={
        'side':'receiver','field':'demand_per_day','value':390,'edited_by':'Operator','reason':'new plan'
    })
    assert res.status_code == 200
    assert res.json()['receiver_profile']['demand_per_day'] == 390


def test_add_constraint_endpoint():
    res = client.post('/api/cases/water-reuse-ab/constraints', json={
        'label':'Kiểm tra ăn mòn','description':'Xác nhận vật liệu đường ống phù hợp','hard':False,'actor':'Engineer'
    })
    assert res.status_code == 200
    payload=res.json()
    assert any(x['label']=='Kiểm tra ăn mòn' for x in payload['custom_constraints'])
    assert any(x['domain']=='custom' for x in payload['candidates'])


def test_report_endpoint():
    res = client.get('/api/cases/water-reuse-ab/report')
    assert res.status_code == 200
    assert 'Bộ hồ sơ quyết định' in res.text


def test_safety_case_is_stopped():
    case = client.get('/api/cases/safety-stop-demo').json()
    assert case['agent']['status'] == 'STOP'
    assert case['agent']['next_evidence_id'] is None

def test_document_upload_updates_supplier_quality():
    csv_content = b"parameter,value,unit\nCOD,38,mg/L\nconductivity,920,uS/cm\n"
    res = client.post('/api/cases/water-reuse-ab/documents', data={'owner':'supplier'}, files={'file':('lab.csv', csv_content, 'text/csv')})
    assert res.status_code == 200
    payload = res.json()
    assert payload['supplier_profile']['quality']['COD'] == 38.0
    assert payload['supplier_profile']['quality']['conductivity'] == 920.0
    assert len(payload['documents']) >= 3


def test_ai_status_endpoint_has_fallback_or_api_mode():
    res = client.get('/api/ai/status')
    assert res.status_code == 200
    payload = res.json()
    assert 'provider' in payload
    assert 'provider_label' in payload
    assert 'active' in payload
    assert payload['label']
    assert 'openai' in payload['supported_providers']
    assert 'anthropic' in payload['supported_providers']
    assert 'gemini' in payload['supported_providers']


def test_single_standard_bundle_updates_both_profiles():
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / 'data' / 'sample_inputs' / 'NexusLoop_demo_input_standard.json'
    content = path.read_bytes()
    res = client.post('/api/cases/water-reuse-ab/documents', data={'owner':'shared'}, files={'file':('NexusLoop_demo_input_standard.json', content, 'application/json')})
    assert res.status_code == 200
    payload = res.json()
    assert payload['supplier_profile']['quantity_per_day'] == 640
    assert payload['receiver_profile']['demand_per_day'] == 480
    assert payload['receiver_profile']['quality_requirements']['COD']['max'] == 50
    assert payload['documents'][-1]['owner'] == 'shared'


def test_ai_providers_endpoint_lists_router_choices():
    res = client.get('/api/ai/providers')
    assert res.status_code == 200
    payload = res.json()
    ids = {x['id'] for x in payload['providers']}
    assert {'openai', 'anthropic', 'gemini', 'openai_compatible', 'ollama'}.issubset(ids)
    assert payload['fallback_available'] is True
