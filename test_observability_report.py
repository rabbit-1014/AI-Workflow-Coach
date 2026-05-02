import json

from utils.observability import (
    generate_workflow_run_id,
    record_model_call_log,
    record_retrieval_trace,
    record_workflow_trace,
)
from utils.observability_report import build_run_summary


def _write_success_records(workflow_run_id: str) -> None:
    record_workflow_trace(
        workflow_run_id=workflow_run_id,
        node_name="analyze_task_node",
        current_stage="task_analyzed",
        success=True,
        duration_ms=10,
    )
    record_workflow_trace(
        workflow_run_id=workflow_run_id,
        node_name="retrieve_for_route_node",
        current_stage="route_retrieved",
        success=True,
        duration_ms=800,
    )
    record_workflow_trace(
        workflow_run_id=workflow_run_id,
        node_name="generate_route_node",
        current_stage="route_generated",
        success=True,
        duration_ms=10000,
    )
    record_model_call_log(
        workflow_run_id=workflow_run_id,
        call_type="route_generation",
        provider="openai_compatible",
        model="deepseek-v4-flash",
        input_chars=3000,
        output_chars=2000,
        duration_ms=10000,
        success=True,
    )
    record_retrieval_trace(
        workflow_run_id=workflow_run_id,
        retrieval_type="route",
        query_chars=28,
        top_k=5,
        doc_count=9,
        duration_ms=800,
        success=True,
    )


def test_success_run_summary_is_healthy():
    workflow_run_id = generate_workflow_run_id("summary_success")
    _write_success_records(workflow_run_id)

    summary = build_run_summary(workflow_run_id)

    assert summary["success"] is True
    assert summary["health_status"] == "healthy"
    assert summary["node_count"] == 3
    assert summary["model_call_count"] == 1
    assert summary["retrieval_count"] == 1
    assert summary["correction_count"] == 0
    assert summary["error_count"] == 0
    assert summary["final_stage"] == "route_generated"
    assert summary["slowest_node"] == "generate_route_node"


def test_correction_run_summary_is_warning():
    workflow_run_id = generate_workflow_run_id("summary_warning")
    _write_success_records(workflow_run_id)
    record_model_call_log(
        workflow_run_id=workflow_run_id,
        call_type="route_generation",
        provider="openai_compatible",
        model="deepseek-v4-flash",
        input_chars=1000,
        output_chars=1000,
        duration_ms=1000,
        success=True,
        is_correction=True,
    )

    summary = build_run_summary(workflow_run_id)

    assert summary["correction_count"] == 1
    assert summary["health_status"] == "warning"
    assert summary["success"] is True


def test_retry_run_summary_is_warning():
    workflow_run_id = generate_workflow_run_id("summary_retry")
    _write_success_records(workflow_run_id)
    record_model_call_log(
        workflow_run_id=workflow_run_id,
        call_type="route_generation",
        provider="openai_compatible",
        model="deepseek-v4-flash",
        input_chars=1000,
        output_chars=1000,
        duration_ms=1000,
        success=True,
        retry_index=1,
        max_retries=1,
    )

    summary = build_run_summary(workflow_run_id)

    assert summary["retry_count"] >= 1
    assert summary["failed_model_call_count"] == 0
    assert summary["retryable_error_count"] == 0
    assert summary["health_status"] == "warning"
    assert summary["success"] is True


def test_error_run_summary_is_failed():
    workflow_run_id = generate_workflow_run_id("summary_failed")
    record_workflow_trace(
        workflow_run_id=workflow_run_id,
        node_name="generate_route_node",
        current_stage="error",
        success=False,
        duration_ms=100,
        error_message="模型调用失败",
    )

    summary = build_run_summary(workflow_run_id)

    assert summary["success"] is False
    assert summary["health_status"] == "failed"
    assert summary["error_count"] >= 1
    assert "模型调用失败" in summary["error_messages"]


def test_empty_records_summary_does_not_crash():
    summary = build_run_summary("not_exists")

    assert summary["success"] is False
    assert summary["health_status"] == "failed"
    assert summary["node_count"] == 0
    assert summary["model_call_count"] == 0
    assert summary["retrieval_count"] == 0
    assert summary["retry_count"] == 0


def test_summary_does_not_include_sensitive_fields():
    workflow_run_id = generate_workflow_run_id("summary_safe")
    _write_success_records(workflow_run_id)

    summary = build_run_summary(workflow_run_id)
    serialized = json.dumps(summary, ensure_ascii=False).lower()

    assert "api_key" not in serialized
    assert "authorization" not in serialized
    assert "prompt" not in serialized
    assert "response" not in serialized
    assert "sk-" not in serialized


if __name__ == "__main__":
    test_success_run_summary_is_healthy()
    test_correction_run_summary_is_warning()
    test_retry_run_summary_is_warning()
    test_error_run_summary_is_failed()
    test_empty_records_summary_does_not_crash()
    test_summary_does_not_include_sensitive_fields()
    print("test_observability_report.py: all tests passed")
