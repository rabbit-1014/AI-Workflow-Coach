import json
import re

from config import MAX_PARSE_CORRECTION_RETRIES
from schemas import RouteOutput
from prompts import ROUTE_SYSTEM_PROMPT, build_route_user_prompt
from services.llm_service import LLMService
from utils.logger import setup_logger


logger = setup_logger(__name__)


class RouteGenerator:
    def __init__(self):
        self.llm_service = LLMService()
        logger.info("RouteGenerator 初始化完成")

    @staticmethod
    def _extract_json(text: str) -> str:
        text = text.strip()

        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

        return text.strip()

    @staticmethod
    def _try_parse_route(raw_text: str) -> tuple[RouteOutput | None, str]:
        try:
            json_text = RouteGenerator._extract_json(raw_text)
            data = json.loads(json_text)
            return RouteOutput.model_validate(data), ""
        except Exception as e:
            error_message = f"{type(e).__name__}: {e}"
            logger.warning(f"RouteOutput 解析失败: {error_message}")
            return None, error_message

    @staticmethod
    def _build_correction_prompt(raw_text: str, error_message: str) -> str:
        truncated = raw_text[:2000]
        return (
            "你上次输出的内容无法被系统解析为合法 JSON，或 JSON 结构不符合 RouteOutput 要求。\n\n"
            f"解析/校验错误信息：\n{error_message}\n\n"
            f"你上次的原始输出：\n{truncated}\n\n"
            "请重新输出一个严格合法的 JSON 对象。不要输出 Markdown，不要输出解释，不要输出代码块。\n"
            "JSON 必须符合以下结构：\n"
            "{\n"
            '  "task_summary": "对用户任务的简要理解",\n'
            '  "route_type": "完整路线 或 通用起步路线",\n'
            '  "steps": [\n'
            "    {\n"
            '      "step_name": "步骤名称",\n'
            '      "step_goal": "这一步要做什么",\n'
            '      "primary_tool": "首选工具与功能",\n'
            '      "backup_tool": "备选工具与原因",\n'
            '      "suggested_input": "建议输入",\n'
            '      "expected_output": "预期产出",\n'
            '      "execution_tip": "执行提醒",\n'
            '      "ready_check": "进入下一步前的最低通过标准"\n'
            "    }\n"
            "  ]\n"
            "}\n"
        )

    def generate_route(self, user_goal: str, route_context: str) -> RouteOutput:
        if not user_goal or not user_goal.strip():
            raise ValueError("user_goal 不能为空。")

        if not route_context or not route_context.strip():
            raise ValueError("route_context 不能为空。")

        user_prompt = build_route_user_prompt(
            user_goal=user_goal,
            route_context=route_context,
        )

        logger.info(f"开始生成路线，user_goal={user_goal}")
        raw_text = self.llm_service.invoke(
            user_prompt=user_prompt,
            system_prompt=ROUTE_SYSTEM_PROMPT,
        )

        logger.info(f"路线生成原始输出长度: {len(raw_text)}")

        result, error_message = self._try_parse_route(raw_text)
        if result is not None:
            logger.info(f"路线生成解析成功，步骤数量: {len(result.steps)}")
            return result

        latest_raw_text = raw_text
        latest_error_message = error_message
        for retry_index in range(1, MAX_PARSE_CORRECTION_RETRIES + 1):
            logger.warning(
                "路线生成 JSON 解析失败，尝试 self-correction 重试 %s/%s",
                retry_index,
                MAX_PARSE_CORRECTION_RETRIES,
            )
            retry_prompt = self._build_correction_prompt(
                latest_raw_text,
                latest_error_message,
            )

            retry_raw_text = self.llm_service.invoke(
                user_prompt=retry_prompt,
                system_prompt=ROUTE_SYSTEM_PROMPT,
            )
            logger.info(f"路线生成重试输出长度: {len(retry_raw_text)}")

            result, retry_error_message = self._try_parse_route(retry_raw_text)
            if result is not None:
                logger.info(f"路线生成重试解析成功，步骤数量: {len(result.steps)}")
                return result

            latest_raw_text = retry_raw_text
            latest_error_message = retry_error_message

        raise ValueError(
            "LLM 输出无法解析为合法 RouteOutput，已 self-correction "
            f"重试 {MAX_PARSE_CORRECTION_RETRIES} 次仍失败。"
            f" 首次错误: {error_message}; 重试错误: {latest_error_message}"
        )
