# P1 Real Quality Evaluation Baseline

P1 real quality eval is manual-only and should not be used as CI gate.
P1 真实质量评估仅用于手动评估，不应作为 CI（持续集成）门禁。

- 运行时间: 2026-05-22T17:34:40
- Git commit: 8282cec
- 运行模式: real manual eval
- case 总数: 10
- route_generated 数量: 7
- schema_valid 数量: 7
- 平均 latency_ms: 28460.7
- failure_type 分布: {'none': 7, 'route_not_generated': 2, 'followup_required': 1}

## Case 明细

| case_id | 场景 | final_stage | route_generated | schema_valid | step_count | latency_ms | retrieval_doc_count | failure_type |
|---|---|---:|---:|---:|---:|---:|---:|---|
| shortdrama_core_01 | AI 动漫短剧 | route_generated | True | True | 5 | 38656 | 9 | none |
| shortdrama_direct_01 | AI 动漫短剧 | route_generated | True | True | 6 | 38991 | 9 | none |
| shortdrama_close_success_01 | AI 漫剧首集 | route_generated | True | True | 7 | 58495 | 9 | none |
| short_video_script_01 | AI 短视频 | direction_choice_required | False | False | 0 | 30 | 0 | route_not_generated |
| shortdrama_fallback_01 | AI 短剧 fallback | direction_choice_required | False | False | 0 | 31 | 0 | route_not_generated |
| content_direct_01 | 小红书内容 | route_generated | True | True | 5 | 31045 | 9 | none |
| content_close_success_01 | 内容生产流程 | route_generated | True | True | 6 | 33243 | 9 | none |
| learning_direct_01 | 学习计划 | route_generated | True | True | 6 | 41460 | 9 | none |
| learning_close_success_01 | 背单词工具 | route_generated | True | True | 6 | 42647 | 9 | none |
| generic_ai_something_01 | 模糊边界 | task_analyzed | False | False | 0 | 9 | 0 | followup_required |

## Route Step Names 摘要

- shortdrama_core_01: 设定/IP方向确认 / 角色视觉锁定 / 分镜脚本编写 / 生成镜头片段 / 剪辑配音与发布验证
- shortdrama_direct_01: 设定与IP方向确认 / 角色视觉锁定 / 分镜脚本编写 / 生成镜头素材 / 配音与字幕制作 / 剪辑与发布验证
- shortdrama_close_success_01: 明确内容定位与观众画像 / 策划视频选题与脚本框架 / 生成语音与字幕初稿 / 生成匹配视觉素材 / 合成与剪辑初版视频 / 发布前检查与平台适配 / 发布并记录基础数据
- short_video_script_01: (none)
- shortdrama_fallback_01: (none)
- content_direct_01: 1. 选题与受众定位 / 2. 搭建正文结构 / 3. 生成配图与素材 / 4. 包装标题与封面 / 5. 发布与数据记录
- content_close_success_01: 明确受众与选题方向 / 批量生成正文草稿 / 生成多版本标题与封面文案 / 配图/视觉素材生产 / 发布前检查与排期 / 发布与数据复盘模板
- learning_direct_01: 目标诊断与学习画像 / 拆学习模块 / 生成14天每日任务表 / 设计单词复习卡片与练习 / 设计阅读练习与AI即时反馈 / 搭建打卡表与复盘模板
- learning_close_success_01: 设定目标与词库范围 / 设计学习卡片 / 生成练习任务 / 做即时反馈 / 设置复习规则 / 迭代与维护
- generic_ai_something_01: (none)

## Retrieval 摘要

- shortdrama_core_01: doc_count=9, sources=tools, workflows, blockages
- shortdrama_direct_01: doc_count=9, sources=tools, workflows, blockages
- shortdrama_close_success_01: doc_count=9, sources=tools, workflows, blockages
- short_video_script_01: doc_count=0, sources=(none)
- shortdrama_fallback_01: doc_count=0, sources=(none)
- content_direct_01: doc_count=9, sources=tools, workflows, blockages
- content_close_success_01: doc_count=9, sources=tools, workflows, blockages
- learning_direct_01: doc_count=9, sources=tools, workflows, blockages
- learning_close_success_01: doc_count=9, sources=tools, workflows, blockages
- generic_ai_something_01: doc_count=0, sources=(none)

## 人工评分字段说明

- manual_tool_fit_score: 工具匹配，0/1/2/null
- manual_actionability_score: 可执行性，0/1/2/null
- manual_specificity_score: 具体程度，0/1/2/null
- manual_assumption_control_score: 假设控制，0/1/2/null
- manual_overall_quality_score: 总体质量，0/1/2/null

## 下一步建议

- 先人工复盘 `manual_*` 字段，不要把本报告接入 CI。
- 如果 route 质量稳定，再进入 P2 RAG Ablation。
- 如果出现 retrieval_doc_count 为 0 或明显跑偏，优先复盘知识库和检索片段。
- 如果出现 schema_failure/model_failure，再单独开修复任务。
