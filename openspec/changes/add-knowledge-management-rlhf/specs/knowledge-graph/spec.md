## MODIFIED Requirements

### Requirement: 品牌实体管理

The system SHALL manage brand entities in knowledge graph with comprehensive brand information.

#### Scenario: Brand entity creation

- **WHEN** brand list is imported
- **THEN** create Brand nodes in Neo4j for each brand
- **AND** store brand attributes (name, industry, positioning, characteristics, history)
- **AND** create relationships between brands and related entities (companies, campaigns, cases)
- **AND** validate brand data and handle duplicates

#### Scenario: Brand knowledge query

- **WHEN** querying brand knowledge
- **THEN** query Brand nodes and related entities from knowledge graph
- **AND** retrieve brand attributes, relationships, and historical cases
- **AND** return comprehensive brand profile
- **AND** support fuzzy matching for brand name variations

### Requirement: 方法论规则实体管理

The system SHALL manage methodology rule entities in knowledge graph.

#### Scenario: Methodology rule entity creation

- **WHEN** methodology rules are imported
- **THEN** create MethodologyRule nodes in Neo4j
- **AND** store rule attributes (type, conditions, application scenarios, effects)
- **AND** create relationships between rules and applicable entities (brands, industries, goals)
- **AND** support rule versioning and updates

#### Scenario: Methodology rule query

- **WHEN** querying applicable methodology rules
- **THEN** query MethodologyRule nodes based on context (brand, industry, goals)
- **AND** match rules based on conditions and application scenarios
- **AND** return applicable rules with priorities
- **AND** support rule conflict detection

### Requirement: 反馈标注的知识图谱

The system SHALL annotate knowledge graph entities with feedback data to track knowledge effectiveness.

#### Scenario: Feedback annotation on knowledge

- **WHEN** feedback is collected for generated plans
- **THEN** trace back to knowledge sources used in plan generation
- **AND** annotate knowledge entities (nodes, relationships) with feedback data
- **AND** track feedback scores and counts for each knowledge entity
- **AND** update knowledge quality scores based on feedback

#### Scenario: Knowledge effectiveness tracking

- **WHEN** querying knowledge graph
- **THEN** include feedback-based quality indicators
- **AND** prioritize high-feedback knowledge entities
- **AND** provide feedback statistics for knowledge entities
- **AND** enable analysis of knowledge effectiveness




