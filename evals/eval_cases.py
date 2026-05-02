EVAL_CASES = [
    {
        "case_id": "direct_route_01",
        "case_type": "direct_route",
        "input": {
            "user_goal": "AI 动漫短剧",
        },
        "expected": {
            "need_followup": False,
            "has_route_result": True,
        },
    },
    {
        "case_id": "direct_route_02",
        "case_type": "direct_route",
        "input": {
            "user_goal": "用 AI 做小红书图文内容创作",
        },
        "expected": {
            "need_followup": False,
            "has_route_result": True,
        },
    },
    {
        "case_id": "followup_needed_01",
        "case_type": "followup_needed",
        "input": {
            "user_goal": "学AI",
        },
        "expected": {
            "need_followup": True,
            "has_followup_question": True,
            "has_route_result": False,
        },
    },
    {
        "case_id": "followup_needed_02",
        "case_type": "followup_needed",
        "input": {
            "user_goal": "做项目",
        },
        "expected": {
            "need_followup": True,
            "has_followup_question": True,
            "has_route_result": False,
        },
    },
    {
        "case_id": "followup_needed_03",
        "case_type": "followup_needed",
        "input": {
            "user_goal": "用AI做点东西",
        },
        "expected": {
            "need_followup": True,
            "has_followup_question": True,
            "has_route_result": False,
        },
    },
    {
        "case_id": "close_success_01",
        "case_type": "close_success",
        "input": {
            "user_goal": "学AI",
            "followup_answer": "我想做 AI 动漫短剧",
        },
        "expected": {
            "close_result": "close_success",
            "has_effective_goal": True,
            "effective_goal": "我想做 AI 动漫短剧",
            "has_route_result": True,
        },
    },
    {
        "case_id": "close_failed_01",
        "case_type": "close_failed",
        "input": {
            "user_goal": "做项目",
            "followup_answer": "随便做点AI的",
        },
        "expected": {
            "close_result": "close_failed",
            "has_effective_goal": True,
            "has_route_result": True,
        },
    },
    {
        "case_id": "fallback_learning_01",
        "case_type": "close_failed",
        "input": {
            "user_goal": "学AI",
            "followup_answer": "都行",
        },
        "expected": {
            "close_result": "close_failed",
            "has_effective_goal": True,
            "effective_goal": "AI 学习辅助",
            "has_route_result": True,
        },
    },
    {
        "case_id": "fallback_anime_01",
        "case_type": "close_failed",
        "input": {
            "user_goal": "AI 动漫短剧",
            "followup_answer": "不知道",
        },
        "expected": {
            "close_result": "close_failed",
            "has_effective_goal": True,
            "effective_goal": "AI 动漫短剧",
            "has_route_result": True,
        },
    },
    {
        "case_id": "fallback_content_01",
        "case_type": "close_failed",
        "input": {
            "user_goal": "用AI做点东西",
            "followup_answer": "先随便试试",
        },
        "expected": {
            "close_result": "close_failed",
            "has_effective_goal": True,
            "effective_goal": "AI 内容创作",
            "has_route_result": True,
        },
    },
    {
        "case_id": "generic_answer_01",
        "case_type": "close_failed",
        "input": {
            "user_goal": "做项目",
            "followup_answer": "做点有意思的",
        },
        "expected": {
            "close_result": "close_failed",
            "has_effective_goal": True,
            "effective_goal": "AI 内容创作",
            "has_route_result": True,
        },
    },
    {
        "case_id": "generic_answer_02",
        "case_type": "close_failed",
        "input": {
            "user_goal": "学AI",
            "followup_answer": "试试看",
        },
        "expected": {
            "close_result": "close_failed",
            "has_effective_goal": True,
            "effective_goal": "AI 学习辅助",
            "has_route_result": True,
        },
    },
    {
        "case_id": "generic_answer_03",
        "case_type": "close_failed",
        "input": {
            "user_goal": "用AI做点东西",
            "followup_answer": "先来一个",
        },
        "expected": {
            "close_result": "close_failed",
            "has_effective_goal": True,
            "effective_goal": "AI 内容创作",
            "has_route_result": True,
        },
    },
    {
        "case_id": "generic_answer_04",
        "case_type": "close_failed",
        "input": {
            "user_goal": "AI 短剧项目",
            "followup_answer": "都可以",
        },
        "expected": {
            "close_result": "close_failed",
            "has_effective_goal": True,
            "effective_goal": "AI 动漫短剧",
            "has_route_result": True,
        },
    },
    {
        "case_id": "close_success_boundary_01",
        "case_type": "close_success",
        "input": {
            "user_goal": "学AI",
            "followup_answer": "我想做一个帮助我背单词的AI工具",
        },
        "expected": {
            "close_result": "close_success",
            "has_effective_goal": True,
            "effective_goal": "我想做一个帮助我背单词的AI工具",
            "has_route_result": True,
        },
    },
    {
        "case_id": "close_success_boundary_02",
        "case_type": "close_success",
        "input": {
            "user_goal": "做项目",
            "followup_answer": "我想做一个AI学习打卡助手",
        },
        "expected": {
            "close_result": "close_success",
            "has_effective_goal": True,
            "effective_goal": "我想做一个AI学习打卡助手",
            "has_route_result": True,
        },
    },
    {
        "case_id": "close_success_boundary_03",
        "case_type": "close_success",
        "input": {
            "user_goal": "用AI做点东西",
            "followup_answer": "做短视频脚本生成器",
        },
        "expected": {
            "close_result": "close_success",
            "has_effective_goal": True,
            "effective_goal": "做短视频脚本生成器",
            "has_route_result": True,
        },
    },
    {
        "case_id": "blockage_01",
        "case_type": "blockage",
        "input": {
            "user_goal": "AI 动漫短剧",
            "selected_step": "生成角色图",
            "blockage_text": "角色图不稳定",
        },
        "expected": {
            "has_blockage_result": True,
        },
    },
]
