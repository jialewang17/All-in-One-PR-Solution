#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为现有Section节点提取SPO关系
"""

import os
import sys
from pathlib import Path
from neo4j import GraphDatabase

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 读取环境变量
try:
    from dotenv import load_dotenv
    load_dotenv('.env', override=True)
except ImportError:
    # 手动读取.env文件
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


def extract_spo_relations():
    """为Section节点提取SPO关系"""
    print("=" * 70)
    print("🔍 提取SPO关系")
    print("=" * 70)
    
    # 检查SPO提取器
    try:
        from core.processing.extractors.spo_extractor import SPOTripleExtractor
        print("\n✅ SPO提取器可用")
    except ImportError as e:
        print(f"\n❌ SPO提取器不可用: {e}")
        return
    
    # 初始化SPO提取器
    try:
        # 优先使用 OpenAI：
        # - 仅从环境变量（或 .env）中读取 OPENAI_API_KEY
        # - 不在代码中硬编码任何真实 API Key
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            spo_extractor = SPOTripleExtractor(
                model_name="gpt-3.5-turbo",
                temperature=0.0,
                use_openrouter=False,
                api_key=api_key,
            )
            print("✅ SPO提取器初始化成功（使用 OpenAI，来自环境变量 OPENAI_API_KEY）")
        else:
            # 未设置 OPENAI_API_KEY 时，回退到 OpenRouter
            spo_extractor = SPOTripleExtractor(
                temperature=0.0,
                use_openrouter=True
            )
            print("✅ SPO提取器初始化成功（使用OpenRouter）")
    except Exception as e:
        print(f"❌ SPO提取器初始化失败: {e}")
        print("  请检查API key配置（OPENROUTER_API_KEY 或 OPENAI_API_KEY）")
        return
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session(database=database) as session:
            # 获取所有Section节点（增加数量，选择有较长文本的）
            result = session.run("""
                MATCH (s:Section)
                WHERE s.text IS NOT NULL AND s.text <> '' AND size(s.text) > 50
                RETURN s.id as section_id, s.text as text, s.level2 as level2
                ORDER BY size(s.text) DESC
                LIMIT 30
            """)
            
            sections = list(result)
            print(f"\n📊 找到 {len(sections)} 个有文本内容的Section（显示前10个）")
            
            if len(sections) == 0:
                print("⚠️ 没有找到可提取的Section")
                return
            
            # 为每个Section提取SPO
            total_triples = 0
            total_relations = 0
            
            for i, record in enumerate(sections, 1):
                section_id = record['section_id']
                text = record['text']
                level2 = record.get('level2', '')
                
                print(f"\n  [{i}/{len(sections)}] 处理Section: {section_id}")
                
                try:
                    # 提取SPO三元组（增加chunk_size以处理更长文本）
                    result_data = spo_extractor.extract_triples_from_text(
                        text,
                        chunk_size=500,  # 增加chunk大小以包含更多上下文
                        overlap=50,
                        verbose=False
                    )
                    
                    triples = result_data.get('triples', [])
                    print(f"    ✅ 提取了 {len(triples)} 个三元组")
                    
                    # 如果提取到三元组，显示示例
                    if len(triples) > 0:
                        print(f"      示例: {triples[0].get('subject', '')} -[{triples[0].get('predicate', '')}]-> {triples[0].get('object', '')}")
                    
                    if len(triples) == 0:
                        continue
                    
                    total_triples += len(triples)
                    
                    # 创建SPO关系
                    for triple in triples:
                        subject = triple.get('subject', '').strip()
                        predicate = triple.get('predicate', '').strip()
                        obj = triple.get('object', '').strip()
                        
                        if not all([subject, predicate, obj]):
                            continue
                        
                        # 尝试将subject映射到Company（使用更宽松的匹配）
                        subject_match = session.run("""
                            MATCH (c:Company)
                            WHERE toLower(c.name) = toLower($subject)
                               OR toLower(c.name) CONTAINS toLower($subject)
                               OR toLower($subject) CONTAINS toLower(c.name)
                            RETURN c.name as name, 'Company' as label
                            ORDER BY 
                                CASE WHEN toLower(c.name) = toLower($subject) THEN 1 
                                     WHEN toLower(c.name) CONTAINS toLower($subject) THEN 2
                                     ELSE 3 END
                            LIMIT 1
                        """, subject=subject).single()
                        
                        if not subject_match:
                            # 尝试Brand（使用更宽松的匹配）
                            subject_match = session.run("""
                                MATCH (b:Brand)
                                WHERE toLower(b.name) = toLower($subject)
                                   OR toLower(b.name) CONTAINS toLower($subject)
                                   OR toLower($subject) CONTAINS toLower(b.name)
                                RETURN b.name as name, 'Brand' as label
                                ORDER BY 
                                    CASE WHEN toLower(b.name) = toLower($subject) THEN 1 
                                         WHEN toLower(b.name) CONTAINS toLower($subject) THEN 2
                                         ELSE 3 END
                                LIMIT 1
                            """, subject=subject).single()
                        
                        # 如果仍然未匹配，自动创建节点（如果看起来像组织实体）
                        if not subject_match:
                            # 判断是否为组织实体
                            org_keywords = ['公司', '集团', '品牌', '企业', '科技', '有限公司', '汽车', '互联']
                            is_org = any(kw in subject for kw in org_keywords) or len(subject) <= 15
                            
                            if is_org:
                                # 判断类型（尽量使用分类器）
                                try:
                                    from core.processing.extractors.org_classifier import OrganizationClassifier
                                    classifier = OrganizationClassifier()
                                    classification = classifier.classify_entity(subject)
                                    entity_type = classification['type']
                                    
                                    if entity_type == 'company':
                                        session.run("""
                                            MERGE (c:Company {name: $subject})
                                            ON CREATE SET 
                                                c.type = 'company',
                                                c.created_at = datetime()
                                        """, subject=subject)
                                        subject_match = {'name': subject, 'label': 'Company'}
                                    elif entity_type == 'brand':
                                        session.run("""
                                            MERGE (b:Brand {name: $subject})
                                            ON CREATE SET 
                                                b.type = 'brand',
                                                b.level = 'group',
                                                b.created_at = datetime()
                                        """, subject=subject)
                                        subject_match = {'name': subject, 'label': 'Brand'}
                                    else:
                                        session.run("""
                                            MERGE (c:Company {name: $subject})
                                            ON CREATE SET 
                                                c.type = 'company',
                                                c.created_at = datetime()
                                        """, subject=subject)
                                        subject_match = {'name': subject, 'label': 'Company'}
                                except Exception:
                                    session.run("""
                                        MERGE (c:Company {name: $subject})
                                        ON CREATE SET 
                                            c.type = 'company',
                                            c.created_at = datetime()
                                    """, subject=subject)
                                    subject_match = {'name': subject, 'label': 'Company'}
                            else:
                                continue
                        
                        subject_name = subject_match['name']
                        subject_label = subject_match['label']
                        
                        # 创建或匹配object节点（Campaign或Concept）
                        campaign_keywords = ['campaign', '活动', 'event', 'promotion', '促销', '大促']
                        if any(kw in obj.lower() for kw in campaign_keywords):
                            object_label = 'Campaign'
                        else:
                            object_label = 'Concept'
                        
                        # 创建关系
                        session.run(f"""
                            MATCH (sub:{subject_label} {{name: $subject}})
                            MERGE (obj:{object_label} {{name: $obj}})
                            ON CREATE SET obj.created_at = datetime()
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
                    
                except Exception as e:
                    print(f"    ⚠️ 处理失败: {e}")
                    continue
            
            print(f"\n" + "=" * 70)
            print(f"📊 提取完成:")
            print(f"  处理Section: {len(sections)} 个")
            print(f"  提取三元组: {total_triples} 个")
            print(f"  创建关系: {total_relations} 个")
            
            # 验证创建的关系
            result = session.run("MATCH ()-[r:SPO_REL]->() RETURN count(r) as count")
            final_count = result.single()['count']
            print(f"  图谱中SPO_REL关系总数: {final_count} 个")
            
    except Exception as e:
        print(f"\n❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()


if __name__ == "__main__":
    extract_spo_relations()


