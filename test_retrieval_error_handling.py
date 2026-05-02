from graph.nodes import retrieve_for_blockage_node, retrieve_for_route_node
import graph.nodes as nodes
from utils.observability import generate_workflow_run_id, read_observability_records


def test_route_retrieval_error_returns_controlled_state_and_trace():
    workflow_run_id = generate_workflow_run_id("route_retrieval_error")
    original_retrieve_by_source = nodes.rag_service.retrieve_by_source

    def fake_retrieve_by_source(*args, **kwargs):
        raise TimeoutError("Request timed out")

    nodes.rag_service.retrieve_by_source = fake_retrieve_by_source
    try:
        result = retrieve_for_route_node({
            "workflow_run_id": workflow_run_id,
            "effective_goal": "做小红书内容创作",
        })
    finally:
        nodes.rag_service.retrieve_by_source = original_retrieve_by_source

    assert result["current_stage"] == "error"
    assert "路线检索失败" in result["error_message"]

    records = read_observability_records(workflow_run_id)
    retrieval_trace = records["retrieval_trace"]
    assert retrieval_trace
    assert retrieval_trace[-1]["success"] is False
    assert retrieval_trace[-1]["error_type"] == "timeout_error"
    assert len(retrieval_trace) == 1


def test_blockage_retrieval_error_returns_controlled_state_and_trace():
    workflow_run_id = generate_workflow_run_id("blockage_retrieval_error")
    original_retrieve_by_source = nodes.rag_service.retrieve_by_source

    def fake_retrieve_by_source(*args, **kwargs):
        raise TimeoutError("Request timed out")

    nodes.rag_service.retrieve_by_source = fake_retrieve_by_source
    try:
        result = retrieve_for_blockage_node({
            "workflow_run_id": workflow_run_id,
            "effective_goal": "做小红书内容创作",
            "selected_step": "制作封面",
            "blockage_text": "点击率低",
        })
    finally:
        nodes.rag_service.retrieve_by_source = original_retrieve_by_source

    assert result["current_stage"] == "error"
    assert "卡点检索失败" in result["error_message"]

    records = read_observability_records(workflow_run_id)
    retrieval_trace = records["retrieval_trace"]
    assert retrieval_trace
    assert retrieval_trace[-1]["success"] is False
    assert retrieval_trace[-1]["error_type"] == "timeout_error"
    assert len(retrieval_trace) == 1


if __name__ == "__main__":
    test_route_retrieval_error_returns_controlled_state_and_trace()
    test_blockage_retrieval_error_returns_controlled_state_and_trace()
    print("test_retrieval_error_handling.py: all tests passed")
