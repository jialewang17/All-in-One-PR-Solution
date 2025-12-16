# All-in-One PR Solution

综合性的公关传播 RAG（Retrieval-Augmented Generation）与知识图谱构建平台。该项目将多格式文档预处理、结构化 JSON 生成、增强知识图谱写入、图/向量检索问答、RLHF（人类反馈强化学习）以及多种辅助工具整合在同一个仓库，帮助品牌/公关团队快速搭建企业级的内容知识中枢。

---

## 🔍 核心能力

- **多格式文档处理**：自动提取 PDF、Word、PPT、Excel、HTML、CSV 等内容，标准化输出清洗文本与结构化 JSON。
- **增强知识图谱**：基于 CategoryL1/L2 分类 Schema，把仅包含 `id / clean_text / category_code` 的 `Section` 节点，以及 `Company`、`Brand`、`CompanyType` 等实体与关系写入 Neo4j，SPO 关系基于 `Section.clean_text` 抽取补充。
- **RAG 检索问答**：结合 Neo4j 图谱与向量检索，实现 GraphRAG + VectorRAG 的多策略问答，提供菜单化交互界面。
- **一键处理流程**：`pr_process_all_v1_1.py` 串联预处理 → JSON → KG 写入 → 案例库导入 → 向量索引 → 可选 SPO 的整条流水线。
- **CLI 工具集**：`tools/processing` 与 `tools/querying` 目录下提供建库、清理、迁移、查询、调试等脚本，可直接运行。
- **RLHF 闭环**：`core/rlhf` 中的品牌知识、方法论规则、反馈收集、奖励模型训练，现已完整接入 `pr_rag_system_v1_1.py` 菜单，可在生成方案后立即录入反馈并触发训练。
- **示例与测试**：`examples/` 与 `tests/` 提供常见场景 demo、端到端与离线自检脚本，便于快速验证环境与功能。

---

## 🎯 主系统功能说明（pr_rag_system_v1_1.py）

`pr_rag_system_v1_1.py` 是系统的核心交互入口，提供菜单化的功能访问。运行 `python pr_rag_system_v1_1.py` 即可进入主菜单。

### 📊 数据处理模式（菜单 1-5）

1. **一键构建增强图谱**：调用 `process_enhanced_all.py`，自动完成分类/Section/实体提取 + 可选 SPO 关系的完整知识图谱构建流程。
2. **迁移旧图谱到新Schema**：将 v1.0 版本的旧图谱结构迁移到 v1.1 的新 Schema（CategoryL1/L2、Section 等新节点类型）。
3. **清理旧 PR_Chunk 节点**：移除 v1.0 遗留的 `PR_Chunk` 节点，保持图谱结构整洁。
4. **仅补充/生成 SPO**：使用 LLM 提取语义关系（SPO），优先调用 API，失败时自动回退到演示规则。
5. **使用演示规则创建 SPO**：不调用 API，使用预定义规则创建演示性质的 SPO 关系（适合无 API Key 场景）。

### 🔍 查询模式（菜单 6-8）

6. **增强RAG对话**：启动交互式问答模式，支持 GraphRAG（基于图谱关系）和 VectorRAG（基于向量相似度）两种检索策略，可实时切换。
7. **直接Neo4j查询**：打开交互式 Cypher 查询控制台，可直接执行 Neo4j 查询语句，适合高级用户和调试场景。
8. **快速查询**：基于 v1.1 新架构的简易问答工具，输入问题即可获得回答，支持 GraphRAG 和文本匹配。

### 📝 生成模式（菜单 9-10）

9. **生成公关传播方案**：
   - 支持多模板输出（图文简报、视频脚本、整合活动方案、短视频脚本、小红书种草、危机公关方案等）。
   - 集成 RLHF 增强生成器，自动应用方法论规则、品牌知识，并生成质量评估。
   - 支持 RAG 检索增强上下文，或手动输入背景信息。
   - 自动保存方案记录到 `outputs/rlhf_plans/`，包含 Plan ID、质量评分、应用规则等元信息。
   - 可导出为 Markdown 文件。

