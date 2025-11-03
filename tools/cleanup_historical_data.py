#!/usr/bin/env python3
"""
清理Neo4j中的历史数据（拿破仑、滑铁卢、Talleyrand相关）
"""

from dotenv import load_dotenv
import os
from langchain_community.graphs import Neo4jGraph
import warnings
warnings.filterwarnings("ignore")

# Load environment variables
load_dotenv('.env', override=True)
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE') or 'neo4j'

print("Connecting to Neo4j...")
kg = Neo4jGraph(
    url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD, database=NEO4J_DATABASE
)

def cleanup_historical_data():
    """清理历史数据"""
    print("🧹 开始清理历史数据...")
    
    # 删除历史相关的节点和关系
    cleanup_queries = [
        # 删除Person节点及其关系
        "MATCH (p:Person) DETACH DELETE p",
        
        # 删除Event节点及其关系
        "MATCH (e:Event) DETACH DELETE e",
        
        # 删除General_info节点及其关系
        "MATCH (g:General_info) DETACH DELETE g",
        
        # 删除Career节点及其关系
        "MATCH (c:Career) DETACH DELETE c",
        
        # 删除Death节点及其关系
        "MATCH (d:Death) DETACH DELETE d",
        
        # 删除历史相关的Chunk节点
        "MATCH (nc:Napoleon_Chunk) DETACH DELETE nc",
        "MATCH (tc:Talleyrand_Chunk) DETACH DELETE tc", 
        "MATCH (wc:Waterloo_Chunk) DETACH DELETE wc",
        
        # 删除TextChunk节点
        "MATCH (tc:TextChunk) DETACH DELETE tc"
    ]
    
    for query in cleanup_queries:
        try:
            result = kg.query(query)
            print(f"✅ 执行清理查询: {query[:50]}...")
        except Exception as e:
            print(f"❌ 清理查询失败: {e}")
    
    print("✅ 历史数据清理完成")

def check_remaining_data():
    """检查剩余数据"""
    print("\n📊 检查剩余数据...")
    
    # 检查节点类型
    node_types_query = "CALL db.labels() YIELD label RETURN label"
    node_types = kg.query(node_types_query)
    print("剩余节点类型:", [item['label'] for item in node_types])
    
    # 检查关系类型
    rel_types_query = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
    rel_types = kg.query(rel_types_query)
    print("剩余关系类型:", [item['relationshipType'] for item in rel_types])
    
    # 检查PR_Chunk节点数量
    pr_chunk_count = kg.query("MATCH (pc:PR_Chunk) RETURN count(pc) as count")
    print(f"PR_Chunk节点数量: {pr_chunk_count[0]['count']}")

def main():
    """主函数"""
    print("🚀 开始清理Neo4j历史数据")
    print("="*60)
    
    try:
        # 清理历史数据
        cleanup_historical_data()
        
        # 检查剩余数据
        check_remaining_data()
        
        print("\n🎉 历史数据清理完成！")
        print("现在Neo4j中只保留公关传播相关的数据")
        
    except Exception as e:
        print(f"❌ 清理过程中出现错误: {e}")

if __name__ == "__main__":
    main()


