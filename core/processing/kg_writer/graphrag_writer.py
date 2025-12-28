#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于 GraphRAG 逻辑的智能知识图谱写入器
使用 LLM 生成 Cypher 写入语句，并利用已有图谱结构进行智能关联
"""

import json
import logging
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from neo4j import GraphDatabase
except ImportError:
    print("❌ 需要安装neo4j: pip install neo4j")
    sys.exit(1)

from core.common.llm_provider import get_chat_llm
from core.querying.graph.graph_client import GraphClient
from core.processing.company_dictionary import get_company_dictionary

# 在本文件中内联 GraphRAGEntityRecognizer，便于统一管理识别与写入逻辑
GRAPHRAG_ENTITY_RECOGNIZER_AVAILABLE = True

# 导入基础写入器的部分功能
from .json_loader import extract_sections_from_json
from .entity_linker import EntityLinker

try:
    from core.processing.extractors.entity_extractor import EntityRelationshipExtractor
    ENTITY_EXTRACTOR_AVAILABLE = True
except ImportError:
    ENTITY_EXTRACTOR_AVAILABLE = False

try:
    from core.processing.extractors.org_classifier import OrganizationClassifier
    ORG_CLASSIFIER_AVAILABLE = True
except ImportError:
    ORG_CLASSIFIER_AVAILABLE = False

from core.common.pr_category_schema import (
    CATEGORY_SCHEMA,
    classify_section,
    get_category_by_code
)

try:
    from core.processing.company_dictionary import CompanyDictionary
    COMPANY_DICT_AVAILABLE = True
except Exception:
    COMPANY_DICT_AVAILABLE = False
    CompanyDictionary = None


class GraphRAGWriter:
    """基于 GraphRAG 逻辑的智能知识图谱写入器"""
    
    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        use_llm_for_cypher: bool = True,
        use_graph_context: bool = True
    ):
        """
        初始化 GraphRAG 写入器
        
        Args:
            uri: Neo4j URI
            username: 用户名
            password: 密码
            database: 数据库名
            use_llm_for_cypher: 是否使用 LLM 生成 Cypher 写入语句
            use_graph_context: 是否利用已有图谱结构进行智能关联
        """
        self._setup_logging()
        
        # 加载环境变量
        try:
            from dotenv import load_dotenv
            load_dotenv('.env', override=True)
        except:
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
        
        # 连接 Neo4j
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password),
            max_connection_lifetime=30 * 60,
            max_connection_pool_size=50,
        )
        
        # 测试连接
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                result.single()
            self.logger.info("✅ Neo4j 连接成功")
        except Exception as e:
            self.logger.error(f"❌ Neo4j 连接失败: {e}")
            raise
        
        # 初始化 GraphRAG 组件
        try:
            self.graph_client = GraphClient()
        except Exception as e:
            self.logger.warning(f"⚠️ GraphClient初始化失败: {e}")
            self.graph_client = None
        
        self.use_llm_for_cypher = use_llm_for_cypher
        self.use_graph_context = use_graph_context
        
        # 初始化 LLM（用于生成 Cypher 写入语句）
        if use_llm_for_cypher:
            self.cypher_llm = get_chat_llm(
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=2000,
            )
            self.logger.info("✅ LLM 初始化成功（用于生成 Cypher 写入语句）")
        
        # 初始化实体提取器和分类器
        if ENTITY_EXTRACTOR_AVAILABLE:
            try:
                self.entity_extractor = EntityRelationshipExtractor()
                self.logger.info("✅ 基础实体提取器初始化成功")
            except Exception as e:
                self.logger.warning(f"⚠️ 基础实体提取器初始化失败: {e}")
                self.entity_extractor = None
        else:
            self.entity_extractor = None
        
        # 初始化 GraphRAG 实体识别器（增强版）
        if GRAPHRAG_ENTITY_RECOGNIZER_AVAILABLE and self.graph_client:
            try:
                self.graphrag_recognizer = GraphRAGEntityRecognizer(
                    graph_client=self.graph_client,
                    use_llm_recognition=use_llm_for_cypher,  # 如果启用LLM，也用于实体识别
                    use_graph_query=use_graph_context,
                    use_semantic_matching=use_graph_context
                )
                self.logger.info("✅ GraphRAG 实体识别器初始化成功（增强版）")
            except Exception as e:
                self.logger.warning(f"⚠️ GraphRAG 实体识别器初始化失败: {e}")
                self.graphrag_recognizer = None
        else:
            self.graphrag_recognizer = None
        
        if ORG_CLASSIFIER_AVAILABLE:
            try:
                self.org_classifier = OrganizationClassifier()
                self.logger.info("✅ 组织分类器初始化成功")
            except Exception as e:
                self.logger.warning(f"⚠️ 组织分类器初始化失败: {e}")
                self.org_classifier = None
        else:
            self.org_classifier = None
        
        # 初始化公司词典
        self.company_dict = get_company_dictionary() if COMPANY_DICT_AVAILABLE else None
        
        # 统计信息
        self.stats = {
            'sections_created': 0,
            'companies_created': 0,
            'brands_created': 0,
            'relations_created': 0,
            'cypher_generated': 0,
            'graph_context_used': 0,
            'entities_found_by_graphrag': 0
        }
    
    def _setup_logging(self):
        """配置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - [GraphRAGWriter] - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        self.logger = logging.getLogger("GraphRAGWriter")

    def _clean_chunk_text(self, text: str) -> str:
        """清洗 Feishu/PDF 解析产生的多余前缀与空行"""
        if not text:
            return ""
        
        cleaned_lines = []
        for line in text.splitlines():
            line = line.replace('Content: ', '').replace('Section: ', '').strip()
            if line:
                cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines)
    
    def create_schema(self):
        """创建 Neo4j Schema（与基础写入器相同）"""
        self.logger.info("🏗️ 创建增强图谱Schema...")
        
        schema_queries = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:CategoryL1) REQUIRE c.code IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:CategoryL2) REQUIRE c.code IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Section) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (b:Brand) REQUIRE b.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (ct:CompanyType) REQUIRE ct.code IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Campaign) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE",
            "CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.name)",
        ]
        
        with self.driver.session(database=self.database) as session:
            for query in schema_queries:
                try:
                    session.run(query)
                except Exception:
                    pass
        
        # 创建分类节点
        self._create_category_nodes()
        self._create_company_type_nodes()
        
        self.logger.info("✅ Schema创建完成")
    
    def _create_category_nodes(self):
        """创建所有CategoryL1和CategoryL2节点"""
        with self.driver.session(database=self.database) as session:
            # 创建CategoryL1节点
            for l1_code, l1_data in CATEGORY_SCHEMA.items():
                session.run("""
                    MERGE (c1:CategoryL1 {code: $code})
                    ON CREATE SET 
                        c1.label = $label,
                        c1.created_at = datetime()
                """, code=l1_code, label=l1_data['label'])
            
            # 创建CategoryL2节点并连接到CategoryL1
            for l1_code, l1_data in CATEGORY_SCHEMA.items():
                for l2_subcode, l2_data in l1_data['sub_categories'].items():
                    l2_code = f"{l1_code}.{l2_subcode}"
                    session.run("""
                        MERGE (c2:CategoryL2 {code: $code})
                        ON CREATE SET 
                            c2.label = $label,
                            c2.parent_code = $parent_code,
                            c2.keywords = $keywords,
                            c2.created_at = datetime()
                    """, 
                        code=l2_code,
                        label=l2_data['label'],
                        parent_code=l1_code,
                        keywords=l2_data['keywords']
                    )
                    
                    session.run("""
                        MATCH (c1:CategoryL1 {code: $parent_code})
                        MATCH (c2:CategoryL2 {code: $code})
                        MERGE (c1)-[:HAS_SUBCATEGORY]->(c2)
                    """, parent_code=l1_code, code=l2_code)
    
    def _create_company_type_nodes(self):
        """创建所有CompanyType节点"""
        if not self.org_classifier:
            return
        
        company_types = self.org_classifier.get_company_type_nodes()
        with self.driver.session(database=self.database) as session:
            for ct in company_types:
                session.run("""
                    MERGE (ct:CompanyType {code: $code})
                    ON CREATE SET
                        ct.label = $label,
                        ct.created_at = datetime()
                """, code=ct['code'], label=ct['label'])
    
    def process_json_files(
        self,
        json_dir: str = "data/json_structured",
        resume: bool = True
    ):
        """处理JSON文件并写入Neo4j（使用 GraphRAG 逻辑）"""
        self.logger.info("📊 开始处理JSON文件（使用 GraphRAG 逻辑）...")
        self.logger.info("=" * 70)
        
        json_path = Path(json_dir)
        if not json_path.exists():
            self.logger.error(f"❌ JSON目录不存在: {json_dir}")
            return
        
        json_files = list(json_path.glob("*.json"))
        if not json_files:
            self.logger.error("❌ 未找到JSON文件")
            return
        
        self.logger.info(f"📁 找到 {len(json_files)} 个JSON文件")
        
        for json_file in json_files:
            self.logger.info(f"📄 处理: {json_file.name}")
            try:
                self._process_single_json_with_graphrag(json_file)
            except Exception as e:
                self.logger.error(f"❌ 处理失败: {e}", exc_info=True)
        
        self._show_statistics()
    
    def _process_single_json_with_graphrag(self, json_file: Path):
        """使用 GraphRAG 逻辑处理单个JSON文件"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        doc_title = json_file.stem
        sections: List[Dict[str, Any]] = []

        # 兼容两种结构：
        # 1) 标准 dict 结构（含 document_title / sections 等）
        # 2) Feishu chunks 扁平 list 结构（每个元素是 {chunk_id, text, meta...}）
        if isinstance(data, list):
            for idx, item in enumerate(data):
                if not isinstance(item, dict):
                    continue
                raw_text = item.get('text', '') or item.get('clean_text', '')
                if not raw_text or not raw_text.strip():
                    continue

                clean_text = self._clean_chunk_text(raw_text)
                if not clean_text:
                    continue

                section_id = item.get('chunk_id') or f"{json_file.stem}__{idx}"
                sections.append({
                    'id': section_id,
                    'title': f"{doc_title} - Part {idx + 1}",
                    'text': clean_text,
                    'source': item.get('source', json_file.name),
                    'meta': item.get('meta', {}),
                    'document_title': doc_title,
                    'level1': '',
                    'level2': ''
                })
        else:
            doc_title = data.get('document_title', json_file.stem)
            sections = extract_sections_from_json(data, json_file.stem, doc_title)
        
        if not sections:
            self.logger.warning("  ⚠️ 未从JSON中解析到Section")
            return
        
        self.logger.info(f"  📝 找到 {len(sections)} 个Section")
        
        # 处理每个Section
        for i, section in enumerate(sections):
            try:
                self._process_section_with_graphrag(section, doc_title)
            except Exception as e:
                self.logger.warning(f"  ⚠️ Section {i+1} 处理失败: {e}")
                continue
    
    def _process_section_with_graphrag(self, section: Dict[str, Any], doc_title: str):
        """使用 GraphRAG 逻辑处理单个Section"""
        section_id = section.get('id')
        section_text = section.get('text', '') or section.get('clean_text', '')
        section_title = section.get('title', '')
        
        if not section_id or not section_text:
            return
        
        # 1. 分类Section（classify_section 返回 (level1_code, level2_code, level2_label) 元组）
        level1_code, level2_code, _ = classify_section(
            title=section_title,
            content=section_text
        )
        section['level1'] = level1_code or ''
        section['level2'] = level2_code or ''
        section['document_title'] = section.get('document_title', doc_title)
        
        # 2. 创建Section节点（使用智能Cypher生成）
        if self.use_llm_for_cypher:
            cypher = self._generate_cypher_for_section(section, level1_code, level2_code)
            if cypher:
                self._execute_cypher_write(cypher, section)
                self.stats['cypher_generated'] += 1
            else:
                # 回退到标准写入
                self._create_section_node_standard(section, level1_code, level2_code)
        else:
            self._create_section_node_standard(section, level1_code, level2_code)
        
        # 3. 提取实体（使用 GraphRAG 增强识别）
        entities = self._extract_entities_with_graphrag(
            section_text, 
            section_id,
            section
        )
        if entities:
            self.stats['entities_found_by_graphrag'] += len(entities)
            self._link_entities_with_graphrag(section_id, entities, section)
        
        # 4. 利用已有图谱结构进行智能关联
        if self.use_graph_context and self.graph_client:
            self._enhance_with_graph_context(section_id, section_text, level2_code)
    
    def _generate_cypher_for_section(
        self,
        section: Dict[str, Any],
        level1_code: Optional[str],
        level2_code: Optional[str]
    ) -> Optional[str]:
        """使用 LLM 生成创建Section节点的Cypher语句"""
        section_id = section.get('id')
        section_text = section.get('text', '') or section.get('clean_text', '')
        section_title = section.get('title', '')
        preview_text = (section_text or '')[:300].replace('\n', ' ')

        prompt = f"""
