from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


LOCAL_TESTS = [
    "test_error_utils.py",
    "test_llm_retry.py",
    "test_retrieval_error_handling.py",
    "test_observability_report.py",
    "test_observability.py",
    "test_self_correction.py",
    "test_workflow.py",
    "test_direction_choice.py",
    "test_node_error_handling.py",
    "test_llm_provider_config.py",
    "evals/followup_gate_eval.py",
]


def _tail_lines(text: str, limit: int = 40) -> str:
    lines = (text or "").splitlines()
    return "\n".join(lines[-limit:])


def _format_command(command: list[str]) -> str:
    return " ".join(command)


def run_command(name: str, command: list[str]) -> dict[str, Any]:
    start = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    duration_seconds = round(time.perf_counter() - start, 2)
    return {
        "name": name,
        "command": _format_command(command),
        "passed": completed.returncode == 0,
        "duration_seconds": duration_seconds,
        "return_code": completed.returncode,
        "stdout_tail": _tail_lines(completed.stdout),
        "stderr_tail": _tail_lines(completed.stderr),
    }


def build_local_test_commands() -> list[tuple[str, list[str]]]:
    return [
        (test_path, [sys.executable, test_path])
        for test_path in LOCAL_TESTS
    ]


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    passed_count = sum(1 for result in results if result.get("passed"))
    total = len(results)
    failed_count = total - passed_count
    return {
        "total": total,
        "passed": passed_count,
        "failed": failed_count,
        "overall_passed": failed_count == 0,
        "duration_seconds": round(
            sum(float(result.get("duration_seconds") or 0) for result in results),
            2,
        ),
    }


def _get_value(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _summary_key_fields(summary: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "success",
        "health_status",
        "final_stage",
        "error_count",
        "model_call_count",
        "retry_count",
        "retrieval_count",
        "retrieved_doc_count_total",
    ]
    return {key: summary.get(key) for key in keys}


def run_real_route_smoke() -> dict[str, Any]:
    from graph.workflow import build_route_workflow
    from utils.observability_report import build_run_summary

    final_state = build_route_workflow().invoke({
        "user_goal": "做一套小红书文案生成流程，能批量出标题、正文和封面文案",
    })
    route_result = final_state.get("route_result")
    steps = _get_value(route_result, "steps", []) or []
    workflow_run_id = final_state.get("workflow_run_id", "")
    summary = build_run_summary(workflow_run_id) if workflow_run_id else {}

    passed = (
        final_state.get("current_stage") == "route_generated"
        and not final_state.get("error_message")
        and route_result is not None
        and bool(workflow_run_id)
        and bool(summary)
    )
    return {
        "name": "real_route_smoke",
        "passed": passed,
        "workflow_run_id": workflow_run_id,
        "current_stage": final_state.get("current_stage", ""),
        "error_message": final_state.get("error_message", ""),
        "step_count": len(steps),
        "summary": _summary_key_fields(summary),
    }


def run_real_blockage_smoke() -> dict[str, Any]:
    from graph.workflow import build_blockage_workflow
    from utils.observability_report import build_run_summary

    final_state = build_blockage_workflow().invoke({
        "user_goal": "做一套小红书文案生成流程，能批量出标题、正文和封面文案",
        "effective_goal": "做一套小红书文案生成流程，能批量出标题、正文和封面文案",
        "selected_step": "包装标题和封面",
        "blockage_text": "我生成的封面标题看起来很普通，点击吸引力不强",
    })
    blockage_result = final_state.get("blockage_result")
    substeps = _get_value(blockage_result, "substeps", []) or []
    workflow_run_id = final_state.get("workflow_run_id", "")
    summary = build_run_summary(workflow_run_id) if workflow_run_id else {}

    passed = (
        final_state.get("current_stage") == "blockage_solved"
        and not final_state.get("error_message")
        and blockage_result is not None
        and bool(workflow_run_id)
        and bool(summary)
    )
    return {
        "name": "real_blockage_smoke",
        "passed": passed,
        "workflow_run_id": workflow_run_id,
        "current_stage": final_state.get("current_stage", ""),
        "error_message": final_state.get("error_message", ""),
        "substeps_count": len(substeps),
        "summary": _summary_key_fields(summary),
    }


def run_local_checks() -> list[dict[str, Any]]:
    return [
        run_command(name, command)
        for name, command in build_local_test_commands()
    ]


def _print_result(result: dict[str, Any]) -> None:
    status = "PASS" if result["passed"] else "FAIL"
    print(f"[{status}] {result['name']} ({result['duration_seconds']}s)")
    if result["passed"]:
        return

    print(f"  command: {result['command']}")
    print(f"  return_code: {result['return_code']}")
    if result.get("stdout_tail"):
        print("  stdout_tail:")
        print(result["stdout_tail"])
    if result.get("stderr_tail"):
        print("  stderr_tail:")
        print(result["stderr_tail"])


def _print_real_smoke_result(result: dict[str, Any]) -> None:
    status = "PASS" if result["passed"] else "FAIL"
    print(f"[{status}] {result['name']}")
    print(f"  workflow_run_id: {result.get('workflow_run_id', '')}")
    print(f"  current_stage: {result.get('current_stage', '')}")
    print(f"  error_message: {result.get('error_message', '')}")
    if "step_count" in result:
        print(f"  step_count: {result['step_count']}")
    if "substeps_count" in result:
        print(f"  substeps_count: {result['substeps_count']}")
    print(f"  summary: {result.get('summary', {})}")


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Workflow Coach smoke check")
    parser.add_argument(
        "--mode",
        choices=["local", "real"],
        default="local",
        help="local runs non-network tests; real also runs minimal external API smoke checks.",
    )
    args = parser.parse_args()

    start = time.perf_counter()
    print("AI Workflow Coach Smoke Check")
    print()
    print(f"Mode: {args.mode}")
    print()

    if args.mode == "real":
        print("真实链路模式会调用外部 API，可能产生费用和网络等待。")
        print()

    results = run_local_checks()
    for result in results:
        _print_result(result)

    real_results = []
    if args.mode == "real" and all(result["passed"] for result in results):
        print()
        real_results = [run_real_route_smoke(), run_real_blockage_smoke()]
        for result in real_results:
            _print_real_smoke_result(result)

    summary = summarize_results(results)
    real_failed = sum(1 for result in real_results if not result["passed"])
    total = summary["total"] + len(real_results)
    passed = summary["passed"] + sum(1 for result in real_results if result["passed"])
    failed = summary["failed"] + real_failed
    duration_seconds = round(time.perf_counter() - start, 2)
    overall_passed = failed == 0

    print()
    print("Summary:")
    print(f"- total: {total}")
    print(f"- passed: {passed}")
    print(f"- failed: {failed}")
    print(f"- duration_seconds: {duration_seconds}")
    print()
    print(f"Result: {'PASS' if overall_passed else 'FAIL'}")
    return 0 if overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
