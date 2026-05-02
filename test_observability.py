import json

from graph.nodes import generate_route_node, solve_blockage_node
import graph.nodes as nodes
from schemas import BlockageOutput, RouteOutput, RouteStep
from utils.observability import (
    generate_workflow_run_id,
    read_observability_records,
    record_model_call_log,
    record_retrieval_trace,
    record_workflow_trace,
)


def test_workflow_trace_write_and_read():
    workflow_run_id = generate_workflow_run_id("test_workflow")

    record_workflow_trace(
        workflow_run_id=workflow_run_id,
        node_name="test_node",
        current_stage="test_stage",
        success=True,
        duration_ms=12,
    )

    records = read_observability_records(workflow_run_id)["workflow_trace"]

    assert records
    assert records[-1]["node_name"] == "test_node"
    assert records[-1]["duration_ms"] == 12
    assert records[-1]["success"] is True


def test_model_call_log_does_not_store_sensitive_content():
    workflow_run_id = generate_workflow_run_id("test_model")

    record_model_call_log(
        workflow_run_id=workflow_run_id,
        call_type="route_generation",
        provider="openai_compatible",
        model="deepseek-v4-flash",
        input_chars=123,
        output_chars=456,
        duration_ms=789,
        success=True,
    )

    records = read_observability_records(workflow_run_id)["model_call_log"]
    serialized = json.dumps(records, ensure_ascii=False)

    assert records
    assert records[-1]["provider"] == "openai_compatible"
    assert records[-1]["model"] == "deepseek-v4-flash"
    assert records[-1]["input_chars"] == 123
    assert records[-1]["output_chars"] == 456
    assert records[-1]["duration_ms"] == 789
    assert "api_key" not in serialized.lower()
    assert "sk-" not in serialized
    assert "prompt" not in serialized.lower()


def test_retrieval_trace_write_and_read_without_query():
    workflow_run_id = generate_workflow_run_id("test_retrieval")

    record_retrieval_trace(
        workflow_run_id=workflow_run_id,
        retrieval_type="route",
        query_chars=28,
        top_k=5,
        doc_count=3,
        duration_ms=45,
        success=True,
    )

    records = read_observability_records(workflow_run_id)["retrieval_trace"]
    serialized = json.dumps(records, ensure_ascii=False)

    assert records
    assert records[-1]["retrieval_type"] == "route"
    assert records[-1]["doc_count"] == 3
    assert records[-1]["duration_ms"] == 45
    assert '"query":' not in serialized.lower()
    assert "query_chars" in serialized


def test_generate_route_node_returns_workflow_run_id():
    workflow_run_id = generate_workflow_run_id("test_route_node")
    original_generate_route = nodes.route_generator.generate_route

    def fake_generate_route(user_goal: str, route_context: str):
        return RouteOutput(
            task_summary="测试路线",
            route_type="测试",
            steps=[
                RouteStep(
                    step_name="测试步骤",
                    step_goal="测试目标",
                    primary_tool="测试工具",
                    backup_tool="测试备选",
                    suggested_input="测试输入",
                    expected_output="测试产出",
                    execution_tip="测试提醒",
                    ready_check="测试标准",
                )
            ],
        )

    nodes.route_generator.generate_route = fake_generate_route
    try:
        result = generate_route_node({
            "workflow_run_id": workflow_run_id,
            "effective_goal": "测试目标",
            "route_context": "测试上下文",
        })
    finally:
        nodes.route_generator.generate_route = original_generate_route

    assert result["workflow_run_id"] == workflow_run_id
    assert result["current_stage"] == "route_generated"

    records = read_observability_records(workflow_run_id)["workflow_trace"]
    assert any(record["node_name"] == "generate_route_node" for record in records)


def test_solve_blockage_node_returns_workflow_run_id():
    workflow_run_id = generate_workflow_run_id("test_blockage_node")
    original_solve_blockage = nodes.blockage_solver.solve_blockage

    def fake_solve_blockage(**kwargs):
        return BlockageOutput(
            why_stuck="测试卡点原因",
            substeps=["步骤一", "步骤二"],
            simple_input="测试简单输入",
            alternative_tool="测试替代工具",
            done_check="测试完成标准",
        )

    nodes.blockage_solver.solve_blockage = fake_solve_blockage
    try:
        result = solve_blockage_node({
            "workflow_run_id": workflow_run_id,
            "effective_goal": "测试目标",
            "selected_step": "测试步骤",
            "blockage_text": "测试卡点",
            "blockage_context": "测试上下文",
        })
    finally:
        nodes.blockage_solver.solve_blockage = original_solve_blockage

    assert result["workflow_run_id"] == workflow_run_id
    assert result["current_stage"] == "blockage_solved"

    records = read_observability_records(workflow_run_id)["workflow_trace"]
    assert any(record["node_name"] == "solve_blockage_node" for record in records)


if __name__ == "__main__":
    test_workflow_trace_write_and_read()
    test_model_call_log_does_not_store_sensitive_content()
    test_retrieval_trace_write_and_read_without_query()
    test_generate_route_node_returns_workflow_run_id()
    test_solve_blockage_node_returns_workflow_run_id()
    print("test_observability.py: all tests passed")