你是一个 Neo4j Cypher 专家。请生成创建 Section 节点的 Cypher 语句。

【输入数据上下文】
- ID: {section_id}
- 标题: {section_title}
- 来源: {section.get('source', '')}
- 一级分类: {level1_code or '未知'}
- 二级分类: {level2_code or '未知'}
- 内容预览: {preview_text}...

【严格规则 - 防止语法错误】
1) 严禁把正文内容直接拼在 Cypher 字符串中，必须用参数占位符。
2) 只能使用以下参数占位符：
   - $section_id
   - $title
   - $content
   - $source
   - $level1
   - $level2
   - $doc_title
3) 使用 MERGE 保证幂等；ON CREATE/ON MATCH 仅设置属性，不要删除节点。
4) 如果存在二级分类 $level2，建立 (cat:CategoryL2 {{code:$level2}})-[:HAS_SECTION]->(s)。
5) 直接输出纯 Cypher，禁止 Markdown、解释或反引号。

【理想模板示例】（仅供参考，实际需你产出正式 Cypher）
MERGE (s:Section {{id: $section_id}})
ON CREATE SET
    s.title = $title,
    s.content = $content,
    s.source = $source,
    s.level1 = $level1,
    s.level2 = $level2,
    s.document_title = $doc_title,
    s.created_at = datetime()
