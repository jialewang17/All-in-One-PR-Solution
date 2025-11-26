# RAG 与 RLHF 增强规范（多格式/实体关系/报告）

## Purpose

为公关传播 RAG 系统新增多格式文档处理、更精准的实体与关系识别，迭代 RLHF 流水线，并提供基于需求确认的报告生成能力。

## Requirements

### Requirement: 多格式文档接入与预处理

The system SHALL ingest and normalize heterogeneous files (PDF, DOCX, PPTX, XLSX/CSV, Markdown/HTML/TXT) into RAG-ready chunks with metadata.

#### Scenario: 多格式解析

- **WHEN** files in supported formats are uploaded
- **THEN** parse content while preserving structural cues (headings, tables, slides, sheets)
- **AND** extract metadata (title, author, created_at, language, source path)
- **AND** return normalized text blocks for downstream cleaning and chunking

#### Scenario: 质量与重试

- **WHEN** a file contains corrupted pages or unsupported elements
- **THEN** skip faulty parts with warnings
- **AND** retry with fallback parser when primary parser fails
- **AND** record per-file status for auditing

#### Scenario: 分块与溯源

- **WHEN** chunks are produced
- **THEN** apply format-aware chunking with overlap and sentence/slide/table boundaries
- **AND** attach source file, page/slide/sheet indices, section anchors, and hash signatures
- **AND** persist chunks for both vector store import and graph augmentation

### Requirement: 精准实体与关系识别

The system SHALL extract domain entities and relations with higher precision/recall and coherent graph outputs.

#### Scenario: 模型与规则协同

- **WHEN** text chunks are processed
- **THEN** run domain-tuned NER/RE models with methodology-rule constraints
- **AND** enforce schema validation against PR graph types and allowed predicates
- **AND** output structured triples with confidence scores

#### Scenario: 案例库对齐与知识注入

- **WHEN** entities/relations are recognized from unstructured text
- **THEN** cross-check against structured references in `公关案例库_传播渠道关系表_表格.csv`, `公关案例库_公关案例库_表格.csv`, `公关案例库_公关目标关系表_表格.csv`, `公关案例库_行业与品牌关系表_表格.csv`, and `关系表详情.docx`
- **AND** expand/validate Neo4j entity和关系类型列表及别名表以覆盖上述文件内容
- **AND** store provenance linking each extracted fact to both source chunk和对应参考表以提升准确性

#### Scenario: 去重与消歧

- **WHEN** entities share names, aliases, or appear across files
- **THEN** perform canonicalization using identifiers (brand IDs, URLs, emails), context similarity, and language-aware alias tables
- **AND** merge duplicates while preserving provenance
- **AND** flag low-confidence merges for review

#### Scenario: 关系一致性与覆盖

- **WHEN** relations are generated
- **THEN** reject contradictory edges against existing graph facts unless explicitly marked as contested
- **AND** support cross-document relations by linking to all source chunks
- **AND** store relation-level confidence, timestamps, and evidence pointers

### Requirement: RAG 检索与召回强化

The system SHALL deliver higher-quality retrieval by combining vector, graph, and entity-linked signals.

#### Scenario: 组合检索

- **WHEN** a query is issued
- **THEN** perform vector search on latest chunks and graph search on entity/relationship paths
- **AND** rerank results with entity overlap, temporal relevance, and feedback-derived weights
- **AND** return deduplicated, source-attributed context

#### Scenario: 上下文防幻觉

- **WHEN** context is built
- **THEN** include citations (file, location, graph node IDs) for each fact
- **AND** drop contexts below confidence thresholds or outside scope
- **AND** surface warnings when retrieval coverage is weak

### Requirement: RLHF 模块迭代

The system SHALL enhance RLHF data flow, reward training, and policy improvement for PR outputs and retrieval.

#### Scenario: 反馈采集与分桶

- **WHEN** user or evaluator feedback arrives
- **THEN** store ratings, rationale, and linked outputs (plans, answers, reports, retrieval traces)
- **AND** bucket feedback by task type and brand/industry for targeted training
- **AND** enforce data quality checks (length, toxicity, duplication)

#### Scenario: 奖励模型训练与验证

- **WHEN** feedback volume meets configured thresholds
- **THEN** prepare balanced preference pairs and scalar signals
- **AND** train/retrain reward models with train/val splits and early stopping
- **AND** log metrics (accuracy, win-rate) and store versioned checkpoints

#### Scenario: 策略优化与上线

- **WHEN** a new reward model passes validation gates
- **THEN** run policy optimization (PPO/iterative rerank) on candidate prompts or retrieval weights
- **AND** A/B compare against the active policy on offline eval sets
- **AND** roll out the better policy with rollback hooks and changelog

### Requirement: 报告生成前的需求确认

The system SHALL generate reports only after understanding and confirming user requirements.

#### Scenario: 需求澄清对话

- **WHEN** a report is requested
- **THEN** elicit key parameters (目标、受众、语气、篇幅、格式、数据时效、引用偏好)
- **AND** summarize interpreted requirements back to the user
- **AND** wait for explicit confirmation or edits before generation

#### Scenario: 方法论对齐

- **WHEN** generating a PR communication plan/report
- **THEN** ground structure和策略建议在 `公关营销传播方法论.md` 的框架与规则上
- **AND** select/justify report sections、渠道组合、目标映射时显式引用方法论要点
- **AND** include citations to both retrieved evidence和方法论条目 where applicable

#### Scenario: 报告生成与版本化

- **WHEN** requirements are confirmed
- **THEN** assemble context from RAG retrieval with citations
- **AND** select templates/styles matching the confirmed parameters
- **AND** emit a versioned report artifact with metadata (requirements snapshot, retrieval sources, generation config)

#### Scenario: 变更追踪

- **WHEN** requirements change after confirmation
- **THEN** invalidate prior draft, request reconfirmation
- **AND** regenerate report with updated context
- **AND** keep history of requirement deltas and report versions
