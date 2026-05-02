# Architecture

## 模块分层

```text
Streamlit UI
  ↓
LangGraph Workflow
  ↓
RAG Service
  ↓
LLMService
  ↓
DashScope / OpenAI-compatible Provider
```

主要模块：

- `app.py`：页面入口，负责用户输入、结果展示和本地状态恢复。
- `graph/`：工作流编排，定义路线生成流、卡点细化流、节点和状态。
- `services/`：业务服务层，封装 RAG、LLM、路线生成和卡点细化。
- `vector_store/`：Chroma 索引构建和检索。
- `knowledge/`：本地 Markdown 知识库。
- `utils/`：错误分类、日志、可观测性和运行摘要。
- `evals/`：回归门禁和评估脚本。

## Route Workflow

```text
user_goal
  ↓
analyze_task_node
  ↓
ask_followup_node（必要时）
  ↓
close_followup_node
  ↓
retrieve_for_route_node
  ↓
generate_route_node
  ↓
route_result
```

路线工作流先理解用户目标，再根据收口状态决定是否继续。进入生成前会进行路线相关 RAG 检索，随后调用聊天模型生成结构化路线结果。

## Blockage Workflow

```text
user_goal + selected_step + blockage_text
  ↓
retrieve_for_blockage_node
  ↓
solve_blockage_node
  ↓
blockage_result
```

卡点工作流依赖已经生成的路线步骤。用户选择卡住的步骤并补充卡点描述后，系统先检索相关工具、流程或常见问题，再生成结构化卡点建议。

## Observability Flow

```text
workflow_run_id
  ├── workflow_trace.jsonl
  ├── model_call_log.jsonl
  └── retrieval_trace.jsonl
       ↓
     run_summary
```

`workflow_run_id` 用来串联一次路线生成或卡点细化。`run_summary` 从 workflow、model call 和 retrieval 三类记录中聚合运行状态、耗时、错误和重试信息。

观测日志只记录工程诊断需要的摘要字段，不记录完整 prompt、完整模型输出、API key 或认证请求头。

## Model Provider Flow

```text
config.py
  ↓
LLMService
  ↓
provider switch
  ├── dashscope
  └── openai_compatible
        ↓
      DeepSeek-V4-Flash
```

聊天生成模型由 `CHAT_PROVIDER`、`CHAT_MODEL_NAME`、`CHAT_API_KEY` 和 `CHAT_BASE_URL` 控制。当前 DeepSeek-V4-Flash 通过 OpenAI 兼容协议接入。

Embedding 由 DashScope 提供：

```text
knowledge/*.md
  ↓
vector_store.build_index
  ↓
Chroma
  ↓
retriever
  ↓
RAG context
```

聊天生成和 embedding 分开配置，便于后续替换聊天模型或调整检索层。
