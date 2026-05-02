import contextvars
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from config import LOG_DIR


OBSERVABILITY_DIR = LOG_DIR / "observability"
WORKFLOW_TRACE_PATH = OBSERVABILITY_DIR / "workflow_trace.jsonl"
MODEL_CALL_LOG_PATH = OBSERVABILITY_DIR / "model_call_log.jsonl"
RETRIEVAL_TRACE_PATH = OBSERVABILITY_DIR / "retrieval_trace.jsonl"

_workflow_run_id_var = contextvars.ContextVar("workflow_run_id", default="")
_call_type_var = contextvars.ContextVar("call_type", default="")


def _timestamp() -> str:
    return datetime.now().isoformat(timespec="milliseconds")


def _duration_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def _write_jsonl(path: Path, payload: dict[str, Any]) -> None:
    OBSERVABILITY_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")


def _read_jsonl_by_workflow_id(path: Path, workflow_run_id: str) -> list[dict[str, Any]]:
    if not workflow_run_id or not path.exists():
        return []

    records = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("workflow_run_id") == workflow_run_id:
                records.append(record)
    return records


def generate_workflow_run_id(prefix: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    safe_prefix = (prefix or "workflow").strip() or "workflow"
    return f"{safe_prefix}_{timestamp}_{suffix}"


def get_or_create_workflow_run_id(state: dict, prefix: str) -> str:
    workflow_run_id = (state or {}).get("workflow_run_id", "")
    if workflow_run_id:
        return workflow_run_id
    return generate_workflow_run_id(prefix)


def record_workflow_trace(
    workflow_run_id: str,
    node_name: str,
    current_stage: str,
    success: bool,
    duration_ms: int,
    error_message: str = "",
    extra: dict | None = None,
) -> None:
    payload = {
        "timestamp": _timestamp(),
        "workflow_run_id": workflow_run_id,
        "node_name": node_name,
        "current_stage": current_stage,
        "success": success,
        "duration_ms": duration_ms,
        "error_message": error_message,
        "extra": extra or {},
    }
    _write_jsonl(WORKFLOW_TRACE_PATH, payload)


def record_model_call_log(
    workflow_run_id: str,
    call_type: str,
    provider: str,
    model: str,
    input_chars: int,
    output_chars: int,
    duration_ms: int,
    success: bool,
    error_type: str = "",
    error_message: str = "",
    is_correction: bool = False,
    retry_index: int = 0,
    max_retries: int = 0,
) -> None:
    payload = {
        "timestamp": _timestamp(),
        "workflow_run_id": workflow_run_id,
        "call_type": call_type,
        "provider": provider,
        "model": model,
        "input_chars": input_chars,
        "output_chars": output_chars,
        "duration_ms": duration_ms,
        "success": success,
        "error_type": error_type,
        "error_message": error_message,
        "is_correction": is_correction,
        "retry_index": retry_index,
        "max_retries": max_retries,
    }
    _write_jsonl(MODEL_CALL_LOG_PATH, payload)


def record_retrieval_trace(
    workflow_run_id: str,
    retrieval_type: str,
    query_chars: int,
    top_k: int | None,
    doc_count: int,
    duration_ms: int,
    success: bool,
    error_type: str = "",
    error_message: str = "",
) -> None:
    payload = {
        "timestamp": _timestamp(),
        "workflow_run_id": workflow_run_id,
        "retrieval_type": retrieval_type,
        "query_chars": query_chars,
        "top_k": top_k,
        "doc_count": doc_count,
        "duration_ms": duration_ms,
        "success": success,
        "error_type": error_type,
        "error_message": error_message,
    }
    _write_jsonl(RETRIEVAL_TRACE_PATH, payload)


def read_observability_records(workflow_run_id: str) -> dict[str, list[dict[str, Any]]]:
    return {
        "workflow_trace": _read_jsonl_by_workflow_id(
            WORKFLOW_TRACE_PATH,
            workflow_run_id,
        ),
        "model_call_log": _read_jsonl_by_workflow_id(
            MODEL_CALL_LOG_PATH,
            workflow_run_id,
        ),
        "retrieval_trace": _read_jsonl_by_workflow_id(
            RETRIEVAL_TRACE_PATH,
            workflow_run_id,
        ),
    }


def set_observability_context(workflow_run_id: str, call_type: str = ""):
    workflow_token = _workflow_run_id_var.set(workflow_run_id or "")
    call_type_token = _call_type_var.set(call_type or "")
    return workflow_token, call_type_token


def reset_observability_context(token) -> None:
    workflow_token, call_type_token = token
    _workflow_run_id_var.reset(workflow_token)
    _call_type_var.reset(call_type_token)


def get_current_workflow_run_id() -> str:
    return _workflow_run_id_var.get()


def get_current_call_type() -> str:
    return _call_type_var.get()


def elapsed_ms(start: float) -> int:
    return _duration_ms(start)
