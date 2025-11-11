# RLHF系统使用指南

## 概述

本系统实现了基于人类反馈的强化学习（RLHF）机制，用于持续改进公关传播方案的生成质量。系统包括以下核心组件：

1. **品牌知识管理系统** - 管理品牌信息和知识
2. **方法论规则库** - 管理品牌传播方法论规则
3. **反馈收集系统** - 收集用户对生成方案的反馈
4. **质量评估系统** - 自动和人工评估方案质量
5. **RLHF系统** - 基于反馈训练奖励模型并优化生成策略

## 功能特性

### 1. 品牌知识管理

#### 导入品牌知识

支持从JSON、CSV、Excel文件导入品牌信息：

```python
from core.pr_knowledge_manager import BrandKnowledgeManager

manager = BrandKnowledgeManager()

# 从JSON导入
result = manager.import_brands_from_json('data/brands.json')

# 从CSV导入
result = manager.import_brands_from_csv('data/brands.csv')

# 从Excel导入
result = manager.import_brands_from_excel('data/brands.xlsx')
```

#### 品牌数据格式

JSON格式示例：

```json
{
  "name": "品牌名称",
  "industry": "行业",
  "brand_positioning": "品牌定位",
  "brand_personality": "品牌个性",
  "target_audience": "目标受众",
  "founded_year": "成立年份",
  "characteristics": "品牌特点"
}
```

#### 查询品牌信息

```python
# 获取品牌信息
brand = manager.get_brand('品牌名称')

# 搜索品牌
brands = manager.search_brands('关键词', industry='行业')

# 获取品牌历史案例
history = manager.get_brand_history('品牌名称')
```

### 2. 方法论规则管理

#### 导入规则

```python
from core.pr_methodology_rules import MethodologyRulesManager

manager = MethodologyRulesManager()

# 从JSON导入规则
result = manager.import_rules_from_json('data/rules.json')
```

#### 规则数据格式

```json
{
  "rule_id": "rule_001",
  "rule_type": "industry",
  "name": "规则名称",
  "description": "规则描述",
  "conditions": {
    "industry": "科技",
    "pr_goal": ["品牌认知", "用户增长"]
  },
  "application_scenarios": ["brand_awareness"],
  "priority": 10,
  "effects": {
    "emphasis": "创新、技术"
  },
  "content": "规则内容"
}
```

#### 获取适用规则

```python
context = {
    'industry': '科技',
    'pr_goal': '品牌认知',
    'scenario': 'brand_awareness'
}

rules = manager.get_applicable_rules(context)
```

### 3. 反馈收集

#### 收集反馈

```python
from core.pr_feedback_collector import FeedbackCollector

collector = FeedbackCollector()

result = collector.collect_feedback(
    plan_id="plan_001",
    feedback_type="rating",
    rating=4.5,
    comment="方案很好",
    categories={
        'relevance': 'high',
        'innovation': 'medium',
        'feasibility': 'high'
    },
    suggestions=["增加更多案例"],
    knowledge_sources=["brand_knowledge"],
    plan_type="A"
)
```

#### 分析反馈

```python
# 分析特定方案的反馈
analysis = collector.analyze_feedback(plan_id="plan_001")

# 分析所有反馈
analysis = collector.analyze_feedback()
```

### 4. 质量评估

#### 自动评估

```python
from core.pr_quality_evaluator import QualityEvaluator

evaluator = QualityEvaluator()

assessment = evaluator.evaluate_plan(
    plan_id="plan_001",
    plan_content="方案内容",
    context={
        'brand': '品牌名称',
        'industry': '行业',
        'pr_goal': '目标'
    }
)

print(f"总体评分: {assessment.overall_score}")
for score in assessment.metric_scores:
    print(f"{score.metric}: {score.score}")
```

#### 人工评估

```python
assessment = evaluator.human_evaluate_plan(
    plan_id="plan_001",
    metric_scores={
        'relevance': 0.9,
        'innovation': 0.8,
        'feasibility': 0.85
    },
    overall_score=0.85,
    comments="评估意见",
    improvements=["改进建议"]
)
```

### 5. RLHF系统

#### 使用统一系统

```python
from unified_pr_system import UnifiedPRSystem

# 初始化系统（启用RLHF）
system = UnifiedPRSystem(enable_rlhf=True)

# 导入品牌知识
system.import_brand_knowledge('data/brands.json', format='json')

# 导入方法论规则
system.import_methodology_rules('data/rules.json')

# 生成方案
enterprise_info = {
    'enterprise_name': '品牌名称',
    'industry': '科技',
    'pr_goal': '品牌认知'
}
result = system.generate_pr_plan(enterprise_info, ["A", "B"])

# 收集反馈
system.collect_feedback(
    plan_id="plan_001",
    rating=4.5,
    comment="很好的方案"
)

# 获取学习进度
progress = system.get_learning_progress()
```

## 配置

### 启用RLHF功能

在 `unified_config.yaml` 中添加RLHF配置：

```yaml
# RLHF配置
rlhf:
  enabled: true
  feedback_db_path: "./data/feedback.db"
  min_feedback_for_training: 10
  training_interval: 100  # 每100条反馈触发一次训练
  reward_model_path: "./models/reward_model.json"
```

## 工作流程

### 1. 初始化阶段

1. 导入品牌知识库
2. 导入方法论规则库
3. 初始化RLHF系统

### 2. 方案生成阶段

1. 系统根据企业信息检索品牌知识
2. 匹配适用的方法论规则
3. 生成方案并自动评估质量
4. 返回方案和质量评分

### 3. 反馈收集阶段

1. 用户对方案进行评分和评论
2. 系统收集反馈数据
3. 分析反馈模式和趋势

### 4. 学习优化阶段

1. 当收集到足够反馈时，触发RLHF训练
2. 训练奖励模型
3. 优化生成策略
4. 评估改进效果

## 最佳实践

### 1. 品牌知识管理

- 定期更新品牌信息
- 确保品牌数据准确性
- 建立品牌知识验证机制

### 2. 规则管理

- 定义清晰的规则条件
- 设置合理的规则优先级
- 定期审查和更新规则

### 3. 反馈收集

- 鼓励用户提供详细反馈
- 收集结构化反馈数据
- 定期分析反馈趋势

### 4. 质量评估

- 结合自动和人工评估
- 建立评估标准
- 跟踪评估结果

### 5. RLHF训练

- 确保有足够的训练数据
- 定期触发训练
- 监控训练效果
- 建立模型版本管理

## 故障排除

### RLHF功能未启用

检查：
1. 是否正确导入RLHF模块
2. 配置文件是否正确
3. 依赖是否安装完整

### 反馈数据不足

解决：
1. 收集更多用户反馈
2. 降低训练数据阈值
3. 使用模拟数据

### 训练失败

检查：
1. 训练数据格式是否正确
2. 模型路径是否可写
3. 系统资源是否充足

## 示例

参见 `demos/demo_rlhf_system.py` 了解完整的使用示例。

## 相关文档

- [统一系统使用指南](README_v1.md)
- [RAG系统指南](PR_RAG_Advanced_Guide.md)
- [知识图谱指南](SPO_Knowledge_Graph_Guide.md)



