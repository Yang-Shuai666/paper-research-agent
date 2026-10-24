# Answer Evaluation: answer_eval

- Generated: 2026-10-24T04:42:04+00:00
- Questions: 30 (26 answerable, 4 unanswerable)
- Retrieval: hybrid + query rewrite + rerank, top-6
- Context expansion: True

| Group | N | Correctness (0-2) | Complete | Faithfulness (0-2) | Citation support (0-2) | Refusal accuracy |
|---|---:|---:|---:|---:|---:|---:|
| factoid | 13 | 1.92 | 0.923 | 2.00 | 2.00 | 1.000 |
| method | 7 | 1.86 | 0.857 | 2.00 | 2.00 | 1.000 |
| multi_hop | 3 | 1.67 | 0.667 | 2.00 | 2.00 | 1.000 |
| cross_paper | 3 | 1.00 | 0.333 | 2.00 | 1.33 | 0.333 |
| unanswerable | 4 | 2.00 | 1.000 | 2.00 | 2.00 | 1.000 |
| **overall** | **30** | **1.80** | **0.833** | **2.00** | **1.93** | **0.933** |

- Latency: retrieval P50 198 ms, P95 1528 ms; generation P50 1737 ms, P95 9083 ms
- Tokens: 50063 prompt, 11778 completion

## Bad cases

### q06 (multi_hop)
- Question: 原始教学材料在 MAIC 的 Read 阶段会经历哪些处理，最终变成智能体可用的知识？
- Judge: correctness=1, faithfulness=2, citation_support=2, refusal=correct
- Reason: 答案涵盖多模态抽取和知识库构建等核心处理，但遗漏了参考答案中的查询生成、开放式 RAG 及教学脚本生成等关键环节，因此仅部分正确。
- Invalid citations: []
- Answer: 结论：原始教学材料在 MAIC 的 Read 阶段会先被预处理，再经过多模态内容抽取、教学化描述生成和知识抽取，最终形成带分类关系的结构化知识库与结构化资源集；这些处理后的内容在后续 Plan 阶段被用于构建 AI 教学智能体。[1][2][3][5][6]

依据如下：

- MAIC-Craft 会对上传资源进行预处理，并通过抽取函数完成 Read 阶段；多模态内容由基于 MLLM 的方法处理，生成全面且具有教学意识的描述。[1]
- 其实现将视觉语言模型用于视觉处理、自动语音识别用于音频转写、文档解析器用于文本抽取，并统一在同一处理流水线中。[2]
- 系统用 MLLM 捕捉不同模态内容
### q13 (method)
- Question: Modular RAG 引入了哪些新的专用模块？
- Judge: correctness=1, faithfulness=2, citation_support=2, refusal=correct
- Reason: 答案正确列出检索片段中出现的 Search、Memory、Task Adapter 模块，但缺少参考答案中的 Routing 和 Predict，且未将 RAG-Fusion 计为模块；引用均有片段支撑。
- Invalid citations: []
- Answer: 结论：片段中明确以“module”命名的 Modular RAG 新专用模块主要有 **Search 模块、Memory 模块和 Task Adapter 模块** [1][3][13]。

依据如下：  
- **Search 模块**：用于适配特定场景，支持跨搜索引擎、数据库、知识图谱等多种数据源直接搜索，并使用 LLM 生成的代码和查询语言 [1][3]；片段还提到“添加搜索模块用于相似性搜索” [4]。  
- **Memory 模块**：利用 LLM 的记忆来引导检索，构建无界记忆池 [3]。  
- **Task Adapter 模块**：面向不同下游任务定制 RAG，自动化零样本
### q16 (factoid)
- Question: RAG 综述列举了哪些评估框架或工具？
- Judge: correctness=1, faithfulness=2, citation_support=2, refusal=correct
- Reason: 系统答案基于片段正确列出了部分评估工具和基准，但遗漏了参考答案中的 RAGQuestEval，故部分正确。
- Invalid citations: []
- Answer: 片段中明确提到的 RAG 评估工具/框架主要有：

1. **RAGAS、ARES、TruLens**：这些是被描述为利用 LLM 判定质量分数的先进自动化工具 [1][2]。
2. **RALLE**：被描述为用于 RAG 应用自动评估的工具，其评估基于任务特定指标 [13]。

此外，片段还提到 **RGB、RECALL、CRUD** 等基准（benchmarks），用于评估 RAG 模型的关键能力 [2]；但它们被表述为基准而非工具。片段提到 Table IV 汇总了评估框架，但未给出 Table IV 的完整内容 [1]。
### q25 (cross_paper)
- Question: MAIC-Craft 的 Open-Ended RAG 与 RAG 综述中的 Advanced/Modular RAG 有哪些对应关系？
- Judge: correctness=0, faithfulness=2, citation_support=0, refusal=false_refusal
- Reason: 问题标注为可回答，参考答案可基于片段中 Advanced RAG 的检索前查询优化与检索后处理、以及 Modular RAG 的模块化编排进行对应分析；系统却整体拒答，虽然片段确实未提及 MAIC-Craft，但该拒答仍属误拒。
- Invalid citations: []
- Answer: 信息不足：提供的片段中没有出现“MAIC-Craft”或“Open-Ended RAG”的任何描述，因此无法判断其与 Advanced/Modular RAG 的对应关系。缺少的是关于 MAIC-Craft 的 Open-Ended RAG 的架构、模块构成与流程的片段说明。
### q26 (cross_paper)
- Question: 三篇论文分别如何评估各自系统？
- Judge: correctness=1, faithfulness=2, citation_support=2, refusal=false_refusal
- Reason: 答案虽正确指出片段仅覆盖RAG综述与AutoGen的部分评估信息，但问题可回答且参考答案完整，仍未给出三篇论文各自评估方法，属错误拒答。
- Invalid citations: []
- Answer: 信息不足：提供的片段只涉及 rag_survey.pdf（其内容是综述 RAG 的评估框架、基准与指标，而非说明评估“自身系统”的方法）[1][6][12] 和 autogen.pdf（对每个问题测试三次，并统计问题求解正确性与失败原因）[16]；缺少第三篇论文的片段及其评估方法，因此无法分别回答三篇论文各自如何评估各自系统。
