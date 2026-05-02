from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from content_eval_cases import CONTENT_EVAL_CASES
from schemas import BlockageOutput, RouteOutput, RouteStep


OUTPUT_PATH = Path(__file__).resolve().parent / "content_eval_outputs.md"


def _goal_kind(goal: str) -> str:
    if "动漫" in goal or "短剧" in goal or "漫剧" in goal:
        return "anime"
    if "小红书" in goal or "图文" in goal or "内容创作" in goal or "自媒体" in goal:
        return "content"
    if "背单词" in goal or "单词" in goal:
        return "vocabulary_tool"
    if "打卡" in goal:
        return "checkin_tool"
    if "学习" in goal:
        return "learning"
    return "general"


def _route_steps_for_goal(goal: str) -> list[RouteStep]:
    kind = _goal_kind(goal)

    if kind == "anime":
        raw_steps = [
            ("锁定短剧设定", "确定主角、题材、单集冲突和平台目标", "ChatGPT / 通义千问", "生成 3 个适合 60 秒 AI 动漫短剧的主角与冲突设定", "主角设定和首集冲突", "一个主角、一个冲突、一个情绪钩子清楚"),
            ("生成角色视觉", "把主角转成可复用的形象规范", "即梦 / Midjourney", "根据主角设定生成正面半身、全身和表情参考图", "角色参考图和提示词模板", "连续生成 3 张图仍能认出同一角色"),
            ("制作首集分镜", "把剧情拆成可生成的短镜头", "ChatGPT", "把第 1 集拆成 6 个镜头，每个镜头含画面、动作、台词和时长", "分镜脚本", "每个镜头只表达一个主要动作"),
            ("生成并剪辑首版", "把镜头素材剪成能看懂的首集", "可灵 / 剪映", "按分镜生成 3 到 5 秒镜头并剪成竖屏成片", "首集成片", "静音播放也能看懂主角、冲突和结果"),
            ("发布验证记录", "发布首集并留下可复盘的原始观察", "短视频平台数据面板 / 表格", "发布后填写记录模板：标题｜封面关键词｜发布时间｜曝光[用户填写]｜完播率[用户填写或未开放]｜互动观察｜评论关键词", "首集发布记录表", "至少填完标题、封面、发布时间和 2 个用户可见指标或观察项"),
        ]
    elif kind == "content":
        raw_steps = [
            ("确定选题和受众", "找到一个能发布的具体内容角度", "ChatGPT / 通义千问", "围绕新手用 AI 提高学习效率生成 10 个小红书选题", "选题清单", "至少 3 个选题有明确受众和痛点"),
            ("生成图文草稿", "产出一篇可编辑的小红书笔记", "ChatGPT", "按痛点、步骤、避坑、总结结构写一篇笔记", "图文文案草稿", "标题、正文、标签和结尾引导齐全"),
            ("制作封面包装", "生成首图标题和视觉层级", "Canva / 即梦", "为笔记设计 3 个封面标题和版式方向", "封面方案", "手机列表尺寸下能看清主题和收益"),
            ("发布并复盘", "记录用户实际看到的数据并决定下一篇怎么改", "小红书数据面板 / 表格", "发布后填写记录模板：标题｜封面文案｜发布时间｜曝光[用户填写]｜点击/阅读[用户填写]｜收藏[用户填写]｜评论关键词｜下一篇假设", "发布复盘表", "下一篇选题或标题能引用用户填写的数据或评论观察"),
        ]
    elif kind == "vocabulary_tool":
        raw_steps = [
            ("定义背词场景", "明确用户、词库范围、每日任务和最小闭环", "ChatGPT", "设计一个面向考研英语的 AI 背单词工具 MVP，限制为当天能搭建的版本", "功能范围和用户路径", "只保留查词、例句、测验、错词复习 4 个核心动作"),
            ("设计词卡字段", "让每个词能被学习、测验、记录和复习", "表格 / Notion", "设计字段：单词｜释义｜AI例句｜助记｜测验题｜答题结果｜掌握状态｜下次复习日期", "词卡结构和空白模板", "每张卡片能支持一次学习、一次测验和一次复习判断"),
            ("生成首批词卡", "用 AI 生成可直接测试的学习材料", "ChatGPT", "为 10 个考研英语单词生成释义、短例句、助记和 1 道选择题，答案单独列出", "首批词卡数据", "至少 10 张词卡字段完整，且题目能直接复制到原型或表格"),
            ("设计答题反馈", "让用户答错后获得具体错因而不是泛泛鼓励", "ChatGPT", "根据答题记录：单词、用户答案、正确答案、例句，输出错因、记忆提示和下一次练习", "反馈模板", "反馈能指出具体混淆点，并给出一个下一次练习动作"),
            ("设置错词复习", "跑通学习到复习的闭环", "Anki / 表格", "根据答错记录生成第二天复习清单，并标记复习日期和复习方式", "错词复习表", "第二天能看到需要复习的词、错因和复习动作"),
            ("做首轮可用性检查", "确认背词工具真的能被连续使用", "表格 / ChatGPT", "填写试用记录模板：日期｜学习词数｜答错词｜卡住原因｜明日调整", "试用记录", "能基于用户填写记录调整词量、题型或复习间隔"),
        ]
    elif kind == "checkin_tool":
        raw_steps = [
            ("定义打卡目标", "明确学习打卡助手跟踪什么、不给什么", "ChatGPT", "设计一个 AI 学习打卡助手的 MVP 功能，包含目标、记录、反馈、复盘边界", "功能清单", "目标、记录、提醒、反馈、复盘边界清晰"),
            ("搭建记录表", "让用户每天能低成本记录真实学习事实", "Notion / 飞书表格", "建立字段：日期｜任务｜计划时长｜实际时长｜完成情况｜错题/卡点｜明日动作", "打卡表", "用户 1 分钟内能完成一次记录，并留下可被 AI 引用的事实"),
            ("生成每日反馈", "根据记录给出具体改进建议", "ChatGPT", "根据当天学习记录输出：事实复述、主要问题、明日 1 个调整动作", "反馈模板", "反馈引用当天记录，不是泛泛鼓励"),
            ("处理低质量输入", "避免用户只写已完成导致反馈空泛", "ChatGPT / 表格", "当记录缺字段时，自动追问：今天做了什么、哪里错了、花了多久、明天要改什么", "补充输入模板", "用户补齐至少 3 个事实字段后再生成反馈"),
            ("做周复盘", "根据完成情况调整下一周任务", "表格 / ChatGPT", "汇总用户填写的完成情况、反复卡点和下周调整，不虚构未记录数据", "周复盘", "下一周计划比上一周更贴近实际完成能力"),
        ]
    elif kind == "learning":
        raw_steps = [
            ("诊断学习目标", "明确当前水平、目标、时间和验收方式", "ChatGPT", f"围绕「{goal}」设计学习诊断问题，并输出当前水平、目标、可用时间、验收标准", "学习画像和目标表", "知道学什么、多久学、学到什么程度"),
            ("拆学习模块", "把学习目标拆成可练习模块", "ChatGPT / Kimi", "把学习目标拆成 3 到 5 个模块，并为每个模块给出练习任务和优先级", "模块清单", "每个模块都有可练习任务和最低完成标准"),
            ("安排每日任务", "形成能执行的短周期计划", "ChatGPT", "生成 7 天计划，每天包含输入材料、练习任务、输出物和预计耗时", "每日任务表", "每天任务能在实际时间内完成，并有明确产出"),
            ("准备练习材料", "把计划转成当天能直接开始的练习", "ChatGPT / 题库工具", "为第 1 天任务生成阅读材料、单词复习清单、练习题和答案", "首日练习包", "用户当天能直接开始练习，不需要再找材料"),
            ("建立反馈格式", "让 AI 根据真实练习结果给出诊断式反馈", "ChatGPT", "根据用户填写的练习记录：任务、答案、错题、耗时、卡点，输出事实、问题、下一步", "反馈模板", "反馈必须引用用户记录里的具体事实"),
            ("反馈和复盘", "根据练习结果调整下一轮", "ChatGPT / 表格", "填写复盘模板：完成任务｜错题/卡点｜耗时[用户填写]｜调整动作｜明日重点", "复盘记录", "下一轮任务基于用户填写的上一轮结果调整"),
        ]
    else:
        raw_steps = [
            ("收敛目标", "把泛目标变成一个可交付的小项目", "ChatGPT", f"基于「{goal}」列出 3 个最小可做方向", "方向清单", "能选出一个一周内可完成的方向"),
            ("定义产出", "明确最终要交付什么", "文档工具", "写出目标用户、使用场景和最终产物", "项目定义", "产物能被别人试用或查看"),
            ("跑通首版", "先完成最小闭环", "低代码 / 手动流程", "用最少工具跑通一次完整流程", "MVP 结果", "至少完成一次从输入到输出"),
        ]

    return [
        RouteStep(
            step_name=step_name,
            step_goal=step_goal,
            primary_tool=primary_tool,
            backup_tool="手动整理 / 轻量表格",
            suggested_input=suggested_input,
            expected_output=expected_output,
            execution_tip="先做最小可验证版本，再根据反馈扩展细节。",
            ready_check=ready_check,
        )
        for step_name, step_goal, primary_tool, suggested_input, expected_output, ready_check in raw_steps
    ]


