#!/usr/bin/env python3
"""
增强公关传播RAG系统 v1.1 演示脚本
展示 v1.1 新架构的功能：三级分类 + Section + 实体分型 + SPO_REL
"""

import json
import os
import sys
from pathlib import Path

# 添加模块路径（确保路径正确）
project_root = Path(__file__).resolve().parents[1]
paths_to_add = {
    str(project_root),
    str(project_root / "core"),
}

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

# 使用绝对导入
try:
    from core.querying.pipelines import EnhancedPRRAGSystemV11
    from core.common.pr_category_schema import (
        CATEGORY_SCHEMA,
        get_category_l1_list,
        get_category_l2_list,
    )
    from core.processing.company_dictionary import get_company_dictionary
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print(f"📁 当前工作目录: {os.getcwd()}")
    print(f"📁 项目根目录: {project_root}")
    print(f"📁 sys.path 前10个路径:")
    for i, p in enumerate(sys.path[:10], 1):
        exists = "✅" if Path(p).exists() else "❌"
        print(f"  {i}. {exists} {p}")
    import traceback
    traceback.print_exc()
    raise


def demo_category_schema():
    """演示 v1.1 的三级分类体系"""
    print("🏗️ v1.1 三级分类体系演示")
    print("=" * 60)
    
    print("📊 一级分类（CategoryL1）:")
    l1_categories = get_category_l1_list()
    for i, cat_code in enumerate(l1_categories[:5], 1):  # 显示前5个
        cat_info = CATEGORY_SCHEMA.get(cat_code, {})
        cat_label = cat_info.get('label', cat_code)
        print(f"  {i}. {cat_code}: {cat_label}")
    if len(l1_categories) > 5:
        print(f"  ... 还有 {len(l1_categories) - 5} 个一级分类")
    
    print("\n📊 二级分类（CategoryL2）示例:")
    l2_categories = get_category_l2_list()
    for i, cat in enumerate(l2_categories[:10], 1):  # 显示前10个
        print(f"  {i}. {cat['code']}: {cat['label']} (父分类: {cat['parent_code']})")
    if len(l2_categories) > 10:
        print(f"  ... 还有 {len(l2_categories) - 10} 个二级分类")
    
    print("\n💡 分类体系特点:")
    print("  ✅ 两级分类结构，支持层次化组织")
    print("  ✅ 每个分类都有 code 和 label")
    print("  ✅ Section 节点通过 level1 和 level2 属性关联分类")
    print("  ✅ Company 节点通过 INVOLVED_IN_CATEGORY 关系关联 CategoryL2")


def demo_company_dictionary():
    """演示公司词典功能"""
    print("\n📚 公司词典功能演示")
    print("=" * 60)
    
    try:
        company_dict = get_company_dictionary()
        
        print(f"✅ 已加载 {len(company_dict.companies)} 个公司")
        
        # 演示文本匹配
        test_text = "奥迪公司通过数字化营销策略，在抖音、小红书等平台开展用户运营活动。"
        print(f"\n📄 测试文本: {test_text}")
        
        companies_found = company_dict.find_companies_in_text(test_text)
        if companies_found:
            print(f"🔍 匹配到的公司: {companies_found}")
        else:
            print("⚠️ 未匹配到公司")
        
        # 显示前10个公司示例
        print(f"\n📋 公司词典示例（前10个）:")
        for i, company in enumerate(sorted(company_dict.companies)[:10], 1):
            print(f"  {i}. {company}")
        
        print("\n💡 公司词典特点:")
        print("  ✅ 从 Neo4j 自动加载 Company 节点")
        print("  ✅ 支持文本中的公司名称匹配")
        print("  ✅ 用于关键词提取和实体识别")
        print("  ✅ 提高查询准确性")
        
    except Exception as e:
        print(f"⚠️ 公司词典加载失败: {e}")


