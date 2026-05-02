import json

from schemas import BlockageOutput, RouteOutput
from services.blockage_solver import BlockageSolver
from services.route_generator import RouteGenerator


def _route_json() -> str:
    return json.dumps(
        {
            "task_summary": "生成校园自习室预约小程序路线",
            "route_type": "完整路线",
            "steps": [
                {
                    "step_name": "梳理需求",
                    "step_goal": "明确预约、签到和权限要求",
                    "primary_tool": "需求清单",
                    "backup_tool": "人工确认",
                    "suggested_input": "校园自习室预约小程序",
                    "expected_output": "需求拆解表",
                    "execution_tip": "先确认硬约束",
                    "ready_check": "需求清单已确认",
                }
            ],
        },
        ensure_ascii=False,
    )


def _blockage_json() -> str:
    return json.dumps(
        {
            "why_stuck": "步骤范围较大，缺少可执行拆分。",
            "substeps": ["先列出输入字段", "再实现最小流程"],
            "simple_input": "请先实现预约创建接口。",
            "alternative_tool": "可以先用伪代码梳理流程。",
            "done_check": "能说明下一步要改哪个文件。",
        },
        ensure_ascii=False,
    )


class FakeLLMService:
    def __init__(self, responses: list[str]):
        self.responses = responses
        self.calls: list[tuple[str, str | None]] = []

    def invoke(self, user_prompt: str, system_prompt: str | None = None) -> str:
        self.calls.append((user_prompt, system_prompt))
        if not self.responses:
            raise AssertionError("FakeLLMService 没有可返回的响应。")
        return self.responses.pop(0)


def _route_generator_with(fake_llm: FakeLLMService) -> RouteGenerator:
    generator = object.__new__(RouteGenerator)
    generator.llm_service = fake_llm
    return generator


def _blockage_solver_with(fake_llm: FakeLLMService) -> BlockageSolver:
    solver = object.__new__(BlockageSolver)
    solver.llm_service = fake_llm
    return solver


def test_route_valid_first_try_does_not_retry():
    fake_llm = FakeLLMService([_route_json()])
    generator = _route_generator_with(fake_llm)

    result = generator.generate_route("做预约小程序", "预约系统上下文")

    assert isinstance(result, RouteOutput)
    assert result.steps[0].step_name == "梳理需求"
    assert len(fake_llm.calls) == 1


def test_route_invalid_then_valid_retries_with_correction_prompt():
    fake_llm = FakeLLMService(["不是合法 JSON", _route_json()])
    generator = _route_generator_with(fake_llm)

    result = generator.generate_route("做预约小程序", "预约系统上下文")

    assert isinstance(result, RouteOutput)
    assert len(fake_llm.calls) == 2
    retry_prompt = fake_llm.calls[1][0]
    assert "JSONDecodeError" in retry_prompt or "ValidationError" in retry_prompt
    assert "不要输出 Markdown" in retry_prompt
    assert "严格合法的 JSON" in retry_prompt


def test_blockage_invalid_then_valid_retries_successfully():
    fake_llm = FakeLLMService(["{坏 JSON", _blockage_json()])
    solver = _blockage_solver_with(fake_llm)

    result = solver.solve_blockage(
        user_goal="做预约小程序",
        selected_step="实现预约接口",
        blockage_text="不知道从哪里开始",
        blockage_context="预约接口上下文",
    )

    assert isinstance(result, BlockageOutput)
    assert result.substeps == ["先列出输入字段", "再实现最小流程"]
    assert len(fake_llm.calls) == 2


def test_route_invalid_twice_raises_clear_error():
    fake_llm = FakeLLMService(["不是合法 JSON", '{"task_summary": "缺字段"}'])
    generator = _route_generator_with(fake_llm)

    try:
        generator.generate_route("做预约小程序", "预约系统上下文")
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("两次解析失败时应抛出 ValueError。")

    assert "已 self-correction 重试 1 次仍失败" in message
    assert "首次错误" in message
    assert "重试错误" in message
    assert len(fake_llm.calls) == 2


if __name__ == "__main__":
    test_route_valid_first_try_does_not_retry()
    test_route_invalid_then_valid_retries_with_correction_prompt()
    test_blockage_invalid_then_valid_retries_successfully()
    test_route_invalid_twice_raises_clear_error()
    print("test_self_correction.py: all tests passed")
