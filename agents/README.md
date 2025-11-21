# Agent 分析工具

该目录包含用于分析和合并不同智能体系统的脚本。现在根据职责拆分为两个子包：

- `agents/analysis/`：合并分析（`AgentMergerAnalysis`）
- `agents/merger/`：代码级合并器（`AgentMerger`）

## 使用说明

这些工具主要服务于开发阶段，在生产环境中通常无需运行。

### 运行合并分析

```bash
python agents/agent_merge_analysis.py
```

- 或在代码中使用：`from agents.analysis import AgentMergerAnalysis`

### 运行合并工具

```bash
python agents/agent_merger.py
```

- 或在代码中使用：`from agents.merger import AgentMerger`

## 注意事项

- 这些工具是开发辅助工具，不是核心系统组件
- 如无需纳入版本管理，可在 `.gitignore` 中忽略 `agents/`