def demo_v1_1_architecture():
    """演示 v1.1 新架构"""
    print("\n🏛️ v1.1 新架构演示")
    print("=" * 60)
    
    print("📦 核心节点类型:")
    nodes = [
        ("CategoryL1", "一级分类节点", "code, label"),
        ("CategoryL2", "二级分类节点", "code, label, parent_code"),
        ("Section", "文本段落节点", "id, title, text, level1, level2"),
        ("Company", "公司节点", "name, type, uncertain"),
        ("Brand", "品牌节点", "name, level, uncertain"),
        ("CompanyType", "公司类型节点", "code, label"),
        ("Campaign", "活动节点", "name"),
        ("Concept", "概念节点", "name"),
    ]
    for node_type, desc, props in nodes:
        print(f"  • {node_type:<15}: {desc}")
        print(f"    属性: {props}")
    
    print("\n🔗 核心关系类型:")
    relationships = [
        ("HAS_SUBCATEGORY", "CategoryL1 → CategoryL2", "分类层次关系"),
        ("HAS_SECTION", "CategoryL2 → Section", "分类包含段落"),
        ("MENTIONS_COMPANY", "Section → Company", "段落提及公司"),
        ("MENTIONS_BRAND", "Section → Brand", "段落提及品牌"),
        ("INVOLVED_IN_CATEGORY", "Company → CategoryL2", "公司涉及分类"),
        ("BELONGS_TO_BRAND", "Company → Brand", "公司所属品牌"),
        ("BELONGS_TO_TYPE", "Company → CompanyType", "公司类型"),
        ("OPERATES_IN_TYPE", "Brand → CompanyType", "品牌运营类型"),
        ("SPO_REL", "Company → Campaign/Concept/Company", "语义关系（predicate属性）"),
    ]
    for rel_type, pattern, desc in relationships:
        print(f"  • {rel_type:<20}: {pattern:<35} ({desc})")
    
    print("\n💡 v1.1 架构优势:")
    print("  ✅ 层次化分类体系，支持精细化管理")
    print("  ✅ Section 节点替代 PR_Chunk，更结构化")
    print("  ✅ SPO_REL 统一表达语义关系")
    print("  ✅ 实体分型（Company/Brand/CompanyType）更精确")
    print("  ✅ 支持向量检索和 GraphRAG 结合")


def demo_spo_relations():
    """演示 SPO_REL 关系"""
    print("\n🔗 SPO_REL 语义关系演示")
    print("=" * 60)
    
    print("📝 SPO_REL 关系说明:")
    print("  SPO_REL 是 v1.1 中统一表达语义关系的关系类型")
    print("  通过 predicate 属性存储具体的语义关系")
    
    print("\n📋 支持的语义关系（predicate 值）:")
    spo_examples = [
        ("launched", "发起活动", "Company → Campaign"),
        ("collaborates_with", "品牌合作", "Company → Company"),
        ("placed_in", "媒体投放", "Company → Concept"),
        ("uses", "使用策略", "Company → Concept"),
        ("competes_with", "竞争关系", "Company → Company"),
        ("creates", "创建内容", "Company → Concept"),
    ]
    for predicate, desc, pattern in spo_examples:
        print(f"  • {predicate:<20}: {desc:<15} ({pattern})")
    
    print("\n💻 Cypher 查询示例:")
    print("""
  # 查询公司发起的活动
  MATCH (c:Company)-[r:SPO_REL]->(camp:Campaign)
  WHERE r.predicate = "launched"
  RETURN c.name, camp.name
  
  # 查询品牌合作
  MATCH (c1:Company)-[r:SPO_REL]->(c2:Company)
  WHERE r.predicate CONTAINS "collaborat"
  RETURN c1.name, c2.name
  
  # 查询媒体投放
  MATCH (c:Company)-[r:SPO_REL]->(concept:Concept)
  WHERE toLower(r.predicate) CONTAINS "placed"
  RETURN c.name, concept.name
    """)
    
    print("\n💡 SPO_REL 优势:")
    print("  ✅ 统一的关系类型，简化查询")
    print("  ✅ predicate 属性灵活表达语义")
    print("  ✅ 支持中英文 predicate 值")
    print("  ✅ 替代 v1 的多种独立关系类型")


def demo_rag_capabilities():
    """演示 v1.1 RAG 系统能力"""
    print("\n🤖 v1.1 RAG 系统能力演示")
    print("=" * 60)
    
    print("📊 GraphRAG 能力:")
    print("  ✅ 基于新架构的 Cypher 查询生成")
    print("  ✅ 三重关系类型验证（生成前/执行前/执行时）")
    print("  ✅ 智能回退查询（多策略）")
    print("  ✅ 公司词典匹配")
    print("  ✅ 关键词提取优化")
    print("  ✅ 实体关系查询（INVOLVED_IN_CATEGORY, SPO_REL）")
    
    print("\n🔍 VectorRAG 能力:")
    print("  ✅ Section 向量相似性搜索")
    print("  ✅ 自动检测向量索引可用性")
    print("  ✅ 向量检索失败自动回退文本搜索")
    print("  ✅ 关联 Company, Brand, CategoryL2 信息")
    print("  ✅ 显示相似度分数")
    
    print("\n🎯 增强功能:")
    print("  ✅ 公司词典自动匹配")
    print("  ✅ 分类体系查询")
    print("  ✅ SPO_REL 语义关系查询")
    print("  ✅ 智能诊断和错误处理")
    print("  ✅ 多策略回退机制")


