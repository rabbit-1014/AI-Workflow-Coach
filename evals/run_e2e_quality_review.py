from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from e2e_quality_cases import E2E_QUALITY_CASES
from graph.nodes import (
    analyze_task_node,
    close_followup_node,
    generate_route_node,
    retrieve_for_blockage_node,
    retrieve_for_route_node,
    solve_blockage_node,
)


OUTPUT_PATH = Path(__file__).with_name("e2e_quality_review.md")


def _get_field(value: Any, field_name: str, default: Any = "") -> Any:
    if isinstance(value, dict):
        return value.get(field_name, default)
    return getattr(value, field_name, default)


def _merge_state(state: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    merged = dict(state)
    merged.update(update)
    return merged


def _run_route_case(case_input: dict[str, Any]) -> dict[str, Any]:
    state: dict[str, Any] = dict(case_input)

    analyze_result = analyze_task_node(state)
    state = _merge_state(state, analyze_result)

    if state.get("need_close_followup"):
        close_result = close_followup_node(state)
        state = _merge_state(state, close_result)

    if not state.get("need_followup"):
        retrieve_result = retrieve_for_route_node(state)
        state = _merge_state(state, retrieve_result)
        generate_result = generate_route_node(state)
        state = _merge_state(state, generate_result)

    return state


def _run_blockage_case(case_input: dict[str, Any]) -> dict[str, Any]:
    state: dict[str, Any] = dict(case_input)
    retrieve_result = retrieve_for_blockage_node(state)
    state = _merge_state(state, retrieve_result)
    solve_result = solve_blockage_node(state)
    state = _merge_state(state, solve_result)
    return state


def _run_case(case: dict[str, Any]) -> dict[str, Any]:
    try:
        if case["case_type"] == "blockage":
            state = _run_blockage_case(case["input"])
        else:
            state = _run_route_case(case["input"])
        return {
            **case,
            "state": state,
            "error": "",
        }
    except Exception:
        return {
            **case,
            "state": dict(case["input"]),
            "error": traceback.format_exc(),
        }


def _render_process_info(state: dict[str, Any]) -> list[str]:
    return [
        f"- need_followup: {state.get('need_followup', '')}",
        f"- followup_question: {state.get('followup_question', '')}",
        f"- followup_answer: {state.get('followup_answer', '')}",
        f"- close_result: {state.get('close_result', '')}",
        f"- effective_goal: {state.get('effective_goal', '')}",
    ]


def _render_route_output(state: dict[str, Any]) -> list[str]:
    route_result = state.get("route_result")
    if not route_result:
        return ["- route_result: " + str(route_result)]

    lines = [
        f"- task_summary: {_get_field(route_result, 'task_summary')}",
        f"- route_type: {_get_field(route_result, 'route_type')}",
        "",
        "### steps",
    ]

    for index, step in enumerate(_get_field(route_result, "steps", []), start=1):
        lines.extend(
            [
                f"{index}. {_get_field(step, 'step_name')}",
                f"   - step_goal: {_get_field(step, 'step_goal')}",
                f"   - primary_tool: {_get_field(step, 'primary_tool')}",
                f"   - suggested_input: {_get_field(step, 'suggested_input')}",
                f"   - expected_output: {_get_field(step, 'expected_output')}",
                f"   - ready_check: {_get_field(step, 'ready_check')}",
            ]
        )

    return lines


def _render_blockage_output(state: dict[str, Any]) -> list[str]:
    blockage_result = state.get("blockage_result")
    if not blockage_result:
        return ["- blockage_result: " + str(blockage_result)]

    lines = [
        f"- why_stuck: {_get_field(blockage_result, 'why_stuck')}",
        "- substeps:",
    ]
    for substep in _get_field(blockage_result, "substeps", []):
        lines.append(f"  - {substep}")

    lines.extend(
        [
            f"- simple_input: {_get_field(blockage_result, 'simple_input')}",
            f"- alternative_tool: {_get_field(blockage_result, 'alternative_tool')}",
            f"- done_check: {_get_field(blockage_result, 'done_check')}",
        ]
    )
    return lines


def _render_manual_review(case_type: str) -> list[str]:
    if case_type == "blockage":
        return [
            "### 人工判断",
            "- 是否真能推进：",
            "- 是否比原路线更细：",
            "- 是否存在空话：",
            "- 是否需要后续修复：",
            "- 备注：",
        ]

    return [
        "### 人工判断",
        "- 目标贴合度：",
        "- 步骤具体度：",
        "- 执行可行性：",
        "- 是否明显跑偏：",
        "- 是否需要后续修复：",
        "- 备注：",
    ]


def _render_case(result: dict[str, Any]) -> list[str]:
    state = result["state"]
    lines = [
        f"## {result['case_id']}",
        f"- bucket: {result['bucket']}",
        f"- case_type: {result['case_type']}",
        f"- input: {result['input']}",
        "",
        "### 过程信息",
        *_render_process_info(state),
        "",
        "### 最终输出",
    ]

    if result["error"]:
        lines.extend(["运行失败：", "```text", result["error"], "```"])
    elif result["case_type"] == "blockage":
        lines.extend(_render_blockage_output(state))
    else:
        lines.extend(_render_route_output(state))

    lines.extend(["", *_render_manual_review(result["case_type"]), ""])
    return lines


def main() -> int:
    results = [_run_case(case) for case in E2E_QUALITY_CASES]

    lines = [
        "# 三类主线端到端真实质量检查",
        "",
        "> 本文件由真实链路生成，只整理输入、过程和最终输出，不自动给质量结论。",
        "",
        f"- total_cases: {len(results)}",
        f"- failed_cases: {sum(1 for result in results if result['error'])}",
        "",
    ]

    for result in results:
        lines.extend(_render_case(result))

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"generated: {OUTPUT_PATH}")
    print(f"total_cases: {len(results)}")
    print(
        "failed_cases: "
        + ",".join(result["case_id"] for result in results if result["error"])
    )
    return 1 if any(result["error"] for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
