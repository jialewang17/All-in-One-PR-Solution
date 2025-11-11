## MODIFIED Requirements

### Requirement: 品牌知识整合

The system SHALL integrate brand knowledge (brand lists, brand attributes, brand history) into RAG retrieval and plan generation.

#### Scenario: Brand knowledge retrieval

- **WHEN** generating PR plan for a specific brand
- **THEN** query brand knowledge from knowledge base
- **AND** retrieve brand attributes, positioning, history, and cases
- **AND** use brand knowledge to enhance context for plan generation
- **AND** apply brand-specific rules and constraints

#### Scenario: Brand knowledge in retrieval

- **WHEN** retrieving relevant knowledge for query
- **THEN** prioritize brand knowledge if query mentions specific brand
- **AND** combine brand knowledge with general knowledge from vector store and graph
- **AND** rank results considering brand relevance
- **AND** annotate knowledge sources (brand knowledge vs general knowledge)

### Requirement: 方法论规则应用

The system SHALL apply brand communication methodology rules during plan generation.

#### Scenario: Methodology rule matching

- **WHEN** generating PR plan
- **THEN** match applicable methodology rules based on brand, industry, and goals
- **AND** apply matched rules to guide plan generation
- **AND** prioritize high-priority rules
- **AND** resolve rule conflicts if any
- **AND** annotate which rules were applied

#### Scenario: Rule-based plan enhancement

- **WHEN** methodology rules are applied
- **THEN** enhance plan generation with rule-guided prompts
- **AND** ensure generated plan follows applicable rules
- **AND** incorporate rule-based best practices
- **AND** validate plan against rule constraints

### Requirement: 反馈驱动的检索优化

The system SHALL optimize retrieval based on feedback data to improve plan quality.

#### Scenario: Feedback-based retrieval weighting

- **WHEN** retrieving knowledge for plan generation
- **THEN** weight retrieval results based on historical feedback
- **AND** prioritize knowledge sources that led to high-quality plans
- **AND** deprioritize knowledge sources that led to low-quality plans
- **AND** adapt retrieval strategy based on feedback patterns

#### Scenario: Quality-aware knowledge selection

- **WHEN** selecting knowledge for context
- **THEN** consider quality scores of knowledge sources
- **AND** prefer high-quality, feedback-validated knowledge
- **AND** balance relevance and quality in knowledge selection
- **AND** track which knowledge sources contribute to high-quality plans

### Requirement: 方案生成质量标注

The system SHALL annotate generated plans with quality indicators and knowledge sources.

#### Scenario: Plan quality annotation

- **WHEN** plan is generated
- **THEN** annotate plan with:
  - Quality score (if available)
  - Knowledge sources used (brand knowledge, methodology rules, general knowledge)
  - Applied methodology rules
  - Confidence scores
- **AND** include annotations in plan output
- **AND** enable quality tracking and analysis




