from datetime import date
from types import SimpleNamespace

import pytest

from app.ai.ai_suggestion_client import AISuggestionClient
from app.ai.ai_tasks import run_ai_suggestion
from app.ai.gemini_client import GeminiAISuggestionClient
from app.schemas.ai_schemas import AISuggestionMode
from app.service_errors import ServiceValidationError
from app.services import ai_service


class StubAIClient(AISuggestionClient):
    def __init__(self, response: str = ""):
        super().__init__("test-key")
        self.response = response

    def call_api(self, prompt: str) -> str:
        return self.response


def test_ai_client_builds_prompts_and_extracts_task_title():
    client = StubAIClient("before <task_title>  Ship safely  </task_title> after")
    task = {"title": "Release", "description": "Desc", "category": "Ops", "deadline": "2026-09-30"}

    result = client.suggest_task_name(task)

    assert result["title"] == "Ship safely"
    assert "Release" in result["prompt"]
    assert result["raw_data"].startswith("before")
    assert client.extract_task_title("missing tags") == ""


def test_ai_client_rejects_non_mapping_objective_input():
    with pytest.raises(ValueError, match="dictionary"):
        StubAIClient().build_prompt_for_objectives([])


def test_ai_client_parses_objectives_and_discards_invalid_fields():
    response = """
    <objective><text> First\n objective </text><assignee> Alice </assignee><due_date>Sep 30, 2026</due_date></objective>
    <objective><text>　</text><assignee>Ignored</assignee><due_date>2026-01-01</due_date></objective>
    <objective><text>Second</text><assignee>　</assignee><due_date>not-a-date</due_date></objective>
    """
    client = StubAIClient(response)

    result = client.generate_objectives({"title": "Goal"})

    assert result["objectives"] == [
        {"title": "First objective", "assignee": "Alice", "due_date": date(2026, 9, 30)},
        {"title": "Second"},
    ]
    assert client._is_blank(None)
    assert not client._is_blank(42)
    assert client._normalize_date("invalid") is None


@pytest.mark.parametrize(
    ("mode", "method", "payload"),
    [
        (AISuggestionMode.TASK_NAME.value, "suggest_task_name", {"title": "T"}),
        (AISuggestionMode.OBJECTIVES.value, "generate_objectives", {"objectives": []}),
    ],
)
def test_ai_task_dispatches_supported_modes(monkeypatch, mode, method, payload):
    fake = SimpleNamespace(**{method: lambda task_info: payload})
    monkeypatch.setattr("app.ai.ai_tasks.GeminiAISuggestionClient", lambda: fake)

    result = run_ai_suggestion.run({"title": "Input"}, mode)

    assert result == {"status": "success", "mode": mode, "result": payload}


@pytest.mark.parametrize(
    ("task_info", "mode", "message"),
    [([], AISuggestionMode.TASK_NAME.value, "task_info must be dict"), ({}, "bad-mode", "Invalid mode")],
)
def test_ai_task_returns_structured_error(task_info, mode, message):
    result = run_ai_suggestion.run(task_info, mode)
    assert result["status"] == "error"
    assert message in result["message"]


def test_enqueue_ai_task_validates_deadline_and_enqueues(monkeypatch):
    called = {}

    def apply_async(*, args):
        called["args"] = args
        return SimpleNamespace(id="job-1")

    monkeypatch.setattr(ai_service.run_ai_suggestion, "apply_async", apply_async)
    data = {
        "task_info": {"deadline": "2026-09-30"},
        "mode": AISuggestionMode.OBJECTIVES,
    }
    assert ai_service.enqueue_ai_task(data) == {"job_id": "job-1"}
    assert called["args"] == [data["task_info"], "objectives"]


def test_enqueue_ai_task_rejects_invalid_deadline():
    with pytest.raises(ServiceValidationError, match="Invalid date"):
        ai_service.enqueue_ai_task({"task_info": {"deadline": "not a date"}, "mode": AISuggestionMode.TASK_NAME})


def test_enqueue_ai_task_rejects_missing_task_info():
    with pytest.raises(ServiceValidationError, match="task_info"):
        ai_service.enqueue_ai_task({"task_info": {}, "mode": AISuggestionMode.TASK_NAME})


class FakeAsyncResult:
    def __init__(self, state, result=None, *, ready=True, successful=True, failed=False):
        self.id = "job"
        self.state = state
        self.result = result
        self.date_done = "today"
        self._ready = ready
        self._successful = successful
        self._failed = failed

    def ready(self):
        return self._ready

    def successful(self):
        return self._successful

    def failed(self):
        return self._failed


@pytest.mark.parametrize(
    ("fake", "expected"),
    [
        (FakeAsyncResult("PENDING", ready=False, successful=False), {"status": "PENDING"}),
        (FakeAsyncResult("SUCCESS", "unexpected"), {}),
        (FakeAsyncResult("SUCCESS", {"status": "success", "mode": "task_name", "result": {"title": "T"}}), {"status": "SUCCESS", "task_title_data": {"title": "T"}}),
        (FakeAsyncResult("SUCCESS", {"status": "success", "mode": "objectives", "result": []}), {"status": "SUCCESS", "objectives_data": []}),
        (FakeAsyncResult("SUCCESS", {"status": "error", "message": "boom"}, successful=False), {"status": "ERROR", "error": "boom"}),
        (FakeAsyncResult("FAILURE", "worker failed", successful=False, failed=True), {}),
    ],
)
def test_get_ai_task_result_states(monkeypatch, fake, expected):
    monkeypatch.setattr(ai_service, "AsyncResult", lambda job_id, app: fake)
    response = ai_service.get_ai_task_result("job")
    for key, value in expected.items():
        assert response[key] == value
    assert response["async_result"]["job_id"] == "job"


def test_gemini_client_configures_model_and_handles_calls(monkeypatch):
    configured = {}
    model = SimpleNamespace(generate_content=lambda prompt: SimpleNamespace(text="  answer  "))
    monkeypatch.setattr("app.ai.gemini_client.genai.configure", lambda **kw: configured.update(kw))
    monkeypatch.setattr("app.ai.gemini_client.genai.GenerativeModel", lambda name: model)
    monkeypatch.setattr("app.ai.gemini_client.genai.list_models", lambda: [SimpleNamespace(name="models/gemini-a"), SimpleNamespace(name="models/other")])

    client = GeminiAISuggestionClient("key", "model")

    assert configured == {"api_key": "key"}
    assert client.call_api("prompt") == "answer"
    assert client.list_models() == ["models/gemini-a"]


def test_gemini_client_wraps_provider_errors(monkeypatch):
    model = SimpleNamespace(generate_content=lambda prompt: (_ for _ in ()).throw(ValueError("down")))
    monkeypatch.setattr("app.ai.gemini_client.genai.configure", lambda **kw: None)
    monkeypatch.setattr("app.ai.gemini_client.genai.GenerativeModel", lambda name: model)
    client = GeminiAISuggestionClient("key", "model")

    with pytest.raises(RuntimeError, match="down"):
        client.call_api("prompt")
