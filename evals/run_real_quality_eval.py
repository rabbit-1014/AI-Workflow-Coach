from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from graph.workflow import build_route_workflow
from real_quality_cases import REAL_QUALITY_CASES
from utils.observability import read_observability_records


REPORTS_DIR = Path(__file__).resolve().parent / "reports"
RESULTS_PATH = REPORTS_DIR / "latest_real_quality_results.json"
REPORT_PATH = REPORTS_DIR / "latest_real_quality_report.md"
VECTOR_STORE_DIR = PROJECT_ROOT / "vector_store" / "chroma_db"

ROUTE_STEP_REQUIRED_FIELDS = [
    "step_name",
    "step_goal",
    "primary_tool",
    "backup_tool",
    "suggested_input",
    "expected_output",
    "execution_tip",
    "ready_check",
]


def _field(value: Any, name: str, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _model_dump(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [_model_dump(item) for item in value]
    if isinstance(value, dict):
        return {key: _model_dump(item) for key, item in value.items()}
    return value


def _git_commit() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return completed.stdout.strip()
    except Exception:
        return ""


def _select_cases(limit: int | None, case_id: str | None) -> list[dict[str, Any]]:
    cases = list(REAL_QUALITY_CASES)
    if case_id:
        cases = [case for case in cases if case["case_id"] == case_id]
        if not cases:
            raise ValueError(f"unknown case_id: {case_id}")
    if limit is not None:
        cases = cases[:limit]
    return cases


def _invoke_route_case(app: Any, case: dict[str, Any]) -> dict[str, Any]:
    first_state = app.invoke({"user_goal": case["user_goal"]})
    followup_answer = (case.get("followup_answer") or "").strip()
    if first_state.get("need_followup") and followup_answer:
        second_input = {
            "user_goal": case["user_goal"],
            "followup_answer": followup_answer,
            "workflow_run_id": first_state.get("workflow_run_id", ""),
        }
        return app.invoke(second_input)
    return first_state


def _route_step_names(route_result: Any) -> list[str]:
    steps = _field(route_result, "steps", []) or []
    return [str(_field(step, "step_name", "")) for step in steps]


def _required_fields_complete(route_result: Any) -> bool:
    if route_result is None:
        return False
    steps = _field(route_result, "steps", []) or []
    if not steps:
        return False
    for step in steps:
        for field_name in ROUTE_STEP_REQUIRED_FIELDS:
            if not str(_field(step, field_name, "") or "").strip():
                return False
    return True


def _retrieved_sources(route_context: str) -> list[str]:
    sources = []
    for source in re.findall(r"^source:\s*(.+)$", route_context or "", flags=re.MULTILINE):
        source = source.strip()
        if source and source not in sources:
            sources.append(source)
    return sources


def _retrieved_snippet_preview(route_context: str, max_items: int = 3, max_chars: int = 120) -> list[dict[str, Any]]:
    if not route_context:
        return []

    previews = []
    for block in re.split(r"(?=【片段\s+\d+】)", route_context):
        if "content:" not in block:
            continue
        source = _match_line(block, "source")
        file_name = _match_line(block, "file_name")
        section_index = _match_line(block, "section_index")
        chunk_index = _match_line(block, "chunk_index")
        content = block.split("content:", 1)[1].strip()
        content = re.split(r"\n---\n|# Workflow 模板片段|# 卡点提醒片段", content, maxsplit=1)[0]
        excerpt = " ".join(content.split())[:max_chars]
        previews.append(
            {
                "source": source,
                "file_name": file_name,
                "section_index": section_index,
                "chunk_index": chunk_index,
                "excerpt": excerpt,
            }
        )
        if len(previews) >= max_items:
            break
    return previews


def _route_context_preview(route_context: str, max_chars: int = 300) -> str:
    return (route_context or "")[:max_chars]


def _match_line(text: str, name: str) -> str:
    match = re.search(rf"^{re.escape(name)}:\s*(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def _failure_type(case: dict[str, Any], final_state: dict[str, Any], error: str, route_generated: bool) -> str:
    if error:
        lowered = error.lower()
        if "routeoutput" in lowered or "json" in lowered or "schema" in lowered:
            return "schema_failure"
        if "retrieve" in lowered or "chroma" in lowered or "embedding" in lowered:
            return "retrieval_failure"
        if "llm" in lowered or "api" in lowered or "openai" in lowered or "dashscope" in lowered:
            return "model_failure"
        return "unknown_failure"

    if final_state.get("error_message"):
        message = str(final_state.get("error_message"))
        lowered = message.lower()
        if "retrieve" in lowered:
            return "retrieval_failure"
        if "llm" in lowered or "api" in lowered:
            return "model_failure"
        if "routeoutput" in lowered or "json" in lowered:
            return "schema_failure"
        return "workflow_failure"

    if final_state.get("need_followup") and not route_generated:
        return "followup_required"

    if case.get("should_generate_route") and not route_generated:
        return "route_not_generated"

    return "none"


def _summarize_observability(workflow_run_id: str) -> dict[str, Any]:
    records = read_observability_records(workflow_run_id)
    retrieval_trace = records["retrieval_trace"]
    model_call_log = records["model_call_log"]
    return {
        "retrieval_doc_count": sum(int(record.get("doc_count") or 0) for record in retrieval_trace),
        "self_correction_count": sum(1 for record in model_call_log if record.get("is_correction")),
        "model_call_count": len(model_call_log),
        "retrieval_count": len(retrieval_trace),
        "retrieval_trace_available": bool(retrieval_trace),
    }


def _run_case(app: Any, case: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    final_state: dict[str, Any] = {}
    error = ""
    try:
        final_state = _invoke_route_case(app, case)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    latency_ms = int((time.perf_counter() - start) * 1000)

    route_result = final_state.get("route_result") if final_state else None
    route_context = final_state.get("route_context", "") if final_state else ""
    workflow_run_id = final_state.get("workflow_run_id", "") if final_state else ""
    obs = _summarize_observability(workflow_run_id) if workflow_run_id else {
        "retrieval_doc_count": 0,
        "self_correction_count": None,
        "model_call_count": 0,
        "retrieval_count": 0,
        "retrieval_trace_available": False,
    }

    route_generated = route_result is not None
    schema_valid = route_generated
    required_fields_complete = _required_fields_complete(route_result)
    failure_type = _failure_type(case, final_state, error, route_generated)

    notes = case.get("notes", "")
    if obs["self_correction_count"] is None:
        notes = f"{notes} self_correction_count unavailable without changing business code.".strip()
    if not route_context and route_generated:
        notes = f"{notes} retrieved_snippet_preview unavailable: route_context empty.".strip()

    return {
        "case_id": case["case_id"],
        "scenario": case["scenario"],
        "user_goal": case["user_goal"],
        "followup_answer": case.get("followup_answer", ""),
        "expected_behavior": case["expected_behavior"],
        "should_generate_route": case["should_generate_route"],
        "final_stage": final_state.get("current_stage", "") if final_state else "",
        "route_generated": route_generated,
        "schema_valid": schema_valid,
        "json_parse_success": schema_valid,
        "step_count": len(_field(route_result, "steps", []) or []),
        "required_fields_complete": required_fields_complete,
        "route_step_names": _route_step_names(route_result),
        "retrieval_count": obs["retrieval_count"],
        "retrieval_doc_count": obs["retrieval_doc_count"],
        "retrieved_sources": _retrieved_sources(route_context),
        "retrieved_snippet_preview": _retrieved_snippet_preview(route_context),
        "route_context_chars": len(route_context or ""),
        "route_context_preview": _route_context_preview(route_context),
        "model_call_count": obs["model_call_count"],
        "chroma_db_exists": VECTOR_STORE_DIR.exists(),
        "vector_store_dir": str(VECTOR_STORE_DIR),
        "retrieval_trace_available": obs["retrieval_trace_available"],
        "latency_ms": latency_ms,
        "failure_type": failure_type,
        "self_correction_count": obs["self_correction_count"],
        "manual_tool_fit_score": None,
        "manual_actionability_score": None,
        "manual_specificity_score": None,
        "manual_assumption_control_score": None,
        "manual_overall_quality_score": None,
        "notes": notes,
        "workflow_run_id": workflow_run_id,
        "error_message": error or final_state.get("error_message", ""),
        "route_result": _model_dump(route_result),
    }


def _average(values: list[int]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def _build_payload(results: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    failure_counts = Counter(result["failure_type"] for result in results)
    latencies = [int(result.get("latency_ms") or 0) for result in results]
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "git_commit": _git_commit(),
        "mode": "real manual eval",
        "limit": args.limit,
        "case_id": args.case_id,
        "total_cases": len(results),
        "route_generated_count": sum(1 for result in results if result["route_generated"]),
        "schema_valid_count": sum(1 for result in results if result["schema_valid"]),
        "average_latency_ms": _average(latencies),
        "failure_type_distribution": dict(failure_counts),
        "manual_scoring_scale": {
            "0": "明显失败",
            "1": "可用但有明显问题",
            "2": "质量好，可作为展示样例",
            "null": "尚未人工复盘",
        },
        "results": results,
    }


def _build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# P1 Real Quality Evaluation Baseline",
        "",
        "P1 real quality eval is manual-only and should not be used as CI gate.",
        "P1 真实质量评估仅用于手动评估，不应作为 CI（持续集成）门禁。",
        "",
        f"- 运行时间: {payload['generated_at']}",
        f"- Git commit: {payload['git_commit']}",
        f"- 运行模式: {payload['mode']}",
        f"- case 总数: {payload['total_cases']}",
        f"- route_generated 数量: {payload['route_generated_count']}",
        f"- schema_valid 数量: {payload['schema_valid_count']}",
        f"- 平均 latency_ms: {payload['average_latency_ms']}",
        f"- failure_type 分布: {payload['failure_type_distribution']}",
        "",
        "## Case 明细",
        "",
        "| case_id | 场景 | final_stage | route_generated | schema_valid | step_count | latency_ms | retrieval_doc_count | failure_type |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for result in payload["results"]:
        lines.append(
            "| {case_id} | {scenario} | {final_stage} | {route_generated} | {schema_valid} | {step_count} | {latency_ms} | {retrieval_doc_count} | {failure_type} |".format(
                **result
            )
        )

    lines.extend(["", "## Route Step Names 摘要", ""])
    for result in payload["results"]:
        names = " / ".join(result["route_step_names"]) if result["route_step_names"] else "(none)"
        lines.append(f"- {result['case_id']}: {names}")

    lines.extend(["", "## Retrieval 摘要", ""])
    for result in payload["results"]:
        sources = ", ".join(result["retrieved_sources"]) if result["retrieved_sources"] else "(none)"
        lines.append(
            f"- {result['case_id']}: doc_count={result['retrieval_doc_count']}, sources={sources}"
        )

    lines.extend(
        [
            "",
            "## 人工评分字段说明",
            "",
            "- manual_tool_fit_score: 工具匹配，0/1/2/null",
            "- manual_actionability_score: 可执行性，0/1/2/null",
            "- manual_specificity_score: 具体程度，0/1/2/null",
            "- manual_assumption_control_score: 假设控制，0/1/2/null",
            "- manual_overall_quality_score: 总体质量，0/1/2/null",
            "",
            "## 下一步建议",
            "",
            "- 先人工复盘 `manual_*` 字段，不要把本报告接入 CI。",
            "- 如果 route 质量稳定，再进入 P2 RAG Ablation。",
            "- 如果出现 retrieval_doc_count 为 0 或明显跑偏，优先复盘知识库和检索片段。",
            "- 如果出现 schema_failure/model_failure，再单独开修复任务。",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run P1 real route quality eval.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--case-id", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cases = _select_cases(args.limit, args.case_id or None)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    app = build_route_workflow()
    results = [_run_case(app, case) for case in cases]
    payload = _build_payload(results, args)

    RESULTS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    REPORT_PATH.write_text(_build_markdown(payload), encoding="utf-8")

    print("P1 Real Quality Evaluation Baseline")
    print(f"total_cases: {payload['total_cases']}")
    print(f"route_generated: {payload['route_generated_count']}")
    print(f"schema_valid: {payload['schema_valid_count']}")
    print(f"average_latency_ms: {payload['average_latency_ms']}")
    print(f"failure_type_distribution: {payload['failure_type_distribution']}")
    print(f"results_json: {RESULTS_PATH}")
    print(f"report_md: {REPORT_PATH}")

    hard_failures = [
        result
        for result in results
        if result["should_generate_route"] and result["failure_type"] != "none"
    ]
    return 1 if hard_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
