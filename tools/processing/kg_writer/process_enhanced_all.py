#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键执行增强版PR-KG流程（三级分类 + 实体分类 + SPO）

步骤（可选开关）：
1) 迁移/清理旧图谱（--migrate / --clean-chunks）
2) 创建Schema与分类节点 + 写入Section/实体关系（必须）
3) 生成SPO关系（默认尝试LLM；也可 --use-demo-spo 基于规则创建演示SPO）
4) 结束后给出查询脚本提示
"""

import os
import sys
import argparse
from pathlib import Path

# 确保项目根目录在 sys.path 中，支持从任意工作目录运行
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv('.env', override=True)
    except Exception:
        # 兼容无dotenv场景
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()


def step_migrate_schema():
    try:
        from tools.processing.kg_writer.migrate_graph_schema import migrate_graph_schema
        migrate_graph_schema()
    except Exception as e:
        print(f"❌ 迁移流程失败: {e}")


def step_clean_chunks():
    try:
        from tools.processing.kg_writer.clean_pr_chunk_nodes import clean_pr_chunk_nodes
        clean_pr_chunk_nodes()
    except Exception as e:
        print(f"❌ 清理PR_Chunk失败: {e}")


def step_write_kg(json_dir: str = "data/json", uri: str | None = None,
                  use_spo: bool = True, use_entity_extractor: bool = True):
    from core.processing.kg_writer.writer import EnhancedKGWriter

    writer = EnhancedKGWriter(
        uri=uri,
        use_spo=use_spo,
        use_entity_extractor=use_entity_extractor
    )
    try:
        writer.create_schema()
        writer.process_json_files(json_dir=json_dir)
    finally:
        writer.close()


def step_extract_spo_relations(prefer_demo: bool = False):
    """
    - 默认优先调用 LLM 提取（tools.processing.extractors.extract_spo_relations）
    - 如果 prefer_demo=True，或LLM不可用，则降级为演示脚本（tools.processing.extractors.create_demo_spo_relations）
    """
    if prefer_demo:
        try:
            from tools.processing.extractors.create_demo_spo_relations import create_demo_spo_relations
            create_demo_spo_relations()
            return
        except Exception as e:
            print(f"❌ 演示SPO关系创建失败: {e}")
            return

    # 先尝试真实提取
    try:
        from tools.processing.extractors.extract_spo_relations import extract_spo_relations
        extract_spo_relations()
        return
    except Exception as e:
        print(f"⚠️ LLM提取SPO失败，将尝试演示脚本: {e}")
        try:
            from tools.processing.extractors.create_demo_spo_relations import create_demo_spo_relations
            create_demo_spo_relations()
        except Exception as e2:
            print(f"❌ 演示SPO关系创建失败: {e2}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="一键运行增强版PR-KG流程"
    )
    parser.add_argument("--migrate", action="store_true",
                        help="运行Schema迁移（清理旧标签/关系、合并PR_Chunk到Section等）")
    parser.add_argument("--clean-chunks", action="store_true",
                        help="删除所有PR_Chunk节点及其关系")
    parser.add_argument("--json-dir", default="data/json",
                        help="输入JSON目录（默认 data/json）")
    parser.add_argument("--uri", default=None,
                        help="Neo4j URI（覆盖.env配置）")
    parser.add_argument("--no-spo", action="store_true",
                        help="跳过SPO关系生成步骤")
    parser.add_argument("--use-demo-spo", action="store_true",
                        help="使用规则演示脚本创建SPO（不调用LLM）")
    parser.add_argument("--no-entity-extractor", action="store_true",
                        help="写入阶段禁用实体提取器")
    return parser.parse_args()


def main():
    print("=" * 70)
    print("🚀 增强版PR-KG一键流程（分类 + 实体 + SPO）")
    print("=" * 70)

    load_env()
    args = parse_args()

    # 迁移/清理（可选）
    if args.migrate:
        print("\n🔄 执行图谱Schema迁移...")
        step_migrate_schema()

    if args.clean_chunks:
        print("\n🧹 清理PR_Chunk节点...")
        step_clean_chunks()

    # 写入分类结构与Section/实体
    print("\n🏗️ 写入分类结构与Section/实体...")
    step_write_kg(
        json_dir=args.json_dir,
        uri=args.uri,
        use_spo=not args.no_spo,  # 写入阶段自带的SPO尝试（可失败不影响）
        use_entity_extractor=not args.no_entity_extractor
    )

    # 额外SPO补充（可选）
    if not args.no_spo:
        print("\n🎯 生成/补充SPO关系...")
        step_extract_spo_relations(prefer_demo=args.use_demo_spo)
    else:
        print("\nℹ️ 已跳过SPO关系生成")

    print("\n✅ 流程完成！你可以使用以下查询脚本验证：")
    print("   python tools/querying/graph/query_enhanced_kg.py company \"奥迪\"")
    print("   python tools/querying/graph/query_enhanced_kg.py company_stage \"奥迪\" ecommerce.sales_strategy")
    print("   python tools/querying/graph/query_enhanced_kg.py stage ecommerce.sales_strategy")
    print("=" * 70)


if __name__ == "__main__":
    main()


