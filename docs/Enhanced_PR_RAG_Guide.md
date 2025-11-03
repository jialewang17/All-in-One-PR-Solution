# 增强公关传播RAG系统使用指南

## 🎯 系统概述

这个增强的公关传播RAG系统解决了原有系统的两个关键问题：

1. **实体识别不足** - 现在能够识别企业、品牌、平台等实体
2. **关系定义缺乏** - 现在支持公关传播特有的关系类型

## 🏗️ 系统架构

### 核心组件

1. **`pr_enhanced_schema.py`** - 图谱模式定义
2. **`pr_entity_extractor.py`** - 实体和关系提取器
3. **`pr_enhanced_neo4j_integration.py`** - 增强的Neo4j集成
4. **`pr_enhanced_rag.py`** - 增强的RAG系统
5. **`test_enhanced_pr_rag.py`** - 测试脚本

### 节点类型

| 节点类型 | 描述 | 主要属性 |
|---------|------|----------|
| **Brand** | 品牌节点 | name, industry, brand_positioning, brand_personality |
| **Company** | 企业节点 | name, industry, company_type, scale, market_position |
| **Agency** | 公关公司节点 | name, specialization, service_scope, reputation |
| **Campaign** | 传播活动节点 | name, campaign_type, key_message, status |
| **Media** | 媒体渠道节点 | name, media_type, reach, engagement_rate |
| **Strategy** | 传播策略节点 | name, strategy_type, target_audience, key_message |
| **Platform** | 平台节点 | platform_name, platform_type, user_base |
| **Influencer** | 意见领袖节点 | name, platform, followers, engagement_rate |
| **Content** | 内容节点 | content_type, format, theme, tone |
| **KPI** | 关键指标节点 | metric_name, target_value, actual_value |

### 关系类型

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

## 🚀 使用步骤

### 1. 运行增强集成

```bash
python3 pr_enhanced_neo4j_integration.py
```

这将：
- 创建增强的图谱模式
- 处理现有chunks并提取实体关系
- 创建实体节点和关系
- 生成嵌入向量

### 2. 测试系统功能

```bash
python3 test_enhanced_pr_rag.py
```

这将测试：
- 实体提取功能
- 关系识别功能
- RAG查询功能
- 实体关系查询

### 3. 使用增强的RAG系统

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

## 🔍 查询示例

### 实体关系查询

```cypher
// 查询品牌合作关系
MATCH (b:Brand)-[r:BRAND_COLLABORATION]->(partner:Brand)
WHERE b.name CONTAINS "华与华"
RETURN b.name, partner.name, r.description

// 查询媒体投放策略
MATCH (b:Brand)-[r:MEDIA_PLACEMENT]->(m:Media)
WHERE b.name CONTAINS "小米"
RETURN b.name, m.name, m.media_type, r.description

// 查询竞争关系
MATCH (b1:Brand)-[r:COMPETES_WITH]->(b2:Brand)
RETURN b1.name, b2.name, r.description
```

### 复杂关系查询

```cypher
// 查询品牌的完整传播生态
MATCH (b:Brand)-[r1:LAUNCHES_CAMPAIGN]->(c:Campaign)-[r2:USES_STRATEGY]->(s:Strategy)
WHERE b.name CONTAINS "奥迪"
RETURN b.name, c.name, s.strategy_type, s.target_audience

// 查询公关公司的客户关系
MATCH (a:Agency)-[r:HAS_AGENCY]-(b:Brand)
WHERE a.name CONTAINS "华与华"
RETURN a.name, b.name, r.service_scope
```

## 📊 系统优势

### 1. 精准实体识别
- 基于LLM的智能实体提取
- 支持多种实体类型识别
- 自动属性填充

### 2. 丰富关系类型
- 符合公关传播特点的关系定义
- 支持复杂关系查询
- 关系置信度评估

### 3. 增强的RAG能力
- GraphRAG + VectorRAG双重查询
- 智能Cypher查询生成
- 上下文感知的回答生成

### 4. 专业领域适配
- 针对公关传播领域优化
- 支持品牌、企业、媒体等实体
- 符合行业术语和概念

## 🔧 自定义配置

### 添加新的实体类型

在 `pr_enhanced_schema.py` 中添加：

```python
'NewEntity': {
    'description': '新实体类型',
    'properties': {
        'name': '实体名称',
        'property1': '属性1',
        'property2': '属性2'
    }
}
```

### 添加新的关系类型

```python
'NEW_RELATIONSHIP': {
    'description': '新关系类型',
    'from': ['Entity1', 'Entity2'],
    'to': ['Entity3', 'Entity4'],
    'properties': ['property1', 'property2']
}
```

### 自定义实体识别模式

```python
'new_entity_keywords': [
    '关键词1', '关键词2', '关键词3'
]
```

## 🐛 故障排除

### 常见问题

1. **实体提取失败**
   - 检查OpenAI API配置
   - 使用规则提取作为回退方案

2. **关系创建失败**
   - 检查Neo4j连接
   - 验证实体名称匹配

3. **Cypher查询错误**
   - 检查查询语法
   - 使用回退查询

### 调试模式

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 测试单个组件
extractor = EntityRelationshipExtractor()
entities = extractor.extract_entities_from_text("测试文本")
```

## 📈 性能优化

### 1. 批量处理
- 批量创建节点和关系
- 使用事务处理

### 2. 索引优化
- 为常用查询字段创建索引
- 优化Cypher查询性能

### 3. 缓存策略
- 缓存实体提取结果
- 缓存嵌入向量

## 🔮 未来扩展

### 1. 更多实体类型
- 添加KOL、内容创作者等实体
- 支持更细粒度的实体分类

### 2. 更复杂的关系
- 时间序列关系
- 因果关系
- 影响关系

### 3. 智能分析
- 关系强度分析
- 影响力计算
- 趋势预测

## 📞 技术支持

如有问题，请检查：
1. 环境配置是否正确
2. Neo4j数据库是否正常运行
3. OpenAI API是否可用
4. 数据格式是否正确

---

**注意**: 这个增强系统需要先运行 `pr_enhanced_neo4j_integration.py` 来创建实体和关系，然后才能使用增强的RAG功能。
