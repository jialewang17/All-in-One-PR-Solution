#!/usr/bin/env python3
"""
增强公关传播RAG系统演示脚本
展示实体识别、关系提取和RAG查询功能
"""

import json
import sys
from pathlib import Path

# 添加core目录到Python路径
sys.path.append(str(Path(__file__).parent.parent / "core"))

from pr_entity_extractor import EntityRelationshipExtractor
from pr_enhanced_schema import PRKnowledgeGraphSchema

def demo_entity_extraction():
    """演示实体提取功能"""
    print("🎯 增强公关传播RAG系统演示")
    print("=" * 60)
    
    extractor = EntityRelationshipExtractor()
    
    # 测试文本
    test_text = """
    华与华与雅诗兰黛合作推出品牌升级活动，在微信、微博等社交媒体平台进行推广。
    小米公司与华为在智能手机市场展开激烈竞争，双方都投入大量资源进行品牌建设。
    奥迪品牌通过数字化营销策略，在抖音、小红书等平台开展用户运营活动。
    一汽丰田与广汽本田在新能源汽车领域展开合作，共同推进绿色出行理念。
    """
    
    print("📄 测试文本:")
    print(test_text.strip())
    print("\n" + "=" * 60)
    
    # 提取实体
    print("🔍 实体提取结果:")
    entities = extractor.extract_entities_from_text(test_text)
    
    for entity_type, entity_list in entities.items():
        if entity_list:
            print(f"\n{entity_type.upper()}:")
            for entity in entity_list:
                if isinstance(entity, dict):
                    name = entity.get('name', '')
                    if name:
                        print(f"  - {name}")
                else:
                    print(f"  - {entity}")
    
    # 提取关系
    print("\n🔗 关系提取结果:")
    relationships = extractor.extract_relationships_from_text(test_text, entities)
    
    for rel in relationships:
        print(f"\n关系类型: {rel['type']}")
        print(f"  主体: {rel['from']}")
        print(f"  客体: {rel['to']}")
        print(f"  上下文: {rel['context']}")
        print(f"  置信度: {rel['confidence']}")

def demo_schema_design():
    """演示图谱模式设计"""
    print("\n🏗️ 图谱模式设计演示")
    print("=" * 60)
    
    schema = PRKnowledgeGraphSchema()
    
    print("📊 节点类型定义:")
    for node_type, config in schema.node_types.items():
        print(f"\n{node_type}:")
        print(f"  描述: {config['description']}")
        print(f"  属性: {list(config['properties'].keys())}")
    
    print("\n🔗 关系类型定义:")
    for rel_type, config in schema.relationship_types.items():
        print(f"\n{rel_type}:")
        print(f"  描述: {config['description']}")
        print(f"  从: {config['from']} -> 到: {config['to']}")
        print(f"  属性: {config['properties']}")

def demo_cypher_generation():
    """演示Cypher查询生成"""
    print("\n🔧 Cypher查询生成演示")
    print("=" * 60)
    
    # 示例查询
    example_queries = [
        "华与华与哪些品牌有合作关系？",
        "小米在哪些媒体平台投放广告？",
        "奥迪的品牌定位是什么？",
        "汽车行业有哪些主要的公关传播策略？"
    ]
    
    print("📝 示例查询问题:")
    for i, question in enumerate(example_queries, 1):
        print(f"{i}. {question}")
    
    print("\n💡 对应的Cypher查询示例:")
    
    cypher_examples = [
        """
        // 查询品牌合作关系
        MATCH (b:Brand)-[r:BRAND_COLLABORATION|COLLABORATES_WITH]->(partner:Brand)
        WHERE b.name CONTAINS "华与华"
        RETURN b.name, partner.name, r.description
        """,
        """
        // 查询媒体投放策略
        MATCH (b:Brand)-[r:MEDIA_PLACEMENT]->(m:Media)
        WHERE b.name CONTAINS "小米"
        RETURN b.name, m.name, m.media_type, r.description
        """,
        """
        // 查询品牌定位
        MATCH (b:Brand)
        WHERE b.name CONTAINS "奥迪"
        RETURN b.name, b.brand_positioning, b.brand_personality
        """,
        """
        // 查询行业策略
        MATCH (s:Strategy)
        WHERE s.target_audience CONTAINS "汽车" OR s.strategy_type CONTAINS "汽车"
        RETURN s.strategy_type, s.target_audience, s.key_message
        """
    ]
    
    for i, cypher in enumerate(cypher_examples, 1):
        print(f"\n{i}. {example_queries[i-1]}")
        print(cypher.strip())

def demo_rag_capabilities():
    """演示RAG能力"""
    print("\n🤖 RAG系统能力演示")
    print("=" * 60)
    
    print("📊 GraphRAG能力:")
    print("  ✅ 基于实体和关系的结构化查询")
    print("  ✅ 智能Cypher查询生成")
    print("  ✅ 多跳关系推理")
    print("  ✅ 实体关系分析")
    
    print("\n🔍 VectorRAG能力:")
    print("  ✅ 语义相似性搜索")
    print("  ✅ 上下文感知回答")
    print("  ✅ 多文档信息融合")
    print("  ✅ 专业领域适配")
    
    print("\n🎯 增强功能:")
    print("  ✅ 实体识别和分类")
    print("  ✅ 关系提取和验证")
    print("  ✅ 品牌合作分析")
    print("  ✅ 媒体策略查询")
    print("  ✅ 竞争关系分析")

def demo_use_cases():
    """演示使用场景"""
    print("\n💼 实际使用场景演示")
    print("=" * 60)
    
    scenarios = [
        {
            "title": "品牌合作分析",
            "question": "华与华与哪些品牌有合作关系？",
            "capability": "通过BRAND_COLLABORATION关系查询品牌间的合作情况"
        },
        {
            "title": "媒体投放策略",
            "question": "小米在哪些媒体平台进行推广？",
            "capability": "通过MEDIA_PLACEMENT关系分析品牌的媒体投放策略"
        },
        {
            "title": "竞争关系分析",
            "question": "华为和小米的竞争关系如何？",
            "capability": "通过COMPETES_WITH关系分析品牌间的竞争态势"
        },
        {
            "title": "传播活动查询",
            "question": "奥迪有哪些成功的传播活动？",
            "capability": "通过LAUNCHES_CAMPAIGN关系查询品牌的活动历史"
        },
        {
            "title": "策略效果评估",
            "question": "数字化营销策略的效果如何？",
            "capability": "通过USES_STRATEGY和MEASURES_KPI关系评估策略效果"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['title']}")
        print(f"   问题: {scenario['question']}")
        print(f"   能力: {scenario['capability']}")

def main():
    """主演示函数"""
    try:
        # 1. 实体提取演示
        demo_entity_extraction()
        
        # 2. 图谱模式演示
        demo_schema_design()
        
        # 3. Cypher生成演示
        demo_cypher_generation()
        
        # 4. RAG能力演示
        demo_rag_capabilities()
        
        # 5. 使用场景演示
        demo_use_cases()
        
        print("\n🎉 增强公关传播RAG系统演示完成！")
        print("\n📋 下一步操作:")
        print("1. 运行 python3 pr_enhanced_neo4j_integration.py 创建增强图谱")
        print("2. 运行 python3 test_enhanced_pr_rag.py 测试完整功能")
        print("3. 查看 Enhanced_PR_RAG_Guide.md 了解详细使用方法")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")

if __name__ == "__main__":
    main()
