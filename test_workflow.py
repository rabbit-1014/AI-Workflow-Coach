from graph.workflow import build_blockage_workflow, build_route_workflow
from schemas import BlockageOutput, RouteOutput, RouteStep


def _fake_route_output(user_goal: str) -> RouteOutput:
    return RouteOutput(
        task_summary=f"测试路线：{user_goal}",
        route_type="测试路线",
        steps=[
            RouteStep(
                step_name="确定目标",
                step_goal="明确要做的最小版本",
                primary_tool="ChatGPT",
                backup_tool="手动梳理",
                suggested_input=user_goal,
                expected_output="一个可执行目标",
                execution_tip="先做最小闭环",
                ready_check="目标已明确",
            )
        ],
    )


def _patch_route_dependencies():
    import graph.nodes as nodes

    nodes.rag_service.retrieve_for_route = lambda user_goal: []
    nodes.rag_service.format_route_context = lambda docs: "测试 route context"
    nodes.route_generator.generate_route = lambda user_goal, route_context: _fake_route_output(user_goal)


def _patch_blockage_dependencies():
    import graph.nodes as nodes

    nodes.rag_service.retrieve_for_blockage = lambda user_goal, selected_step, blockage_text: []
    nodes.rag_service.format_blockage_context = lambda docs: "测试 blockage context"
    nodes.blockage_solver.solve_blockage = lambda **kwargs: BlockageOutput(
        why_stuck="测试卡点原因",
        substeps=["测试子步骤"],
        simple_input="测试输入",
        alternative_tool="测试替代工具",
        done_check="测试完成标准",
    )


def test_route_workflow():
    _patch_route_dependencies()
    app = build_route_workflow()

    initial_state = {
        "user_goal": "AI 动漫短剧"
    }

    final_state = app.invoke(initial_state)

    print("=" * 80)
    print("路线流测试完成")
    print("current_stage:", final_state.get("current_stage"))
    print("need_followup:", final_state.get("need_followup"))
    print("error_message:", final_state.get("error_message"))

    route_result = final_state.get("route_result")
    if route_result:
        print("task_summary:", route_result.task_summary)
        print("route_type:", route_result.route_type)
        print("steps_count:", len(route_result.steps))
    else:
        print("route_result: None")

    return final_state


def test_route_followup_breakpoint():
    _patch_route_dependencies()
    app = build_route_workflow()

    clear_state = app.invoke({
        "user_goal": "AI 动漫短剧"
    })
    assert clear_state.get("route_result") is not None
    assert clear_state.get("need_followup") is False

    followup_state = app.invoke({
        "user_goal": "学AI"
    })
    assert followup_state.get("need_followup") is True
    assert followup_state.get("followup_question")
    assert followup_state.get("route_result") is None
    assert followup_state.get("current_stage") == "task_analyzed"

    resumed_state = app.invoke({
        "user_goal": "学AI",
        "followup_answer": "做 60 秒 AI 动漫短剧，包含角色设定、分镜、成片和发布"
    })
    assert resumed_state.get("need_followup") is False
    assert resumed_state.get("close_result") == "close_success"
    assert resumed_state.get("effective_goal") == "做 60 秒 AI 动漫短剧，包含角色设定、分镜、成片和发布"
    assert resumed_state.get("route_result") is not None
    assert resumed_state.get("current_stage") == "route_generated"

    fallback_state = app.invoke({
        "user_goal": "做项目",
        "followup_answer": "随便做点AI的"
    })
    assert fallback_state.get("need_followup") is False
    assert fallback_state.get("close_result") == "close_failed"
    assert fallback_state.get("effective_goal") == "AI 内容创作"
    assert fallback_state.get("route_result") is not None
    assert fallback_state.get("current_stage") == "route_generated"


def test_blockage_workflow():
    _patch_blockage_dependencies()
    app = build_blockage_workflow()

    initial_state = {
        "user_goal": "AI 动漫短剧",
        "selected_step": "生成角色图",
        "blockage_text": "角色图不稳定"
    }

    final_state = app.invoke(initial_state)

    print("=" * 80)
    print("卡点流测试完成")
    print("current_stage:", final_state.get("current_stage"))
    print("error_message:", final_state.get("error_message"))

    blockage_result = final_state.get("blockage_result")
    if blockage_result:
        print("why_stuck:", blockage_result.why_stuck)
        print("substeps_count:", len(blockage_result.substeps))
    else:
        print("blockage_result: None")

    return final_state


def test_blockage_nodes_use_effective_goal_priority():
    import graph.nodes as nodes

    retrieve_goals = []
    solve_goals = []

    nodes.rag_service.retrieve_for_blockage = (
        lambda user_goal, selected_step, blockage_text: retrieve_goals.append(user_goal) or []
    )
    nodes.rag_service.format_blockage_context = lambda docs: "测试 blockage context"
    nodes.blockage_solver.solve_blockage = lambda **kwargs: (
        solve_goals.append(kwargs["user_goal"])
        or BlockageOutput(
            why_stuck="测试卡点原因",
            substeps=["测试子步骤"],
            simple_input="测试输入",
            alternative_tool="测试替代工具",
            done_check="测试完成标准",
        )
    )

    cases = [
        (
            {
                "user_goal": "我想做内容",
                "followup_answer": "做小红书文案流程",
                "effective_goal": "做一套小红书文案生成流程，能批量出标题、正文和封面文案",
                "selected_step": "生成标题",
                "blockage_text": "标题太普通",
            },
            "做一套小红书文案生成流程，能批量出标题、正文和封面文案",
        ),
        (
            {
                "user_goal": "我想做内容",
                "followup_answer": "做小红书文案流程",
                "selected_step": "生成标题",
                "blockage_text": "标题太普通",
            },
            "做小红书文案流程",
        ),
        (
            {
                "user_goal": "用 AI 做小红书图文内容创作",
                "selected_step": "制作封面和标题",
                "blockage_text": "封面点击率低",
            },
            "用 AI 做小红书图文内容创作",
        ),
    ]

    for state, expected_goal in cases:
        retrieve_result = nodes.retrieve_for_blockage_node(state)
        assert retrieve_result.get("current_stage") == "blockage_retrieved"
        assert retrieve_goals[-1] == expected_goal

        solve_state = {
            **state,
            "blockage_context": retrieve_result["blockage_context"],
        }
        solve_result = nodes.solve_blockage_node(solve_state)
        assert solve_result.get("current_stage") == "blockage_solved"
        assert solve_goals[-1] == expected_goal


if __name__ == "__main__":
    test_route_workflow()
    test_blockage_workflow()
