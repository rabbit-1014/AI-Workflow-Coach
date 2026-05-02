# Engineering Notes

## 1. 为什么项目不只是调 API

AI Workflow Coach 的核心价值不在于把用户输入转发给模型，而在于把“目标理解、信息收口、知识检索、结构化生成、异常兜底、运行观测”串成一个可回归的工程链路。

V1 的输出也不是自由聊天文本，而是两类结构化中间结果：

- 可执行的 AI 工作流路线
- 针对某个路线步骤的卡点细化建议

这让项目更接近一个轻量工作流系统，而不是一次性 prompt demo。

## 2. 输入收口机制

用户目标可能非常模糊，例如只说“我想做 AI 视频”。系统会先做任务理解，并在必要时进入补问和收口。

收口结果分为：

- `close_success`：信息足够，直接进入路线生成。
- `close_partial`：信息不完整，但可以基于已有条件生成带假设的路线。
- `close_failed`：关键信息不足，返回可控提示，不强行生成。

这个设计的重点是避免系统在输入不足时直接编造完整方案。

## 3. 模型供应商抽象

聊天生成模型通过配置选择 provider：

- `dashscope`
- `openai_compatible`

DeepSeek-V4-Flash 使用 `openai_compatible` 接入。DashScope 仍负责 embedding 和 RAG 检索。

这种拆分让聊天模型和向量化模型可以分别演进，后续替换模型时不需要重写业务工作流。

## 4. 结构化输出与 self-correction

路线生成和卡点细化都使用 Pydantic schema 做结构化校验。模型输出如果 JSON 解析失败或结构不符合预期，会进入 self-correction 流程。

self-correction 的目标不是提升内容质量评分，而是尽量把模型输出修复为可被程序消费的结构。超过配置次数后，系统返回可控错误，而不是让异常向页面层扩散。

## 5. 可观测性设计

V1 使用本地 JSONL 做轻量可观测性，不依赖外部观测平台。

当前记录三类 trace：

- `workflow_trace`：节点、阶段、耗时、错误类型。
- `model_call_log`：provider、模型、调用类型、耗时、重试信息、输入输出字符数。
- `retrieval_trace`：检索类型、过滤条件、召回数量、耗时、错误类型。

每次运行通过 `workflow_run_id` 串联，并可生成 `run_summary`。日志不保存完整 prompt、完整模型输出、API key 或认证请求头。

## 6. 外部服务稳定性治理

LLM 调用会区分错误类型：

- `timeout_error` / `connection_error` / `api_error`：有限重试。
- `auth_error` / `config_error` / `parse_error`：不重试。

RAG 检索失败当前不重试，而是记录 `retrieval_trace` 并返回可控 `error_message`。这样可以让 workflow 保持可解释的失败状态。

## 7. 回归门禁

项目提供 smoke check 作为本地回归门禁：

```bash
.venv/bin/python evals/run_smoke_check.py --mode local
```

local 模式不真实调用 DeepSeek / DashScope，适合日常开发后快速检查。当前封存前 local smoke check 结果为 11 passed / 0 failed。

真实链路验收使用：

```bash
.venv/bin/python evals/run_smoke_check.py --mode real
```

real 模式会真实调用外部 API，可能产生费用和网络等待，只适合阶段性验收。

## 8. 当前限制

- V1 不做多 Agent 协作。
- V1 不自动执行外部工具。
- V1 不支持用户上传知识库。
- 当前知识库规模有限，输出质量受知识覆盖影响。
- 当前日志为本地文件，尚未做日志轮转和集中化观测。
- 当前不宣称生产级高并发能力。

## 9. 后续演进方向

- FastAPI 服务化
- 用户历史记录
- 日志轮转
- LangSmith 接入
- 限流 / 缓存 / 队列
- Docker 部署
- 更完整的权限和安全治理
