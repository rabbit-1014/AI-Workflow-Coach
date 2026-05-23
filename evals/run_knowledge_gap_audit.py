from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from graph.workflow import build_route_workflow
from knowledge_gap_audit_cases import KNOWLEDGE_GAP_AUDIT_CASES
from utils.observability import read_observability_records


REPORTS_DIR = Path(__file__).resolve().parent / "reports"
RESULTS_PATH = REPORTS_DIR / "latest_knowledge_gap_audit_results.json"
REPORT_PATH = REPORTS_DIR / "latest_knowledge_gap_audit_report.md"
P1_RESULTS_PATH = REPORTS_DIR / "latest_real_quality_results.json"

KNOWLEDGE_FILES = [
    PROJECT_ROOT / "knowledge" / "tools.md",
    PROJECT_ROOT / "knowledge" / "workflows.md",
    PROJECT_ROOT / "knowledge" / "blockages.md",
    PROJECT_ROOT / "knowledge" / "reference_workflow_patterns.md",
]

P1_CASE_FOCUS = {
    "shortdrama_core_01": ["动漫短剧", "角色", "分镜", "镜头", "剪辑", "成片"],
    "shortdrama_direct_01": ["60 秒", "动漫短剧", "高中生", "热血", "角色", "分镜", "剪辑"],
    "shortdrama_close_success_01": ["30 秒", "漫剧", "首集", "角色设定", "分镜脚本", "成片"],
    "content_direct_01": ["小红书", "图文", "学习效率", "标题", "正文", "封面"],
    "content_close_success_01": ["小红书", "文案", "标题", "正文", "封面", "批量"],
    "learning_direct_01": ["14 天", "英语", "阅读", "单词", "复习"],
    "learning_close_success_01": ["背单词", "例句", "测验", "错词", "复习"],
}


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
    cases = list(KNOWLEDGE_GAP_AUDIT_CASES)
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
        return app.invoke(
            {
                "user_goal": case["user_goal"],
                "followup_answer": followup_answer,
                "workflow_run_id": first_state.get("workflow_run_id", ""),
            }
        )
    return first_state


def _route_step_names(route_result: Any) -> list[str]:
    steps = _field(route_result, "steps", []) or []
    return [str(_field(step, "step_name", "") or "") for step in steps]


def _retrieved_sources(route_context: str) -> list[str]:
    sources: list[str] = []
    for source in re.findall(r"^source:\s*(.+)$", route_context or "", flags=re.MULTILINE):
        source = source.strip()
        if source and source not in sources:
            sources.append(source)
    return sources


