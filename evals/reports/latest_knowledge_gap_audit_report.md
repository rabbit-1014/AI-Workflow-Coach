# P1.5a Evidence-driven Knowledge Gap Audit 报告

## 1. 本轮目标与边界

本轮只做知识库缺口审查：复用 P1 10 个 case 结果，并新增 10 个扩展 case 观察真实 with-RAG 输出。不修改 knowledge、prompt、workflow、retriever，也不进入 P2。

## 2. 上一版局部 patch 方案的弊端

- 只围绕 `shortdrama_close_success_01` 容易过拟合单个弱 case。
- 直接预设修改 `workflows.md` 和 `reference_workflow_patterns.md` 会跳过证据采集。
- P2 前需要先区分知识库缺口、检索错配、模型利用不足和灰区输入。

## 3. 当前 P1 结果复用情况

- 已读取: `D:\ai_projects\AI-Workflow-Coach\evals\reports\latest_real_quality_results.json`
- P1 case 总数: 10
- P1 route_generated: 7
- P1 failure_type 分布: {'none': 7, 'route_not_generated': 2, 'followup_required': 1}

## 4. 新增 10 个扩展 case 运行结果

| case_id | route_generated | final_stage | failure_type | retrieval_doc_count | route_context_chars | step_count | preliminary_quality_label | suspected_knowledge_gap |
|---|---:|---|---|---:|---:|---:|---|---|
| shortdrama_pilot_episode_01 | True | route_generated | none | 9 | 3937 | 6 | usable | unknown_pending_review |
| shortdrama_character_consistency_01 | True | route_generated | none | 9 | 3937 | 7 | usable | unknown_pending_review |
| shortdrama_storyboard_to_video_01 | True | route_generated | none | 9 | 3937 | 6 | usable | unknown_pending_review |
| shortdrama_voice_subtitle_edit_01 | True | route_generated | none | 9 | 3937 | 7 | usable | unknown_pending_review |
| shortdrama_beginner_fast_route_01 | True | route_generated | none | 9 | 3937 | 6 | usable | unknown_pending_review |
| content_xhs_series_01 | True | route_generated | none | 9 | 3704 | 6 | usable | unknown_pending_review |
| content_public_account_article_01 | True | route_generated | none | 9 | 3704 | 6 | usable | unknown_pending_review |
| learning_exam_review_01 | True | route_generated | none | 9 | 3845 | 7 | usable | unknown_pending_review |
| learning_vocab_memory_01 | True | route_generated | none | 9 | 3845 | 6 | usable | unknown_pending_review |
| boundary_tool_building_01 | False | task_analyzed | boundary_behavior | 0 | 0 | 0 | boundary | unknown_pending_review |

## 5. 综合 20 个 case 的知识库支撑观察

- P1.5a 新增 case 总数: 10
- P1.5a route_generated: 9
- P1.5a failure_type 分布: {'none': 9, 'boundary_behavior': 1}
- 读取 knowledge 文件: tools.md, workflows.md, blockages.md, reference_workflow_patterns.md

- AI 漫剧首集: {'total': 1, 'route_generated': 1, 'failure_types': {'none': 1}, 'avg_retrieval_doc_count': 9.0}
- AI 动漫短剧角色一致性: {'total': 1, 'route_generated': 1, 'failure_types': {'none': 1}, 'avg_retrieval_doc_count': 9.0}
- 短剧大纲到视频: {'total': 1, 'route_generated': 1, 'failure_types': {'none': 1}, 'avg_retrieval_doc_count': 9.0}
- AI 短剧后期合成: {'total': 1, 'route_generated': 1, 'failure_types': {'none': 1}, 'avg_retrieval_doc_count': 9.0}
- AI 动漫短剧新手最小闭环: {'total': 1, 'route_generated': 1, 'failure_types': {'none': 1}, 'avg_retrieval_doc_count': 9.0}
- 小红书图文系列: {'total': 1, 'route_generated': 1, 'failure_types': {'none': 1}, 'avg_retrieval_doc_count': 9.0}
- 公众号文章: {'total': 1, 'route_generated': 1, 'failure_types': {'none': 1}, 'avg_retrieval_doc_count': 9.0}
- 概率论复习计划: {'total': 1, 'route_generated': 1, 'failure_types': {'none': 1}, 'avg_retrieval_doc_count': 9.0}
- 英语单词复习流程: {'total': 1, 'route_generated': 1, 'failure_types': {'none': 1}, 'avg_retrieval_doc_count': 9.0}
- 灰区：短视频脚本生成器: {'total': 1, 'route_generated': 0, 'failure_types': {'boundary_behavior': 1}, 'avg_retrieval_doc_count': 0.0}

## 6. 弱 case 溯源

以下为需要人工重点复核的初步证据链。`initial_attribution` 是保守初筛，不是最终结论。

### shortdrama_close_success_01

- 来源: P1
- 用户目标: 我想做 AI 视频
- route_step_names: 明确内容定位与观众画像 / 策划视频选题与脚本框架 / 生成语音与字幕初稿 / 生成匹配视觉素材 / 合成与剪辑初版视频 / 发布前检查与平台适配 / 发布并记录基础数据
- retrieved_snippet_preview: tools/tools.md#3: ## 常用工具组合 ### ChatGPT / 通义千问 - 常用步骤：设定、剧情大纲、分镜脚本、提示词、字幕和标题。 - 适合产出：角色设定、世界观一句话、分镜表、镜头提示词、旁白。 - 轻量替代：豆包。 - 最小用法：要求输出分镜表，字 || workflows/workflows.md#10: ## 路径模式 1：AI 动漫短剧 - 适用场景：用户想做 AI / 动漫短剧，但尚未明确时长、集数、平台或风格。 - 目标产物：一条可启动的动漫短剧制作路线；具体时长、集数和发布平台应在第一步由用户确认。 - 新手建议：可以从较短版本开始 || workflows/workflows.md#9: ## 典型最小闭环 设定/IP 方向 -> 角色视觉一致性 -> 分镜/脚本 -> 生成/剪辑 -> 首轮验证/发布 最低闭环不是"生成几段好看的视频"，而是完成一条可测试的短剧作品；具体集数、时长和发布平台应由用户确认。 ---
- route_context_preview: # 工具知识片段
【片段 1】
source: tools
file_name: tools.md
section_index: 3
chunk_index: 20
content:
## 常用工具组合

