#!/usr/bin/env python3
"""
增强公关传播 RAG v1.1 端到端测试

覆盖范围：
- Neo4j 连接与基础统计
- 分类体系 / 公司词典 / 组织分类器
- GraphRAG + VectorRAG 双通路问答
"""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for candidate in {str(PROJECT_ROOT), str(PROJECT_ROOT / "core")}:
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from core.querying.pipelines import EnhancedPRRAGSystemV11
from core.common.pr_category_schema import (
    CATEGORY_SCHEMA,
    get_category_l1_list,
    get_category_l2_list,
)
from core.processing.company_dictionary import get_company_dictionary
from core.processing.extractors.org_classifier import OrganizationClassifier
from core.common.pr_neo4j_env import graph


def test_neo4j_connection():
    """检查 Neo4j 是否可访问，并输出核心节点/关系统计"""
    print("\n🧪 Neo4j 连接与统计")
    print("=" * 60)
    try:
        graph.query("RETURN 1 AS ok")
        print("✅ Neo4j 连接正常")
    except Exception as exc:
        raise RuntimeError(f"无法连接 Neo4j: {exc}") from exc

    node_queries = [
        ("总节点", "MATCH (n) RETURN count(n) AS c"),
        ("Section", "MATCH (:Section) RETURN count(*) AS c"),
        ("Company", "MATCH (:Company) RETURN count(*) AS c"),
        ("Brand", "MATCH (:Brand) RETURN count(*) AS c"),
    ]
    rel_queries = [
        ("SPO_REL", "MATCH ()-[r:SPO_REL]->() RETURN count(r) AS c"),
        ("INVOLVED_IN_CATEGORY", "MATCH ()-[r:INVOLVED_IN_CATEGORY]->() RETURN count(r) AS c"),
        ("MENTIONS_COMPANY", "MATCH ()-[r:MENTIONS_COMPANY]->() RETURN count(r) AS c"),
    ]

    for label, query in node_queries + rel_queries:
        result = graph.query(query)
        count = result[0]["c"] if result else 0
        print(f"  • {label:<22}: {count}")


def test_category_schema():
    """验证分类体系定义是否完整"""
    print("\n🧪 分类体系")
    print("=" * 60)
    l1 = get_category_l1_list()
    l2 = get_category_l2_list()
    print(f"✅ 一级分类 {len(l1)} 个，示例: {l1[:5]}")
    print(f"✅ 二级分类 {len(l2)} 个")

    missing = [
        item for item in l2 if item.get("parent_code") not in CATEGORY_SCHEMA
    ]
    if missing:
        print("⚠️ 存在缺失父分类的二级分类:")
        for item in missing[:5]:
            print(f"  - {item['code']} -> {item.get('parent_code')}")
    else:
        print("✅ 二级分类 parent_code 均可解析")


def test_company_dictionary():
    """检查公司词典是否能匹配文本"""
    print("\n🧪 公司词典")
    print("=" * 60)
    dictionary = get_company_dictionary()
    print(f"✅ 当前公司数量: {len(dictionary.companies)}")
    sample = "奥迪与华与华合作，在抖音与小红书同步投放。"
    matches = dictionary.find_companies_in_text(sample)
    print(f"🔍 文本匹配结果: {matches or '未命中'}")


def test_organization_classifier():
    """验证组织分类器输出"""
    print("\n🧪 组织分类器")
    print("=" * 60)
    classifier = OrganizationClassifier()
    for name in ["奥迪", "小米公司", "抖音", "华与华"]:
        result = classifier.classify_entity(name)
        entity_type = result.get("type", "unknown")
        confidence = result.get("confidence")
        print(f"  - {name:<6}: {entity_type:<10} ({confidence:.2f})")


def test_rag_queries():
    """运行 GraphRAG + VectorRAG 问答"""
    print("\n🧪 GraphRAG / VectorRAG 问答")
    print("=" * 60)
    rag = EnhancedPRRAGSystemV11()
    questions = [
        "奥迪有哪些营销策略？",
        "哪些公司在电商销售策略方面有经验？",
    ]
    for q in questions:
        print(f"\n🤔 问题: {q}")
        try:
            graph_answer = rag.query(q, use_graph=True)
            print("📊 GraphRAG:", (graph_answer[:200] + "...") if graph_answer else "无结果")
        except Exception as exc:
            print(f"❌ GraphRAG 失败: {exc}")

        try:
            vector_answer = rag.query(q, use_graph=False)
            print("🔍 VectorRAG:", (vector_answer[:200] + "...") if vector_answer else "无结果")
        except Exception as exc:
            print(f"❌ VectorRAG 失败: {exc}")


def main():
    print("🚀 v1.1 增强 RAG 综合测试")
    print("=" * 80)
    checkpoints = []
    for name, func in [
        ("Neo4j 连接", test_neo4j_connection),
        ("分类体系", test_category_schema),
        ("公司词典", test_company_dictionary),
        ("组织分类器", test_organization_classifier),
        ("RAG 问答", test_rag_queries),
    ]:
        try:
            func()
            checkpoints.append((name, True))
        except Exception as exc:
            checkpoints.append((name, False))
            print(f"\n❌ {name} 测试失败: {exc}")

    print("\n📊 汇总")
    print("=" * 40)
    passed = sum(1 for _, ok in checkpoints if ok)
    for name, ok in checkpoints:
        status = "✅" if ok else "❌"
        print(f"{status} {name}")
    print(f"\n完成: {passed}/{len(checkpoints)} 个测试")


if __name__ == "__main__":
    main()


