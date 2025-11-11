## MODIFIED Requirements

### Requirement: 统一实体和关系提取

The system SHALL provide a unified extraction pipeline that combines SPO triple extraction and traditional entity-relationship extraction into a single, consistent process.

#### Scenario: Unified extraction pipeline

- **WHEN** extract_from_text is called with text input
- **THEN** use unified extraction pipeline that combines SPO and entity extraction
- **AND** extract entities and relationships in a single pass
- **AND** convert SPO triples to entity-relationship format
- **AND** merge and normalize results from both methods
- **AND** return unified extraction results

#### Scenario: Extraction method selection

- **WHEN** text is provided for extraction
- **THEN** automatically select best extraction method based on document type
- **AND** use SPO extraction for structured facts
- **AND** use entity extraction for named entities
- **AND** combine results with confidence scores

### Requirement: 提高提取准确性

The system SHALL improve extraction accuracy through optimized prompts, multi-pass extraction, and validation mechanisms.

#### Scenario: Optimized prompt for unstructured data

- **WHEN** extracting from unstructured documents (PR plans, industry research, case studies)
- **THEN** use specialized prompts designed for each document type
- **AND** include domain-specific context and examples
- **AND** request confidence scores for each extraction
- **AND** return high-confidence extractions

#### Scenario: Multi-pass extraction and fusion

- **WHEN** extracting entities and relationships
- **THEN** perform multiple extraction passes with different strategies
- **AND** fuse results from multiple passes
- **AND** resolve conflicts using confidence scores
- **AND** return consolidated extraction results

#### Scenario: Confidence scoring

- **WHEN** entities and relationships are extracted
- **THEN** assign confidence scores to each extraction
- **AND** confidence scores range from 0.0 to 1.0
- **AND** filter low-confidence extractions based on threshold
- **AND** include confidence scores in extraction results

### Requirement: 数据质量评估

The system SHALL assess and report data quality for extracted entities, relationships, and triples.

#### Scenario: Extraction quality assessment

- **WHEN** extraction is completed
- **THEN** assess extraction quality using multiple metrics:
  - Accuracy: percentage of correctly extracted entities/relationships
  - Completeness: percentage of expected entities/relationships found
  - Consistency: consistency of extracted data across documents
  - Validity: validity of extracted triples and relationships
- **AND** generate quality assessment report
- **AND** flag low-quality extractions for review

#### Scenario: Quality metrics calculation

- **WHEN** quality assessment is performed
- **THEN** calculate entity extraction accuracy (precision, recall, F1)
- **AND** calculate relationship extraction accuracy
- **AND** calculate triple validity rate
- **AND** calculate data consistency score
- **AND** return quality metrics in structured format

### Requirement: 非结构化数据优化

The system SHALL optimize extraction for unstructured documents including PR plans, industry research, media methods, tool guides, and brand cases.

#### Scenario: Document type detection

- **WHEN** text is provided for extraction
- **THEN** automatically detect document type (PR plan, research, method, tool, case)
- **AND** select appropriate extraction strategy for document type
- **AND** apply type-specific prompts and validation rules

#### Scenario: PR plan extraction

- **WHEN** extracting from PR campaign plans
- **THEN** focus on extracting campaign entities, strategies, channels, target audiences
- **AND** extract campaign relationships (launches, uses, targets)
- **AND** extract temporal and spatial information
- **AND** extract budget and KPI information

#### Scenario: Industry research extraction

- **WHEN** extracting from industry research documents
- **THEN** focus on extracting industry trends, market insights, competitor information
- **AND** extract research methodologies and data sources
- **AND** extract key findings and conclusions
- **AND** extract statistical and quantitative data

#### Scenario: Case study extraction

- **WHEN** extracting from brand case studies
- **THEN** focus on extracting brand entities, campaign details, results
- **AND** extract success factors and lessons learned
- **AND** extract brand relationships and partnerships
- **AND** extract quantitative results and metrics

### Requirement: 后处理和验证

The system SHALL post-process and validate extraction results to ensure quality and consistency.

#### Scenario: Entity normalization

- **WHEN** entities are extracted
- **THEN** normalize entity names (remove variations, handle aliases)
- **AND** merge duplicate entities
- **AND** validate entity properties
- **AND** return normalized entity list

#### Scenario: Relationship validation

- **WHEN** relationships are extracted
- **THEN** validate relationship types against schema
- **AND** normalize relationship names
- **AND** check relationship consistency (no circular references, valid entity pairs)
- **AND** filter invalid relationships

#### Scenario: Triple consistency check

- **WHEN** triples are extracted
- **THEN** check for logical inconsistencies
- **AND** validate triple structure (subject, predicate, object)
- **AND** check for contradictory triples
- **AND** flag inconsistent triples for review

### Requirement: 批量处理和质量控制

The system SHALL support batch processing with quality control for multiple documents.

#### Scenario: Batch extraction with quality control

- **WHEN** batch_extract is called with multiple documents
- **THEN** process each document with unified extraction pipeline
- **AND** assess quality for each document
- **AND** aggregate quality metrics across batch
- **AND** generate batch quality report
- **AND** flag low-quality documents for manual review




