"""
Anti-assumption eval: 规则检查，验证输出文本是否把用户没说的信息写成确定事实。
不调用外部 API，纯本地正则匹配。

核心逻辑：按句子分割后逐句检查，只有违规词所在句子内有允许标记才放过。
"""

import re
import sys

# --- 模式：把未确认信息写成确定事实的表达 ---
BAD_PATTERNS = [
    (r"用户想做一集", "把'一集'写成用户已确定需求"),
    (r"用户想做.*30.*秒", "把时长30秒写成用户已确定需求"),
    (r"用户想做.*60.*秒", "把时长60秒写成用户已确定需求"),
    (r"用户想做.*2.*分钟", "把时长2分钟写成用户已确定需求"),
    (r"用户希望制作一条60秒", "把60秒写成用户已确定需求"),
    (r"用户希望制作.*30秒", "把30秒写成用户已确定需求"),
    (r"首集控制在", "把首集时长写成确定规则"),
    (r"必须控制在", "把时长写成强制要求"),
    (r"发布到抖音", "把平台写成用户已确定需求"),
    (r"发布到小红书", "把平台写成用户已确定需求"),
    (r"发布到B站", "把平台写成用户已确定需求"),
    (r"只保留\s*1\s*个主角", "把角色数量写成确定规则"),
    (r"只保留\s*1\s*个场景", "把场景数量写成确定规则"),
    (r"控制在\s*30\s*到\s*60\s*秒", "把时长写成确定规则"),
    (r"一条\s*30\s*到\s*60\s*秒", "把时长写成默认目标"),
]

# --- 上下文标记：只有在违规词所在句子内出现才有效 ---
ALLOWED_MARKERS = [
    "可选",
    "建议",
    "如果是新手",
    "可以选择",
    "待确认",
    "先确认",
    "需要确认",
    "由用户确认",
    "尚未明确",
    "试水",
]


def _split_sentences(text: str) -> list[str]:
    """按中文/英文句号、分号、换行分割句子。"""
    parts = re.split(r"[。；;\n]", text)
    return [p.strip() for p in parts if p.strip()]


def _sentence_has_allowed_marker(sentence: str) -> bool:
    """检查单个句子内是否包含允许标记。"""
    return any(marker in sentence for marker in ALLOWED_MARKERS)


def check_output(user_input: str, output: str) -> tuple[bool, str | None]:
    """检查输出是否把用户没说的信息写成确定事实。返回 (pass, reason)。"""
    sentences = _split_sentences(output)

    for sentence in sentences:
        for pattern, reason in BAD_PATTERNS:
            if re.search(pattern, sentence):
                if _sentence_has_allowed_marker(sentence):
                    continue
                return False, reason

    return True, None


# --- 测试用例 ---
TEST_CASES = [
    # === Bad samples ===
    {
        "user_input": "动漫短剧",
        "output": "用户想做一集 AI 动漫短剧（30秒-2分钟）。",
        "expected": "FAIL",
    },
    {
        "user_input": "动漫短剧",
        "output": "首集只保留 1 个主角、1 个场景、1 个冲突，控制在 30-60 秒。",
        "expected": "FAIL",
    },
    {
        "user_input": "动漫短剧",
        "output": "发布到抖音并追求完播率提升。",
        "expected": "FAIL",
    },
    {
        "user_input": "动漫短剧",
        "output": "用户想做 30 秒的 AI 动漫短剧，发布到小红书。",
        "expected": "FAIL",
    },
    # bad：前面有"建议"但坏 pattern 在另一个句子
    {
        "user_input": "动漫短剧",
        "output": "建议先确认风格。用户想做一集 30 秒 AI 动漫短剧。",
        "expected": "FAIL",
    },
    # bad：页面实际出现过的问题
    {
        "user_input": "动漫短剧",
        "output": "用户希望制作一条60秒的AI动漫短剧。",
        "expected": "FAIL",
    },
    # bad：固定时长作为默认目标
    {
        "user_input": "动漫短剧",
        "output": "目标产物：一条 30 到 60 秒短视频。",
        "expected": "FAIL",
    },
    # === Good samples ===
    {
        "user_input": "动漫短剧",
        "output": "用户想做动漫短剧，但尚未明确时长、平台和风格，第一步需要确认这些关键决策。",
        "expected": "PASS",
    },
    {
        "user_input": "动漫短剧",
        "output": "如果是新手，可以选择 30-60 秒试水短片，或 1-2 分钟完整短剧。",
        "expected": "PASS",
    },
    {
        "user_input": "动漫短剧",
        "output": "可选发布平台包括抖音、视频号或 B站，具体平台需要用户确认。",
        "expected": "PASS",
    },
    {
        "user_input": "动漫短剧",
        "output": "建议先确认短剧规格：时长、集数、风格和制作方式。",
        "expected": "PASS",
    },
    {
        "user_input": "动漫短剧",
        "output": "待确认：时长范围、发布平台、角色数量、场景数量。",
        "expected": "PASS",
    },
    # good：试水建议 + 由用户确认
    {
        "user_input": "动漫短剧",
        "output": "如果是新手，可以选择 30-60 秒试水短片，但具体时长需要由用户确认。",
        "expected": "PASS",
    },
    # good：建议形式
    {
        "user_input": "动漫短剧",
        "output": "新手建议先做一个短版本试水，例如 30-60 秒短片，确认画风和角色后再扩展。",
        "expected": "PASS",
    },
    # good：可选建议提到首集
    {
        "user_input": "动漫短剧",
        "output": "建议首集控制复杂度，但具体规格需要用户确认。",
        "expected": "PASS",
    },
]


def main():
    print("Anti-assumption eval")
    total = len(TEST_CASES)
    passed = 0
    failed = 0

    for i, case in enumerate(TEST_CASES, 1):
        ok, reason = check_output(case["user_input"], case["output"])
        actual = "PASS" if ok else "FAIL"

        if actual == case["expected"]:
            passed += 1
            status = "OK"
        else:
            failed += 1
            status = "MISMATCH"

        if status != "OK":
            print(f"  [{status}] case {i}: expected={case['expected']} got={actual}")
            if reason:
                print(f"    reason: {reason}")
            print(f"    input:  {case['user_input']}")
            print(f"    output: {case['output']}")

    print(f"total: {total}")
    print(f"passed: {passed}")
    print(f"failed: {failed}")
    print(f"Result: {'PASS' if failed == 0 else 'FAIL'}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
