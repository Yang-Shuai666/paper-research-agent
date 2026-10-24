# Answer Evaluation: answer_eval_no_expansion

- Generated: 2026-10-24T04:45:53+00:00
- Questions: 30 (26 answerable, 4 unanswerable)
- Retrieval: hybrid + query rewrite + rerank, top-6
- Context expansion: False

| Group | N | Correctness (0-2) | Complete | Faithfulness (0-2) | Citation support (0-2) | Refusal accuracy |
|---|---:|---:|---:|---:|---:|---:|
| factoid | 13 | 1.62 | 0.769 | 2.00 | 2.00 | 0.846 |
| method | 7 | 1.71 | 0.714 | 2.00 | 2.00 | 1.000 |
| multi_hop | 3 | 1.33 | 0.333 | 2.00 | 2.00 | 1.000 |
| cross_paper | 3 | 1.00 | 0.333 | 2.00 | 1.33 | 0.667 |
| unanswerable | 4 | 2.00 | 1.000 | 2.00 | 2.00 | 1.000 |
| **overall** | **30** | **1.60** | **0.700** | **2.00** | **1.93** | **0.900** |

- Latency: retrieval P50 200 ms, P95 227 ms; generation P50 2140 ms, P95 10646 ms
- Tokens: 23889 prompt, 13110 completion

## Bad cases

### q05 (factoid)
- Question: MAIC 初始预设的四类同学智能体分别是什么？
- Judge: correctness=0, faithfulness=2, citation_support=2, refusal=false_refusal
- Reason: 问题可回答，但系统答案以信息不足为由拒绝，未给出四类同学智能体的完整名称。
- Invalid citations: []
- Answer: 信息不足：提供的片段仅能确认初始预设的同学智能体共四类 [1][2]，且其中一类为“Class Clown (TI, EC, CM)” [1]；其余三类同学智能体的名称在片段中未给出，因此无法确定四类分别是什么。
### q06 (multi_hop)
- Question: 原始教学材料在 MAIC 的 Read 阶段会经历哪些处理，最终变成智能体可用的知识？
- Judge: correctness=1, faithfulness=2, citation_support=2, refusal=correct
- Reason: 答案基于片段正确描述了Read阶段的预处理、多模态抽取和结构化知识库，但遗漏了查询生成、开放式RAG及最终生成教学脚本供智能体使用等关键环节，且误称信息不足。
- Invalid citations: []
- Answer: 结论：按片段可确认，原始教学材料在 Read 阶段先被预处理，再通过抽取函数处理；多模态内容会生成“全面且具教学意识的描述”，同时通过知识抽取被组织为结构化知识库并跨模态建立分类关系，最终形成结构化资源集 [1]。该结构化资源集是后续 Plan 阶段所基于的“高度结构化资源” [5][4]。但片段未明确说明该资源集进一步转化为“智能体可用知识”的完整接口或机制。

处理流程与产物：

1. 上传资源先经过预处理，随后 MAIC-Craft 使用抽取函数完成 Read 阶段 [1]。
2. 多模态内容由基于 ML-LM 的方法处理，生成全面且具教学意识的描述 [1]。
3. 同时，MAIC-Cr
### q08 (factoid)
- Question: MAIC 的实证研究持续多长时间，在什么课程中开展？
- Judge: correctness=0, faithfulness=2, citation_support=2, refusal=false_refusal
- Reason: 问题可回答，但系统以信息不足拒绝作答，未给出TGAI课程和两个月实验干预这一关键信息。
- Invalid citations: []
- Answer: 信息不足：提供的片段仅说明开展了大规模用户实证研究并获得清华大学伦理批准 [3]，以及最终有319名学生完成课程 [1][6]，但没有给出研究的持续时长和具体课程名称。
### q13 (method)
- Question: Modular RAG 引入了哪些新的专用模块？
- Judge: correctness=1, faithfulness=2, citation_support=2, refusal=correct
- Reason: 系统答案依据片段正确指出了Search及Rewrite-Retrieve-Read中的重写模块，并说明片段未给出完整清单，但缺少参考答案中的RAG-Fusion、Memory、Routing、Predict、Task Adapter等关键模块，因此部分正确但不完整。
- Invalid citations: []
- Answer: 结论：就所给片段而言，Modular RAG 明确命名的专用模块包括 **Search module（搜索模块）**，以及 Rewrite-Retrieve-Read 模型中的 **rewriting module（重写模块）**；片段没有给出完整的新模块清单。

