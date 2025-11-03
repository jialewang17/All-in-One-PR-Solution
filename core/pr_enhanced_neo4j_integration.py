#!/usr/bin/env python3
"""
增强的公关传播Neo4j集成系统
创建实体节点、关系和向量索引
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph
from langchain_openai import OpenAIEmbeddings
from pr_neo4j_env import *
from pr_entity_extractor import EntityRelationshipExtractor
from pr_enhanced_schema import PRKnowledgeGraphSchema

class EnhancedPRNeo4jIntegration:
    """增强的公关传播Neo4j集成系统"""
    
    def __init__(self):
        self.kg = Neo4jGraph(
            url=NEO4J_URI, 
            username=NEO4J_USERNAME, 
            password=NEO4J_PASSWORD, 
            database=NEO4J_DATABASE
        )
        self.extractor = EntityRelationshipExtractor()
        self.schema = PRKnowledgeGraphSchema()
        self.embeddings = OpenAIEmbeddings()
        
        # 统计信息
        self.stats = {
            'chunks_processed': 0,
            'entities_created': 0,
            'relationships_created': 0,
            'embeddings_generated': 0
        }

    def create_enhanced_schema(self):
        """创建增强的图谱模式"""
        print("🏗️ 创建增强的公关传播图谱模式")
        print("-" * 50)
        
        # 创建节点约束
        constraints = self.schema.get_schema_cypher()
        
        try:
            self.kg.query(constraints)
            print("✅ 节点约束创建完成")
        except Exception as e:
            print(f"⚠️ 约束创建警告: {e}")
        
        # 创建向量索引
        self._create_vector_index()
        
        print("✅ 增强图谱模式创建完成")

    def _create_vector_index(self):
        """创建向量索引"""
        create_vector_index = f"""
        CREATE VECTOR INDEX {VECTOR_INDEX_NAME} IF NOT EXISTS
        FOR (pc:PR_Chunk) ON (pc.{VECTOR_EMBEDDING_PROPERTY})
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: 1536,
                `vector.similarity_function`: 'cosine'
            }}
        }}
        """
        
        try:
            self.kg.query(create_vector_index)
            print("✅ 向量索引创建完成")
        except Exception as e:
            print(f"⚠️ 向量索引创建警告: {e}")

    def process_chunks_with_entities(self):
        """处理chunks并提取实体关系"""
        print("\n🔍 处理chunks并提取实体关系")
        print("-" * 50)
        
        chunks_dir = Path("data/chunks")
        if not chunks_dir.exists():
            print(f"❌ Chunks目录不存在: {chunks_dir}")
            return
        
        chunk_files = list(chunks_dir.glob("*_chunks.json"))
        if not chunk_files:
            print("❌ 未找到chunk文件")
            return
        
        total_entities = 0
        total_relationships = 0
        
        for chunk_file in chunk_files:
            print(f"📄 处理文件: {chunk_file.name}")
            
            try:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    chunks_data = json.load(f)
                
                for chunk in chunks_data:
                    # 提取实体和关系
                    processed_chunk = self.extractor.process_chunk(chunk)
                    
                    # 创建PR_Chunk节点
                    self._create_chunk_node(processed_chunk)
                    
                    # 创建实体节点
                    entities_created = self._create_entity_nodes(processed_chunk['entities'])
                    total_entities += entities_created
                    
                    # 创建关系
                    relationships_created = self._create_relationships(
                        processed_chunk['relationships'], 
                        processed_chunk['entities']
                    )
                    total_relationships += relationships_created
                    
                    self.stats['chunks_processed'] += 1
                
                print(f"✅ {chunk_file.name}: {len(chunks_data)} chunks processed")
                
            except Exception as e:
                print(f"❌ 处理文件失败 {chunk_file.name}: {e}")
        
        print(f"\n📊 处理统计:")
        print(f"   - 处理的chunks: {self.stats['chunks_processed']}")
        print(f"   - 创建的实体: {total_entities}")
        print(f"   - 创建的关系: {total_relationships}")

    def _create_chunk_node(self, processed_chunk: dict):
        """创建PR_Chunk节点"""
        create_chunk_query = """
        MERGE (chunk:PR_Chunk {chunkId: $chunkId})
        ON CREATE SET 
            chunk.text = $text,
            chunk.source = $source,
            chunk.content_type = $content_type,
            chunk.industry = $industry,
            chunk.brand_mentioned = $brand_mentioned
        RETURN chunk
        """
        
        try:
            self.kg.query(create_chunk_query, params={
                'chunkId': processed_chunk['chunk_id'],
                'text': processed_chunk['text'],
                'source': processed_chunk['source'],
                'content_type': processed_chunk['metadata']['content_type'],
                'industry': processed_chunk['metadata']['industry'],
                'brand_mentioned': processed_chunk['metadata']['brand_mentioned']
            })
        except Exception as e:
            print(f"⚠️ 创建chunk节点失败: {e}")

    def _create_entity_nodes(self, entities: dict) -> int:
        """创建实体节点"""
        created_count = 0
        
        # 创建品牌节点
        for brand in entities.get('brands', []):
            if self._create_brand_node(brand):
                created_count += 1
        
        # 创建企业节点
        for company in entities.get('companies', []):
            if self._create_company_node(company):
                created_count += 1
        
        # 创建公关公司节点
        for agency in entities.get('agencies', []):
            if self._create_agency_node(agency):
                created_count += 1
        
        # 创建活动节点
        for campaign in entities.get('campaigns', []):
            if self._create_campaign_node(campaign):
                created_count += 1
        
        # 创建媒体节点
        for media in entities.get('media', []):
            if self._create_media_node(media):
                created_count += 1
        
        # 创建策略节点
        for strategy in entities.get('strategies', []):
            if self._create_strategy_node(strategy):
                created_count += 1
        
        return created_count

    def _create_brand_node(self, brand: dict) -> bool:
        """创建品牌节点"""
        create_brand_query = """
        MERGE (brand:Brand {name: $name})
        ON CREATE SET 
            brand.industry = $industry,
            brand.brand_positioning = $brand_positioning,
            brand.brand_personality = $brand_personality,
            brand.target_audience = $target_audience
        RETURN brand
        """
        
        try:
            self.kg.query(create_brand_query, params={
                'name': brand.get('name', ''),
                'industry': brand.get('industry', 'unknown'),
                'brand_positioning': brand.get('brand定位', ''),
                'brand_personality': brand.get('brand个性', ''),
                'target_audience': brand.get('target_audience', '')
            })
            return True
        except Exception as e:
            print(f"⚠️ 创建品牌节点失败: {e}")
            return False

    def _create_company_node(self, company: dict) -> bool:
        """创建企业节点"""
        create_company_query = """
        MERGE (company:Company {name: $name})
        ON CREATE SET 
            company.industry = $industry,
            company.company_type = $company_type,
            company.scale = $scale,
            company.market_position = $market_position
        RETURN company
        """
        
        try:
            self.kg.query(create_company_query, params={
                'name': company.get('name', ''),
                'industry': company.get('industry', 'unknown'),
                'company_type': company.get('企业类型', ''),
                'scale': company.get('企业规模', ''),
                'market_position': company.get('市场地位', '')
            })
            return True
        except Exception as e:
            print(f"⚠️ 创建企业节点失败: {e}")
            return False

    def _create_agency_node(self, agency: dict) -> bool:
        """创建公关公司节点"""
        create_agency_query = """
        MERGE (agency:Agency {name: $name})
        ON CREATE SET 
            agency.specialization = $specialization,
            agency.service_scope = $service_scope,
            agency.reputation = $reputation
        RETURN agency
        """
        
        try:
            self.kg.query(create_agency_query, params={
                'name': agency.get('name', ''),
                'specialization': agency.get('专业领域', ''),
                'service_scope': agency.get('服务范围', ''),
                'reputation': agency.get('行业声誉', '')
            })
            return True
        except Exception as e:
            print(f"⚠️ 创建公关公司节点失败: {e}")
            return False

    def _create_campaign_node(self, campaign: dict) -> bool:
        """创建活动节点"""
        create_campaign_query = """
        MERGE (campaign:Campaign {name: $name})
        ON CREATE SET 
            campaign.campaign_type = $campaign_type,
            campaign.key_message = $key_message,
            campaign.status = $status
        RETURN campaign
        """
        
        try:
            self.kg.query(create_campaign_query, params={
                'name': campaign.get('name', ''),
                'campaign_type': campaign.get('活动类型', ''),
                'key_message': campaign.get('核心信息', ''),
                'status': 'active'
            })
            return True
        except Exception as e:
            print(f"⚠️ 创建活动节点失败: {e}")
            return False

    def _create_media_node(self, media: dict) -> bool:
        """创建媒体节点"""
        create_media_query = """
        MERGE (media:Media {name: $name})
        ON CREATE SET 
            media.media_type = $media_type,
            media.reach = $reach,
            media.engagement_rate = $engagement_rate
        RETURN media
        """
        
        try:
            self.kg.query(create_media_query, params={
                'name': media.get('name', ''),
                'media_type': media.get('媒体类型', ''),
                'reach': media.get('覆盖范围', ''),
                'engagement_rate': media.get('参与度', '')
            })
            return True
        except Exception as e:
            print(f"⚠️ 创建媒体节点失败: {e}")
            return False

    def _create_strategy_node(self, strategy: dict) -> bool:
        """创建策略节点"""
        create_strategy_query = """
        MERGE (strategy:Strategy {name: $name})
        ON CREATE SET 
            strategy.strategy_type = $strategy_type,
            strategy.target_audience = $target_audience,
            strategy.key_message = $key_message
        RETURN strategy
        """
        
        try:
            self.kg.query(create_strategy_query, params={
                'name': strategy.get('name', ''),
                'strategy_type': strategy.get('策略类型', ''),
                'target_audience': strategy.get('目标受众', ''),
                'key_message': strategy.get('核心信息', '')
            })
            return True
        except Exception as e:
            print(f"⚠️ 创建策略节点失败: {e}")
            return False

    def _create_relationships(self, relationships: list, entities: dict) -> int:
        """创建关系"""
        created_count = 0
        
        for rel in relationships:
            if self._create_relationship(rel):
                created_count += 1
        
        return created_count

    def _create_relationship(self, relationship: dict) -> bool:
        """创建单个关系"""
        rel_type = relationship.get('type', '')
        from_entity = relationship.get('from', '')
        to_entity = relationship.get('to', '')
        
        if not all([rel_type, from_entity, to_entity]):
            return False
        
        # 根据关系类型创建不同的关系
        if rel_type == 'COLLABORATES_WITH':
            return self._create_collaboration_relationship(from_entity, to_entity, relationship)
        elif rel_type == 'MEDIA_PLACEMENT':
            return self._create_media_placement_relationship(from_entity, to_entity, relationship)
        elif rel_type == 'BRAND_COLLABORATION':
            return self._create_brand_collaboration_relationship(from_entity, to_entity, relationship)
        elif rel_type == 'COMPETES_WITH':
            return self._create_competition_relationship(from_entity, to_entity, relationship)
        
        return False

    def _create_collaboration_relationship(self, from_entity: str, to_entity: str, rel_data: dict) -> bool:
        """创建合作关系"""
        create_collab_query = """
        MATCH (a), (b)
        WHERE a.name = $from_name AND b.name = $to_name
        MERGE (a)-[r:COLLABORATES_WITH]->(b)
        ON CREATE SET 
            r.description = $description,
            r.confidence = $confidence,
            r.context = $context
        RETURN r
        """
        
        try:
            self.kg.query(create_collab_query, params={
                'from_name': from_entity,
                'to_name': to_entity,
                'description': rel_data.get('description', ''),
                'confidence': rel_data.get('confidence', 0.5),
                'context': rel_data.get('context', '')
            })
            return True
        except Exception as e:
            print(f"⚠️ 创建合作关系失败: {e}")
            return False

    def _create_media_placement_relationship(self, from_entity: str, to_entity: str, rel_data: dict) -> bool:
        """创建媒体投放关系"""
        create_media_query = """
        MATCH (a), (b)
        WHERE a.name = $from_name AND b.name = $to_name
        MERGE (a)-[r:MEDIA_PLACEMENT]->(b)
        ON CREATE SET 
            r.description = $description,
            r.confidence = $confidence,
            r.context = $context
        RETURN r
        """
        
        try:
            self.kg.query(create_media_query, params={
                'from_name': from_entity,
                'to_name': to_entity,
                'description': rel_data.get('description', ''),
                'confidence': rel_data.get('confidence', 0.5),
                'context': rel_data.get('context', '')
            })
            return True
        except Exception as e:
            print(f"⚠️ 创建媒体投放关系失败: {e}")
            return False

    def _create_brand_collaboration_relationship(self, from_entity: str, to_entity: str, rel_data: dict) -> bool:
        """创建品牌合作关系"""
        create_brand_collab_query = """
        MATCH (a:Brand), (b:Brand)
        WHERE a.name = $from_name AND b.name = $to_name
        MERGE (a)-[r:BRAND_COLLABORATION]->(b)
        ON CREATE SET 
            r.description = $description,
            r.confidence = $confidence,
            r.context = $context
        RETURN r
        """
        
        try:
            self.kg.query(create_brand_collab_query, params={
                'from_name': from_entity,
                'to_name': to_entity,
                'description': rel_data.get('description', ''),
                'confidence': rel_data.get('confidence', 0.5),
                'context': rel_data.get('context', '')
            })
            return True
        except Exception as e:
            print(f"⚠️ 创建品牌合作关系失败: {e}")
            return False

    def _create_competition_relationship(self, from_entity: str, to_entity: str, rel_data: dict) -> bool:
        """创建竞争关系"""
        create_comp_query = """
        MATCH (a), (b)
        WHERE a.name = $from_name AND b.name = $to_name
        MERGE (a)-[r:COMPETES_WITH]->(b)
        ON CREATE SET 
            r.description = $description,
            r.confidence = $confidence,
            r.context = $context
        RETURN r
        """
        
        try:
            self.kg.query(create_comp_query, params={
                'from_name': from_entity,
                'to_name': to_entity,
                'description': rel_data.get('description', ''),
                'confidence': rel_data.get('confidence', 0.5),
                'context': rel_data.get('context', '')
            })
            return True
        except Exception as e:
            print(f"⚠️ 创建竞争关系失败: {e}")
            return False

    def generate_embeddings(self):
        """生成嵌入向量"""
        print("\n🔍 生成嵌入向量")
        print("-" * 50)
        
        # 获取所有PR_Chunk节点
        get_chunks_query = "MATCH (pc:PR_Chunk) RETURN pc.chunkId, pc.text LIMIT 20"
        chunks = self.kg.query(get_chunks_query)
        
        for chunk in chunks:
            chunk_id = chunk['pc.chunkId']
            text = chunk['pc.text']
            
            try:
                # 生成嵌入
                embedding = self.embeddings.embed_query(text)
                
                # 更新节点
                update_embedding_query = f"""
                MATCH (pc:PR_Chunk {{chunkId: $chunkId}})
                SET pc.{VECTOR_EMBEDDING_PROPERTY} = $embedding
                RETURN pc
                """
                
                self.kg.query(update_embedding_query, params={
                    'chunkId': chunk_id,
                    'embedding': embedding
                })
                
                self.stats['embeddings_generated'] += 1
                
            except Exception as e:
                print(f"⚠️ 生成嵌入失败 {chunk_id}: {e}")
        
        print(f"✅ 生成了 {self.stats['embeddings_generated']} 个嵌入向量")

    def create_next_relationships(self):
        """创建NEXT关系"""
        print("\n🔗 创建NEXT关系")
        print("-" * 50)
        
        # 为每个formItem创建NEXT关系
        get_form_items_query = "MATCH (pc:PR_Chunk) RETURN DISTINCT pc.source as source"
        form_items = self.kg.query(get_form_items_query)
        
        for item in form_items:
            source = item['source']
            
            create_next_query = """
            MATCH (from_chunk:PR_Chunk)
            WHERE from_chunk.source = $source
            WITH from_chunk ORDER BY from_chunk.chunkSeqId ASC
            WITH collect(from_chunk) as chunk_list
            CALL apoc.nodes.link(chunk_list, "NEXT", {avoidDuplicates: true})
            RETURN size(chunk_list) as linked_count
            """
            
            try:
                result = self.kg.query(create_next_query, params={'source': source})
                print(f"✅ {source}: {result[0]['linked_count']} chunks linked")
            except Exception as e:
                print(f"❌ 链接失败 {source}: {e}")

    def get_graph_statistics(self):
        """获取图谱统计信息"""
        print("\n📊 图谱统计信息")
        print("-" * 50)
        
        # 节点统计
        node_stats_query = """
        CALL db.labels() YIELD label
        CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {}) YIELD value
        RETURN label, value.count as count
        ORDER BY count DESC
        """
        
        try:
            node_stats = self.kg.query(node_stats_query)
            print("节点统计:")
            for stat in node_stats:
                print(f"  - {stat['label']}: {stat['count']}")
        except Exception as e:
            print(f"⚠️ 获取节点统计失败: {e}")
        
        # 关系统计
        rel_stats_query = """
        CALL db.relationshipTypes() YIELD relationshipType
        CALL apoc.cypher.run('MATCH ()-[r:' + relationshipType + ']->() RETURN count(r) as count', {}) YIELD value
        RETURN relationshipType, value.count as count
        ORDER BY count DESC
        """
        
        try:
            rel_stats = self.kg.query(rel_stats_query)
            print("\n关系统计:")
            for stat in rel_stats:
                print(f"  - {stat['relationshipType']}: {stat['count']}")
        except Exception as e:
            print(f"⚠️ 获取关系统计失败: {e}")

    def run_enhanced_integration(self):
        """运行增强集成"""
        print("🚀 增强公关传播RAG Neo4j集成开始")
        print("=" * 60)
        
        try:
            # 1. 创建增强图谱模式
            self.create_enhanced_schema()
            
            # 2. 处理chunks并提取实体关系
            self.process_chunks_with_entities()
            
            # 3. 生成嵌入向量
            self.generate_embeddings()
            
            # 4. 创建NEXT关系
            self.create_next_relationships()
            
            # 5. 显示统计信息
            self.get_graph_statistics()
            
            print("\n🎉 增强公关传播RAG集成完成！")
            
        except Exception as e:
            print(f"❌ 集成过程中出现错误: {e}")

if __name__ == "__main__":
    integration = EnhancedPRNeo4jIntegration()
    integration.run_enhanced_integration()
