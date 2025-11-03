# 公关传播RAG系统 v1.0

## 🎯 系统概述

公关传播RAG系统 v1.0 是一个基于Neo4j的增强版知识图谱RAG系统，专门用于分析公关公司案例、品牌传播方案等内容。本版本解决了原有系统的两个关键问题：

1. **实体识别不足** - 现在能够精准识别企业、品牌、平台等实体
2. **关系定义缺乏** - 现在支持公关传播特有的关系类型

## 🏗️ 系统架构

### 核心组件

```
公关传播RAG系统 v1.0
├── pr_rag_system_v1.py          # 主入口程序
├── pr_rag_config_v1.py          # 系统配置
├── pr_enhanced_schema.py        # 图谱模式定义
├── pr_entity_extractor.py       # 实体关系提取器
├── pr_enhanced_neo4j_integration.py  # 增强Neo4j集成
├── pr_enhanced_rag.py          # 增强RAG系统
├── pr_multi_format_preprocessing.py  # 多格式预处理
├── pr_chunking.py              # 文本分块
├── pr_neo4j_env.py            # Neo4j环境配置
└── pr_txt2json.py             # 文本转JSON
```

### 工具模块

```
工具模块
├── chunk_editor.py             # Chunk编辑工具
├── incremental_processor.py    # 增量处理器
├── neo4j_direct_query.py      # 直接Neo4j查询
├── ask_pr.py                  # 问答工具
├── quick_query.py             # 快速查询
└── cleanup_historical_data.py # 历史数据清理
```

### 演示和测试

```
演示和测试
├── demo_enhanced_pr_rag.py    # 功能演示
├── test_enhanced_pr_rag.py    # 完整测试
├── demo_direct_query.py       # 直接查询演示
└── demo_direct_query_simple.py # 简单演示
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置Neo4j和OpenAI API信息
```

### 2. 启动系统

```bash
# 启动主程序
python3 pr_rag_system_v1.py
```

### 3. 选择操作模式

系统提供多种操作模式：

- **完整处理** - 处理所有文件
- **增量处理** - 只处理新文件
- **Chunk编辑** - 编辑已有chunks
- **增强RAG查询** - 使用新的实体关系系统
- **直接Neo4j查询** - 绕过预处理直接查询
- **功能演示** - 展示系统功能

## 📊 核心功能

### 1. 智能实体识别

系统能够识别以下实体类型：

| 实体类型 | 描述 | 主要属性 |
|---------|------|----------|
| **Brand** | 品牌节点 | name, industry, brand_positioning, brand_personality |
| **Company** | 企业节点 | name, industry, company_type, scale, market_position |
| **Agency** | 公关公司节点 | name, specialization, service_scope, reputation |
| **Campaign** | 传播活动节点 | name, campaign_type, key_message, status |
| **Strategy** | 传播策略节点 | name, strategy_type, target_audience, key_message |
| **Media** | 媒体渠道节点 | name, media_type, reach, engagement_rate |
| **Platform** | 平台节点 | platform_name, platform_type, user_base |
| **Influencer** | 意见领袖节点 | name, platform, followers, engagement_rate |
| **Content** | 内容节点 | content_type, format, theme, tone |
| **KPI** | 关键指标节点 | metric_name, target_value, actual_value |

### 2. 关系类型

系统支持以下关系类型：

| 关系类型 | 描述 | 示例 |
|---------|------|------|
| **BELONGS_TO** | 隶属于 | 品牌隶属于企业 |
| **COLLABORATES_WITH** | 合作关系 | 企业间商业合作 |
| **BRAND_COLLABORATION** | 品牌联名 | 品牌间联名合作 |
| **MEDIA_PLACEMENT** | 媒体投放 | 品牌在媒体平台投放 |
| **COMPETES_WITH** | 竞争关系 | 品牌间竞争 |
| **LAUNCHES_CAMPAIGN** | 发起活动 | 品牌发起传播活动 |
| **USES_STRATEGY** | 使用策略 | 活动使用传播策略 |
| **CREATES_CONTENT** | 创建内容 | 品牌创建内容 |
| **MEASURES_KPI** | 测量指标 | 活动测量KPI |

### 3. 增强RAG查询

- **GraphRAG**: 基于实体和关系的结构化查询
- **VectorRAG**: 基于语义相似性的向量查询
- **智能Cypher生成**: 自动生成专业查询语句
- **多跳关系推理**: 支持复杂关系分析

## 📁 数据流程

```
数据输入 → 预处理 → JSON转换 → 分块处理 → 实体识别 → Neo4j集成 → RAG查询
    ↓         ↓         ↓         ↓         ↓         ↓         ↓
data/raw/ → data/cleaned/ → data/json/ → data/chunks/ → 实体节点 → 知识图谱 → 智能回答
```

## 🔍 使用示例

### 1. 启动系统

```bash
python3 pr_rag_system_v1.py
```

