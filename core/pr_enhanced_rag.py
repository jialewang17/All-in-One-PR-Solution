#!/usr/bin/env python3
"""
增强的公关传播RAG系统
利用实体和关系进行更精准的查询
"""

import textwrap
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_community.graphs import Neo4jGraph
from langchain_openai import OpenAIEmbeddings
from pr_neo4j_env import *

class EnhancedPRGraphRAG:
    """增强的公关传播GraphRAG"""
    
    def __init__(self):
        self.kg = Neo4jGraph(
            url=NEO4J_URI, 
            username=NEO4J_USERNAME, 
            password=NEO4J_PASSWORD, 
            database=NEO4J_DATABASE
        )
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,
            max_tokens=2000
        )
        
        # 增强的Cypher查询模板
        self.cypher_query_template = PromptTemplate(
            input_variables=["question"],
            template="""
你是一个专业的公关传播分析师。基于以下问题，生成相应的Cypher查询语句。

问题: {question}

可用的节点类型:
- Brand: 品牌节点 (name, industry, brand_positioning, brand_personality)
- Company: 企业节点 (name, industry, company_type, scale)
- Agency: 公关公司节点 (name, specialization, service_scope)
- Campaign: 传播活动节点 (name, campaign_type, key_message, status)
- Media: 媒体渠道节点 (name, media_type, reach, engagement_rate)
- Strategy: 传播策略节点 (name, strategy_type, target_audience)
- PR_Chunk: 文本分块节点 (text, content_type, industry, brand_mentioned)

可用的关系类型:
- COLLABORATES_WITH: 合作关系
- BRAND_COLLABORATION: 品牌联名
- MEDIA_PLACEMENT: 媒体投放
- COMPETES_WITH: 竞争关系
- LAUNCHES_CAMPAIGN: 发起活动
- USES_STRATEGY: 使用策略
- CREATES_CONTENT: 创建内容
- NEXT: 文本顺序关系

请生成一个Cypher查询语句来回答这个问题。查询应该:
1. 优先使用实体节点和关系
2. 如果实体信息不足，则查询相关的PR_Chunk节点
3. 返回最相关的信息

只返回Cypher查询语句，不要包含其他解释。
"""
        )

    def query(self, question: str) -> str:
        """查询增强的图谱"""
        try:
            # 生成Cypher查询
            cypher_query = self._generate_cypher_query(question)
            
            # 执行查询
            results = self.kg.query(cypher_query)
            
            # 生成回答
            answer = self._generate_answer(question, results, cypher_query)
            
            return answer
            
        except Exception as e:
            return f"❌ GraphRAG查询失败: {e}"

    def _generate_cypher_query(self, question: str) -> str:
        """生成Cypher查询语句"""
        try:
            prompt = self.cypher_query_template.format(question=question)
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            print(f"⚠️ Cypher查询生成失败: {e}")
            # 回退到简单查询
            return self._fallback_cypher_query(question)

    def _fallback_cypher_query(self, question: str) -> str:
        """回退的Cypher查询"""
        # 简单的关键词匹配查询
        return """
        MATCH (pc:PR_Chunk)
        WHERE pc.text CONTAINS $keyword OR pc.brand_mentioned CONTAINS $keyword
        RETURN pc.text as text, pc.source as source, pc.brand_mentioned as brands
        ORDER BY pc.chunkSeqId
        LIMIT 5
        """

    def _generate_answer(self, question: str, results: List[Dict], cypher_query: str) -> str:
        """生成回答"""
        if not results:
            return "❌ 未找到相关信息"
        
        # 构建上下文
        context = self._build_context(results)
        
        # 生成回答的提示
        answer_prompt = f"""
基于以下公关传播知识图谱的查询结果，回答用户的问题。

用户问题: {question}

查询结果:
{context}

请基于这些信息提供一个专业、准确的回答。回答应该:
1. 直接回答用户的问题
2. 引用具体的品牌、企业、活动或策略
3. 提供实用的建议或洞察
4. 保持专业性和准确性

回答:
"""
        
        try:
            response = self.llm.invoke(answer_prompt)
            return response.content
        except Exception as e:
            return f"❌ 回答生成失败: {e}"

    def _build_context(self, results: List[Dict]) -> str:
        """构建上下文"""
        context_parts = []
        
        for i, result in enumerate(results[:5]):  # 限制结果数量
            context_part = f"结果 {i+1}:\n"
            
            # 处理不同类型的结果
            if 'text' in result:
                context_part += f"内容: {result['text'][:200]}...\n"
            if 'source' in result:
                context_part += f"来源: {result['source']}\n"
            if 'brands' in result:
                context_part += f"相关品牌: {result['brands']}\n"
            if 'name' in result:
                context_part += f"实体名称: {result['name']}\n"
            if 'industry' in result:
                context_part += f"行业: {result['industry']}\n"
            if 'description' in result:
                context_part += f"描述: {result['description']}\n"
            
            context_parts.append(context_part)
        
        return "\n".join(context_parts)