def _fake_route_output(user_goal: str) -> RouteOutput:
    kind = _goal_kind(user_goal)
    route_type_by_kind = {
        "anime": "MOCK：AI 动漫短剧最小闭环路线",
        "content": "MOCK：内容创作发布复盘路线",
        "vocabulary_tool": "MOCK：AI 背单词工具 MVP 路线",
        "checkin_tool": "MOCK：AI 学习打卡助手 MVP 路线",
        "learning": "MOCK：学习辅助最小闭环路线",
        "general": "MOCK：AI 项目通用起步路线",
    }
    return RouteOutput(
        task_summary=f"MOCK 结构检查：围绕「{user_goal}」生成一条示例路线。",
        route_type=route_type_by_kind.get(kind, "MOCK：AI 项目通用起步路线"),
        steps=_route_steps_for_goal(user_goal),
    )


def _fake_blockage_output(user_goal: str, selected_step: str, blockage_text: str) -> BlockageOutput:
    if "反馈" in selected_step or "鸡汤" in blockage_text:
        return BlockageOutput(
            why_stuck="MOCK：反馈太泛通常是因为没有输入学习记录、错题和耗时，模型只能生成鼓励话术。",
            substeps=[
                "把当天记录补成 4 个字段：任务、实际输出、错题/卡点、耗时。",
                "把原提示词改成诊断格式：先复述事实，再指出问题，最后给下一步练习。",
                "要求 AI 禁止使用“继续加油”等空泛鼓励，必须引用用户填写的具体记录。",
                "每次只保留 1 到 2 个明日调整动作，避免反馈变成新计划。",
            ],
            simple_input="根据今天的学习记录：任务=[用户填写]，实际输出=[用户填写]，错题/卡点=[用户填写]，耗时=[用户填写]。请按事实、问题、明日练习输出，不要写泛泛鼓励。",
            alternative_tool="先用飞书表格或 Notion 记录学习事实，再把当日一行记录交给 ChatGPT 生成反馈。",
            done_check="反馈能引用至少 1 条用户记录，指出 1 个具体错因，并给出 1 个下一次练习任务。",
        )
    if "封面" in selected_step or "点击率" in blockage_text:
        return BlockageOutput(
            why_stuck="MOCK：封面点击率低通常是因为标题收益点不清、视觉焦点太多或手机列表尺寸不可读。",
            substeps=[
                "把封面标题压缩到 8 到 14 个字。",
                "只保留一个主视觉和一个主标题。",
                "做痛点型、结果型、数字型 3 个版本对比。",
            ],
            simple_input="主题：新手用 AI 提高学习效率。请生成 3 个小红书封面标题，要求短、具体、有收益感。",
            alternative_tool="用 Canva 模板先确定标题层级，再用 AI 生成主视觉。",
            done_check="缩小到手机列表尺寸后，2 秒内能看清主题和收益。",
        )
    if "角色" in selected_step or "角色" in blockage_text:
        return BlockageOutput(
            why_stuck="MOCK：角色不一致通常是因为没有固定角色锁定卡，提示词和参考图每次都在变化。",
            substeps=[
                "写 80 到 120 字角色锁定描述。",
                "选 1 张主参考图，固定发型、服装和主色。",
                "后续每次只改变动作、表情或场景。",
            ],
            simple_input="同一个 16 岁高中生主角，黑色短发，蓝白校服，坚定眼神，动漫风，正面半身。",
            alternative_tool="先用即梦或 Midjourney 生成角色基准图，再用支持参考图的工具做镜头。",
            done_check="连续生成 3 张图，旁观者能判断是同一个角色。",
        )
    return BlockageOutput(
        why_stuck="MOCK：当前卡点太泛通常是因为没有定位到具体步骤、输入材料和最低完成标准。",
        substeps=[
            "先明确当前卡在哪个步骤。",
            "补充已有输入和期望产物。",
            "把下一步压缩成 1 个可在当天完成的动作。",
        ],
        simple_input="我现在卡在这个步骤：[步骤名]；已有材料：[列出材料]；想得到：[产物]。请给 3 个最小修正动作。",
        alternative_tool="先用表格列出步骤、卡点、已有输入、期望输出，再让模型逐项拆解。",
        done_check="能说清下一步要做什么、用什么输入、产出什么结果。",
    )


