from __future__ import annotations

from collections import Counter
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from retrieval_structure_cases import RETRIEVAL_STRUCTURE_CASES
from services.rag_service import RagService


BUCKET_KEYWORDS = {
    "learning": [
        "学习",
        "复习",
        "考试",
        "备考",
        "课程",
        "错题",
        "练习",
        "学习计划",
        "背单词",
        "单词",
        "阅读",
        "测验",
        "学习辅助",
    ],
    "content": [
        "内容",
        "文案",
        "小红书",
        "标题",
        "图文",
        "自媒体",
        "选题",
        "文章",
        "初稿",
        "发布",
        "内容创作",
        "封面",
    ],
    "shortdrama": [
        "动漫短剧",
        "短剧",
        "漫剧",
        "分镜",
        "成片",
        "视频",
        "配音",
        "字幕",
        "镜头",
        "角色图",
        "角色",
        "剪辑",
    ],
}

SOURCE_NAMES = ["tools", "workflows", "blockages"]
BUCKET_NAMES = ["learning", "content", "shortdrama", "unknown"]


def _classify_text(text: str) -> tuple[str, dict[str, int]]:
    normalized = text.lower()
    scores = {
        bucket: sum(1 for keyword in keywords if keyword.lower() in normalized)
        for bucket, keywords in BUCKET_KEYWORDS.items()
    }
    if not any(scores.values()):
        return "unknown", scores

    priority = ["shortdrama", "learning", "content"]
    bucket = max(scores, key=lambda item: (scores[item], -priority.index(item)))
    return bucket, scores


def _capture_retrieve_for_route(service: RagService, input_goal: str) -> tuple[str, dict[str, list[Any]]]:
    captured_queries: list[str] = []
    original_retrieve_by_source = service.retrieve_by_source

    def wrapped_retrieve_by_source(query: str, source: str):
        captured_queries.append(query)
        return original_retrieve_by_source(query, source)

    service.retrieve_by_source = wrapped_retrieve_by_source
    try:
        retrieved_docs = service.retrieve_for_route(input_goal)
    finally:
        service.retrieve_by_source = original_retrieve_by_source

    actual_query = captured_queries[0] if captured_queries else ""
    return actual_query, retrieved_docs


def _doc_record(doc: Any, source_name: str) -> dict[str, Any]:
    content = doc.page_content
    bucket, scores = _classify_text(content)
    metadata = doc.metadata or {}
    excerpt = " ".join(content.strip().split())[:160]
    section_index = metadata.get("section_index", "unknown")
    return {
        "file_name": metadata.get("file_name", "unknown"),
        "source": source_name,
        "metadata_source": metadata.get("source", "unknown"),
        "section_index": section_index,
        "chunk_index": metadata.get("chunk_index", "unknown"),
        "bucket_guess": bucket,
        "bucket_scores": scores,
        "suspected_type": _suspected_type(source_name, section_index, bucket, scores),
        "excerpt": excerpt,
    }


def _suspected_type(
    source_name: str,
    section_index: Any,
    bucket: str,
    scores: dict[str, int],
) -> str:
    if section_index == 0:
        return "overview_doc"
    active_scores = sum(1 for score in scores.values() if score > 0)
    if active_scores >= 2:
        return "coarse_or_cross_bucket_chunk"
    if source_name == "tools":
        return "source_tool_card"
    if source_name == "workflows":
        return "adjacent_workflow_template"
    if source_name == "blockages":
        return "adjacent_blockage_card"
    return "unknown"


def _source_bucket_breakdown(records_by_source: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, int]]:
    breakdown = {}
    for source_name in SOURCE_NAMES:
        counts = Counter(record["bucket_guess"] for record in records_by_source.get(source_name, []))
        breakdown[source_name] = {
            bucket: counts.get(bucket, 0)
            for bucket in BUCKET_NAMES
        }
    return breakdown


