from fastapi.testclient import TestClient
from main import app, store, runs

client = TestClient(app)


def setup_function():
    store.reset_all()
    runs._runs = []
    runs._timers = {}


def test_observability_exposes_real_flow_and_provenance():
    res = client.get('/api/cases/water-reuse-ab/observability')
    assert res.status_code == 200
    payload = res.json()
    ids = [x['id'] for x in payload['flow']]
    assert ids == ['ingest', 'compare', 'ai', 'rules', 'options', 'rank', 'decide', 'act', 'pack']
    matched = next(x for x in payload['provenance'] if x['id'] == 'matched-volume')
    assert matched['value'] == 450
    assert 'min' in matched['formula']


def test_mutation_creates_replayable_run():
    res = client.post('/api/cases/water-reuse-ab/evidence', json={
        'evidence_id':'legal-review','outcome':'PASS','source':'Verified memo','note':'ok','submitted_by':'Reviewer'
    })
    assert res.status_code == 200
    history = client.get('/api/cases/water-reuse-ab/runs').json()
    assert history and history[0]['status'] == 'completed'
    assert history[0]['steps'][-1]['id'] == 'pack'
    assert history[0]['before']['evidence'] < history[0]['after']['evidence']


def test_failed_domain_action_is_visible_in_failure_history():
    res = client.post('/api/cases/water-reuse-ab/evidence', json={
        'evidence_id':'does-not-exist','outcome':'PASS','source':'x','submitted_by':'Reviewer'
    })
    assert res.status_code == 400
    history = client.get('/api/cases/water-reuse-ab/runs').json()
    assert history[0]['status'] == 'failed'
    assert history[0]['error']['component'] == 'Evidence Validator'


def test_ultimate_ui_is_default_root():
    res = client.get('/')
    assert res.status_code == 200
    assert 'NexusLoop Ultimate' in res.text
    assert 'NexusLoop Live Flow' in res.text
