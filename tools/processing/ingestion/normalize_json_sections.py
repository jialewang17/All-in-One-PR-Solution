#!/usr/bin/env python3
"""
将松散结构的 JSON 文件转换为标准的 {document_title, sections[]} 结构。
增强版：支持实体预提取和元数据增强，提升写入 Neo4j 的精准度。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.common.pr_category_schema import classify_section, get_category_by_code

# 统一控制切分粒度
MAX_SECTION_LEN = 280


def _strip_noise(text: str) -> str:
    """
    极度精简文本：
    - 移除纯数字/坐标轴/百分比等噪声行
    - 合并多余空白为单空格
    """
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        # 过滤纯数字、百分比、简单坐标/轴数据
        if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?%?", line):
            continue
        if re.fullmatch(r"[0-9]{2,4}[.,/][0-9]{1,4}", line):
            continue
        # 过滤疑似坐标轴标签（如 0100200、X轴、Y轴）
        if re.fullmatch(r"[0-9]{5,}", line) or line.lower() in {"x", "y", "x轴", "y轴"}:
            continue
        lines.append(line)
    compact = " ".join(lines)
    # 合并多余空格
    compact = re.sub(r"\s+", " ", compact).strip()
    return compact


def _is_header_or_footer_line(line: str) -> bool:
    """识别页眉/页脚等噪声行。"""
    lower = line.lower()
    if "prweek.com" in lower:
        return True
    # 纯页码或 Page N / N
    if re.fullmatch(r"[0-9]{1,3}", line):
        return True
    if re.fullmatch(r"page\s*\d+", lower):
        return True
    if re.fullmatch(r"\d+\s*/\s*\d+", line):
        return True
    return False


def _normalize_punct_and_spaces(text: str) -> str:
    """
    清理无意义空格与标点：
    - 合并连续标点为单个（如 "!!" -> "!"）
    - 移除标点前的空格（" ，" -> "，"）
    - 去除首尾多余标点/空格
    """
    if not text:
        return text
    # 合并连续标点
    text = re.sub(r"([，。！？?!,.])\1+", r"\1", text)
    # 去掉标点前的空格
    text = re.sub(r"\s+([，。！？?!,.;；])", r"\1", text)
    # 合并多余空格
    text = re.sub(r"\s+", " ", text)
    # 去掉首尾标点与空格
    text = text.strip(" ，。！？?!,.;；")
    return text


def _denoise_repeated_tokens(text: str) -> str:
    """
    进一步去噪：
    - 连续标点/空格模式（如 '。 。 。'）收敛为单个标点
    - 重复短词（如 'AI AI AI'）收敛为单个
    """
    if not text:
        return text
    # 将“标点+空格”重复的序列压缩为单个标点
    text = re.sub(r"(?:[。！？?!；;，,]\s*){2,}", "。", text)
    # 将重复的短词（1-3字符，含英文/数字）压缩
    text = re.sub(r"\b([A-Za-z0-9]{1,3})\b(?:\s+\1\b){2,}", r"\1", text)
    # 再次合并多余空格
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_text(raw: Any) -> str:
    """去除 Content: 前缀并清理空行。"""
    if raw is None:
        return ""

    if isinstance(raw, list):
        text = "\n".join(str(item) for item in raw)
    else:
        text = str(raw)

    cleaned_lines: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if _is_header_or_footer_line(stripped):
            continue
        lower = stripped.lower()
        if lower.startswith("content:"):
            stripped = stripped[8:].strip()
        cleaned_lines.append(stripped)

    cleaned = "\n".join(cleaned_lines)
    cleaned = _strip_noise(cleaned)
    cleaned = _normalize_punct_and_spaces(cleaned)
    cleaned = _denoise_repeated_tokens(cleaned)
    return cleaned


def infer_document_type(file_stem: str) -> str:
    """从文件名推断文档类型。"""
    stem_lower = file_stem.lower()
    if "case" in stem_lower or "案例" in stem_lower:
        return "case"
    elif "proposal" in stem_lower or "方案" in stem_lower or "竞标" in stem_lower:
        return "proposal"
    elif "report" in stem_lower or "报告" in stem_lower or "方法论" in stem_lower:
        return "report"
    else:
        return "other"


def calculate_quality_score(text: str, entity_count: int = 0) -> float:
    """计算文本质量评分（0-1）。"""
    score = 0.0
    text_len = len(text)
    
    # 长度评分（0-0.6）
    if text_len >= 500:
        score += 0.6
    elif text_len >= 200:
        score += 0.4
    elif text_len >= 50:
        score += 0.2
    
    # 实体评分（0-0.4）
    if entity_count >= 5:
        score += 0.4
    elif entity_count >= 2:
        score += 0.2
    elif entity_count >= 1:
        score += 0.1
    
    return min(score, 1.0)


def extract_brand_from_title(document_title: str, file_stem: str) -> Optional[str]:
    """
    从文档标题或文件名中提取潜在品牌名
    
    规则：
    1. case_品牌名_... 格式
    2. proposal_品牌名_... 格式
    3. report_品牌名_... 格式
    4. framework_品牌名_... 格式
    5. 品牌名_案例/方案/报告 格式
    
    优化：提取核心品牌名，避免提取过长的描述性文本
    
    Args:
        document_title: 文档标题
        file_stem: 文件名（不含扩展名）
    
    Returns:
        提取的品牌名，如果无法提取则返回 None
    """
    # 优先使用文档标题，如果没有则使用文件名
    source_text = document_title or file_stem
    if not source_text:
        return None
    
    # 匹配格式：case_品牌名_... 或 proposal_品牌名_... 等
    patterns = [
        r'^(?:case|proposal|report|framework)_([^_]+?)_',  # case_品牌名_...
        r'^([^_]+?)_(?:案例|方案|报告|方法论|竞标)',  # 品牌名_案例
        r'^([^_]+?)_(?:新零售|体验|数字营销|电商)',  # 品牌名_业务类型
    ]
    
    for pattern in patterns:
        match = re.search(pattern, source_text)
        if match:
            potential_brand = match.group(1).strip()
            
            # 优化：提取核心品牌名（限制长度，避免提取过长的描述性文本）
            # 如果提取的文本过长（>10个字符），尝试提取前几个字符作为品牌名
            if len(potential_brand) > 10:
                # 尝试提取前2-6个字符作为品牌名（常见品牌名长度）
                # 优先提取2-4个字符（如"奥迪"、"小米"）
                for length in [4, 3, 2]:
                    candidate = potential_brand[:length]
                    # 检查是否是有效的品牌名（不是通用词）
                    if _is_valid_brand_name(candidate):
                        return candidate
                # 如果都不行，尝试提取到第一个常见业务关键词之前
                business_keywords = ['新零售', '电商', '数字营销', '体验', '竞标', '方案', '策略']
                for keyword in business_keywords:
                    if keyword in potential_brand:
                        idx = potential_brand.find(keyword)
                        if idx > 0 and idx <= 10:
                            candidate = potential_brand[:idx]
                            if _is_valid_brand_name(candidate):
                                return candidate
            
            # 过滤掉明显不是品牌名的词
            if len(potential_brand) >= 2 and len(potential_brand) <= 10:
                # 排除通用词
                if _is_valid_brand_name(potential_brand):
                    return potential_brand
    
    return None


def _is_valid_brand_name(name: str) -> bool:
    """检查是否是有效的品牌名"""
    if not name or len(name) < 2:
        return False
    
    # 排除通用词
    generic_words = {
        '45家', '品牌', '案例', '方案', '报告', '方法论', '策略', '指南',
        '创新营销', 'AI营销', '内容人工智能', '用户画像构建', '精准营销',
        '2025', '2024', '2023', '2022', '2021',
        '新零售', '电商', '数字营销', '体验', '竞标', '业务'
    }
    if name in generic_words:
        return False
    
    # 排除纯数字
    if re.match(r'^\d+$', name):
        return False
    
    # 排除包含多个业务关键词的文本
    business_keywords = ['新零售', '电商', '数字营销', '体验', '竞标', '方案', '策略', '业务', '模式']
    keyword_count = sum(1 for keyword in business_keywords if keyword in name)
    if keyword_count >= 2:
        return False
    
    return True


def _looks_like_heading(text: str) -> bool:
    """粗略判断小标题/目录行，避免被误并入上一段。"""
    if not text:
        return False
    stripped = text.strip()
    # 很短的行或以冒号收尾，多为标题
    if len(stripped) <= 18 and stripped.endswith(("：", ":")):
        return True
    # 全大写/数字/符号构成的行
    if re.fullmatch(r"[A-Z0-9\s\.\-:：]+", stripped):
        return True
    # 前置序号的短行
    if re.fullmatch(r"[一二三四五六七八九十\dIVXivx\.、\s]{1,6}.*", stripped) and len(stripped) <= 20:
        return True
    # 典型目录词
    keywords = ["目录", "摘要", "参考文献", "附录", "致谢"]
    if any(k in stripped for k in keywords) and len(stripped) <= 20:
        return True
    return False


def _should_merge(prev_text: str, next_text: str, max_len: int = MAX_SECTION_LEN) -> bool:
    """判断两段是否需要缝合，限制合并后长度。"""
    if not prev_text or not next_text:
        return False
    # 若上一段以句末标点结束，则不并
    if re.search(r"[。！？?!；;…]\s*$", prev_text):
        return False
    # 下一段像标题则不并
    if _looks_like_heading(next_text):
        return False
    # 合并后过长则不并
    if len(prev_text) + len(next_text) > max_len:
        return False
    return True


def _split_sentences(text: str) -> List[str]:
    """按句子粗分，保留分隔符，若失败则返回整段。"""
    if not text:
        return [text]
    # 将常见项目符号视作分隔符
    normalized = text.replace("•", "。").replace("·", "。")
    # 基于句末标点分割
    parts = re.split(r"(?<=[。！？!?；;])\s*", normalized)
    parts = [p.strip() for p in parts if p and p.strip()]
    return parts or [text.strip()]


def _split_long_sections(
    sections: List[Dict[str, Any]],
    file_stem: str,
    max_len: int = 600,
    extract_entities: bool = False,
    entity_extractor: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """将过长的 section 按句子切分为不超过 max_len 的块。"""
    if not sections:
        return sections

    split_results: List[Dict[str, Any]] = []

    for section in sections:
        text = section.get("clean_text", "") or ""
        if len(text) <= max_len:
            split_results.append(section)
            continue

        # 句子分割并组装到长度友好的块
        sentences = _split_sentences(text)
        buf: List[str] = []
        buf_len = 0

        def flush_buffer():
            nonlocal buf, buf_len
            if not buf:
                return
            chunk_text = " ".join(buf).strip()
            if not chunk_text:
                buf, buf_len = [], 0
                return

            # 重新分类
            _, level2_code, level2_label = classify_section(title="", content=chunk_text)
            new_section = {
                "id": section["id"],  # 占位，稍后统一重排
                "clean_text": chunk_text,
                # category_code 使用二级分类名称（若有），否则用 code
                "category_code": level2_label or level2_code,
                "extracted_data": section.get("extracted_data", {"companies": [], "brands": [], "keywords": []}),
            }

            # 按需重新抽取实体
            if extract_entities and entity_extractor:
                try:
                    ents = entity_extractor.extract_entities(chunk_text)
                    if ents:
                        new_section["extracted_data"] = {
                            "companies": [
                                e.get("name")
                                for e in ents
                                if isinstance(e, dict) and e.get("type", "").lower() == "company" and e.get("name")
                            ],
                            "brands": [
                                e.get("name")
                                for e in ents
                                if isinstance(e, dict) and e.get("type", "").lower() == "brand" and e.get("name")
                            ],
                            "keywords": [],
                        }
                except Exception:
                    pass

            split_results.append(new_section)
            buf, buf_len = [], 0

        for sent in sentences:
            # 若单句仍超长，做硬切片
            if len(sent) > max_len:
                # 先冲掉缓冲
                flush_buffer()
                for i in range(0, len(sent), max_len):
                    part = sent[i : i + max_len].strip()
                    if part:
                        buf = [part]
                        buf_len = len(part)
                        flush_buffer()
                continue

            if buf_len + len(sent) + 1 <= max_len:
                buf.append(sent)
                buf_len += len(sent) + 1
            else:
                flush_buffer()
                buf.append(sent)
                buf_len = len(sent)

        flush_buffer()

    # 重新编号
    for idx, sec in enumerate(split_results):
        sec["id"] = f"{file_stem}#{idx + 1:04d}"

    return split_results


def _merge_fragments(
    sections: List[Dict[str, Any]],
    file_stem: str,
    extract_entities: bool = False,
    entity_extractor: Optional[Any] = None,
    max_len: int = MAX_SECTION_LEN,
) -> List[Dict[str, Any]]:
    """按规则合并碎片段落，并重新编号。"""
    if not sections:
        return sections

    merged: List[Dict[str, Any]] = []
    current = sections[0].copy()

    for nxt in sections[1:]:
        if _should_merge(current["clean_text"], nxt["clean_text"], max_len=max_len):
            current["clean_text"] = f"{current['clean_text']} {nxt['clean_text']}".strip()
            # 重新分类
            _, level2_code, level2_label = classify_section(title="", content=current["clean_text"])
            current["category_code"] = level2_label or level2_code
            # 合并实体或重新抽取
            if extract_entities and entity_extractor:
                try:
                    ents = entity_extractor.extract_entities(current["clean_text"])
                    if ents:
                        current["extracted_data"] = {
                            "companies": [
                                e.get("name")
                                for e in ents
                                if isinstance(e, dict) and e.get("type", "").lower() == "company" and e.get("name")
                            ],
                            "brands": [
                                e.get("name")
                                for e in ents
                                if isinstance(e, dict) and e.get("type", "").lower() == "brand" and e.get("name")
                            ],
                            "keywords": [],
                        }
                except Exception:
                    pass
            else:
                # 简单合并已有实体列表去重
                companies = set(current["extracted_data"].get("companies", [])) | set(
                    nxt.get("extracted_data", {}).get("companies", [])
                )
                brands = set(current["extracted_data"].get("brands", [])) | set(
                    nxt.get("extracted_data", {}).get("brands", [])
                )
                current["extracted_data"] = {
                    "companies": sorted(companies),
                    "brands": sorted(brands),
                    "keywords": [],
                }
        else:
            merged.append(current)
            current = nxt.copy()

    merged.append(current)

    # 重新编号，保证 id 连续
    for idx, sec in enumerate(merged):
        sec["id"] = f"{file_stem}#{idx + 1:04d}"

    return merged


def normalize_payload(
    data: Dict[str, Any], 
    file_stem: str,
    extract_entities: bool = False,
    entity_extractor: Optional[Any] = None
) -> Dict[str, Any]:
    """
    将任意键值结构转为标准 sections 列表（重构版）：
    - doc_meta: 统一存储标题/类型/来源/品牌组
    - sections: 使用 clean_text、category_code、extracted_data
    """
    doc_title = (
        data.get("document_title")
        or data.get("title")
        or data.get("doc_title")
        or file_stem
    )
    
    doc_type = infer_document_type(file_stem)
    doc_source = data.get("source") or file_stem
    
    sections: List[Dict[str, Any]] = []

    for idx, (key, value) in enumerate(data.items()):
        if key in {"document_title", "sections"}:
            continue

        if isinstance(value, dict):
            text_source = (
                value.get("text")
                or value.get("content")
                or value.get("Content")
                or ""
            )
        else:
            text_source = value

        cleaned = clean_text(text_source)
        if not cleaned:
            continue

        # 分类信息（使用 CategoryL2 名称，若不可用则退回 code）
        _, level2_code, level2_label = classify_section(title=key or "", content=cleaned)
        category_code = level2_label or level2_code
        
        extracted_data = {
            "companies": [],
            "brands": [],
            "keywords": []
        }

        # 预提取实体（如果启用）
        if extract_entities and entity_extractor and cleaned:
            try:
                entities_list = entity_extractor.extract_entities(cleaned)
                if entities_list:
                    extracted_data["companies"] = [
                        e.get("name") for e in entities_list
                        if isinstance(e, dict) and e.get("type", "").lower() == "company" and e.get("name")
                    ]
                    extracted_data["brands"] = [
                        e.get("name") for e in entities_list
                        if isinstance(e, dict) and e.get("type", "").lower() == "brand" and e.get("name")
                    ]
            except Exception:
                # 实体提取失败不影响主流程
                pass
        
        section = {
            "id": f"{file_stem}#{idx + 1:04d}",
            "clean_text": cleaned,
            "category_code": category_code,
            "extracted_data": extracted_data
        }
        
        sections.append(section)

    # 段落缝合，避免碎片节点
    sections = _merge_fragments(
        sections,
        file_stem=file_stem,
        extract_entities=extract_entities,
        entity_extractor=entity_extractor,
        max_len=MAX_SECTION_LEN,
    )

    # 切分过长段落，避免超长 section
    sections = _split_long_sections(
        sections,
        file_stem=file_stem,
        max_len=MAX_SECTION_LEN,
        extract_entities=extract_entities,
        entity_extractor=entity_extractor,
    )

    # 提取品牌名（从文档标题或文件名）作为 brand_group
    doc_meta = {
        "title": doc_title,
        "type": doc_type,
        "source": doc_source
    }
    
    result = {
        "doc_meta": doc_meta,
        "sections": sections,
        "total_sections": len(sections),
    }
    
    return result


def process_file(
    source_path: Path,
    destination_path: Path,
    overwrite: bool = True,
    extract_entities: bool = False,
    entity_extractor: Optional[Any] = None,
) -> bool:
    """对单个 JSON 文件执行规范化。"""
    try:
        with open(source_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:  # pragma: no cover - 防御性
        print(f"❌ 无法读取 {source_path.name}: {exc}")
        return False

    if not isinstance(data, dict):
        print(f"⚠️ 跳过 {source_path.name}：不是 dict 结构")
        return False

    if "sections" in data and isinstance(data["sections"], list):
        # 如果已有 sections，检查是否需要重新处理（例如添加实体）
        if extract_entities and not any(
            s.get("entities") for s in data["sections"] if isinstance(s, dict)
        ):
            # 有 sections 但缺少实体，允许重新处理
            pass
        else:
            print(f"ℹ️ 已有 sections 字段，跳过 {source_path.name}")
            return False

    normalized = normalize_payload(
        data, 
        source_path.stem,
        extract_entities=extract_entities,
        entity_extractor=entity_extractor
    )
    if not normalized["sections"]:
        print(f"⚠️ {source_path.name} 未生成任何 section，已跳过")
        return False

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    if destination_path.exists() and not overwrite:
        print(f"⚠️ 目标文件已存在，默认会覆盖；如需保留旧文件请使用 --no-overwrite: {destination_path}")
        return False

    with open(destination_path, "w", encoding="utf-8") as fh:
        json.dump(normalized, fh, ensure_ascii=False, indent=2)

    # 统计信息
    total_entities = sum(
        (
            len(s.get("entities", {}).get("companies", [])) +
            len(s.get("entities", {}).get("brands", []))
        )
        for s in normalized["sections"] 
        if isinstance(s, dict)
    )
    
    print(f"✅ {source_path.name} → {destination_path}")
    print(f"   📊 {len(normalized['sections'])} sections, {total_entities} entities")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="将 data/json 下的松散 JSON 转换为标准 sections 结构（增强版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础转换（不提取实体，快速）
  python normalize_json_sections.py --input-dir data/json --output-dir data/json_structured

  # 启用实体预提取（更精准，但较慢）
  python normalize_json_sections.py --extract-entities --input-dir data/json

  # 覆盖已存在的文件
  python normalize_json_sections.py --overwrite --extract-entities
        """
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/json",
        help="待处理 JSON 目录（默认 data/json）",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/json_structured",
        help="输出目录（默认 data/json_structured）",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="默认覆盖已存在的输出文件；若需保留旧文件请使用本参数",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="直接覆盖输入目录下的原文件（谨慎使用）",
    )
    parser.add_argument(
        "--extract-entities",
        action="store_true",
        help="预提取实体信息（需要 API key，较慢但更精准）",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"❌ 输入目录不存在: {input_dir}")
        return

    output_dir = input_dir if args.in_place else Path(args.output_dir)
    files = sorted(input_dir.glob("*.json"))
    if not files:
        print(f"⚠️ {input_dir} 未找到 JSON 文件")
        return

    # 初始化实体提取器（如果启用）
    entity_extractor = None
    if args.extract_entities:
        try:
            from core.processing.extractors.entity_extractor import EntityRelationshipExtractor
            print("🔄 正在初始化实体提取器...")
            entity_extractor = EntityRelationshipExtractor()
            print("✅ 实体提取器初始化成功")
        except Exception as e:
            print(f"⚠️ 实体提取器初始化失败: {e}")
            print("   将跳过实体预提取，仅进行基础规范化")
            entity_extractor = None

    converted = 0
    total_sections = 0
    total_entities = 0
    
    for json_file in files:
        dest_path = output_dir / json_file.name
        if process_file(
            json_file, 
            dest_path, 
            overwrite=(not args.no_overwrite) or args.in_place,
            extract_entities=args.extract_entities and entity_extractor is not None,
            entity_extractor=entity_extractor
        ):
            converted += 1
            # 统计已处理文件的信息
            try:
                with open(dest_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    sections = data.get("sections", [])
                    total_sections += len(sections)
                    total_entities += sum(
                        s.get("entity_count", 0) 
                        for s in sections 
                        if isinstance(s, dict)
                    )
            except:
                pass

    print(f"\n🎯 完成：共规范化 {converted} 个文件")
    if converted > 0:
        print(f"   📊 总计 {total_sections} 个 sections")
        if args.extract_entities:
            print(f"   🔍 总计 {total_entities} 个实体")


if __name__ == "__main__":
    main()

