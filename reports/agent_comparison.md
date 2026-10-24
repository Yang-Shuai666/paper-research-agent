# Single-shot RAG vs Agent: agent_comparison

- Generated: 2026-10-24T05:27:19+00:00
- Model: `deepseek-flash`
- Questions: 10 (q05, q06, q13, q17, q23, q24, q25, q26, q27, q30)
- Single-shot: hybrid + query rewrite + rerank + neighbor expansion, top-6
- Agent: 4 tools, max 6 tool calls, evidence refs [n]

## Aggregate

| Mode | N | Correctness (0-2) | Complete | Faithfulness (0-2) | Citation support (0-2) | Refusal accuracy | Avg steps | Avg latency (ms) | Prompt tokens | Completion tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| single-shot | 10 | 1.50 | 0.600 | 1.90 | 1.90 | 0.800 | 0.0 | 5021 | 17361 | 6447 |
| agent | 10 | 1.70 | 0.700 | 2.00 | 2.00 | 1.000 | 4.1 | 9915 | 120173 | 11815 |

### Single-shot by question type

| Group | N | Correctness (0-2) | Complete | Faithfulness (0-2) | Citation support (0-2) | Refusal accuracy |
|---|---:|---:|---:|---:|---:|---:|
| factoid | 1 | 2.00 | 1.000 | 2.00 | 2.00 | 1.000 |
| method | 1 | 1.00 | 0.000 | 1.00 | 1.00 | 1.000 |
| multi_hop | 3 | 1.67 | 0.667 | 2.00 | 2.00 | 1.000 |
| cross_paper | 3 | 1.00 | 0.333 | 2.00 | 2.00 | 0.333 |
| unanswerable | 2 | 2.00 | 1.000 | 2.00 | 2.00 | 1.000 |
| **overall** | **10** | **1.50** | **0.600** | **1.90** | **1.90** | **0.800** |

### Agent by question type

| Group | N | Correctness (0-2) | Complete | Faithfulness (0-2) | Citation support (0-2) | Refusal accuracy |
|---|---:|---:|---:|---:|---:|---:|
| factoid | 1 | 2.00 | 1.000 | 2.00 | 2.00 | 1.000 |
| method | 1 | 2.00 | 1.000 | 2.00 | 2.00 | 1.000 |
| multi_hop | 3 | 1.67 | 0.667 | 2.00 | 2.00 | 1.000 |
| cross_paper | 3 | 1.33 | 0.333 | 2.00 | 2.00 | 1.000 |
| unanswerable | 2 | 2.00 | 1.000 | 2.00 | 2.00 | 1.000 |
| **overall** | **10** | **1.70** | **0.700** | **2.00** | **2.00** | **1.000** |

## Per-question results

| ID | Type | Single correctness | Agent correctness | Δ | Single citations (valid/invalid) | Agent citations (valid/invalid) | Agent steps | Agent stop |
|---|---|---:|---:|---:|---:|---:|---|---|
| q05 | factoid | 2 | 2 | +0 | 4/0 | 4/0 | search_library → read_page | answer |
| q06 | multi_hop | 1 | 1 | +0 | 6/0 | 10/0 | search_library → search_library → read_page → read_page | answer |
| q13 | method | 1 | 2 | +1 | 5/0 | 9/0 | search_library → search_library → read_page → read_page | answer |
| q17 | multi_hop | 2 | 2 | +0 | 4/0 | 11/0 | search_library → search_library → read_page | answer |
| q23 | multi_hop | 2 | 2 | +0 | 8/0 | 11/0 | search_library → search_library → read_page | answer |
| q24 | cross_paper | 2 | 2 | +0 | 13/0 | 25/0 | compare_papers → compare_papers → read_page → search_library → read_page | answer |
| q25 | cross_paper | 0 | 1 | +1 | 4/0 | 20/0 | compare_papers → search_library → read_page → read_page → read_page → read_page | max_steps |
| q26 | cross_paper | 1 | 1 | +0 | 3/0 | 37/0 | compare_papers → search_library → read_page → read_page → read_page → search_library | max_steps |
| q27 | unanswerable | 2 | 2 | +0 | 2/0 | 7/0 | search_library → search_library → search_library → search_library → read_page → search_library | max_steps |
| q30 | unanswerable | 2 | 2 | +0 | 4/0 | 5/0 | search_library → search_library | answer |

