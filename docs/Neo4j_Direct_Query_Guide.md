# Neo4j直接查询系统使用指南

## 🎯 功能概述

这个系统允许你直接从Neo4j数据库中查询公关传播RAG，跳过所有预处理步骤。你可以在Neo4j平台上直接创建节点和关系，然后使用这个系统进行智能问答。

## 📁 文件说明

### 1. `ask_pr.py` - 命令行快速查询（推荐）
**最简单的使用方式**

```bash
python3 ask_pr.py "你的问题"
```

**示例：**
```bash
python3 ask_pr.py "美妆类品牌应该如何建立和消费者的联系"
python3 ask_pr.py "华与华有哪些成功的品牌案例"
python3 ask_pr.py "内容营销的核心策略是什么"
```

### 2. `quick_query.py` - 快速查询示例
**展示如何使用查询功能**

```bash
python3 quick_query.py
```

### 3. `neo4j_direct_query.py` - 交互式查询系统
**提供多种查询方式和交互界面**

```bash
python3 neo4j_direct_query.py
```

## 🚀 快速开始

### 前提条件
1. **Neo4j数据库运行中**
2. **已导入PR_Chunk节点**（通过之前的处理流程或直接在Neo4j中创建）
3. **环境变量配置正确**（.env文件）

### 最简单的使用方式
```bash
# 直接询问问题
python3 ask_pr.py "你的问题"
```

## 🔧 在Neo4j中直接创建数据

### 创建PR_Chunk节点
```cypher
// 创建品牌案例节点
CREATE (c:PR_Chunk {
  chunkId: "brand_case_001",
  text: "雅诗兰黛通过沉浸式体验活动建立与消费者的联系，包括肌肤检测、SPA、瑜伽等环节",
  source: "雅诗兰黛案例",
  formItem: "品牌策略",
  chunkSeqId: 0,
  content_type: "brand_strategy",
  industry: "beauty",
  brand_mentioned: ["雅诗兰黛"]
})

// 创建营销策略节点
CREATE (c:PR_Chunk {
  chunkId: "marketing_strategy_001", 
  text: "内容营销的核心是通过有价值的内容吸引目标受众，建立品牌认知和信任",
  source: "营销策略文档",
  formItem: "内容营销",
  chunkSeqId: 0,
  content_type: "strategy",
  industry: "marketing",
  brand_mentioned: []
})
```

### 创建关系
```cypher
// 创建NEXT关系连接相关chunks
MATCH (c1:PR_Chunk {chunkId: "brand_case_001"})
MATCH (c2:PR_Chunk {chunkId: "marketing_strategy_001"})
CREATE (c1)-[:NEXT]->(c2)
```

### 创建向量索引
```cypher
// 创建向量索引（如果还没有）
CREATE VECTOR INDEX PR_OpenAI IF NOT EXISTS
FOR (c:PR_Chunk) ON (c.textEmbeddingOpenAI)
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}}
```

### 添加向量嵌入
```cypher
// 为节点添加向量嵌入（需要OpenAI API）
MATCH (c:PR_Chunk)
WHERE c.textEmbeddingOpenAI IS NULL
CALL apoc.ml.openai.embedding([c.text], 'your-openai-api-key') YIELD embeddings
SET c.textEmbeddingOpenAI = embeddings[0]
```

## 📊 查询方式

### 1. 向量搜索（推荐）
- 使用语义相似度搜索
- 找到最相关的内容
- 适合复杂问题

### 2. Cypher查询
- 使用关键词匹配
- 精确匹配特定字段
- 适合结构化查询

## 🎯 使用场景

### 场景1: 快速问答
```bash
python3 ask_pr.py "如何提升品牌知名度"
```

### 场景2: 批量查询
```python
from ask_pr import ask_question

questions = [
    "美妆品牌如何建立消费者联系",
    "内容营销策略有哪些",
    "华与华的成功案例"
]

for q in questions:
    answer = ask_question(q)
    print(f"问题: {q}")
    print(f"回答: {answer}")
    print("-" * 50)
```

### 场景3: 交互式查询
```bash
python3 neo4j_direct_query.py
```

## 🔍 数据要求

### 必需的节点属性
- `chunkId`: 唯一标识符
- `text`: 文本内容
- `textEmbeddingOpenAI`: 向量嵌入（用于向量搜索）

### 可选的节点属性
- `content_type`: 内容类型
- `industry`: 行业分类
- `brand_mentioned`: 提及的品牌
- `source`: 来源文件
- `formItem`: 所属section

### 必需的关系
- `NEXT`: 连接相关chunks

## ⚠️ 注意事项

### 数据质量
- 确保文本内容质量高
- 正确设置content_type和industry
- 及时更新brand_mentioned字段

### 性能优化
- 定期检查向量索引状态
- 清理孤立的节点
- 监控查询性能

### 错误处理
- 检查Neo4j连接状态
- 验证API密钥配置
- 查看错误日志

## 🚀 高级功能

### 自定义查询
```python
from neo4j_direct_query import Neo4jDirectQuery

query_system = Neo4jDirectQuery()

# 使用向量搜索
answer = query_system.query("你的问题", method="vector")

# 使用Cypher查询
answer = query_system.query("你的问题", method="cypher")
```

### 批量处理
```python
questions = ["问题1", "问题2", "问题3"]
answers = []

for question in questions:
    answer = ask_question(question)
    answers.append({"question": question, "answer": answer})
```

## 📈 最佳实践

### 1. 数据组织
- 按行业分类组织chunks
- 设置合适的content_type
- 建立清晰的NEXT关系

### 2. 查询优化
- 使用具体的查询词
- 结合多个关键词
- 利用行业和品牌信息

### 3. 结果分析
- 关注相关文档数量
- 分析回答质量
- 持续优化数据

## 🔧 故障排除

### 常见问题
1. **"未找到相关信息"** - 检查Neo4j中是否有PR_Chunk节点
2. **"向量索引不可用"** - 检查向量索引是否正确创建
3. **"查询失败"** - 检查API密钥和网络连接

### 解决方案
1. 运行数据导入流程
2. 重新创建向量索引
3. 检查环境变量配置

---

**推荐使用**: `ask_pr.py` 是最简单直接的使用方式，适合快速查询和测试。


