<!-- 96b452f7-0ef5-45d0-b7d9-abe3828ac33f fbb689e9-285c-4082-afa5-0d81933d5c4a -->
# 个人助理工具集成规范

## 1. 系统架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    Web Frontend (Vue 3)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ 知识查询  │  │ 方案生成  │  │ 笔记管理  │  │TrendRadar│ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/WebSocket
┌──────────────────────┴──────────────────────────────────┐
│              FastAPI Backend Server                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ UnifiedPR API│  │Vault Sync API│  │TrendRadar API│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼────┐  ┌──────▼──────┐  ┌───▼──────────┐
│  Neo4j KG  │  │ sanhu_vault  │  │ B站爬虫服务  │
│  Vector DB │  │ 文件系统     │  │ 议题追踪     │
└────────────┘  └──────────────┘  └──────────────┘
```

### 1.2 技术栈

**后端：**

- FastAPI (Python 3.10+)
- WebSocket 支持（实时同步）
- 文件系统监控（watchdog）
- 异步任务队列（Celery 或 asyncio）

**前端：**

- Vue 3 + TypeScript
- Vite 构建工具
- Pinia 状态管理
- Vue Router
- Element Plus / Naive UI（UI组件库）
- Axios（HTTP客户端）

**数据存储：**

- Neo4j（知识图谱）
- ChromaDB（向量存储）
- SQLite（配置、任务状态）
- 本地文件系统（sanhu_vault）

## 2. sanhu_vault 双向同步模块

### 2.1 功能需求

#### Requirement: 笔记索引与检索

系统 SHALL 能够索引 sanhu_vault 目录下的所有 Markdown 文件，并支持全文检索。

**实现细节：**

- 文件路径：`core/knowledge/vault_sync.py`
- 监控目录：`/Users/biaowenhuang/Documents/sanhu_vault`
- 支持格式：`.md` 文件
- 索引方式：提取文件内容、元数据（标题、标签、创建时间、修改时间）
- 存储位置：Neo4j 新增 `VaultNote` 节点类型，向量存储到 ChromaDB

**数据结构：**

```python
VaultNote {
    id: str (文件路径hash)
    title: str (从文件名或frontmatter提取)
    path: str (相对路径)
    content: str (Markdown内容)
    tags: List[str] (从frontmatter提取)
    created_at: datetime
    updated_at: datetime
    word_count: int
    links: List[str] (内部链接)
}
```

#### Requirement: 文件变更监控

系统 SHALL 实时监控 sanhu_vault 目录的文件变更（创建、修改、删除），并自动更新索引。

**实现细节：**

- 使用 `watchdog` 库监控文件系统事件
- 事件类型：`created`, `modified`, `deleted`, `moved`
- 防抖处理：500ms 内多次变更只处理最后一次
- 异步处理：使用后台任务队列避免阻塞

**API端点：**

- `GET /api/vault/status` - 获取同步状态
- `POST /api/vault/sync` - 手动触发全量同步
- `GET /api/vault/files` - 列出所有已索引文件
- `GET /api/vault/search?q={query}` - 搜索笔记

#### Requirement: 笔记写入功能

系统 SHALL 能够通过 API 创建、更新、删除 sanhu_vault 中的笔记文件。

**实现细节：**

- 文件路径：`core/knowledge/vault_writer.py`
- 支持操作：创建、更新、删除、重命名
- 格式保持：保留 frontmatter、链接格式
- 冲突处理：检测文件是否被外部修改，提供合并选项

**API端点：**

- `POST /api/vault/notes` - 创建新笔记
- `PUT /api/vault/notes/{note_id}` - 更新笔记
- `DELETE /api/vault/notes/{note_id}` - 删除笔记
- `POST /api/vault/notes/{note_id}/merge` - 合并冲突

#### Requirement: 笔记内容增强

系统 SHALL 在生成方案或回答查询时，能够引用并链接到相关笔记。

**实现细节：**

- RAG 检索时包含 vault 笔记内容
- 返回结果中包含笔记引用链接
- 支持从笔记中提取结构化信息（实体、关系）

### 2.2 实现文件

**核心模块：**

- `core/knowledge/vault_sync.py` - 同步管理器
- `core/knowledge/vault_indexer.py` - 索引器
- `core/knowledge/vault_writer.py` - 写入器
- `core/knowledge/vault_watcher.py` - 文件监控

**API路由：**

- `api/vault.py` - FastAPI 路由定义

**配置：**

- `unified_config.yaml` 新增 `vault` 配置段

## 3. TrendRadar 议题追踪模块

### 3.1 功能需求

#### Requirement: B站 Up主内容爬取

系统 SHALL 能够爬取指定 B站 Up主的视频更新、动态更新。

**实现细节：**

- 文件路径：`core/trendradar/bilibili_crawler.py`
- 爬取目标：视频列表、视频详情、动态列表
- 数据提取：标题、描述、发布时间、播放量、点赞数、评论数、标签
- 更新频率：可配置（默认每小时）
- 存储方式：Neo4j `BilibiliVideo` 节点，关联到 `Up主` 节点

**数据结构：**

```python
BilibiliUp {
    uid: str (Up主ID)
    name: str (Up主名称)
    avatar: str (头像URL)
    description: str (简介)
    follower_count: int (粉丝数)
}

