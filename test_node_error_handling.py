import graph.nodes as nodes


def test_generate_route_node_catches_value_error():
    original_generate_route = nodes.route_generator.generate_route

    def raise_value_error(user_goal: str, route_context: str):
        raise ValueError("LLM 输出无法解析为合法 RouteOutput")

    nodes.route_generator.generate_route = raise_value_error
    try:
        result = nodes.generate_route_node({
            "effective_goal": "做小红书内容创作",
            "route_context": "测试上下文",
        })
    finally:
        nodes.route_generator.generate_route = original_generate_route

    assert result["current_stage"] == "error"
    assert "路线生成失败" in result["error_message"]
    assert "LLM 输出无法解析" in result["error_message"]


def test_solve_blockage_node_catches_value_error():
    original_solve_blockage = nodes.blockage_solver.solve_blockage

    def raise_value_error(
        user_goal: str,
        selected_step: str,
        blockage_text: str,
        blockage_context: str,
    ):
        raise ValueError("LLM 输出无法解析为合法 BlockageOutput")

    nodes.blockage_solver.solve_blockage = raise_value_error
    try:
        result = nodes.solve_blockage_node({
            "effective_goal": "做小红书内容创作",
            "selected_step": "制作封面",
            "blockage_text": "点击率低",
            "blockage_context": "测试上下文",
        })
    finally:
        nodes.blockage_solver.solve_blockage = original_solve_blockage

    assert result["current_stage"] == "error"
    assert "卡点细化失败" in result["error_message"]
    assert "LLM 输出无法解析" in result["error_message"]


if __name__ == "__main__":
    test_generate_route_node_catches_value_error()
    test_solve_blockage_node_catches_value_error()
    print("test_node_error_handling.py: all tests passed")
