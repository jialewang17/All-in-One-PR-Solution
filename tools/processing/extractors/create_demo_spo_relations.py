#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建演示SPO关系（不依赖API，基于规则匹配）
展示SPO关系的应用场景
"""

import os
import re
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

# SPO模式匹配规则
SPO_PATTERNS = [
    (r'([\w\u4e00-\u9fff]+公司|[\w\u4e00-\u9fff]+集团|[\w\u4e00-\u9fff]+品牌)\s*(发起|推出|举办|开展|启动)\s*([\w\u4e00-\u9fff]+活动|[\w\u4e00-\u9fff]+促销|[\w\u4e00-\u9fff]+营销)', 
     'launched', 'Campaign'),
    (r'([\w\u4e00-\u9fff]+公司|[\w\u4e00-\u9fff]+品牌)\s*(通过|使用|利用|借助)\s*([\w\u4e00-\u9fff]+平台|[\w\u4e00-\u9fff]+渠道|[\w\u4e00-\u9fff]+媒体)', 
     'uses_channel', 'Concept'),
    (r'([\w\u4e00-\u9fff]+公司|[\w\u4e00-\u9fff]+品牌)\s*(与|和|跟)\s*([\w\u4e00-\u9fff]+公司|[\w\u4e00-\u9fff]+品牌)\s*(合作|联合|联手)', 
     'collaborates_with', 'Company'),
    (r'([\w\u4e00-\u9fff]+公司|[\w\u4e00-\u9fff]+品牌)\s*(聚焦|专注|重点|主打)\s*([\w\u4e00-\u9fff]+策略|[\w\u4e00-\u9fff]+方案|[\w\u4e00-\u9fff]+概念)', 
     'focuses_on', 'Concept'),
]


def extract_spo_from_text(text, section_id, level2):
    """从文本中提取SPO三元组（基于规则）"""
    triples = []
    
    for pattern, predicate, object_type in SPO_PATTERNS:
        matches = re.finditer(pattern, text)
        for match in matches:
            subject = match.group(1)
            obj = match.group(3)
            
            subject = re.sub(r'(公司|集团|品牌)$', '', subject).strip()
            obj = obj.strip()
            
            if len(subject) > 1 and len(obj) > 1:
                triples.append({
                    'subject': subject,
                    'predicate': predicate,
                    'object': obj,
                    'object_type': object_type
                })
    
    return triples


def create_demo_spo_relations():
    """创建演示SPO关系"""
    print("=" * 70)
    print("🔍 创建演示SPO关系（基于规则匹配）")
    print("=" * 70)
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session(database=database) as session:
            result = session.run("""
                MATCH (s:Section)
                WHERE s.text IS NOT NULL AND s.text <> '' AND size(s.text) > 50
                RETURN s.id as section_id, s.text as text, s.level2 as level2
                ORDER BY s.id
                LIMIT 20
            """)
            
            sections = list(result)
            print(f"\n📊 处理 {len(sections)} 个Section节点")
            
            total_triples = 0
            total_relations = 0
            
            for i, record in enumerate(sections, 1):
                section_id = record['section_id']
                text = record['text']
                level2 = record.get('level2', '')
                
                triples = extract_spo_from_text(text, section_id, level2)
                
                if len(triples) == 0:
                    continue
                
                total_triples += len(triples)
                print(f"  [{i}] Section {section_id}: 提取 {len(triples)} 个三元组")
                
                for triple in triples:
                    subject = triple['subject']
                    predicate = triple['predicate']
                    obj = triple['object']
                    object_type = triple['object_type']
                    
                    try:
                        subject_match = session.run("""
                            MATCH (c:Company)
                            WHERE toLower(c.name) CONTAINS toLower($subject)
                               OR toLower($subject) CONTAINS toLower(c.name)
                            RETURN c.name as name, 'Company' as label
                            LIMIT 1
                        """, subject=subject).single()
                        
                        if not subject_match:
                            subject_match = session.run("""
                                MATCH (b:Brand)
                                WHERE toLower(b.name) CONTAINS toLower($subject)
                                   OR toLower($subject) CONTAINS toLower(b.name)
                                RETURN b.name as name, 'Brand' as label
                                LIMIT 1
                            """, subject=subject).single()
                        
                        if not subject_match:
                            continue
                        
                        subject_name = subject_match['name']
                        subject_label = subject_match['label']
                        
                        session.run(f"""
                            MERGE (obj:{object_type} {{name: $obj}})
                            ON CREATE SET obj.created_at = datetime()
                        """, obj=obj)
                        
                        session.run(f"""
                            MATCH (sub:{subject_label} {{name: $subject}})
                            MATCH (obj:{object_type} {{name: $obj}})
                            MERGE (sub)-[r:SPO_REL]->(obj)
                            ON CREATE SET 
                                r.predicate = $predicate,
                                r.section_id = $section_id,
                                r.level2_code = $level2,
                                r.created_at = datetime()
                            ON MATCH SET
                                r.predicate = $predicate,
                                r.section_id = $section_id,
                                r.level2_code = $level2
                        """,
                            subject=subject_name,
                            obj=obj,
                            predicate=predicate,
                            section_id=section_id,
                            level2=level2
                        )
                        
                        total_relations += 1
                        
                    except Exception:
                        continue
            
            print(f"\n" + "=" * 70)
            print(f"📊 创建完成:")
            print(f"  处理Section: {len(sections)} 个")
            print(f"  提取三元组: {total_triples} 个")
            print(f"  创建SPO_REL关系: {total_relations} 个")
            
            result = session.run("""
                MATCH ()-[r:SPO_REL]->()
                RETURN count(r) as count,
                       collect(DISTINCT r.predicate)[0..10] as predicates
            """)
            record = result.single()
            final_count = record['count']
            predicates = record['predicates']
            
            print(f"\n✅ 图谱中SPO_REL关系总数: {final_count} 个")
            if predicates:
                print(f"   示例谓词: {', '.join(predicates)}")
            
            result = session.run("""
                MATCH (a)-[r:SPO_REL]->(b)
                RETURN labels(a)[0] as from_label,
                       a.name as from_name,
                       r.predicate as predicate,
                       labels(b)[0] as to_label,
                       b.name as to_name
                LIMIT 5
            """)
            
            print(f"\n📋 示例SPO关系:")
            for record in result:
                print(f"  {record['from_label']}({record['from_name']}) -[{record['predicate']}]-> {record['to_label']}({record['to_name']})")
            
    except Exception as e:
        print(f"\n❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()


if __name__ == "__main__":
    create_demo_spo_relations()


