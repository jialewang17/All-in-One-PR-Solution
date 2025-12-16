## 图谱结构说明文档

> 快速总览：哪些节点是固定定义直接写入，哪些节点依赖 LLM 抽取
>
> - **预定义/直接写入的节点**（不依赖 LLM 抽取）  
>   - `CategoryL1` / `CategoryL2`：来自 `CATEGORY_SCHEMA`，初始化时统一创建  
>   - `Section`：来自 `data/json_structured/*.json` 的规范化分段文本  
>   - `Channel`、`Industry`、`PRCase`、`PRGoal`：来自 CSV/Excel 案例库  
>   - `CompanyType`：来自组织分类器内置表 `industry_types`，初始化时统一创建
>
> - **依赖 LLM/规则抽取的节点**（运行时从文本或三元组生成）  
>   - `Company`、`Brand`：对 Section 的 `clean_text` 进行实体抽取 + 分类  
>   - `Campaign`、`Concept`：SPO 抽取的 `object` 字段按规则归类创建  
>   - 相关关系如 `MENTIONS_*`、`BELONGS_TO_*`、`SPO_REL` 也随抽取结果生成

本文档说明当前 Neo4j 公关知识图谱中各类 **节点** 和 **关系** 的来源与生成逻辑，便于后续维护与排错。

- **节点部分**：每种节点从哪里来，是直接从原始数据写入，还是由下游步骤生成。
- **关系部分**：每种关系连接了哪些节点，由哪个脚本、在什么阶段生成。

---

## 一、节点来源

### 1. `CategoryL1`（一级分类）

- **来源脚本**: `core/processing/kg_writer/writer.py` → `EnhancedKGWriter.create_schema()`
- **数据源**: `core/common/pr_category_schema.py` 中的 `CATEGORY_SCHEMA`
- **生成方式**:
  - 初始化阶段遍历 `CATEGORY_SCHEMA`，对每个一级分类 `l1_code`:
    - `MERGE (c:CategoryL1 {code: $l1_code})`
    - `SET c.label = $l1_label`
  - 同时为 `CategoryL1` 创建唯一约束：
    - `CREATE CONSTRAINT IF NOT EXISTS FOR (c:CategoryL1) REQUIRE c.code IS UNIQUE`
- **说明**:
  - 用于组织二级分类，后续通过 `HAS_SUBCATEGORY` 连接到 `CategoryL2`。

### 2. `CategoryL2`（二级分类）

- **来源脚本**: `writer.py` → `create_schema()` + Section 写入阶段
- **数据源**: `CATEGORY_SCHEMA` 的 `sub_categories`（如 `ecommerce.live_streaming`）
- **生成方式**:
  - 初始化阶段为所有二级分类创建节点与约束：
    - `MERGE (c:CategoryL2 {code: $l2_code})`
    - `SET c.label = $l2_label`
    - `CREATE CONSTRAINT IF NOT EXISTS FOR (c:CategoryL2) REQUIRE c.code IS UNIQUE`
  - 与 `CategoryL1` 通过 `HAS_SUBCATEGORY` 连接（见关系部分）。
- **说明**:
  - Section 的分类字段 `level2` / `category_code` 会对应到 `CategoryL2.code`。

### 3. `Section`

- **主要用途**: 承载结构化后的文档分段文本，是后续实体抽取与 SPO 抽取的基础。
- **来源链路**:
  1. **规范化脚本**: `tools/processing/ingestion/normalize_json_sections.py`
     - 将 `data/json` 下的原始 JSON 规范化到 `data/json_structured/*.json`。
     - 每个规范化后的文件结构:
       ```json
       {
         "doc_meta": { ... },
         "sections": [
           {
             "id": "...",
             "clean_text": "...",
             "category_code": "...",
             "extracted_data": { ... }
           }
         ],
         "total_sections": N
       }
       ```
  2. **Section 提取**: `core/processing/kg_writer/json_loader.py` → `extract_sections_from_json()`
     - 当 JSON 中存在 `sections` 数组时:
       - `id` 原样使用。
       - `clean_text` 作为 section 文本，映射到 `section['text']` / `section['clean_text']`。
       - `category_code` 映射到 `section['level2']`（二级分类 code）。
  3. **写入 Neo4j**: `core/processing/kg_writer/writer.py`
     - `_extract_sections_from_json()` 收集所有 Section 结构。
     - `_batch_write_sections()` / `_create_section()` 实际写入 `Section` 节点。