10. **生成公关传播报告**：
    - 需求确认流程：收集报告目标、受众、语气、长度、格式等需求。
    - 方法论对齐：自动检索知识库中的相关案例、渠道、方法论。
    - 支持 RAG 检索增强，或使用行业经验生成。
    - 可保存为 Markdown 文件。

### 📈 反馈/学习模式（菜单 11-14）

11. **导入方法论规则**：
    - 从 `data/rlhf/methodology_rules.json` 批量导入 PR 方法论规则到 Neo4j。
    - 规则会以 `MethodologyRule` 节点形式存储，并与品牌/行业建立 `APPLIES_TO` 关系。
    - 导入后，方案生成器会自动应用匹配的规则。

12. **录入方案反馈（RLHF）**：
    - 输入 Plan ID（从最近生成的方案中获取）。
    - 记录评分（1-5 分）、文字评价、改进建议、结构化指标等反馈信息。
    - 反馈数据保存到 `data/feedback.db`，供后续训练使用。

13. **手动触发 RLHF 训练**：
    - 读取 `data/feedback.db` 中的反馈数据。
    - 结合 `outputs/rlhf_plans/` 中的方案记录，准备训练样本。
    - 训练奖励模型，更新权重以优化后续方案生成质量。
    - 可设置最少反馈数量阈值（默认 5 条）。

14. **查看 RLHF 学习进度**：
    - 显示模型训练状态、训练轮次、最近训练时间。
    - 统计反馈总数、平均评分。
    - 展示高频改进建议，辅助判断是否需要继续收集反馈。

### 🧪 测试模式（菜单 15-17）

15. **功能演示**：可在控制台选择运行增强 RAG (`examples/rag/demo_enhanced_pr_rag_v1_1.py`)、方案生成 (`examples/demo_plan_generation.py`)、报告生成 (`examples/demo_report_generation.py`) 或报告+RAG (`examples/demo_report_and_rag.py`) 等示例。
16. **完整测试**：运行 `tests/test_enhanced_pr_rag_v1_1.py`，执行端到端测试（需要 Neo4j 连接）。
17. **系统状态检查**：
    - 检查 Neo4j 连接状态。
    - 统计节点总数、Section、Company、Brand 等关键节点数量。
    - 统计 `INVOLVED_IN_CATEGORY`、`SPO_REL` 等关系数量。

### 📚 帮助模式（菜单 18-19）

18. **使用指南**：显示简版使用指南，包括各功能的使用顺序和注意事项。
19. **系统架构**：展示 v1.1 版本的架构概览，包括数据流向和查询方式说明。

### 🚪 系统（菜单 20）

20. **退出**：安全退出系统。

---

## 🧠 运行逻辑概览

```
[原始文档 data/raw]
        │  (tools.processing.ingestion.pr_multi_format_preprocessing)
        ▼
[清洗文本 data/cleaned]
        │  (core.processing.ingestion.txt_to_json)
        ▼
[结构化 JSON data/json]
        │  (tools.processing.ingestion.normalize_json_sections → data/json_structured)
        ▼
[规范化 JSON data/json_structured]
        │  (tools.processing.kg_writer.run_enhanced_kg_writer：写入 Section/实体/SPO)
        ▼
[Neo4j：Category / Section(id+clean_text+category_code) / Company / Brand / CompanyType / SPO]
        │  ├─ 可选：tools.processing.extractors.extract_spo_relations
        │  └─ 可选：tools.processing.extractors.create_demo_spo_relations
        ▼
[查询与应用层]
        ├─ core.querying.pipelines.EnhancedPRRAGSystemV11（API）
        ├─ tools.querying.graph/ pipelines CLI
        └─ unified_pr_system / agents 进行方案生成、RLHF、分析
```

核心思路：所有“核心实现”放在 `core/` 供 import 调用，`tools/` 仅承载 CLI。Feature Registry (`manage_features.py + config/features.yaml`) 将上述阶段串成可编排的命令，`pr_process_all_v1_1.py`、`pr_rag_system_v1_1.py`、`unified_pr_system.py` 则在此基础上提供一键流程、菜单或集成入口。

---

## 🆕 首次使用建议流程

1. **准备环境**  
   - 创建虚拟环境、安装依赖，填写 `.env`（至少 Neo4j 与 OpenAI/OpenRouter Key）。  
   - 运行 `python manage_features.py list` 验证 Feature Registry 加载正常。
