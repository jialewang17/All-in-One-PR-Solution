#!/usr/bin/env python3
"""
快速查询系统 - 直接从Neo4j查询公关传播RAG
"""

import os
import textwrap
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Neo4jVector
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import warnings
warnings.filterwarnings("ignore")

# Load environment variables
load_dotenv('.env', override=True)

# Neo4j connection
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE') or 'neo4j'

# Initialize connections
kg = Neo4jGraph(
    url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD, database=NEO4J_DATABASE
)

llm = ChatOpenAI(temperature=0)
embeddings = OpenAIEmbeddings()

def quick_query(question):
    """快速查询函数"""
    print(f"🤔 问题: {question}")
    print("=" * 80)
    
    try:
        # 使用向量搜索
        vector_store = Neo4jVector.from_existing_graph(
            embedding=embeddings,
            url=NEO4J_URI,
            username=NEO4J_USERNAME,
            password=NEO4J_PASSWORD,
            index_name='PR_OpenAI',
            node_label='PR_Chunk',
            text_node_properties=['text'],
            embedding_node_property='textEmbeddingOpenAI',
        )
        
        # 搜索相关文档
        docs = vector_store.similarity_search(question, k=5)
        
        if not docs:
            return "未找到相关信息"
        
        print(f"📚 找到 {len(docs)} 个相关文档片段")
        
        # 构建上下文
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # 创建专业prompt
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
        
        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=prompt_template
        )
        
        chain = LLMChain(llm=llm, prompt=prompt)
        response = chain.run(context=context, question=question)
        
        return response
        
    except Exception as e:
        return f"查询失败: {e}"

def main():
    """主函数 - 快速查询示例"""
    print("🚀 公关传播RAG快速查询系统")
    print("=" * 60)
    
    # 示例问题
    example_questions = [
        "美妆类品牌应该如何建立和消费者的联系",
        "华与华有哪些成功的品牌案例",
        "内容营销的核心策略是什么",
        "如何提升品牌传播效果"
    ]
    
    print("📋 示例问题:")
    for i, q in enumerate(example_questions, 1):
        print(f"{i}. {q}")
    
    print("\n💡 使用方法:")
    print("1. 直接运行: python3 quick_query.py")
    print("2. 在代码中调用: quick_query('你的问题')")
    print("3. 交互式查询: python3 neo4j_direct_query.py")
    
    # 测试一个示例问题
    print(f"\n🧪 测试查询:")
    test_question = "美妆类品牌应该如何建立和消费者的联系"
    answer = quick_query(test_question)
    
    print(f"\n🤖 回答:")
    print("-" * 40)
    print(textwrap.fill(answer, 80))

if __name__ == "__main__":
    main()


