# SPO知识图谱系统使用指南

本指南介绍如何使用整合的SPO（Subject-Predicate-Object）三元组提取和知识图谱构建功能。

## 概述

这个系统整合了Fareed Khan的知识图谱构建方法，实现了：

1. **SPO三元组提取**：使用LLM从非结构化文本中提取Subject-Predicate-Object三元组
2. **知识图谱构建**：使用NetworkX在内存中构建和管理知识图谱
3. **基于图谱的RAG**：利用图谱结构进行检索增强生成

## 核心模块

### 1. SPO三元组提取器 (`pr_spo_extractor.py`)

用于从文本中提取SPO三元组。

```python
from core.pr_spo_extractor import SPOTripleExtractor

# 初始化提取器
extractor = SPOTripleExtractor(
    model_name="deepseek/deepseek-chat-v3-0324",
    use_openrouter=True,
    temperature=0.0  # 0.0用于确定性提取
)

# 从文本提取三元组
result = extractor.extract_triples_from_text(
    text="你的文本内容...",
    chunk_size=150,  # 每块的词数
    overlap=30,       # 重叠词数
    verbose=True
)

# 归一化三元组
normalized = extractor.normalize_triples(result['triples'])
```

### 2. 知识图谱构建器 (`pr_kg_builder.py`)

使用NetworkX构建和管理知识图谱。

```python
from core.pr_kg_builder import KnowledgeGraphBuilder

# 创建图谱构建器
kg = KnowledgeGraphBuilder()

# 添加三元组
triples = [
    {'subject': 'entity1', 'predicate': 'relation', 'object': 'entity2'}
]
kg.add_triples(triples)

# 获取统计信息
stats = kg.get_statistics()

# 查找相关实体
related = kg.find_related_entities('entity1', max_hops=2)

# 导出图谱
kg.export_to_json('graph.json')
```

### 3. 基于图谱的RAG (`pr_kg_rag.py`)

利用知识图谱进行问答。

```python
from core.pr_kg_rag import KnowledgeGraphRAG
from core.pr_kg_builder import KnowledgeGraphBuilder

# 创建图谱
kg = KnowledgeGraphBuilder()
kg.add_triples(normalized_triples)

# 创建RAG系统
rag = KnowledgeGraphRAG(kg, use_openrouter=True)

# 回答问题
answer = rag.query(
    question="你的问题...",
    normalized_triples=normalized_triples
)
```

### 4. 集成系统 (`pr_integrated_kg_system.py`)

整合所有功能的便捷接口。

```python
from core.pr_integrated_kg_system import IntegratedKGSystem

# 初始化系统
system = IntegratedKGSystem(use_openrouter=True)

# 处理文本并构建图谱
result = system.process_text(
    text="你的文本内容...",
    chunk_size=150,
    overlap=30,
    verbose=True
)

# 查询
answer = system.query("你的问题...")

# 获取统计信息
stats = system.get_graph_statistics()

# 导出图谱
system.export_graph('graph.json')
```

### 5. 增强的实体提取器 (`pr_entity_extractor.py`)

原有的实体提取器现在支持SPO方法。

```python
from core.pr_entity_extractor import EntityRelationshipExtractor

# 使用SPO提取器
extractor = EntityRelationshipExtractor(
    use_spo_extractor=True,
    spo_config={
        'model_name': 'deepseek/deepseek-chat-v3-0324',
        'use_openrouter': True
    }
)

# 提取SPO三元组
spo_result = extractor.extract_spo_triples_from_text(
    text="你的文本...",
    chunk_size=150,
    overlap=30
)

# 或使用传统方法处理chunk
result = extractor.process_chunk(chunk_data)
```

## 配置

### 环境变量

设置以下环境变量之一：

```bash
# 使用OpenRouter（推荐）
export OPENROUTER_API_KEY="your-api-key"

# 或使用OpenAI
export OPENAI_API_KEY="your-api-key"
```