- **最终节点字段（按当前配置，仅保留三项）**:
  - `id`:
    - 来源: `json_structured.sections[i].id`
    - 用途: Section 的主键（唯一约束）。
  - `clean_text`:
    - 来源: `json_structured.sections[i].clean_text`（在写入前最多截断到约 10000 字符）。
    - 用途: 向量索引、实体抽取、SPO 抽取的唯一文本来源。
  - `category_code`:
    - 来源: `json_structured.sections[i].category_code`，在内部对应 `CategoryL2.code`。

- **已移除字段**:
  - `title`、`preview`、`content`、`text` 等字段已按当前要求移除，避免与 `json_structured` 不一致。

### 4. `Company`（公司）

- **来源脚本**:
  - `core/processing/kg_writer/writer.py` → 实体抽取流程。
  - `core/processing/kg_writer/entity_linker.py` → `EntityLinker.link()`
  - `core/processing/extractors/entity_extractor.py` → `EntityRelationshipExtractor`
- **数据源**:
  - 文本: `Section.clean_text`
  - 辅助: 公司/品牌词典 (`CompanyDictionary`)、组织分类器 (`OrganizationClassifier`)
- **生成方式**（概略）:
  1. 对每个 Section，`writer.py` 调用 `EntityRelationshipExtractor.extract_entities(clean_text)`。
  2. 抽取结果中的实体会附带初步类型信息（company/brand/unknown 等）。
  3. `EntityLinker.link()` 对每个实体:
     - 检查名称长度（2–5 字）等过滤条件。
     - 使用 `OrganizationClassifier` + 词典确认类型。
  4. 若最终判定为公司:
     - `MERGE (c:Company {name: $name})`
     - 记录统计信息，并创建 `MENTIONS_COMPANY` / 类型关系等。

- **说明**:
  - 仅当实体显式被识别为公司时才创建 Company 节点，避免“垃圾公司节点”。

### 5. `Brand`（品牌）

- **来源脚本**:
  - 同 Company，由实体抽取与 `EntityLinker` 生成。
- **数据源**:
  - 文本: `Section.clean_text`
  - 词典与规则: 用于过滤通用词、限制长度等。
- **生成方式**:
  - 实体最终类型为 `brand` 且通过过滤:
    - `MERGE (b:Brand {name: $name})`
  - 文档级 `brand_group` 功能已被移除：不再根据文档标题或文件名额外创建 Brand 节点，只使用文本中真实出现的品牌。

### 6. `CompanyType`（公司类型）

- **来源脚本**: `entity_linker.py`
- **数据源**:
  - 实体抽取或分类结果中的类型标签，如 “车企”、“平台”、“媒体”等。
- **生成方式**:
  - 当某 Company/Brand 具备类型 `type_code` 时:
    - `MERGE (ct:CompanyType {code: $type_code})`
    - 在关系部分通过 `BELONGS_TO_TYPE` / `OPERATES_IN_TYPE` 连接。

### 7. `Channel`（传播渠道）

- **来源脚本**: `tools/processing/ingestion/load_case_library_to_neo4j.py` → `GraphSyncer.sync_channels()`
- **数据源**:
  - 公关案例渠道关系 Excel/CSV，例如:
    - `公关案例库_传播渠道关系表.xlsx`
    - 包含“一级传播渠道”、“二级传播渠道”、“三级传播渠道”等列。
- **生成方式**:
  - 对一级/二级/三级渠道列:
    - `MERGE (ch:Channel {name: $name, level: 1/2/3})`
  - 若有渠道大类字段，可能会同时生成 `ChannelCategory` 并建立归属关系（视具体表结构而定）。

### 8. `Industry`（行业）

- **来源脚本**: `load_case_library_to_neo4j.py` → `sync_industries()` + `sync_cases()`
- **数据源**:
  - 行业维度表 / 案例表中的:
    - `一级行业分类`
    - `二级行业分类`
- **生成方式**:
  - 行业层级:
    - `MERGE (i1:Industry {name: $p_name, level: 1})`
    - `MERGE (i2:Industry {name: $c_name, level: 2})`
  - 案例归属:
    - `MERGE (c:PRCase {name: $case_name})`
    - `MERGE (c)-[:IN_INDUSTRY]->(i)`

### 9. `PRCase`（公关/营销案例）

- **来源脚本**: `load_case_library_to_neo4j.py` → `sync_cases()`
- **数据源**:
  - 主案例表: `公关案例库_公关案例库_表格.csv`（或类似）。
  - 用于命名的字段: `企业 / 品牌/项目 / 品牌 / 项目名称 / 案例名称` 中择一。
- **生成方式**:
  - `case_name = clean_str(企业 or 品牌/项目 or 品牌 or 项目名称 or 案例名称)`
  - `MERGE (c:PRCase {name: $case_name})`
  - `SET c += {所有非空字段}`（作为属性）。

### 10. `PRGoal`（传播目标）