BilibiliVideo {
    bvid: str (视频ID)
    title: str (标题)
    description: str (描述)
    up_uid: str (Up主ID)
    publish_time: datetime (发布时间)
    view_count: int (播放量)
    like_count: int (点赞数)
    comment_count: int (评论数)
    tags: List[str] (标签)
    duration: int (时长，秒)
    cover_url: str (封面URL)
}
```

**配置方式：**

- 通过前端界面添加 Up主（输入 UID 或链接）
- 配置文件：`config/trendradar.yaml`

#### Requirement: AI议题智能筛选

系统 SHALL 能够从爬取的内容中智能筛选与 AI/大模型相关的议题。

**实现细节：**

- 文件路径：`core/trendradar/ai_topic_filter.py`
- 筛选策略：
        - 关键词匹配（AI、大模型、LLM、GPT、Claude、Gemini等）
        - LLM 语义相似度（使用 embedding 计算）
        - 标题/描述/标签综合分析
- 可配置关注点：用户可自定义关注的关键词列表
- 优先级排序：根据相关性、热度、时间综合排序

**数据结构：**

```python
AITopic {
    id: str
    title: str
    source: str (来源：bilibili/other)
    source_id: str (原始内容ID)
    relevance_score: float (相关性分数 0-1)
    hot_score: float (热度分数)
    publish_time: datetime
    summary: str (AI生成的摘要)
    tags: List[str]
}
```

#### Requirement: 议题分析与报告

系统 SHALL 能够对收集的议题进行分析，生成趋势报告。

**实现细节：**

- 趋势分析：时间序列分析、关键词频率变化
- 情感分析：正面/中性/负面
- 关联分析：议题之间的关联关系
- 报告生成：每日/每周/每月自动生成报告

**API端点：**

- `GET /api/trendradar/topics` - 获取议题列表
- `GET /api/trendradar/topics/{topic_id}` - 获取议题详情
- `GET /api/trendradar/trends` - 获取趋势分析
- `POST /api/trendradar/ups` - 添加 Up主
- `DELETE /api/trendradar/ups/{uid}` - 删除 Up主
- `GET /api/trendradar/report` - 生成报告

### 3.2 实现文件

**核心模块：**

- `core/trendradar/bilibili_crawler.py` - B站爬虫
- `core/trendradar/ai_topic_filter.py` - AI议题筛选
- `core/trendradar/trend_analyzer.py` - 趋势分析
- `core/trendradar/scheduler.py` - 定时任务调度

**API路由：**

- `api/trendradar.py` - FastAPI 路由定义

**配置：**

- `config/trendradar.yaml` - TrendRadar 配置

## 4. Web 前端开发

### 4.1 项目结构

```
frontend/
├── src/
│   ├── main.ts              # 入口文件
│   ├── App.vue              # 根组件
│   ├── router/              # 路由配置
│   │   └── index.ts
│   ├── stores/              # Pinia 状态管理
│   │   ├── knowledge.ts    # 知识查询状态
│   │   ├── plan.ts          # 方案生成状态
│   │   ├── vault.ts         # 笔记管理状态
│   │   └── trendradar.ts    # TrendRadar状态
│   ├── views/               # 页面组件
│   │   ├── KnowledgeQuery.vue
│   │   ├── PlanGeneration.vue
│   │   ├── VaultManager.vue
│   │   └── TrendRadar.vue
│   ├── components/          # 通用组件
│   │   ├── ChatInterface.vue
│   │   ├── PlanForm.vue
│   │   ├── NoteEditor.vue
│   │   └── TopicCard.vue
│   ├── api/                 # API 客户端
│   │   ├── knowledge.ts
│   │   ├── plan.ts
│   │   ├── vault.ts
│   │   └── trendradar.ts
│   └── styles/              # 样式文件
│       └── main.css
├── public/                  # 静态资源
├── package.json
├── tsconfig.json
└── vite.config.ts
```

### 4.2 页面设计

#### 4.2.1 知识查询页面

**功能：**

- 类 ChatGPT 对话界面
- 支持多轮对话
- 显示知识来源（图谱节点、笔记链接）
- 支持语音输入（可选）

**UI组件：**

- 消息列表（用户/助手）
- 输入框（支持 Markdown）
- 发送按钮
- 清除对话按钮
- 知识来源标签

**状态管理：**

```typescript
interface KnowledgeState {
  messages: Message[]
  loading: boolean
  sources: Source[]
}
```

#### 4.2.2 方案生成页面

**功能：**

- 企业信息表单输入
- 方案类型多选
- 实时预览生成结果
- 导出功能（Markdown/Word/PPT）

**UI组件：**

- 表单组件（企业名称、行业、阶段等）
- 方案类型选择器
- 结果展示区域（标签页）
- 导出按钮

**状态管理：**

```typescript
interface PlanState {
  enterpriseInfo: EnterpriseInfo
  selectedTypes: string[]
  results: Record<string, string>
  generating: boolean
}
```

#### 4.2.3 笔记管理页面

**功能：**

- 笔记列表（树形结构，按文件夹组织）
- 笔记编辑器（Markdown + 预览）
- 搜索功能
- 创建/编辑/删除笔记
- 同步状态显示

**UI组件：**

- 文件树组件
- Markdown 编辑器（CodeMirror 或 Monaco）
- 预览面板
- 搜索框
- 同步状态指示器

**状态管理：**

```typescript
interface VaultState {
  files: VaultFile[]
  currentNote: VaultNote | null
  searchQuery: string
  syncStatus: SyncStatus
}
```

#### 4.2.4 TrendRadar 页面

**功能：**

- Up主管理（添加/删除）
- 议题列表（卡片展示）
- 趋势图表
- 议题详情（关联内容、分析）

**UI组件：**

- Up主列表
- 议题卡片网格
- 趋势图表（ECharts）
- 筛选器（时间、标签、来源）

**状态管理：**

```typescript
interface TrendRadarState {
  ups: BilibiliUp[]
  topics: AITopic[]
  trends: TrendData[]
  filters: TopicFilters
}
```

### 4.3 样式设计

**设计原则：**

- 简洁明快：大量留白，清晰的信息层次
- 科技风格：深色主题（可选浅色），渐变背景，玻璃态效果
- 响应式：支持桌面端和移动端

**颜色方案：**

- 主色：深蓝 (#1a1f35) / 亮蓝 (#3b82f6)
- 辅助色：紫色 (#8b5cf6)、青色 (#06b6d4)
- 背景：深灰 (#0f172a) / 浅灰 (#f8fafc)
- 文字：白色 (#ffffff) / 深灰 (#1e293b)

**字体：**

- 中文：思源黑体 / 苹方
- 英文/代码：Inter / JetBrains Mono

## 5. API 设计

### 5.1 知识查询 API

```
POST /api/knowledge/query
Request: { query: string, use_graph: boolean }
Response: { answer: string, sources: Source[] }

