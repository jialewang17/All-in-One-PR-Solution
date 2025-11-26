**一体化助理 Web 端 Spec（Python + FastAPI + React/Vite）**

- **目标与范围**

  - 本地优先的一体化个人助理，整合智能体工作流、学习笔记库（/Users/biaowenhuang/Documents/sanhu_vault）、TrendRadar 订阅源（含 B 站）。
  - 提供 Web 前端作为主要入口；后端负责笔记读写、订阅抓取、任务调度、摘要与检索。
  - 数据保持 Obsidian 兼容，支持 Git 版本化导出。

- **技术栈**

  - 后端：Python 3.10+，FastAPI + Uvicorn；调度 APScheduler（如需队列可扩展 Celery + Redis）。
  - 前端：React + Vite（SPA）；样式 Tailwind + 自定义主题；字体 Space Grotesk/Manrope。
  - 数据：文件系统（vault + ./data 配置与缓存）、SQLite（元数据/订阅状态）、FAISS/Chroma（可选向量检索）。
  - 同步：Git 仓库（默认 ./data/git_repo 或指向 vault 同级），支持 commit/push。

- **功能需求**

  - 笔记库：
    - 读取/写入 Markdown（保持 Obsidian 链接与 frontmatter）。
    - 过滤：标签/日期/路径；新增、追加、反向链接。
    - 导出/同步：与 Git 版本化；手动或定时 commit/push。
  - 智能体工作流：
    - 任务模板：PR 评审、学习总结、趋势汇总等，可配置目录/参数。
    - 状态机：排队/运行/完成/失败；日志持久化；重试/终止。
  - TrendRadar：
    - 源类型：RSS、B 站（rss/api/crawler）、GitHub Release/Repo、技术博客。
    - 每源配置：关键词、屏蔽词、抓取频率（分钟）、启用/停用。
    - 聚合视图：按主题（如“AI 大模型”）分组，时间线卡片，收藏/已读/忽略，摘要按钮。
  - B 站关注：
    - 添加 UP（ID/空间链接），抓取最新视频标题/简介/标签/发布时间/互动数据。
    - 模式：rss | api | crawler；关键词过滤；失败重试；摘要生成。
  - 搜索/检索：
    - 跨笔记、趋势结果、任务历史；过滤时间/标签/源类型；可选情感/态度。
    - 向量检索（可选）：vault + 趋势数据嵌入。
  - 摘要/分析：
    - 文本或 URL 调用摘要接口；模型来源可选本地/远程。
  - 安全与隐私：
    - 数据本地存储；外部请求源受配置控制；API 密钥仅存本地（后端代理）。

- **非功能需求**

  - 可扩展：新增源类型/任务模板无需大改。
  - 性能：常规操作无明显卡顿；抓取异步批量，带缓存。
  - 稳定性：抓取失败重试、错误日志可视化。
  - 易配置：单一配置文件与前端设置面板同步。

- **系统架构**

  - 前端 SPA 通过 REST 与 FastAPI 通信；WebSocket 可选用于任务状态推送。
  - 后端层次：
    - API 层：FastAPI 路由。
    - 服务层：任务管理、TrendRadar 抓取、B 站适配器、摘要/向量服务。
    - 持久层：文件系统 + SQLite + 可选向量库。
    - 调度层：APScheduler 定时任务。
  - 目录示例：
    - ./data/config.yaml 配置
    - ./data/cache/ 抓取缓存
    - ./data/sqlite.db 元数据
    - ./data/git_repo/ 版本化（或指向 vault）
    - sanhu_vault/ 笔记库

- **配置文件示例 ./data/config.yaml**

  yaml

  

  `vault_path: "/Users/biaowenhuang/Documents/sanhu_vault" trend_sources:  - id: bili-123    type: bili    mode: api        # rss | api | crawler    up_id: 123456    keywords: ["大模型","评测"]    mute: ["整活"]    interval_min: 60    enabled: true  - id: rss-jiqizhixin    type: rss    url: "https://xxx/rss"    keywords: ["LLM"]    enabled: true tasks:  - name: "PR 评审"    template: "repo_path:..., summary:true" git:  repo_path: "./data/git_repo"  auto_commit: false embeddings:  enabled: true  backend: "faiss" `

