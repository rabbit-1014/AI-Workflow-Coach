from graph.direction_options import (
    build_direction_options,
    detect_bucket,
    is_partial_answer,
    is_specific_enough_answer,
)


# ── detect_bucket 基础 ─────────────────────────────────────────

def test_detect_bucket():
    assert detect_bucket("", "小红书") == "content"
    assert detect_bucket("", "背单词") == "learning"
    assert detect_bucket("", "分镜") == "shortdrama"
    assert detect_bucket("", "AI 视频") == "shortdrama"
    assert detect_bucket("", "公众号") == "content"


def test_detect_bucket_shortdrama_variants():
    assert detect_bucket("我想做短剧", "") == "shortdrama"
    assert detect_bucket("我想做真人短剧", "") == "shortdrama"
    assert detect_bucket("我想做 AI 动漫短剧", "") == "shortdrama"
    assert detect_bucket("我想做抖音剧情号", "") == "shortdrama"
    assert detect_bucket("我想做短剧脚本", "") == "shortdrama"
    assert detect_bucket("我想做分镜", "") == "shortdrama"
    assert detect_bucket("我想做微短剧", "") == "shortdrama"
    assert detect_bucket("我想做竖屏短剧", "") == "shortdrama"
    assert detect_bucket("我想做系列短剧", "") == "shortdrama"
    assert detect_bucket("我想做动画短剧", "") == "shortdrama"
    assert detect_bucket("我想做快手短剧", "") == "shortdrama"
    assert detect_bucket("短剧", "") == "shortdrama"


def test_detect_bucket_content_variants():
    assert detect_bucket("我想做小红书内容", "") == "content"
    assert detect_bucket("我想写公众号文章", "") == "content"
    assert detect_bucket("我想做短视频文案", "") == "content"


def test_detect_bucket_learning_variants():
    assert detect_bucket("我想背单词", "") == "learning"
    assert detect_bucket("我想做学习计划", "") == "learning"
    assert detect_bucket("我想整理错题", "") == "learning"


# ── 方向选项数量和可读性 ──────────────────────────────────────

def test_direction_options_default_count():
    """默认应返回 6 条。"""
    options = build_direction_options("shortdrama", "短剧", "")
    assert len(options) == 6, f"默认应返回 6 条，实际 {len(options)}: {options}"


def test_direction_options_limit_8():
    """传 limit=8 应返回 8 条。"""
    options = build_direction_options("shortdrama", "短剧", "", limit=8)
    assert len(options) == 8, f"limit=8 应返回 8 条，实际 {len(options)}: {options}"


def test_shortdrama_options_no_60s():
    """所有 shortdrama 方向选项不能包含 '60 秒' 或 '30 秒'。"""
    options = build_direction_options("shortdrama", "短剧", "", limit=8)
    for option in options:
        assert "60 秒" not in option, f"不应出现 '60 秒': {option}"
        assert "30 秒" not in option, f"不应出现 '30 秒': {option}"


def test_shortdrama_options_are_beginner_friendly():
    """shortdrama 选项应是小白能理解的需求澄清。"""
    options = build_direction_options("shortdrama", "短剧", "", limit=8)
    options_text = " ".join(options)

    assert "新手" in options_text or "从 0" in options_text, \
        f"应包含新手友好选项: {options}"
    assert "AI" in options_text or "动漫短剧" in options_text, \
        f"应包含 AI 动漫短剧选项: {options}"
    assert "真人短剧" in options_text, \
        f"应包含真人短剧选项: {options}"
    assert "标题" in options_text or "封面" in options_text, \
        f"应包含标题/封面优化选项: {options}"
    assert "系列" in options_text or "剧情线" in options_text, \
        f"应包含系列短剧选项: {options}"


