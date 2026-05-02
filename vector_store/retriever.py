from typing import List

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings

from config import (
    VECTOR_STORE_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    TOP_K,
    validate_api_key,
)
from utils.logger import setup_logger


logger = setup_logger(__name__)


class VectorRetriever:
    """封装 Chroma 向量检索逻辑。"""

    def __init__(self, top_k: int = TOP_K):
        validate_api_key()

        self.top_k = top_k
        self.embeddings = DashScopeEmbeddings(model=EMBEDDING_MODEL_NAME)

        self.vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=str(VECTOR_STORE_DIR),
            embedding_function=self.embeddings,
        )

        logger.info(
            f"VectorRetriever 初始化完成，collection={COLLECTION_NAME}, top_k={self.top_k}"
        )

    def search(self, query: str, metadata_filter: dict | None = None) -> List[Document]:
        """根据用户输入，从 Chroma 中检索相关文档。"""
        if not query or not query.strip():
            raise ValueError("检索 query 不能为空。")

        logger.info(f"开始检索 query: {query}")
        logger.info(f"metadata_filter: {metadata_filter}")

        docs = self.vector_store.similarity_search(
            query=query,
            k=self.top_k,
            filter=metadata_filter,
        )

        logger.info(f"检索完成，命中文档数量: {len(docs)}")

        for index, doc in enumerate(docs):
            logger.info(f"命中 {index + 1} metadata: {doc.metadata}")
            logger.info(f"命中 {index + 1} 内容前 80 字: {doc.page_content[:80]}")

        return docs