# Agent 分析工具

这个目录包含了用于分析和合并不同智能体系统的工具。

## 文件说明

- `agent_merge_analysis.py` - 智能体合并分析报告生成器
  - 分析两个智能体系统的架构和功能
  - 识别集成点
  - 生成合并计划

- `agent_merger.py` - 智能体合并工具
  - 分析智能体的代码流程
  - 检测冲突
  - 生成合并后的代码

## 使用说明

这些工具主要用于开发阶段，用于分析和整合不同的智能体系统。在生产环境中通常不需要使用这些工具。

### 运行合并分析

```bash
python3 agents/agent_merge_analysis.py
```

### 运行合并工具

```bash
python3 agents/agent_merger.py
```

## 注意事项

- 这些工具是开发辅助工具，不是核心系统组件
- 如果不需要上传到 GitHub，可以在 `.gitignore` 中添加 `agents/`

