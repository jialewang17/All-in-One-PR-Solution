## Why

当前的实体提取和关系建立存在以下问题：
1. SPO 三元组提取和传统实体提取流程分离，导致数据不一致和重复工作
2. 提取准确性不够高，特别是对于非结构化数据（公关传播方案、行业研究、案例等）
3. RAG 系统的数据质量缺乏科学的数据质量评估和验证机制
4. 不同提取方法的结果缺乏统一和验证

为了提高 RAG 系统的科学性和数据质量，需要合并 SPO 三元组提取和实体提取流程，建立统一的数据质量评估体系，并针对非结构化数据优化提取准确性。

## What Changes

- 合并 SPO 三元组提取和实体提取流程，创建统一的提取管道
- 改进 LLM 提示词和提取策略，提高实体和关系提取的准确性
- 建立数据质量评估机制，包括准确性验证、一致性检查、完整性评估
- 针对非结构化数据（公关传播方案、行业研究、媒体传播方法、工具操作、品牌案例）优化提取
- 实现提取结果的后处理和验证流程
- 建立数据质量报告和监控机制
- 优化知识图谱构建，确保高质量的三元组数据

## Impact

- Affected specs: 
  - `entity-extraction` (MODIFIED) - 合并提取流程，改进准确性
  - `knowledge-graph` (MODIFIED) - 优化图谱构建，提高数据质量
  - `pr-rag-system` (MODIFIED) - 建立数据质量评估机制
- Affected code: 
  - `core/pr_entity_extractor.py` - 合并 SPO 提取，改进提取逻辑
  - `core/pr_spo_extractor.py` - 优化 SPO 提取准确性
  - `core/pr_integrated_kg_system.py` - 建立数据质量评估
  - `core/pr_enhanced_rag.py` - 添加数据质量验证
  - `core/pr_enhanced_schema.py` - 扩展实体和关系类型定义