class EnhancedPRVectorRAG:
    """增强的公关传播VectorRAG"""
    
    def __init__(self):
        self.kg = Neo4jGraph(
            url=NEO4J_URI, 
            username=NEO4J_USERNAME, 
            password=NEO4J_PASSWORD, 
            database=NEO4J_DATABASE
        )
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,
            max_tokens=2000
        )
        self.embeddings = OpenAIEmbeddings()
        
        # 增强的向量查询模板
        self.vector_query_template = PromptTemplate(
            input_variables=["question", "context"],
            template="""
你是一个专业的公关传播分析师。基于以下上下文信息，回答用户的问题。

用户问题: {question}

上下文信息:
{context}

请提供一个专业、准确的回答，包括:
1. 直接回答用户的问题
2. 引用具体的案例、品牌或策略
3. 提供实用的建议
4. 保持专业性和准确性

回答:
"""
        )

    def query(self, question: str) -> str:
        """查询增强的向量索引"""
        try:
            # 生成问题嵌入
            question_embedding = self.embeddings.embed_query(question)
            
            # 向量相似性查询
            vector_query = f"""
            CALL db.index.vector.queryNodes('{VECTOR_INDEX_NAME}', 5, $embedding)
            YIELD node, score
            RETURN node.text as text, 
                   node.source as source, 
                   node.content_type as content_type,
                   node.industry as industry,
                   node.brand_mentioned as brand_mentioned,
                   score
            ORDER BY score DESC
            """
            
            results = self.kg.query(vector_query, params={'embedding': question_embedding})
            
            if not results:
                return "❌ 未找到相关信息"
            
            # 构建上下文
            context = self._build_vector_context(results)
            
            # 生成回答
            answer_prompt = self.vector_query_template.format(question=question, context=context)
            response = self.llm.invoke(answer_prompt)
            
            return response.content
            
        except Exception as e:
            return f"❌ VectorRAG查询失败: {e}"

    def _build_vector_context(self, results: List[Dict]) -> str:
        """构建向量查询上下文"""
        context_parts = []
        
        for i, result in enumerate(results):
            context_part = f"相关文档 {i+1} (相似度: {result['score']:.3f}):\n"
            context_part += f"内容: {result['text'][:300]}...\n"
            context_part += f"来源: {result['source']}\n"
            context_part += f"内容类型: {result['content_type']}\n"
            context_part += f"行业: {result['industry']}\n"
            context_part += f"相关品牌: {result['brand_mentioned']}\n"
            context_parts.append(context_part)
        
        return "\n".join(context_parts)

