# AI Workflow Coach

一个面向 AI 工具使用场景的结构化工作流生成与卡点细化系统。

## 项目定位

AI Workflow Coach 不是普通聊天机器人，也不是万能 AI Agent。V1 的目标是帮助用户把模糊目标收口成更可执行的 AI 使用路线，并在用户卡住某一步时继续拆细。

当前系统主要做五件事：

- 根据用户目标生成可执行 AI 工作流路线
- 对模糊目标进行补问收口
- 在路线生成前做 RAG（检索增强生成）
- 在用户卡住某一步时做卡点细化
- 用 LangGraph 管理路线生成和卡点细化的状态流转

V1 边界：

- V1 不做多 Agent 协作
- V1 不做自动执行外部工具
- V1 不做用户知识库上传
- V1 不做复杂权限系统
- V1 不做生产级高并发

## 核心场景

当前重点场景是 AI 动漫短剧 / 短视频。系统会围绕创意拆解、素材准备、工具选择、流程推进和卡点处理，生成更适合执行的工作流路线。

系统也支持内容创作和学习辅助两类扩展场景。例如，用户可以用它拆解一条内容生产流程，或把学习目标转换为阶段化执行步骤。相比通用聊天，项目更强调“先把路线拆清，再把卡点拆细”。

## 核心流程

```text
用户输入目标
-> 任务理解
-> 必要时补问
-> close_success / close_partial / close_failed 收口
-> 路线生成前 RAG 检索
-> 结构化路线生成
-> 用户选择卡点步骤
-> 卡点细化前 RAG 检索
-> 结构化卡点建议生成
```

收口状态说明：

- `close_success`（收口成功）：用户目标已经足够明确，可以直接进入路线生成。
- `close_partial`（收口半成功）：用户补充信息仍不完整，但已经足够生成一条带假设和边界的路线。
- `close_failed`（收口失败）：目标仍过于模糊或缺少关键条件，系统返回可控提示，不继续强行生成路线。

## 技术栈

- Python
- Streamlit
- LangGraph
- LangChain
- Chroma
- DashScope embedding（用于向量化 / RAG）
- DeepSeek-V4-Flash / `openai_compatible`（用于聊天生成模型）
- Pydantic（结构化输出校验）
- JSONL logs（本地可观测日志）
- GitHub Actions（非网络回归门禁）

## 目录结构

当前项目目录可简化理解为：

```text
AI-Workflow-Coach/
├── app.py
├── config.py
├── prompts.py
├── schemas.py
├── requirements.txt
├── README.md
├── .github/
│   └── workflows/
│       └── regression.yml
├── docs/
│   ├── architecture.md
│   └── engineering_notes.md
├── graph/
│   ├── direction_options.py
│   ├── nodes.py
│   ├── state.py
│   └── workflow.py
├── services/
│   ├── blockage_solver.py
│   ├── llm_service.py
│   ├── rag_service.py
│   ├── route_generator.py
│   └── task_analyzer.py
├── vector_store/
│   ├── build_index.py
│   ├── retriever.py
│   └── chroma_db/
├── knowledge/
│   ├── blockages.md
│   ├── reference_workflow_patterns.md
│   ├── tools.md
│   └── workflows.md
├── utils/
│   ├── error_utils.py
│   ├── logger.py
│   ├── observability.py
│   ├── observability_report.py
│   └── persistence.py
└── evals/
    ├── run_smoke_check.py
    ├── run_regression_gate.py
    ├── run_real_quality_eval.py
    ├── run_knowledge_gap_audit.py
    ├── run_rag_ablation.py
    ├── reports/
    └── ...
```

重点模块：

- `graph/`：LangGraph 工作流、节点和状态定义。
- `services/`：RAG、LLM 调用、路线生成、卡点细化等服务封装。
- `vector_store/`：Chroma 索引构建和检索封装。
- `knowledge/`：本地 Markdown 知识库。
- `utils/`：错误分类、日志、可观测性、运行摘要和本地状态持久化。
- `evals/`：本地 smoke check、真实质量评估、知识库缺口审查、RAG 消融和回归门禁脚本。

## 模型供应商配置

当前聊天生成模型支持两类 provider：

- `dashscope`（通义千问原生协议）
- `openai_compatible`（OpenAI 兼容协议）

DeepSeek-V4-Flash 当前通过 `openai_compatible`（OpenAI 兼容协议）接入。DashScope 仍用于 embedding（向量化）和 RAG 检索。

`.env` 示例：

```env
CHAT_PROVIDER=openai_compatible
CHAT_MODEL_NAME=deepseek-v4-flash
CHAT_API_KEY=your_chat_api_key
CHAT_BASE_URL=https://api.deepseek.com

DASHSCOPE_API_KEY=your_dashscope_api_key
EMBEDDING_MODEL_NAME=text-embedding-v3

MAX_LLM_API_RETRIES=1
MAX_PARSE_CORRECTION_RETRIES=1
```

说明：