def _is_specific_followup_answer(followup_answer: str) -> bool:
    if not followup_answer:
        return False

    normalized_answer = followup_answer.replace(" ", "")
    generic_answers = ["随便", "都行", "都可以", "不知道", "没想好", "先通用一点"]
    return not any(word in normalized_answer for word in generic_answers)


def _mock_state_for_case(case: dict[str, Any]) -> dict[str, Any]:
    case_type = case["case_type"]
    case_input = case["input"]

    if case_type == "blockage":
        return {
            **case_input,
            "current_stage": "mock_blockage_solved",
            "error_message": "",
            "blockage_result": _fake_blockage_output(
                user_goal=case_input["user_goal"],
                selected_step=case_input["selected_step"],
                blockage_text=case_input["blockage_text"],
            ),
        }

    user_goal = case_input.get("user_goal", "")
    followup_answer = case_input.get("followup_answer", "")
    state: dict[str, Any] = {
        **case_input,
        "current_stage": "mock_route_generated",
        "error_message": "",
    }

    if followup_answer:
        if _is_specific_followup_answer(followup_answer):
            state["close_result"] = "close_success"
            state["effective_goal"] = followup_answer
            effective_goal = followup_answer
        else:
            state["close_result"] = "close_failed"
            state["effective_goal"] = user_goal
            effective_goal = user_goal
    else:
        effective_goal = user_goal

    state["route_result"] = _fake_route_output(effective_goal)
    return state


