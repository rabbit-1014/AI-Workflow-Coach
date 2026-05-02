from utils.observability import read_observability_records
from utils.error_utils import RETRYABLE_ERROR_TYPES


def _sum_duration(records: list[dict]) -> int:
    return sum(int(record.get("duration_ms") or 0) for record in records)


def _collect_errors(*record_groups: list[dict]) -> list[str]:
    error_messages = []
    for records in record_groups:
        for record in records:
            error_message = record.get("error_message", "")
            if record.get("success") is False or error_message:
                error_messages.append(error_message or "未知错误")
    return error_messages


def _collect_unresolved_model_errors(model_call_log: list[dict]) -> list[str]:
    error_messages = []
    for index, record in enumerate(model_call_log):
        error_message = record.get("error_message", "")
        if record.get("success") is not False and not error_message:
            continue

        call_type = record.get("call_type", "")
        has_later_success = any(
            later_record.get("call_type", "") == call_type
            and later_record.get("success") is True
            for later_record in model_call_log[index + 1:]
        )
        if has_later_success:
            continue

        error_messages.append(error_message or "未知错误")

    return error_messages


def _health_status(
    success: bool,
    error_count: int,
    final_stage: str,
    correction_count: int,
    retry_count: int,
    slowest_node_duration_ms: int,
    model_total_duration_ms: int,
) -> str:
    if error_count > 0 or final_stage == "error" or not success:
        return "failed"
    if (
        correction_count > 0
        or retry_count > 0
        or slowest_node_duration_ms > 20000
        or model_total_duration_ms > 30000
    ):
        return "warning"
    return "healthy"


def build_run_summary(workflow_run_id: str) -> dict:
    records = read_observability_records(workflow_run_id)
    workflow_trace = records["workflow_trace"]
    model_call_log = records["model_call_log"]
    retrieval_trace = records["retrieval_trace"]

    final_stage = workflow_trace[-1].get("current_stage", "") if workflow_trace else ""
    error_messages = (
        _collect_errors(workflow_trace, retrieval_trace)
        + _collect_unresolved_model_errors(model_call_log)
    )
    error_count = len(error_messages)
    success = error_count == 0 and final_stage not in {"error", ""}

    node_names = [record.get("node_name", "") for record in workflow_trace]
    total_node_duration_ms = _sum_duration(workflow_trace)
    slowest_node_record = max(
        workflow_trace,
        key=lambda record: int(record.get("duration_ms") or 0),
        default={},
    )
    slowest_node = slowest_node_record.get("node_name", "")
    slowest_node_duration_ms = int(slowest_node_record.get("duration_ms") or 0)

    model_total_duration_ms = _sum_duration(model_call_log)
    model_provider = model_call_log[-1].get("provider", "") if model_call_log else ""
    model_name = model_call_log[-1].get("model", "") if model_call_log else ""
    input_chars_total = sum(int(record.get("input_chars") or 0) for record in model_call_log)
    output_chars_total = sum(int(record.get("output_chars") or 0) for record in model_call_log)
    correction_count = sum(1 for record in model_call_log if record.get("is_correction"))
    retry_count = sum(
        1 for record in model_call_log if int(record.get("retry_index") or 0) > 0
    )
    failed_model_call_count = sum(
        1 for record in model_call_log if record.get("success") is False
    )
    retryable_error_count = sum(
        1
        for record in model_call_log
        if record.get("success") is False
        and record.get("error_type") in RETRYABLE_ERROR_TYPES
    )

    retrieval_total_duration_ms = _sum_duration(retrieval_trace)
    retrieved_doc_count_total = sum(
        int(record.get("doc_count") or 0) for record in retrieval_trace
    )
    retrieval_types = []
    for record in retrieval_trace:
        retrieval_type = record.get("retrieval_type", "")
        if retrieval_type and retrieval_type not in retrieval_types:
            retrieval_types.append(retrieval_type)

    health_status = _health_status(
        success=success,
        error_count=error_count,
        final_stage=final_stage,
        correction_count=correction_count,
        retry_count=retry_count,
        slowest_node_duration_ms=slowest_node_duration_ms,
        model_total_duration_ms=model_total_duration_ms,
    )

    return {
        "workflow_run_id": workflow_run_id,
        "success": success,
        "health_status": health_status,
        "final_stage": final_stage,
        "error_count": error_count,
        "error_messages": error_messages[:5],
        "node_count": len(workflow_trace),
        "node_names": node_names,
        "total_node_duration_ms": total_node_duration_ms,
        "slowest_node": slowest_node,
        "slowest_node_duration_ms": slowest_node_duration_ms,
        "model_call_count": len(model_call_log),
        "model_total_duration_ms": model_total_duration_ms,
        "model_provider": model_provider,
        "model_name": model_name,
        "input_chars_total": input_chars_total,
        "output_chars_total": output_chars_total,
        "correction_count": correction_count,
        "retry_count": retry_count,
        "failed_model_call_count": failed_model_call_count,
        "retryable_error_count": retryable_error_count,
        "retrieval_count": len(retrieval_trace),
        "retrieval_total_duration_ms": retrieval_total_duration_ms,
        "retrieved_doc_count_total": retrieved_doc_count_total,
        "retrieval_types": retrieval_types,
    }
