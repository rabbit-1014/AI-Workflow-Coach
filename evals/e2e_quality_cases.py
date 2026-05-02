E2E_QUALITY_CASES = [
    {
        "case_id": "learning_direct_01",
        "bucket": "learning",
        "case_type": "direct_route",
        "input": {
            "user_goal": "用 AI 做一个 14 天英语学习计划，重点提升阅读和单词复习",
        },
    },
    {
        "case_id": "learning_close_success_01",
        "bucket": "learning",
        "case_type": "close_success",
        "input": {
            "user_goal": "我想做个学习工具",
            "followup_answer": "做一个 AI 背单词工具，能生成例句、测验和错词复习",
        },
    },
    {
        "case_id": "learning_blockage_01",
        "bucket": "learning",
        "case_type": "blockage",
        "input": {
            "user_goal": "做一个 AI 学习打卡助手",
            "selected_step": "生成每日反馈",
            "blockage_text": "AI 给的反馈都像鸡汤，不知道怎么改进学习",
        },
    },
    {
        "case_id": "content_direct_01",
        "bucket": "content",
        "case_type": "direct_route",
        "input": {
            "user_goal": "用 AI 做小红书图文内容创作，主题是新手如何开始用 AI 提高学习效率",
        },
    },
    {
        "case_id": "content_close_success_01",
        "bucket": "content",
        "case_type": "close_success",
        "input": {
            "user_goal": "我想做内容",
            "followup_answer": "做一套小红书文案生成流程，能批量出标题、正文和封面文案",
        },
    },
    {
        "case_id": "content_blockage_01",
        "bucket": "content",
        "case_type": "blockage",
        "input": {
            "user_goal": "用 AI 做小红书图文内容创作",
            "selected_step": "制作封面和标题",
            "blockage_text": "封面看起来还行，但点击率很低",
        },
    },
    {
        "case_id": "shortdrama_direct_01",
        "bucket": "shortdrama",
        "case_type": "direct_route",
        "input": {
            "user_goal": "做一集 60 秒 AI 动漫短剧，主角是高中生，风格热血，想发到短视频平台",
        },
    },
    {
        "case_id": "shortdrama_close_success_01",
        "bucket": "shortdrama",
        "case_type": "close_success",
        "input": {
            "user_goal": "我想做 AI 视频",
            "followup_answer": "做一个 30 秒漫剧首集，需要角色设定、分镜脚本和首集成片流程",
        },
    },
    {
        "case_id": "shortdrama_blockage_01",
        "bucket": "shortdrama",
        "case_type": "blockage",
        "input": {
            "user_goal": "AI 动漫短剧",
            "selected_step": "生成角色视觉",
            "blockage_text": "角色每张图都不像同一个人，后面没法做分镜",
        },
    },
]