ON MATCH SET
    s.updated_at = datetime()
WITH s
OPTIONAL MATCH (cat:CategoryL2 {{code: $level2}})
FOREACH (_ IN CASE WHEN cat IS NULL OR $level2 = '' THEN [] ELSE [1] END |
    MERGE (cat)-[:HAS_SECTION]->(s)
)

请直接返回 Cypher 语句，不要添加任何多余字符。
"""
        
        try:
            response = self.cypher_llm.invoke(prompt)
            cypher = (response.content or "").strip()
            
            # 清理Markdown标记
            import re
            cypher = re.sub(r"^```(?:cypher|sql)?\s*\n", "", cypher, flags=re.MULTILINE)
            cypher = re.sub(r"\n```\s*$", "", cypher, flags=re.MULTILINE)
            cypher = cypher.strip()
            
            return cypher if cypher else None
        except Exception as e:
            self.logger.warning(f"⚠️ Cypher生成失败: {e}")
            return None
    
    def _execute_cypher_write(self, cypher: str, section: Dict[str, Any]):
        """执行生成的Cypher写入语句"""
        section_id = section.get('id')
        section_text = section.get('text', '') or section.get('clean_text', '')
        section_title = section.get('title', '')

        # 准备参数（必须与Prompt中占位符一致）
        params = {
            'section_id': section_id,
            'title': section_title,
            'content': section_text,
            'source': section.get('source', ''),
            'doc_title': section.get('document_title', ''),
            'level1': section.get('level1', ''),
            'level2': section.get('level2', '')
        }
        
        try:
            with self.driver.session(database=self.database) as session:
                # 执行Cypher语句
                result = session.run(cypher, params)
                result.consume()  # 确保执行完成
                self.stats['sections_created'] += 1
        except Exception as e:
            self.logger.warning(f"⚠️ Cypher执行失败，回退到标准写入: {e}")
            # 回退到标准写入
            level1_code, level2_code, _ = classify_section(
                title=section_title,
                content=section_text
            )
            self._create_section_node_standard(section, level1_code, level2_code)
    
    def _create_section_node_standard(
        self,
        section: Dict[str, Any],
        level1_code: Optional[str],
        level2_code: Optional[str]
    ):
        """标准方式创建Section节点（回退方案）"""
        section_id = section.get('id')
        section_text = section.get('text', '') or section.get('clean_text', '')
        section_title = section.get('title', '')
        
        with self.driver.session(database=self.database) as session:
            # 创建Section节点
            session.run("""
                MERGE (s:Section {id: $id})
                ON CREATE SET
                    s.title = $title,
                    s.content = $content,
                    s.level1 = $level1,
                    s.level2 = $level2,
                    s.created_at = datetime()
            """, 
                id=section_id,
                title=section_title,
                content=section_text,
                level1=level1_code or '',
                level2=level2_code or ''
            )
            
            # 连接到CategoryL2
            if level2_code:
                session.run("""
                    MATCH (s:Section {id: $section_id})
                    MATCH (cat:CategoryL2 {code: $level2_code})
                    MERGE (cat)-[:HAS_SECTION]->(s)
                """, section_id=section_id, level2_code=level2_code)
            
            self.stats['sections_created'] += 1
    
    def _extract_entities_with_graphrag(
        self,
        text: str,
        section_id: str,
        section: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """使用 GraphRAG 增强方法提取实体"""
        entities = []
        
        # 优先使用 GraphRAG 实体识别器（增强版）
        if self.graphrag_recognizer:
            try:
                section_context = {
                    'id': section_id,
                    'title': section.get('title', ''),
                    'level2': section.get('level2', '')
                }
                entities = self.graphrag_recognizer.recognize_entities(
                    text,
                    section_context=section_context
                )
                self.logger.debug(f"✅ GraphRAG 识别到 {len(entities)} 个实体")
            except Exception as e:
                self.logger.warning(f"⚠️ GraphRAG 实体识别失败: {e}")
                # 回退到基础方法
                entities = self._extract_entities_fallback(text)
        else:
            # 回退到基础方法
            entities = self._extract_entities_fallback(text)
        
        # 如果启用图谱上下文，进一步丰富实体信息
        if self.use_graph_context and entities and self.graph_client:
            entities = self._enrich_entities_with_graph(entities, text)
        
        return entities
    
    def _extract_entities_fallback(self, text: str) -> List[Dict[str, Any]]:
        """回退方法：使用基础实体提取器"""
        entities = []
        
        if self.entity_extractor:
            try:
                entities = self.entity_extractor.extract_entities_from_text(text)
            except Exception as e:
                self.logger.warning(f"⚠️ 基础实体提取失败: {e}")
        
        return entities
    
    def _enrich_entities_with_graph(
        self,
        entities: List[Dict[str, Any]],
        text: str
    ) -> List[Dict[str, Any]]:
        """利用已有图谱结构丰富实体信息"""
        enriched = []
        
        for entity in entities:
            entity_name = entity.get('name', '')
            if not entity_name:
                continue
            
            # 查询图谱中是否已存在该实体
            existing_entity = self._query_existing_entity(entity_name)
            if existing_entity:
                # 合并信息
                entity.update(existing_entity)
                entity['exists_in_graph'] = True
                self.stats['graph_context_used'] += 1
            else:
                entity['exists_in_graph'] = False
            
            enriched.append(entity)
        
        return enriched
    
    def _query_existing_entity(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """查询图谱中是否已存在该实体"""
        if not self.graph_client:
            return None
        
        try:
            # 先查Company
            result = self.graph_client.query("""
                MATCH (c:Company)
                WHERE toLower(c.name) = toLower($name)
                RETURN c.name AS name, c.type AS type, c.confidence AS confidence
                LIMIT 1
            """, params={'name': entity_name})
            
            if result:
                return {
                    'type': 'Company',
                    'confidence': result[0].get('confidence', 0.8),
                    'verified': True
                }
            
            # 再查Brand
            result = self.graph_client.query("""
                MATCH (b:Brand)
                WHERE toLower(b.name) = toLower($name)
                RETURN b.name AS name, b.level AS level
                LIMIT 1
            """, params={'name': entity_name})
            
            if result:
                return {
                    'type': 'Brand',
                    'confidence': 0.8,
                    'verified': True
                }
            
            return None
        except Exception as e:
            self.logger.debug(f"查询已有实体失败: {e}")
            return None
    
    def _link_entities_with_graphrag(
        self,
        section_id: str,
        entities: List[Dict[str, Any]],
        section: Dict[str, Any]
    ):
        """使用 GraphRAG 逻辑关联实体"""
        with self.driver.session(database=self.database) as session:
            for entity in entities:
                entity_name = entity.get('name', '')
                entity_type = entity.get('type', 'Company')
                
                if not entity_name:
                    continue
                
                # 创建或更新实体节点
                if entity_type == 'Company':
                    session.run("""
                        MERGE (c:Company {name: $name})
                        ON CREATE SET
                            c.type = 'company',
                            c.created_at = datetime(),
                            c.confidence = $confidence,
                            c.verified = $verified
                        ON MATCH SET
                            c.confidence = COALESCE($confidence, c.confidence),
                            c.verified = COALESCE($verified, c.verified, false)
                    """, 
                        name=entity_name,
                        confidence=entity.get('confidence', 0.7),
                        verified=entity.get('verified', False)
                    )
                    
                    # 关联到Section
                    session.run("""
                        MATCH (s:Section {id: $section_id})
                        MATCH (c:Company {name: $name})
                        MERGE (s)-[:MENTIONS_COMPANY]->(c)
                    """, section_id=section_id, name=entity_name)
                    
                    self.stats['companies_created'] += 1
                    self.stats['relations_created'] += 1
                
                elif entity_type == 'Brand':
                    session.run("""
                        MERGE (b:Brand {name: $name})
                        ON CREATE SET
                            b.type = 'brand',
                            b.created_at = datetime(),
                            b.confidence = $confidence
                    """, 
                        name=entity_name,
                        confidence=entity.get('confidence', 0.7)
                    )
                    
                    # 关联到Section
                    session.run("""
                        MATCH (s:Section {id: $section_id})
                        MATCH (b:Brand {name: $name})
                        MERGE (s)-[:MENTIONS_BRAND]->(b)
                    """, section_id=section_id, name=entity_name)
                    
                    self.stats['brands_created'] += 1
                    self.stats['relations_created'] += 1
    
    def _enhance_with_graph_context(
        self,
        section_id: str,
        section_text: str,
        level2_code: Optional[str]
    ):
        """利用已有图谱结构进行智能增强"""
        try:
            # 查找相关实体和关系
            related_entities = self._find_related_entities_in_graph(section_text)
            
            if related_entities:
                # 创建额外的关联关系
                with self.driver.session(database=self.database) as session:
                    for entity_name, entity_type in related_entities:
                        if entity_type == 'Company':
                            session.run("""
                                MATCH (s:Section {id: $section_id})
                                MATCH (c:Company)
                                WHERE toLower(c.name) CONTAINS toLower($entity_name)
                                MERGE (s)-[:MENTIONS_COMPANY]->(c)
                            """, section_id=section_id, entity_name=entity_name)
                        elif entity_type == 'Brand':
                            session.run("""
                                MATCH (s:Section {id: $section_id})
                                MATCH (b:Brand)
                                WHERE toLower(b.name) CONTAINS toLower($entity_name)
                                MERGE (s)-[:MENTIONS_BRAND]->(b)
                            """, section_id=section_id, entity_name=entity_name)
                
                self.stats['graph_context_used'] += len(related_entities)
        except Exception as e:
            self.logger.debug(f"图谱上下文增强失败: {e}")
    
    def _find_related_entities_in_graph(self, text: str) -> List[tuple]:
        """在已有图谱中查找相关实体"""
        if not self.graph_client:
            return []
        
        related = []
        
        # 使用公司词典查找
        if self.company_dict:
            companies = self.company_dict.find_companies_in_text(text)
            for company in companies:
                # 检查图谱中是否存在
                try:
                    result = self.graph_client.query("""
                        MATCH (c:Company)
                        WHERE toLower(c.name) = toLower($name)
                        RETURN c.name AS name
                        LIMIT 1
                    """, params={'name': company})
                    
                    if result:
                        related.append((company, 'Company'))
                except Exception:
                    pass
        
        return related
    
    def _show_statistics(self):
        """显示统计信息"""
        self.logger.info("\n📊 GraphRAG写入统计:")
        self.logger.info("=" * 70)
        for key, value in self.stats.items():
            self.logger.info(f"  {key}: {value}")
        self.logger.info("=" * 70)
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            self.logger.info("✅ 连接已关闭")


class GraphRAGEntityRecognizer:
    """基于 GraphRAG 的增强实体识别器（内联版本）"""
    
    def __init__(
        self,
        graph_client: Optional[GraphClient] = None,
        use_llm_recognition: bool = True,
        use_graph_query: bool = True,
        use_semantic_matching: bool = True
    ):
        """
        初始化 GraphRAG 实体识别器
        
        Args:
            graph_client: 图谱查询客户端（由 GraphRAGWriter 注入）
            use_llm_recognition: 是否使用 LLM 进行实体识别
            use_graph_query: 是否使用图谱查询来识别实体
            use_semantic_matching: 是否使用语义匹配
        """
        self._setup_logging()
        
        self.graph_client = graph_client
        self.use_llm_recognition = use_llm_recognition
        self.use_graph_query = use_graph_query
        self.use_semantic_matching = use_semantic_matching
        
        # 初始化 LLM（用于实体识别）
        if use_llm_recognition:
            try:
                self.llm = get_chat_llm(
                    model="gpt-4o-mini",
                    temperature=0.1,
                    max_tokens=2000,
                )
                self.logger.info("✅ LLM 初始化成功（用于实体识别）")
            except Exception as e:
                self.logger.warning(f"⚠️ LLM 初始化失败: {e}")
                self.llm = None
        else:
            self.llm = None
        
        # 初始化基础实体提取器
        if ENTITY_EXTRACTOR_AVAILABLE:
            try:
                self.entity_extractor = EntityRelationshipExtractor()
                self.logger.info("✅ 基础实体提取器初始化成功")
            except Exception as e:
                self.logger.warning(f"⚠️ 基础实体提取器初始化失败: {e}")
                self.entity_extractor = None
        else:
            self.entity_extractor = None
        
        # 初始化公司词典
        if COMPANY_DICT_AVAILABLE:
            try:
                self.company_dict = get_company_dictionary()
            except Exception as e:
                self.logger.warning(f"⚠️ 公司词典初始化失败: {e}")
                self.company_dict = None
        else:
            self.company_dict = None
        
        # 统计信息
        self.stats = {
            'entities_found_by_dict': 0,
            'entities_found_by_llm': 0,
            'entities_found_by_graph': 0,
            'entities_found_by_semantic': 0,
            'entities_verified': 0
        }
    
    def _setup_logging(self):
        """配置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - [GraphRAGEntityRecognizer] - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        self.logger = logging.getLogger("GraphRAGEntityRecognizer")
    
    def recognize_entities(
        self,
        text: str,
        section_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        使用 GraphRAG 方法识别实体
        
        Args:
            text: 要分析的文本
            section_context: Section 上下文信息（可选）
        
        Returns:
            实体列表，每个实体包含 name, type, confidence, source 等信息
        """
        all_entities: Dict[str, Dict[str, Any]] = {}
        
        # 1. 使用公司词典识别（快速、准确）
        dict_entities = self._recognize_by_dictionary(text)
        for entity in dict_entities:
            all_entities[entity['name']] = entity
        
        # 2. 使用 LLM 识别（智能、全面）
        if self.use_llm_recognition:
            llm_entities = self._recognize_by_llm(text, section_context)
            for entity in llm_entities:
                name = entity['name']
                if name not in all_entities:
                    all_entities[name] = entity
                else:
                    # 合并信息，提高置信度
                    existing = all_entities[name]
                    existing['confidence'] = max(
                        existing.get('confidence', 0.5),
                        entity.get('confidence', 0.5)
                    )
                    existing.setdefault('sources', []).append(entity.get('source', 'llm'))
        
        # 3. 使用图谱查询识别（利用已有知识）
        if self.use_graph_query:
            graph_entities = self._recognize_by_graph_query(text)
            for entity in graph_entities:
                name = entity['name']
                if name not in all_entities:
                    all_entities[name] = entity
                else:
                    # 如果图谱中已存在，提高置信度并标记为已验证
                    existing = all_entities[name]
                    existing['confidence'] = min(1.0, existing.get('confidence', 0.5) + 0.2)
                    existing['verified'] = True
                    existing['exists_in_graph'] = True
        
        # 4. 使用语义匹配识别（模糊匹配）
        if self.use_semantic_matching:
            semantic_entities = self._recognize_by_semantic_matching(text, list(all_entities.keys()))
            for entity in semantic_entities:
                name = entity['name']
                if name not in all_entities:
                    all_entities[name] = entity
        
        # 5. 验证和去重
        verified_entities = self._verify_and_deduplicate(list(all_entities.values()))
        
        return verified_entities
    
    def _recognize_by_dictionary(self, text: str) -> List[Dict[str, Any]]:
        """使用公司词典识别实体"""
        entities: List[Dict[str, Any]] = []
        
        if not self.company_dict:
            return entities
        
        companies = self.company_dict.find_companies_in_text(text)
        for company in companies:
            entities.append({
                'name': company,
                'type': 'Company',
                'confidence': 0.9,
                'source': 'dictionary',
                'sources': ['dictionary'],
                'verified': False
            })
            self.stats['entities_found_by_dict'] += 1
        
        return entities
    
    def _recognize_by_llm(
        self,
        text: str,
        section_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """使用 LLM 识别实体"""
        entities: List[Dict[str, Any]] = []
        
        if not self.llm:
            return entities
        
        # 构建上下文信息
        context_info = ""
        if section_context:
            context_info = f"""
上下文信息:
- Section标题: {section_context.get('title', '')}
- 分类: {section_context.get('level2', '')}
"""
        
        prompt = f"""
你是一个实体识别专家。请从以下文本中识别出所有提到的公司（Company）和品牌（Brand）实体。

{context_info}

文本内容:
{text[:1000]}

要求:
1. 识别所有明确提到的公司名和品牌名
2. 区分 Company（公司）和 Brand（品牌）
3. 对于每个实体，评估置信度（0.0-1.0）
4. 只返回 JSON 格式，不要包含其他解释

输出格式（JSON数组）:
[
  {{
    "name": "实体名称",
    "type": "Company" 或 "Brand",
    "confidence": 0.0-1.0,
    "reason": "识别原因（可选）"
  }}
]

只返回 JSON 数组:
"""
        
        try:
            response = self.llm.invoke(prompt)
            content = (response.content or "").strip()
            
            # 清理 Markdown 标记
            content = re.sub(r"^```(?:json)?\s*\n", "", content, flags=re.MULTILINE)
            content = re.sub(r"\n```\s*$", "", content, flags=re.MULTILINE)
            content = content.strip()
            
            # 解析 JSON
            llm_entities = json.loads(content)
            
            for entity in llm_entities:
                name = entity.get('name', '').strip()
                if not name:
                    continue
                entities.append({
                    'name': name,
                    'type': entity.get('type', 'Company'),
                    'confidence': float(entity.get('confidence', 0.7)),
                    'source': 'llm',
                    'sources': ['llm'],
                    'reason': entity.get('reason', ''),
                    'verified': False
                })
                self.stats['entities_found_by_llm'] += 1
            
        except Exception as e:
            self.logger.warning(f"⚠️ LLM 实体识别失败: {e}")
        
        return entities
    
    def _recognize_by_graph_query(self, text: str) -> List[Dict[str, Any]]:
        """使用图谱查询识别实体"""
        entities: List[Dict[str, Any]] = []
        
        if not self.graph_client:
            return entities
        
        try:
            # 提取文本中的关键词
            keywords = self._extract_keywords(text)
            
            # 查询图谱中匹配的实体
            for keyword in keywords[:10]:  # 限制查询数量
                # 查询 Company
                result = self.graph_client.query("""
                    MATCH (c:Company)
                    WHERE toLower(c.name) CONTAINS toLower($keyword)
                       OR toLower($keyword) CONTAINS toLower(c.name)
                    RETURN c.name AS name, c.type AS type, c.confidence AS confidence
                    LIMIT 5
                """, params={'keyword': keyword})
                
                for row in result:
                    entities.append({
                        'name': row.get('name', ''),
                        'type': 'Company',
                        'confidence': row.get('confidence', 0.8),
                        'source': 'graph_query',
                        'sources': ['graph_query'],
                        'verified': True,
                        'exists_in_graph': True
                    })
                    self.stats['entities_found_by_graph'] += 1
                
                # 查询 Brand
                result = self.graph_client.query("""
                    MATCH (b:Brand)
                    WHERE toLower(b.name) CONTAINS toLower($keyword)
                       OR toLower($keyword) CONTAINS toLower(b.name)
                    RETURN b.name AS name, b.level AS level
                    LIMIT 5
                """, params={'keyword': keyword})
                
                for row in result:
                    entities.append({
                        'name': row.get('name', ''),
                        'type': 'Brand',
                        'confidence': 0.8,
                        'source': 'graph_query',
                        'sources': ['graph_query'],
                        'verified': True,
                        'exists_in_graph': True
                    })
                    self.stats['entities_found_by_graph'] += 1
        
        except Exception as e:
            self.logger.debug(f"图谱查询识别失败: {e}")
        
        return entities
    
    def _recognize_by_semantic_matching(
        self,
        text: str,
        existing_entities: List[str]
    ) -> List[Dict[str, Any]]:
        """使用语义匹配识别实体（模糊匹配）"""
        entities: List[Dict[str, Any]] = []
        
        if not self.graph_client:
            return entities
        
        try:
            # 提取文本中的潜在实体名（2-6个中文字符）
            potential_entities = re.findall(r'[\u4e00-\u9fa5]{2,6}', text)
            
            # 查询图谱中相似的实体
            for potential in potential_entities[:20]:  # 限制查询数量
                if potential in existing_entities:
                    continue
                
                # 模糊匹配 Company
                result = self.graph_client.query("""
                    MATCH (c:Company)
                    WHERE toLower(c.name) CONTAINS toLower($potential)
                       OR toLower($potential) CONTAINS toLower(c.name)
                    RETURN c.name AS name, c.confidence AS confidence
                    ORDER BY 
                        CASE 
                            WHEN toLower(c.name) = toLower($potential) THEN 1
                            WHEN toLower(c.name) CONTAINS toLower($potential) THEN 2
                            ELSE 3
                        END
                    LIMIT 1
                """, params={'potential': potential})
                
                if result:
                    row = result[0]
                    entities.append({
                        'name': row.get('name', ''),
                        'type': 'Company',
                        'confidence': 0.6,  # 模糊匹配置信度较低
                        'source': 'semantic_matching',
                        'sources': ['semantic_matching'],
                        'verified': True,
                        'exists_in_graph': True,
                        'matched_from': potential
                    })
                    self.stats['entities_found_by_semantic'] += 1
        
        except Exception as e:
            self.logger.debug(f"语义匹配识别失败: {e}")
        
        return entities
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        keywords: List[str] = []
        
        # 使用公司词典提取
        if self.company_dict:
            companies = self.company_dict.find_companies_in_text(text)
            keywords.extend(companies)
        
        # 提取2-6个中文字符的词语
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,6}', text)
        keywords.extend(chinese_words)
        
        # 去重
        seen: set[str] = set()
        unique_keywords: List[str] = []
        for kw in keywords:
            if kw not in seen and len(kw) >= 2:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:20]  # 限制数量
    
    def _verify_and_deduplicate(
        self,
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """验证和去重实体"""
        verified: List[Dict[str, Any]] = []
        seen_names: set[str] = set()
        
        # 按置信度排序
        entities.sort(key=lambda x: x.get('confidence', 0.5), reverse=True)
        
        for entity in entities:
            name = entity.get('name', '').strip()
            if not name or len(name) < 2:
                continue
            
            # 标准化名称（转小写）
            name_lower = name.lower()
            
            # 检查是否已存在（考虑变体）
            if name_lower not in seen_names:
                # 检查是否有相似的实体（避免重复）
                is_duplicate = False
                for seen_name in seen_names:
                    if self._is_similar_entity(name_lower, seen_name):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    # 如果多个来源识别到同一实体，合并信息
                    if 'sources' not in entity:
                        entity['sources'] = [entity.get('source', 'unknown')]
                    
                    verified.append(entity)
                    seen_names.add(name_lower)
                    self.stats['entities_verified'] += 1
        
        return verified
    
    def _is_similar_entity(self, name1: str, name2: str) -> bool:
        """判断两个实体名是否相似"""
        # 完全匹配
        if name1 == name2:
            return True
        
        # 包含关系
        if name1 in name2 or name2 in name1:
            return True
        
        # 简单编辑距离：长度差 ≤1 且字符差异小
        if abs(len(name1) - len(name2)) <= 1:
            diff = sum(c1 != c2 for c1, c2 in zip(name1, name2))
            if diff <= 1:
                return True
        
        return False
    
    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        return self.stats.copy()


