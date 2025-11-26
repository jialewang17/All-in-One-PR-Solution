# 一体化个人助理工具 API 文档

## 快速开始

### 启动后端服务

```bash
# 安装依赖
pip install -r config/requirements_v1.txt

# 启动 FastAPI 服务
python api/main.py

# 或使用 uvicorn 直接启动
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后，访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/health

## API 端点

### 知识查询

#### POST /api/knowledge/query
查询知识库

**请求体：**
```json
{
  "query": "什么是公关传播策略？",
  "use_graph": true
}
```

**响应：**
```json
{
  "answer": "公关传播策略是...",
  "sources": []
}
```

### 方案生成

#### POST /api/plan/generate
生成公关传播方案

**请求体：**
```json
{
  "enterprise_info": {
    "enterprise_name": "示例公司",
    "enterprise_stage": "中小微企业",
    "industry": "科技",
    "market_type": "ToC",
    "pr_goal": "品牌认知"
  },
  "output_types": ["A", "B", "C"]
}
```

### 笔记管理

#### GET /api/vault/status
获取同步状态

#### POST /api/vault/sync
手动触发全量同步

#### GET /api/vault/files
列出所有已索引文件

#### GET /api/vault/notes/{note_id}
获取笔记内容

#### POST /api/vault/notes
创建新笔记

#### PUT /api/vault/notes/{note_id}
更新笔记

#### DELETE /api/vault/notes/{note_id}
删除笔记

#### GET /api/vault/search?q={query}
搜索笔记

### TrendRadar

#### GET /api/trendradar/ups
获取 Up主列表

#### POST /api/trendradar/ups
添加 Up主

#### DELETE /api/trendradar/ups/{uid}
删除 Up主

#### GET /api/trendradar/topics
获取议题列表（支持分页和筛选）

#### GET /api/trendradar/topics/{topic_id}
获取议题详情

#### GET /api/trendradar/trends?period=week
获取趋势分析

#### POST /api/trendradar/config
更新配置

#### GET /api/trendradar/report
生成报告

## WebSocket

### /ws
WebSocket 端点用于实时通信

连接后可以发送消息，服务器会回显。

## 配置

### unified_config.yaml

添加了以下配置段：

```yaml
vault:
  enabled: true
  path: "/Users/biaowenhuang/Documents/sanhu_vault"
  watch_enabled: true
  sync_interval: 60

trendradar:
  enabled: true
  bilibili:
    crawl_interval: 3600
    max_videos_per_up: 50
  ai_topics:
    keywords: ["AI", "大模型", "LLM", ...]
    min_relevance_score: 0.7
```

### config/trendradar.yaml

TrendRadar 独立配置文件，包含 Up主列表和 AI 关键词。

## 下一步

前端开发（Vue 3 + TypeScript）将在后续实现。