- **API 设计（主要端点）**

  - 笔记：
    - GET /api/notes?query=&tag=&from=&to= 检索
    - POST /api/notes {path, content, tags?, append?:bool} 新建/追加
  - 任务：
    - GET /api/tasks
    - POST /api/tasks {type, params}
    - PATCH /api/tasks/:id {action: "cancel"|"retry"} 或状态更新
  - 趋势源：
    - GET /api/trend/sources
    - POST /api/trend/sources
    - PATCH /api/trend/sources/:id
    - DELETE /api/trend/sources/:id
  - 抓取：
    - POST /api/trend/ingest 手动触发
    - GET /api/trend/feed?topic=AI&unread=true
  - B 站：
    - POST /api/bili/check 手动检查指定 UP
  - 搜索：
    - GET /api/search?q=&type=notes|trend|tasks
  - 摘要：
    - POST /api/summary {text|url, model?:local|remote}
  - 同步：
    - POST /api/git/commit {message?}（可自动生成 message）
    - POST /api/git/push
    - GET /api/git/status

- **数据模型（示例）**

  - NoteMeta: {path, title, tags, mtime, links} 存 SQLite/缓存
  - TrendSource: {id, type, mode?, url?, up_id?, keywords[], mute[], interval_min, enabled}
  - TrendItem: {id, source_id, title, summary, link, published_at, tags, unread, starred}
  - Task: {id, type, params, status, log_path, created_at, updated_at}
  - Config: 直接映射 config.yaml

- **后端模块**

  - app/main.py FastAPI 启动/路由注册
  - app/services/notes.py 笔记读写、索引、Obsidian 链接处理
  - app/services/trend.py 抓取调度、聚合、过滤、入库
  - app/services/bili.py B 站 rss/api/crawler 适配、重试、速率限制
  - app/services/tasks.py 任务创建/状态/日志
  - app/services/summary.py 摘要（本地/远程模型适配）
  - app/services/git_sync.py commit/push/status
  - app/services/embed.py 可选向量索引/查询
  - app/scheduler.py APScheduler 任务注册（按源 interval_min）

- **前端页面**

  - 仪表盘：任务状态、最新趋势卡片、今日笔记入口。
  - TrendRadar：左侧源/过滤，右侧卡片列表（来源/时间/标签/摘要/收藏/已读/忽略）。
  - 笔记：列表+搜索+标签；新建/追加；双击打开原文件；显示路径/更新时间。
  - 任务：创建/启动/重试/终止；日志弹窗。
  - 设置：源管理、关键词/屏蔽词、抓取频率、API 密钥、vault 路径测试、主题切换、Git 同步控制。
  - 全局搜索：快捷键唤起，跨源模糊搜索。

- **UI 风格**

  - 主题：蓝青科技风，暗/亮双主题，CSS 变量统一色板。
  - 字体：Space Grotesk/Manrope；标题/正文分级。
  - 组件：卡片描边+微阴影，按钮中圆角，悬停轻微浮动/高光，卡片/页面淡入动效。

- **关键流程**

  - 添加 B 站 UP：前端设置 -> 调用 POST /api/trend/sources with {type:"bili", mode, up_id, keywords, interval_min} -> 调度器按频率抓取 -> 新增 TrendItem -> 前端 TrendRadar 展示。
  - 创建 AI 大模型主题：新增多个源（B 站、RSS、GitHub Release）标记 topic/keywords -> 聚合视图按主题过滤。
  - PR 评审任务：前端创建任务选择 repo 路径 -> 后端执行模板 -> 结果写入 vault/缓存 -> 前端任务页与笔记可见。
  - Git 同步：前端按钮 -> POST /api/git/commit -> POST /api/git/push（若配置 remote），状态在设置页显示。

- **调度与重试**

  - APScheduler 根据 interval_min 注册抓取作业；抓取失败记录日志，指数退避重试（如 1/5/15 分钟）。
  - 手动 POST /api/trend/ingest 可立即触发全量或指定源抓取。

- **日志与监控**

  - 任务日志写入 ./data/logs/{task_id}.log；抓取日志 ./data/logs/trend/{source_id}.log。
  - 前端日志弹窗/最近错误提示；一键清理缓存/重建索引。

- **扩展点**

  - 新源类型：在 app/services/trend.py 注册适配器；配置 schema 可扩展。
  - 模型切换：摘要/嵌入模块通过适配层支持本地/远程。
  - 多用户：未来可加本地账号/权限层，不影响现有接口。

- **待确认/配置项**

  - 摘要/嵌入模型选择（本地或远程 API）。
  - Git remote 地址（若需 push）。
  - B 站 API 密钥/爬虫频率限制。