- **来源脚本**: `load_case_library_to_neo4j.py` → `sync_goals()`
- **数据源**:
  - 传播目的/目标表中的 “传播目的”、“业务目标”等列。
- **生成方式**:
  - `MERGE (g:PRGoal {name: $goal_name})`
  - 后续通过 `ACHIEVES_GOAL` 连接到 `PRCase`。

### 11. `Concept`（概念）

- **来源脚本**: `core/processing/kg_writer/writer.py` → `_create_spo_relations()`
- **数据源**:
  - 从 SPO 三元组抽取器返回的结果中 `object` 字段。
- **生成方式**:
  1. 对每个三元组 `(subject, predicate, object)`:
     - 若 `object` 既不是 Company，也不符合 Campaign 关键词，则视为通用概念。
  2. 在 Neo4j 中:
     - `MERGE (c:Concept {name: $object})`
  3. 与 Company 之间通过 `SPO_REL` 连接（见关系部分）。

### 12. `Campaign`（活动）

- **来源脚本**: `writer.py` → `_create_spo_relations()`
- **数据源**:
  - SPO 三元组的 `object` 字段。
- **生成方式**:
  - 如果 `object` 文本中包含活动相关关键词:
    - `['campaign', '活动', 'event', 'promotion', '促销', '大促']`
  - 则:
    - `MERGE (c:Campaign {name: $object})`
  - 同样通过 `SPO_REL` 与 Company 连接。

---

## 二、关系类型与生成逻辑

下面列出当前图谱中主要的关系类型、连接的节点类型以及对应的生成逻辑。

### 1. `HAS_SUBCATEGORY`

- **节点对**: `CategoryL1` → `CategoryL2`
- **来源脚本**: `writer.py` → `create_schema()`
- **生成方式**:
  - 遍历 `CATEGORY_SCHEMA` 中每个 `l1_code` 与其 `sub_categories`:
    ```cypher
    MERGE (l1:CategoryL1 {code: $l1_code})
    MERGE (l2:CategoryL2 {code: $l2_code})
    MERGE (l1)-[:HAS_SUBCATEGORY]->(l2)
    ```

### 2. `HAS_SECTION`

- **节点对**: `CategoryL2` → `Section`
- **来源脚本**: `writer.py` → `_batch_write_sections()` / `_create_section()`
- **生成方式**:
  - 每创建/更新一个 Section 后:
    ```cypher
    MATCH (s:Section {id: $section_id})
    MATCH (c2:CategoryL2 {code: $level2_code})
    MERGE (c2)-[:HAS_SECTION]->(s)
    ```

### 3. `USES_CHANNEL`

- **节点对**: `PRCase` → `Channel`
- **来源脚本**: `load_case_library_to_neo4j.py` → `sync_cases()`
- **数据源**:
  - 案例表中的渠道相关列（如“主要平台”、“渠道类型”、“渠道大类”等）。
- **生成方式**:
  - 对每个案例、每个解析出的渠道名称:
    ```cypher
    MERGE (ch:Channel {name: $channel_name})
    MERGE (c:PRCase {name: $case_name})
    MERGE (c)-[:USES_CHANNEL]->(ch)
    ```

### 4. `IN_INDUSTRY`

- **节点对**:
  - `Industry(level2)` → `Industry(level1)`（行业层级）
  - `PRCase` → `Industry`（案例所属行业）
- **来源脚本**: `load_case_library_to_neo4j.py` → `sync_industries()` + `sync_cases()`
- **生成方式**:
  - 行业层级:
    ```cypher
    MERGE (i1:Industry {name: $p_name, level: 1})
    MERGE (i2:Industry {name: $c_name, level: 2})
    MERGE (i2)-[:IN_INDUSTRY]->(i1)
    ```
  - 案例归属:
    ```cypher
    MATCH (c:PRCase {name: $case})
    MERGE (i:Industry {name: $ind})
    MERGE (c)-[:IN_INDUSTRY]->(i)
    ```

### 5. `ACHIEVES_GOAL`

- **节点对**: `PRCase` → `PRGoal`
- **来源脚本**: `load_case_library_to_neo4j.py` → `sync_goals()` / `sync_cases()`
- **生成方式**:
  - 从案例表中读取“传播目标/业务目标”等字段:
    ```cypher
    MERGE (g:PRGoal {name: $goal})
    MATCH (c:PRCase {name: $case})
    MERGE (c)-[:ACHIEVES_GOAL]->(g)
    ```

### 6. `MENTIONS_COMPANY`

- **节点对**: `Section` → `Company`
- **来源脚本**: `entity_linker.py` → `EntityLinker.link()`
- **生成方式**:
  - 对于某个 Section 中识别出的 Company 实体:
    ```cypher
    MERGE (s:Section {id: $section_id})
    MERGE (c:Company {name: $company_name})
    MERGE (s)-[:MENTIONS_COMPANY]->(c)
    ```

