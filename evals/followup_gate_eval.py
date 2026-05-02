from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from followup_gate_cases import FOLLOWUP_GATE_CASES
from graph.nodes import _should_ask_followup, analyze_task_node


REQUIRED_BUCKET_HINTS = [
    "AI 学习辅助",
    "AI 内容创作",
    "AI 动漫短剧/短视频",
]


def _has_required_bucket_hints(question: str) -> bool:
    return all(hint in question for hint in REQUIRED_BUCKET_HINTS)


def _run_case(case: dict) -> dict:
    state = analyze_task_node({"user_goal": case["user_goal"]})
    helper_need_followup = _should_ask_followup(case["user_goal"])
    node_need_followup = state.get("need_followup")
    followup_question = state.get("followup_question", "")
    expected_need_followup = case["expected_need_followup"]

    need_followup_ok = (
        helper_need_followup == expected_need_followup
        and node_need_followup == expected_need_followup
    )

    if case["expected_bucket_hint_required"]:
        question_ok = bool(followup_question) and _has_required_bucket_hints(followup_question)
    else:
        question_ok = not followup_question

    return {
        "case_id": case["case_id"],
        "user_goal": case["user_goal"],
        "expected_need_followup": expected_need_followup,
        "helper_need_followup": helper_need_followup,
        "node_need_followup": node_need_followup,
        "followup_question": followup_question,
        "need_followup_ok": need_followup_ok,
        "question_ok": question_ok,
        "passed": need_followup_ok and question_ok,
        "notes": case["notes"],
    }


def main() -> int:
    results = [_run_case(case) for case in FOLLOWUP_GATE_CASES]
    passed = [result for result in results if result["passed"]]
    failed = [result for result in results if not result["passed"]]

    print("# 首轮补问判断专项测试")
    print()
    print(f"- total_cases: {len(results)}")
    print(f"- passed: {len(passed)}")
    print(f"- failed: {len(failed)}")
    print()

    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"## {result['case_id']} [{status}]")
        print(f"- user_goal: {result['user_goal']}")
        print(f"- expected_need_followup: {result['expected_need_followup']}")
        print(f"- helper_need_followup: {result['helper_need_followup']}")
        print(f"- node_need_followup: {result['node_need_followup']}")
        print(f"- need_followup_ok: {result['need_followup_ok']}")
        print(f"- question_ok: {result['question_ok']}")
        print(f"- followup_question: {result['followup_question']}")
        print(f"- notes: {result['notes']}")
        print()

    if failed:
        print("FAILED_CASES=" + ",".join(result["case_id"] for result in failed))
        return 1

    print("FAILED_CASES=")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