GET /api/knowledge/history
Response: { messages: Message[] }
```

### 5.2 方案生成 API

```
POST /api/plan/generate
Request: { enterprise_info: EnterpriseInfo, output_types: string[] }
Response: { results: Record<string, string> }

POST /api/plan/export
Request: { plan_id: string, format: string }
Response: { file_url: string }
```

### 5.3 笔记管理 API

```
GET /api/vault/files
Response: { files: VaultFile[] }

GET /api/vault/notes/{note_id}
Response: { note: VaultNote }

POST /api/vault/notes
Request: { title: string, content: string, path: string }
Response: { note: VaultNote }

PUT /api/vault/notes/{note_id}
Request: { content: string }
Response: { note: VaultNote }

DELETE /api/vault/notes/{note_id}
Response: { success: boolean }

GET /api/vault/search?q={query}
Response: { results: VaultNote[] }

GET /api/vault/status
Response: { syncing: boolean, last_sync: datetime, file_count: int }
```

### 5.4 TrendRadar API

```
GET /api/trendradar/ups
Response: { ups: BilibiliUp[] }

POST /api/trendradar/ups
Request: { uid: string, name: string }
Response: { up: BilibiliUp }

DELETE /api/trendradar/ups/{uid}
Response: { success: boolean }

GET /api/trendradar/topics
Query: ?page=1&limit=20&filter={json}
Response: { topics: AITopic[], total: int }

