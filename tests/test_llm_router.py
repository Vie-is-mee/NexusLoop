from nexusloop.ai.router import LLMRouter


def _clear_provider_env(monkeypatch):
    for key in [
        'OPENAI_API_KEY','OPENAI_MODEL','ANTHROPIC_API_KEY','ANTHROPIC_MODEL',
        'GEMINI_API_KEY','GOOGLE_API_KEY','GEMINI_MODEL',
        'OPENAI_COMPATIBLE_API_KEY','OPENAI_COMPATIBLE_BASE_URL','OPENAI_COMPATIBLE_MODEL',
        'OLLAMA_MODEL',
    ]:
        monkeypatch.delenv(key, raising=False)


def test_router_falls_back_when_no_provider_configured(monkeypatch):
    _clear_provider_env(monkeypatch)
    monkeypatch.setenv('NEXUSLOOP_AI_PROVIDER', 'auto')
    monkeypatch.setenv('NEXUSLOOP_AI_MODE', 'auto')
    router = LLMRouter()
    assert router.current is None
    assert router.active is False


def test_router_auto_selects_configured_provider_by_priority(monkeypatch):
    _clear_provider_env(monkeypatch)
    monkeypatch.setenv('NEXUSLOOP_AI_PROVIDER', 'auto')
    monkeypatch.setenv('NEXUSLOOP_AI_MODE', 'auto')
    monkeypatch.setenv('NEXUSLOOP_PROVIDER_PRIORITY', 'anthropic,openai,gemini')
    monkeypatch.setenv('OPENAI_API_KEY', 'fake-openai-key')
    monkeypatch.setenv('OPENAI_MODEL', 'fake-openai-model')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'fake-anthropic-key')
    monkeypatch.setenv('ANTHROPIC_MODEL', 'fake-anthropic-model')
    router = LLMRouter()
    assert router.current is not None
    assert router.current.id == 'anthropic'


def test_router_can_select_openai_compatible(monkeypatch):
    _clear_provider_env(monkeypatch)
    monkeypatch.setenv('NEXUSLOOP_AI_PROVIDER', 'openai_compatible')
    monkeypatch.setenv('OPENAI_COMPATIBLE_API_KEY', 'fake')
    monkeypatch.setenv('OPENAI_COMPATIBLE_BASE_URL', 'https://example.invalid/v1')
    monkeypatch.setenv('OPENAI_COMPATIBLE_MODEL', 'model-x')
    router = LLMRouter()
    assert router.current is not None
    assert router.current.id == 'openai_compatible'
    assert router.current.model == 'model-x'


def test_router_supports_ollama_without_cloud_key(monkeypatch):
    _clear_provider_env(monkeypatch)
    monkeypatch.setenv('NEXUSLOOP_AI_PROVIDER', 'ollama')
    monkeypatch.setenv('OLLAMA_MODEL', 'local-model')
    router = LLMRouter()
    assert router.current is not None
    assert router.current.id == 'ollama'
