#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彻底清理PR_Chunk节点
"""

import os
from neo4j import GraphDatabase

# 读取环境变量
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

uri = os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
username = os.getenv('NEO4J_USERNAME', 'neo4j')
password = os.getenv('NEO4J_PASSWORD', '')
database = os.getenv('NEO4J_DATABASE', 'neo4j')


def clean_pr_chunk_nodes():
    """彻底清理PR_Chunk节点"""
    print("=" * 70)
    print("🧹 彻底清理PR_Chunk节点")
    print("=" * 70)
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session(database=database) as session:
            # 检查PR_Chunk节点
            result = session.run("MATCH (p:PR_Chunk) RETURN count(p) as count")
            count = result.single()['count']
            print(f"\n找到 {count} 个PR_Chunk节点")
            
            if count == 0:
                print("✅ 没有PR_Chunk节点需要清理")
                return
            
            # 检查是否有关系
            result = session.run("""
                MATCH (p:PR_Chunk)-[r]->()
                RETURN count(r) as relation_count
            """)
            relation_count = result.single()['relation_count']
            
            if relation_count > 0:
                print(f"⚠️ 发现 {relation_count} 个关系，将一并删除")
            
            # 删除所有PR_Chunk节点及其关系
            result = session.run("""
                MATCH (p:PR_Chunk)
                DETACH DELETE p
                RETURN count(p) as deleted_count
            """)
            
            deleted = result.single()['deleted_count']
            print(f"✅ 删除了 {deleted} 个PR_Chunk节点")
            
            # 验证
            result = session.run("MATCH (p:PR_Chunk) RETURN count(p) as count")
            remaining = result.single()['count']
            
            if remaining == 0:
                print("✅ PR_Chunk节点已完全清理")
            else:
                print(f"⚠️ 仍有 {remaining} 个PR_Chunk节点")
        
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()


if __name__ == "__main__":
    clean_pr_chunk_nodes()


