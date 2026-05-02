from __future__ import annotations

from collections import Counter
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from retrieval_noise_cases import RETRIEVAL_NOISE_CASES
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

BUCKET_NAMES = {
    "learning": "AI 学习辅助",
    "content": "AI 内容创作",
    "shortdrama": "AI 动漫短剧/短视频",
}


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


def _query_cross_bucket_terms(query: str, expected_bucket: str) -> dict[str, list[str]]:
    normalized = query.lower()
    result: dict[str, list[str]] = {}
    for bucket, keywords in BUCKET_KEYWORDS.items():
        if bucket == expected_bucket:
            continue
        hits = [keyword for keyword in keywords if keyword.lower() in normalized]
        if hits:
            result[bucket] = hits
    return result


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


def _summarize_doc(doc: Any) -> dict[str, Any]:
    content = doc.page_content
    bucket, scores = _classify_text(content)
    metadata = doc.metadata or {}
    excerpt = " ".join(content.strip().split())[:140]
    return {
        "file_name": metadata.get("file_name", "unknown"),
        "source": metadata.get("source", "unknown"),
        "section_index": metadata.get("section_index", "unknown"),
        "bucket_guess": bucket,
        "bucket_scores": scores,
        "why": _bucket_reason(bucket, scores),
        "excerpt": excerpt,
    }


def _bucket_reason(bucket: str, scores: dict[str, int]) -> str:
    if bucket == "unknown":
        return "未命中三类关键词，无法稳定归桶。"
    return f"{BUCKET_NAMES[bucket]}关键词得分最高：{scores[bucket]}。"


def _noise_level(
    expected_bucket: str,
    doc_summaries: list[dict[str, Any]],
    query_cross_terms: dict[str, list[str]],
) -> tuple[str, str]:
    known_docs = [doc for doc in doc_summaries if doc["bucket_guess"] != "unknown"]
    off_bucket_docs = [
        doc
        for doc in known_docs
        if doc["bucket_guess"] != expected_bucket
    ]
    off_bucket_count = len(off_bucket_docs)
    known_count = len(known_docs)

    has_shortdrama_query_noise = (
        expected_bucket != "shortdrama" and "shortdrama" in query_cross_terms
    )
    has_off_bucket_docs = off_bucket_count > 0
    off_bucket_ratio = off_bucket_count / known_count if known_count else 0

    reasons = []
    if has_shortdrama_query_noise:
        reasons.append("actual_query 含短剧方向固定词")
    if has_off_bucket_docs:
        reasons.append(f"{off_bucket_count}/{known_count} 个可归类片段来自别桶")
    if not reasons:
        reasons.append("query 和召回片段未见明显跨桶污染")

    if has_shortdrama_query_noise and off_bucket_ratio >= 0.4:
        return "high", "；".join(reasons)
    if has_shortdrama_query_noise or off_bucket_ratio > 0:
        return "medium", "；".join(reasons)
    return "low", "；".join(reasons)


def _run_case(service: RagService, case: dict[str, str]) -> dict[str, Any]:
    actual_query, retrieved_docs = _capture_retrieve_for_route(service, case["input_goal"])
    flattened_docs = [
        doc
        for source_name in ["tools", "workflows", "blockages"]
        for doc in retrieved_docs.get(source_name, [])
    ]
    doc_summaries = [_summarize_doc(doc) for doc in flattened_docs]
    bucket_counts = Counter(doc["bucket_guess"] for doc in doc_summaries)
    query_cross_terms = _query_cross_bucket_terms(actual_query, case["bucket"])
    noise_level, noise_reason = _noise_level(
        case["bucket"],
        doc_summaries,
        query_cross_terms,
    )

    return {
        "case_id": case["case_id"],
        "bucket": case["bucket"],
        "case_type": case["case_type"],
        "input_goal": case["input_goal"],
        "actual_query": actual_query,
        "retrieved_doc_count": len(flattened_docs),
        "bucket_counts": dict(bucket_counts),
        "query_cross_bucket_terms": query_cross_terms,
        "top_docs_summary": doc_summaries[:5],
        "noise_level": noise_level,
        "noise_reason": noise_reason,
        "notes": case["notes"],
    }


def main() -> int:
    service = RagService()
    results = [_run_case(service, case) for case in RETRIEVAL_NOISE_CASES]

    print("# 检索噪声专项检查")
    print()
    print(f"- total_cases: {len(results)}")
    print("- mode: real_retrieval")
    print("- target: retrieve_for_route")
    print()

    for result in results:
        print(f"## {result['case_id']}")
        print(f"- bucket: {result['bucket']}")
        print(f"- case_type: {result['case_type']}")
        print(f"- input_goal: {result['input_goal']}")
        print(f"- actual_query: {result['actual_query']}")
        print(f"- retrieved_doc_count: {result['retrieved_doc_count']}")
        print(f"- bucket_counts: {result['bucket_counts']}")
        print(f"- query_cross_bucket_terms: {result['query_cross_bucket_terms']}")
        print(f"- noise_level: {result['noise_level']}")
        print(f"- noise_reason: {result['noise_reason']}")
        print(f"- notes: {result['notes']}")
        print("- top_docs_summary:")
        for index, doc in enumerate(result["top_docs_summary"], start=1):
            print(
                f"  {index}. file={doc['file_name']} source={doc['source']} "
                f"section={doc['section_index']} bucket_guess={doc['bucket_guess']}"
            )
            print(f"     why: {doc['why']}")
            print(f"     excerpt: {doc['excerpt']}")
        print()

    high_or_medium = [
        result["case_id"]
        for result in results
        if result["noise_level"] in {"medium", "high"}
    ]
    print("NOISE_CASES=" + ",".join(high_or_medium))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