2. **初始化数据库**  
   - `python tools/processing/kg_writer/migrate_graph_schema.py`（可选，首次搭建可跳过）。  
   - `python tools/processing/kg_writer/clean_pr_chunk_nodes.py`（若数据库无旧数据可跳过）。
3. **导入数据**  
   - 将原始文件放入 `data/raw/`，将参考数据（案例库 CSV、方法论文档、关系表 DOCX）放入 `data/reference/`。  
   - 运行 `python pr_process_all_v1_1.py` 执行完整流程：预处理 → JSON 转换 → 增强 KG 写入 → 案例库导入 → 向量索引 → 可选 SPO。  
   - 或使用参数跳过某些步骤：`--skip-case-library`（跳过案例库导入）、`--no-vector`（跳过向量索引）、`--kg-no-spo`（跳过 SPO 提取）。
4. **验证与体验**  
   - `python tests/test_system_status.py` 检查连接。  
   - `python pr_rag_system_v1_1.py` 体验菜单化查询；或 `python tools/querying/pipelines/quick_query_v1_1.py` 直接问答。  
   - 通过菜单 11~14 完成“导入方法论规则 → 录入方案反馈 → 触发 RLHF 训练 → 查看学习进度”，或运行 `examples/rlhf/demo_rlhf_system.py` / `unified_pr_system.py` 体验一体化流程。

---

## 🔁 v1 → v1.1 迁移指南

1. **备份旧库**：导出 Neo4j 4.x/v1 的关键节点；备份 `data/` 与 `.env`。  
2. **升级代码与依赖**：拉取 v1.1 分支，重新安装 `config/requirements_v1.txt`。  
3. **迁移图谱 Schema**：运行 `python tools/processing/kg_writer/migrate_graph_schema.py`，自动创建 CategoryL1/L2、Section 与新关系。  
4. **清理旧节点**：执行 `python tools/processing/kg_writer/clean_pr_chunk_nodes.py`，移除 `PR_Chunk` 等 v1 遗留结构。  
5. **重建数据**：将 v1 素材放入 `data/raw/`，运行 `python pr_process_all_v1_1.py`（或按 Feature 分步执行）以生成 v1.1 所需的 JSON、节点与 SPO。  
6. **更新调用入口**：  
   - 代码中保持使用 `core.*` 模块；CLI 路径改为 `tools/processing/...`、`tools/querying/...` 的新层级。  
   - 若之前依赖旧兼容脚本（如 `tools/quick_query.py`），需要改为新路径。  
7. **验证**：运行 `python manage_features.py list`、`python tests/test_system_status.py`，再用小规模查询或 `pr_rag_system_v1_1.py` 验证。

---

## 🗂️ 仓库结构

```
.
├── core/                 # 仅供 import 的业务模块
│   ├── common/           # 分类 Schema、Neo4j env、文本转换等共用工具
│   ├── processing/       # KG 写入器、实体/SPO 提取、公司词典等
│   ├── querying/         # 增强 RAG 核心实现
│   │   ├── graph/        # CypherBuilder、GraphClient、GraphRAGQueryEngine
│   │   ├── vector/       # EmbeddingProvider、SectionRetriever
│   │   └── pipelines/    # EnhancedPRRAGSystemV11（Graph/Section 编排）
│   ├── generation/       # templates/ + executors/ + postprocessors/（一功能一模块）
│   └── rlhf/             # data/ + policies/ + trainer/（反馈/方法论/RLHF 管线）
├── tools/                # 可直接运行的 CLI（已与 core 模块一一对应）
│   ├── processing/
│   │   ├── ingestion/    # 多格式预处理
│   │   ├── kg_writer/    # 迁移、清理、建库一键脚本
│   │   ├── extractors/   # SPO/实体提取脚本
│   │   ├── company/      # 词典初始化等
│   │   └── vector/       # Section 向量索引
│   └── querying/
│       ├── graph/        # 图谱/Neo4j 查询工具
│       └── pipelines/    # Quick Query 等组合脚本
├── agents/               # 多智能体分析/合并工具
├── config/               # requirements、feature registry 等配置
├── data/                 # 原始/清洗/JSON/Chunk/SPO 等数据目录
├── docs/                 # 主要文档（RLHF、Agents、规格等）
├── examples/             # RAG / Query / RLHF 示例程序
├── openspec/             # 设计文档与架构变更 proposal
├── scripts/              # smoke 测试、运维脚本
├── tests/                # 自动化测试（离线自检、端到端、系统状态）
├── manage_features.py    # 功能注册与调度 CLI
├── pr_process_all_v1_1.py # 一键处理主流程
├── pr_rag_system_v1_1.py  # 菜单式增强 RAG 主入口
├── pr_rag_config_v1_1.py  # 菜单系统模块映射
├── unified_pr_system.py   # 集成式入口（含 RLHF 等高级功能）
└── README.md             # 当前文档
```

