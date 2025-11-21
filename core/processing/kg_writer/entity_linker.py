#!/usr/bin/env python3
"""
实体/品牌节点写入与关系构建逻辑 Cursor Write It-qcf ;
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


class EntityLinker:
    """负责将 Section 与 Company/Brand/Type 关联 Cursor Write It-qcf ;"""

    GENERIC_KEYWORDS = {
        '平台', '电商', '营销', '广告', '媒体', '数据', '报告', '行业', '用户', '内容', '方案', '策略', '指南',
        '案例', '活动', '工具', '系统', '引擎', '技术', '服务', '商城', '积分', '会员', '排行榜', '排名',
        '研究', '研究院', '协会', '大学', '学院', '医院', '出版社', '公司', '集团', '股份', '旗舰店', '官方',
        '项目组', '应用', '网站', '官网', '直播', '短视频', '媒体平台', '家电', '手机', '汽车', 'SUV', '越野',
        '电动汽车', '旗舰机', '旗舰手机', '观察', '洞察', '趋势', '总结', '盘点', '白皮书', '样本', '人物',
        '人群', '消费者', '社交', '矩阵', '玩法', '运营', '增长', '投放', '传播', '营销人', '案例库', '课程',
        '学院', '解决方案', '品牌推广', '品牌传播', '品牌营销', '品牌策略', '品牌案例', '财报', '市场',
        '行业报告', '行业洞察', '行业分析'
    }

    GENERIC_SUFFIXES = {
        '平台', '营销', '传播', '策略', '方案', '案例', '指南', '洞察', '趋势', '观察', '矩阵', '运营', '玩法',
        '增长', '报告', '研究', '分析', '投放', '白皮书', '财报', '总结', '盘点', '榜单', '排行榜', '竞品',
        '行业', '市场', '研究院', '实验室', '智库', '学院', '课程', '俱乐部', '实验室', '观察室', '范式',
        '模型', '系统', '工具', '引擎', '方案', '中心', '基地', '阵地', '指数'
    }

    def __init__(
        self,
        driver,
        database: str,
        stats: Dict[str, int],
        org_classifier=None,
        company_dict=None,
    ):
        self.driver = driver
        self.database = database
        self.stats = stats
        self.org_classifier = org_classifier
        self.company_dict = company_dict

    # ----------------------------- Public API -----------------------------
    def link(self, section_id: str, entities: Any, section: Dict[str, Any]) -> None:
        """入口：连接 Section 与实体 Cursor Write It-qcf ;"""
        normalized_entities = self._normalize_entities(entities)
        if not normalized_entities:
            return

        if not self.org_classifier:
            self._link_section_to_entities_legacy(section_id, normalized_entities, section)
            return

        with self.driver.session(database=self.database) as session:
            all_entities: List[Dict[str, Any]] = []
            all_entities.extend(normalized_entities.get('companies', []))
            all_entities.extend(normalized_entities.get('brands', []))

            section_text = section.get('text', '')
            section_title = section.get('title', '')
            context = f"{section_title} {section_text}"[:500]
            category_code = section.get('level2', '')

            for entity in all_entities:
                entity_name = entity.get('name', '') if isinstance(entity, dict) else str(entity)
                if not entity_name or len(entity_name) < 2:
                    continue

                classification = self.org_classifier.classify_entity(
                    entity_name,
                    context=context,
                    category_code=category_code
                )

                entity_type = classification['type']
                attributes = classification['attributes']
                industry_types = classification['industry_types']

                if entity_type == 'company':
                    self._create_company_node(session, entity_name, attributes)
                    brand_part = attributes.get('brand_part')
                    if brand_part and brand_part != entity_name:
                        brand_attrs = {'type': 'brand', 'level': 'group'}
                        self._create_brand_node(session, brand_part, brand_attrs)
                        self._create_belongs_to_brand_relation(session, entity_name, brand_part)
                elif entity_type == 'brand':
                    self._create_brand_node(session, entity_name, attributes)
                else:
                    self._create_brand_node(session, entity_name, attributes)

                if industry_types:
                    for industry in industry_types:
                        self._create_belongs_to_type_relation(session, entity_name, entity_type, industry)

                self._link_section_to_entity(session, section_id, entity_name, entity_type)

    # ----------------------------- Helpers -----------------------------
    def _normalize_entities(self, entities: Any) -> Dict[str, List[Dict[str, Any]]]:
        if isinstance(entities, list):
            normalized = {'companies': [], 'brands': []}
            for entity in entities:
                if not isinstance(entity, dict):
                    continue
                entity_type = entity.get('type', '').lower()
                if entity_type == 'company':
                    normalized['companies'].append(entity)
                elif entity_type == 'brand':
                    normalized['brands'].append(entity)
                else:
                    normalized['brands'].append(entity)
            return normalized
        if isinstance(entities, dict):
            return entities
        return {'companies': [], 'brands': []}

    def _link_section_to_entities_legacy(self, section_id: str, entities: Dict[str, Any], section: Dict[str, Any]) -> None:
        with self.driver.session(database=self.database) as session:
            for company in entities.get('companies', []):
                company_name = company.get('name', '') if isinstance(company, dict) else str(company)
                if not company_name or len(company_name) < 2:
                    continue

                session.run("""
                    MERGE (c:Company {name: $name})
                    ON CREATE SET 
                        c.created_at = datetime(),
                        c.industry = $industry
                    ON MATCH SET
                        c.industry = COALESCE(c.industry, $industry)
                """,
                    name=company_name,
                    industry=company.get('industry', 'unknown') if isinstance(company, dict) else 'unknown'
                )

                session.run("""
                    MATCH (s:Section {id: $section_id})
                    MATCH (c:Company {name: $company_name})
                    MERGE (s)-[:MENTIONS_COMPANY]->(c)
                """, section_id=section_id, company_name=company_name)

                self.stats['companies_created'] += 1

            for brand in entities.get('brands', []):
                brand_name = brand.get('name', '') if isinstance(brand, dict) else str(brand)
                if not brand_name or len(brand_name) < 2:
                    continue

                session.run("""
                    MERGE (c:Company {name: $name})
                    ON CREATE SET 
                        c.created_at = datetime(),
                        c.industry = $industry,
                        c.is_brand = true
                """,
                    name=brand_name,
                    industry=brand.get('industry', 'unknown') if isinstance(brand, dict) else 'unknown'
                )

                session.run("""
                    MATCH (s:Section {id: $section_id})
                    MATCH (c:Company {name: $name})
                    MERGE (s)-[:MENTIONS_COMPANY]->(c)
                """, section_id=section_id, name=brand_name)

    # ----------------------------- Node Builders -----------------------------
    def _create_company_node(self, session, name: str, attributes: Dict[str, Any]) -> None:
        session.run("""
            MERGE (c:Company {name: $name})
            ON CREATE SET 
                c.type = 'company',
                c.created_at = datetime(),
                c.uncertain = COALESCE($uncertain, false)
            ON MATCH SET
                c.type = COALESCE(c.type, 'company'),
                c.uncertain = COALESCE($uncertain, c.uncertain, false)
        """, name=name, uncertain=attributes.get('uncertain', False))
        self.stats['companies_created'] += 1

    def _create_brand_node(
        self,
        session,
        name: str,
        attributes: Dict[str, Any],
        classification: Optional[Dict[str, Any]] = None
    ) -> None:
        norm = self._normalize_name(name)
        context_text = attributes.get('context') if isinstance(attributes, dict) else None
        category_code = attributes.get('category_code') if isinstance(attributes, dict) else None
        if not self._should_create_brand(
            norm,
            context=context_text,
            category_code=category_code,
            classification=classification
        ):
            self.stats['brands_skipped'] += 1
            return

        level = attributes.get('level', 'group')
        uncertain = attributes.get('uncertain', False)
        session.run("""
            MERGE (b:Brand {name: $name})
            ON CREATE SET 
                b.type = 'brand',
                b.level = $level,
                b.created_at = datetime(),
                b.uncertain = COALESCE($uncertain, false)
            ON MATCH SET
                b.type = COALESCE(b.type, 'brand'),
                b.level = COALESCE(b.level, $level),
                b.uncertain = COALESCE($uncertain, b.uncertain, false)
        """, name=norm, level=level, uncertain=uncertain)
        self.stats['brands_created'] += 1

    def _create_belongs_to_brand_relation(self, session, company_name: str, brand_name: str) -> None:
        session.run("""
            MATCH (c:Company {name: $company_name})
            MATCH (b:Brand {name: $brand_name})
            MERGE (c)-[:BELONGS_TO_BRAND]->(b)
        """, company_name=company_name, brand_name=brand_name)
        self.stats['belongs_to_brand_relations'] += 1

    def _create_belongs_to_type_relation(self, session, entity_name: str, entity_type: str, industry: Dict[str, Any]) -> None:
        industry_code = industry['code']
        if entity_type == 'company':
            session.run("""
                MATCH (c:Company {name: $entity_name})
                MATCH (ct:CompanyType {code: $industry_code})
                MERGE (c)-[:BELONGS_TO_TYPE]->(ct)
            """, entity_name=entity_name, industry_code=industry_code)
        elif entity_type == 'brand':
            session.run("""
                MATCH (b:Brand {name: $entity_name})
                MATCH (ct:CompanyType {code: $industry_code})
                MERGE (b)-[:OPERATES_IN_TYPE]->(ct)
            """, entity_name=entity_name, industry_code=industry_code)
        self.stats['belongs_to_type_relations'] += 1

    def _link_section_to_entity(self, session, section_id: str, entity_name: str, entity_type: str) -> None:
        if entity_type == 'company':
            session.run("""
                MATCH (s:Section {id: $section_id})
                MATCH (c:Company {name: $entity_name})
                MERGE (s)-[:MENTIONS_COMPANY]->(c)
            """, section_id=section_id, entity_name=entity_name)
        elif entity_type == 'brand':
            norm = self._normalize_name(entity_name)
            session.run("""
                MATCH (s:Section {id: $section_id})
                MATCH (b:Brand {name: $entity_name})
                MERGE (s)-[:MENTIONS_BRAND]->(b)
            """, section_id=section_id, entity_name=norm)
        else:
            session.run("""
                MATCH (s:Section {id: $section_id})
                MATCH (c:Company {name: $entity_name})
                MERGE (s)-[:MENTIONS_COMPANY]->(c)
            """, section_id=section_id, entity_name=entity_name)

    # ----------------------------- Brand Filters -----------------------------
    def _should_create_brand(
        self,
        name: str,
        context: Optional[str] = None,
        category_code: Optional[str] = None,
        classification: Optional[Dict[str, Any]] = None
    ) -> bool:
        if not name or len(name) < 2:
            return False

        if classification and classification.get('is_brand', False):
            return True

        if self._is_in_company_dictionary(name):
            return True

        if self._is_generic_name(name):
            return False

        if self._seems_generic_brand_name(name):
            if context:
                lowered = context.lower()
                if '品牌' in context or 'brand' in lowered:
                    return True
            return False

        if category_code and category_code.startswith('MKT.'):
            return True

        return True

    def _is_generic_name(self, name: str) -> bool:
        lowered = name.lower()
        for keyword in self.GENERIC_KEYWORDS:
            if keyword in name:
                return True
            if keyword.lower() in lowered:
                return True
        return False

    def _is_in_company_dictionary(self, name: str) -> bool:
        if not self.company_dict:
            return False
        normalized = self._normalize_name(name)
        return self.company_dict.exists(normalized)

    def _seems_generic_brand_name(self, name: str) -> bool:
        for suffix in self.GENERIC_SUFFIXES:
            if name.endswith(suffix):
                return True
        if re.match(r'^[A-Za-z\s]+(Plan|Strategy|Guide|Report|Insight|Toolkit)$', name):
            return True
        if len(name) <= 3 and re.match(r'^[A-Za-z]+$', name):
            return True
        return False

    @staticmethod
    def _normalize_name(name: Any) -> str:
        if not isinstance(name, str):
            return ""
        n = name.strip().strip('\'"“”‘’').strip()
        n = re.sub(r'\s{2,}', ' ', n)
        return n

