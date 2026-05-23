# P2 RAG Ablation Report

P2 v1 是一轮真实成对对比基线，只提供规则初筛和证据，不声明统计显著，不作为最终质量结论。

- 运行时间: 2026-05-23T12:46:30
- Git commit: 8282cec
- total_pairs: 9
- pair_valid_count: 9
- pair_invalid_count: 0
- stopped_early: False
- stop_reason: 

## Core Summary

- core_ablation_cases 主结论摘要: {'valid_core_case_count': 8, 'preliminary_winner_distribution': {'with_rag': 7, 'tie': 1}, 'avg_named_tool_count_delta': 4.38, 'avg_expected_tool_hit_delta': 3.5, 'avg_focus_keyword_hit_delta': 0.25, 'avg_step_focus_delta': 0.12, 'avg_generic_phrase_delta': -0.38}

## Case Pair Table

| case_id | group | pair_valid | invalid_reason | with_docs | without_docs | preliminary_winner | tool_delta | focus_delta | step_delta | generic_reduction |
|---|---|---:|---|---:|---:|---|---:|---:|---:|---:|
| shortdrama_core_01 | core_ablation_cases | True |  | 9 | 0 | with_rag | 5 | 2 | 1 | 0 |
| shortdrama_direct_01 | core_ablation_cases | True |  | 9 | 0 | with_rag | 5 | 0 | 0 | 0 |
| shortdrama_pilot_episode_01 | core_ablation_cases | True |  | 9 | 0 | with_rag | 7 | 0 | 1 | 0 |
| shortdrama_character_consistency_01 | core_ablation_cases | True |  | 9 | 0 | tie | 2 | -1 | -1 | -2 |
| content_xhs_series_01 | core_ablation_cases | True |  | 9 | 0 | with_rag | 2 | 0 | 0 | 0 |
| content_public_account_article_01 | core_ablation_cases | True |  | 9 | 0 | with_rag | 6 | 1 | 0 | 0 |
| learning_exam_review_01 | core_ablation_cases | True |  | 9 | 0 | with_rag | 4 | 0 | 0 | -1 |
| learning_vocab_memory_01 | core_ablation_cases | True |  | 9 | 0 | with_rag | 4 | 0 | 0 | 0 |
| shortdrama_close_success_01 | diagnostic_cases | True |  | 9 | 0 | with_rag | 2 | 0 | -2 | 0 |

## 关键问题回答

### 同一批 case，with-RAG 和 without-RAG 的输出差异在哪里？

- 以有效 pair 的步骤名、工具命中、场景关键词命中和泛化短语数量做规则初筛；具体差异见下方逐 case 对照。
- `diagnostic_cases` 只用于观察已知弱点，不参与 RAG 整体有效性主结论。

### RAG 是否让工具推荐更具体？

- core 平均具名工具数量差: 4.38
- core 平均期望工具命中差: 3.5

### RAG 是否让步骤更贴近场景？

- core 平均场景关键词命中差: 0.25
- core 平均步骤名场景命中差: 0.12

### RAG 是否减少泛化废话？

- core 平均泛化短语减少量: -0.38
- 正数表示 with-RAG 比 without-RAG 更少出现泛化短语；负数表示更多。

## 逐 case 对照

### shortdrama_core_01 (core_ablation_cases)

- pair_valid: True
- invalid_reason: 
- preliminary_winner: with_rag（规则初筛，不是最终质量结论）
- with-RAG steps: 设定/IP 方向 / 角色视觉锁定 / 分镜脚本 / 生成镜头 / 剪辑发布验证
- without-RAG steps: 故事构思与脚本生成 / 角色与视觉风格设计 / 分镜与关键帧生成 / AI动画生成（主体制作） / 配音与音效合成 / 后期剪辑与渲染输出 / 发布与初步反馈记录
- pair_diff: {'named_tool_count_delta': 5, 'expected_tool_hit_delta': 5, 'focus_keyword_hit_delta': 2, 'generic_phrase_delta': 0, 'step_focus_delta': 1, 'with_rag_metrics': {'named_tool_count': 13, 'expected_tool_hits': 9, 'focus_keyword_hits': 6, 'step_focus_hits': 4, 'generic_phrase_count': 0}, 'without_rag_metrics': {'named_tool_count': 8, 'expected_tool_hits': 4, 'focus_keyword_hits': 4, 'step_focus_hits': 3, 'generic_phrase_count': 0}, 'preliminary_winner': 'with_rag'}

### shortdrama_direct_01 (core_ablation_cases)

