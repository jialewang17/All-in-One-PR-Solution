# 统一公关传播智能体系统规范

## Purpose

统一的公关传播智能体系统，整合 RAG 系统、知识图谱、实体提取和方案生成功能，提供一体化的公关传播智能服务。

## Requirements

### Requirement: 系统初始化

The system SHALL initialize all components including RAG system, knowledge graph, entity extractor, and plan generation components.

#### Scenario: Successful system initialization

- **WHEN** UnifiedPRSystem is initialized with valid config
- **THEN** all components (RAG system, GraphRAG, entity extractor) are initialized
- **AND** system is ready to process queries

#### Scenario: Configuration loading

- **WHEN** config file exists
- **THEN** load configuration from YAML file
- **WHEN** config file does not exist
- **THEN** create default configuration and save to file

### Requirement: 知识查询功能

The system SHALL provide knowledge query capability using RAG system with optional graph enhancement.

#### Scenario: Graph-enhanced query

- **WHEN** query is executed with use_graph=True
- **THEN** use enhanced RAG system with knowledge graph
- **AND** return relevant knowledge from both vector store and graph

#### Scenario: Vector-only query

- **WHEN** query is executed with use_graph=False
- **THEN** use vector RAG system only
- **AND** return relevant knowledge from vector store

### Requirement: 公关方案生成

The system SHALL generate PR campaign plans based on enterprise information and knowledge retrieval.

#### Scenario: Generate multiple output types

- **WHEN** generate_pr_plan is called with enterprise info and output types
- **THEN** retrieve relevant knowledge from graph and vector store
- **AND** generate requested output types (A: 图文简报, B: 视频脚本, C: 活动方案, D: 短视频脚本, E: 小红书笔记, F: 危机应对方案)
- **AND** return generated plans as dictionary

#### Scenario: Default output types

- **WHEN** generate_pr_plan is called without output_types parameter
- **THEN** generate all default output types (A, B, C, D, E, F)

### Requirement: 实体分析功能

The system SHALL analyze entities and relationships from text input.

#### Scenario: Entity extraction

- **WHEN** analyze_entities is called with text input
- **THEN** extract entities using entity extractor
- **AND** extract relationships using entity extractor
- **AND** return entities, relationships, and analysis summary

### Requirement: 统一查询接口

The system SHALL provide a unified query interface that automatically routes queries to appropriate handlers.

#### Scenario: Auto mode routing

- **WHEN** unified_query is called with mode="auto"
- **THEN** analyze query content to determine type
- **AND** route to knowledge_query if query contains knowledge keywords
- **AND** route to entity_analysis if query contains entity/relationship keywords
- **AND** route to plan_generation if query contains plan/campaign keywords

#### Scenario: Explicit mode routing

- **WHEN** unified_query is called with explicit mode
- **THEN** route directly to specified handler (knowledge_query, entity_analysis, plan_generation)
- **AND** return result with mode and timestamp

### Requirement: 企业信息解析

The system SHALL parse enterprise information from query text for plan generation.

#### Scenario: Parse enterprise info

- **WHEN** _parse_enterprise_info is called with query text
- **THEN** extract enterprise stage, industry, market type, PR goal from query
- **AND** return enterprise info dictionary with default values for missing fields

### Requirement: 系统关闭

The system SHALL properly close all components and release resources.

#### Scenario: System shutdown

- **WHEN** close method is called
- **THEN** close GraphRAG connection
- **AND** release all resources
- **AND** print shutdown confirmation message




