import types

import config
from services.llm_service import LLMService
from utils.observability import (
    generate_workflow_run_id,
    read_observability_records,
    record_workflow_trace,
    reset_observability_context,
    set_observability_context,
)
from utils.observability_report import build_run_summary


def _snapshot_config():
    return {
        "CHAT_PROVIDER": config.CHAT_PROVIDER,
        "CHAT_MODEL_NAME": config.CHAT_MODEL_NAME,
        "CHAT_API_KEY": config.CHAT_API_KEY,
        "CHAT_BASE_URL": config.CHAT_BASE_URL,
        "EFFECTIVE_CHAT_PROVIDER": config.EFFECTIVE_CHAT_PROVIDER,
        "EFFECTIVE_CHAT_API_KEY": config.EFFECTIVE_CHAT_API_KEY,
        "EFFECTIVE_CHAT_BASE_URL": config.EFFECTIVE_CHAT_BASE_URL,
        "MAX_LLM_API_RETRIES": config.MAX_LLM_API_RETRIES,
    }


def _restore_config(snapshot):
    for key, value in snapshot.items():
        setattr(config, key, value)


def _configure_openai_compatible(max_retries: int = 1):
    config.CHAT_PROVIDER = "openai_compatible"
    config.CHAT_MODEL_NAME = "deepseek-v4-flash"
    config.CHAT_API_KEY = "fake-chat-key"
    config.CHAT_BASE_URL = "https://api.example.test"
    config.EFFECTIVE_CHAT_PROVIDER = "openai_compatible"
    config.EFFECTIVE_CHAT_API_KEY = "fake-chat-key"
    config.EFFECTIVE_CHAT_BASE_URL = "https://api.example.test"
    config.MAX_LLM_API_RETRIES = max_retries


def test_timeout_then_success_retries_once_and_logs_warning_summary():
    snapshot = _snapshot_config()
    workflow_run_id = generate_workflow_run_id("llm_retry_success")
    token = set_observability_context(workflow_run_id, "route_generation")
    try:
        _configure_openai_compatible(max_retries=1)
        llm = LLMService()
        calls = {"count": 0}

        def fake_invoke_openai(self, user_prompt, system_prompt=None):
            calls["count"] += 1
            if calls["count"] == 1:
                raise TimeoutError("Request timed out")
            return '{"ok": true}'

        llm._invoke_openai_compatible = types.MethodType(fake_invoke_openai, llm)

        result = llm.invoke("生成 JSON", "系统提示")
    finally:
        reset_observability_context(token)
        _restore_config(snapshot)

    assert result == '{"ok": true}'
    assert calls["count"] == 2

    records = read_observability_records(workflow_run_id)["model_call_log"]
    assert len(records) == 2
    assert records[0]["success"] is False
    assert records[0]["error_type"] == "timeout_error"
    assert records[0]["retry_index"] == 0
    assert records[0]["max_retries"] == 1
    assert records[1]["success"] is True
    assert records[1]["retry_index"] == 1

    record_workflow_trace(
        workflow_run_id=workflow_run_id,
        node_name="generate_route_node",
        current_stage="route_generated",
        success=True,
        duration_ms=100,
    )
    summary = build_run_summary(workflow_run_id)
    assert summary["retry_count"] >= 1
    assert summary["health_status"] == "warning"


def test_auth_error_does_not_retry():
    snapshot = _snapshot_config()
    workflow_run_id = generate_workflow_run_id("llm_retry_auth")
    token = set_observability_context(workflow_run_id, "route_generation")
    try:
        _configure_openai_compatible(max_retries=1)
        llm = LLMService()
        calls = {"count": 0}

        def fake_invoke_openai(self, user_prompt, system_prompt=None):
            calls["count"] += 1
            raise RuntimeError("401 unauthorized invalid api key")

        llm._invoke_openai_compatible = types.MethodType(fake_invoke_openai, llm)

        try:
            llm.invoke("生成 JSON", "系统提示")
        except RuntimeError as e:
            assert "unauthorized" in str(e)
        else:
            raise AssertionError("auth error should be raised")
    finally:
        reset_observability_context(token)
        _restore_config(snapshot)

    assert calls["count"] == 1
    records = read_observability_records(workflow_run_id)["model_call_log"]
    assert len(records) == 1
    assert records[0]["success"] is False
    assert records[0]["error_type"] == "auth_error"
    assert records[0]["retry_index"] == 0
    assert not any(record["retry_index"] == 1 for record in records)


def test_two_timeouts_fail_after_one_retry():
    snapshot = _snapshot_config()
    workflow_run_id = generate_workflow_run_id("llm_retry_fail")
    token = set_observability_context(workflow_run_id, "route_generation")
    try:
        _configure_openai_compatible(max_retries=1)
        llm = LLMService()
        calls = {"count": 0}

        def fake_invoke_openai(self, user_prompt, system_prompt=None):
            calls["count"] += 1
            raise TimeoutError("Request timed out")

        llm._invoke_openai_compatible = types.MethodType(fake_invoke_openai, llm)

        try:
            llm.invoke("生成 JSON", "系统提示")
        except TimeoutError:
            pass
        else:
            raise AssertionError("timeout should be raised after retry")
    finally:
        reset_observability_context(token)
        _restore_config(snapshot)

    assert calls["count"] == 2
    records = read_observability_records(workflow_run_id)["model_call_log"]
    assert len(records) == 2
    assert [record["retry_index"] for record in records] == [0, 1]
    assert all(record["success"] is False for record in records)
    assert all(record["error_type"] == "timeout_error" for record in records)


if __name__ == "__main__":
    test_timeout_then_success_retries_once_and_logs_warning_summary()
    test_auth_error_does_not_retry()
    test_two_timeouts_fail_after_one_retry()
    print("test_llm_retry.py: all tests passed")
