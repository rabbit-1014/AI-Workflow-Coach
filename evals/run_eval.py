from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval_cases import EVAL_CASES
from graph.workflow import build_blockage_workflow, build_route_workflow
from schemas import BlockageOutput, RouteOutput, RouteStep


def _fake_route_output(user_goal: str) -> RouteOutput:
    return RouteOutput(
        task_summary=f"评估路线：{user_goal}",
        route_type="eval_minimal_route",
        steps=[
            RouteStep(
                step_name="确定最小目标",
                step_goal="把用户目标收敛成一个可执行的小闭环",
                primary_tool="MockTool",
                backup_tool="Manual",
                suggested_input=user_goal,
                expected_output="一个可执行目标",
                execution_tip="先验证最短路径",
                ready_check="目标足够明确",
            )
        ],
    )


def _fake_blockage_output() -> BlockageOutput:
    return BlockageOutput(
        why_stuck="评估卡点原因",
        substeps=["拆成一个更小的动作"],
        simple_input="评估用最小输入",
        alternative_tool="评估替代工具",
        done_check="评估完成标准",
    )


def _patch_external_dependencies() -> None:
    import graph.nodes as nodes

    nodes.rag_service.retrieve_for_route = lambda user_goal: []
    nodes.rag_service.format_route_context = lambda docs: "eval route context"
    nodes.route_generator.generate_route = (
        lambda user_goal, route_context: _fake_route_output(user_goal)
    )

    nodes.rag_service.retrieve_for_blockage = (
        lambda user_goal, selected_step, blockage_text: []
    )
    nodes.rag_service.format_blockage_context = lambda docs: "eval blockage context"
    nodes.blockage_solver.solve_blockage = lambda **kwargs: _fake_blockage_output()


def _actual_value(state: dict[str, Any], check_name: str) -> Any:
    if check_name == "has_route_result":
        return state.get("route_result") is not None
    if check_name == "has_followup_question":
        return bool(state.get("followup_question"))
    if check_name == "has_effective_goal":
        return bool(state.get("effective_goal"))
    if check_name == "has_blockage_result":
        return state.get("blockage_result") is not None
    return state.get(check_name)


def _check_expected(state: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    failures = []
    for check_name, expected_value in expected.items():
        actual_value = _actual_value(state, check_name)
        if actual_value != expected_value:
            failures.append(
                f"expected {check_name}={expected_value!r}, got {actual_value!r}"
            )
    return failures


def _run_case(case: dict[str, Any], route_app: Any, blockage_app: Any) -> dict[str, Any]:
    case_type = case["case_type"]
    case_input = case["input"]

    if case_type == "blockage":
        final_state = blockage_app.invoke(case_input)
    else:
        final_state = route_app.invoke(case_input)

    failures = _check_expected(final_state, case["expected"])
    return {
        "case_id": case["case_id"],
        "case_type": case_type,
        "passed": not failures,
        "failures": failures,
    }


def main() -> int:
    _patch_external_dependencies()
    route_app = build_route_workflow()
    blockage_app = build_blockage_workflow()

    results = []
    for case in EVAL_CASES:
        result = _run_case(case, route_app, blockage_app)
        results.append(result)

        status = "PASS" if result["passed"] else "FAIL"
        print(
            f"case_id={result['case_id']} "
            f"case_type={result['case_type']} "
            f"{status}"
        )
        for failure in result["failures"]:
            print(f"  - {failure}")

    total_cases = len(results)
    passed = sum(1 for result in results if result["passed"])
    failed = total_cases - passed
    pass_rate = (passed / total_cases * 100) if total_cases else 0.0

    print("")
    print(f"total_cases = {total_cases}")
    print(f"passed = {passed}")
    print(f"failed = {failed}")
    print(f"pass_rate = {pass_rate:.1f}%")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
