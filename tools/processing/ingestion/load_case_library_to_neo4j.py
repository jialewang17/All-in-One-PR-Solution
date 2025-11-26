#!/usr/bin/env python3
"""
将案例库结构化表同步到 Neo4j，扩展 GraphRAG 的实体和关系。

支持：
- 渠道分类/渠道
- 公关目标
- 行业分类与品牌/案例
- 案例基础信息
"""

from __future__ import annotations

import argparse
from typing import Dict, List

from core.knowledge.reference_loader import ReferenceSources
from core.querying.graph import GraphClient


def _merge_channel(graph: GraphClient, primary: str, secondary: str, tertiary_items: List[str]):
    graph.query(
        """
        MERGE (c:ChannelCategory {name: $primary})
        MERGE (ch:Channel {name: $secondary})
        MERGE (ch)-[:BELONGS_TO_CHANNEL_CATEGORY]->(c)
        """,
        params={"primary": primary, "secondary": secondary},
    )
    for item in tertiary_items:
        item = item.strip()
        if not item:
            continue
        graph.query(
            """
            MERGE (sub:Channel {name: $item})
            MERGE (sub)-[:BELONGS_TO_CHANNEL_CATEGORY]->(:ChannelCategory {name: $primary})
            MERGE (sub)-[:RELATED_TO_CHANNEL]->(:Channel {name: $secondary})
            """,
            params={"item": item, "primary": primary, "secondary": secondary},
        )


def _merge_goal(graph: GraphClient, primary: str, secondary: str):
    graph.query(
        """
        MERGE (g1:PRGoal {name: $primary})
        MERGE (g2:PRGoal {name: $secondary})
        MERGE (g2)-[:REFINES]->(g1)
        """,
        params={"primary": primary, "secondary": secondary},
    )


def _merge_industry(graph: GraphClient, primary: str, secondaries: List[str]):
    graph.query("MERGE (:Industry {name: $name})", params={"name": primary})
    for sec in secondaries:
        sec = sec.strip()
        if not sec:
            continue
        graph.query(
            """
            MERGE (p:Industry {name: $primary})
            MERGE (c:Industry {name: $secondary})
            MERGE (c)-[:IN_INDUSTRY]->(p)
            """,
            params={"primary": primary, "secondary": sec},
        )


def _merge_case(graph: GraphClient, record: Dict[str, str]):
    name = record.get("企业") or record.get("品牌") or record.get("项目名称") or record.get("案例名称")
    if not name:
        return
    graph.query(
        """
        MERGE (c:PRCase {name: $name})
        SET c += $props
        """,
        params={"name": name, "props": record},
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync case library CSV/Docx into Neo4j.")
    parser.add_argument("--base-dir", default=".", help="Reference files base dir")
    args = parser.parse_args()

    ref = ReferenceSources(args.base_dir)
    graph = GraphClient()
    tables = ref.export_case_tables()

    channels = tables.get("channels", [])
    for row in channels:
        primary = str(row.get("一级") or "").strip() or str(row.get("一级1") or "").strip()
        secondary = str(row.get("二级1") or "").strip()
        tertiary = str(row.get("二级对应三级") or "")
        tertiary_items = [t.strip() for t in tertiary.split(",") if t.strip()]
        if primary or secondary:
            _merge_channel(graph, primary or secondary, secondary or primary, tertiary_items)

    goals = tables.get("goals", [])
    for row in goals:
        primary = str(row.get("一级分类") or "").strip()
        secondary = str(row.get("二级分类") or "").strip()
        if secondary:
            _merge_goal(graph, primary or secondary, secondary)

    industries = tables.get("industry_brand", [])
    for row in industries:
        primary = str(row.get("一级行业分类") or "").strip()
        secondaries = str(row.get("二级行业分类") or "").split(",")
        if primary:
            _merge_industry(graph, primary, secondaries)

    cases = tables.get("cases", [])
    for row in cases:
        _merge_case(graph, row)

    print("✅ 案例库/渠道/目标/行业 同步完成")


if __name__ == "__main__":
    main()
