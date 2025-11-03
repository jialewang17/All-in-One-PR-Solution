# 公关传播RAG系统 - 高级功能指南

## 🎯 新增功能概述

### 1. Chunk结果人工编辑功能
- **功能**: 允许用户修改chunk的metadata（content_type, industry, brand_mentioned等）
- **同步**: 修改后自动同步到Neo4j数据库
- **文件**: `chunk_editor.py`

### 2. 增量处理系统
- **功能**: 自动识别已处理文件，只处理新文件
- **优势**: 节省token，避免重复工作
- **文件**: `incremental_processor.py`

## 📋 使用方法

### 方法1: 使用主程序（推荐）
```bash
python3 pr_process_all.py
```

选择处理模式：
- **1. 完整处理** - 处理所有文件（首次使用）
- **2. 增量处理** - 只处理新文件（日常使用）
- **3. Chunk编辑** - 编辑已有chunks
- **4. 仅测试RAG系统** - 测试查询功能

### 方法2: 直接使用功能模块

#### Chunk编辑功能
```bash
python3 chunk_editor.py
```

功能特点：
- 选择要编辑的chunk文件
- 支持编辑所有chunks或指定范围
- 支持搜索特定chunks进行编辑
- 实时同步到Neo4j数据库

#### 增量处理功能
```bash
python3 incremental_processor.py
```

功能特点：
- 自动检测新文件
- 跳过已处理文件
- 检查Neo4j状态
- 可选清理孤立chunks

## 🔧 详细功能说明

### Chunk编辑功能

#### 支持的编辑字段：
- **content_type**: 内容类型（如：general, strategy, campaign, media等）
- **industry**: 行业分类（如：beauty, fashion, tech等）
- **brand_mentioned**: 提及的品牌列表

#### 编辑模式：
1. **编辑所有chunks** - 逐个编辑文件中的所有chunks
2. **编辑指定范围** - 编辑指定索引范围的chunks
3. **搜索并编辑** - 根据关键词搜索并编辑特定chunks

#### 同步机制：
- 修改保存后，自动更新Neo4j中对应节点的属性
- 使用chunkId作为唯一标识符进行匹配
- 支持批量更新多个chunks

### 增量处理系统

#### 文件识别机制：
- 使用MD5哈希值比较文件内容
- 记录文件大小、修改时间等元信息
- 支持多种文件格式的增量检测

#### 处理流程：
1. **扫描新文件** - 检查data/raw目录中的新文件
2. **跳过已处理** - 自动跳过已处理的文件
3. **处理新文件** - 对新文件执行完整处理流程
4. **更新记录** - 更新已处理文件记录

#### 状态检查：
- 检查Neo4j中的节点数量
- 检查关系数量
- 检查向量索引状态
- 可选清理孤立chunks

## 📊 数据管理

### 已处理文件记录
文件位置：`data/processed_files.json`

记录内容：
```json
{
  "files": {
    "data/raw/example.pdf": {
      "path": "data/raw/example.pdf",
      "name": "example.pdf",
      "size": 12345,
      "modified": 1234567890.123,
      "hash": "abc123def456"
    }
  },
  "chunks": {},
  "last_processed": "2024-01-01T12:00:00"
}
```

### Neo4j节点属性
PR_Chunk节点包含以下属性：
- `chunkId`: 唯一标识符
- `text`: 文本内容
- `source`: 来源文件
- `formItem`: 所属section
- `chunkSeqId`: 序列号
- `content_type`: 内容类型（可编辑）
- `industry`: 行业分类（可编辑）
- `brand_mentioned`: 提及品牌（可编辑）
- `textEmbeddingOpenAI`: 向量嵌入

## 🚀 最佳实践

### 首次使用
1. 运行完整处理模式处理所有文件
2. 使用Chunk编辑功能完善metadata
3. 测试RAG系统功能

### 日常使用
1. 将新文件放入data/raw目录
2. 运行增量处理模式
3. 根据需要编辑新chunks的metadata
4. 测试查询功能

### 数据维护
1. 定期检查Neo4j状态
2. 清理孤立chunks（可选）
3. 备份processed_files.json记录

## ⚠️ 注意事项

### Chunk编辑
- 修改前建议备份原始文件
- 大量chunks编辑可能需要较长时间
- 确保Neo4j连接正常

### 增量处理
- 不要手动删除processed_files.json
- 文件内容变化会触发重新处理
- 支持文件重命名和移动

### 性能优化
- 大量文件处理时建议分批进行
- 定期清理Neo4j中的孤立节点
- 监控向量索引状态

## 🔍 故障排除

### 常见问题
1. **Chunk编辑失败** - 检查Neo4j连接
2. **增量处理跳过文件** - 检查文件哈希值
3. **同步失败** - 检查chunkId匹配

### 解决方案
1. 重启Neo4j服务
2. 清理processed_files.json重新开始
3. 检查文件权限和路径

## 📈 扩展功能

### 未来可添加的功能
- 批量chunk编辑
- 自动分类建议
- 关系图谱可视化
- 性能监控面板
- 数据导出功能

---

**使用建议**: 建议首次使用完整处理模式，之后使用增量处理模式进行日常维护。