## Where the Agent helped

### q13 (method)
- Question: Modular RAG 引入了哪些新的专用模块？
- Single-shot: correctness=1, citations=5/0, refusal=correct
  - 结论：片段中明确称为 Modular RAG 新专用模块的有 **Search module（搜索模块）**、**Memory module（记忆模块）** 和 **Task Adapter module（任务适配器模块）** [1][3][13]。 依据： - Search module 可适配特定场景，支持通过 LLM 生成的代码和查询语言，直接搜索搜索引擎、数据库、知识图谱等不同数据源 [1][3]。 - Memory module 利用 LLM 的记忆来指导检索，并创建无界记忆池 [3]。 - Task Adapter module 用于将 RAG 适配到不同下游任务，自动化零样本输入的提示检索，并通过少样本查询生成创建任务特定检索器 [13]。 补充：片段还提到 RAG-Fusion 的多查询策略，以...
- Agent: correctness=2, citations=9/0, steps=search_library → search_library → read_page → read_page, stop=answer
  - Modular RAG 在原有 Naive RAG、Advanced RAG 的流程基础上，引入了 **5 个新的专用模块**（New Modules）： 1. **Search（搜索）模块**：针对具体场景进行调整，用 LLM 生成的代码和查询语言，直接检索搜索引擎、数据库、知识图谱等多种数据源 [1][5]。文中还提到用 RAG-Fusion 弥补传统搜索的不足。它采用多查询策略把用户查询扩展成多个视角，并进行并行向量检索和智能重排序 [5]。 2. **Memory（记忆）模块**：借助 LLM 的记忆能力来引导检索，构建无界记忆池；并通过迭代自增强，使文本更贴近数据分布 [5][2]。 3. **Routing（路由）模块**：在多个数据源之间导航，为查询选择最优路径；这条路径可以是摘要、特定数据库检索...
- Judge reason: 答案覆盖了 Search、RAG-Fusion、Memory、Routing、Predict、Task Adapter 全部新模块并补充 New Patterns，各事实性陈述均有片段依据且引用编号有效；虽将 RAG-Fusion 归入 Search 子项并把模块数表述为 5 个，但内容完整一致。

### q25 (cross_paper)
- Question: MAIC-Craft 的 Open-Ended RAG 与 RAG 综述中的 Advanced/Modular RAG 有哪些对应关系？
- Single-shot: correctness=0, citations=4/0, refusal=false_refusal
  - 信息不足：提供的片段中未提及“MAIC-Craft”或“Open-Ended RAG”，因此无法判断其与 Advanced/Modular RAG 的对应关系；缺少关于 MAIC-Craft 的 Open-Ended RAG 的设计与实现信息，以及可与片段 [1]–[6] 所述 Modular RAG 模块（如 Search 模块、Memory 模块、RAG-Fusion）和片段 [7]–[9] 所述 Advanced RAG 预检索/后检索流程进行对照的具体描述。
- Agent: correctness=1, citations=20/0, steps=compare_papers → search_library → read_page → read_page → read_page → read_page, stop=max_steps
  - ## 结论 **两篇论文都没有明确论证过二者的对应关系**：openmaic.pdf 正文一直没有对“Open-Ended RAG”作出定义，该词只出现在图2的结构标注中[1][20][21]；rag_survey.pdf 也从未提及 MAIC 或开放式 RAG。因此，下面的对应关系只是基于双方框架结构作出的**功能类比**，并不是原文提出的结论。 ## 基于结构的对应关系 **1. 对应 Advanced RAG 的一侧（检索前后的优化、仍然呈链式结构）** - 综述把 Advanced RAG 定义为“围绕 pre-retrieval 和 post-retrieval 的多项优化策略，流程与 Naive RAG 类似，仍呈链式结构”[10]；其中 pre-retrieval 包括优化索引结构（增强数据粒度、...