class EnhancedPRRAGSystem:
    """增强的公关传播RAG系统"""
    
    def __init__(self):
        self.graph_rag = EnhancedPRGraphRAG()
        self.vector_rag = EnhancedPRVectorRAG()
        
    def query(self, question: str, use_graph: bool = True) -> str:
        """查询增强的RAG系统"""
        print(f"🔍 查询问题: {question}")
        print(f"📊 使用模式: {'GraphRAG' if use_graph else 'VectorRAG'}")
        print("-" * 60)
        
        if use_graph:
            return self.graph_rag.query(question)
        else:
            return self.vector_rag.query(question)
    
    def get_entity_relationships(self, entity_name: str) -> Dict[str, Any]:
        """获取实体的关系信息"""
        try:
            # 查询实体及其关系
            entity_query = """
            MATCH (e)-[r]->(related)
            WHERE e.name CONTAINS $entity_name
            RETURN e.name as entity_name, 
                   type(r) as relationship_type, 
                   related.name as related_entity,
                   labels(related) as related_type
            LIMIT 20
            """
            
            results = self.graph_rag.kg.query(entity_query, params={'entity_name': entity_name})
            
            # 组织关系数据
            relationships = {
                'entity_name': entity_name,
                'outgoing_relationships': [],
                'incoming_relationships': []
            }
            
            for result in results:
                rel_info = {
                    'type': result['relationship_type'],
                    'related_entity': result['related_entity'],
                    'related_type': result['related_type']
                }
                relationships['outgoing_relationships'].append(rel_info)
            
            return relationships
            
        except Exception as e:
            return {'error': f"获取实体关系失败: {e}"}
    
    def get_brand_collaborations(self, brand_name: str) -> List[Dict[str, Any]]:
        """获取品牌合作关系"""
        try:
            collaboration_query = """
            MATCH (b:Brand)-[r:BRAND_COLLABORATION|COLLABORATES_WITH]->(related)
            WHERE b.name CONTAINS $brand_name
            RETURN b.name as brand_name,
                   type(r) as collaboration_type,
                   related.name as partner_name,
                   labels(related) as partner_type,
                   r.description as description
            """
            
            results = self.graph_rag.kg.query(collaboration_query, params={'brand_name': brand_name})
            
            collaborations = []
            for result in results:
                collaborations.append({
                    'brand_name': result['brand_name'],
                    'collaboration_type': result['collaboration_type'],
                    'partner_name': result['partner_name'],
                    'partner_type': result['partner_type'],
                    'description': result['description']
                })
            
            return collaborations
            
        except Exception as e:
            return [{'error': f"获取品牌合作关系失败: {e}"}]
    
    def get_media_strategies(self, brand_name: str) -> List[Dict[str, Any]]:
        """获取品牌的媒体策略"""
        try:
            media_strategy_query = """
            MATCH (b:Brand)-[r:MEDIA_PLACEMENT]->(m:Media)
            WHERE b.name CONTAINS $brand_name
            RETURN b.name as brand_name,
                   m.name as media_name,
                   m.media_type as media_type,
                   m.reach as reach,
                   r.description as strategy_description
            """
            
            results = self.graph_rag.kg.query(media_strategy_query, params={'brand_name': brand_name})
            
            strategies = []
            for result in results:
                strategies.append({
                    'brand_name': result['brand_name'],
                    'media_name': result['media_name'],
                    'media_type': result['media_type'],
                    'reach': result['reach'],
                    'strategy_description': result['strategy_description']
                })
            
            return strategies
            
        except Exception as e:
            return [{'error': f"获取媒体策略失败: {e}"}]

def test_enhanced_rag():
    """测试增强的RAG系统"""
    rag_system = EnhancedPRRAGSystem()
    
    test_questions = [
        "华与华有哪些品牌合作案例？",
        "小米在哪些媒体平台进行推广？",
        "奥迪的品牌传播策略是什么？",
        "汽车行业的公关传播有什么特点？"
    ]
    
    print("🧪 测试增强的RAG系统")
    print("=" * 60)
    
    for question in test_questions:
        print(f"\n🤔 问题: {question}")
        print("-" * 40)
        
        # 测试GraphRAG
        print("📊 GraphRAG回答:")
        graph_answer = rag_system.query(question, use_graph=True)
        print(textwrap.fill(graph_answer, 80))
        
        print("\n" + "-" * 40)
        
        # 测试VectorRAG
        print("🔍 VectorRAG回答:")
        vector_answer = rag_system.query(question, use_graph=False)
        print(textwrap.fill(vector_answer, 80))
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    test_enhanced_rag()
