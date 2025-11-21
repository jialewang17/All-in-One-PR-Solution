# 公关传播智能体项目概述

## 项目简介

这是一个基于 AI 的公关传播智能体系统，整合了 RAG（检索增强生成）、知识图谱、实体提取和方案生成功能，为公关传播领域提供智能化的知识管理和内容生成服务。

## 技术栈

- **编程语言**: Python 3.x
- **AI/ML 框架**: 
  - LangChain (RAG 和 LLM 集成)
  - OpenAI API (GPT-3.5-turbo, GPT-4)
  - OpenRouter API (支持多种 LLM 模型)
- **图数据库**: Neo4j (知识图谱存储)
- **向量数据库**: ChromaDB (向量存储和检索)
- **文档处理**: 
  - PyPDF2 / pdfplumber (PDF 解析)
  - python-docx (Word 文档处理)
  - openpyxl (Excel 处理)
  - python-pptx (PowerPoint 处理)
- **配置管理**: YAML 配置文件
- **环境管理**: python-dotenv

## 项目结构

```
All-in-One PR Solution/
├── unified_pr_system.py          # 统一系统主入口
├── pr_rag_system_v1_1.py         # RAG 系统 v1.1
├── unified_config.yaml           # 统一配置文件
├── core/                         # 核心功能模块（仅供 import）
│   ├── common/                   # 公共配置与工具
│   ├── processing/               # 预处理、实体、SPO、写入器等
│   ├── querying/                 # RAG 主体
│   ├── generation/               # 方案生成等
│   └── rlhf/                     # RLHF 相关模块
├── agents/                       # Agent 工具
│   ├── analysis/                 # 代码分析
│   └── merger/                   # 合并策略
├── tools/                        # 可直接运行的命令行脚本
│   ├── processing/               # 建库、预处理、迁移
│   └── querying/                 # 查询/调试脚本
├── examples/                     # 演示脚本
│   ├── rag/demo_enhanced_pr_rag_v1_1.py
│   ├── rag/demo_enhanced_pr_rag.py
│   ├── query/demo_direct_query.py
│   └── rlhf/demo_rlhf_system.py
├── tests/                        # 自动化测试
│   ├── test_enhanced_pr_rag_v1_1.py
│   ├── test_enhanced_pr_rag.py
│   └── test_system_status.py
├── docs/                         # 文档
│   ├── Enhanced_PR_RAG_Guide.md  # 详细使用指南
│   ├── PR_RAG_Advanced_Guide.md  # 高级功能指南
│   └── Neo4j_Direct_Query_Guide.md # 直接查询指南
└── data/                         # 数据目录
    ├── raw/                      # 原始数据
    ├── cleaned/                  # 清理后数据
    ├── json/                     # JSON 格式数据
    └── chunks/                   # 分块数据
```

## 核心功能模块

### 1. 统一公关传播智能体系统 (unified-pr-system)

- 整合 RAG 系统、知识图谱、实体提取和方案生成
- 提供统一的查询接口
- 支持知识查询、实体分析、方案生成三种模式

### 2. RAG 系统 (pr-rag-system)

- 基于 Neo4j 知识图谱和向量存储的增强 RAG
- 支持图增强查询和纯向量查询
- 自动生成 Cypher 查询语句
- 结合图数据和向量检索结果生成答案

### 3. 知识图谱系统 (knowledge-graph)

- SPO 三元组提取
- 知识图谱构建和存储
- 图谱查询功能
- 数据导出和统计

### 4. 实体提取系统 (entity-extraction)

- 基于 LLM 的智能实体识别
- 实体关系提取
- 支持多种实体类型（品牌、企业、媒体、活动等）
- 支持多种关系类型（合作、竞争、媒体投放等）

### 5. 文档处理系统 (document-processing)

- 多格式文档解析（PDF、Word、Excel、PPT）
- 文本清理和规范化
- 文本分块
- 增量处理支持

### 6. Agent 工具系统 (agent-tools)

- Agent 代码分析
- 冲突检测
- 合并计划生成
- 代码合并

## 约定和规范

### 代码规范

- 使用 Python 3.x 语法
- 遵循 PEP 8 代码风格
- 使用类型提示（Type Hints）
- 函数和类使用文档字符串（Docstrings）

### 错误处理

- 使用 try-except 捕获异常
- 提供有意义的错误消息
- 记录错误日志
- 优雅降级处理

### 配置管理

- 使用 YAML 配置文件
- 使用环境变量存储敏感信息
- 支持默认配置
- 配置文件验证

### 数据处理

- 支持增量处理
- 数据格式标准化
- 数据验证和清理
- 数据备份和恢复

## 开发工作流

### 1. 环境准备

```bash
# 安装依赖
pip install -r config/requirements_v1.txt

# 配置环境变量
cp config/.env.example config/.env
# 编辑 config/.env 文件
```

### 2. 数据准备

- 将原始文档放入 `data/raw/` 目录
- 运行预处理脚本清理和转换数据
- 数据会自动分块并存储到 `data/chunks/`

### 3. 系统初始化

- 启动 Neo4j 数据库
- 运行系统初始化脚本
- 导入数据到知识图谱和向量存储

### 4. 功能测试

- 使用演示脚本测试功能
- 使用工具模块进行查询和分析
- 验证结果准确性

## 依赖关系

### 核心依赖

- Neo4j 数据库必须运行
- OpenAI API 或 OpenRouter API 必须可用
- ChromaDB 向量存储

### 可选依赖

- SPO 提取器（如果使用 SPO 三元组提取）
- 文档处理库（如果处理特定格式文档）

## 性能考虑

- 使用连接池管理数据库连接
- 批量处理数据以提高效率
- 使用缓存减少重复计算
- 优化 Cypher 查询性能

## 安全考虑

- API 密钥存储在环境变量中
- 数据库密码加密存储
- 输入数据验证和清理
- 防止 SQL 注入和代码注入

## 扩展性

- 模块化设计，易于扩展
- 支持插件机制
- 支持多种 LLM 模型
- 支持多种数据源

## 测试策略

- 单元测试核心功能
- 集成测试系统组件
- 端到端测试完整流程
- 性能测试和负载测试

## 文档维护

- 保持代码文档更新
- 更新用户指南
- 记录 API 变更
- 维护变更日志