- Judge reason: 答案给出的“查询生成对应检索前优化、知识库构建对应索引与元数据升级、课程组件模块化对应 Modular RAG”这一结构类比与参考答案一致；但它漏掉了参考答案中的三点：一是检索后处理的对应关系，二是 Search、Routing、Task Adapter 等具体模块的映射，三是“RAG 是多智能体内容生成流程中的一个模块”这一点；因此只算部分正确。


## Regressions and remaining failures

### q06 (multi_hop)
- Question: 原始教学材料在 MAIC 的 Read 阶段会经历哪些处理，最终变成智能体可用的知识？
- Single-shot: correctness=1, citations=6/0, refusal=correct
  - 结论：在 Read 阶段，原始教学材料先被预处理，再通过多模态提取与描述生成、知识抽取与知识库构建，最终形成结构化知识库及其组成的结构化资源集；这些高度结构化资源随后在 Plan 阶段被用于支持 AI 教学智能体进行课程规划。[1][2][3][5][6] 依据： - 预处理上传资源后，MAIC-Craft 使用提取函数完成 Read 阶段。[1][2] - 多模态内容由基于 MLLM 的方法处理，生成全面且具有教学意识的描述。[1] - 系统同时实施知识提取方法，将教育内容组织为结构化知识库，并在不同资源模态之间构建分类关系，形成最终的结构化资源集。[1][3] - 实现上整合了视觉语言模型用于视觉处理、自动语音识别用于音频转写、文档解析器用于文本提取，并置于统一处理流水线中。[2] - MAIC-Craft...
- Agent: correctness=1, citations=10/0, steps=search_library → search_library → read_page → read_page, stop=answer
  - **结论**：MAIC-Craft 的 Read 阶段是一个“多模态抽取 → 教学化描述生成 → 知识库构建”的流水线，把上传的异构原始资源（课程幻灯片、教材、视频、音频讲座等任意组合）转换为包含描述与知识结构的高结构化资源集 [14]。 **具体处理流程**（分三步）： 1. **多模态内容抽取（Multimodal Content Extraction）** - 用多模态大模型（MLLM）捕获各模态内容，对每个资源 unit 抽取**文本内容 $R^t_i$** 与**视觉内容 $R^v_i$**，即 $f^T_1: R_i \to (R^t_i, R^v_i)$ [15][16]。 - 其中 $R^t_i$ 既包含直接文本，也包含**由音频转写而来的内容** [16]。 - 实现上集成了三类组件于统一处理...
- Judge reason: 答案准确覆盖了多模态抽取、描述生成与知识库构建三步，但遗漏了参考答案中 Read 阶段之后的查询生成与开放式 RAG（以及最终教学脚本/智能体交付）环节，故仅部分完整。

### q26 (cross_paper)
- Question: 三篇论文分别如何评估各自系统？
- Single-shot: correctness=1, citations=3/0, refusal=false_refusal
  - 信息不足：提供的片段只涉及 rag_survey.pdf 和 autogen.pdf，缺少第三篇论文的片段，因此无法回答“三篇论文分别如何评估各自系统”。另外，rag_survey 片段仅说明该综述总结了 RAG 的评估方法、任务、数据集、基准和工具 [12][14]，并未说明其评估某个自建系统；autogen 片段仅说明每个基于 LLM 的系统在每个问题上测试三次，并报告问题解决正确率及失败原因 [16]。
- Agent: correctness=1, citations=37/0, steps=compare_papers → search_library → read_page → read_page → read_page → search_library, stop=max_steps
  - # 三篇论文的评估方式对比 ## 1. AutoGen：以多任务基准测试和与基线系统的对比为主 **定性评估**：用 MATH 数据集的两个 level-5 难题，每题测试三次，记录各系统的正确次数并分析失败原因 [52][1]。AutoGPT 因无法获取代码执行结果、且在定性评估中一题未解而被排除 [1]。 **定量评估**：同样在 MATH 上做两组实验：(1) 120 道 level-5 难题（六个类别各 20 题，排除几何）；(2) 完整测试集 5000 题 [1][2][5]。对比对象包括 Multi-Agent Debate、LangChain ReAct、vanilla GPT-4、ChatGPT + Code Interpreter、ChatGPT + Plugin（Wolfram Alpha）...
