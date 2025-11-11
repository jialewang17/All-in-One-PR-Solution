# 公关传播 RAG 系统规范

## Purpose

基于 Neo4j 知识图谱和向量存储的增强版 RAG（检索增强生成）系统，用于公关传播领域的知识检索和问答。

## Requirements

### Requirement: RAG 系统初始化

The system SHALL initialize RAG system with Neo4j graph and vector store connections.

#### Scenario: Successful RAG initialization

- **WHEN** EnhancedPRRAGSystem is initialized
- **THEN** connect to Neo4j database
- **AND** initialize vector store (ChromaDB)
- **AND** load embeddings model
- **AND** system is ready to process queries

### Requirement: 增强 RAG 查询

The system SHALL provide enhanced RAG query that combines graph-based and vector-based retrieval.

#### Scenario: Graph-enhanced query

- **WHEN** query is executed with use_graph=True
- **THEN** generate Cypher query from user question
- **AND** execute Cypher query on Neo4j graph
- **AND** retrieve relevant chunks from vector store
- **AND** combine graph results and vector results
- **AND** generate answer using LLM with retrieved context

#### Scenario: Vector-only query

- **WHEN** query is executed with use_graph=False
- **THEN** retrieve relevant chunks from vector store only
- **AND** generate answer using LLM with retrieved context

### Requirement: Cypher 查询生成

The system SHALL generate Cypher queries from natural language questions.

#### Scenario: Cypher generation

- **WHEN** question is provided
- **THEN** use LLM to generate Cypher query
- **AND** query should use available node types (Brand, Company, Agency, Campaign, Media, Strategy, PR_Chunk)
- **AND** query should use available relationship types (COLLABORATES_WITH, BRAND_COLLABORATION, MEDIA_PLACEMENT, etc.)
- **AND** return valid Cypher query statement

#### Scenario: Fallback query

- **WHEN** Cypher generation fails
- **THEN** use fallback query with keyword matching
- **AND** query PR_Chunk nodes with text or brand_mentioned fields

### Requirement: 上下文构建

The system SHALL build context from graph results and vector retrieval results.

#### Scenario: Context construction

- **WHEN** graph results and vector hits are retrieved
- **THEN** format graph results into context text
- **AND** format vector hits into context text with source information
- **AND** combine both contexts
- **AND** truncate to maximum context length

### Requirement: 答案生成

The system SHALL generate answers using LLM with retrieved context.

#### Scenario: Answer generation

- **WHEN** question and context are provided
- **THEN** use LLM to generate answer
- **AND** answer should be based on retrieved context
- **AND** answer should be relevant to the question
- **AND** return generated answer as string

### Requirement: 错误处理

The system SHALL handle errors gracefully and provide meaningful error messages.

#### Scenario: Query failure

- **WHEN** query execution fails
- **THEN** return error message with failure reason
- **AND** do not crash the system

#### Scenario: Connection failure

- **WHEN** Neo4j or vector store connection fails
- **THEN** return error message
- **AND** suggest checking connection configuration




