"""
Neo4j 客户端封装：集中管理连接与查询。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from langchain_community.graphs import Neo4jGraph

from core.common.pr_neo4j_env import (
    NEO4J_DATABASE,
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USERNAME,
)


class GraphClient:
    """提供统一的 Neo4jGraph 访问接口。"""

    def __init__(
        self,
        uri: str = NEO4J_URI,
        username: str = NEO4J_USERNAME,
        password: str = NEO4J_PASSWORD,
        database: str = NEO4J_DATABASE,
    ) -> None:
        self._graph = Neo4jGraph(
            url=uri,
            username=username,
            password=password,
            database=database,
        )

    def query(self, cypher: str, params: Optional[Dict[str, Any]] = None):
        """执行 Cypher 查询。"""
        return self._graph.query(cypher, params=params) if params else self._graph.query(cypher)

    @property
    def raw(self) -> Neo4jGraph:
        """暴露底层 Neo4jGraph 实例，供特殊场景直接访问。"""
        return self._graph

