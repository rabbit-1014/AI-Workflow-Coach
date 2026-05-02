from services.llm_service import LLMService


def main():
    try:
        print("Testing OpenAI-compatible chat provider...")
        llm = LLMService()
        result = llm.invoke(
            user_prompt='请只输出一个 JSON：{"ok": true}',
            system_prompt="你只能输出 JSON，不要解释，不要 Markdown。",
        )
    except Exception as e:
        print(f"调用失败：{e}")
        return

    print(f"provider={llm.provider}")
    print(f"model={llm.model_name}")
    print(result)


if __name__ == "__main__":
    main()
