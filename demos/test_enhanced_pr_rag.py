#!/usr/bin/env python3
"""
增强公关传播RAG系统测试脚本
测试实体识别、关系提取和RAG查询功能
"""

import json
from pr_entity_extractor import EntityRelationshipExtractor
from pr_enhanced_rag import EnhancedPRRAGSystem
from pr_enhanced_schema import PRKnowledgeGraphSchema

def test_entity_extraction():
    """测试实体提取功能"""
    print("🧪 测试实体提取功能")
    print("=" * 60)
    
    extractor = EntityRelationshipExtractor()
    
    test_texts = [
        "华与华与雅诗兰黛合作推出品牌升级活动，在微信、微博等社交媒体平台进行推广。",
        "小米公司与华为在智能手机市场展开激烈竞争，双方都投入大量资源进行品牌建设。",
        "奥迪品牌通过数字化营销策略，在抖音、小红书等平台开展用户运营活动。",
        "一汽丰田与广汽本田在新能源汽车领域展开合作，共同推进绿色出行理念。"
    ]
    
    for i, text in enumerate(test_texts):
        print(f"\n📄 测试文本 {i+1}: {text}")
        print("-" * 40)
        
        # 提取实体
        entities = extractor.extract_entities_from_text(text)
        print("提取的实体:")
        for entity_type, entity_list in entities.items():
            if entity_list:
                print(f"  {entity_type}: {[e.get('name', '') for e in entity_list]}")
        
        # 提取关系
        relationships = extractor.extract_relationships_from_text(text, entities)
        print("提取的关系:")
        for rel in relationships:
            print(f"  {rel['type']}: {rel['from']} -> {rel['to']}")

def test_schema_design():
    """测试图谱模式设计"""
    print("\n🏗️ 测试图谱模式设计")
    print("=" * 60)
    
    schema = PRKnowledgeGraphSchema()
    
    print("节点类型:")
    for node_type, config in schema.node_types.items():
        print(f"  - {node_type}: {config['description']}")
        print(f"    属性: {list(config['properties'].keys())}")
    
    print("\n关系类型:")
    for rel_type, config in schema.relationship_types.items():
        print(f"  - {rel_type}: {config['description']}")
        print(f"    从: {config['from']} -> 到: {config['to']}")

def test_enhanced_rag():
    """测试增强的RAG系统"""
    print("\n🔍 测试增强的RAG系统")
    print("=" * 60)
    
    rag_system = EnhancedPRRAGSystem()
    
    test_questions = [
        "华与华有哪些品牌合作案例？",
        "小米在哪些媒体平台进行推广？",
        "奥迪的品牌传播策略是什么？",
        "汽车行业的公关传播有什么特点？",
        "品牌联名合作有哪些成功案例？"
    ]
    
    for i, question in enumerate(test_questions):
        print(f"\n🤔 问题 {i+1}: {question}")
        print("-" * 40)
        
        try:
            # 测试GraphRAG
            print("📊 GraphRAG回答:")
            graph_answer = rag_system.query(question, use_graph=True)
            print(graph_answer[:200] + "..." if len(graph_answer) > 200 else graph_answer)
            
            print("\n" + "-" * 20)
            
            # 测试VectorRAG
            print("🔍 VectorRAG回答:")
            vector_answer = rag_system.query(question, use_graph=False)
            print(vector_answer[:200] + "..." if len(vector_answer) > 200 else vector_answer)
            
        except Exception as e:
            print(f"❌ 查询失败: {e}")
        
        print("\n" + "=" * 60)

def test_entity_relationships():
    """测试实体关系查询"""
    print("\n🔗 测试实体关系查询")
    print("=" * 60)
    
    rag_system = EnhancedPRRAGSystem()
    
    test_entities = ["华与华", "小米", "奥迪", "雅诗兰黛"]
    
    for entity in test_entities:
        print(f"\n🏷️ 查询实体: {entity}")
        print("-" * 40)
        
        try:
            # 获取实体关系
            relationships = rag_system.get_entity_relationships(entity)
            print("实体关系:")
            print(json.dumps(relationships, ensure_ascii=False, indent=2))
            
            # 获取品牌合作
            collaborations = rag_system.get_brand_collaborations(entity)
            print("\n品牌合作:")
            print(json.dumps(collaborations, ensure_ascii=False, indent=2))
            
            # 获取媒体策略
            media_strategies = rag_system.get_media_strategies(entity)
            print("\n媒体策略:")
            print(json.dumps(media_strategies, ensure_ascii=False, indent=2))
            
        except Exception as e:
            print(f"❌ 查询失败: {e}")

def test_cypher_generation():
    """测试Cypher查询生成"""
    print("\n🔧 测试Cypher查询生成")
    print("=" * 60)
    
    rag_system = EnhancedPRRAGSystem()
    
    test_questions = [
        "华与华与哪些品牌有合作关系？",
        "小米在哪些媒体平台投放广告？",
        "奥迪的品牌定位是什么？",
        "汽车行业有哪些主要的公关传播策略？"
    ]
    
    for question in test_questions:
        print(f"\n🤔 问题: {question}")
        print("-" * 40)
        
        try:
            cypher_query = rag_system.graph_rag._generate_cypher_query(question)
            print("生成的Cypher查询:")
            print(cypher_query)
            
        except Exception as e:
            print(f"❌ Cypher生成失败: {e}")

def main():
    """主测试函数"""
    print("🚀 增强公关传播RAG系统完整测试")
    print("=" * 80)
    
    try:
        # 1. 测试实体提取
        test_entity_extraction()
        
        # 2. 测试图谱模式
        test_schema_design()
        
        # 3. 测试Cypher生成
        test_cypher_generation()
        
        # 4. 测试RAG查询
        test_enhanced_rag()
        
        # 5. 测试实体关系
        test_entity_relationships()
        
        print("\n🎉 所有测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")

if __name__ == "__main__":
    main()
