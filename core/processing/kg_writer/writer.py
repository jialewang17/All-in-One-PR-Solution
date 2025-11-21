#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的知识图谱写入器
实现CategoryL1/CategoryL2/Section/Company节点结构 + SPO三元组集成
"""

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

try:
    from neo4j import GraphDatabase
except ImportError:
    print("❌ 需要安装neo4j: pip install neo4j")
    sys.exit(1)

try:
    from core.processing.extractors.spo_extractor import SPOTripleExtractor
    SPO_AVAILABLE = True
except ImportError:
    SPO_AVAILABLE = False
    print("⚠️ SPO提取器不可用")

try:
    from core.processing.extractors.entity_extractor import EntityRelationshipExtractor
    ENTITY_EXTRACTOR_AVAILABLE = True
except ImportError:
    ENTITY_EXTRACTOR_AVAILABLE = False
    print("⚠️ 实体提取器不可用")

try:
    from core.processing.extractors.org_classifier import OrganizationClassifier
    ORG_CLASSIFIER_AVAILABLE = True
except ImportError:
    ORG_CLASSIFIER_AVAILABLE = False
    print("⚠️ 组织分类器不可用")

from core.common.pr_category_schema import (
    CATEGORY_SCHEMA,
    get_category_l2_list,
    classify_section,
    get_category_by_code
)
from .json_loader import extract_sections_from_json
from .entity_linker import EntityLinker

# 可选：公司/品牌词典用于保守放行（优先信任）
try:
    from core.processing.company_dictionary import CompanyDictionary
    COMPANY_DICT_AVAILABLE = True
except Exception:
    COMPANY_DICT_AVAILABLE = False
    CompanyDictionary = None


class EnhancedKGWriter:
    """增强的知识图谱写入器"""
    
    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        use_spo: bool = True,
        use_entity_extractor: bool = True
    ):
        """
        初始化增强KG写入器
        
        Args:
            uri: Neo4j URI
            username: 用户名
            password: 密码
            database: 数据库名
            use_spo: 是否使用SPO提取器
            use_entity_extractor: 是否使用实体提取器
        """
        # 加载环境变量
        try:
            from dotenv import load_dotenv
            load_dotenv('.env', override=True)
        except:
            # 手动读取.env文件
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
        
        self.uri = uri or os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
        self.username = username or os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD', '')
        self.database = database or os.getenv('NEO4J_DATABASE', 'neo4j')
        
        # 打印连接信息（隐藏密码）
        print(f"\n🔗 连接信息:")
        print(f"   URI: {self.uri}")
        print(f"   用户名: {self.username}")
        print(f"   数据库: {self.database}")
        
        # 连接Neo4j
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password),
            max_connection_lifetime=30 * 60,
            max_connection_pool_size=50,
            connection_acquisition_timeout=2 * 60,
            keep_alive=True,
        )
        
        # 测试连接
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                result.single()
            print("✅ Neo4j连接成功")
        except Exception as e:
            print(f"❌ Neo4j连接失败: {e}")
            raise
        
        # 初始化提取器
        self.use_spo = use_spo and SPO_AVAILABLE
        self.use_entity_extractor = use_entity_extractor and ENTITY_EXTRACTOR_AVAILABLE
        
        # 初始化组织分类器
        if ORG_CLASSIFIER_AVAILABLE:
            try:
                self.org_classifier = OrganizationClassifier()
                print("✅ 组织分类器已初始化")
            except Exception as e:
                print(f"⚠️ 组织分类器初始化失败: {e}")
                self.org_classifier = None
        else:
            self.org_classifier = None
        
        if self.use_spo:
            try:
                self.spo_extractor = SPOTripleExtractor(
                    temperature=0.0,
                    use_openrouter=False
                )
                print("✅ SPO提取器已初始化")
            except Exception as e:
                print(f"⚠️ SPO提取器初始化失败: {e}")
                self.use_spo = False
        
        if self.use_entity_extractor:
            try:
                self.entity_extractor = EntityRelationshipExtractor()
                print("✅ 实体提取器已初始化")
            except Exception as e:
                print(f"⚠️ 实体提取器初始化失败: {e}")
                self.use_entity_extractor = False
        
        # 统计信息
        self.stats = {
            'category_l1_created': 0,
            'category_l2_created': 0,
            'sections_created': 0,
            'companies_created': 0,
            'brands_created': 0,
            'brands_skipped': 0,
            'company_types_created': 0,
            'spo_relations_created': 0,
            'involved_in_category_relations': 0,
            'belongs_to_brand_relations': 0,
            'belongs_to_type_relations': 0
        }

        # 初始化分类器与公司/品牌词典
        self.org_classifier = OrganizationClassifier() if ORG_CLASSIFIER_AVAILABLE else None
        # 仅用于校验，不落盘：save_to_file=False 可避免运行时自动写 company_dictionary.json
        self.company_dict = CompanyDictionary(save_to_file=True) if COMPANY_DICT_AVAILABLE and CompanyDictionary else None
        self.entity_linker = EntityLinker(
            driver=self.driver,
            database=self.database,
            stats=self.stats,
            org_classifier=self.org_classifier,
            company_dict=self.company_dict,
        )

    def create_schema(self):
        """创建Neo4j Schema和分类节点"""
        print("\n🏗️ 创建增强图谱Schema...")
        print("-" * 70)
        
        schema_queries = [
            # CategoryL1节点约束
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:CategoryL1) REQUIRE c.code IS UNIQUE",
            # CategoryL2节点约束
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:CategoryL2) REQUIRE c.code IS UNIQUE",
            # Section节点约束
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Section) REQUIRE s.id IS UNIQUE",
            # Company节点约束
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
            # Brand节点约束
            "CREATE CONSTRAINT IF NOT EXISTS FOR (b:Brand) REQUIRE b.name IS UNIQUE",
            # CompanyType节点约束
            "CREATE CONSTRAINT IF NOT EXISTS FOR (ct:CompanyType) REQUIRE ct.code IS UNIQUE",
            # Campaign节点约束（用于SPO中的活动）
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Campaign) REQUIRE c.name IS UNIQUE",
            # Concept节点约束（用于SPO中的概念）
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE",
            
            # 索引
            "CREATE INDEX IF NOT EXISTS FOR (s:Section) ON (s.level1)",
            "CREATE INDEX IF NOT EXISTS FOR (s:Section) ON (s.level2)",
            "CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.name)",
        ]
        
        with self.driver.session(database=self.database) as session:
            for query in schema_queries:
                try:
                    session.run(query)
                except Exception as e:
                    print(f"  ⚠️ Schema创建警告: {str(e)[:100]}")
        
        print("✅ Schema创建完成")
        
        # 创建CategoryL1和CategoryL2节点
        self._create_category_nodes()
        
        # 创建CompanyType节点
        self._create_company_type_nodes()
    
    def _create_category_nodes(self):
        """创建所有CategoryL1和CategoryL2节点"""
        print("\n📋 创建分类节点...")
        
        # 检查是否已存在
        with self.driver.session(database=self.database) as session:
            result = session.run("MATCH (c:CategoryL1) RETURN count(c) as count")
            existing_l1 = result.single()['count']
            result = session.run("MATCH (c:CategoryL2) RETURN count(c) as count")
            existing_l2 = result.single()['count']
            
            if existing_l1 == len(CATEGORY_SCHEMA) and existing_l2 >= len(CATEGORY_SCHEMA) * 5:
                print(f"  ⚠️ 分类节点已存在（L1: {existing_l1}, L2: {existing_l2}），跳过创建")
                self.stats['category_l1_created'] = existing_l1
                self.stats['category_l2_created'] = existing_l2
                return
        
        with self.driver.session(database=self.database) as session:
            # 创建CategoryL1节点
            for l1_code, l1_data in CATEGORY_SCHEMA.items():
                try:
                    session.run("""
                        MERGE (c1:CategoryL1 {code: $code})
                        ON CREATE SET 
                            c1.label = $label,
                            c1.created_at = datetime()
                        ON MATCH SET
                            c1.label = $label
                    """, code=l1_code, label=l1_data['label'])
                    self.stats['category_l1_created'] += 1
                except Exception as e:
                    print(f"  ⚠️ 创建CategoryL1失败 {l1_code}: {e}")
            
            # 创建CategoryL2节点并连接到CategoryL1
            for l1_code, l1_data in CATEGORY_SCHEMA.items():
                for l2_subcode, l2_data in l1_data['sub_categories'].items():
                    l2_code = f"{l1_code}.{l2_subcode}"
                    
                    try:
                        # 创建CategoryL2节点
                        session.run("""
                            MERGE (c2:CategoryL2 {code: $code})
                            ON CREATE SET 
                                c2.label = $label,
                                c2.parent_code = $parent_code,
                                c2.keywords = $keywords,
                                c2.created_at = datetime()
                            ON MATCH SET
                                c2.label = $label,
                                c2.keywords = $keywords
                        """, 
                            code=l2_code,
                            label=l2_data['label'],
                            parent_code=l1_code,
                            keywords=l2_data['keywords']
                        )
                        
                        # 连接到CategoryL1
                        session.run("""
                            MATCH (c1:CategoryL1 {code: $parent_code})
                            MATCH (c2:CategoryL2 {code: $code})
                            MERGE (c1)-[:HAS_SUBCATEGORY]->(c2)
                        """, parent_code=l1_code, code=l2_code)
                        
                        self.stats['category_l2_created'] += 1
                    except Exception as e:
                        print(f"  ⚠️ 创建CategoryL2失败 {l2_code}: {e}")
        
        print(f"✅ 创建了 {self.stats['category_l1_created']} 个CategoryL1节点")
        print(f"✅ 创建了 {self.stats['category_l2_created']} 个CategoryL2节点")
    
    def _create_company_type_nodes(self):
        """创建所有CompanyType节点"""
        if not self.org_classifier:
            print("⚠️ 组织分类器不可用，跳过CompanyType节点创建")
            return
        
        print("\n📋 创建CompanyType节点...")
        
        company_types = self.org_classifier.get_company_type_nodes()
        
        with self.driver.session(database=self.database) as session:
            for ct in company_types:
                try:
                    session.run("""
                        MERGE (ct:CompanyType {code: $code})
                        ON CREATE SET
                            ct.label = $label,
                            ct.created_at = datetime()
                        ON MATCH SET
                            ct.label = $label
                    """, code=ct['code'], label=ct['label'])
                    self.stats['company_types_created'] += 1
                except Exception as e:
                    print(f"  ⚠️ 创建CompanyType失败 {ct['code']}: {e}")
        
        print(f"✅ 创建了 {self.stats['company_types_created']} 个CompanyType节点")

    def process_json_files(self, json_dir: str = "data/json"):
        """处理JSON文件并写入Neo4j"""
        print("\n📊 开始处理JSON文件...")
        print("=" * 70)
        
        json_path = Path(json_dir)
        if not json_path.exists():
            print(f"❌ JSON目录不存在: {json_dir}")
            return
        
        json_files = list(json_path.glob("*.json"))
        if not json_files:
            print("❌ 未找到JSON文件")
            return
        
        print(f"📁 找到 {len(json_files)} 个JSON文件")
        
        for json_file in json_files:
            print(f"\n📄 处理: {json_file.name}")
            try:
                self._process_single_json(json_file)
            except Exception as e:
                print(f"  ❌ 处理失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 创建Company与CategoryL2的汇总关系
        print("\n📊 创建Company-CategoryL2汇总关系...")
        self._create_company_category_summary()
        
        # 显示统计
        self._show_statistics()
    
    def _process_single_json(self, json_file: Path):
        """处理单个JSON文件"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取文档标题
        doc_title = data.get('document_title', json_file.stem)
        
        # 解析Section列表
        sections = extract_sections_from_json(data, json_file.stem, doc_title)
        
        print(f"  📝 提取到 {len(sections)} 个Section")
        
        # 处理每个Section（批量处理，增加错误处理）
        success_count = 0
        for i, section in enumerate(sections):
            if not isinstance(section, dict):
                print(f"  ⚠️ Section结构异常 index={i}, 类型={type(section).__name__}, 内容={str(section)[:80]}")
                continue
            try:
                # 创建Section节点
                section_id = section['id']
                self._create_section(section, doc_title)
                
                # 提取实体并连接
                if self.use_entity_extractor:
                    entities = self.entity_extractor.extract_entities_from_text(section.get('text', ''))
                    self.entity_linker.link(section_id, entities, section)
                
                # 提取SPO三元组（可选，如果失败不影响主流程）
                if self.use_spo:
                    try:
                        spo_triples = self._extract_spo_for_section(section)
                        self._create_spo_relations(spo_triples, section_id, section)
                    except Exception as e:
                        pass  # SPO提取失败不影响主流程
                
                success_count += 1
                
                # 每处理10个section打印一次进度
                if (i + 1) % 10 == 0:
                    print(f"    处理进度: {i + 1}/{len(sections)}")
                    
            except Exception as e:
                section_id = section.get('id') if isinstance(section, dict) else f"index_{i}"
                print(f"  ⚠️ Section处理失败 {section_id}: {e}")
                continue
        
        print(f"  ✅ 完成: {success_count}/{len(sections)} sections")
    
    def _extract_sections_from_json(self, data: Dict, doc_name: str, doc_title: str) -> List[Dict]:
        """
        从JSON中提取Section列表
        支持多种JSON结构格式
        """
        sections = []
        
        # 策略1: PDF解析器的三层结构（有metadata和嵌套结构）
        has_three_level = False
        for key, value in data.items():
            if key in ['document_title', 'metadata']:
                continue
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, dict) and 'chapters' in sub_value:
                        has_three_level = True
                        break
                if has_three_level:
                    break
        
        if has_three_level:
            # PDF解析器格式
            for level1_key, level1_data in data.items():
                if level1_key in ['document_title', 'metadata', '其他章节']:
                    continue
                
                if isinstance(level1_data, dict):
                    level1_label = level1_data.get('label', level1_key)
                    level1_code = level1_key
                    
                    for level2_key, level2_data in level1_data.items():
                        if level2_key == 'label':
                            continue
                        
                        if isinstance(level2_data, dict) and 'chapters' in level2_data:
                            level2_label = level2_data.get('label', level2_key)
                            level2_code = f"{level1_code}.{level2_key}"
                            
                            chapters = level2_data.get('chapters', {})
                            for chapter_title, chapter_content in chapters.items():
                                if not chapter_content or len(chapter_content.strip()) < 10:
                                    continue
                                
                                section_id = f"{doc_name}_{level1_code}_{level2_key}_{len(sections)}"
                                sections.append({
                                    'id': section_id,
                                    'title': chapter_title,
                                    'text': chapter_content,
                                    'level1': level1_code,
                                    'level1_label': level1_label,
                                    'level2': level2_code,
                                    'level2_label': level2_label,
                                    'source': doc_name,
                                    'document_title': doc_title
                                })
        
        # 策略2: 扁平结构（当前chunks格式）
        else:
            # 从JSON的key-value对中提取
            for key, value in data.items():
                # 兼容不同结构：list/dict/str
                normalized_value = value
                if isinstance(normalized_value, list):
                    flattened_parts = []
                    for item in normalized_value:
                        if isinstance(item, dict):
                            flattened_parts.append(
                                item.get('text')
                                or item.get('content')
                                or item.get('value')
                                or ''
                            )
                        else:
                            flattened_parts.append(str(item))
                    normalized_value = "\n".join(part for part in flattened_parts if part)
                elif isinstance(normalized_value, dict):
                    normalized_value = (
                        normalized_value.get('text')
                        or normalized_value.get('content')
                        or normalized_value.get('value')
                        or ''
                    )

                if not isinstance(normalized_value, str):
                    normalized_value = str(normalized_value or '')

                normalized_value = normalized_value.strip()
                if not normalized_value:
                    continue
                
                # 尝试从key推断分类
                level1_code, level2_code, level2_label = classify_section(title=key, content=normalized_value[:200])
                
                section_id = f"{doc_name}_{level1_code}_{level2_code.split('.')[-1]}_{len(sections)}"
                sections.append({
                    'id': section_id,
                    'title': key,
                    'text': normalized_value,
                    'level1': level1_code,
                    'level1_label': get_category_by_code(level2_code)['l1_label'] if get_category_by_code(level2_code) else level1_code,
                    'level2': level2_code,
                    'level2_label': level2_label,
                    'source': doc_name,
                    'document_title': doc_title
                })
        
        return sections
    
    def _create_section(self, section: Dict, doc_title: str):
        """创建Section节点并连接到CategoryL2"""
        section_id = section['id']
        level2_code = section.get('level2', '')
        
        with self.driver.session(database=self.database) as session:
            # 创建Section节点
            session.run("""
                MERGE (s:Section {id: $id})
                ON CREATE SET 
                    s.title = $title,
                    s.text = $text,
                    s.level1 = $level1,
                    s.level2 = $level2,
                    s.source = $source,
                    s.document_title = $doc_title,
                    s.created_at = datetime()
                ON MATCH SET
                    s.title = $title,
                    s.text = $text
            """,
                id=section_id,
                title=section.get('title', ''),
                text=section.get('text', '')[:10000],  # 限制长度
                level1=section.get('level1', ''),
                level2=level2_code,
                source=section.get('source', ''),
                doc_title=doc_title
            )
            
            # 连接到CategoryL2
            if level2_code:
                session.run("""
                    MATCH (s:Section {id: $section_id})
                    MATCH (c2:CategoryL2 {code: $level2_code})
                    MERGE (c2)-[:HAS_SECTION]->(s)
                """, section_id=section_id, level2_code=level2_code)
            
            self.stats['sections_created'] += 1
    
    
    
    
    def _extract_spo_for_section(self, section: Dict) -> List[Dict]:
        """为Section提取SPO三元组"""
        if not self.use_spo:
            return []
        
        text = section.get('text', '')
        if not text or len(text) < 20:
            return []
        
        try:
            result = self.spo_extractor.extract_triples_from_text(
                text,
                chunk_size=200,
                overlap=30,
                verbose=False
            )
            
            triples = result.get('triples', [])
            # 添加section信息
            for triple in triples:
                triple['section_id'] = section.get('id', '')
                triple['level1'] = section.get('level1', '')
                triple['level2'] = section.get('level2', '')
            
            return triples
        except Exception as e:
            return []
    
    def _create_spo_relations(self, triples: List[Dict], section_id: str, section: Dict):
        """创建SPO关系"""
        with self.driver.session(database=self.database) as session:
            for triple in triples:
                subject = triple.get('subject', '').strip()
                predicate = triple.get('predicate', '').strip()
                obj = triple.get('object', '').strip()
                
                if not all([subject, predicate, obj]):
                    continue
                
                level2_code = section.get('level2', '')
                
                # 尝试将subject映射到Company
                subject_company = session.run("""
                    MATCH (c:Company)
                    WHERE toLower(c.name) = toLower($subject)
                    RETURN c LIMIT 1
                """, subject=subject).single()
                
                if not subject_company:
                    continue
                
                # 尝试将object映射到实体（Company, Campaign, Concept）
                object_label = None
                
                # 先尝试Company
                obj_company = session.run("""
                    MATCH (c:Company)
                    WHERE toLower(c.name) = toLower($obj)
                    RETURN c, 'Company' as label LIMIT 1
                """, obj=obj).single()
                
                if obj_company:
                    object_label = 'Company'
                else:
                    # 尝试Campaign（如果object包含活动关键词）
                    campaign_keywords = ['campaign', '活动', 'event', 'promotion', '促销', '大促']
                    if any(kw in obj.lower() for kw in campaign_keywords):
                        # 创建Campaign节点
                        session.run("""
                            MERGE (c:Campaign {name: $name})
                            ON CREATE SET c.created_at = datetime()
                        """, name=obj)
                        object_label = 'Campaign'
                    else:
                        # 创建Concept节点（通用概念）
                        session.run("""
                            MERGE (c:Concept {name: $name})
                            ON CREATE SET c.created_at = datetime()
                        """, name=obj)
                        object_label = 'Concept'
                
                # 创建关系（使用SPO_REL关系，predicate作为属性）
                if object_label:
                    session.run(f"""
                        MATCH (c1:Company {{name: $subject}})
                        MATCH (c2:{object_label} {{name: $obj}})
                        MERGE (c1)-[r:SPO_REL]->(c2)
                        ON CREATE SET 
                            r.predicate = $predicate,
                            r.section_id = $section_id,
                            r.level2_code = $level2_code,
                            r.created_at = datetime()
                        ON MATCH SET
                            r.predicate = $predicate,
                            r.section_id = $section_id,
                            r.level2_code = $level2_code
                    """,
                        subject=subject,
                        obj=obj,
                        predicate=predicate,
                        section_id=section_id,
                        level2_code=level2_code
                    )
                    
                    self.stats['spo_relations_created'] += 1
    
    def _create_company_category_summary(self):
        """创建Company与CategoryL2的汇总关系"""
        with self.driver.session(database=self.database) as session:
            # 统计每个Company在每个CategoryL2中的出现次数
            result = session.run("""
                MATCH (s:Section)-[:MENTIONS_COMPANY]->(c:Company)
                WHERE s.level2 IS NOT NULL AND s.level2 <> ''
                WITH c, s.level2 as level2_code, count(s) as mention_count,
                     collect(s.id)[0] as first_section_id
                MATCH (c2:CategoryL2 {code: level2_code})
                MERGE (c)-[r:INVOLVED_IN_CATEGORY]->(c2)
                ON CREATE SET 
                    r.count = mention_count,
                    r.first_section_id = first_section_id,
                    r.created_at = datetime()
                ON MATCH SET
                    r.count = mention_count
                RETURN count(r) as relations_created
            """)
            
            record = result.single()
            if record:
                self.stats['involved_in_category_relations'] = record['relations_created']
                print(f"  ✅ 创建了 {record['relations_created']} 个INVOLVED_IN_CATEGORY关系")
    
    def _show_statistics(self):
        """显示统计信息"""
        print("\n" + "=" * 70)
        print("📊 导入统计")
        print("=" * 70)
        print(f"  CategoryL1节点: {self.stats['category_l1_created']}")
        print(f"  CategoryL2节点: {self.stats['category_l2_created']}")
        print(f"  Section节点: {self.stats['sections_created']}")
        print(f"  Company节点: {self.stats['companies_created']}")
        print(f"  Brand节点: {self.stats['brands_created']}")
        print(f"  CompanyType节点: {self.stats['company_types_created']}")
        print(f"  SPO关系: {self.stats['spo_relations_created']}")
        print(f"  INVOLVED_IN_CATEGORY关系: {self.stats['involved_in_category_relations']}")
        print(f"  BELONGS_TO_BRAND关系: {self.stats['belongs_to_brand_relations']}")
        print(f"  BELONGS_TO_TYPE关系: {self.stats['belongs_to_type_relations']}")
        
        # 查询Neo4j中的实际统计
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)
            
            print("\n📈 Neo4j节点统计:")
            print("-" * 70)
            for record in result:
                print(f"  {record['label']}: {record['count']} 个")
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()


if __name__ == "__main__":
    import sys
    
    # 支持命令行参数
    uri = sys.argv[1] if len(sys.argv) > 1 else None
    
    writer = EnhancedKGWriter(uri=uri)
    
    try:
        writer.create_schema()
        writer.process_json_files()
    finally:
        writer.close()

