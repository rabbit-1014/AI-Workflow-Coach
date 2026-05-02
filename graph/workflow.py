from langgraph.graph import END, START, StateGraph

from graph.state import WorkflowState
from graph.nodes import (
    analyze_task_node,
    ask_followup_node,
    close_followup_node,
    generate_route_node,
    retrieve_for_blockage_node,
    retrieve_for_route_node,
    solve_blockage_node,
)


def route_after_analyze(state: WorkflowState) -> str:
    if state.get("need_close_followup"):
        return "close_followup"

    if state.get("need_followup"):
        return END

    return "retrieve_for_route"


def route_after_close_followup(state: WorkflowState) -> str:
    close_result = state.get("close_result", "")

    if close_result == "close_partial":
        return END

    if close_result in {"close_success", "close_failed"}:
        return "retrieve_for_route"

    return END


def build_route_workflow():
    graph = StateGraph(WorkflowState)

    graph.add_node("analyze_task", analyze_task_node)
    graph.add_node("ask_followup", ask_followup_node)
    graph.add_node("close_followup", close_followup_node)
    graph.add_node("retrieve_for_route", retrieve_for_route_node)
    graph.add_node("generate_route", generate_route_node)

    graph.add_edge(START, "analyze_task")

    graph.add_conditional_edges(
        "analyze_task",
        route_after_analyze,
        {
            "close_followup": "close_followup",
            "retrieve_for_route": "retrieve_for_route",
            END: END,
        },
    )

    graph.add_edge("ask_followup", "close_followup")

    graph.add_conditional_edges(
        "close_followup",
        route_after_close_followup,
        {
            "retrieve_for_route": "retrieve_for_route",
            END: END,
        },
    )

    graph.add_edge("retrieve_for_route", "generate_route")
    graph.add_edge("generate_route", END)

    return graph.compile()


def build_blockage_workflow():
    graph = StateGraph(WorkflowState)

    graph.add_node("retrieve_for_blockage", retrieve_for_blockage_node)
    graph.add_node("solve_blockage", solve_blockage_node)

    graph.add_edge(START, "retrieve_for_blockage")
    graph.add_edge("retrieve_for_blockage", "solve_blockage")
    graph.add_edge("solve_blockage", END)

    return graph.compile()
