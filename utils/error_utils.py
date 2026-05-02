RETRYABLE_ERROR_TYPES = {"timeout_error", "connection_error", "api_error"}


def classify_error(error: Exception) -> str:
    error_class = type(error).__name__.lower()
    error_text = str(error).lower()
    combined = f"{error_class} {error_text}"

    if (
        "api key 未配置" in str(error)
        or "CHAT_API_KEY 未配置" in str(error)
        or "DEEPSEEK_API_KEY 未配置" in str(error)
        or "DASHSCOPE_API_KEY 未配置" in str(error)
    ):
        return "config_error"

    if (
        "401" in combined
        or "unauthorized" in combined
        or "invalid api key" in combined
        or "authentication" in combined
        or "permission denied" in combined
    ):
        return "auth_error"

    if (
        "jsondecodeerror" in combined
        or "无法解析为合法" in combined
        or "json decode" in combined
    ):
        return "parse_error"

    if "validationerror" in combined or "model_validate" in combined:
        return "validation_error"

    if (
        "timeout" in combined
        or "timed out" in combined
        or "request timed out" in combined
    ):
        return "timeout_error"

    if (
        "connection" in combined
        or "network" in combined
        or "connecterror" in combined
    ):
        return "connection_error"

    if "api" in combined or "openai" in combined or "dashscope" in combined:
        return "api_error"

    return "unknown_error"


def is_retryable_error(error_type: str) -> bool:
    return error_type in RETRYABLE_ERROR_TYPES
