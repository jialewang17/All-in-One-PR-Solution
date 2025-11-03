# 公关传播RAG系统 v1.0

## 🎯 项目概述

这是公关传播RAG系统的v1.0版本，包含完整的增强版知识图谱RAG功能。

## 📁 项目结构

```
pr_rag_v1/
├── pr_rag_system_v1.py          # 主入口程序
├── pr_rag_config_v1.py          # 系统配置
├── start_pr_rag_v1.sh           # 启动脚本
├── requirements_v1.txt          # 依赖包列表
├── README_v1.md                 # 详细说明文档
├── core/                        # 核心算法文件
│   ├── pr_enhanced_schema.py    # 图谱模式定义
│   ├── pr_entity_extractor.py   # 实体关系提取器
│   ├── pr_enhanced_neo4j_integration.py  # Neo4j集成
│   ├── pr_enhanced_rag.py       # 增强RAG系统
│   ├── pr_multi_format_preprocessing.py  # 多格式预处理
│   ├── pr_chunking.py          # 文本分块
│   ├── pr_neo4j_env.py         # Neo4j环境配置
│   └── pr_txt2json.py          # 文本转JSON
├── tools/                       # 工具模块
│   ├── chunk_editor.py          # Chunk编辑工具
│   ├── incremental_processor.py # 增量处理器
│   ├── neo4j_direct_query.py   # 直接Neo4j查询
│   ├── ask_pr.py               # 问答工具
│   ├── quick_query.py          # 快速查询
│   └── cleanup_historical_data.py  # 历史数据清理
├── demos/                       # 演示和测试
│   ├── demo_enhanced_pr_rag.py  # 功能演示
│   ├── test_enhanced_pr_rag.py  # 完整测试
│   ├── demo_direct_query.py     # 直接查询演示
│   └── demo_direct_query_simple.py  # 简单演示
├── docs/                        # 文档
│   ├── Enhanced_PR_RAG_Guide.md # 详细使用指南
│   ├── PR_RAG_Advanced_Guide.md # 高级功能指南
│   └── Neo4j_Direct_Query_Guide.md  # 直接查询指南
├── config/                      # 配置文件
│   ├── .env                     # 环境变量
│   └── requirements_v1.txt      # 依赖包列表
└── data/                        # 数据目录
    ├── raw/                     # 原始数据
    ├── cleaned/                 # 清理后数据
    ├── json/                    # JSON格式数据
    └── chunks/                  # 分块数据
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r config/requirements_v1.txt

# 配置环境变量
cp config/.env.example config/.env
# 编辑 config/.env 文件
```

### 2. 启动系统

```bash
# 使用启动脚本
./start_pr_rag_v1.sh

# 或直接启动主程序
python3 pr_rag_system_v1.py
```

## 📊 核心功能

- ✅ 智能实体识别 (品牌、企业、媒体、活动等)
- ✅ 关系提取 (合作、竞争、媒体投放等)
- ✅ 增强RAG查询 (GraphRAG + VectorRAG)
- ✅ 多格式文档处理 (PDF、Word、Excel、PPT等)
- ✅ 增量处理 (只处理新文件)
- ✅ Chunk编辑 (人工优化数据)

## 🔧 版本信息

- **版本**: v1.0
- **发布日期**: 2025-10-22
- **主要改进**: 增强实体识别、丰富关系类型、优化RAG查询

## 📚 详细文档

请查看 `docs/` 目录下的详细文档：
- [Enhanced_PR_RAG_Guide.md](docs/Enhanced_PR_RAG_Guide.md) - 详细使用指南
- [PR_RAG_Advanced_Guide.md](docs/PR_RAG_Advanced_Guide.md) - 高级功能指南
- [Neo4j_Direct_Query_Guide.md](docs/Neo4j_Direct_Query_Guide.md) - 直接查询指南

## 🧪 测试和演示

```bash
# 功能演示
python3 demos/demo_enhanced_pr_rag.py

# 完整测试
python3 demos/test_enhanced_pr_rag.py

# 快速查询
python3 tools/ask_pr.py "你的问题"
```

## 📞 技术支持

如有问题，请检查：
1. 环境配置是否正确
2. Neo4j数据库是否正常运行
3. OpenAI API是否可用
4. 数据格式是否正确

---

**公关传播RAG系统 v1.0** - 让公关传播更智能！