### ChatGPT / 通义千问

- 常用步骤：设定、剧情大纲、分镜脚本、提示词、字幕和标题。
- 适合产出：角色设定、世界观一句话、分镜表、镜头提示词、旁白。
- 轻量替代：豆包。
- 最小用法：要求输出分镜表，字段包含镜头、时长、画面、动作、台词、提示词。

### 即梦 / Midjourney / 豆包图像

- 常用步骤：角色视觉、场景图、关键帧、封面图。
- 适合产出：角色
- 对应 knowledge 文件观察: {'tools.md': ['漫剧', '角色设定', '分镜脚本', '成片'], 'workflows.md': ['漫剧', '分镜脚本', '成片'], 'blockages.md': ['漫剧'], 'reference_workflow_patterns.md': ['漫剧', '成片']}
- 初步归因: unknown_pending_review
- 说明: Focus keyword evidence is weak or this was previously identified as usable-but-generic.

### learning_close_success_01

- 来源: P1
- 用户目标: 我想做个学习工具
- route_step_names: 设定目标与词库范围 / 设计学习卡片 / 生成练习任务 / 做即时反馈 / 设置复习规则 / 迭代与维护
- retrieved_snippet_preview: tools/tools.md#1: ## 常用工具组合 ### ChatGPT / 通义千问 - 常用步骤：目标诊断、学习计划、练习生成、即时反馈、错题解释。 - 适合产出：学习画像、每日任务、练习题、答题反馈、复盘建议。 - 轻量替代：豆包、Kimi。 - 最小用法：让模型 || workflows/workflows.md#3: ## 路径模式 2：AI 背单词工具 - 适用场景：用户想做背单词、词汇复习、错词回顾类小工具。 - 目标产物：一个能跑通“导入词汇 -> 练习 -> 反馈 -> 复习”的 MVP。 - 关键中间产物：词库字段、练习题样例、记忆反馈模板、错 || workflows/workflows.md#2: ## 路径模式 1：AI 学习计划 - 适用场景：用户想学习 AI、英语、考试科目、技能课程，但不知道如何安排。 - 目标产物：一份可执行的 7 天或 14 天学习计划。 - 关键中间产物：当前水平诊断、学习目标、每日任务表、练习清单、复盘
- route_context_preview: # 工具知识片段
【片段 1】
source: tools
file_name: tools.md
section_index: 1
chunk_index: 18
content:
## 常用工具组合

### ChatGPT / 通义千问

- 常用步骤：目标诊断、学习计划、练习生成、即时反馈、错题解释。
- 适合产出：学习画像、每日任务、练习题、答题反馈、复盘建议。
- 轻量替代：豆包、Kimi。
- 最小用法：让模型按“目标、当前水平、每日时间、练习、验收”输出，不只生成鼓励性计划。

### Kimi

- 常用步骤：资料阅读、课程笔记整理、长文总结、错题归纳。
- 适合产出：知识框
- 对应 knowledge 文件观察: {'tools.md': ['错词', '复习'], 'workflows.md': ['背单词', '例句', '错词', '复习'], 'blockages.md': ['背单词', '例句', '错词', '复习'], 'reference_workflow_patterns.md': []}
- 初步归因: unknown_pending_review
- 说明: Focus keyword evidence is weak or this was previously identified as usable-but-generic.

### boundary_tool_building_01

- 来源: P1.5a
- 用户目标: 我想做一个短视频脚本生成器。
- route_step_names: (none)
- retrieved_snippet_preview: (none)
- route_context_preview: 
- 对应 knowledge 文件观察: {'tools.md': ['短视频', '脚本', '工具'], 'workflows.md': ['短视频', '脚本', '工具'], 'blockages.md': ['短视频', '工具'], 'reference_workflow_patterns.md': ['短视频', '脚本']}
- 初步归因: ambiguous_case
- 说明: Boundary input should be reviewed separately from knowledge quality.

## 7. 建议的知识库补强方向

- `knowledge/tools.md`: 仅当扩展 case 显示工具角色不清时再补，不在本轮直接修改。
- `knowledge/workflows.md`: 若漫剧首集、公众号、概率论复习等扩展 case 输出泛化，可在 P1.5b 补最小 workflow 片段。
- `knowledge/blockages.md`: 若卡点类输入无法形成具体修正动作，可在 P1.5b 补对应卡点片段。
- `knowledge/reference_workflow_patterns.md`: 若边界或模式归类反复偏移，可在 P1.5b 补模式边界说明。

## 8. 范围外发现

- prompt、model、retriever、top-k、chunking、metadata filter、workflow 状态传递问题只记录，不在 P1.5a 修复。

## 9. 是否建议进入 P1.5b 知识库最小补强

需要 GPT / 人工基于本报告复核后决定。若多个 case 的证据链指向同一知识缺口，再进入 P1.5b。

## 10. 是否建议进入 P2 RAG Ablation

如果知识库缺口明显，建议先做 P1.5b；如果缺口不明显且 RAG 信号稳定，再进入 P2。

## 11. 是否建议 commit

本轮不自动 commit，也不建议立即 commit；等待 GPT 和人工审查。
