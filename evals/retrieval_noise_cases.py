RETRIEVAL_NOISE_CASES = [
    {
        "case_id": "direct_learning_plan_01",
        "bucket": "learning",
        "input_goal": "用 AI 做一个 14 天英语学习计划，重点提升阅读和单词复习",
        "case_type": "direct",
        "notes": "学习辅助直通目标，检查是否被短剧固定词带偏。",
    },
    {
        "case_id": "direct_content_xiaohongshu_01",
        "bucket": "content",
        "input_goal": "用 AI 做小红书图文内容创作，主题是新手如何开始用 AI 提高学习效率",
        "case_type": "direct",
        "notes": "内容创作直通目标，检查是否误召回短剧片段。",
    },
    {
        "case_id": "direct_shortdrama_60s_01",
        "bucket": "shortdrama",
        "input_goal": "做一集 60 秒 AI 动漫短剧，主角是高中生，风格热血，想发到短视频平台",
        "case_type": "direct",
        "notes": "短剧直通目标，检查本桶命中是否显著更稳。",
    },
    {
        "case_id": "fallback_learning_01",
        "bucket": "learning",
        "input_goal": "AI 学习辅助",
        "case_type": "fallback",
        "notes": "学习桶 close_failed 保底目标，检查桶级目标检索纯度。",
    },
    {
        "case_id": "fallback_content_01",
        "bucket": "content",
        "input_goal": "AI 内容创作",
        "case_type": "fallback",
        "notes": "内容桶 close_failed 保底目标，检查是否被短剧固定词污染。",
    },
    {
        "case_id": "fallback_shortdrama_01",
        "bucket": "shortdrama",
        "input_goal": "AI 动漫短剧",
        "case_type": "fallback",
        "notes": "短剧桶 close_failed 保底目标，作为短剧命中对照。",
    },
]
