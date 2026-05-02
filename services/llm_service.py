import time
from typing import Optional

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage

import config
from utils.error_utils import classify_error, is_retryable_error
from utils.logger import setup_logger
from utils.observability import (
    elapsed_ms,
    get_current_call_type,
    get_current_workflow_run_id,
    record_model_call_log,
)


logger = setup_logger(__name__)


class LLMService:
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_retries: Optional[int] = None,
        provider: Optional[str] = None,
    ):
        configured_provider = (provider or config.CHAT_PROVIDER).strip().lower()
        self.original_provider = configured_provider
        self.provider = (
            "openai_compatible"
            if configured_provider == "deepseek"
            else configured_provider
        )
        self.model_name = model_name or config.CHAT_MODEL_NAME
        self.temperature = (
            temperature if temperature is not None else config.LLM_TEMPERATURE
        )
        self.max_retries = (
            max_retries if max_retries is not None else config.LLM_MAX_RETRIES
        )
        self.llm = None
        self.client = None

        if self.provider == "dashscope":
            self._init_dashscope()
        elif self.provider == "openai_compatible":
            self._init_openai_compatible()
        else:
            raise ValueError(f"不支持的 CHAT_PROVIDER: {self.original_provider}")

        logger.info(
            f"LLMService 初始化完成: provider={self.provider}, "
            f"model={self.model_name}, temperature={self.temperature}"
        )

    def _init_dashscope(self) -> None:
        if not config.DASHSCOPE_API_KEY:
            raise ValueError("缺少 DASHSCOPE_API_KEY，请先配置环境变量。")

        self.llm = ChatTongyi(
            model=self.model_name,
            temperature=self.temperature,
            max_retries=self.max_retries,
            dashscope_api_key=config.DASHSCOPE_API_KEY,
        )

    def _init_openai_compatible(self) -> None:
        if not config.EFFECTIVE_CHAT_API_KEY:
            raise ValueError("CHAT_API_KEY 未配置，无法调用 OpenAI-compatible chat provider。")
        if not config.EFFECTIVE_CHAT_BASE_URL:
            raise ValueError("CHAT_BASE_URL 未配置，无法调用 OpenAI-compatible chat provider。")

    def invoke(self, user_prompt: str, system_prompt: Optional[str] = None) -> str:
        if not user_prompt or not user_prompt.strip():
            raise ValueError("user_prompt 不能为空。")

        input_chars = len(user_prompt or "") + len(system_prompt or "")
        is_correction = "你上次输出的内容无法被系统解析" in user_prompt
        last_error = None

        for attempt in range(config.MAX_LLM_API_RETRIES + 1):
            start = time.perf_counter()
            try:
                if self.provider == "dashscope":
                    content = self._invoke_dashscope(user_prompt, system_prompt)
                elif self.provider == "openai_compatible":
                    content = self._invoke_openai_compatible(user_prompt, system_prompt)
                else:
                    raise ValueError(f"不支持的 CHAT_PROVIDER: {self.original_provider}")
            except Exception as e:
                error_type = classify_error(e)
                record_model_call_log(
                    workflow_run_id=get_current_workflow_run_id(),
                    call_type=get_current_call_type(),
                    provider=self.provider,
                    model=self.model_name,
                    input_chars=input_chars,
                    output_chars=0,
                    duration_ms=elapsed_ms(start),
                    success=False,
                    error_type=error_type,
                    error_message=str(e),
                    is_correction=is_correction,
                    retry_index=attempt,
                    max_retries=config.MAX_LLM_API_RETRIES,
                )
                last_error = e

                if (
                    attempt >= config.MAX_LLM_API_RETRIES
                    or not is_retryable_error(error_type)
                ):
                    raise

                logger.warning(
                    "LLM 调用失败，准备重试: error_type=%s, retry_index=%s/%s",
                    error_type,
                    attempt + 1,
                    config.MAX_LLM_API_RETRIES,
                )
                time.sleep(0.5)
                continue

            record_model_call_log(
                workflow_run_id=get_current_workflow_run_id(),
                call_type=get_current_call_type(),
                provider=self.provider,
                model=self.model_name,
                input_chars=input_chars,
                output_chars=len(content or ""),
                duration_ms=elapsed_ms(start),
                success=True,
                is_correction=is_correction,
                retry_index=attempt,
                max_retries=config.MAX_LLM_API_RETRIES,
            )
            return content

        raise last_error

    def _invoke_dashscope(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        messages = []

        if system_prompt and system_prompt.strip():
            messages.append(SystemMessage(content=system_prompt.strip()))

        messages.append(HumanMessage(content=user_prompt.strip()))

        logger.info("开始调用 LLM")
        response = self.llm.invoke(messages)

        content = response.content if hasattr(response, "content") else str(response)

        logger.info(f"LLM 调用完成，返回长度: {len(content)}")
        return content

    def _invoke_openai_compatible(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        messages = []

        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})

        messages.append({"role": "user", "content": user_prompt.strip()})

        if self.client is None:
            try:
                from openai import OpenAI
            except ModuleNotFoundError as e:
                raise ValueError(
                    "openai 依赖未安装，无法调用 OpenAI-compatible chat provider。"
                ) from e

            self.client = OpenAI(
                api_key=config.EFFECTIVE_CHAT_API_KEY,
                base_url=config.EFFECTIVE_CHAT_BASE_URL,
            )

        logger.info("开始调用 LLM")
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=False,
        )

        content = response.choices[0].message.content or ""

        logger.info(f"LLM 调用完成，返回长度: {len(content)}")
        return content
