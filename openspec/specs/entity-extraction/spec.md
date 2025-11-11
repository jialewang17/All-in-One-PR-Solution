# 实体提取系统规范

## Purpose

基于 LLM 的智能实体识别和关系提取系统，用于从公关传播文本中提取品牌、企业、媒体、活动等实体及其关系。

## Requirements

### Requirement: 实体提取

The system SHALL extract entities from text including brands, companies, agencies, campaigns, media, and strategies.

#### Scenario: Entity extraction from text

- **WHEN** extract_entities is called with text input
- **THEN** use LLM to identify entities in the text
- **AND** extract entity properties (name, industry, type, etc.)
- **AND** return list of entities with their properties

#### Scenario: Entity types

- **WHEN** entities are extracted
- **THEN** identify Brand entities (品牌)
- **AND** identify Company entities (企业)
- **AND** identify Agency entities (公关公司)
- **AND** identify Campaign entities (传播活动)
- **AND** identify Media entities (媒体渠道)
- **AND** identify Strategy entities (传播策略)

### Requirement: 关系提取

The system SHALL extract relationships between entities from text.

#### Scenario: Relationship extraction

- **WHEN** extract_relationships is called with text input
- **THEN** use LLM to identify relationships between entities
- **AND** extract relationship types (COLLABORATES_WITH, BRAND_COLLABORATION, MEDIA_PLACEMENT, COMPETES_WITH, etc.)
- **AND** extract relationship properties
- **AND** return list of relationships

#### Scenario: Relationship types

- **WHEN** relationships are extracted
- **THEN** identify COLLABORATES_WITH relationships (合作关系)
- **AND** identify BRAND_COLLABORATION relationships (品牌联名)
- **AND** identify MEDIA_PLACEMENT relationships (媒体投放)
- **AND** identify COMPETES_WITH relationships (竞争关系)
- **AND** identify LAUNCHES_CAMPAIGN relationships (发起活动)
- **AND** identify USES_STRATEGY relationships (使用策略)

### Requirement: SPO 三元组提取

The system SHALL extract Subject-Predicate-Object triples using SPO extractor when enabled.

#### Scenario: SPO extraction enabled

- **WHEN** use_spo_extractor is True and SPO extractor is available
- **THEN** use SPOTripleExtractor to extract triples
- **AND** return triples in SPO format
- **AND** normalize triples

#### Scenario: SPO extraction disabled

- **WHEN** use_spo_extractor is False or SPO extractor is unavailable
- **THEN** use traditional LLM-based extraction
- **AND** extract entities and relationships separately

### Requirement: 实体关系整合

The system SHALL integrate entities and relationships into knowledge graph format.

#### Scenario: Knowledge graph integration

- **WHEN** entities and relationships are extracted
- **THEN** format entities as nodes with properties
- **AND** format relationships as edges with properties
- **AND** return data in knowledge graph format
- **AND** ready for Neo4j import

### Requirement: 批量处理

The system SHALL support batch processing of multiple texts.

#### Scenario: Batch entity extraction

- **WHEN** extract_entities_batch is called with text list
- **THEN** process each text sequentially
- **AND** extract entities from each text
- **AND** merge duplicate entities
- **AND** return aggregated entity list

#### Scenario: Batch relationship extraction

- **WHEN** extract_relationships_batch is called with text list
- **THEN** process each text sequentially
- **AND** extract relationships from each text
- **AND** merge duplicate relationships
- **AND** return aggregated relationship list

### Requirement: 错误处理

The system SHALL handle extraction errors gracefully.

#### Scenario: LLM failure

- **WHEN** LLM extraction fails
- **THEN** fall back to rule-based extraction if available
- **AND** return partial results with error message
- **AND** do not crash the system

#### Scenario: Invalid input

- **WHEN** invalid or empty text is provided
- **THEN** return empty results
- **AND** return appropriate error message