- Judge reason: 答案对三篇论文的评估方式大体准确且引用充分，但遗漏了参考答案中 MAIC 通过 TGAI 课程两个月真实教学实验评估学生投入与学习效果这一关键事实。


## Cross-paper cases

### q24 (cross_paper)
- Question: MAIC 的多智能体课堂与 AutoGen 的多智能体框架在角色设计上有什么不同？
- Single-shot: correctness=2, citations=13/0, refusal=correct
  - **结论：** MAIC 的角色设计是面向教学场景的“角色专门化”设计，直接部署 AI 教师、助教和可定制同学等教学角色，并让学习者组织个性化协作生态 [1][3]；AutoGen 的角色设计则是通用的“可对话智能体”抽象，开发者通过选择、配置或扩展内置能力来创建不同角色，内置示例包括 AI 助手与人类代理/工具代理 [11][14][16]。因此，MAIC 更偏向教学职能预设与课堂协作角色生态，AutoGen 更偏向通用、可编程、可复用的角色构建框架 [1][3][11][14]。 **依据与差异：** 1. **角色类型不同：** MAIC 部署角色专门化的 AI 同伴，包括教学助手和可定制同学 [1][3]；AutoGen 使用通用可对话智能体设计，智能体可利用 LLM、人类输入、工具或其组合 [9][11]。 2. **角色形成方式不同：** MAIC 的 AI 教师智能体自主完成课程交付，并基于多模态学生交互轨迹和潜在知识状态估计实时调整教学策略 [1][2]；AutoGen 中开发者可通过选择和配置内置能力子集来快速创建具有不同角色的智能体，并可扩展后端以实现更多自定义行为...
- Agent: correctness=2, citations=25/0, steps=compare_papers → compare_papers → read_page → search_library → read_page, stop=answer
  - ## 结论 **核心区别**：MAIC 的角色是**由教育学分类推导出的“课堂角色”**，即教师、助教、多种学生同伴，再加上隐藏的调度者，每个角色都按照行为类别和人格特征进行定制；AutoGen 的角色则是**面向开发者的通用能力抽象**，它提供可复用的基础类，角色由“LLM、工具或人类”的能力组合与开发者自定义的对话流程决定，并不对应特定的教学身份。 ## MAIC 的角色设计（教育学驱动、预设且带人格） - 角色分类依据：根据 Schwanke 的教育学工作，把课堂互动行为系统地归为四类——**Teaching & Initiation (TI)**、**In-depth Discussion (ID)**、**Emotional Companionship (EC)**、**Classroom Management (CM)**，并据此保证智能体角色的多样性与覆盖面[37][38] - 每个智能体对每个角色进行一次定制，即 `A = ρ(LLM, prompt_A)`，并关联一个或多个课堂行为标签[5]。四类原型学生智能体（可按需自行扩展）分别是：**Class Clown (T...
- Judge reason: 答案准确区分了MAIC教育学驱动的预设课堂角色与AutoGen通用可编程智能体角色，关键事实均有有效片段引用支撑。

### q25 (cross_paper)
- Question: MAIC-Craft 的 Open-Ended RAG 与 RAG 综述中的 Advanced/Modular RAG 有哪些对应关系？
- Single-shot: correctness=0, citations=4/0, refusal=false_refusal
  - 信息不足：提供的片段中未提及“MAIC-Craft”或“Open-Ended RAG”，因此无法判断其与 Advanced/Modular RAG 的对应关系；缺少关于 MAIC-Craft 的 Open-Ended RAG 的设计与实现信息，以及可与片段 [1]–[6] 所述 Modular RAG 模块（如 Search 模块、Memory 模块、RAG-Fusion）和片段 [7]–[9] 所述 Advanced RAG 预检索/后检索流程进行对照的具体描述。