依据：Search module 可针对特定场景，通过 LLM 生成的代码和查询语言，直接跨搜索引擎、数据库、知识图谱等数据源进行搜索 [1]。Modular RAG 通过集成新模块或调整现有模块间交互流来扩展灵活性 [4]；其中 Rewrite-Retrieve-Read 通过 rewriting module 和 LM-feed
### q14 (method)
- Question: RAG 综述中提到的查询转换（Query Transformation）方法有哪些代表？
- Judge: correctness=1, faithfulness=2, citation_support=2, refusal=correct
- Reason: 答案正确提到 Query Rewrite 和 RRR，但遗漏了参考答案中的 HyDE 与 Step-back Prompting 等关键代表。
- Invalid citations: []
- Answer: 查询转换方法的明确代表是 **Query Rewrite（查询重写）**，包括用 LLM 提示进行查询重写，以及使用专门的小型语言模型，如 **RRR（Rewrite-retrieve-read）** [1]。  
另外，片段还提到**递归检索（Recursive retrieval）**会逐步细化用户查询并将问题拆解为子问题，但片段未将其明确归类为“查询转换” [3]。
### q16 (factoid)
- Question: RAG 综述列举了哪些评估框架或工具？
- Judge: correctness=1, faithfulness=2, citation_support=2, refusal=correct
- Reason: 答案基本列出了片段中的主要评估框架和工具且有引用支撑，但遗漏参考答案中的 RAGQuestEval，因此仅部分完整。
- Invalid citations: []
- Answer: 结论：片段中明确列举的评估基准/框架包括 **RGB、RECALL、CRUD**；评估工具包括 **RAGAS、ARES、TruLens**，并另提到 **RALLE** 是用于 RAG 应用自动评估的工具 [2][5][6]。

依据：
- RGB、RECALL 和 CRUD 被列为评估 RAG 模型关键能力的代表性基准 [2]。
- RAGAS、ARES 和 TruLens 被列为使用 LLM 判定质量分数的先进自动化工具 [1][2]。
- 评估框架汇总表中也列出了 RGB、RECALL、RAGAS、ARES、TruLens [6]。
- RALLE 被描述为面向 RAG 应用自动评估、
### q17 (multi_hop)
- Question: RAG 中的“Lost in the middle”问题出现在哪个阶段？综述建议如何缓解？
- Judge: correctness=1, faithfulness=2, citation_support=2, refusal=correct
- Reason: 答案正确解释了“Lost in the middle”问题及其一般性缓解方向，但未给出参考答案中的重排序、上下文选择/压缩等具体措施，故仅部分完整。
- Invalid citations: []
- Answer: 结论：“Lost in the middle”是过长上下文导致 LLM 在最终生成时倾向只关注长文本开头和结尾、遗忘中间内容的问题；综述在 Context Curation 部分建议通过进一步处理检索内容来缓解，但片段未展开具体缓解措施。[1]

依据：片段指出冗余信息会干扰 LLM 最终生成，过长上下文也会导致该问题；因此在 RAG 系统中通常需要进一步处理检索内容。[1]
### q25 (cross_paper)
- Question: MAIC-Craft 的 Open-Ended RAG 与 RAG 综述中的 Advanced/Modular RAG 有哪些对应关系？
- Judge: correctness=0, faithfulness=2, citation_support=0, refusal=false_refusal
- Reason: 问题可回答且参考答案给出了对应关系，系统答案却以信息不足拒绝，属于错误拒答。
- Invalid citations: []
- Answer: 信息不足：所提供的论文片段未包含 MAIC-Craft 或 Open-Ended RAG 的任何定义、架构或流程描述，也未说明其与 Advanced/Modular RAG 的对应关系，因此无法依据片段建立对应关系。
### q26 (cross_paper)
- Question: 三篇论文分别如何评估各自系统？
- Judge: correctness=1, faithfulness=2, citation_support=2, refusal=correct
- Reason: 答案引证有效且基本忠实，但遗漏了AutoGen基准/应用案例、RAG具体评估维度与框架、MAIC人工评估和两个月真实教学实验等关键事实。
- Invalid citations: []
- Answer: 结论：AutoGen 的评估方式是每个问题测试三次，并报告问题解决正确率与失败原因 [3]；OpenMAIC 从学习表现、技术接受度、自我报告高阶思维三方面评估 [4]，并采用内容理解、长上下文连贯性、教学设计三项自动化指标评估生成脚本 [6]；RAG 综述主要回顾 RAG 的评估框架、基准、下游任务与评估方法 [1][2][5]，片段未提供其自身系统的具体评估实验 [1][5]。

依据：
- AutoGen：每个基于 LLM 的系统在每个问题上测试三次，表格报告问题解决正确率并总结失败原因，例如 AutoGen 为 3/3，AutoGPT 为 0/3 [3]。
- OpenMAIC：评估从