> 说明：`core/` 中的文件都是包模块，不建议直接 `python file.py` 运行；若需单独调试，请使用 `python -m core.xxx.yyy`。`tools/` 目录已去掉旧版兼容层，所有 CLI 均放在上述子目录中，请按新路径调用。

> Query 层解释：`core/querying/graph` 负责 Prompt→Cypher 与 Neo4j 查询，`core/querying/vector` 承担向量检索与答案生成，`core/querying/pipelines` 提供 `EnhancedPRRAGSystemV11` 的统一接口，方便前端直接调用单一入口。  
> Generation 层依次包含 `templates/`（提示词库）、`executors/`（LLM 调用与方案 orchestrator）、`postprocessors/`（输出规整）；RLHF 层拆分为 `data/`（反馈/知识 DAO）、`policies/`（方法论规则）、`trainer/`（质量评估、奖励模型、训练主循环），实现“一功能一模块”的映射关系。
> Orchestration 层可通过 `config/features.yaml` + `manage_features.py` 动态查看与运行能力；`pr_process_all_v1_1.py`、`pr_rag_system_v1_1.py` 等协同入口也已登记为 `orchestration` 类的 Feature，便于前端调用或自动化集成。

---

## ✅ 环境要求

- Python 3.10+（推荐创建 virtualenv）
- Neo4j 5.x（Aura 或本地），开启 Bolt/Neo4j+SSC 访问
- OpenAI API Key 或 OpenRouter API Key（用于实体/SPO 提取与 RAG）
- pip 依赖参见 `config/requirements_v1.txt`

准备 `.env`：

```
NEO4J_URI=neo4j+ssc://xxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=*****
NEO4J_DATABASE=neo4j
OPENAI_API_KEY=sk-...
# 或
OPENROUTER_API_KEY=or-...
```

---

## 🚀 快速上手

1. **克隆与安装**
```bash
   git clone <repo-url>
   cd All-in-One-PR-Solution
   python -m venv .venv && .\.venv\Scripts\activate
pip install -r config/requirements_v1.txt
   cp .env.example .env  # 如无示例，可自行创建
```

2. **准备数据**
   - 将原始文档放入 `data/raw/`
   - `pr_process_all_v1_1.py` 会自动在 `data/cleaned`、`data/json` 创建输出
   - **推荐**：运行 `normalize_json_sections.py` 规范化 JSON 到 `data/json_structured/`（系统默认从此目录读取）

3. **运行一键流程**
```bash
   python pr_process_all_v1_1.py
   ```
   完整流程包括：
   - 步骤1：多格式文档预处理（PDF/Word/PPT/Excel/HTML/CSV → 清洗文本）
   - 步骤2：JSON 格式转换（清洗文本 → 结构化 JSON，输出到 `data/json/`）
   - **推荐步骤**：JSON 规范化（`data/json/` → `data/json_structured/`，统一数据结构）
   - 步骤3：v1.1 增强知识图谱写入（从 `data/json_structured/` 读取，分类/Section/实体提取 → Neo4j）
   - 步骤4：导入案例库结构化知识（渠道/案例/目标/行业关系 → Neo4j）
   - 步骤5：创建向量索引并生成嵌入（Section 节点向量化 → Neo4j）
   - 可选：手动选择是否补充 SPO 关系（LLM 提取或演示规则）
   
   运行成功后，所有数据会写入 Neo4j，可直接用于查询和方案生成。