- `CHAT_API_KEY` 用于聊天生成模型。
- `DASHSCOPE_API_KEY` 用于 embedding（向量化）/ RAG（检索增强生成）。
- 不要把真实 API key 写入仓库。
- 可以参考上方变量创建本地 `.env`，其中只保留占位符或自己的本机配置。

## 可观测性与稳定性设计

### Observability（可观测性）

项目使用本地 JSONL 记录关键运行信息，便于定位工作流、模型调用和检索问题：

- `workflow_trace`：记录节点级状态、阶段、耗时和错误类型。
- `model_call_log`：记录模型 provider、模型名、调用类型、耗时、重试次数、输入输出字符数和是否触发 self-correction。
- `retrieval_trace`：记录检索类型、过滤条件、召回数量、耗时和错误类型。
- `workflow_run_id`：串联一次路线生成或卡点细化的运行编号。
- `run_summary`：从 trace / model call / retrieval 记录聚合出的运行摘要。

可观测日志不记录：

- 完整 prompt
- 完整模型输出
- API key
- 认证请求头

### Reliability（稳定性治理）

当前 V1 已加入轻量稳定性治理：

- JSON 解析失败会触发 self-correction（自我修正），让模型按结构化 schema 修复输出。
- LLM API 的 `timeout_error` / `connection_error` / `api_error` 会按配置有限重试。
- `auth_error` / `config_error` / `parse_error` 不重试，避免无意义重复调用。
- RAG 检索失败当前不重试，而是记录错误并返回可控 `error_message`，避免工作流直接崩溃。

## 运行方式

创建环境并安装依赖：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

然后参考上方变量创建 `.env`，填写自己的 `CHAT_API_KEY` 和 `DASHSCOPE_API_KEY`。不要提交真实 key。

第一次运行前，或更新 `knowledge/` 后，可以构建向量库：

```bash
python -m vector_store.build_index
```

启动页面：

```bash
streamlit run app.py
```

## 测试方式

### 本地回归门禁

```bash
python evals/run_regression_gate.py
```

说明：

- 不真实调用 DeepSeek / DashScope。
- 顺序运行 `py_compile`、反擅自假设检查、方向选择检查和本地 smoke check。
- 适合作为日常开发后的本地底线检查。
- GitHub Actions 复用同一门禁，但只验证非网络回归，不评估模型输出质量。

如只想运行本地 smoke check，也可以使用：

```bash
python evals/run_smoke_check.py --mode local
```

### 真实链路验收

```bash
python evals/run_smoke_check.py --mode real
```

说明：

- 会真实调用外部 API。
- 可能产生费用和网络等待。
- 用于阶段验收。
- 不适合每次小改都跑。

## 评估与回归体系

第二阶段工程增强主要用于回答两个问题：系统是否真的能生成可用路线，以及后续改动有没有破坏主链路。

- P1 Real Quality Evaluation：使用真实模型运行黄金样例，人工复核路线生成质量；该评估会调用真实 API，不进入 CI。
- P1.5a Knowledge Gap Audit：基于真实 case、检索片段和知识库内容，审查当前 knowledge 是否支撑核心场景。
- P2 RAG Ablation：对同一批 case 做 with-RAG / without-RAG 成对对比。当前结论是，RAG 主要提升工具推荐具体性和 grounding（依据锚定），但对减少泛化表达帮助有限。
- P3 Local Regression Gate + CI：提供非网络本地回归门禁，并接入 GitHub Actions，用于检查系统底线是否被改坏。

真实质量评估和 RAG 消融可以手动运行：

```bash
python evals/run_real_quality_eval.py --limit 10
python evals/run_rag_ablation.py --limit 9
```

这两类评估会调用真实 API，可能产生费用和等待时间，不作为 CI gate。

## 报告文件

当前评估报告保存在 `evals/reports/`：

- `evals/reports/latest_real_quality_report.md`
- `evals/reports/latest_knowledge_gap_audit_report.md`
- `evals/reports/latest_rag_ablation_report.md`

## 当前边界与后续计划

当前 V1 已完成：

- 主链路
- RAG
- LangGraph 状态流转
- 模型供应商抽象
- 输入收口
- self-correction
- 异常兜底
- 可观测性
- run summary
- 外部服务有限重试
- smoke check / regression gate
- 真实质量评估、知识库缺口审查和 RAG 消融基线

当前边界：

- 对于“用 AI 完成任务”和“开发 AI 工具”边界不清的输入，系统当前倾向于补问或方向选择；后续可以引入低置信度意图识别兜底。
- RAG 能提升工具推荐具体性和知识 grounding，但不能单独解决所有泛化表达问题。
- P1 / P2 属于手动真实评估，不适合放进 CI；CI 只做非网络回归门禁。

后续可扩展：

- 低置信度意图识别
- 固定 demo 样例和面试展示脚本
- FastAPI 服务化
- 用户历史记录
- 日志轮转
- LangSmith 接入
- 限流 / 缓存 / 队列
- Docker 部署
- 更完整的权限和安全治理
