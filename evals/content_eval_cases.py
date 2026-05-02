CONTENT_EVAL_CASES = [
    # A. 学习辅助
    {
        "case_id": "learning_direct_01",
        "case_type": "direct_route",
        "input": {
            "user_goal": "用 AI 做一个 14 天英语学习计划，重点提升阅读和单词复习",
        },
        "why_selected": "学习辅助直通场景，检查路线是否覆盖目标诊断、计划、练习、反馈和复盘。",
        "notes": "应避免只给时间表，需有练习和验收标准。",
    },
    {
        "case_id": "learning_close_success_01",
        "case_type": "close_success",
        "input": {
            "user_goal": "我想做个学习工具",
            "followup_answer": "做一个 AI 背单词工具，能生成例句、测验和错词复习",
        },
        "why_selected": "补问后收口到明确学习工具，检查路线是否围绕背词闭环而不是泛学习计划。",
    },
    {
        "case_id": "learning_close_failed_01",
        "case_type": "close_failed",
        "input": {
            "user_goal": "我想学 AI",
            "followup_answer": "都行，你看着安排",
        },
        "why_selected": "学习类 fallback 场景，检查保底路线是否能给出可执行的最小学习闭环。",
    },
    {
        "case_id": "learning_blockage_01",
        "case_type": "blockage",
        "input": {
            "user_goal": "做一个 AI 学习打卡助手",
            "selected_step": "生成每日反馈",
            "blockage_text": "AI 给的反馈都像鸡汤，不知道怎么改进学习",
        },
        "why_selected": "学习反馈典型卡点，检查建议是否能把反馈拆成事实、问题和下一步练习。",
    },

    # B. 内容创作
    {
        "case_id": "content_direct_01",
        "case_type": "direct_route",
        "input": {
            "user_goal": "用 AI 做小红书图文内容创作，主题是新手如何开始用 AI 提高学习效率",
        },
        "why_selected": "内容创作直通场景，检查路线是否覆盖选题、草稿、封面包装、发布和复盘。",
    },
    {
        "case_id": "content_close_success_01",
        "case_type": "close_success",
        "input": {
            "user_goal": "我想做内容",
            "followup_answer": "做一套小红书文案生成流程，能批量出标题、正文和封面文案",
        },
        "why_selected": "补问后收口到内容创作流程，检查路线是否能从泛内容变成可执行生产链路。",
    },
    {
        "case_id": "content_close_failed_01",
        "case_type": "close_failed",
        "input": {
            "user_goal": "用 AI 做自媒体",
            "followup_answer": "随便，能发就行",
        },
        "why_selected": "内容创作 fallback 场景，检查保底方向是否不过度发散，并能形成单篇发布闭环。",
    },
    {
        "case_id": "content_blockage_01",
        "case_type": "blockage",
        "input": {
            "user_goal": "用 AI 做小红书图文内容创作",
            "selected_step": "制作封面和标题",
            "blockage_text": "封面看起来还行，但点击率很低",
        },
        "why_selected": "内容包装典型卡点，检查建议是否具体到标题收益点、视觉层级和对比测试。",
    },

    # C. 动漫短剧 / 漫剧 / 短视频创作
    {
        "case_id": "shortdrama_direct_01",
        "case_type": "direct_route",
        "input": {
            "user_goal": "做一集 60 秒 AI 动漫短剧，主角是高中生，风格热血，想发到短视频平台",
        },
        "why_selected": "短剧直通核心场景，检查路线是否覆盖设定、角色一致性、分镜、生成剪辑和发布验证。",
    },
    {
        "case_id": "shortdrama_close_success_01",
        "case_type": "close_success",
        "input": {
            "user_goal": "我想做 AI 视频",
            "followup_answer": "做一个 30 秒漫剧首集，需要角色设定、分镜脚本和首集成片流程",
        },
        "why_selected": "补问后收口到漫剧首集，检查路线是否保留短剧制作的阶段感和中间产物。",
    },
    {
        "case_id": "shortdrama_close_failed_01",
        "case_type": "close_failed",
        "input": {
            "user_goal": "AI 短剧项目",
            "followup_answer": "都可以，先给我一个方向",
        },
        "why_selected": "短剧 fallback 场景，检查在补充信息不足时是否仍能给出最小首集路线。",
    },
    {
        "case_id": "shortdrama_blockage_01",
        "case_type": "blockage",
        "input": {
            "user_goal": "AI 动漫短剧",
            "selected_step": "生成角色视觉",
            "blockage_text": "角色每张图都不像同一个人，后面没法做分镜",
        },
        "why_selected": "角色一致性核心卡点，检查建议是否能落到角色锁定卡、参考图和一致性验收。",
    },

]