4. **体验增强 RAG 菜单**
   ```bash
   python pr_rag_system_v1_1.py
   ```
   常用菜单：
   - **数据处理（1-5）**：一键构建图谱、迁移 Schema、清理节点、补充 SPO
   - **查询（6-8）**：增强 RAG 对话（Graph + Vector）、直接 Neo4j 查询、快速问答
   - **生成（9-10）**：生成公关传播方案（多模板+RLHF）、生成公关传播报告
   - **RLHF（11-14）**：导入方法论规则、录入反馈、触发训练、查看进度
   - **测试（15-17）**：功能演示、完整测试、系统状态检查

5. **常用 CLI 工具**
   ```bash
   # JSON 规范化（基础版，快速）
   python tools/processing/ingestion/normalize_json_sections.py --input-dir data/json --output-dir data/json_structured

   # JSON 规范化（增强版，预提取实体，更精准但较慢）
   python tools/processing/ingestion/normalize_json_sections.py --extract-entities --input-dir data/json

   # 一键流程的更细化版本（默认从 data/json_structured/ 读取）
   python tools/processing/kg_writer/process_enhanced_all.py

   # Neo4j 直接查询
   python tools/querying/graph/neo4j_direct_query_new.py

   # 图谱查询示例
   python tools/querying/graph/query_enhanced_kg.py company 奥迪

   # 功能清单/运行
   python manage_features.py list
   python manage_features.py run run_full_pipeline

   # 冒烟回归
   scripts/smoke_rag.bat

   # 统一公关智能体（问答 + 方案 + 实体 + RLHF）
   python unified_pr_system.py --mode query --query "新能源车上市需要怎样的传播策略？"
   python unified_pr_system.py --mode generate
   python unified_pr_system.py --mode analyze --query "分析这个品牌案例"
   ```

6. **功能清单 & 调度**
   - 所有正式功能都登记在 `config/features.yaml`
   - 可通过 `manage_features.py` 查看与执行，方便前端或自动化系统对接：
     ```bash
     python manage_features.py list
     python manage_features.py list --category processing
     python manage_features.py show preprocess_multi_format
     python manage_features.py run extract_spo_relations
     ```

7. **示例 & 测试**
```bash
   # RAG 端到端测试（需 Neo4j）
   python tests/test_enhanced_pr_rag_v1_1.py

   # 环境/连接自检
   python tests/test_system_status.py

   # RLHF 演示
   python examples/rlhf/demo_rlhf_system.py
   ```

---

## 🧰 目录/脚本速查

| 类型 | 关键脚本 | 说明 |
|------|----------|------|
| 主入口 | `pr_process_all_v1_1.py` | 一键处理流水线（预处理→JSON→KG→案例库→向量索引→可选SPO） |
| 主入口 | `pr_rag_system_v1_1.py` | 菜单式增强 RAG 系统 |
| 主入口 | `unified_pr_system.py` | 一体化 CLI（GraphRAG 查询 / 方案生成 / 实体分析 / RLHF，使用 `--mode query|generate|analyze` 与 `--query` 参数） |
| CLI | `tools/processing/ingestion/pr_multi_format_preprocessing.py` | 多格式预处理 |
| CLI | `core/processing/ingestion/txt_to_json.py` | TXT→JSON 转换（可直接 `python` 执行） |
| CLI | `tools/processing/ingestion/normalize_json_sections.py` | 将松散 JSON 规范化为 `{document_title, sections[]}` 结构（支持实体预提取、元数据增强） |
| CLI | `tools/processing/kg_writer/run_enhanced_kg_writer.py` | JSON→Neo4j 写入 |
| CLI | `tools/processing/extractors/extract_spo_relations.py` | LLM 版 SPO 提取 |
| CLI | `tools/processing/extractors/create_demo_spo_relations.py` | 规则版 SPO 提取 |
| CLI | `tools/processing/vector/create_section_vector_index.py` | Section 向量索引同步 |
| CLI | `tools/querying/pipelines/quick_query_v1_1.py` | 快速问答脚本 |
| CLI | `tools/querying/graph/query_enhanced_kg.py` | 多维图谱查询 demo |
| CLI | `tools/querying/graph/neo4j_direct_query_new.py` | 交互式 Cypher 查询 |
| 管理 | `manage_features.py` + `config/features.yaml` | 功能清单展示与命令调度 |
| RLHF | `core/rlhf/*` + `examples/rlhf/demo_rlhf_system.py` + `tools/rlhf/import_methodology_rules.py` | 反馈收集、方法论规则、奖励模型训练 |
| 测试 | `tests/test_enhanced_pr_rag_v1_1.py` | 端到端测试（Neo4j） |
| 测试 | `tests/test_system_status.py` | Neo4j/环境健康检查 |
| Smoke | `scripts/smoke_rag.bat` | 快速冒烟（功能登记/健康检查/测试入口） |