GET /api/trendradar/topics/{topic_id}
Response: { topic: AITopic, related: AITopic[] }

GET /api/trendradar/trends
Query: ?period=week
Response: { trends: TrendData[] }

POST /api/trendradar/config
Request: { keywords: string[], crawl_interval: int }
Response: { success: boolean }
```

## 6. 数据流设计

### 6.1 sanhu_vault 同步流程

```
文件变更事件 → VaultWatcher → 防抖处理 → 异步任务队列
    ↓
VaultIndexer → 提取内容/元数据 → 更新 Neo4j → 更新向量索引
    ↓
通知前端（WebSocket）→ 更新 UI
```

### 6.2 TrendRadar 爬取流程

```
定时任务触发 → BilibiliCrawler → 爬取 Up主内容
    ↓
AITopicFilter → 筛选 AI 相关 → 存储到 Neo4j
    ↓
TrendAnalyzer → 分析趋势 → 生成报告
    ↓
通知前端（WebSocket）→ 更新议题列表
```

### 6.3 知识查询流程

```
用户输入 → 前端发送请求 → FastAPI 路由
    ↓
UnifiedPRSystem.query_knowledge() → RAG 检索
    ↓
合并结果（图谱 + 向量 + vault 笔记）→ LLM 生成答案
    ↓
返回结果 + 来源 → 前端展示
```

## 7. 配置文件

### 7.1 unified_config.yaml 扩展

```yaml
vault:
  enabled: true
  path: "/Users/biaowenhuang/Documents/sanhu_vault"
  watch_enabled: true
  sync_interval: 60  # 秒
  index_on_startup: true

trendradar:
  enabled: true
  bilibili:
    crawl_interval: 3600  # 秒
    max_videos_per_up: 50
  ai_topics:
    keywords:
      - "AI"
      - "大模型"
      - "LLM"
      - "GPT"
      - "Claude"
      - "Gemini"
    min_relevance_score: 0.7
  report:
    auto_generate: true
    schedule: "daily"  # daily/weekly/monthly
```

### 7.2 config/trendradar.yaml

```yaml
bilibili_ups:
  - uid: "123456"
    name: "Up主名称"
    enabled: true
    tags: ["AI", "技术"]

