import time
from typing import Dict, List

from langchain_core.documents import Document

from vector_store.retriever import VectorRetriever
from utils.error_utils import classify_error
from utils.logger import setup_logger
from utils.observability import (
    elapsed_ms,
    get_current_workflow_run_id,
    record_retrieval_trace,
)


logger = setup_logger(__name__)


ROUTE_QUERY_KEYWORDS = {
    "learning": [
        "学习",
        "复习",
        "考试",
        "备考",
        "课程",
        "错题",
        "练习",
        "计划",
        "背单词",
        "单词",
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
        "动漫",
    ],
}

ROUTE_QUERY_EXPANSIONS = {
    "learning": "工具 workflow 步骤 学习 计划 复习 练习 反馈",
    "content": "工具 workflow 步骤 内容 文案 图文 标题 发布",
    "shortdrama": "工具 workflow 步骤 分镜 角色 配音 剪辑",
    "default": "工具 workflow 步骤",
}

ROUTE_BUCKET_SECTION_INDEXES = {
    "tools": {
        "learning": [1],
        "content": [2],
        "shortdrama": [3],
    },
    "workflows": {
        "learning": [1, 2, 3, 4],
        "content": [5, 6, 7, 8],
        "shortdrama": [9, 10, 11, 12],
    },
    "blockages": {
        "learning": [1, 2, 3, 4],
        "content": [5, 6, 7, 8],
        "shortdrama": [9, 10, 11, 12],
    },
}


def _normalize_query_text(text: str) -> str:
    return "".join(text.lower().split())


def _infer_route_bucket(user_goal: str) -> str:
    normalized_goal = _normalize_query_text(user_goal)
    scores = {}

    for bucket, keywords in ROUTE_QUERY_KEYWORDS.items():
        score = sum(
            1
            for keyword in keywords
            if _normalize_query_text(keyword) in normalized_goal
        )
        if score:
            scores[bucket] = score

    if not scores:
        return "default"

    priority = ["shortdrama", "learning", "content"]
    return max(scores, key=lambda bucket: (scores[bucket], -priority.index(bucket)))


def _build_route_query(user_goal: str) -> str:
    bucket = _infer_route_bucket(user_goal)
    expansion = ROUTE_QUERY_EXPANSIONS[bucket]
    return f"{user_goal} {expansion}"


def _build_route_metadata_filter(source: str, bucket: str) -> dict:
    section_indexes = ROUTE_BUCKET_SECTION_INDEXES.get(source, {}).get(bucket)
    if not section_indexes:
        return {"source": source}

    return {
        "$and": [
            {"source": source},
            {"section_index": {"$in": section_indexes}},
        ]
    }


