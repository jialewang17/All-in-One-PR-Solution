#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强知识图谱查询示例（Graph 查询子模块）
展示如何查询公司相关的营销内容和竞品
"""

import sys
import os
from neo4j import GraphDatabase

# 加载环境变量
try:
    from dotenv import load_dotenv

    load_dotenv(".env", override=True)
except Exception:
    # 手动读取.env文件
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


def get_driver():
    """获取Neo4j驱动"""
    uri = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")
    database = os.getenv("NEO4J_DATABASE", "neo4j")

    return GraphDatabase.driver(uri, auth=(username, password)), database


def query_company_marketing_by_stage(company_name: str):
    """查询公司相关的所有营销内容（按阶段组织）"""
    driver, database = get_driver()

    with driver.session(database=database) as session:
        query = """
        MATCH (c:Company {name: $company_name})-[r:INVOLVED_IN_CATEGORY]->(c2:CategoryL2)
        MATCH (c1:CategoryL1)-[:HAS_SUBCATEGORY]->(c2)
        MATCH (c2)-[:HAS_SECTION]->(s:Section)
        MATCH (s)-[:MENTIONS_COMPANY]->(c)
        WITH c1, c2, s, r.count as mention_count
        RETURN c1.label as level1_name, 
               c2.label as level2_name,
               mention_count,
               collect(DISTINCT {title: s.title, text: s.text[0..200]}) as sections
        ORDER BY mention_count DESC, c1.label, c2.label
        LIMIT 20
        """

        print(f"\n📊 {company_name} 的营销内容（按阶段组织）")
        print("=" * 70)

        result = session.run(query, company_name=company_name)
        for record in result:
            print(f"\n【{record['level1_name']}】- {record['level2_name']}")
            print(f"  出现次数: {record['mention_count']}")
            print(f"  相关Section: {len(record['sections'])} 个")
            for i, sec in enumerate(record["sections"][:3], 1):
                print(f"    {i}. {sec.get('title', '无标题')}")
                print(f"       {sec.get('text', '')[:100]}...")

    driver.close()


def query_similar_companies(company_name: str):
    """查询同类型公司（相同CategoryL2下出现的其他公司）"""
    driver, database = get_driver()

    with driver.session(database=database) as session:
        query = """
        MATCH (c:Company {name: $company_name})-[r1:INVOLVED_IN_CATEGORY]->(c2:CategoryL2)
        MATCH (other:Company)-[r2:INVOLVED_IN_CATEGORY]->(c2)
        WHERE other.name <> $company_name
        WITH c2, other, r2.count as other_count
        RETURN c2.label as stage_name,
               c2.code as stage_code,
               collect(DISTINCT {name: other.name, count: other_count}) as similar_companies
        ORDER BY size(similar_companies) DESC
        LIMIT 10
        """

        print(f"\n🔍 {company_name} 的同类型公司（相同阶段）")
        print("=" * 70)

        result = session.run(query, company_name=company_name)
        for record in result:
            if record["similar_companies"]:
                print(f"\n阶段: {record['stage_name']} ({record['stage_code']})")
                for comp in record["similar_companies"][:5]:
                    print(f"  • {comp['name']} (出现{comp['count']}次)")


def query_competitor_companies(company_name: str):
    """查询竞品公司（基于相似SPO行为）"""
    driver, database = get_driver()

    with driver.session(database=database) as session:
        query = """
        MATCH (c:Company {name: $company_name})-[r1:SPO_REL]->(obj1)
        MATCH (other:Company)-[r2:SPO_REL]->(obj2)
        WHERE other.name <> $company_name 
          AND r1.predicate = r2.predicate
          AND r1.level2_code = r2.level2_code
        WITH other, r1.level2_code as stage_code, 
             count(DISTINCT r1.predicate) as similar_actions,
             collect(DISTINCT r1.predicate) as shared_predicates
        RETURN other.name as competitor, 
               similar_actions,
               shared_predicates,
               stage_code
        ORDER BY similar_actions DESC
        LIMIT 10
        """

        print(f"\n⚔️ {company_name} 的竞品公司（相似SPO行为）")
        print("=" * 70)

        result = session.run(query, company_name=company_name)
        competitors = []
        for record in result:
            competitors.append(
                {
                    "name": record["competitor"],
                    "score": record["similar_actions"],
                    "predicates": record["shared_predicates"],
                    "stage": record["stage_code"],
                }
            )

        if competitors:
            for comp in competitors:
                print(f"\n  {comp['name']}:")
                print(f"    相似行为: {comp['score']} 次")
                print(f"    共同行为: {', '.join(comp['predicates'][:5])}")
                print(f"    阶段: {comp['stage']}")
        else:
            print("  未找到竞品公司")


def query_company_in_stage(company_name: str, stage_code: str):
    """查询公司在特定阶段的内容和SPO关系"""
    driver, database = get_driver()

    with driver.session(database=database) as session:
        # 查询Section
        query1 = """
        MATCH (c:Company {name: $company_name})
        MATCH (c2:CategoryL2 {code: $stage_code})
        MATCH (c2)-[:HAS_SECTION]->(s:Section)
        MATCH (s)-[:MENTIONS_COMPANY]->(c)
        RETURN s.title as title, s.text as text
        LIMIT 10
        """

        print(f"\n📄 {company_name} 在阶段 {stage_code} 的内容")
        print("=" * 70)

        result = session.run(query1, company_name=company_name, stage_code=stage_code)
        sections = []
        for record in result:
            sections.append({"title": record["title"], "text": record["text"]})
            print(f"\n标题: {record['title']}")
            print(f"内容: {record['text'][:300]}...")

        # 查询SPO关系
        query2 = """
        MATCH (c:Company {name: $company_name})-[r:SPO_REL]->(obj)
        WHERE r.level2_code = $stage_code
        RETURN r.predicate as action, obj.name as target, labels(obj)[0] as target_type
        LIMIT 10
        """

        print(f"\n\n🎯 {company_name} 在阶段 {stage_code} 的行为（SPO）")
        print("=" * 70)

        result = session.run(query2, company_name=company_name, stage_code=stage_code)
        for record in result:
            print(f"  {record['action']} -> {record['target']} ({record['target_type']})")

        # 查询同阶段其他公司
        query3 = """
        MATCH (c:Company {name: $company_name})-[:INVOLVED_IN_CATEGORY]->(c2:CategoryL2 {code: $stage_code})
        MATCH (other:Company)-[r:INVOLVED_IN_CATEGORY]->(c2)
        WHERE other.name <> $company_name
        RETURN other.name as company, r.count as count
        ORDER BY count DESC
        LIMIT 5
        """

        print(f"\n\n👥 同阶段其他公司（{stage_code}）")
        print("=" * 70)

        result = session.run(query3, company_name=company_name, stage_code=stage_code)
        for record in result:
            print(f"  {record['company']}: 出现{record['count']}次")

    driver.close()


def query_stage_companies(stage_code: str):
    """查询某个阶段下被提到最多的公司"""
    driver, database = get_driver()

    with driver.session(database=database) as session:
        query = """
        MATCH (c2:CategoryL2 {code: $stage_code})
        MATCH (c:Company)-[r:INVOLVED_IN_CATEGORY]->(c2)
        RETURN c.name as company, r.count as mention_count
        ORDER BY mention_count DESC
        LIMIT 10
        """

        print(f"\n📊 阶段 {stage_code} 下的公司排名")
        print("=" * 70)

        result = session.run(query, stage_code=stage_code)
        for i, record in enumerate(result, 1):
            print(f"  {i}. {record['company']}: {record['mention_count']} 次")

        # 查询典型做法（SPO predicate）
        query2 = """
        MATCH (c2:CategoryL2 {code: $stage_code})
        MATCH (c:Company)-[r:SPO_REL]->(obj)
        WHERE r.level2_code = $stage_code
        WITH r.predicate as action, count(*) as frequency
        RETURN action, frequency
        ORDER BY frequency DESC
        LIMIT 10
        """

        print(f"\n\n🎯 该阶段的典型行为（SPO predicate）")
        print("=" * 70)

        result = session.run(query2, stage_code=stage_code)
        for record in result:
            print(f"  {record['action']}: {record['frequency']} 次")

    driver.close()


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python3 tools/querying/graph/query_enhanced_kg.py company <公司名>")
        print("  python3 tools/querying/graph/query_enhanced_kg.py company_stage <公司名> <阶段code>")
        print("  python3 tools/querying/graph/query_enhanced_kg.py stage <阶段code>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "company" and len(sys.argv) > 2:
        company_name = sys.argv[2]
        query_company_marketing_by_stage(company_name)
        query_similar_companies(company_name)
        query_competitor_companies(company_name)

    elif command == "company_stage" and len(sys.argv) > 3:
        company_name = sys.argv[2]
        stage_code = sys.argv[3]
        query_company_in_stage(company_name, stage_code)

    elif command == "stage" and len(sys.argv) > 2:
        stage_code = sys.argv[2]
        query_stage_companies(stage_code)

    else:
        print("❌ 参数错误，请查看使用方法")


if __name__ == "__main__":
    main()



