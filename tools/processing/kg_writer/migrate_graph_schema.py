#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图谱Schema迁移脚本
统一标签命名、清理重复节点、合并节点、更新关系
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


def migrate_graph_schema():
    """迁移图谱Schema"""
    print("=" * 70)
    print("🔄 图谱Schema迁移")
    print("=" * 70)
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session(database=database) as session:
            # 步骤1: 删除Strategie节点
            print("\n1️⃣ 删除Strategie节点...")
            result = session.run("""
                MATCH (s:Strategie)
                DETACH DELETE s
                RETURN count(s) as deleted_count
            """)
            deleted = result.single()['deleted_count']
            print(f"  ✅ 删除了 {deleted} 个Strategie节点")
            
            # 步骤2: 合并PR_Chunk到Section
            print("\n2️⃣ 合并PR_Chunk到Section节点...")
            
            # 先检查PR_Chunk节点数量
            result = session.run("MATCH (p:PR_Chunk) RETURN count(p) as count")
            pr_chunk_count = result.single()['count']
            print(f"  找到 {pr_chunk_count} 个PR_Chunk节点")
            
            if pr_chunk_count > 0:
                # 策略1：通过文本内容匹配Section（精确匹配或相似度）
                # 转移CONTAINS_ENTITY关系到MENTIONS_COMPANY
                result = session.run("""
                    MATCH (p:PR_Chunk)-[r1:CONTAINS_ENTITY]->(e)
                    OPTIONAL MATCH (s:Section)
                    WHERE p.text = s.text 
                       OR (p.text IS NOT NULL AND s.text IS NOT NULL 
                           AND substring(p.text, 0, 100) = substring(s.text, 0, 100))
                    WITH p, collect(DISTINCT s)[0] as matched_section, collect(e) as entities
                    WHERE matched_section IS NOT NULL
                    UNWIND entities as entity
                    MERGE (matched_section)-[:MENTIONS_COMPANY]->(entity)
                    WITH count(DISTINCT p) as chunks_processed
                    RETURN chunks_processed
                """)
                
                record = result.single()
                processed = record['chunks_processed'] if record else 0
                print(f"  ✅ 处理了 {processed} 个PR_Chunk的关系转移")
                
                # 策略2：对于无法匹配的PR_Chunk，直接创建Section节点
                result = session.run("""
                    MATCH (p:PR_Chunk)
                    WHERE NOT EXISTS {
                        MATCH (s:Section)
                        WHERE p.text = s.text 
                           OR (p.text IS NOT NULL AND s.text IS NOT NULL 
                               AND substring(p.text, 0, 100) = substring(s.text, 0, 100))
                    }
                    WITH p, coalesce(p.chunk_id, toString(id(p))) as chunk_id
                    MERGE (s:Section {id: 'merged_chunk_' + chunk_id})
                    SET s.text = coalesce(p.text, ''),
                        s.title = coalesce(p.title, ''),
                        s.source = coalesce(p.source, ''),
                        s.level1 = coalesce(p.level1, 'other'),
                        s.level2 = coalesce(p.level2, 'other.general'),
                        s.created_at = coalesce(p.created_at, datetime())
                    WITH p, s
                    MATCH (p)-[:CONTAINS_ENTITY]->(e)
                    MERGE (s)-[:MENTIONS_COMPANY]->(e)
                    WITH count(DISTINCT p) as chunks_created
                    RETURN chunks_created
                """)
                
                record = result.single()
                created = record['chunks_created'] if record else 0
                if created > 0:
                    print(f"  ✅ 为 {created} 个无法匹配的PR_Chunk创建了Section节点")
                
                # 删除所有PR_Chunk节点（关系已转移）
                result = session.run("""
                    MATCH (p:PR_Chunk)
                    DETACH DELETE p
                    RETURN count(p) as deleted
                """)
                deleted = result.single()['deleted']
                print(f"  ✅ 删除了 {deleted} 个PR_Chunk节点")
            
            # 步骤3: 更新SPO关系（从:REL改为:SPO_REL）
            print("\n3️⃣ 更新SPO关系为:SPO_REL...")
            
            # 检查是否有:REL关系
            result = session.run("MATCH ()-[r:REL]->() RETURN count(r) as count")
            rel_count = result.single()['count']
            print(f"  找到 {rel_count} 个:REL关系")
            
            if rel_count > 0:
                result = session.run("""
                    MATCH (a)-[r:REL]->(b)
                    WHERE r.predicate IS NOT NULL
                    WITH a, b, r, 
                         r.predicate as predicate, 
                         r.section_id as section_id, 
                         r.level2_code as level2_code,
                         r.created_at as created_at
                    MERGE (a)-[new_rel:SPO_REL]->(b)
                    SET new_rel.predicate = predicate,
                        new_rel.section_id = section_id,
                        new_rel.level2_code = level2_code,
                        new_rel.created_at = COALESCE(created_at, datetime())
                    DELETE r
                    RETURN count(new_rel) as updated_count
                """)
                
                updated = result.single()['updated_count']
                print(f"  ✅ 更新了 {updated} 个SPO关系（:REL → :SPO_REL）")
                
                # 删除剩余的:REL关系（没有predicate的）
                result = session.run("""
                    MATCH ()-[r:REL]->()
                    DELETE r
                    RETURN count(r) as deleted_count
                """)
                deleted = result.single()['deleted_count']
                if deleted > 0:
                    print(f"  ✅ 删除了 {deleted} 个无predicate的:REL关系")
            else:
                print("  ℹ️ 没有找到:REL关系，跳过")
            
            # 步骤4: 清理重复属性
            print("\n4️⃣ 清理重复属性...")
            
            # 删除brand_mentions和brand_mentioned属性
            result = session.run("""
                MATCH (n)
                WHERE n.brand_mentions IS NOT NULL OR n.brand_mentioned IS NOT NULL
                REMOVE n.brand_mentions, n.brand_mentioned
                RETURN count(n) as cleaned_count
            """)
            
            cleaned = result.single()['cleaned_count']
            print(f"  ✅ 清理了 {cleaned} 个节点的重复属性")
            
            # 步骤5: 统一属性命名
            print("\n5️⃣ 统一属性命名...")
            
            # 确保所有节点都有正确的核心属性
            # Brand节点：保留name, type, level, industry
            result = session.run("""
                MATCH (b:Brand)
                WHERE b.name IS NULL OR b.type IS NULL
                SET b.type = COALESCE(b.type, 'brand'),
                    b.level = COALESCE(b.level, 'group')
                RETURN count(b) as updated_brands
            """)
            updated_brands = result.single()['updated_brands']
            print(f"  ✅ 更新了 {updated_brands} 个Brand节点的属性")
            
            # Company节点：保留name, type, industry
            result = session.run("""
                MATCH (c:Company)
                WHERE c.type IS NULL
                SET c.type = 'company'
                RETURN count(c) as updated_companies
            """)
            updated_companies = result.single()['updated_companies']
            print(f"  ✅ 更新了 {updated_companies} 个Company节点的属性")
            
            # CategoryL1和CategoryL2：确保有code和label
            result = session.run("""
                MATCH (c:CategoryL1)
                WHERE c.code IS NULL OR c.label IS NULL
                RETURN count(c) as missing_attrs
            """)
            missing_l1 = result.single()['missing_attrs']
            if missing_l1 > 0:
                print(f"  ⚠️ {missing_l1} 个CategoryL1节点缺少code或label")
            
            result = session.run("""
                MATCH (c:CategoryL2)
                WHERE c.code IS NULL OR c.label IS NULL
                RETURN count(c) as missing_attrs
            """)
            missing_l2 = result.single()['missing_attrs']
            if missing_l2 > 0:
                print(f"  ⚠️ {missing_l2} 个CategoryL2节点缺少code或label")
            
            # 步骤6: 确保关系存在
            print("\n6️⃣ 验证关键关系...")
            
            # 检查BELONGS_TO_BRAND关系
            result = session.run("MATCH ()-[r:BELONGS_TO_BRAND]->() RETURN count(r) as count")
            belongs_to_brand = result.single()['count']
            print(f"  BELONGS_TO_BRAND关系: {belongs_to_brand} 个")
            
            # 检查BELONGS_TO_TYPE关系
            result = session.run("MATCH ()-[r:BELONGS_TO_TYPE]->() RETURN count(r) as count")
            belongs_to_type = result.single()['count']
            print(f"  BELONGS_TO_TYPE关系: {belongs_to_type} 个")
            
            # 检查SPO_REL关系
            result = session.run("MATCH ()-[r:SPO_REL]->() RETURN count(r) as count")
            spo_rel = result.single()['count']
            print(f"  SPO_REL关系: {spo_rel} 个")
            
            # 最终统计
            print("\n" + "=" * 70)
            print("📊 最终统计")
            print("=" * 70)
            
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)
            
            print("\n节点统计:")
            for record in result:
                print(f"  {record['label']}: {record['count']} 个")
            
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
            """)
            
            print("\n关系统计:")
            for record in result:
                print(f"  {record['rel_type']}: {record['count']} 个")
        
        print("\n✅ Schema迁移完成！")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()


if __name__ == "__main__":
    migrate_graph_schema()