- pair_valid: True
- invalid_reason: 
- preliminary_winner: with_rag（规则初筛，不是最终质量结论）
- with-RAG steps: 设定与角色锁定 / 角色视觉锁定 / 分镜脚本编写 / 生成短镜头素材 / 配音与字幕准备 / 剪辑、BGM与成片导出 / 发布验证与数据记录
- without-RAG steps: 确定角色设定与世界观基调 / 编写60秒剧本（含关键台词与动作） / 设计关键帧与画面描述（分镜清单） / 生成角色与场景图像素材 / 动画化：将静态图转为动态视频片段 / 配音、配乐与音效合成 / 剪辑合成并导出短视频
- pair_diff: {'named_tool_count_delta': 5, 'expected_tool_hit_delta': 4, 'focus_keyword_hit_delta': 0, 'generic_phrase_delta': 0, 'step_focus_delta': 0, 'with_rag_metrics': {'named_tool_count': 14, 'expected_tool_hits': 9, 'focus_keyword_hits': 7, 'step_focus_hits': 3, 'generic_phrase_count': 0}, 'without_rag_metrics': {'named_tool_count': 9, 'expected_tool_hits': 5, 'focus_keyword_hits': 7, 'step_focus_hits': 3, 'generic_phrase_count': 0}, 'preliminary_winner': 'with_rag'}

### shortdrama_pilot_episode_01 (core_ablation_cases)

- pair_valid: True
- invalid_reason: 
- preliminary_winner: with_rag（规则初筛，不是最终质量结论）
- with-RAG steps: 设定与角色设定 / 角色视觉锁定 / 分镜脚本 / 生成镜头素材 / 剪辑与配音 / 发布与首轮验证
- without-RAG steps: 角色与视觉风格设定 / 文案与叙事脚本编写 / 分镜脚本与镜头规划 / 生成关键帧/镜头画面 / 视频剪辑与音效合成 / 发布前检查与导出
- pair_diff: {'named_tool_count_delta': 7, 'expected_tool_hit_delta': 6, 'focus_keyword_hit_delta': 0, 'generic_phrase_delta': 0, 'step_focus_delta': 1, 'with_rag_metrics': {'named_tool_count': 13, 'expected_tool_hits': 9, 'focus_keyword_hits': 6, 'step_focus_hits': 3, 'generic_phrase_count': 0}, 'without_rag_metrics': {'named_tool_count': 6, 'expected_tool_hits': 3, 'focus_keyword_hits': 6, 'step_focus_hits': 2, 'generic_phrase_count': 0}, 'preliminary_winner': 'with_rag'}

### shortdrama_character_consistency_01 (core_ablation_cases)

- pair_valid: True
- invalid_reason: 
- preliminary_winner: tie（规则初筛，不是最终质量结论）
- with-RAG steps: 定义故事核心与角色锁定卡 / 生成角色基准图与参考集 / 编写分镜脚本与镜头拆解 / 生成镜头片段（图生视频） / 剪辑、配音与字幕合成 / 发布验证与迭代记录
- without-RAG steps: 角色视觉定义与一致性锚点构建 / 分镜脚本与关键帧设计 / 角色-场景一致性生成（逐镜头输出） / 帧序列动画化与运动一致性控制 / 音频与字幕合成 / 最终剪辑与发布验证
- pair_diff: {'named_tool_count_delta': 2, 'expected_tool_hit_delta': 4, 'focus_keyword_hit_delta': -1, 'generic_phrase_delta': -2, 'step_focus_delta': -1, 'with_rag_metrics': {'named_tool_count': 11, 'expected_tool_hits': 8, 'focus_keyword_hits': 5, 'step_focus_hits': 2, 'generic_phrase_count': 2}, 'without_rag_metrics': {'named_tool_count': 9, 'expected_tool_hits': 4, 'focus_keyword_hits': 6, 'step_focus_hits': 3, 'generic_phrase_count': 0}, 'preliminary_winner': 'tie'}

### content_xhs_series_01 (core_ablation_cases)

- pair_valid: True
- invalid_reason: 
- preliminary_winner: with_rag（规则初筛，不是最终质量结论）
- with-RAG steps: 锁定选题与受众 / 规划正文结构 / 生成配图/素材清单 / 包装标题与封面文案 / 正文草稿与文案润色 / 发布与复盘计划
- without-RAG steps: 选题方向与内容框架规划 / 单篇标题与正文生成 / 封面文案与视觉提示生成 / 内容排版与细节优化 / 多篇批量生产与待发布清单整理 / 发布前检查与风险规避
- pair_diff: {'named_tool_count_delta': 2, 'expected_tool_hit_delta': 2, 'focus_keyword_hit_delta': 0, 'generic_phrase_delta': 0, 'step_focus_delta': 0, 'with_rag_metrics': {'named_tool_count': 8, 'expected_tool_hits': 6, 'focus_keyword_hits': 7, 'step_focus_hits': 5, 'generic_phrase_count': 0}, 'without_rag_metrics': {'named_tool_count': 6, 'expected_tool_hits': 4, 'focus_keyword_hits': 7, 'step_focus_hits': 5, 'generic_phrase_count': 0}, 'preliminary_winner': 'with_rag'}

### content_public_account_article_01 (core_ablation_cases)