### 2. 选择操作模式

```
🚀 请选择操作模式:

📊 数据处理模式:
  1. 完整处理 - 处理所有文件
  2. 增量处理 - 只处理新文件
  3. Chunk编辑 - 编辑已有chunks

🔍 查询模式:
  5. 增强RAG查询 - 使用新的实体关系系统
  6. 直接Neo4j查询 - 绕过预处理直接查询
  7. 快速查询 - 简单问答模式

请选择 (1-13): 5
```

### 3. 使用增强RAG查询

```python
from pr_enhanced_rag import EnhancedPRRAGSystem

# 初始化系统
rag_system = EnhancedPRRAGSystem()

# GraphRAG查询
answer = rag_system.query("华与华有哪些品牌合作案例？", use_graph=True)

# VectorRAG查询
answer = rag_system.query("小米在哪些媒体平台进行推广？", use_graph=False)

# 获取实体关系
relationships = rag_system.get_entity_relationships("华与华")

# 获取品牌合作
collaborations = rag_system.get_brand_collaborations("小米")

# 获取媒体策略
strategies = rag_system.get_media_strategies("奥迪")
```

## 📊 系统优势

### 1. 专业领域适配
- 专门针对公关传播领域设计
- 支持品牌、企业、媒体等实体识别
- 涵盖公关传播的各类关系

### 2. 智能实体识别
- 基于LLM+规则的智能实体提取
- 支持多种实体类型和属性
- 自动属性填充和关系建立

### 3. 增强查询能力
- GraphRAG + VectorRAG双重能力
- 智能Cypher查询生成
- 多跳关系推理

### 4. 高效处理
- 增量处理，只处理新文件
- 支持多种文档格式
- 人工优化数据质量

## 🔧 配置说明

### 环境变量配置

```bash
# Neo4j配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# OpenAI配置
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 系统配置

```python
# 查看系统配置
python3 pr_rag_config_v1.py

# 检查模块状态
python3 pr_rag_config_v1.py
```

## 📚 文档和指南

- [Enhanced_PR_RAG_Guide.md](Enhanced_PR_RAG_Guide.md) - 详细使用指南
- [PR_RAG_Advanced_Guide.md](PR_RAG_Advanced_Guide.md) - 高级功能指南
- [Neo4j_Direct_Query_Guide.md](Neo4j_Direct_Query_Guide.md) - 直接查询指南

## 🧪 测试和演示

### 功能演示

```bash
# 运行功能演示
python3 demo_enhanced_pr_rag.py
```

### 完整测试

```bash
# 运行完整测试
python3 test_enhanced_pr_rag.py
```

### 快速查询

```bash
# 快速问答
python3 ask_pr.py "华与华有哪些品牌合作案例？"
```

## 🔮 实际应用场景

### 1. 品牌合作分析
- 查询品牌间的合作关系
- 分析合作效果和影响
- 发现潜在合作机会

### 2. 媒体投放策略
- 分析品牌的媒体投放策略
- 评估不同媒体的效果
- 优化媒体投放组合

### 3. 竞争关系分析
- 了解品牌间的竞争态势
- 分析竞争策略和效果
- 制定差异化策略

### 4. 传播活动查询
- 查询品牌的活动历史
- 分析活动效果和影响
- 学习成功案例经验

### 5. 策略效果评估
- 评估传播策略的效果
- 分析KPI达成情况
- 优化策略执行

## 🐛 故障排除

### 常见问题

1. **环境配置问题**
   - 检查.env文件配置
   - 确认Neo4j数据库运行状态
   - 验证OpenAI API密钥

2. **模块导入失败**
   - 检查Python路径
   - 确认依赖包安装
   - 验证文件完整性

3. **Neo4j连接失败**
   - 检查数据库服务状态
   - 验证连接参数
   - 确认网络连接

### 调试模式

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查系统状态
python3 pr_rag_system_v1.py
# 选择 "10. 系统状态检查"
```

## 📈 性能优化

### 1. 批量处理
- 批量创建节点和关系
- 使用事务处理
- 优化Cypher查询

### 2. 索引优化
- 为常用查询字段创建索引
- 优化向量索引配置
- 定期维护数据库

### 3. 缓存策略
- 缓存实体提取结果
- 缓存嵌入向量
- 使用Redis缓存

## 🔮 未来规划

### v1.1 计划功能
- 更多实体类型支持
- 更复杂的关系类型
- 时间序列分析
- 影响力计算

### v1.2 计划功能
- 多语言支持
- 实时数据更新
- 可视化界面
- API接口

## 📞 技术支持

如有问题，请检查：

1. 环境配置是否正确
2. Neo4j数据库是否正常运行
3. OpenAI API是否可用
4. 数据格式是否正确

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🙏 致谢

感谢所有贡献者和用户的支持！

---

**公关传播RAG系统 v1.0** - 让公关传播更智能！