ai_keywords:
  - "AI"
  - "人工智能"
  - "大模型"
  - "LLM"
  - "GPT"
  - "Claude"
  - "Gemini"
  - "AGI"
  - "机器学习"
  - "深度学习"
```

## 8. 实现步骤

### Phase 1: 后端基础架构

1. 创建 FastAPI 应用框架
2. 实现基础 API 路由（知识查询、方案生成）
3. 集成现有 UnifiedPRSystem
4. 添加 WebSocket 支持

### Phase 2: sanhu_vault 集成

1. 实现 VaultIndexer（索引器）
2. 实现 VaultWatcher（文件监控）
3. 实现 VaultWriter（写入器）
4. 实现同步 API
5. 测试双向同步功能

### Phase 3: TrendRadar 开发

1. 实现 BilibiliCrawler（爬虫）
2. 实现 AITopicFilter（筛选器）
3. 实现 TrendAnalyzer（分析器）
4. 实现定时任务调度
5. 实现 TrendRadar API

### Phase 4: 前端开发

1. 搭建 Vue 3 + TypeScript 项目
2. 配置路由和状态管理
3. 实现知识查询页面
4. 实现方案生成页面
5. 实现笔记管理页面
6. 实现 TrendRadar 页面
7. 样式优化和响应式适配

### Phase 5: 集成测试

1. 端到端功能测试
2. 性能优化
3. 错误处理完善
4. 文档编写

## 9. 文件清单

### 新增后端文件

- `api/main.py` - FastAPI 应用入口
- `api/knowledge.py` - 知识查询路由
- `api/plan.py` - 方案生成路由
- `api/vault.py` - 笔记管理路由
- `api/trendradar.py` - TrendRadar 路由
- `core/knowledge/vault_sync.py` - 同步管理器
- `core/knowledge/vault_indexer.py` - 索引器
- `core/knowledge/vault_writer.py` - 写入器
- `core/knowledge/vault_watcher.py` - 文件监控
- `core/trendradar/bilibili_crawler.py` - B站爬虫
- `core/trendradar/ai_topic_filter.py` - AI议题筛选
- `core/trendradar/trend_analyzer.py` - 趋势分析
- `core/trendradar/scheduler.py` - 定时任务
- `config/trendradar.yaml` - TrendRadar 配置

### 新增前端文件

- `frontend/` - 完整前端项目目录
- `frontend/package.json` - 依赖配置
- `frontend/vite.config.ts` - 构建配置
- `frontend/tsconfig.json` - TypeScript 配置

### 修改现有文件

- `unified_config.yaml` - 添加 vault 和 trendradar 配置
- `unified_pr_system.py` - 集成新模块
- `core/querying/pipelines/qa_pipeline.py` - 支持 vault 笔记检索

## 10. 依赖项

### 后端新增依赖

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
websockets>=12.0
watchdog>=3.0.0
beautifulsoup4>=4.12.0
requests>=2.31.0
aiohttp>=3.9.0
celery>=5.3.0 (可选，用于后台任务)
```

### 前端依赖

```
vue@^3.3.0
vue-router@^4.2.0
pinia@^2.1.0
axios@^1.6.0
element-plus@^2.4.0 (或 naive-ui)
@codemirror/view@^6.0.0
@codemirror/lang-markdown@^6.0.0
echarts@^5.4.0
marked@^11.0.0 (Markdown解析)
```

## 11. 测试要求

### 单元测试

- VaultIndexer 索引功能
- VaultWriter 写入功能
- BilibiliCrawler 爬取功能
- AITopicFilter 筛选功能

### 集成测试

- 文件监控和自动同步
- 笔记创建/更新/删除流程
- TrendRadar 完整流程
- 前端与后端 API 交互

### 端到端测试

- 用户完整工作流（查询 → 生成方案 → 保存笔记）
- TrendRadar 议题追踪流程