# All-in-One PR Solution

综合性的公关传播 RAG（Retrieval-Augmented Generation）与知识图谱构建平台。该项目将多格式文档预处理、结构化 JSON 生成、增强知识图谱写入、图/向量检索问答、RLHF（人类反馈强化学习）以及多种辅助工具整合在同一个仓库，帮助品牌/公关团队快速搭建企业级的内容知识中枢。

---

## 🔍 核心能力

- **多格式文档处理**：自动提取 PDF、Word、PPT、Excel、HTML、CSV 等内容，标准化输出清洗文本与结构化 JSON。
- **增强知识图谱**：基于 CategoryL1/L2 分类 Schema，把 Section、Company、Brand、CompanyType 等节点与关系写入 Neo4j，支持 SPO 关系补充。
- **RAG 检索问答**：结合 Neo4j 图谱与向量检索，实现 GraphRAG + VectorRAG 的多策略问答，提供菜单化交互界面。
- **一键处理流程**：`pr_process_all_v1_1.py` 串联预处理 → JSON → KG 写入 → 可选 SPO 的整条流水线。
- **CLI 工具集**：`tools/processing` 与 `tools/querying` 目录下提供建库、清理、迁移、查询、调试等脚本，可直接运行。
- **RLHF 模块**：`core/rlhf` 下封装了反馈收集、质量评估、知识管理、增强式 RAG 等组件，配套示例演示完整流程。
- **示例与测试**：`examples/` 与 `tests/` 提供常见场景 demo、端到端与离线自检脚本，便于快速验证环境与功能。

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
        │  (tools.processing.kg_writer.run_enhanced_kg_writer)
        ▼
[Neo4j：Category / Section / Company / SPO]
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
   - 将原始文件放入 `data/raw/`，运行 `python pr_process_all_v1_1.py` 或按步骤执行 `preprocess_multi_format → convert_txt_to_json → run_enhanced_kg_writer`。  
   - 需要 SPO 时再运行 `python tools/processing/extractors/extract_spo_relations.py`，无 Key 可用 `create_demo_spo_relations.py`。
4. **验证与体验**  
   - `python tests/test_system_status.py` 检查连接。  
   - `python pr_rag_system_v1_1.py` 体验菜单化查询；或 `python tools/querying/pipelines/quick_query_v1_1.py` 直接问答。  
   - 想测试 RLHF/方案生成，再运行 `python examples/rlhf/demo_rlhf_system.py` 或 `python unified_pr_system.py`。

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

3. **运行一键流程**
   ```bash
   python pr_process_all_v1_1.py
   ```
   流程：预处理 → JSON 转换 → v1.1 增强 KG 写入 → 手动选择是否补充 SPO。运行成功后数据会写入 Neo4j。

4. **体验增强 RAG 菜单**
   ```bash
   python pr_rag_system_v1_1.py
   ```
   常用菜单：
   - 1~5：建库/分类/实体/SPO 等处理工具
   - 6：增强 RAG 对话（Graph + Vector）
   - 8：快速问答
   - 11：系统状态检查

5. **常用 CLI 工具**
   ```bash
   # 一键流程的更细化版本，可带参数
   python tools/processing/kg_writer/process_enhanced_all.py --json-dir data/json

   # Neo4j 直接查询
   python tools/querying/graph/neo4j_direct_query_new.py

   # 图谱查询示例
   python tools/querying/graph/query_enhanced_kg.py company 奥迪

   # 功能清单/运行
   python manage_features.py list
   python manage_features.py run run_full_pipeline

   # 冒烟回归
   scripts/smoke_rag.bat
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
| 主入口 | `pr_process_all_v1_1.py` | 一键处理流水线 |
| 主入口 | `pr_rag_system_v1_1.py` | 菜单式增强 RAG 系统 |
| CLI | `tools/processing/ingestion/pr_multi_format_preprocessing.py` | 多格式预处理 |
| CLI | `core/processing/ingestion/txt_to_json.py` | TXT→JSON 转换（可直接 `python` 执行） |
| CLI | `tools/processing/kg_writer/run_enhanced_kg_writer.py` | JSON→Neo4j 写入 |
| CLI | `tools/processing/extractors/extract_spo_relations.py` | LLM 版 SPO 提取 |
| CLI | `tools/processing/extractors/create_demo_spo_relations.py` | 规则版 SPO 提取 |
| CLI | `tools/processing/vector/create_section_vector_index.py` | Section 向量索引同步 |
| CLI | `tools/querying/pipelines/quick_query_v1_1.py` | 快速问答脚本 |
| CLI | `tools/querying/graph/query_enhanced_kg.py` | 多维图谱查询 demo |
| CLI | `tools/querying/graph/neo4j_direct_query_new.py` | 交互式 Cypher 查询 |
| 管理 | `manage_features.py` + `config/features.yaml` | 功能清单展示与命令调度 |
| RLHF | `core/rlhf/*` + `examples/rlhf/demo_rlhf_system.py` | 反馈收集、质量评估、RLHF RAG |
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

---

## 📚 相关文档

- `docs/`：更详细的 v1.1 使用指南、注意事项、FAQ。
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
