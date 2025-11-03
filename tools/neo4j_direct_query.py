#!/usr/bin/env python3
"""
Neo4j直接查询系统
直接从Neo4j读取现有数据，进行智能问答
跳过所有预处理步骤
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

class Neo4jDirectQuery:
    def __init__(self):
        """初始化Neo4j直接查询系统"""
        self.kg = kg
        self.llm = llm
        self.embeddings = embeddings
        
    def check_neo4j_status(self):
        """检查Neo4j数据库状态"""
        print("🔍 检查Neo4j数据库状态...")
        
        try:
            # 检查节点类型
            node_types_query = "CALL db.labels() YIELD label RETURN label"
            node_types = self.kg.query(node_types_query)
            print(f"📊 节点类型: {[item['label'] for item in node_types]}")
            
            # 检查关系类型
            rel_types_query = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
            rel_types = self.kg.query(rel_types_query)
            print(f"🔗 关系类型: {[item['relationshipType'] for item in rel_types]}")
            
            # 检查PR_Chunk节点数量
            chunk_count_query = "MATCH (c:PR_Chunk) RETURN count(c) as count"
            result = self.kg.query(chunk_count_query)
            chunk_count = result[0]['count'] if result else 0
            print(f"📄 PR_Chunk节点数量: {chunk_count}")
            
            # 检查NEXT关系数量
            next_count_query = "MATCH ()-[r:NEXT]->() RETURN count(r) as count"
            result = self.kg.query(next_count_query)
            next_count = result[0]['count'] if result else 0
            print(f"🔗 NEXT关系数量: {next_count}")
            
            # 检查向量索引
            try:
                vector_store = Neo4jVector.from_existing_graph(
                    embedding=self.embeddings,
                    url=NEO4J_URI,
                    username=NEO4J_USERNAME,
                    password=NEO4J_PASSWORD,
                    index_name='PR_OpenAI',
                    node_label='PR_Chunk',
                    text_node_properties=['text'],
                    embedding_node_property='textEmbeddingOpenAI',
                )
                print("✅ 向量索引可用")
            except Exception as e:
                print(f"⚠️ 向量索引不可用: {e}")
            
            return chunk_count > 0
            
        except Exception as e:
            print(f"❌ 检查Neo4j状态失败: {e}")
            return False
    
    def query_with_vector_search(self, question):
        """使用向量搜索查询"""
        print("🔍 使用向量搜索查询...")
        
        try:
            vector_store = Neo4jVector.from_existing_graph(
                embedding=self.embeddings,
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
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            response = chain.run(context=context, question=question)
            
            return response
            
        except Exception as e:
            return f"向量搜索查询失败: {e}"
    
    def query_with_cypher(self, question):
        """使用Cypher查询"""
        print("🔍 使用Cypher查询...")
        
        try:
            # 构建Cypher查询
            cypher_query = f"""
            MATCH (c:PR_Chunk)
            WHERE c.text CONTAINS '{question}' OR 
                  c.content_type CONTAINS '{question}' OR
                  c.industry CONTAINS '{question}' OR
                  ANY(brand IN c.brand_mentioned WHERE brand CONTAINS '{question}')
            RETURN c.text as text, c.content_type as content_type, 
                   c.industry as industry, c.brand_mentioned as brand_mentioned
            LIMIT 10
            """
            
            result = self.kg.query(cypher_query)
            
            if not result:
                return "未找到相关信息"
            
            print(f"📊 找到 {len(result)} 个相关记录")
            
            # 构建上下文
            context_parts = []
            for record in result:
                text = record.get('text', '')
                content_type = record.get('content_type', '')
                industry = record.get('industry', '')
                brand_mentioned = record.get('brand_mentioned', [])
                
                context_part = f"内容: {text[:200]}...\n类型: {content_type}\n行业: {industry}\n品牌: {brand_mentioned}"
                context_parts.append(context_part)
            
            context = "\n\n".join(context_parts)
            
            # 创建prompt
            prompt_template = """
            基于以下公关传播数据，回答用户的问题：
            
            数据：
            {context}
            
            问题：{question}
            
            请给出专业、详细的回答。
            """
            
            prompt = PromptTemplate(
                input_variables=["context", "question"],
                template=prompt_template
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            response = chain.run(context=context, question=question)
            
            return response
            
        except Exception as e:
            return f"Cypher查询失败: {e}"
    
    def query(self, question, method="vector"):
        """查询方法"""
        print(f"🤔 问题: {question}")
        print("=" * 80)
        
        if method == "vector":
            return self.query_with_vector_search(question)
        elif method == "cypher":
            return self.query_with_cypher(question)
        else:
            return "无效的查询方法"
    
    def interactive_query(self):
        """交互式查询"""
        print("🚀 Neo4j直接查询系统")
        print("=" * 60)
        
        # 检查数据库状态
        if not self.check_neo4j_status():
            print("❌ Neo4j数据库中没有找到PR_Chunk节点")
            print("请确保已经运行过数据导入步骤")
            return
        
        print("\n✅ 数据库状态正常，可以开始查询")
        print("\n📋 查询方法:")
        print("1. 向量搜索 (推荐)")
        print("2. Cypher查询")
        print("3. 退出")
        
        while True:
            print("\n" + "=" * 60)
            method_choice = input("选择查询方法 (1-3): ").strip()
            
            if method_choice == "3":
                print("👋 再见！")
                break
            
            if method_choice not in ["1", "2"]:
                print("❌ 无效选择")
                continue
            
            method = "vector" if method_choice == "1" else "cypher"
            
            # 获取问题
            question = input("\n请输入你的问题: ").strip()
            if not question:
                print("❌ 问题不能为空")
                continue
            
            # 执行查询
            print(f"\n🔍 正在查询...")
            try:
                answer = self.query(question, method)
                print(f"\n🤖 回答:")
                print("-" * 40)
                print(textwrap.fill(answer, 80))
            except Exception as e:
                print(f"❌ 查询失败: {e}")
            
            # 询问是否继续
            continue_choice = input("\n是否继续查询? (y/n): ").strip().lower()
            if continue_choice != 'y':
                break

def main():
    """主函数"""
    query_system = Neo4jDirectQuery()
    query_system.interactive_query()

if __name__ == "__main__":
    main()


