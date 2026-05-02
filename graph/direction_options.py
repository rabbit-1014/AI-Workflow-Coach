MAIN_BUCKET_KEYWORDS = {
    "learning": [
        "学习", "学习计划", "学习工具", "背单词", "单词", "词汇",
        "错题", "错题本", "复习", "刷题", "题库", "打卡", "学习打卡",
        "考试", "备考", "考研", "四六级", "雅思", "托福", "高考", "期末",
        "课程", "课堂笔记", "知识点", "知识卡片", "闪卡", "anki", "Anki",
        "笔记整理", "论文阅读", "文献阅读", "长文阅读", "知识问答",
        "测验", "练习", "记忆", "每日任务", "薄弱点",
    ],
    "content": [
        "内容", "内容创作", "自媒体", "账号运营", "内容矩阵",
        "小红书", "公众号", "知乎", "B站", "哔哩哔哩", "抖音", "快手",
        "视频号", "微博", "多平台分发",
        "文案", "图文", "笔记", "标题", "封面", "封面文案", "正文",
        "选题", "大纲", "脚本", "口播稿", "短视频脚本",
        "种草文案", "带货文案", "产品文案", "爆款标题",
        "评论区", "开头钩子", "结尾引导", "发布复盘",
        "文章", "长文", "短文", "播客", "直播切片", "二创",
        "涨粉", "点击率", "收藏", "互动", "转化", "热点", "改写", "润色", "排版",
    ],
    "shortdrama": [
        "AI短剧", "短剧", "动漫短剧", "漫剧", "AI漫剧", "剧情短视频",
        "AI视频", "视频生成", "分镜", "镜头", "角色", "角色设定",
        "角色一致性", "角色图", "参考图", "画面提示词", "镜头提示词",
        "成片", "剪辑", "配音", "字幕", "旁白", "台词",
        "世界观", "剧本", "剧情", "预告片",
        "可灵", "即梦", "Runway", "Midjourney",
        "画面", "动作", "场景", "转场", "竖屏", "第一集", "连续剧", "故事", "冲突", "人设",
    ],
}