### 模型配置

默认使用 `deepseek/deepseek-chat-v3-0324`，你可以修改：

```python
system = IntegratedKGSystem(
    model_name="gpt-4o",  # 或其他模型
    use_openrouter=False  # 如果使用OpenAI
)
```

## 使用示例

### 示例1：完整流程

```python
from core.pr_integrated_kg_system import IntegratedKGSystem

# 1. 初始化
system = IntegratedKGSystem()

# 2. 处理文本
text = """
    你的非结构化文本内容...
    """
result = system.process_text(text, chunk_size=150, overlap=30)

# 3. 查看统计
stats = system.get_graph_statistics()
print(f"节点数: {stats['nodes']}, 边数: {stats['edges']}")

# 4. 查询
answer = system.query("你的问题...")
print(answer)

# 5. 导出
system.export_graph('my_knowledge_graph.json')
```

### 示例2：仅提取三元组

```python
from core.pr_spo_extractor import SPOTripleExtractor

extractor = SPOTripleExtractor()
result = extractor.extract_triples_from_text(text)

# 查看提取的三元组
for triple in result['triples'][:10]:
    print(f"{triple['subject']} --[{triple['predicate']}]--> {triple['object']}")
```

### 示例3：使用实体提取器

```python
from core.pr_entity_extractor import EntityRelationshipExtractor

extractor = EntityRelationshipExtractor(use_spo_extractor=True)

# 处理chunk（自动使用SPO方法）
chunk_data = {
    'text': '你的文本...',
    'chunkId': 'chunk-001'
}
result = extractor.process_chunk(chunk_data)

# 查看结果
print(result['spo_triples'])  # SPO三元组
print(result['entities'])     # 实体
print(result['relationships'])  # 关系
```

## 运行演示

运行完整的演示：

```bash
python demo_spo_kg_system.py
```

或运行集成系统的内置演示：

```python
from core.pr_integrated_kg_system import demo_integrated_system

demo_integrated_system()
```

## 注意事项

1. **API密钥**：确保设置了正确的API密钥环境变量
2. **分块参数**：根据文本长度和复杂度调整`chunk_size`和`overlap`
3. **模型选择**：某些模型可能不支持`temperature=0.0`或`response_format`，系统会自动处理
4. **内存使用**：大规模文本处理可能需要较多内存，建议分批处理
5. **错误处理**：提取失败时会自动回退到规则提取（如果可用）

## 性能优化

1. **调整chunk_size**：较小的块可以提高提取精度，但会增加API调用次数
2. **调整overlap**：适当的重叠可以保持上下文连贯性
3. **批量处理**：对于大量文本，考虑分批处理并合并结果
4. **缓存结果**：保存提取的三元组，避免重复处理

## 故障排除

### 问题：API调用失败

**解决方案**：
- 检查API密钥是否正确设置
- 确认网络连接正常
- 检查API额度是否充足

### 问题：提取结果为空

**解决方案**：
- 检查文本是否为空或过短
- 尝试调整`chunk_size`参数
- 检查模型是否支持JSON输出格式

### 问题：内存不足

**解决方案**：
- 减小`chunk_size`
- 分批处理文本
- 清理不需要的图谱数据

## 扩展功能

### 自定义提示词

可以修改`pr_spo_extractor.py`中的提示词模板以适应特定领域：

```python
# 修改 extraction_user_prompt_template
```

### 集成到Neo4j

可以将NetworkX图谱数据导出并导入到Neo4j：

```python
# 导出图谱
kg.export_to_json('graph.json')

# 使用现有的Neo4j集成模块导入
```

## 参考文献

- 原始方法：Fareed Khan - Converting Unstructured Data into a Knowledge Graph
- 文章链接：https://levelup.gitconnected.com/converting-unstructured-data-into-a-knowledge-graph-using-an-end-to-end-pipeline-552a508045f9