- Agent: correctness=1, citations=20/0, steps=compare_papers → search_library → read_page → read_page → read_page → read_page, stop=max_steps
  - ## 结论 **两篇论文都没有明确论证过二者的对应关系**：openmaic.pdf 正文一直没有对“Open-Ended RAG”作出定义，该词只出现在图2的结构标注中[1][20][21]；rag_survey.pdf 也从未提及 MAIC 或开放式 RAG。因此，下面的对应关系只是基于双方框架结构作出的**功能类比**，并不是原文提出的结论。 ## 基于结构的对应关系 **1. 对应 Advanced RAG 的一侧（检索前后的优化、仍然呈链式结构）** - 综述把 Advanced RAG 定义为“围绕 pre-retrieval 和 post-retrieval 的多项优化策略，流程与 Naive RAG 类似，仍呈链式结构”[10]；其中 pre-retrieval 包括优化索引结构（增强数据粒度、优化索引结构、**添加 metadata**、对齐优化、混合检索）和查询优化（查询重写、查询变换、查询扩展）[33]。 - MAIC-Craft 图2 中的 **Query Generation Q1…Qn** 环节[20]在功能上与 query 重写、扩展这类检索前优化相对应[...
- Judge reason: 答案给出的“查询生成对应检索前优化、知识库构建对应索引与元数据升级、课程组件模块化对应 Modular RAG”这一结构类比与参考答案一致；但它漏掉了参考答案中的三点：一是检索后处理的对应关系，二是 Search、Routing、Task Adapter 等具体模块的映射，三是“RAG 是多智能体内容生成流程中的一个模块”这一点；因此只算部分正确。

### q26 (cross_paper)
- Question: 三篇论文分别如何评估各自系统？
- Single-shot: correctness=1, citations=3/0, refusal=false_refusal
  - 信息不足：提供的片段只涉及 rag_survey.pdf 和 autogen.pdf，缺少第三篇论文的片段，因此无法回答“三篇论文分别如何评估各自系统”。另外，rag_survey 片段仅说明该综述总结了 RAG 的评估方法、任务、数据集、基准和工具 [12][14]，并未说明其评估某个自建系统；autogen 片段仅说明每个基于 LLM 的系统在每个问题上测试三次，并报告问题解决正确率及失败原因 [16]。
- Agent: correctness=1, citations=37/0, steps=compare_papers → search_library → read_page → read_page → read_page → search_library, stop=max_steps
  - # 三篇论文的评估方式对比 ## 1. AutoGen：以多任务基准测试和与基线系统的对比为主 **定性评估**：用 MATH 数据集的两个 level-5 难题，每题测试三次，记录各系统的正确次数并分析失败原因 [52][1]。AutoGPT 因无法获取代码执行结果、且在定性评估中一题未解而被排除 [1]。 **定量评估**：同样在 MATH 上做两组实验：(1) 120 道 level-5 难题（六个类别各 20 题，排除几何）；(2) 完整测试集 5000 题 [1][2][5]。对比对象包括 Multi-Agent Debate、LangChain ReAct、vanilla GPT-4、ChatGPT + Code Interpreter、ChatGPT + Plugin（Wolfram Alpha）[5]。指标为 F1、Recall 和正确率 [4]。 **另外，还在多个场景中做了评测**： - **问答场景**：用 Natural Questions 数据集上的 5,332 个非冗余上下文文档与 6,775 条查询，评估 Retrieval-Augmented Chat ...
- Judge reason: 答案对三篇论文的评估方式大体准确且引用充分，但遗漏了参考答案中 MAIC 通过 TGAI 课程两个月真实教学实验评估学生投入与学习效果这一关键事实。

## Tool usage

| Tool | Calls |
|---|---:|
| compare_papers | 4 |
| read_page | 17 |
| search_library | 20 |

## Latency

- Single-shot: P50 5324 ms, P95 8769 ms
- Agent: P50 8187 ms, P95 16889 ms
