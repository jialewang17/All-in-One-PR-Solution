"""
嵌入模型提供器
"""

from __future__ import annotations

from langchain_openai import OpenAIEmbeddings


class EmbeddingProvider:
    """集中管理向量嵌入模型，方便后续替换。"""

    def __init__(self, embeddings: OpenAIEmbeddings | None = None) -> None:
        self._embeddings = embeddings or OpenAIEmbeddings()

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        return self._embeddings

    def embed_query(self, query: str):
        return self._embeddings.embed_query(query)

