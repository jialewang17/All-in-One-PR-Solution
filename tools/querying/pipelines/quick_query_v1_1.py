#!/usr/bin/env python3
"""
快速查询系统 v1.1 - Pipelines 子模块
基于 Section 节点的 Graph+Vector 检索流程
"""

import os
import textwrap
import warnings

from neo4j import GraphDatabase
from dotenv import load_dotenv

# 忽略第三方库的非关键警告，避免干扰交互体验
warnings.filterwarnings("ignore", category=UserWarning)

load_dotenv(".env", override=True)

# 导入新架构配置
try:
    from core.common.pr_neo4j_env import (
        NEO4J_URI,
        NEO4J_USERNAME,
        NEO4J_PASSWORD,
        NEO4J_DATABASE,
        VECTOR_INDEX_NAME,
        VECTOR_NODE_LABEL,
        VECTOR_SOURCE_PROPERTY,
        VECTOR_EMBEDDING_PROPERTY,
    )
except ImportError:
    # 降级配置
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    NEO4J_DATABASE = os.getenv("NEO4J_DATABASE") or "neo4j"
    VECTOR_INDEX_NAME = "SectionEmbedding"
    VECTOR_NODE_LABEL = "Section"
    VECTOR_SOURCE_PROPERTY = "text"
    VECTOR_EMBEDDING_PROPERTY = "textEmbedding"

# 初始化基础组件（保留统一的 OpenAI 入口）
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate

# ===== LangChain 新式调用：使用 RunnableSequence（prompt | llm）规避 LLMChain 弃用警告 =====
llm = ChatOpenAI(temperature=0)
embeddings = OpenAIEmbeddings()
prompt_template = """
你是一个专业的公关传播和品牌营销专家。基于以下公关传播相关内容，回答用户的问题。

相关内容：
{context}

问题：{question}

请基于这些内容，给出专业、详细、实用的回答。回答要求：
1. 基于提供的具体内容进行回答
2. 结合公关传播和品牌营销的专业知识
3. 提供具体可行的建议和策略
4. 回答要专业、准确、有针对性
5. 如果内容不够充分，可以结合你的专业知识进行补充

请用中文回答。
"""

prompt = PromptTemplate(input_variables=["context", "question"], template=prompt_template)
llm_chain = prompt | llm


def _get_driver():
    """获取 Neo4j 驱动，便于后续复用。"""
    return GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
        database=NEO4J_DATABASE,
    )


def _search_sections_vector(question: str, top_k: int = 5):
    """
    使用新版 Neo4j 向量检索接口（db.index.vector.queryNodes）获取 Section。
    避免触发 db.create.setVectorProperty 的弃用警告。
    """
    driver = _get_driver()
    question_embedding = embeddings.embed_query(question)
    cypher = f"""
    CALL db.index.vector.queryNodes($index, $topK, $embedding)
    YIELD node, score
    MATCH (node:{VECTOR_NODE_LABEL})
    WITH node, score,
         split(node.content, '\\n\\n')[0] AS title,
         CASE 
           WHEN size(split(node.content, '\\n\\n')) > 1 
           THEN split(node.content, '\\n\\n')[1]
           ELSE node.content
         END AS text
    RETURN text,
           title,
           node.id AS section_id,
           score
    ORDER BY score DESC
    """

    sections = []
    with driver.session() as session:
        for record in session.run(
            cypher,
            index=VECTOR_INDEX_NAME,
            topK=top_k,
            embedding=question_embedding,
        ):
            sections.append(
                {
                    "text": record["text"] or "",
                    "title": record["title"] or "未命名段落",
                    "section_id": record["section_id"],
                    "score": record["score"],
                }
            )

    driver.close()
    return sections


def quick_query_v1_1(question: str) -> str:
    """
    快速查询函数（v1.1 新架构版，逻辑对齐 v1 向量检索）
    - 向量检索由 Neo4j Vector Index 完成（避免弃用 API）
    - LLM 调用使用 RunnableSequence，规避 LangChain 弃用警告
    """
    try:
        sections = _search_sections_vector(question, top_k=5)
        if not sections:
            return "未找到相关信息"

        # 构建上下文，附带 section 信息便于溯源
        formatted_sections = []
        for idx, sec in enumerate(sections, 1):
            formatted_sections.append(
                f"【Section {idx} | {sec['title']} | Score={sec['score']:.3f}】\n{sec['text']}"
            )
        context = "\n\n".join(formatted_sections)

        result = llm_chain.invoke({"context": context, "question": question})

        # invoke 返回 ChatMessage / dict，统一抽取 content
        if isinstance(result, str):
            return result
        if hasattr(result, "content"):
            return result.content
        if isinstance(result, dict) and "text" in result:
            return result["text"]
        return str(result)
    except Exception as e:
        return f"查询失败: {e}"


def main():
    """主函数 - 快速查询示例（交互式）"""
    print("🚀 公关传播RAG快速查询系统 v1.1")
    print("=" * 60)
    print("📊 基于新架构：Section 节点 + 三级分类 + SPO 关系")
    print("=" * 60)

    example_questions = [
        "内容营销的核心策略是什么",
    ]

    print("📋 示例问题:")
    for idx, q in enumerate(example_questions, 1):
        print(f"{idx}. {q}")

    print("\n💡 使用方法:")
    print("1. 直接运行: python3 tools/querying/pipelines/quick_query_v1_1.py")
    print("2. 在代码中调用: quick_query_v1_1('你的问题')")

    print(f"\n🧪 测试查询:")
    test_question = example_questions[0]
    answer = quick_query_v1_1(test_question)

    print(f"\n🤖 回答:")
    print("-" * 40)
    print(textwrap.fill(answer, 80))
    print("-" * 40)


if __name__ == "__main__":
    main()



