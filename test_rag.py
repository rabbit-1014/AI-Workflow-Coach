from services.rag_service import RagService
from utils.logger import setup_logger


logger = setup_logger(__name__)


def print_section(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def test_route_retrieval():
    """测试路线生成前检索。"""
    print_section("测试 1：路线生成前检索")

    rag_service = RagService()
    user_goal = "AI 动漫短剧"

    retrieved_docs = rag_service.retrieve_for_route(user_goal)

    print("检索数量：")
    print({source: len(docs) for source, docs in retrieved_docs.items()})

    print("\n路线生成上下文预览：")
    context = rag_service.format_route_context(retrieved_docs)
    print(context[:2000])

    assert len(retrieved_docs["tools"]) > 0, "tools 检索结果为空"
    assert len(retrieved_docs["workflows"]) > 0, "workflows 检索结果为空"
    assert len(retrieved_docs["blockages"]) > 0, "blockages 检索结果为空"


def test_blockage_retrieval():
    """测试卡点细化前检索。"""
    print_section("测试 2：卡点细化前检索")

    rag_service = RagService()

    user_goal = "AI 动漫短剧"
    selected_step = "生成角色图"
    blockage_text = "角色图不稳定"

    retrieved_docs = rag_service.retrieve_for_blockage(
        user_goal=user_goal,
        selected_step=selected_step,
        blockage_text=blockage_text,
    )

    print("检索数量：")
    print({source: len(docs) for source, docs in retrieved_docs.items()})

    print("\n卡点细化上下文预览：")
    context = rag_service.format_blockage_context(retrieved_docs)
    print(context[:2000])

    assert len(retrieved_docs["blockages"]) > 0, "blockages 检索结果为空"
    assert len(retrieved_docs["tools"]) > 0, "tools 检索结果为空"


def main():
    test_route_retrieval()
    test_blockage_retrieval()

    print_section("RAG 检索链路测试通过")
    print("输入：AI 动漫短剧")
    print("结果：已成功检索 tools / workflows / blockages 相关片段")


if __name__ == "__main__":
    main()