def _json_block(value: Any) -> str:
    return "```json\n" + json.dumps(value, ensure_ascii=False, indent=2) + "\n```"


def _field(value: Any, name: str, default: str = "") -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _render_route_result(state: dict[str, Any]) -> list[str]:
    route_result = state.get("route_result")
    if route_result is None:
        return ["route_result: None"]

    lines = [
        f"- task_summary: {_field(route_result, 'task_summary')}",
        f"- route_type: {_field(route_result, 'route_type')}",
        "",
        "### steps",
    ]
    for index, step in enumerate(_field(route_result, "steps", []), start=1):
        lines.extend(
            [
                f"{index}. {_field(step, 'step_name')}",
                f"   - step_goal: {_field(step, 'step_goal')}",
                f"   - primary_tool: {_field(step, 'primary_tool')}",
                f"   - backup_tool: {_field(step, 'backup_tool')}",
                f"   - suggested_input: {_field(step, 'suggested_input')}",
                f"   - expected_output: {_field(step, 'expected_output')}",
                f"   - execution_tip: {_field(step, 'execution_tip')}",
                f"   - ready_check: {_field(step, 'ready_check')}",
            ]
        )
    return lines


def _render_blockage_result(state: dict[str, Any]) -> list[str]:
    blockage_result = state.get("blockage_result")
    if blockage_result is None:
        return ["blockage_result: None"]

    lines = [
        f"- why_stuck: {_field(blockage_result, 'why_stuck')}",
        "- substeps:",
    ]
    for substep in _field(blockage_result, "substeps", []):
        lines.append(f"  - {substep}")
    lines.extend(
        [
            f"- simple_input: {_field(blockage_result, 'simple_input')}",
            f"- alternative_tool: {_field(blockage_result, 'alternative_tool')}",
            f"- done_check: {_field(blockage_result, 'done_check')}",
        ]
    )
    return lines