---

## 🧪 开发与测试建议

- **虚拟环境**：建议在 `.venv` 中开发，避免依赖冲突。
- **Lint / 格式化**：可按需安装 `black`、`flake8`、`mypy`（requirements 中已列出）。
- **数据安全**：`data/` 目录默认在本地；如果使用敏感数据，注意清理导出。
- **Neo4j Schema**：`create_schema()` 使用 `IF NOT EXISTS`，重复运行会看到 “IndexAlreadyExists” 警告，无需担心。
- **实体/SPO 提取**：依赖 OpenAI 或 OpenRouter；未配置 API Key 时可选择 `--use-demo-spo` 规则脚本保证流程可运行。
- **RLHF 数据**：方案生成记录保存在 `outputs/rlhf_plans/planrun_*.json`，反馈写入 `data/feedback.db`，如需备份/迁移 RLHF 进度请一并处理这两个目录。

---

## 📈 RLHF 闭环使用指南

1. **导入方法论规则**  
   - 运行 `python tools/rlhf/import_methodology_rules.py --rules data/rlhf/methodology_rules.json`（或通过菜单 11）将规则写入 Neo4j，生成 `(:MethodologyRule)-[:APPLIES_TO]->(:Brand|:Industry)`。
2. **生成方案并保存记录**  
   - 菜单 9 默认调用 `EnhancedPRRAGWithRLHF`，在终端中展示各模板方案，同时把完整 payload 保存至 `outputs/rlhf_plans/planrun_<timestamp>.json`（包含 `plan_id、quality_score、applied_rules` 等元信息）。
3. **录入反馈**  
   - 菜单 12 输入 `plan_id`、评分、建议等内容，系统会写入 `data/feedback.db` 的 `feedback` 表，可随时查询或导出。
4. **训练奖励模型**  
   - 菜单 13 会读取 `feedback.db` 与对应的 `planrun` 记录，凑齐满足阈值的样本后调用 `RLHFTrainer.train_reward_model()`，在 `core/rlhf/trainer/` 内更新权重缓存。
5. **查看进度与洞察**  
   - 菜单 14 汇总训练次数、最近训练时间、反馈总数、平均评分以及高频建议，辅助判断是否需要继续收集反馈。

> 注：若希望与其他系统集成，可直接 import `core.rlhf.data.FeedbackCollector`、`core.rlhf.policies.MethodologyRulesManager` 等模块，或复用 `EnhancedPRRAGWithRLHF` 的 `generate_plan` / `collect_feedback_for_plan` 方法。

---

## 📚 相关文档

- `docs/`：更详细的 v1.1 使用指南、注意事项、FAQ。
- `docs/kg_graph_structure.md`：当前知识图谱中各类节点与关系的来源说明（哪些是预定义写入、哪些依赖 LLM 抽取）。
- `docs/RLHF_System_Guide.md`：RLHF 系统说明。
- `docs/RLHF_IMPLEMENTATION_SUMMARY.md`：RLHF 设计摘要。
- `docs/AGENTS.md`：代理（agents）模块介绍。
- `docs/archive/`：历史版本的 README、指南等。

---

## 🤝 贡献指南

1. 建议先阅读 `openspec/project.md` 与 `docs/` 下的相关指南，了解目录约定与最新改动。
2. 功能/架构级更改可按照 `openspec` 流程提交 proposal。
3. 对 `core/` 模块的直接执行请使用 `python -m`，避免相对导入失效。
4. 合并前请运行相关测试（至少 `tests/test_system_status.py`）。

---

如需进一步帮助或扩展新场景，可以在 `docs/` 目录中查找更多操作细节，或直接联系维护者。祝你构建顺利 🎉！
