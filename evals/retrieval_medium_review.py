from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.rag_service import RagService


OUTPUT_PATH = Path(__file__).with_name("retrieval_medium_review.md")

REVIEW_CASES = [
    {
        "case_id": "direct_learning_plan_01",
        "bucket": "learning",
        "input_goal": "用 AI 做一个 14 天英语学习计划，重点提升阅读和单词复习",
    },
    {
        "case_id": "fallback_learning_01",
        "bucket": "learning",
        "input_goal": "AI 学习辅助",
    },
    {
        "case_id": "direct_content_xiaohongshu_01",
        "bucket": "content",
        "input_goal": "用 AI 做小红书图文内容创作，主题是新手如何开始用 AI 提高学习效率",
    },
    {
        "case_id": "fallback_content_01",
        "bucket": "content",
        "input_goal": "AI 内容创作",
    },
]

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


def _classify_text(text: str) -> tuple[str, dict[str, int], dict[str, list[str]]]:
    normalized = text.lower()
    hits = {
        bucket: [
            keyword
            for keyword in keywords
            if keyword.lower() in normalized
        ]
        for bucket, keywords in BUCKET_KEYWORDS.items()
    }
    scores = {bucket: len(bucket_hits) for bucket, bucket_hits in hits.items()}

    if not any(scores.values()):
        return "unknown", scores, hits

    priority = ["shortdrama", "learning", "content"]
    bucket = max(scores, key=lambda item: (scores[item], -priority.index(item)))
    return bucket, scores, hits


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


def _flagged_docs(expected_bucket: str, retrieved_docs: dict[str, list[Any]]) -> list[dict[str, Any]]:
    flagged = []

    for source_name in ["tools", "workflows", "blockages"]:
        for doc in retrieved_docs.get(source_name, []):
            bucket_guess, scores, hits = _classify_text(doc.page_content)
            if bucket_guess == expected_bucket:
                continue

            metadata = doc.metadata or {}
            excerpt = " ".join(doc.page_content.strip().split())[:220]
            matched_keywords = {
                bucket: bucket_hits
                for bucket, bucket_hits in hits.items()
                if bucket_hits
            }
            flagged.append(
                {
                    "source": source_name,
                    "file_name": metadata.get("file_name", "unknown"),
                    "section_index": metadata.get("section_index", "unknown"),
                    "chunk_index": metadata.get("chunk_index", "unknown"),
                    "current_bucket_guess": bucket_guess,
                    "why_flagged": (
                        f"current_bucket_guess={bucket_guess}，expected_bucket={expected_bucket}；"
                        f"matched_keywords={matched_keywords}；bucket_scores={scores}"
                    ),
                    "excerpt": excerpt,
                }
            )

    return flagged


def _render_case(result: dict[str, Any]) -> list[str]:
    lines = [
        f"## {result['case_id']}",
        f"- bucket: {result['bucket']}",
        f"- input_goal: {result['input_goal']}",
        f"- actual_query: {result['actual_query']}",
        "",
    ]

    if not result["flagged_docs"]:
        lines.extend(["无可疑片段。", ""])
        return lines

    for index, doc in enumerate(result["flagged_docs"], start=1):
        lines.extend(
            [
                f"### 可疑片段 {index}",
                f"- source: {doc['source']}",
                f"- file_name: {doc['file_name']}",
                f"- section_index: {doc['section_index']}",
                f"- chunk_index: {doc['chunk_index']}",
                f"- current_bucket_guess: {doc['current_bucket_guess']}",
                f"- why_flagged: {doc['why_flagged']}",
                f"- excerpt: {doc['excerpt']}",
                "",
                "人工判断：  ",
                "是否真是别桶片段：  ",
                "是否应视为当前桶的边界片段：  ",
                "是否需要后续系统修复：  ",
                "备注：",
                "",
            ]
        )

    return lines


def main() -> int:
    service = RagService()
    results = []

    for case in REVIEW_CASES:
        actual_query, retrieved_docs = _capture_retrieve_for_route(service, case["input_goal"])
        results.append(
            {
                **case,
                "actual_query": actual_query,
                "flagged_docs": _flagged_docs(case["bucket"], retrieved_docs),
            }
        )

    lines = [
        "# 剩余 medium 噪声人工核验清单",
        "",
        "> 本文件只整理当前评估脚本判为可疑的片段，供人工核验；不自动判定真噪声或误判。",
        "",
    ]

    for result in results:
        lines.extend(_render_case(result))

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"generated: {OUTPUT_PATH}")
    print(f"total_cases: {len(results)}")
    print(
        "flagged_docs: "
        + ", ".join(
            f"{result['case_id']}={len(result['flagged_docs'])}"
            for result in results
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