def demo_rag_queries():
    """演示 RAG 查询功能"""
    print("\n🔍 v1.1 RAG 查询演示")
    print("=" * 60)
    
    try:
        rag_system = EnhancedPRRAGSystemV11()
        
        test_questions = [
            "奥迪有哪些营销策略？",
            "哪些公司在电商销售策略方面有经验？",
            "品牌定位相关的案例有哪些？",
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{'='*60}")
            print(f"🤔 问题 {i}: {question}")
            print("-" * 60)
            
            try:
                # 测试 GraphRAG
                print("📊 GraphRAG 回答:")
                graph_answer = rag_system.query(question, use_graph=True)
                print(graph_answer[:300] + "..." if len(graph_answer) > 300 else graph_answer)
                
                print("\n" + "-" * 40)
                
                # 测试 VectorRAG
                print("🔍 VectorRAG 回答:")
                vector_answer = rag_system.query(question, use_graph=False)
                print(vector_answer[:300] + "..." if len(vector_answer) > 300 else vector_answer)
                
            except Exception as e:
                print(f"❌ 查询失败: {e}")
        
    except Exception as e:
        print(f"⚠️ RAG 系统初始化失败: {e}")
        print("   请确保 Neo4j 连接正常，且已创建 v1.1 图谱")


def demo_entity_relationships():
    """演示实体关系查询"""
    print("\n🔗 实体关系查询演示")
    print("=" * 60)
    
    try:
        rag_system = EnhancedPRRAGSystemV11()
        
        test_entities = ["奥迪", "小米", "华与华"]
        
        for entity in test_entities:
            print(f"\n🏷️ 查询实体: {entity}")
            print("-" * 40)
            
            try:
                relationships = rag_system.get_entity_relationships(entity)
                
                if relationships.get('error'):
                    print(f"  ⚠️ {relationships['error']}")
                    continue
                
                print(f"  实体类型: {relationships.get('entity_type', 'Unknown')}")
                
                outgoing = relationships.get('outgoing_relationships', [])
                if outgoing:
                    print(f"\n  出向关系 ({len(outgoing)} 个):")
                    for rel in outgoing[:5]:  # 显示前5个
                        rel_type = rel.get('type', '')
                        related = rel.get('related_entity', '')
                        context = rel.get('context', '')
                        print(f"    • {rel_type}: → {related}")
                        if context:
                            print(f"      上下文: {context}")
                
                incoming = relationships.get('incoming_relationships', [])
                if incoming:
                    print(f"\n  入向关系 ({len(incoming)} 个):")
                    for rel in incoming[:5]:  # 显示前5个
                        rel_type = rel.get('type', '')
                        related = rel.get('related_entity', '')
                        print(f"    • {rel_type}: ← {related}")
                
                if not outgoing and not incoming:
                    print("  ℹ️ 未找到关系")
                    
            except Exception as e:
                print(f"  ❌ 查询失败: {e}")
        
    except Exception as e:
        print(f"⚠️ RAG 系统初始化失败: {e}")


def demo_use_cases():
    """演示 v1.1 使用场景"""
    print("\n💼 v1.1 实际使用场景演示")
    print("=" * 60)
    
    scenarios = [
        {
            "title": "分类体系查询",
            "question": "品牌定位相关的案例有哪些？",
            "capability": "通过 CategoryL2.code 查询特定分类下的 Section",
            "cypher_example": """
MATCH (cat:CategoryL2 {code: "brand_info.brand_positioning"})-[:HAS_SECTION]->(s:Section)
RETURN s.title, s.text
LIMIT 10
            """
        },
        {
            "title": "公司分类关联查询",
            "question": "哪些公司在电商销售策略方面有经验？",
            "capability": "通过 INVOLVED_IN_CATEGORY 关系查询公司参与的分类",
            "cypher_example": """
MATCH (c:Company)-[r:INVOLVED_IN_CATEGORY]->(cat:CategoryL2)
WHERE cat.code CONTAINS "ecommerce" OR cat.code CONTAINS "sales"
RETURN c.name, cat.label, r.count
ORDER BY r.count DESC
            """
        },
        {
            "title": "SPO_REL 语义关系查询",
            "question": "奥迪发起了哪些活动？",
            "capability": "通过 SPO_REL 关系的 predicate 属性查询语义关系",
            "cypher_example": """
MATCH (c:Company)-[r:SPO_REL]->(camp:Campaign)
WHERE c.name CONTAINS "奥迪" AND r.predicate CONTAINS "launch"
RETURN c.name, camp.name, r.predicate
            """
        },
        {
            "title": "Section 向量检索",
            "question": "数字化营销的最佳实践是什么？",
            "capability": "使用向量相似性搜索找到最相关的 Section",
            "cypher_example": """
CALL db.index.vector.queryNodes('section_vector_index', 5, $embedding)
YIELD node, score
MATCH (node:Section)
RETURN node.title, substring(node.text, 0, 200), score
ORDER BY score DESC
            """
        },
        {
            "title": "公司词典匹配",
            "question": "奥迪的营销策略是什么？",
            "capability": "使用公司词典自动识别问题中的公司名称",
            "note": "系统会自动从问题中提取'奥迪'，并使用公司词典验证"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['title']}")
        print(f"   问题: {scenario['question']}")
        print(f"   能力: {scenario['capability']}")
        if 'cypher_example' in scenario:
            print(f"   Cypher 示例:")
            print(scenario['cypher_example'].strip())
        if 'note' in scenario:
            print(f"   说明: {scenario['note']}")


def demo_v1_vs_v1_1():
    """演示 v1 与 v1.1 的区别"""
    print("\n🔄 v1 与 v1.1 架构对比")
    print("=" * 60)
    
    print("📦 节点类型对比:")
    print("  v1:")
    print("    • PR_Chunk (文本分块)")
    print("    • Brand, Company, Agency, Campaign, Media, Strategy")
    print("  v1.1:")
    print("    • Section (结构化段落，带分类信息)")
    print("    • CategoryL1, CategoryL2 (两级分类)")
    print("    • Company, Brand, CompanyType, Campaign, Concept")
    
    print("\n🔗 关系类型对比:")
    print("  v1:")
    print("    • BRAND_COLLABORATION, MEDIA_PLACEMENT, COMPETES_WITH")
    print("    • LAUNCHES_CAMPAIGN, USES_STRATEGY, CREATES_CONTENT")
    print("    • NEXT (文本顺序)")
    print("  v1.1:")
    print("    • SPO_REL (统一语义关系，predicate 属性表达具体语义)")
    print("    • HAS_SUBCATEGORY, HAS_SECTION (分类层次)")
    print("    • MENTIONS_COMPANY, MENTIONS_BRAND (段落关联)")
    print("    • INVOLVED_IN_CATEGORY (公司分类关联)")
    
    print("\n💡 主要改进:")
    print("  ✅ 层次化分类体系，支持精细化管理")
    print("  ✅ Section 节点替代 PR_Chunk，更结构化")
    print("  ✅ SPO_REL 统一表达语义关系，更灵活")
    print("  ✅ 公司词典自动匹配，提高准确性")
    print("  ✅ 三重验证机制，提高查询可靠性")
    print("  ✅ 智能回退策略，提高查询成功率")


def main():
    """主演示函数"""
    print("🚀 增强公关传播RAG系统 v1.1 完整演示")
    print("=" * 80)
    
    try:
        # 1. 分类体系演示
        demo_category_schema()
        
        # 2. 公司词典演示
        demo_company_dictionary()
        
        # 3. v1.1 架构演示
        demo_v1_1_architecture()
        
        # 4. SPO_REL 关系演示
        demo_spo_relations()
        
        # 5. RAG 能力演示
        demo_rag_capabilities()
        
        # 6. 使用场景演示
        demo_use_cases()
        
        # 7. v1 vs v1.1 对比
        demo_v1_vs_v1_1()
        
        # 8. RAG 查询演示（可选，需要 Neo4j 连接）
        print("\n" + "=" * 80)
        user_input = input("\n是否运行 RAG 查询演示？(需要 Neo4j 连接) [y/N]: ")
        if user_input.lower() == 'y':
            demo_rag_queries()
            demo_entity_relationships()
        
        print("\n" + "=" * 80)
        print("🎉 v1.1 增强公关传播RAG系统演示完成！")
        print("\n📋 下一步操作:")
        print("1. 运行 '1 一键构建增强图谱' 创建 v1.1 图谱")
        print("2. 运行 '6 增强RAG对话' 进行实际查询")
        print("3. 运行 '8 快速查询' 使用 v1.1 快速问答")
        print("4. 查看 docs/Enhanced_KG_Design.md 了解详细使用方法")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


