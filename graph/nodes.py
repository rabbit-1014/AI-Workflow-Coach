import time

from graph.direction_options import (
    build_direction_options,
    detect_bucket,
    is_generic_failed_answer,
    is_partial_answer,
    is_specific_enough_answer,
)
from graph.state import WorkflowState
from services.blockage_solver import BlockageSolver
from services.rag_service import RagService
from services.route_generator import RouteGenerator
from utils.error_utils import classify_error
from utils.logger import setup_logger
from utils.observability import (
    elapsed_ms,
    get_or_create_workflow_run_id,
    record_workflow_trace,
    reset_observability_context,
    set_observability_context,
)


logger = setup_logger(__name__)

rag_service = RagService()
route_generator = RouteGenerator()
blockage_solver = BlockageSolver()


GENERIC_FOLLOWUP_PHRASES = [
    "随便",
    "都行",
    "都可以",
    "不知道",
    "没想好",
    "没想清楚",
    "还没想清楚",
    "先通用一点",
    "你看着安排",
    "先给个方向",
    "先来一个",
    "先试试",
    "能发就行",
    "做点东西",
    "做点ai",
]

GENERIC_INITIAL_GOAL_PHRASES = [
    "赚钱",
    "做项目",
    "学ai",
    "我想学ai",
    "用ai",
    "用ai做点东西",
    "做点东西",
    "我想做内容",
    "做内容",
    "我想做ai视频",
    "做ai视频",
    "ai视频",
]

CLEAR_BUCKET_GOALS = [
    "ai学习辅助",
    "ai内容创作",
    "ai动漫短剧",
    "ai短剧",
]

CONCRETE_GOAL_MARKERS = [
    "14天",
    "7天",
    "30秒",
    "60秒",
    "分钟",
    "主角",
    "风格",
    "平台",
    "短视频平台",
    "主题",
    "小红书",
    "图文",
    "标题",
    "封面",
    "正文",
    "高频问题",
    "重点",
    "提升",
    "阅读",
    "单词复习",
    "背单词",
    "错词",
    "测验",
    "分镜",
    "角色设定",
    "首集",
    "成片",
    "整理成",
    "覆盖",
    "生成",
    "流程",
    "工具",
]

