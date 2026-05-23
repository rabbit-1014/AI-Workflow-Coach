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

import graph.nodes as workflow_nodes
from graph.workflow import build_route_workflow
from rag_ablation_cases import RAG_ABLATION_CASES
from utils.observability import read_observability_records


REPORTS_DIR = Path(__file__).resolve().parent / "reports"
RESULTS_PATH = REPORTS_DIR / "latest_rag_ablation_results.json"
REPORT_PATH = REPORTS_DIR / "latest_rag_ablation_report.md"

GENERIC_PHRASES = [
    "明确目标",
    "制定计划",
    "优化调整",
    "持续优化",
    "复盘迭代",
    "根据反馈",
    "逐步完善",
    "提升效率",
    "收集反馈",
    "数据复盘",
    "内容定位",
]

TOOL_VOCAB = [
    "ChatGPT",
    "通义千问",
    "Kimi",
    "豆包",
    "即梦",
    "Midjourney",
    "可灵",
    "Runway",
    "Pika",
    "剪映",
    "CapCut",
    "ElevenLabs",
    "Canva",
    "稿定设计",
    "Notion",
    "飞书",
    "Excel",
    "小红书",
    "公众号",
]

NO_RAG_FORBIDDEN_MARKERS = [
    "source:",
    "file_name:",
    "chunk_index:",
    "section_index:",
    "tools.md",
    "workflows.md",
    "blockages.md",
    "## 常用工具组合",
    "## 路径模式",
    "## 卡点",
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
    cases = list(RAG_ABLATION_CASES)
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
        previews.append(
            {
                "source": _match_line(block, "source"),
                "file_name": _match_line(block, "file_name"),
                "section_index": _match_line(block, "section_index"),
                "chunk_index": _match_line(block, "chunk_index"),
                "excerpt": " ".join(content.split())[:max_chars],
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


def _failure_type(final_state: dict[str, Any], error: str, route_generated: bool) -> str:
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
    if not route_generated:
        return "route_not_generated"
    return "none"


def _empty_retrieve_for_route(_user_goal: str) -> dict[str, list[Any]]:
    return {"tools": [], "workflows": [], "blockages": []}


def _run_case(case: dict[str, Any], ablation_mode: str) -> dict[str, Any]:
    original_retrieve_for_route = workflow_nodes.rag_service.retrieve_for_route
    patched = ablation_mode == "without_rag"
    if patched:
        workflow_nodes.rag_service.retrieve_for_route = _empty_retrieve_for_route

    started = time.perf_counter()
    final_state: dict[str, Any] = {}
    error = ""
    try:
        app = build_route_workflow()
        final_state = _invoke_route_case(app, case)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        if patched:
            workflow_nodes.rag_service.retrieve_for_route = original_retrieve_for_route

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
    return {
        "ablation_mode": ablation_mode,
        "workflow_run_id": workflow_run_id,
        "final_stage": final_state.get("current_stage", "") if final_state else "",
        "route_generated": route_generated,
        "schema_valid": route_generated,
        "failure_type": _failure_type(final_state, error, route_generated),
        "route_step_names": _route_step_names(route_result),
        "step_count": len(_route_step_names(route_result)),
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
        "route_result": _model_dump(route_result),
        "error_message": error or final_state.get("error_message", ""),
    }


def _route_text(result: dict[str, Any]) -> str:
    return json.dumps(result.get("route_result"), ensure_ascii=False) if result.get("route_result") else ""


def _count_unique_terms(text: str, terms: list[str]) -> int:
    return sum(1 for term in terms if term and term in text)


def _generic_phrase_count(text: str) -> int:
    return _count_unique_terms(text, GENERIC_PHRASES)


def _step_focus_hits(result: dict[str, Any], focus_keywords: list[str]) -> int:
    return _count_unique_terms(" / ".join(result.get("route_step_names") or []), focus_keywords)


def _validate_pair(with_result: dict[str, Any], without_result: dict[str, Any]) -> tuple[bool, str]:
    if with_result.get("retrieval_doc_count", 0) == 0:
        return False, "with_rag_retrieval_doc_count_is_0"

    if without_result.get("retrieval_doc_count") != 0:
        return False, "without_rag_retrieval_doc_count_not_0"
    if without_result.get("retrieved_sources"):
        return False, "without_rag_retrieved_sources_not_empty"
    if without_result.get("retrieved_snippet_preview"):
        return False, "without_rag_retrieved_snippet_preview_not_empty"

    route_context_preview = without_result.get("route_context_preview", "")
    if any(marker in route_context_preview for marker in NO_RAG_FORBIDDEN_MARKERS):
        return False, "without_rag_route_context_contains_knowledge_marker"

    return True, ""


def _compare_pair(case: dict[str, Any], with_result: dict[str, Any], without_result: dict[str, Any], pair_valid: bool) -> dict[str, Any]:
    with_text = _route_text(with_result)
    without_text = _route_text(without_result)
    focus_keywords = case.get("focus_keywords", [])
    expected_tool_terms = case.get("expected_tool_terms", [])

    with_named_tool_count = _count_unique_terms(with_text, TOOL_VOCAB)
    without_named_tool_count = _count_unique_terms(without_text, TOOL_VOCAB)
    with_expected_tool_hits = _count_unique_terms(with_text, expected_tool_terms)
    without_expected_tool_hits = _count_unique_terms(without_text, expected_tool_terms)
    with_focus_hits = _count_unique_terms(with_text, focus_keywords)
    without_focus_hits = _count_unique_terms(without_text, focus_keywords)
    with_step_focus_hits = _step_focus_hits(with_result, focus_keywords)
    without_step_focus_hits = _step_focus_hits(without_result, focus_keywords)
    with_generic_count = _generic_phrase_count(with_text)
    without_generic_count = _generic_phrase_count(without_text)

    named_tool_count_delta = with_named_tool_count - without_named_tool_count
    expected_tool_hit_delta = with_expected_tool_hits - without_expected_tool_hits
    focus_keyword_hit_delta = with_focus_hits - without_focus_hits
    step_focus_delta = with_step_focus_hits - without_step_focus_hits
    generic_phrase_delta = without_generic_count - with_generic_count

    if not pair_valid:
        preliminary_winner = "inconclusive"
    else:
        with_score = (
            with_expected_tool_hits
            + with_focus_hits
            + with_step_focus_hits
            - with_generic_count
            + (1 if with_result.get("route_generated") else -3)
        )
        without_score = (
            without_expected_tool_hits
            + without_focus_hits
            + without_step_focus_hits
            - without_generic_count
            + (1 if without_result.get("route_generated") else -3)
        )
        if with_score - without_score >= 2:
            preliminary_winner = "with_rag"
        elif without_score - with_score >= 2:
            preliminary_winner = "without_rag"
        else:
            preliminary_winner = "tie"

    return {
        "named_tool_count_delta": named_tool_count_delta,
        "expected_tool_hit_delta": expected_tool_hit_delta,
        "focus_keyword_hit_delta": focus_keyword_hit_delta,
        "generic_phrase_delta": generic_phrase_delta,
        "step_focus_delta": step_focus_delta,
        "with_rag_metrics": {
            "named_tool_count": with_named_tool_count,
            "expected_tool_hits": with_expected_tool_hits,
            "focus_keyword_hits": with_focus_hits,
            "step_focus_hits": with_step_focus_hits,
            "generic_phrase_count": with_generic_count,
        },
        "without_rag_metrics": {
            "named_tool_count": without_named_tool_count,
            "expected_tool_hits": without_expected_tool_hits,
            "focus_keyword_hits": without_focus_hits,
            "step_focus_hits": without_step_focus_hits,
            "generic_phrase_count": without_generic_count,
        },
        "preliminary_winner": preliminary_winner,
    }


def _run_pair(case: dict[str, Any]) -> dict[str, Any]:
    with_result = _run_case(case, "with_rag")
    without_result = _run_case(case, "without_rag")
    pair_valid, invalid_reason = _validate_pair(with_result, without_result)
    return {
        "case_id": case["case_id"],
        "case_group": case["case_group"],
        "scenario": case["scenario"],
        "user_goal": case["user_goal"],
        "followup_answer": case.get("followup_answer", ""),
        "notes": case.get("notes", ""),
        "with_rag_result": with_result,
        "without_rag_result": without_result,
        "pair_valid": pair_valid,
        "invalid_reason": invalid_reason,
        "pair_diff": _compare_pair(case, with_result, without_result, pair_valid),
    }


def _aggregate_core_results(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    core_pairs = [
        pair for pair in pairs
        if pair["case_group"] == "core_ablation_cases" and pair["pair_valid"]
    ]
    winner_counts = Counter(pair["pair_diff"]["preliminary_winner"] for pair in core_pairs)
    avg = lambda key: round(sum(pair["pair_diff"][key] for pair in core_pairs) / len(core_pairs), 2) if core_pairs else 0.0
    return {
        "valid_core_case_count": len(core_pairs),
        "preliminary_winner_distribution": dict(winner_counts),
        "avg_named_tool_count_delta": avg("named_tool_count_delta"),
        "avg_expected_tool_hit_delta": avg("expected_tool_hit_delta"),
        "avg_focus_keyword_hit_delta": avg("focus_keyword_hit_delta"),
        "avg_step_focus_delta": avg("step_focus_delta"),
        "avg_generic_phrase_delta": avg("generic_phrase_delta"),
    }


def _build_payload(pairs: list[dict[str, Any]], args: argparse.Namespace, stopped_early: bool, stop_reason: str) -> dict[str, Any]:
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "git_commit": _git_commit(),
        "mode": "P2 RAG ablation v1 paired real eval",
        "disclaimer": "P2 v1 is a single-run paired baseline and does not claim statistical significance.",
        "limit": args.limit,
        "case_id": args.case_id,
        "total_pairs": len(pairs),
        "stopped_early": stopped_early,
        "stop_reason": stop_reason,
        "core_summary": _aggregate_core_results(pairs),
        "pair_valid_count": sum(1 for pair in pairs if pair["pair_valid"]),
        "pair_invalid_count": sum(1 for pair in pairs if not pair["pair_valid"]),
        "pairs": pairs,
    }


def _md_row(values: list[Any]) -> str:
    return "| " + " | ".join(str(value).replace("\n", " ") for value in values) + " |"


def _step_summary(result: dict[str, Any]) -> str:
    return " / ".join(result.get("route_step_names") or []) or "(none)"


def _build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = [
        "# P2 RAG Ablation Report",
        "",
        "P2 v1 是一轮真实成对对比基线，只提供规则初筛和证据，不声明统计显著，不作为最终质量结论。",
        "",
        f"- 运行时间: {payload['generated_at']}",
        f"- Git commit: {payload['git_commit']}",
        f"- total_pairs: {payload['total_pairs']}",
        f"- pair_valid_count: {payload['pair_valid_count']}",
        f"- pair_invalid_count: {payload['pair_invalid_count']}",
        f"- stopped_early: {payload['stopped_early']}",
        f"- stop_reason: {payload['stop_reason']}",
        "",
        "## Core Summary",
        "",
        f"- core_ablation_cases 主结论摘要: {payload['core_summary']}",
        "",
        "## Case Pair Table",
        "",
        "| case_id | group | pair_valid | invalid_reason | with_docs | without_docs | preliminary_winner | tool_delta | focus_delta | step_delta | generic_reduction |",
        "|---|---|---:|---|---:|---:|---|---:|---:|---:|---:|",
    ]

    for pair in payload["pairs"]:
        diff = pair["pair_diff"]
        lines.append(
            _md_row(
                [
                    pair["case_id"],
                    pair["case_group"],
                    pair["pair_valid"],
                    pair["invalid_reason"],
                    pair["with_rag_result"]["retrieval_doc_count"],
                    pair["without_rag_result"]["retrieval_doc_count"],
                    diff["preliminary_winner"],
                    diff["named_tool_count_delta"],
                    diff["focus_keyword_hit_delta"],
                    diff["step_focus_delta"],
                    diff["generic_phrase_delta"],
                ]
            )
        )

    lines.extend(
        [
            "",
            "## 关键问题回答",
            "",
            "### 同一批 case，with-RAG 和 without-RAG 的输出差异在哪里？",
            "",
            "- 以有效 pair 的步骤名、工具命中、场景关键词命中和泛化短语数量做规则初筛；具体差异见下方逐 case 对照。",
            "- `diagnostic_cases` 只用于观察已知弱点，不参与 RAG 整体有效性主结论。",
            "",
            "### RAG 是否让工具推荐更具体？",
            "",
            f"- core 平均具名工具数量差: {payload['core_summary']['avg_named_tool_count_delta']}",
            f"- core 平均期望工具命中差: {payload['core_summary']['avg_expected_tool_hit_delta']}",
            "",
            "### RAG 是否让步骤更贴近场景？",
            "",
            f"- core 平均场景关键词命中差: {payload['core_summary']['avg_focus_keyword_hit_delta']}",
            f"- core 平均步骤名场景命中差: {payload['core_summary']['avg_step_focus_delta']}",
            "",
            "### RAG 是否减少泛化废话？",
            "",
            f"- core 平均泛化短语减少量: {payload['core_summary']['avg_generic_phrase_delta']}",
            "- 正数表示 with-RAG 比 without-RAG 更少出现泛化短语；负数表示更多。",
            "",
            "## 逐 case 对照",
            "",
        ]
    )

    for pair in payload["pairs"]:
        diff = pair["pair_diff"]
        lines.extend(
            [
                f"### {pair['case_id']} ({pair['case_group']})",
                "",
                f"- pair_valid: {pair['pair_valid']}",
                f"- invalid_reason: {pair['invalid_reason']}",
                f"- preliminary_winner: {diff['preliminary_winner']}（规则初筛，不是最终质量结论）",
                f"- with-RAG steps: {_step_summary(pair['with_rag_result'])}",
                f"- without-RAG steps: {_step_summary(pair['without_rag_result'])}",
                f"- pair_diff: {diff}",
                "",
            ]
        )

    lines.extend(
        [
            "## 结论边界",
            "",
            "- 本报告只记录 P2 v1 单轮真实成对对比，不声明统计显著。",
            "- 如果 without-RAG 在个别 case 表现更好，只记录发现，不修改代码。",
            "- 如果后续要做最终结论，需要人工复核核心 case 输出全文。",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run P2 RAG ablation paired eval.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--case-id", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cases = _select_cases(args.limit, args.case_id or None)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    pairs: list[dict[str, Any]] = []
    stopped_early = False
    stop_reason = ""
    for case in cases:
        pair = _run_pair(case)
        pairs.append(pair)
        if pair["invalid_reason"].startswith("without_rag_"):
            stopped_early = True
            stop_reason = pair["invalid_reason"]
            break

    payload = _build_payload(pairs, args, stopped_early, stop_reason)
    RESULTS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(_build_markdown(payload), encoding="utf-8")

    print("P2 RAG Ablation")
    print(f"total_pairs: {payload['total_pairs']}")
    print(f"pair_valid_count: {payload['pair_valid_count']}")
    print(f"pair_invalid_count: {payload['pair_invalid_count']}")
    print(f"stopped_early: {payload['stopped_early']}")
    print(f"stop_reason: {payload['stop_reason']}")
    print(f"core_summary: {payload['core_summary']}")
    print(f"results_json: {RESULTS_PATH}")
    print(f"report_md: {REPORT_PATH}")

    return 1 if stopped_early else 0


if __name__ == "__main__":
    raise SystemExit(main())