DIRECTION_OPTION_POOL = [
    {
        "bucket": "learning",
        "option": "做 7 天英语学习计划，重点是阅读和单词复习",
        "keywords": ["英语", "学习计划", "阅读", "单词", "复习", "7天"],
        "priority": 10,
    },
    {
        "bucket": "learning",
        "option": "做 AI 背单词工具，能生成例句、测验和错词复习",
        "keywords": ["背单词", "单词", "词汇", "例句", "测验", "错词"],
        "priority": 10,
    },
    {
        "bucket": "learning",
        "option": "做 AI 学习打卡助手，能根据记录生成每日反馈",
        "keywords": ["打卡", "学习打卡", "每日反馈", "记录", "复盘"],
        "priority": 9,
    },
    {
        "bucket": "learning",
        "option": "做错题复盘助手，能归纳错因、生成同类题和复习计划",
        "keywords": ["错题", "错题本", "错因", "同类题", "复习计划"],
        "priority": 9,
    },
    {
        "bucket": "learning",
        "option": "做课堂笔记整理流程，把课程内容整理成知识点、题目和复习卡片",
        "keywords": ["课堂笔记", "笔记整理", "课程", "知识点", "复习卡片"],
        "priority": 8,
    },
    {
        "bucket": "learning",
        "option": "做考试冲刺计划，按剩余时间拆分每日学习任务",
        "keywords": ["考试", "备考", "冲刺", "每日任务", "计划"],
        "priority": 8,
    },
    {
        "bucket": "learning",
        "option": "做论文 / 长文阅读辅助流程，包含摘要、术语解释和问题清单",
        "keywords": ["论文", "文献", "长文阅读", "摘要", "术语", "问题清单"],
        "priority": 8,
    },
    {
        "bucket": "learning",
        "option": "做面试学习计划，围绕岗位要求拆知识点、练习题和复盘表",
        "keywords": ["面试", "岗位", "知识点", "练习题", "复盘"],
        "priority": 7,
    },
    {
        "bucket": "learning",
        "option": "做知识点问答助手，围绕一个主题生成解释、例题和自测题",
        "keywords": ["知识点", "问答", "解释", "例题", "自测"],
        "priority": 7,
    },
    {
        "bucket": "learning",
        "option": "做编程学习练习流程，包含知识点、代码练习、错题复盘和项目任务",
        "keywords": ["编程", "代码", "练习", "项目任务", "错题复盘"],
        "priority": 7,
    },
    {
        "bucket": "content",
        "option": "做小红书图文内容创作，包含选题、正文、封面和发布复盘",
        "keywords": ["小红书", "图文", "笔记", "正文", "封面", "发布复盘"],
        "priority": 10,
    },
    {
        "bucket": "content",
        "option": "做一套小红书文案生成流程，能批量出标题、正文和封面文案",
        "keywords": ["小红书", "文案", "标题", "正文", "封面文案", "批量"],
        "priority": 10,
    },
    {
        "bucket": "content",
        "option": "做小红书标题与封面优化流程，提高点击吸引力",
        "keywords": ["小红书", "标题", "封面", "点击率", "吸引力"],
        "priority": 9,
    },
    {
        "bucket": "content",
        "option": "做公众号文章创作流程，包含选题、大纲、正文和标题优化",
        "keywords": ["公众号", "文章", "选题", "大纲", "正文", "标题"],
        "priority": 9,
    },
    {
        "bucket": "content",
        "option": "做公众号选题库和标题生成流程",
        "keywords": ["公众号", "选题库", "标题", "文章"],
        "priority": 8,
    },
    {
        "bucket": "content",
        "option": "做短视频脚本文案流程，包含选题、脚本、开头钩子和发布复盘",
        "keywords": ["短视频脚本", "脚本", "选题", "开头钩子", "发布复盘"],
        "priority": 8,
    },
    {
        "bucket": "content",
        "option": "做 B 站视频选题与脚本流程，包含开头、结构、案例和结尾引导",
        "keywords": ["B站", "哔哩哔哩", "视频选题", "脚本", "结构", "结尾引导"],
        "priority": 8,
    },
    {
        "bucket": "content",
        "option": "做播客选题与脚本流程，包含主题定位、提纲和口播稿",
        "keywords": ["播客", "选题", "脚本", "提纲", "口播稿"],
        "priority": 7,
    },
    {
        "bucket": "content",
        "option": "做直播切片二创流程，包含素材筛选、标题包装和短视频改写",
        "keywords": ["直播切片", "二创", "素材筛选", "标题包装", "短视频改写"],
        "priority": 7,
    },
    {
        "bucket": "content",
        "option": "做知识类内容矩阵流程，把一个主题拆成多平台内容",
        "keywords": ["知识类", "内容矩阵", "多平台", "分发", "主题"],
        "priority": 7,
    },
    {
        "bucket": "content",
        "option": "做产品种草文案流程，包含卖点提炼、用户痛点和平台化表达",
        "keywords": ["种草", "带货", "产品文案", "卖点", "痛点"],
        "priority": 7,
    },
    {
        "bucket": "content",
        "option": "做长文改写成多平台内容流程，包含公众号、小红书和短视频脚本",
        "keywords": ["长文", "改写", "公众号", "小红书", "短视频脚本"],
        "priority": 7,
    },
    {
        "bucket": "shortdrama",
        "option": "做 60 秒 AI 动漫短剧，包含角色设定、分镜、成片和发布",
        "keywords": ["60秒", "AI动漫短剧", "短剧", "角色设定", "分镜", "成片"],
        "priority": 10,
    },
    {
        "bucket": "shortdrama",
        "option": "做 30 秒漫剧首集流程，重点是角色一致性和镜头生成",
        "keywords": ["30秒", "漫剧", "首集", "角色一致性", "镜头"],
        "priority": 10,
    },
    {
        "bucket": "shortdrama",
        "option": "做 AI 短剧角色一致性流程，包含角色卡、参考图和镜头提示词",
        "keywords": ["角色一致性", "角色卡", "参考图", "镜头提示词", "角色图"],
        "priority": 9,
    },
    {
        "bucket": "shortdrama",
        "option": "做短视频剧情分镜流程，包含脚本、画面、配音和剪辑",
        "keywords": ["分镜", "剧情", "脚本", "画面", "配音", "剪辑"],
        "priority": 9,
    },
    {
        "bucket": "shortdrama",
        "option": "做 AI 视频脚本转分镜流程，把剧情拆成可生成镜头",
        "keywords": ["AI视频", "脚本转分镜", "剧情", "镜头", "视频生成"],
        "priority": 8,
    },
    {
        "bucket": "shortdrama",
        "option": "做 AI 配音与字幕流程，包含台词整理、配音生成和剪辑同步",
        "keywords": ["配音", "字幕", "台词", "旁白", "剪辑同步"],
        "priority": 8,
    },
    {
        "bucket": "shortdrama",
        "option": "做短剧封面与标题包装流程，用于提升点击吸引力",
        "keywords": ["短剧", "封面", "标题", "包装", "点击"],
        "priority": 7,
    },
    {
        "bucket": "shortdrama",
        "option": "做系列短剧世界观和角色设定流程，适合多集内容",
        "keywords": ["系列", "世界观", "角色设定", "多集", "人设"],
        "priority": 7,
    },
    {
        "bucket": "shortdrama",
        "option": "做 AI 漫剧预告片流程，包含高光片段、旁白和节奏剪辑",
        "keywords": ["漫剧", "预告片", "高光", "旁白", "节奏剪辑"],
        "priority": 7,
    },
    {
        "bucket": "shortdrama",
        "option": "做可灵 / 即梦视频生成流程，包含提示词、镜头生成和素材筛选",
        "keywords": ["可灵", "即梦", "视频生成", "提示词", "镜头", "素材筛选"],
        "priority": 7,
    },
    {
        "bucket": "shortdrama",
        "option": "做角色图到分镜视频流程，包含角色图、动作镜头和场景变化",
        "keywords": ["角色图", "分镜视频", "动作", "镜头", "场景"],
        "priority": 7,
    },
    {
        "bucket": "shortdrama",
        "option": "做短剧首集脚本到成片流程，包含剧本、分镜、配音、剪辑和发布",
        "keywords": ["短剧", "首集", "剧本", "分镜", "配音", "剪辑", "发布"],
        "priority": 7,
    },
]