### 7. `MENTIONS_BRAND`

- **节点对**: `Section` → `Brand`
- **来源脚本**: 同 `MENTIONS_COMPANY`
- **生成方式**:
  ```cypher
  MERGE (s:Section {id: $section_id})
  MERGE (b:Brand {name: $brand_name})
  MERGE (s)-[:MENTIONS_BRAND]->(b)
  ```

### 8. `BELONGS_TO_BRAND`

- **节点对**:
  - 常见: `Company` → `Brand` 或 `Section` → `Brand`
- **来源脚本**: `entity_linker.py`
- **生成方式**:
  - 当逻辑判断“某公司/某内容属于某品牌”时:
    ```cypher
    MERGE (b:Brand {name: $brand})
    MERGE (c:Company {name: $company})
    MERGE (c)-[:BELONGS_TO_BRAND]->(b)
    ```
  - 具体触发条件依赖 `EntityLinker` 的内部规则（如品牌名出现在公司名中等）。

### 9. `BELONGS_TO_TYPE`

- **节点对**: `Company` / `Brand` → `CompanyType`
- **来源脚本**: `entity_linker.py`
- **生成方式**:
  - 当实体被识别出公司类型时:
    ```cypher
    MERGE (ct:CompanyType {code: $type_code})
    MERGE (c:Company {name: $name})-[:BELONGS_TO_TYPE]->(ct)
    ```

### 10. `OPERATES_IN_TYPE`

- **节点对**: 业务实体（如 `PRCase` 或其他） → `CompanyType`
- **来源脚本**: `entity_linker.py`（视具体实现）
- **生成方式**:
  - 当某实体在某类公司生态中运作时:
    ```cypher
    MERGE (ct:CompanyType {code: $type_code})
    MERGE (x { ... })-[:OPERATES_IN_TYPE]->(ct)
    ```

### 11. `SPO_REL`

- **节点对**: `Company` → (`Company` / `Campaign` / `Concept`)
- **来源脚本**: `writer.py` → `_extract_spo_for_section()` + `_create_spo_relations()`
- **数据源**:
  - 对 `Section.clean_text` 使用 `SPOTripleExtractor` 抽取的三元组:
    - `subject`
    - `predicate`
    - `object`
- **生成方式**（简化流程）:
  1. `_extract_spo_for_section(section)`:
     - 若 `text` 长度足够，调用 LLM 提取：
       ```python
       result = spo_extractor.extract_triples_from_text(
           text,
           chunk_size=200,
           overlap=30,
           verbose=False
       )
       triples = result.get('triples', [])
       ```
  2. `_create_spo_relations(triples, section_id, section)`:
     - 对每个三元组:
       - `subject` → 匹配 Company:
         ```cypher
         MATCH (c:Company)
         WHERE toLower(c.name) = toLower($subject)
         ```
       - `object` → 依次匹配:
         1. Company  
         2. 含活动关键词 → 创建/匹配 `Campaign`  
         3. 否则 → 创建/匹配 `Concept`
       - 创建关系:
         ```cypher
         MATCH (c1:Company {name: $subject})
         MATCH (c2:{Company|Campaign|Concept} {name: $object})
         MERGE (c1)-[r:SPO_REL]->(c2)
         ON CREATE SET r.predicate = $predicate, r.created_at = datetime()
         ```

---

## 三、使用与扩展建议

1. **检查某个节点从哪来**  
   - CSV / Excel → 查 `tools/processing/ingestion/load_case_library_to_neo4j.py`  
   - JSON Section → 查 `normalize_json_sections.py` 与 `json_loader.py` → `writer.py`  
   - LLM 抽取（Company/Brand/Campaign/Concept/SPO_REL）→ 查 `entity_extractor.py`、`entity_linker.py`、`writer.py` 中的 SPO 部分。

2. **想裁剪某类节点或关系**  
   - 可以在对应脚本中注释或删掉相应的 `MERGE` 逻辑，例如:
     - 暂时不需要 `Campaign` 和 `Concept`，可在 `_create_spo_relations()` 中屏蔽相关分支。

3. **想新增字段或关系**  
   - 建议链路为:
     - `normalize_json_sections.py` 中加入字段 →  
       `json_loader.py` 中解析该字段 →  
       `writer.py` 中写入到 Section 或其他节点 →  
       如有需要，在 `EntityLinker` 或 SPO 逻辑中使用。

本文件会随代码变更及时更新，以保持与实际图谱结构一致。若你调整了节点/关系结构，推荐同步修改本文档。 


