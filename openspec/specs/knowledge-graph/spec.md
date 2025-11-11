# 知识图谱系统规范

## Purpose

基于 Neo4j 的公关传播知识图谱系统，支持 SPO 三元组提取、图谱构建、实体关系管理和图谱查询。

## Requirements

### Requirement: SPO 三元组提取

The system SHALL extract Subject-Predicate-Object triples from text using LLM.

#### Scenario: Triple extraction from text

- **WHEN** extract_triples_from_text is called with text input
- **THEN** chunk text into manageable pieces
- **AND** use LLM to extract SPO triples from each chunk
- **AND** return all extracted triples with metadata

#### Scenario: Triple normalization

- **WHEN** normalize_triples is called with extracted triples
- **THEN** merge duplicate triples
- **AND** standardize entity names
- **AND** return normalized unique triples

### Requirement: 知识图谱构建

The system SHALL build knowledge graph from SPO triples in Neo4j.

#### Scenario: Graph construction

- **WHEN** build_graph is called with triples
- **THEN** create nodes for subjects and objects
- **AND** create relationships (edges) between nodes
- **AND** store triples in Neo4j database
- **AND** return construction statistics

#### Scenario: Node and relationship creation

- **WHEN** triples are processed
- **THEN** create or update nodes with properties
- **AND** create relationships with properties
- **AND** handle duplicate nodes by merging properties

### Requirement: 图谱查询功能

The system SHALL provide query capabilities for the knowledge graph.

#### Scenario: Graph query

- **WHEN** query_graph is called with Cypher query
- **THEN** execute query on Neo4j database
- **AND** return query results
- **AND** format results in readable format

#### Scenario: Entity relationship query

- **WHEN** query_entity_relationships is called with entity name
- **THEN** find all nodes matching entity name
- **AND** retrieve all relationships connected to the entity
- **AND** return entity and its relationships

### Requirement: 集成知识图谱系统

The system SHALL provide integrated knowledge graph system that combines extraction, construction, and query.

#### Scenario: End-to-end processing

- **WHEN** process_text is called with text
- **THEN** extract SPO triples from text
- **AND** normalize triples
- **AND** build knowledge graph
- **AND** return processing results with statistics

#### Scenario: Batch processing

- **WHEN** process_multiple_texts is called with text list
- **THEN** process each text sequentially
- **AND** accumulate all triples
- **AND** build unified knowledge graph
- **AND** return aggregated results

### Requirement: 图谱数据导出

The system SHALL provide functionality to export graph data.

#### Scenario: Export triples

- **WHEN** export_triples is called
- **THEN** query all triples from Neo4j
- **AND** export to JSON format
- **AND** save to specified file path

#### Scenario: Export statistics

- **WHEN** export_statistics is called
- **THEN** calculate graph statistics (node count, relationship count, etc.)
- **AND** export statistics to JSON format

### Requirement: Neo4j 集成

The system SHALL integrate with Neo4j database for graph storage and query.

#### Scenario: Neo4j connection

- **WHEN** system is initialized
- **THEN** connect to Neo4j database using configuration
- **AND** verify connection
- **AND** create indexes if needed

#### Scenario: Schema management

- **WHEN** system is initialized
- **THEN** create node labels and relationship types if not exist
- **AND** create constraints if needed
- **AND** create indexes for performance