class RagService:
    """RAG 检索服务层。

    当前阶段只负责：
    1. 调用向量检索器
    2. 按 source 检索 tools / workflows / blockages
    3. 整理检索结果
    4. 返回给后续路线生成或卡点细化模块

    当前阶段不负责调用 LLM。
    """

    def __init__(self):
        self.retriever = VectorRetriever()
        logger.info("RagService 初始化完成")

    def retrieve_general(self, query: str) -> List[Document]:
        """通用检索，不限制 source。"""
        logger.info(f"执行通用检索: {query}")
        return self.retriever.search(query)

    def retrieve_by_source(
        self,
        query: str,
        source: str,
        metadata_filter: dict | None = None,
    ) -> List[Document]:
        """按知识来源检索。

        source 可选：
        - tools
        - workflows
        - blockages
        """
        route_metadata_filters = getattr(self, "_route_metadata_filters", {})
        filter_condition = metadata_filter or route_metadata_filters.get(source) or {"source": source}
        logger.info(
            f"按 source 检索: query={query}, source={source}, metadata_filter={filter_condition}"
        )
        return self.retriever.search(
            query=query,
            metadata_filter=filter_condition,
        )

    def retrieve_for_route(self, user_goal: str) -> Dict[str, List[Document]]:
        """路线生成前的检索。

        路线生成需要重点参考：
        1. tools：可用工具
        2. workflows：任务流程模板
        3. blockages：常见卡点，作为路线提醒
        """
        logger.info(f"开始路线生成前检索: {user_goal}")
        start = time.perf_counter()

        route_bucket = _infer_route_bucket(user_goal)
        route_query = _build_route_query(user_goal)
        self._route_metadata_filters = {
            source: _build_route_metadata_filter(source, route_bucket)
            for source in ["tools", "workflows", "blockages"]
        }

        try:
            result = {
                "tools": self.retrieve_by_source(route_query, "tools"),
                "workflows": self.retrieve_by_source(route_query, "workflows"),
                "blockages": self.retrieve_by_source(route_query, "blockages"),
            }
        except Exception as e:
            error_type = classify_error(e)
            record_retrieval_trace(
                workflow_run_id=get_current_workflow_run_id(),
                retrieval_type="route",
                query_chars=len(route_query),
                top_k=getattr(self.retriever, "top_k", None),
                doc_count=0,
                duration_ms=elapsed_ms(start),
                success=False,
                error_type=error_type,
                error_message=str(e),
            )
            raise
        finally:
            self._route_metadata_filters = {}

        logger.info(
            "路线检索完成: tools=%s, workflows=%s, blockages=%s",
            len(result["tools"]),
            len(result["workflows"]),
            len(result["blockages"]),
        )

        record_retrieval_trace(
            workflow_run_id=get_current_workflow_run_id(),
            retrieval_type="route",
            query_chars=len(route_query),
            top_k=getattr(self.retriever, "top_k", None),
            doc_count=sum(len(docs) for docs in result.values()),
            duration_ms=elapsed_ms(start),
            success=True,
        )

        return result

    def retrieve_for_blockage(self, user_goal: str, selected_step: str, blockage_text: str) -> Dict[str, List[Document]]:
        """卡点细化前的检索。

        卡点细化重点参考：
        1. blockages：解决当前卡点
        2. tools：必要时推荐替代工具
        """
        logger.info(
            f"开始卡点细化前检索: goal={user_goal}, step={selected_step}, blockage={blockage_text}"
        )

        blockage_query = f"{user_goal} {selected_step} {blockage_text} 卡点 解决步骤 替代工具 done_check"
        start = time.perf_counter()

        try:
            result = {
                "blockages": self.retrieve_by_source(blockage_query, "blockages"),
                "tools": self.retrieve_by_source(blockage_query, "tools"),
            }
        except Exception as e:
            error_type = classify_error(e)
            record_retrieval_trace(
                workflow_run_id=get_current_workflow_run_id(),
                retrieval_type="blockage",
                query_chars=len(blockage_query),
                top_k=getattr(self.retriever, "top_k", None),
                doc_count=0,
                duration_ms=elapsed_ms(start),
                success=False,
                error_type=error_type,
                error_message=str(e),
            )
            raise

        logger.info(
            "卡点检索完成: blockages=%s, tools=%s",
            len(result["blockages"]),
            len(result["tools"]),
        )

        record_retrieval_trace(
            workflow_run_id=get_current_workflow_run_id(),
            retrieval_type="blockage",
            query_chars=len(blockage_query),
            top_k=getattr(self.retriever, "top_k", None),
            doc_count=sum(len(docs) for docs in result.values()),
            duration_ms=elapsed_ms(start),
            success=True,
        )

        return result

    @staticmethod
    def format_docs(docs: List[Document]) -> str:
        """把 Document 列表格式化成字符串，方便后续放进 prompt。"""
        if not docs:
            return "没有检索到相关片段。"

        formatted_parts = []

        for index, doc in enumerate(docs, start=1):
            source = doc.metadata.get("source", "unknown")
            file_name = doc.metadata.get("file_name", "unknown")
            section_index = doc.metadata.get("section_index", "unknown")
            chunk_index = doc.metadata.get("chunk_index", "unknown")

            formatted_parts.append(
                f"【片段 {index}】\n"
                f"source: {source}\n"
                f"file_name: {file_name}\n"
                f"section_index: {section_index}\n"
                f"chunk_index: {chunk_index}\n"
                f"content:\n{doc.page_content}\n"
            )

        return "\n---\n".join(formatted_parts)

    def format_route_context(self, retrieved_docs: Dict[str, List[Document]]) -> str:
        """格式化路线生成所需的检索上下文。"""
        tools_context = self.format_docs(retrieved_docs.get("tools", []))
        workflows_context = self.format_docs(retrieved_docs.get("workflows", []))
        blockages_context = self.format_docs(retrieved_docs.get("blockages", []))

        return (
            "# 工具知识片段\n"
            f"{tools_context}\n\n"
            "# Workflow 模板片段\n"
            f"{workflows_context}\n\n"
            "# 卡点提醒片段\n"
            f"{blockages_context}"
        )

    def format_blockage_context(self, retrieved_docs: Dict[str, List[Document]]) -> str:
        """格式化卡点细化所需的检索上下文。"""
        blockages_context = self.format_docs(retrieved_docs.get("blockages", []))
        tools_context = self.format_docs(retrieved_docs.get("tools", []))

        return (
            "# 卡点解决片段\n"
            f"{blockages_context}\n\n"
            "# 可参考工具片段\n"
            f"{tools_context}"
        )