BUCKET_KEYWORDS = {
    "learning": [
        "学",
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

FALLBACK_GOALS = {
    "learning": "AI 学习辅助",
    "content": "AI 内容创作",
    "shortdrama": "AI 动漫短剧",
}


def _finish_node(
    workflow_run_id: str,
    node_name: str,
    start: float,
    result: dict,
    extra: dict | None = None,
) -> dict:
    result["workflow_run_id"] = workflow_run_id
    error_message = result.get("error_message", "")
    record_workflow_trace(
        workflow_run_id=workflow_run_id,
        node_name=node_name,
        current_stage=result.get("current_stage", ""),
        success=not bool(error_message),
        duration_ms=elapsed_ms(start),
        error_message=error_message,
        extra=extra or {},
    )
    return result


def analyze_task_node(state: WorkflowState) -> dict:
    start = time.perf_counter()
    workflow_run_id = get_or_create_workflow_run_id(state, prefix="route")
    user_goal = state.get("user_goal", "").strip()
    if not user_goal:
        return _finish_node(workflow_run_id, "analyze_task_node", start, {
            "current_stage": "error",
            "error_message": "user_goal 不能为空。"
        })

    followup_answer = state.get("followup_answer", "").strip()
    if followup_answer:
        task_understanding = f"用户原始目标为「{user_goal}」，补充后的具体方向为「{followup_answer}」。"

        logger.info("analyze_task_node 完成，检测到 followup_answer，进入补问收口")
        return _finish_node(workflow_run_id, "analyze_task_node", start, {
            "current_stage": "task_analyzed",
            "task_understanding": task_understanding,
            "need_followup": False,
            "need_close_followup": True,
            "error_message": ""
        }, extra={"has_followup_answer": True})

    need_followup = _should_ask_followup(user_goal, followup_answer)

    task_understanding = f"用户希望围绕「{user_goal}」获得可执行的 AI workflow 建议。"

    result = {
        "current_stage": "task_analyzed",
        "task_understanding": task_understanding,
        "need_followup": need_followup,
        "need_close_followup": False,
        "error_message": ""
    }

    if need_followup:
        result["followup_question"] = (
            "你更偏向哪种方向：AI 学习辅助、AI 内容创作，还是 AI 动漫短剧/短视频？"
        )

    logger.info(f"analyze_task_node 完成，need_followup={need_followup}")
    return _finish_node(
        workflow_run_id,
        "analyze_task_node",
        start,
        result,
        extra={"need_followup": need_followup},
    )


def _should_ask_followup(user_goal: str, followup_answer: str = "") -> bool:
    if followup_answer.strip():
        return False

    normalized_goal = _normalize_text(user_goal)
    if not normalized_goal:
        return True

    if _is_generic_initial_goal(user_goal):
        return True

    if normalized_goal in {_normalize_text(goal) for goal in CLEAR_BUCKET_GOALS}:
        return False

    bucket = _bucket_from_text(user_goal)
    if not bucket:
        return len(normalized_goal) < 18

    if _has_concrete_goal_signals(user_goal):
        return False

    return len(normalized_goal) < 16


def _is_generic_initial_goal(user_goal: str) -> bool:
    normalized_goal = _normalize_text(user_goal)
    return any(
        _normalize_text(phrase) == normalized_goal
        or _normalize_text(phrase) in normalized_goal and len(normalized_goal) <= 12
        for phrase in GENERIC_INITIAL_GOAL_PHRASES
    )


def _has_concrete_goal_signals(user_goal: str) -> bool:
    normalized_goal = _normalize_text(user_goal)
    marker_count = sum(
        1
        for marker in CONCRETE_GOAL_MARKERS
        if _normalize_text(marker) in normalized_goal
    )
    return marker_count >= 2 or (marker_count >= 1 and len(normalized_goal) >= 24)


def ask_followup_node(state: WorkflowState) -> dict:
    start = time.perf_counter()
    workflow_run_id = get_or_create_workflow_run_id(state, prefix="route")
    logger.info("ask_followup_node 执行")
    return _finish_node(workflow_run_id, "ask_followup_node", start, {
        "current_stage": "followup_asked"
    })


def close_followup_node(state: WorkflowState) -> dict:
    start = time.perf_counter()
    workflow_run_id = get_or_create_workflow_run_id(state, prefix="route")
    user_goal = state.get("user_goal", "").strip()
    followup_answer = state.get("followup_answer", "").strip()
    is_generic = is_generic_failed_answer(followup_answer)
    bucket = detect_bucket(user_goal, followup_answer)

    if is_generic and not bucket:
        close_result = "close_failed"
        effective_goal = _fallback_effective_goal(user_goal, followup_answer)
        task_understanding = (
            f"补问回答仍偏泛，系统将以保底方向「{effective_goal}」生成最小起步路线。"
        )
    elif is_generic and bucket:
        direction_options = build_direction_options(
            bucket=bucket,
            user_goal=user_goal,
            followup_answer=followup_answer,
        )
        logger.info(
            f"close_followup_node 完成，close_result=close_partial, bucket={bucket}"
        )
        return _finish_node(workflow_run_id, "close_followup_node", start, {
            "current_stage": "direction_choice_required",
            "close_result": "close_partial",
            "need_close_followup": False,
            "need_direction_choice": True,
            "detected_bucket": bucket,
            "direction_options": direction_options,
            "selected_direction_option": "",
            "effective_goal": "",
            "route_result": None,
            "error_message": "",
        }, extra={"close_result": "close_partial", "detected_bucket": bucket})
    elif is_specific_enough_answer(followup_answer):
        close_result = "close_success"
        effective_goal = followup_answer
        task_understanding = f"补问后确认用户更具体的方向为：{effective_goal}"
        logger.info(f"close_followup_node 完成，close_result={close_result}")
        return _finish_node(workflow_run_id, "close_followup_node", start, {
            "current_stage": "followup_closed",
            "close_result": close_result,
            "effective_goal": effective_goal,
            "task_understanding": task_understanding,
            "need_close_followup": False,
            "need_direction_choice": False,
            "direction_options": [],
            "selected_direction_option": "",
            "detected_bucket": "",
            "error_message": "",
        }, extra={"close_result": close_result})
    elif is_partial_answer(user_goal, followup_answer):
        direction_options = build_direction_options(
            bucket=bucket,
            user_goal=user_goal,
            followup_answer=followup_answer,
        )
        logger.info(
            f"close_followup_node 完成，close_result=close_partial, bucket={bucket}"
        )
        return _finish_node(workflow_run_id, "close_followup_node", start, {
            "current_stage": "direction_choice_required",
            "close_result": "close_partial",
            "need_close_followup": False,
            "need_direction_choice": True,
            "detected_bucket": bucket,
            "direction_options": direction_options,
            "selected_direction_option": "",
            "effective_goal": "",
            "route_result": None,
            "error_message": "",
        }, extra={"close_result": "close_partial", "detected_bucket": bucket})
    else:
        close_result = "close_failed"
        effective_goal = _fallback_effective_goal(user_goal, followup_answer)
        task_understanding = (
            f"补问回答仍偏泛，系统将以保底方向「{effective_goal}」生成最小起步路线。"
        )

    logger.info(f"close_followup_node 完成，close_result={close_result}")
    return _finish_node(workflow_run_id, "close_followup_node", start, {
        "current_stage": "followup_closed",
        "close_result": close_result,
        "effective_goal": effective_goal,
        "task_understanding": task_understanding,
        "need_close_followup": False,
        "need_direction_choice": False,
        "direction_options": [],
        "selected_direction_option": "",
        "detected_bucket": "",
        "error_message": "",
    }, extra={"close_result": close_result})


def _is_specific_followup_answer(user_goal: str, followup_answer: str) -> bool:
    _ = user_goal
    return is_specific_enough_answer(followup_answer)


def _normalize_text(text: str) -> str:
    return "".join(text.lower().split())


def _is_generic_followup_answer(followup_answer: str) -> bool:
    normalized_answer = _normalize_text(followup_answer)
    if not normalized_answer:
        return True

    return any(
        _normalize_text(phrase) in normalized_answer
        for phrase in GENERIC_FOLLOWUP_PHRASES
    )


def _infer_goal_bucket(user_goal: str, followup_answer: str = "") -> str:
    user_bucket = _bucket_from_text(user_goal)
    if user_bucket:
        return user_bucket

    if followup_answer and not _is_generic_followup_answer(followup_answer):
        followup_bucket = _bucket_from_text(followup_answer)
        if followup_bucket:
            return followup_bucket

    return "content"


def _bucket_from_text(text: str) -> str:
    normalized_text = _normalize_text(text)
    if not normalized_text:
        return ""

    scores = {}
    for bucket, keywords in BUCKET_KEYWORDS.items():
        score = sum(1 for keyword in keywords if _normalize_text(keyword) in normalized_text)
        if score:
            scores[bucket] = score

    if not scores:
        return ""

    priority = ["shortdrama", "learning", "content"]
    return max(scores, key=lambda bucket: (scores[bucket], -priority.index(bucket)))


def _fallback_effective_goal(user_goal: str, followup_answer: str = "") -> str:
    bucket = _infer_goal_bucket(user_goal, followup_answer)
    return FALLBACK_GOALS[bucket]


def _get_effective_goal_for_blockage(state: WorkflowState) -> str:
    return (
        state.get("effective_goal")
        or state.get("followup_answer")
        or state.get("user_goal")
        or ""
    ).strip()


def retrieve_for_route_node(state: WorkflowState) -> dict:
    start = time.perf_counter()
    workflow_run_id = get_or_create_workflow_run_id(state, prefix="route")
    user_goal = (
        state.get("effective_goal", "").strip()
        or state.get("followup_answer", "").strip()
        or state.get("user_goal", "").strip()
    )

    if not user_goal:
        return _finish_node(workflow_run_id, "retrieve_for_route_node", start, {
            "current_stage": "error",
            "error_message": "retrieve_for_route_node 缺少 user_goal。"
        })

    token = set_observability_context(
        workflow_run_id=workflow_run_id,
        call_type="route_retrieval",
    )
    try:
        retrieved_docs = rag_service.retrieve_for_route(user_goal)
        route_context = rag_service.format_route_context(retrieved_docs)
    except Exception as e:
        error_type = classify_error(e)
        logger.exception("retrieve_for_route_node 路线检索失败")
        return _finish_node(workflow_run_id, "retrieve_for_route_node", start, {
            "current_stage": "error",
            "error_message": f"路线检索失败：{e}",
        }, extra={"error_type": error_type})
    finally:
        reset_observability_context(token)

    logger.info("retrieve_for_route_node 完成")
    return _finish_node(workflow_run_id, "retrieve_for_route_node", start, {
        "current_stage": "route_retrieved",
        "route_context": route_context,
        "error_message": ""
    }, extra={"route_context_chars": len(route_context)})


def generate_route_node(state: WorkflowState) -> dict:
    start = time.perf_counter()
    workflow_run_id = get_or_create_workflow_run_id(state, prefix="route")
    user_goal = (
        state.get("effective_goal", "").strip()
        or state.get("followup_answer", "").strip()
        or state.get("user_goal", "").strip()
    )
    route_context = state.get("route_context", "").strip()

    if not user_goal or not route_context:
        return _finish_node(workflow_run_id, "generate_route_node", start, {
            "current_stage": "error",
            "error_message": "generate_route_node 缺少 user_goal 或 route_context。"
        })

    token = set_observability_context(
        workflow_run_id=workflow_run_id,
        call_type="route_generation",
    )
    try:
        route_result = route_generator.generate_route(user_goal, route_context)
    except ValueError as e:
        logger.error(f"generate_route_node 路线生成失败: {e}")
        return _finish_node(workflow_run_id, "generate_route_node", start, {
            "current_stage": "error",
            "error_message": f"路线生成失败：{e}",
        })
    except Exception:
        logger.exception("generate_route_node 出现未预期异常")
        return _finish_node(workflow_run_id, "generate_route_node", start, {
            "current_stage": "error",
            "error_message": "路线生成失败：系统内部错误，请稍后重试。",
        })
    finally:
        reset_observability_context(token)

    logger.info("generate_route_node 完成")
    return _finish_node(workflow_run_id, "generate_route_node", start, {
        "current_stage": "route_generated",
        "route_result": route_result,
        "error_message": ""
    }, extra={"step_count": len(route_result.steps)})


def retrieve_for_blockage_node(state: WorkflowState) -> dict:
    start = time.perf_counter()
    workflow_run_id = get_or_create_workflow_run_id(state, prefix="blockage")
    user_goal = _get_effective_goal_for_blockage(state)
    selected_step = state.get("selected_step", "").strip()
    blockage_text = state.get("blockage_text", "").strip()

    if not user_goal or not selected_step or not blockage_text:
        return _finish_node(workflow_run_id, "retrieve_for_blockage_node", start, {
            "current_stage": "error",
            "error_message": "retrieve_for_blockage_node 缺少 user_goal / selected_step / blockage_text。"
        })

    token = set_observability_context(
        workflow_run_id=workflow_run_id,
        call_type="blockage_retrieval",
    )
    try:
        retrieved_docs = rag_service.retrieve_for_blockage(
            user_goal=user_goal,
            selected_step=selected_step,
            blockage_text=blockage_text,
        )
        blockage_context = rag_service.format_blockage_context(retrieved_docs)
    except Exception as e:
        error_type = classify_error(e)
        logger.exception("retrieve_for_blockage_node 卡点检索失败")
        return _finish_node(workflow_run_id, "retrieve_for_blockage_node", start, {
            "current_stage": "error",
            "error_message": f"卡点检索失败：{e}",
        }, extra={"error_type": error_type})
    finally:
        reset_observability_context(token)

    logger.info("retrieve_for_blockage_node 完成")
    return _finish_node(workflow_run_id, "retrieve_for_blockage_node", start, {
        "current_stage": "blockage_retrieved",
        "blockage_context": blockage_context,
        "error_message": ""
    }, extra={"blockage_context_chars": len(blockage_context)})


def solve_blockage_node(state: WorkflowState) -> dict:
    start = time.perf_counter()
    workflow_run_id = get_or_create_workflow_run_id(state, prefix="blockage")
    user_goal = _get_effective_goal_for_blockage(state)
    selected_step = state.get("selected_step", "").strip()
    blockage_text = state.get("blockage_text", "").strip()
    blockage_context = state.get("blockage_context", "").strip()

    if not user_goal or not selected_step or not blockage_text or not blockage_context:
        return _finish_node(workflow_run_id, "solve_blockage_node", start, {
            "current_stage": "error",
            "error_message": "solve_blockage_node 缺少必要输入。"
        })

    token = set_observability_context(
        workflow_run_id=workflow_run_id,
        call_type="blockage_generation",
    )
    try:
        blockage_result = blockage_solver.solve_blockage(
            user_goal=user_goal,
            selected_step=selected_step,
            blockage_text=blockage_text,
            blockage_context=blockage_context,
        )
    except ValueError as e:
        logger.error(f"solve_blockage_node 卡点细化失败: {e}")
        return _finish_node(workflow_run_id, "solve_blockage_node", start, {
            "current_stage": "error",
            "error_message": f"卡点细化失败：{e}",
        })
    except Exception:
        logger.exception("solve_blockage_node 出现未预期异常")
        return _finish_node(workflow_run_id, "solve_blockage_node", start, {
            "current_stage": "error",
            "error_message": "卡点细化失败：系统内部错误，请稍后重试。",
        })
    finally:
        reset_observability_context(token)

    logger.info("solve_blockage_node 完成")
    return _finish_node(workflow_run_id, "solve_blockage_node", start, {
        "current_stage": "blockage_solved",
        "blockage_result": blockage_result,
        "error_message": ""
    }, extra={"substeps_count": len(blockage_result.substeps)})