def test_shortdrama_options_keyword_priority():
    """关键词命中应影响排序。"""
    # "真人短剧" 应让真人选项排更前
    options = build_direction_options("shortdrama", "我想做真人短剧", "", limit=6)
    assert "真人" in options[0], f"真人短剧输入应让真人选项排第一: {options}"

    # "系列短剧" 应让系列选项排更前
    options = build_direction_options("shortdrama", "我想做系列短剧", "", limit=6)
    assert "系列" in options[0], f"系列短剧输入应让系列选项排第一: {options}"

    # "AI 动漫短剧" 应让 AI 动漫选项排更前
    options = build_direction_options("shortdrama", "我想做 AI 动漫短剧", "", limit=6)
    assert "AI" in options[0] or "动漫" in options[0], \
        f"AI 动漫短剧输入应让 AI 动漫选项排第一: {options}"


def test_content_and_learning_default_count():
    """content / learning 也应默认返回 6 条。"""
    content_opts = build_direction_options("content", "内容", "")
    assert len(content_opts) == 6

    learning_opts = build_direction_options("learning", "学习", "")
    assert len(learning_opts) == 6


# ── 明确领域目标 → specific enough → close_success ────────────

def test_explicit_domain_goals_are_specific():
    """明确领域目标应被视为 specific enough。"""
    explicit_goals = [
        "动漫短剧",
        "AI动漫短剧",
        "AI 动漫短剧",
        "动画短剧",
        "真人短剧",
        "短剧脚本",
        "短剧剧本",
        "抖音剧情号",
        "短视频剧情号",
        "小红书图文",
        "公众号文章",
        "背单词计划",
    ]
    for goal in explicit_goals:
        assert is_specific_enough_answer(goal) is True, \
            f"'{goal}' 应被视为 specific enough"


def test_explicit_domain_goal_sentences_are_specific():
    """真实用户句式也应被视为 specific enough。"""
    cases = [
        "我想做动漫短剧",
        "我想做 AI 动漫短剧",
        "我想拍真人短剧",
        "我想写短剧脚本",
        "我想做短剧剧本",
        "我想做抖音剧情号",
        "我想做短视频剧情号",
        "我想做小红书图文",
        "我想写公众号文章",
        "我想做背单词计划",
    ]
    for text in cases:
        assert is_specific_enough_answer(text) is True, f"'{text}' 应被视为 specific enough"


def test_short_drama_alone_not_specific():
    """'短剧' 单独出现不应被视为 specific enough。"""
    assert is_specific_enough_answer("短剧") is False
    assert is_specific_enough_answer("微短剧") is False
    assert is_specific_enough_answer("竖屏短剧") is False


def test_short_drama_alone_is_partial():
    """'短剧' 单独出现应识别为 partial。"""
    assert detect_bucket("短剧", "") == "shortdrama"
    assert is_specific_enough_answer("短剧") is False
    assert is_partial_answer("我想做内容", "短剧") is True


# ── close_followup_node 集成测试（需要 API key） ──────────────

def test_close_partial_stops_for_direction_choice():
    """此测试需要 API key，仅在可用时运行。"""
    try:
        from graph.workflow import build_route_workflow
    except Exception:
        return

    app = build_route_workflow()
    final_state = app.invoke({
        "user_goal": "我想做内容",
        "followup_answer": "小红书",
    })

    assert final_state.get("close_result") == "close_partial"
    assert final_state.get("need_direction_choice") is True
    assert final_state.get("direction_options")
    assert len(final_state.get("direction_options", [])) >= 6
    assert final_state.get("route_result") is None
    assert final_state.get("current_stage") == "direction_choice_required"


def test_close_success_not_affected():
    """此测试需要 API key，仅在可用时运行。"""
    try:
        from graph.nodes import close_followup_node
    except Exception:
        return

    state = close_followup_node({
        "user_goal": "我想做内容",
        "followup_answer": "做一套小红书文案生成流程，能批量出标题、正文和封面文案",
    })

    assert state.get("close_result") == "close_success"
    assert state.get("need_direction_choice") is False
    assert state.get("effective_goal") == "做一套小红书文案生成流程，能批量出标题、正文和封面文案"