def _suspected_overview_docs(
    expected_bucket: str,
    records_by_source: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    suspects = []
    for source_name in SOURCE_NAMES:
        for record in records_by_source.get(source_name, []):
            if record["section_index"] == 0:
                reason = "section_index=0，属于文件总览/边界说明，可能覆盖多桶语义。"
            elif record["bucket_guess"] != expected_bucket:
                reason = f"召回片段归为 {record['bucket_guess']}，但当前 case 期望 {expected_bucket}。"
            else:
                continue

            suspects.append(
                {
                    "file_name": record["file_name"],
                    "source": record["source"],
                    "section_index": record["section_index"],
                    "bucket_guess": record["bucket_guess"],
                    "suspected_type": record["suspected_type"],
                    "reason": reason,
                    "excerpt": record["excerpt"],
                }
            )
    return suspects[:6]


def _dominant_noise_source(
    expected_bucket: str,
    records_by_source: dict[str, list[dict[str, Any]]],
) -> str:
    off_bucket_counts = {
        source_name: sum(
            1
            for record in records_by_source.get(source_name, [])
            if record["bucket_guess"] not in {expected_bucket, "unknown"}
        )
        for source_name in SOURCE_NAMES
    }
    max_count = max(off_bucket_counts.values())
    if max_count == 0:
        return "mixed"

    dominant_sources = [
        source_name
        for source_name, count in off_bucket_counts.items()
        if count == max_count
    ]
    return dominant_sources[0] if len(dominant_sources) == 1 else "mixed"


def _structure_noise_reason(
    expected_bucket: str,
    records_by_source: dict[str, list[dict[str, Any]]],
    dominant_source: str,
) -> str:
    source_reasons = []
    for source_name in SOURCE_NAMES:
        records = records_by_source.get(source_name, [])
        off_bucket = [
            record
            for record in records
            if record["bucket_guess"] not in {expected_bucket, "unknown"}
        ]
        overview = [record for record in records if record["section_index"] == 0]
        cross_bucket = [
            record
            for record in records
            if sum(1 for score in record["bucket_scores"].values() if score > 0) >= 2
        ]

        if off_bucket:
            source_reasons.append(f"{source_name} 有 {len(off_bucket)} 个相邻桶片段混入")
        if overview:
            source_reasons.append(f"{source_name} 命中 {len(overview)} 个总览片段")
        if cross_bucket:
            source_reasons.append(f"{source_name} 有 {len(cross_bucket)} 个多桶关键词片段")

    if not source_reasons:
        return "未见明显结构性噪声。"

    prefix = (
        f"主噪声来源判断为 {dominant_source}；"
        if dominant_source != "mixed"
        else "噪声来源呈 mixed；"
    )
    return prefix + "；".join(source_reasons)


def _run_case(service: RagService, case: dict[str, str]) -> dict[str, Any]:
    actual_query, retrieved_docs = _capture_retrieve_for_route(service, case["input_goal"])
    records_by_source = {
        source_name: [
            _doc_record(doc, source_name)
            for doc in retrieved_docs.get(source_name, [])
        ]
        for source_name in SOURCE_NAMES
    }
    source_breakdown = _source_bucket_breakdown(records_by_source)
    dominant_source = _dominant_noise_source(case["bucket"], records_by_source)
    suspects = _suspected_overview_docs(case["bucket"], records_by_source)
    reason = _structure_noise_reason(case["bucket"], records_by_source, dominant_source)

    return {
        "case_id": case["case_id"],
        "bucket": case["bucket"],
        "case_type": case["case_type"],
        "input_goal": case["input_goal"],
        "actual_query": actual_query,
        "source_bucket_breakdown": source_breakdown,
        "dominant_noise_source": dominant_source,
        "structure_noise_reason": reason,
        "suspected_overview_docs": suspects,
        "notes": case["notes"],
    }


def _aggregate_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    direct_or_fallback = {
        result["case_id"]: result
        for result in results
    }
    return {
        "learning_main_sources": [
            direct_or_fallback["direct_learning_plan_01"]["dominant_noise_source"],
            direct_or_fallback["fallback_learning_01"]["dominant_noise_source"],
        ],
        "content_main_sources": [
            direct_or_fallback["direct_content_xiaohongshu_01"]["dominant_noise_source"],
            direct_or_fallback["fallback_content_01"]["dominant_noise_source"],
        ],
        "shortdrama_main_sources": [
            direct_or_fallback["direct_shortdrama_60s_01"]["dominant_noise_source"],
            direct_or_fallback["fallback_shortdrama_01"]["dominant_noise_source"],
        ],
    }


def main() -> int:
    service = RagService()
    results = [_run_case(service, case) for case in RETRIEVAL_STRUCTURE_CASES]
    aggregate = _aggregate_results(results)

    print("# 检索结构噪声专项诊断")
    print()
    print(f"- total_cases: {len(results)}")
    print("- mode: real_retrieval")
    print("- target: retrieve_for_route structure")
    print()

    for result in results:
        print(f"## {result['case_id']}")
        print(f"- bucket: {result['bucket']}")
        print(f"- case_type: {result['case_type']}")
        print(f"- input_goal: {result['input_goal']}")
        print(f"- actual_query: {result['actual_query']}")
        print(f"- source_bucket_breakdown: {result['source_bucket_breakdown']}")
        print(f"- dominant_noise_source: {result['dominant_noise_source']}")
        print(f"- structure_noise_reason: {result['structure_noise_reason']}")
        print("- suspected_overview_docs:")
        for index, doc in enumerate(result["suspected_overview_docs"], start=1):
            print(
                f"  {index}. file={doc['file_name']} source={doc['source']} "
                f"section={doc['section_index']} bucket_guess={doc['bucket_guess']} "
                f"type={doc['suspected_type']}"
            )
            print(f"     reason: {doc['reason']}")
            print(f"     excerpt: {doc['excerpt']}")
        print(f"- notes: {result['notes']}")
        print()

    print("# aggregate")
    print(f"- learning_main_sources: {aggregate['learning_main_sources']}")
    print(f"- content_main_sources: {aggregate['content_main_sources']}")
    print(f"- shortdrama_main_sources: {aggregate['shortdrama_main_sources']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
