from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    KNOWLEDGE_DIR,
    VECTOR_STORE_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    SEPARATORS,
    ensure_dirs,
    validate_api_key,
)
from utils.logger import setup_logger

#传入日志器工具对象,并在日志中写出对应的文件名
logger = setup_logger(__name__)


#读取知识库文件路径,装进列表,返回出去
def load_markdown_files() -> List[Path]:
    """读取 knowledge 目录下的所有 md 文件路径。"""
    md_files = sorted(KNOWLEDGE_DIR.glob("*.md"))       #筛选knowledge文件夹中的.md结尾的文件(知识库文件),并按顺序排好
    logger.info(f"发现知识文件数量: {len(md_files)}")

    #如果没有知识库文件,直接停止运行并报错
    if not md_files:
        raise FileNotFoundError(f"knowledge 目录下没有找到 .md 文件: {KNOWLEDGE_DIR}")

    return md_files

#作用很小,在metadata中给文本块附加信息来源,标注上来源于哪类文件,都不属于就是unknown
def infer_source_from_file(file_path: Path) -> str:
    """根据文件名推断知识来源。"""
    if file_path.name == "tools.md":
        return "tools"
    if file_path.name == "workflows.md":
        return "workflows"
    if file_path.name == "blockages.md":
        return "blockages"
    return "unknown"


def split_markdown_by_heading(text: str) -> List[str]:
    """按 Markdown 标题切分文本，尽量保持每个小节语义完整。"""
    sections = []
    current_lines = []

    for line in text.splitlines():
        if line.startswith("## ") and current_lines:
            sections.append("\n".join(current_lines).strip())
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append("\n".join(current_lines).strip())

    return [section for section in sections if section]


def build_raw_documents(md_files: List[Path]) -> List[Document]:
    """读取 md 文件，并按标题切成带 metadata 的 Document。"""
    documents = []

    for file_path in md_files:
        source = infer_source_from_file(file_path)
        text = file_path.read_text(encoding="utf-8")
        sections = split_markdown_by_heading(text)

        logger.info(f"{file_path.name} 切分出小节数量: {len(sections)}")

        for index, section in enumerate(sections):
            documents.append(
                Document(
                    page_content=section,
                    metadata={
                        "source": source,
                        "file_name": file_path.name,
                        "section_index": index,
                    },
                )
            )

    logger.info(f"基础 Document 数量: {len(documents)}")
    return documents


def split_long_documents(documents: List[Document]) -> List[Document]:
    """对过长 Document 做二次切分。"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARATORS,
    )

    split_docs = splitter.split_documents(documents)

    for index, doc in enumerate(split_docs):
        doc.metadata["chunk_index"] = index

    logger.info(f"二次切分后 Document 数量: {len(split_docs)}")
    return split_docs


def build_vector_store(documents: List[Document]) -> None:
    """将 Document 写入 Chroma 向量数据库。"""
    if not documents:
        raise ValueError("没有可写入向量库的 Document。")

    logger.info("开始初始化 DashScope Embeddings")
    embeddings = DashScopeEmbeddings(model=EMBEDDING_MODEL_NAME)

    logger.info("开始写入 Chroma 向量数据库")
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(VECTOR_STORE_DIR),
    )

    count = vector_store._collection.count()
    logger.info(f"Chroma 写入完成，当前 collection 文档数量: {count}")

def main():
    ensure_dirs()
    validate_api_key()

    md_files = load_markdown_files()
    raw_documents = build_raw_documents(md_files)
    split_documents = split_long_documents(raw_documents)

    for doc in split_documents[:3]:
        logger.info(f"示例 metadata: {doc.metadata}")
        logger.info(f"示例内容长度: {len(doc.page_content)}")
        logger.info(f"示例内容前 80 字: {doc.page_content[:80]}")

    build_vector_store(split_documents)


if __name__ == "__main__":
    main()