def test_close_failed_keeps_failed_result():
    """此测试需要 API key，仅在可用时运行。"""
    try:
        from graph.nodes import close_followup_node
    except Exception:
        return

    state = close_followup_node({
        "user_goal": "做项目",
        "followup_answer": "随便做点AI的",
    })

    assert state.get("close_result") == "close_failed"
    assert state.get("need_direction_choice") is False


def test_pure_generic_answer_goes_close_failed():
    """此测试需要 API key，仅在可用时运行。"""
    try:
        from graph.nodes import close_followup_node
    except Exception:
        return

    state = close_followup_node({
        "user_goal": "做项目",
        "followup_answer": "随便",
    })

    assert state.get("close_result") == "close_failed"
    assert state.get("need_direction_choice") is False


def test_generic_content_answer_goes_close_partial():
    """此测试需要 API key，仅在可用时运行。"""
    try:
        from graph.nodes import close_followup_node
    except Exception:
        return

    state = close_followup_node({
        "user_goal": "我想做内容",
        "followup_answer": "随便帮我做一个小红书内容创作流程",
    })

    assert state.get("close_result") == "close_partial"
    assert state.get("need_direction_choice") is True
    assert state.get("detected_bucket") == "content"
    assert state.get("direction_options")
    assert len(state.get("direction_options", [])) >= 6
    assert state.get("route_result") is None


def test_generic_shortdrama_answer_goes_close_partial():
    """此测试需要 API key，仅在可用时运行。"""
    try:
        from graph.nodes import close_followup_node
    except Exception:
        return

    state = close_followup_node({
        "user_goal": "我想做 AI 视频",
        "followup_answer": "你看着办，做一个 AI 视频生成流程",
    })

    assert state.get("close_result") == "close_partial"
    assert state.get("need_direction_choice") is True
    assert state.get("detected_bucket") == "shortdrama"
    assert state.get("direction_options")
    assert state.get("route_result") is None


# ── 初始任务分析补问判断 ──────────────────────────────────────

def test_clear_domain_goals_skip_followup():
    """明确领域目标不应触发补问。"""
    try:
        from graph.nodes import analyze_task_node
    except Exception:
        return

    should_not_followup = [
        "动漫短剧",
        "我想做动漫短剧",
        "AI 动漫短剧",
        "我想做 AI 动漫短剧",
        "真人短剧",
        "我想拍真人短剧",
        "短剧脚本",
        "我想写短剧脚本",
    ]
    for goal in should_not_followup:
        state = analyze_task_node({"user_goal": goal})
        assert state.get("need_followup") is False, \
            f"'{goal}' 不应触发补问，但 need_followup={state.get('need_followup')}"


def test_vague_shortdrama_still_triggers_followup():
    """泛化的'短剧'仍应触发补问。"""
    try:
        from graph.nodes import analyze_task_node
    except Exception:
        return

    should_followup = ["短剧", "我想做短剧"]
    for goal in should_followup:
        state = analyze_task_node({"user_goal": goal})
        assert state.get("need_followup") is True, \
            f"'{goal}' 应触发补问，但 need_followup={state.get('need_followup')}"


if __name__ == "__main__":
    test_detect_bucket()
    test_detect_bucket_shortdrama_variants()
    test_detect_bucket_content_variants()
    test_detect_bucket_learning_variants()
    test_direction_options_default_count()
    test_direction_options_limit_8()
    test_shortdrama_options_no_60s()
    test_shortdrama_options_are_beginner_friendly()
    test_shortdrama_options_keyword_priority()
    test_content_and_learning_default_count()
    test_explicit_domain_goals_are_specific()
    test_explicit_domain_goal_sentences_are_specific()
    test_short_drama_alone_not_specific()
    test_short_drama_alone_is_partial()
    test_close_partial_stops_for_direction_choice()
    test_close_success_not_affected()
    test_close_failed_keeps_failed_result()
    test_pure_generic_answer_goes_close_failed()
    test_generic_content_answer_goes_close_partial()
    test_generic_shortdrama_answer_goes_close_partial()
    test_clear_domain_goals_skip_followup()
    test_vague_shortdrama_still_triggers_followup()
    print("test_direction_choice.py: all tests passed")