def _render_eval_slots() -> list[str]:
    return [
        "## 人工评估预留",
        "",
        "- 目标贴合度：",
        "- 步骤具体度：",
        "- 执行可行性：",
        "- 收口合理性：",
        "- 推进价值：",
        "- 备注：",
    ]


def _run_real_case(case: dict[str, Any], route_app: Any, blockage_app: Any) -> dict[str, Any]:
    case_type = case["case_type"]
    if case_type == "blockage":
        final_state = blockage_app.invoke(case["input"])
    else:
        final_state = route_app.invoke(case["input"])

    return {
        "case": case,
        "state": final_state,
    }


def _run_mock_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case": case,
        "state": _mock_state_for_case(case),
    }


def _render_case(result: dict[str, Any]) -> str:
    case = result["case"]
    state = result["state"]
    case_type = case["case_type"]

    lines = [
        f"## {case['case_id']}",
        "",
        f"- case_type: {case_type}",
        f"- why_selected: {case['why_selected']}",
    ]
    if case.get("notes"):
        lines.append(f"- notes: {case['notes']}")

    lines.extend(
        [
            "",
            "## input",
            "",
            _json_block(case["input"]),
            "",
            "## 关键状态",
            "",
            f"- close_result: {state.get('close_result', '')}",
            f"- effective_goal: {state.get('effective_goal', '')}",
            f"- current_stage: {state.get('current_stage', '')}",
            f"- error_message: {state.get('error_message', '')}",
            "",
            "## 生成结果",
            "",
        ]
    )

    if case_type == "blockage":
        lines.extend(_render_blockage_result(state))
    else:
        lines.extend(_render_route_result(state))

    lines.extend(["", *_render_eval_slots(), ""])
    return "\n".join(lines)


def build_markdown(results: list[dict[str, Any]], mode: str) -> str:
    if mode == "real":
        mode_note = "真实输出模式：使用当前真实 workflow、真实检索和真实 LLM 生成结果。"
    else:
        mode_note = "MOCK 结构检查模式：本文件不是内容质量证据，只用于检查 case 结构和渲染格式。"

    lines = [
        "# 内容质量人工评估输出",
        "",
        f"- mode: {mode}",
        f"- total_cases: {len(results)}",
        f"- 说明：{mode_note}",
        "",
    ]
    for result in results:
        lines.append(_render_case(result))
    return "\n".join(lines)


def run_real() -> list[dict[str, Any]]:
    from graph.workflow import build_blockage_workflow, build_route_workflow

    route_app = build_route_workflow()
    blockage_app = build_blockage_workflow()

    return [
        _run_real_case(case, route_app=route_app, blockage_app=blockage_app)
        for case in CONTENT_EVAL_CASES
    ]


def run_mock() -> list[dict[str, Any]]:
    return [_run_mock_case(case) for case in CONTENT_EVAL_CASES]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run content quality eval cases.")
    parser.add_argument(
        "--mode",
        choices=("real", "mock"),
        default="real",
        help="real 使用真实 workflow/RAG/LLM；mock 只做结构检查。默认 real。",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help="Markdown 输出路径。默认 evals/content_eval_outputs.md。",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        if args.mode == "real":
            results = run_real()
        else:
            print("WARNING: mock 模式只用于结构检查，不是内容质量证据。", file=sys.stderr)
            results = run_mock()
    except Exception as exc:
        print(f"content eval failed in {args.mode} mode: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_markdown(results, mode=args.mode), encoding="utf-8")
    print(f"generated: {args.output}")
    print(f"mode: {args.mode}")
    print(f"total_cases: {len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
