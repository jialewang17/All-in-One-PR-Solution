#!/usr/bin/env python3
"""
创建 Section 节点的向量索引并生成嵌入
用于解决向量索引不可用的问题
"""

import os
import sys
from pathlib import Path

# 添加路径
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))
sys.path.append('core')

from dotenv import load_dotenv
load_dotenv('.env', override=True)

from neo4j import GraphDatabase
from langchain_openai import OpenAIEmbeddings
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


def create_vector_index(driver):
    """创建向量索引"""
    with driver.session(database=NEO4J_DATABASE) as session:
        create_index_query = f"""
        CREATE VECTOR INDEX {VECTOR_INDEX_NAME} IF NOT EXISTS
        FOR (s:{VECTOR_NODE_LABEL})
        ON s.{VECTOR_EMBEDDING_PROPERTY}
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: 1536,
                `vector.similarity_function`: 'cosine'
            }}
        }}
        """
        try:
            session.run(create_index_query)
            print(f"✅ 向量索引 '{VECTOR_INDEX_NAME}' 创建成功")
            return True
        except Exception as e:
            print(f"⚠️ 向量索引创建失败: {e}")
            check_query = f"SHOW INDEXES WHERE name = '{VECTOR_INDEX_NAME}'"
            result = session.run(check_query)
            if list(result):
                print(f"✅ 向量索引 '{VECTOR_INDEX_NAME}' 已存在")
                return True
            return False


def generate_embeddings(driver, batch_size=100):
    """为 Section 节点生成嵌入"""
    embeddings = OpenAIEmbeddings()
    
    with driver.session(database=NEO4J_DATABASE) as session:
        query = f"""
        MATCH (s:{VECTOR_NODE_LABEL})
        WHERE s.{VECTOR_EMBEDDING_PROPERTY} IS NULL
          AND s.{VECTOR_SOURCE_PROPERTY} IS NOT NULL
        RETURN s.id AS id, s.{VECTOR_SOURCE_PROPERTY} AS text
        LIMIT 1000
        """
        result = session.run(query)
        sections = list(result)
        
        if not sections:
            print("✅ 所有 Section 节点都已包含嵌入向量")
            return
        
        print(f"📊 找到 {len(sections)} 个需要生成嵌入的 Section 节点")
        
        for i in range(0, len(sections), batch_size):
            batch = sections[i:i+batch_size]
            texts = [item['text'] for item in batch]
            ids = [item['id'] for item in batch]
            
            try:
                embedding_vectors = embeddings.embed_documents(texts)
                
                for section_id, embedding in zip(ids, embedding_vectors):
                    update_query = f"""
                    MATCH (s:{VECTOR_NODE_LABEL} {{id: $id}})
                    SET s.{VECTOR_EMBEDDING_PROPERTY} = $embedding
                    """
                    session.run(update_query, id=section_id, embedding=embedding)
                
                print(f"✅ 已处理 {min(i+batch_size, len(sections))}/{len(sections)} 个节点")
            except Exception as e:
                print(f"⚠️ 批量处理失败: {e}")
                continue


def main():
    """主函数"""
    print("=" * 60)
    print("创建 Section 向量索引并生成嵌入")
    print("=" * 60)
    
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
    )
    
    try:
        print("\n📝 步骤 1: 创建向量索引...")
        if not create_vector_index(driver):
            print("❌ 向量索引创建失败，请检查 Neo4j 配置")
            return
        
        print("\n📝 步骤 2: 为 Section 节点生成嵌入...")
        generate_embeddings(driver)
        
        print("\n" + "=" * 60)
        print("✅ 向量索引和嵌入生成完成！")
        print("=" * 60)
        print("\n💡 提示：现在可以重新运行 RAG 系统，向量搜索应该可用了")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()


if __name__ == "__main__":
    main()