def _match_line(text: str, name: str) -> str:
    match = re.search(rf"^{re.escape(name)}:\s*(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def _retrieved_snippet_preview(route_context: str, max_items: int = 3, max_chars: int = 140) -> list[dict[str, Any]]:
    if not route_context:
        return []

    previews: list[dict[str, Any]] = []
    blocks = re.split(r"(?=【片段\s*\d+】)", route_context)
    if len(blocks) <= 1:
        blocks = re.split(r"(?=source:\s*)", route_context)

    for block in blocks:
        if "content:" not in block:
            continue
        content = block.split("content:", 1)[1].strip()
        content = re.split(r"\n---\n|# Workflow|# 卡点|# 工具", content, maxsplit=1)[0]
        excerpt = " ".join(content.split())[:max_chars]
        previews.append(
            {
                "source": _match_line(block, "source"),
                "file_name": _match_line(block, "file_name"),
                "section_index": _match_line(block, "section_index"),
                "chunk_index": _match_line(block, "chunk_index"),
                "excerpt": excerpt,
            }
        )
        if len(previews) >= max_items:
            break
    return previews


def _summarize_observability(workflow_run_id: str) -> dict[str, Any]:
    try:
        records = read_observability_records(workflow_run_id)
    except Exception:
        return {
            "retrieval_doc_count": 0,
            "retrieval_count": 0,
            "model_call_count": 0,
            "self_correction_count": None,
            "retrieval_trace_available": False,
        }

    retrieval_trace = records["retrieval_trace"]
    model_call_log = records["model_call_log"]
    return {
        "retrieval_doc_count": sum(int(record.get("doc_count") or 0) for record in retrieval_trace),
        "retrieval_count": len(retrieval_trace),
        "model_call_count": len(model_call_log),
        "self_correction_count": sum(1 for record in model_call_log if record.get("is_correction")),
        "retrieval_trace_available": bool(retrieval_trace),
    }


def _failure_type(case: dict[str, Any], final_state: dict[str, Any], error: str, route_generated: bool) -> str:
    final_stage = str(final_state.get("current_stage", "") or "")
    if case.get("is_boundary") and not route_generated:
        if final_state.get("need_followup") or final_stage == "direction_choice_required":
            return "boundary_behavior"

    if error:
        lowered = error.lower()
        if "json" in lowered or "schema" in lowered or "routeoutput" in lowered:
            return "schema_failure"
        if "retrieve" in lowered or "chroma" in lowered or "embedding" in lowered:
            return "retrieval_failure"
        if "llm" in lowered or "api" in lowered or "openai" in lowered or "dashscope" in lowered:
            return "model_failure"
        return "unknown_failure"

    if final_state.get("error_message"):
        message = str(final_state.get("error_message"))
        lowered = message.lower()
        if "retrieve" in lowered or "chroma" in lowered:
            return "retrieval_failure"
        if "llm" in lowered or "api" in lowered:
            return "model_failure"
        if "json" in lowered or "schema" in lowered or "routeoutput" in lowered:
            return "schema_failure"
        return "workflow_failure"

    if final_state.get("need_followup") and not route_generated:
        return "followup_required"
    if case.get("should_generate_route") and not route_generated:
        return "route_not_generated"
    return "none"


def _keyword_hits(text: str, keywords: list[str]) -> list[str]:
    normalized = text or ""
    return [keyword for keyword in keywords if keyword and keyword in normalized]


def _preliminary_label(case: dict[str, Any], route_generated: bool, failure_type: str) -> str:
    if case.get("is_boundary"):
        return "boundary"
    if not route_generated or failure_type not in {"none", "boundary_behavior"}:
        return "failed"
    return "usable"


def _run_case(app: Any, case: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    final_state: dict[str, Any] = {}
    error = ""
    try:
        final_state = _invoke_route_case(app, case)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    latency_ms = int((time.perf_counter() - started) * 1000)

    route_result = final_state.get("route_result") if final_state else None
    route_context = final_state.get("route_context", "") if final_state else ""
    workflow_run_id = final_state.get("workflow_run_id", "") if final_state else ""
    obs = _summarize_observability(workflow_run_id) if workflow_run_id else {
        "retrieval_doc_count": 0,
        "retrieval_count": 0,
        "model_call_count": 0,
        "self_correction_count": None,
        "retrieval_trace_available": False,
    }

    route_generated = route_result is not None
    failure_type = _failure_type(case, final_state, error, route_generated)
    route_step_names = _route_step_names(route_result)
    focus_text = "\n".join(route_step_names) + "\n" + route_context
    focus_hits = _keyword_hits(focus_text, case.get("focus_keywords", []))

    return {
        "case_id": case["case_id"],
        "scenario": case["scenario"],
        "user_goal": case["user_goal"],
        "expected_focus": case.get("expected_focus", ""),
        "should_generate_route": case.get("should_generate_route", True),
        "is_boundary": case.get("is_boundary", False),
        "final_stage": final_state.get("current_stage", "") if final_state else "",
        "route_generated": route_generated,
        "schema_valid": route_generated,
        "failure_type": failure_type,
        "route_step_names": route_step_names,
        "step_count": len(route_step_names),
        "retrieval_count": obs["retrieval_count"],
        "retrieval_doc_count": obs["retrieval_doc_count"],
        "retrieved_sources": _retrieved_sources(route_context),
        "retrieved_snippet_preview": _retrieved_snippet_preview(route_context),
        "route_context_chars": len(route_context or ""),
        "route_context_preview": (route_context or "")[:500],
        "latency_ms": latency_ms,
        "model_call_count": obs["model_call_count"],
        "self_correction_count": obs["self_correction_count"],
        "retrieval_trace_available": obs["retrieval_trace_available"],
        "preliminary_quality_label": _preliminary_label(case, route_generated, failure_type),
        "focus_keywords": case.get("focus_keywords", []),
        "focus_keyword_hits": focus_hits,
        "suspected_knowledge_gap": "unknown_pending_review",
        "out_of_scope_findings": [],
        "notes": case.get("notes", ""),
        "workflow_run_id": workflow_run_id,
        "error_message": error or final_state.get("error_message", ""),
        "route_result": _model_dump(route_result),
    }


def _load_p1_results() -> dict[str, Any]:
    if not P1_RESULTS_PATH.exists():
        return {"available": False, "path": str(P1_RESULTS_PATH), "results": []}
    try:
        payload = json.loads(P1_RESULTS_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"available": False, "path": str(P1_RESULTS_PATH), "error": f"{type(exc).__name__}: {exc}", "results": []}
    return {
        "available": True,
        "path": str(P1_RESULTS_PATH),
        "total_cases": payload.get("total_cases", 0),
        "route_generated_count": payload.get("route_generated_count", 0),
        "failure_type_distribution": payload.get("failure_type_distribution", {}),
        "results": payload.get("results", []),
    }


def _read_knowledge() -> dict[str, str]:
    content: dict[str, str] = {}
    for path in KNOWLEDGE_FILES:
        if path.exists():
            content[path.name] = path.read_text(encoding="utf-8", errors="replace")
    return content


def _knowledge_keyword_hits(keywords: list[str], knowledge: dict[str, str]) -> dict[str, list[str]]:
    return {
        file_name: _keyword_hits(text, keywords)
        for file_name, text in knowledge.items()
    }


def _summarize_by_scenario(results: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        grouped[result["scenario"]].append(result)
    return {
        scenario: {
            "total": len(items),
            "route_generated": sum(1 for item in items if item["route_generated"]),
            "failure_types": dict(Counter(item["failure_type"] for item in items)),
            "avg_retrieval_doc_count": round(
                sum(int(item.get("retrieval_doc_count") or 0) for item in items) / len(items), 2
            ),
        }
        for scenario, items in grouped.items()
    }


def _build_review_items(p1_results: list[dict[str, Any]], audit_results: list[dict[str, Any]], knowledge: dict[str, str]) -> list[dict[str, Any]]:
    review_items: list[dict[str, Any]] = []

    for result in p1_results:
        case_id = result.get("case_id", "")
        if case_id not in P1_CASE_FOCUS:
            continue
        focus_keywords = P1_CASE_FOCUS[case_id]
        step_text = " / ".join(result.get("route_step_names") or [])
        context_preview = result.get("route_context_preview", "")
        focus_hits = _keyword_hits(step_text + "\n" + context_preview, focus_keywords)
        if case_id == "shortdrama_close_success_01" or len(focus_hits) < max(2, len(focus_keywords) // 3):
            review_items.append(
                {
                    "case_id": case_id,
                    "source": "P1",
                    "user_goal": result.get("user_goal", ""),
                    "route_step_names": result.get("route_step_names", []),
                    "retrieved_snippet_preview": result.get("retrieved_snippet_preview", []),
                    "route_context_preview": context_preview,
                    "knowledge_observation": _knowledge_keyword_hits(focus_keywords, knowledge),
                    "initial_attribution": "unknown_pending_review",
                    "reason": "Focus keyword evidence is weak or this was previously identified as usable-but-generic.",
                }
            )

    for result in audit_results:
        if result.get("is_boundary"):
            review_items.append(
                {
                    "case_id": result["case_id"],
                    "source": "P1.5a",
                    "user_goal": result["user_goal"],
                    "route_step_names": result.get("route_step_names", []),
                    "retrieved_snippet_preview": result.get("retrieved_snippet_preview", []),
                    "route_context_preview": result.get("route_context_preview", ""),
                    "knowledge_observation": _knowledge_keyword_hits(result.get("focus_keywords", []), knowledge),
                    "initial_attribution": "ambiguous_case",
                    "reason": "Boundary input should be reviewed separately from knowledge quality.",
                }
            )
            continue

        if not result.get("route_generated") or len(result.get("focus_keyword_hits", [])) < 2:
            keywords = result.get("focus_keywords", [])
            knowledge_hits = _knowledge_keyword_hits(keywords, knowledge)
            any_knowledge_hit = any(knowledge_hits.values())
            attribution = "retrieval_mismatch" if any_knowledge_hit and result.get("retrieval_doc_count", 0) == 0 else "unknown_pending_review"
            review_items.append(
                {
                    "case_id": result["case_id"],
                    "source": "P1.5a",
                    "user_goal": result["user_goal"],
                    "route_step_names": result.get("route_step_names", []),
                    "retrieved_snippet_preview": result.get("retrieved_snippet_preview", []),
                    "route_context_preview": result.get("route_context_preview", ""),
                    "knowledge_observation": knowledge_hits,
                    "initial_attribution": attribution,
                    "reason": "Route failed or output/context has limited focus-keyword evidence.",
                }
            )

    return review_items[:5]


def _build_payload(results: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    p1 = _load_p1_results()
    knowledge = _read_knowledge()
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "git_commit": _git_commit(),
        "mode": "P1.5a evidence-driven knowledge gap audit",
        "limit": args.limit,
        "case_id": args.case_id,
        "p1_results_reused": p1,
        "audit_case_count": len(results),
        "audit_route_generated_count": sum(1 for result in results if result["route_generated"]),
        "audit_failure_type_distribution": dict(Counter(result["failure_type"] for result in results)),
        "audit_scenario_summary": _summarize_by_scenario(results),
        "results": results,
        "review_items": _build_review_items(p1.get("results", []), results, knowledge),
        "knowledge_files_read": list(knowledge.keys()),
    }


def _md_table_row(values: list[Any]) -> str:
    return "| " + " | ".join(str(value).replace("\n", " ") for value in values) + " |"


def _format_preview(previews: list[dict[str, Any]]) -> str:
    if not previews:
        return "(none)"
    chunks = []
    for preview in previews[:3]:
        source = preview.get("source", "")
        file_name = preview.get("file_name", "")
        section = preview.get("section_index", "")
        excerpt = preview.get("excerpt", "")
        chunks.append(f"{source}/{file_name}#{section}: {excerpt}")
    return " || ".join(chunks)


def _build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = [
        "# P1.5a Evidence-driven Knowledge Gap Audit 报告",
        "",
        "## 1. 本轮目标与边界",
        "",
        "本轮只做知识库缺口审查：复用 P1 10 个 case 结果，并新增 10 个扩展 case 观察真实 with-RAG 输出。不修改 knowledge、prompt、workflow、retriever，也不进入 P2。",
        "",
        "## 2. 上一版局部 patch 方案的弊端",
        "",
        "- 只围绕 `shortdrama_close_success_01` 容易过拟合单个弱 case。",
        "- 直接预设修改 `workflows.md` 和 `reference_workflow_patterns.md` 会跳过证据采集。",
        "- P2 前需要先区分知识库缺口、检索错配、模型利用不足和灰区输入。",
        "",
        "## 3. 当前 P1 结果复用情况",
        "",
    ]

    p1 = payload["p1_results_reused"]
    if p1.get("available"):
        lines.extend(
            [
                f"- 已读取: `{p1.get('path')}`",
                f"- P1 case 总数: {p1.get('total_cases')}",
                f"- P1 route_generated: {p1.get('route_generated_count')}",
                f"- P1 failure_type 分布: {p1.get('failure_type_distribution')}",
            ]
        )
    else:
        lines.append(f"- 未成功读取 P1 结果: `{p1.get('path')}`")

    lines.extend(
        [
            "",
            "## 4. 新增 10 个扩展 case 运行结果",
            "",
            "| case_id | route_generated | final_stage | failure_type | retrieval_doc_count | route_context_chars | step_count | preliminary_quality_label | suspected_knowledge_gap |",
            "|---|---:|---|---|---:|---:|---:|---|---|",
        ]
    )
    for result in payload["results"]:
        lines.append(
            _md_table_row(
                [
                    result["case_id"],
                    result["route_generated"],
                    result["final_stage"],
                    result["failure_type"],
                    result["retrieval_doc_count"],
                    result["route_context_chars"],
                    result["step_count"],
                    result["preliminary_quality_label"],
                    result["suspected_knowledge_gap"],
                ]
            )
        )

    lines.extend(["", "## 5. 综合 20 个 case 的知识库支撑观察", ""])
    lines.append(f"- P1.5a 新增 case 总数: {payload['audit_case_count']}")
    lines.append(f"- P1.5a route_generated: {payload['audit_route_generated_count']}")
    lines.append(f"- P1.5a failure_type 分布: {payload['audit_failure_type_distribution']}")
    lines.append(f"- 读取 knowledge 文件: {', '.join(payload['knowledge_files_read'])}")
    lines.append("")
    for scenario, summary in payload["audit_scenario_summary"].items():
        lines.append(f"- {scenario}: {summary}")

    lines.extend(
        [
            "",
            "## 6. 弱 case 溯源",
            "",
            "以下为需要人工重点复核的初步证据链。`initial_attribution` 是保守初筛，不是最终结论。",
        ]
    )
    if not payload["review_items"]:
        lines.append("")
        lines.append("- 暂无自动筛出的重点弱 case；建议人工按 JSON 结果继续复核。")
    for item in payload["review_items"]:
        lines.extend(
            [
                "",
                f"### {item['case_id']}",
                "",
                f"- 来源: {item['source']}",
                f"- 用户目标: {item['user_goal']}",
                f"- route_step_names: {' / '.join(item.get('route_step_names') or []) or '(none)'}",
                f"- retrieved_snippet_preview: {_format_preview(item.get('retrieved_snippet_preview') or [])}",
                f"- route_context_preview: {(item.get('route_context_preview') or '')[:300]}",
                f"- 对应 knowledge 文件观察: {item.get('knowledge_observation')}",
                f"- 初步归因: {item.get('initial_attribution')}",
                f"- 说明: {item.get('reason')}",
            ]
        )

    lines.extend(
        [
            "",
            "## 7. 建议的知识库补强方向",
            "",
            "- `knowledge/tools.md`: 仅当扩展 case 显示工具角色不清时再补，不在本轮直接修改。",
            "- `knowledge/workflows.md`: 若漫剧首集、公众号、概率论复习等扩展 case 输出泛化，可在 P1.5b 补最小 workflow 片段。",
            "- `knowledge/blockages.md`: 若卡点类输入无法形成具体修正动作，可在 P1.5b 补对应卡点片段。",
            "- `knowledge/reference_workflow_patterns.md`: 若边界或模式归类反复偏移，可在 P1.5b 补模式边界说明。",
            "",
            "## 8. 范围外发现",
            "",
            "- prompt、model、retriever、top-k、chunking、metadata filter、workflow 状态传递问题只记录，不在 P1.5a 修复。",
            "",
            "## 9. 是否建议进入 P1.5b 知识库最小补强",
            "",
            "需要 GPT / 人工基于本报告复核后决定。若多个 case 的证据链指向同一知识缺口，再进入 P1.5b。",
            "",
            "## 10. 是否建议进入 P2 RAG Ablation",
            "",
            "如果知识库缺口明显，建议先做 P1.5b；如果缺口不明显且 RAG 信号稳定，再进入 P2。",
            "",
            "## 11. 是否建议 commit",
            "",
            "本轮不自动 commit，也不建议立即 commit；等待 GPT 和人工审查。",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run P1.5a evidence-driven knowledge gap audit.")
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

    RESULTS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(_build_markdown(payload), encoding="utf-8")

    print("P1.5a Evidence-driven Knowledge Gap Audit")
    print(f"audit_case_count: {payload['audit_case_count']}")
    print(f"audit_route_generated: {payload['audit_route_generated_count']}")
    print(f"audit_failure_type_distribution: {payload['audit_failure_type_distribution']}")
    print(f"results_json: {RESULTS_PATH}")
    print(f"report_md: {REPORT_PATH}")

    non_boundary_results = [result for result in results if not result.get("is_boundary")]
    blocking_failures = [
        result
        for result in non_boundary_results
        if result["failure_type"] in {"model_failure", "retrieval_failure", "unknown_failure"}
    ]
    all_non_boundary_failed = bool(non_boundary_results) and all(
        not result["route_generated"] for result in non_boundary_results
    )
    return 1 if all_non_boundary_failed or len(blocking_failures) >= 2 else 0


if __name__ == "__main__":
    raise SystemExit(main())
