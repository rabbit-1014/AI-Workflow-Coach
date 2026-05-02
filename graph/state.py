from typing import Optional

from typing_extensions import TypedDict

from schemas import BlockageOutput, RouteOutput


class WorkflowState(TypedDict, total=False):
    workflow_run_id: str

    user_goal: str
    current_stage: str

    task_understanding: str
    need_followup: bool
    need_close_followup: bool
    followup_question: str
    followup_answer: str
    close_result: str
    effective_goal: str
    need_direction_choice: bool
    direction_options: list[str]
    selected_direction_option: str
    detected_bucket: str

    route_context: str
    route_result: RouteOutput

    selected_step: str
    blockage_text: str
    blockage_context: str
    blockage_result: BlockageOutput

    error_message: str
