"""
Cypher 生成器：负责将自然语言问题转换为针对 v1.1 图谱的查询语句。
"""

from __future__ import annotations

from typing import Optional

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


class CypherBuilder:
    """封装 PromptTemplate 与 LLM，生成结构化 Cypher 查询。"""

    def __init__(self, llm: Optional[ChatOpenAI] = None) -> None:
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=1500,
        )
        self.prompt = PromptTemplate(
            input_variables=["question"],
            template=_CYPHER_PROMPT_TEMPLATE,
        )

    def build(self, question: str) -> str:
        """根据问题生成 Cypher 语句；如生成失败则抛出 ValueError。"""
        prompt = self.prompt.format(question=question)
        response = self.llm.invoke(prompt)
        text = (response.content or "").strip()
        if not text:
            raise ValueError("cypher 内容为空")
        return self._clean_cypher(text)

    @staticmethod
    def fallback_cypher() -> str:
        """备用查询语句，与 v1 版本保持兼容。"""
        return _FALLBACK_CYPHER

    @staticmethod
    def _clean_cypher(cypher: str) -> str:
        """移除 Markdown 代码块标记并修复 substring 语法。"""
        import re

        cypher = re.sub(r"^```(?:cypher|sql)?\s*\n", "", cypher, flags=re.MULTILINE)
        cypher = re.sub(r"\n```\s*$", "", cypher, flags=re.MULTILINE)
        cypher = cypher.strip()

        pattern = r"substring\s*\(\s*([^,)]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?![)])"

        def fix_substring(match: "re.Match[str]") -> str:
            return f"substring({match.group(1)}, {match.group(2)}, {match.group(3)})"

        cypher = re.sub(pattern, fix_substring, cypher, flags=re.IGNORECASE)
        cypher = re.sub(
            r"(substring\s*\([^)]*\))\s*\d+\)",
            r"\1",
            cypher,
            flags=re.IGNORECASE,
        )
        return cypher


_CYPHER_PROMPT_TEMPLATE = """
你是 Neo4j Cypher 专家，请将下述问题转换为针对 v1.1 图谱的查询，只返回 Cypher 语句且不要附加解释。

问题: {question}

节点:
- CategoryL1(code, label)
- CategoryL2(code, label, parent_code)
- Section(id, title, text, level1, level2)
- Company(name, type, uncertain)
- Brand(name, level, uncertain)
- CompanyType(code, label)
- Campaign(name)
- Concept(name)

关系（方向不可改变）:
- (:CategoryL1)-[:HAS_SUBCATEGORY]->(:CategoryL2)
- (:CategoryL2)-[:HAS_SECTION]->(:Section)
- (:Section)-[:MENTIONS_COMPANY]->(:Company)
- (:Section)-[:MENTIONS_BRAND]->(:Brand)
- (:Company)-[:INVOLVED_IN_CATEGORY]->(:CategoryL2)
- (:Company)-[:BELONGS_TO_TYPE|OPERATES_IN_TYPE]->(:CompanyType)
- (:Company)-[:SPO_REL {{predicate: launched/collaborates_with/placed_in/uses/competes_with/creates}}]->(:Company)

规则:
1. 只使用上述节点与方向，禁止新增或反转关系
2. 名称统一用 toLower(...) CONTAINS 模糊匹配
3. 需要原文时返回 Section.title 以及 substring(s.text, 0, 300) AS excerpt

示例 1（合作/联名）:
MATCH (c1:Company)-[r:SPO_REL]->(c2:Company)
WHERE toLower(c1.name) CONTAINS toLower("华与华")
  AND toLower(r.predicate) CONTAINS "collaborat"
RETURN c1.name AS sourceCompany,
       c2.name AS partnerCompany,
       r.predicate AS relation,
       r.section_id AS sectionId
LIMIT 10

示例 2（行业洞察）:
MATCH (cat:CategoryL2)-[:HAS_SECTION]->(s:Section)
WHERE toLower(cat.label) CONTAINS toLower("汽车")
RETURN cat.label AS category,
       s.title AS sectionTitle,
       substring(s.text, 0, 300) AS excerpt
LIMIT 5

示例 3（Section 关联公司）:
MATCH (s:Section)-[:MENTIONS_COMPANY]->(c:Company)
WHERE toLower(c.name) CONTAINS toLower("小米")
RETURN s.title AS sectionTitle,
       substring(s.text, 0, 300) AS excerpt,
       collect(DISTINCT c.name) AS companies,
       s.level1 AS level1,
       s.level2 AS level2
LIMIT 5
"""

_FALLBACK_CYPHER = """
MATCH (s:Section)
WHERE toLower(s.text) CONTAINS toLower($keyword)
   OR toLower(s.title) CONTAINS toLower($keyword)
OPTIONAL MATCH (s)-[:MENTIONS_COMPANY]->(c:Company)
OPTIONAL MATCH (s)-[:MENTIONS_BRAND]->(b:Brand)
RETURN s.title AS section_title,
       s.level1 AS level1,
       s.level2 AS level2,
       substring(s.text, 0, 400) AS excerpt,
       collect(DISTINCT c.name) AS companies,
       collect(DISTINCT b.name) AS brands
LIMIT 5
"""