GENERIC_FAILED_ANSWERS = [
    "随便",
    "都行",
    "不知道",
    "没想好",
    "你看着办",
    "做点东西",
    "先给个方向",
    "无所谓",
]

SUCCESS_ACTION_TERMS = [
    "流程", "工具", "生成", "计划", "复盘", "标题", "正文", "封面",
    "例句", "测验", "错词", "分镜", "成片", "配音", "剪辑", "发布", "反馈",
]

SHORTDRAMA_TIEBREAK_TERMS = [
    "分镜", "镜头", "角色", "成片", "可灵", "即梦", "动漫", "漫剧", "角色一致性",
]

CONTENT_TIEBREAK_TERMS = [
    "小红书", "公众号", "文案", "口播稿", "账号运营", "标题", "图文", "文章",
]


def _normalize_text(text: str) -> str:
    return "".join((text or "").lower().split())


def _contains_keyword(text: str, keyword: str) -> bool:
    return _normalize_text(keyword) in _normalize_text(text)


def detect_bucket(user_goal: str, followup_answer: str) -> str:
    text = f"{user_goal} {followup_answer}"
    normalized_text = _normalize_text(text)
    if not normalized_text:
        return ""

    scores = {}
    for bucket, keywords in MAIN_BUCKET_KEYWORDS.items():
        score = sum(1 for keyword in keywords if _contains_keyword(text, keyword))
        if score:
            scores[bucket] = score

    if not scores:
        return ""

    if scores.get("content") and scores.get("shortdrama"):
        if any(_contains_keyword(text, term) for term in SHORTDRAMA_TIEBREAK_TERMS):
            return "shortdrama"
        if any(_contains_keyword(text, term) for term in CONTENT_TIEBREAK_TERMS):
            return "content"

    priority = ["shortdrama", "learning", "content"]
    return max(scores, key=lambda bucket: (scores[bucket], -priority.index(bucket)))


def build_direction_options(
    bucket: str,
    user_goal: str,
    followup_answer: str,
    limit: int = 3,
) -> list[str]:
    candidate_options = [
        item for item in DIRECTION_OPTION_POOL if item["bucket"] == bucket
    ]
    if not candidate_options:
        return []

    text = f"{user_goal} {followup_answer}"
    scored_options = []
    for item in candidate_options:
        hit_count = sum(1 for keyword in item["keywords"] if _contains_keyword(text, keyword))
        scored_options.append((hit_count, item["priority"], item["option"]))

    if not any(hit_count for hit_count, _, _ in scored_options):
        scored_options = [
            (0, item["priority"], item["option"])
            for item in candidate_options
        ]

    scored_options.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [option for _, _, option in scored_options[:limit]]


def is_generic_failed_answer(followup_answer: str) -> bool:
    normalized_answer = _normalize_text(followup_answer)
    if not normalized_answer:
        return True
    return any(_normalize_text(answer) in normalized_answer for answer in GENERIC_FAILED_ANSWERS)


def is_specific_enough_answer(followup_answer: str) -> bool:
    normalized_answer = _normalize_text(followup_answer)
    if len(normalized_answer) < 14:
        return False
    return any(_contains_keyword(followup_answer, term) for term in SUCCESS_ACTION_TERMS)


def is_partial_answer(user_goal: str, followup_answer: str) -> bool:
    if is_generic_failed_answer(followup_answer):
        return False
    if is_specific_enough_answer(followup_answer):
        return False
    return bool(detect_bucket(user_goal, followup_answer))
