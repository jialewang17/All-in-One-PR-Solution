#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neo4j 新结构自检与示例脚本（Graph 查询子模块）
适用于“三级分类 + Section + 实体分型 + SPO”知识图谱
"""

import os
from typing import List, Dict

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from langchain_community.graphs import Neo4jGraph


def load_environment():
    """加载 .env 配置"""
    if load_dotenv:
        load_dotenv(".env", override=True)
        return

    # 兜底：手动解析 .env
    if not os.path.exists(".env"):
        return

    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip()


class EnhancedNeo4jInspector:
    """面向增强结构的 Neo4j 自检工具"""

    def __init__(
        self,
        uri: str = None,
        username: str = None,
        password: str = None,
        database: str = None,
    ) -> None:
        load_environment()

        self.uri = uri or os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "")
        self.database = database or os.getenv("NEO4J_DATABASE", "neo4j")

        self.graph = Neo4jGraph(
            url=self.uri,
            username=self.username,
            password=self.password,
            database=self.database,
        )

    def _fetch_count(self, query: str, key: str = "count") -> int:
        records = self.graph.query(query)
        if not records:
            return 0
        return int(records[0].get(key, 0) or 0)

    def show_node_statistics(self) -> None:
        print("\n📊 节点统计")
        items = [
            ("Section", "MATCH (n:Section) RETURN count(n) AS count"),
            ("CategoryL2", "MATCH (n:CategoryL2) RETURN count(n) AS count"),
            ("Company", "MATCH (n:Company) RETURN count(n) AS count"),
            ("Brand", "MATCH (n:Brand) RETURN count(n) AS count"),
        ]
        for label, query in items:
            count = self._fetch_count(query)
            print(f"  • {label:<12}: {count}")

    def show_relationship_statistics(self) -> None:
        print("\n🔗 关系统计")
        items = [
            ("HAS_SUBCATEGORY", "MATCH ()-[r:HAS_SUBCATEGORY]->() RETURN count(r) AS count"),
            ("HAS_SECTION", "MATCH ()-[r:HAS_SECTION]->() RETURN count(r) AS count"),
            ("MENTIONS_COMPANY", "MATCH ()-[r:MENTIONS_COMPANY]->() RETURN count(r) AS count"),
            ("MENTIONS_BRAND", "MATCH ()-[r:MENTIONS_BRAND]->() RETURN count(r) AS count"),
            ("INVOLVED_IN_CATEGORY", "MATCH ()-[r:INVOLVED_IN_CATEGORY]->() RETURN count(r) AS count"),
            ("SPO_REL", "MATCH ()-[r:SPO_REL]->() RETURN count(r) AS count"),
        ]
        for name, query in items:
            count = self._fetch_count(query)
            print(f"  • {name:<20}: {count}")

    def run_examples(self) -> None:
        print("\n🧪 示例查询（展示前 5 条，若存在）")

        examples: List[Dict[str, str]] = [
            {
                "title": "L1-L2 分类结构",
                "query": """
                    MATCH (c1:CategoryL1)-[:HAS_SUBCATEGORY]->(c2:CategoryL2)
                    RETURN c1.code AS categoryL1, c2.code AS categoryL2, c2.label AS label
                    LIMIT 5
                """,
            },
            {
                "title": "CategoryL2 下的 Section",
                "query": """
                    MATCH (c2:CategoryL2)-[:HAS_SECTION]->(s:Section)
                    RETURN c2.code AS categoryL2, s.id AS sectionId, s.title AS sectionTitle
                    LIMIT 5
                """,
            },
            {
                "title": "Section 提到的公司",
                "query": """
                    MATCH (s:Section)-[:MENTIONS_COMPANY]->(c:Company)
                    RETURN s.id AS sectionId, c.name AS company, s.title AS sectionTitle
                    LIMIT 5
                """,
            },
            {
                "title": "Section 提到的品牌",
                "query": """
                    MATCH (s:Section)-[:MENTIONS_BRAND]->(b:Brand)
                    RETURN s.id AS sectionId, b.name AS brand, s.title AS sectionTitle
                    LIMIT 5
                """,
            },
            {
                "title": "公司参与的分类",
                "query": """
                    MATCH (c:Company)-[r:INVOLVED_IN_CATEGORY]->(c2:CategoryL2)
                    RETURN c.name AS company, c2.code AS categoryL2, r.count AS involvementCount
                    ORDER BY involvementCount DESC
                    LIMIT 5
                """,
            },
            {
                "title": "公司相关的 SPO 行为",
                "query": """
                    MATCH (c:Company)-[r:SPO_REL]->(target)
                    RETURN
                        c.name AS company,
                        r.predicate AS predicate,
                        COALESCE(target.name, target.title, target.id) AS targetName,
                        labels(target)[0] AS targetType
                    LIMIT 5
                """,
            },
        ]

        for item in examples:
            print(f"\n▶ {item['title']}")
            try:
                records = self.graph.query(item["query"])
                if not records:
                    print("   （无数据）")
                    continue
                for record in records:
                    pretty = ", ".join(
                        f"{key}={value}"
                        for key, value in record.items()
                        if value not in (None, "", [], {})
                    )
                    print(f"   {pretty}")
            except Exception as exc:
                print(f"   ⚠ 查询失败: {exc}")

    def run(self) -> None:
        print("🚀 Neo4j 新结构自检与示例")
        print("=" * 60)
        print(f"URI      : {self.uri}")
        print(f"Database : {self.database}")
        print(f"Username : {self.username}")

        try:
            self.show_node_statistics()
            self.show_relationship_statistics()
            self.run_examples()
            print("\n✅ 自检完成")
        except Exception as exc:
            print(f"\n❌ 自检失败: {exc}")


def main() -> None:
    inspector = EnhancedNeo4jInspector()
    inspector.run()


if __name__ == "__main__":
    main()



