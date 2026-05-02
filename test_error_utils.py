import json

from utils.error_utils import classify_error, is_retryable_error


def test_timeout_error_is_classified_retryable():
    assert classify_error(TimeoutError("Request timed out")) == "timeout_error"
    assert is_retryable_error("timeout_error") is True


def test_connection_error_is_classified_retryable():
    assert classify_error(ConnectionError("Connection error: network down")) == "connection_error"
    assert is_retryable_error("connection_error") is True


def test_missing_key_is_config_error_not_retryable():
    assert classify_error(ValueError("CHAT_API_KEY 未配置")) == "config_error"
    assert is_retryable_error("config_error") is False


def test_unauthorized_is_auth_error_not_retryable():
    assert classify_error(RuntimeError("401 unauthorized invalid api key")) == "auth_error"
    assert is_retryable_error("auth_error") is False


def test_json_decode_error_is_parse_error_not_retryable():
    error = json.JSONDecodeError("Expecting value", "not-json", 0)
    assert classify_error(error) == "parse_error"
    assert is_retryable_error("parse_error") is False


def test_validation_error_text_is_validation_error_not_retryable():
    assert classify_error(ValueError("ValidationError: model_validate failed")) == "validation_error"
    assert is_retryable_error("validation_error") is False


if __name__ == "__main__":
    test_timeout_error_is_classified_retryable()
    test_connection_error_is_classified_retryable()
    test_missing_key_is_config_error_not_retryable()
    test_unauthorized_is_auth_error_not_retryable()
    test_json_decode_error_is_parse_error_not_retryable()
    test_validation_error_text_is_validation_error_not_retryable()
    print("test_error_utils.py: all tests passed")