- pair_valid: True
- invalid_reason: 
- preliminary_winner: with_rag（规则初筛，不是最终质量结论）
- with-RAG steps: 明确受众与选题 / 收集素材与案例 / 搭建正文结构 / 生成正文草稿 / 修改与优化（去除AI感） / 包装标题与封面 / 发布与复盘
- without-RAG steps: 选题与读者痛点定位 / 生成文章大纲与结构 / 逐段生成正文内容 / 优化标题、金句与排版 / 撰写开头与结尾引导互动 / 最终检查与发布准备
- pair_diff: {'named_tool_count_delta': 6, 'expected_tool_hit_delta': 1, 'focus_keyword_hit_delta': 1, 'generic_phrase_delta': 0, 'step_focus_delta': 0, 'with_rag_metrics': {'named_tool_count': 11, 'expected_tool_hits': 4, 'focus_keyword_hits': 7, 'step_focus_hits': 3, 'generic_phrase_count': 0}, 'without_rag_metrics': {'named_tool_count': 5, 'expected_tool_hits': 3, 'focus_keyword_hits': 6, 'step_focus_hits': 3, 'generic_phrase_count': 0}, 'preliminary_winner': 'with_rag'}

### learning_exam_review_01 (core_ablation_cases)

- pair_valid: True
- invalid_reason: 
- preliminary_winner: with_rag（规则初筛，不是最终质量结论）
- with-RAG steps: 目标诊断与学习画像 / 拆解概率论知识模块 / 生成每日任务表（10天） / 题型训练与即时反馈 / 错题整理与隔日复习 / 复盘迭代与最终总结
- without-RAG steps: 制定10天复习大纲 / 生成每日知识点梳理笔记 / 生成题型训练与解答 / 错题复盘与薄弱点分析 / 综合模拟测试与冲刺
- pair_diff: {'named_tool_count_delta': 4, 'expected_tool_hit_delta': 3, 'focus_keyword_hit_delta': 0, 'generic_phrase_delta': -1, 'step_focus_delta': 0, 'with_rag_metrics': {'named_tool_count': 7, 'expected_tool_hits': 6, 'focus_keyword_hits': 6, 'step_focus_hits': 5, 'generic_phrase_count': 1}, 'without_rag_metrics': {'named_tool_count': 3, 'expected_tool_hits': 3, 'focus_keyword_hits': 6, 'step_focus_hits': 5, 'generic_phrase_count': 0}, 'preliminary_winner': 'with_rag'}

### learning_vocab_memory_01 (core_ablation_cases)

- pair_valid: True
- invalid_reason: 
- preliminary_winner: with_rag（规则初筛，不是最终质量结论）
- with-RAG steps: 1. 定义词库与用户画像 / 2. 设计学习卡片模板 / 3. 生成练习任务（例句+测验） / 4. 实现即时反馈与错因分析 / 5. 设置错词复习规则 / 6. 闭环验证与迭代
- without-RAG steps: 导入待复习单词列表 / 为每个单词生成例句 / 生成测验题目（选择题/填空题） / 用户作答并记录结果 / 识别并收集错题
- pair_diff: {'named_tool_count_delta': 4, 'expected_tool_hit_delta': 3, 'focus_keyword_hit_delta': 0, 'generic_phrase_delta': 0, 'step_focus_delta': 0, 'with_rag_metrics': {'named_tool_count': 7, 'expected_tool_hits': 6, 'focus_keyword_hits': 6, 'step_focus_hits': 4, 'generic_phrase_count': 0}, 'without_rag_metrics': {'named_tool_count': 3, 'expected_tool_hits': 3, 'focus_keyword_hits': 6, 'step_focus_hits': 4, 'generic_phrase_count': 0}, 'preliminary_winner': 'with_rag'}

### shortdrama_close_success_01 (diagnostic_cases)

- pair_valid: True
- invalid_reason: 
- preliminary_winner: with_rag（规则初筛，不是最终质量结论）
- with-RAG steps: 设定首集方向与主角 / 角色视觉锁定 / 分镜脚本制作 / 生成镜头素材 / 剪辑与配音 / 首集发布验证
- without-RAG steps: 角色设定与角色卡生成 / 30秒剧本/对白草稿 / 分镜脚本制作 / 视觉素材生成（角色、背景、道具） / 动画/剪辑合成（首集成片） / 音效与配音制作 / 输出与发布准备
- pair_diff: {'named_tool_count_delta': 2, 'expected_tool_hit_delta': 5, 'focus_keyword_hit_delta': 0, 'generic_phrase_delta': 0, 'step_focus_delta': -2, 'with_rag_metrics': {'named_tool_count': 10, 'expected_tool_hits': 8, 'focus_keyword_hits': 5, 'step_focus_hits': 2, 'generic_phrase_count': 0}, 'without_rag_metrics': {'named_tool_count': 8, 'expected_tool_hits': 3, 'focus_keyword_hits': 5, 'step_focus_hits': 4, 'generic_phrase_count': 0}, 'preliminary_winner': 'with_rag'}

## 结论边界

- 本报告只记录 P2 v1 单轮真实成对对比，不声明统计显著。
- 如果 without-RAG 在个别 case 表现更好，只记录发现，不修改代码。
- 如果后续要做最终结论，需要人工复核核心 case 输出全文。
