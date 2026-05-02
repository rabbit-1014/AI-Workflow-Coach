import config
import services.llm_service as llm_module


def _snapshot_config():
    return {
        "CHAT_PROVIDER": config.CHAT_PROVIDER,
        "CHAT_MODEL_NAME": config.CHAT_MODEL_NAME,
        "CHAT_API_KEY": config.CHAT_API_KEY,
        "CHAT_BASE_URL": config.CHAT_BASE_URL,
        "DEEPSEEK_API_KEY": config.DEEPSEEK_API_KEY,
        "DEEPSEEK_BASE_URL": config.DEEPSEEK_BASE_URL,
        "EFFECTIVE_CHAT_PROVIDER": config.EFFECTIVE_CHAT_PROVIDER,
        "EFFECTIVE_CHAT_API_KEY": config.EFFECTIVE_CHAT_API_KEY,
        "EFFECTIVE_CHAT_BASE_URL": config.EFFECTIVE_CHAT_BASE_URL,
        "DASHSCOPE_API_KEY": config.DASHSCOPE_API_KEY,
    }


def _restore_config(snapshot):
    for key, value in snapshot.items():
        setattr(config, key, value)


def _set_chat_config(
    provider: str,
    chat_api_key: str = "",
    chat_base_url: str = "",
    deepseek_api_key: str = "",
    deepseek_base_url: str = "https://api.deepseek.com",
):
    config.CHAT_PROVIDER = provider
    config.CHAT_MODEL_NAME = "deepseek-v4-flash"
    config.CHAT_API_KEY = chat_api_key
    config.CHAT_BASE_URL = chat_base_url
    config.DEEPSEEK_API_KEY = deepseek_api_key
    config.DEEPSEEK_BASE_URL = deepseek_base_url
    config.EFFECTIVE_CHAT_PROVIDER = (
        "openai_compatible" if provider == "deepseek" else provider
    )
    config.EFFECTIVE_CHAT_API_KEY = chat_api_key or deepseek_api_key
    config.EFFECTIVE_CHAT_BASE_URL = chat_base_url or (
        deepseek_base_url
        if provider in {"deepseek", "openai_compatible"}
        else ""
    )


def test_openai_compatible_missing_key_raises_clear_error():
    snapshot = _snapshot_config()
    try:
        _set_chat_config(
            provider="openai_compatible",
            chat_api_key="",
            chat_base_url="https://api.deepseek.com",
        )

        try:
            llm_module.LLMService()
        except ValueError as e:
            assert "CHAT_API_KEY 未配置" in str(e)
        else:
            raise AssertionError("missing CHAT_API_KEY should raise ValueError")
    finally:
        _restore_config(snapshot)


def test_openai_compatible_missing_base_url_raises_clear_error():
    snapshot = _snapshot_config()
    try:
        _set_chat_config(
            provider="openai_compatible",
            chat_api_key="fake-chat-key",
            chat_base_url="",
            deepseek_base_url="",
        )

        try:
            llm_module.LLMService()
        except ValueError as e:
            assert "CHAT_BASE_URL 未配置" in str(e)
        else:
            raise AssertionError("missing CHAT_BASE_URL should raise ValueError")
    finally:
        _restore_config(snapshot)


def test_deepseek_legacy_config_maps_to_openai_compatible():
    snapshot = _snapshot_config()
    try:
        _set_chat_config(
            provider="deepseek",
            deepseek_api_key="fake-deepseek-key",
            deepseek_base_url="https://api.deepseek.com",
        )

        llm = llm_module.LLMService()

        assert llm.original_provider == "deepseek"
        assert llm.provider == "openai_compatible"
        assert config.EFFECTIVE_CHAT_API_KEY == "fake-deepseek-key"
        assert config.EFFECTIVE_CHAT_BASE_URL == "https://api.deepseek.com"
    finally:
        _restore_config(snapshot)


def test_dashscope_provider_does_not_require_openai_compatible_key():
    snapshot = _snapshot_config()
    original_chat_tongyi = llm_module.ChatTongyi

    class FakeChatTongyi:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def invoke(self, messages):
            class Response:
                content = "dashscope-ok"

            return Response()

    try:
        _set_chat_config(provider="dashscope")
        config.CHAT_MODEL_NAME = "qwen-test"
        config.DASHSCOPE_API_KEY = "fake_dashscope_key"
        llm_module.ChatTongyi = FakeChatTongyi

        llm = llm_module.LLMService()
        result = llm.invoke("测试", "系统提示")

        assert llm.provider == "dashscope"
        assert result == "dashscope-ok"
        assert llm.llm.kwargs["model"] == "qwen-test"
        assert llm.llm.kwargs["dashscope_api_key"] == "fake_dashscope_key"
    finally:
        llm_module.ChatTongyi = original_chat_tongyi
        _restore_config(snapshot)


def test_unsupported_provider_raises_clear_error():
    snapshot = _snapshot_config()
    try:
        _set_chat_config(provider="unknown")

        try:
            llm_module.LLMService()
        except ValueError as e:
            assert "不支持的 CHAT_PROVIDER" in str(e)
        else:
            raise AssertionError("unsupported provider should raise ValueError")
    finally:
        _restore_config(snapshot)


if __name__ == "__main__":
    test_openai_compatible_missing_key_raises_clear_error()
    test_openai_compatible_missing_base_url_raises_clear_error()
    test_deepseek_legacy_config_maps_to_openai_compatible()
    test_dashscope_provider_does_not_require_openai_compatible_key()
    test_unsupported_provider_raises_clear_error()
    print("test_llm_provider_config.py: all tests passed")
