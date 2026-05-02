import json
import re

from config import MAX_PARSE_CORRECTION_RETRIES
from schemas import BlockageOutput
from prompts import BLOCKAGE_SYSTEM_PROMPT, build_blockage_user_prompt
from services.llm_service import LLMService
from utils.logger import setup_logger


logger = setup_logger(__name__)


class BlockageSolver:
    def __init__(self):
        self.llm_service = LLMService()
        logger.info("BlockageSolver 初始化完成")

    @staticmethod
    def _extract_json(text: str) -> str:
        text = text.strip()

        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

        return text.strip()

    @staticmethod
    def _try_parse_blockage(raw_text: str) -> tuple[BlockageOutput | None, str]:
        try:
            json_text = BlockageSolver._extract_json(raw_text)
            data = json.loads(json_text)
            return BlockageOutput.model_validate(data), ""
        except Exception as e:
            error_message = f"{type(e).__name__}: {e}"
            logger.warning(f"BlockageOutput 解析失败: {error_message}")
            return None, error_message

    @staticmethod
    def _build_correction_prompt(raw_text: str, error_message: str) -> str:
        truncated = raw_text[:2000]
        return (
            "你上次输出的内容无法被系统解析为合法 JSON，或 JSON 结构不符合 BlockageOutput 要求。\n\n"
            f"解析/校验错误信息：\n{error_message}\n\n"
            f"你上次的原始输出：\n{truncated}\n\n"
            "请重新输出一个严格合法的 JSON 对象。不要输出 Markdown，不要输出解释，不要输出代码块。\n"
            "JSON 必须符合以下结构：\n"
            "{\n"
            '  "why_stuck": "为什么容易卡在这里",\n'
            '  "substeps": ["更细的执行子步骤 1", "更细的执行子步骤 2"],\n'
            '  "simple_input": "更简单、可直接参考的输入示例",\n'
            '  "alternative_tool": "替代工具或替代做法",\n'
            '  "done_check": "这一步完成的判断标准"\n'
            "}\n"
        )

    def solve_blockage(
        self,
        user_goal: str,
        selected_step: str,
        blockage_text: str,
        blockage_context: str,
    ) -> BlockageOutput:
        if not user_goal or not user_goal.strip():
            raise ValueError("user_goal 不能为空。")

        if not selected_step or not selected_step.strip():
            raise ValueError("selected_step 不能为空。")

        if not blockage_text or not blockage_text.strip():
            raise ValueError("blockage_text 不能为空。")

        if not blockage_context or not blockage_context.strip():
            raise ValueError("blockage_context 不能为空。")

        user_prompt = build_blockage_user_prompt(
            user_goal=user_goal,
            selected_step=selected_step,
            blockage_text=blockage_text,
            blockage_context=blockage_context,
        )

        logger.info(
            f"开始生成卡点解决方案，user_goal={user_goal}, selected_step={selected_step}"
        )
        raw_text = self.llm_service.invoke(
            user_prompt=user_prompt,
            system_prompt=BLOCKAGE_SYSTEM_PROMPT,
        )

        logger.info(f"卡点解决原始输出长度: {len(raw_text)}")

        result, error_message = self._try_parse_blockage(raw_text)
        if result is not None:
            logger.info(f"卡点解决解析成功，substeps 数量: {len(result.substeps)}")
            return result

        latest_raw_text = raw_text
        latest_error_message = error_message
        for retry_index in range(1, MAX_PARSE_CORRECTION_RETRIES + 1):
            logger.warning(
                "卡点解决 JSON 解析失败，尝试 self-correction 重试 %s/%s",
                retry_index,
                MAX_PARSE_CORRECTION_RETRIES,
            )
            retry_prompt = self._build_correction_prompt(
                latest_raw_text,
                latest_error_message,
            )

            retry_raw_text = self.llm_service.invoke(
                user_prompt=retry_prompt,
                system_prompt=BLOCKAGE_SYSTEM_PROMPT,
            )
            logger.info(f"卡点解决重试输出长度: {len(retry_raw_text)}")

            result, retry_error_message = self._try_parse_blockage(retry_raw_text)
            if result is not None:
                logger.info(f"卡点解决重试解析成功，substeps 数量: {len(result.substeps)}")
                return result

            latest_raw_text = retry_raw_text
            latest_error_message = retry_error_message

        raise ValueError(
            "LLM 输出无法解析为合法 BlockageOutput，已 self-correction "
            f"重试 {MAX_PARSE_CORRECTION_RETRIES} 次仍失败。"
            f" 首次错误: {error_message}; 重试错误: {latest_error_message}"
        )
