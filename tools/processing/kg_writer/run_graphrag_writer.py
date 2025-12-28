#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 GraphRAG 逻辑的知识图谱写入工具
"""

import os
import sys
import argparse
from pathlib import Path

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_env():
    """加载环境变量"""
    try:
        from dotenv import load_dotenv
        load_dotenv('.env', override=True)
    except Exception:
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="使用 GraphRAG 逻辑写入知识图谱"
    )
    parser.add_argument(
        "--json-dir",
        default="data/json_structured",
        help="输入JSON目录（默认 data/json_structured）"
    )
    parser.add_argument(
        "--uri",
        default=None,
        help="Neo4j URI（覆盖.env配置）"
    )
    parser.add_argument(
        "--no-llm-cypher",
        action="store_true",
        help="禁用使用LLM生成Cypher语句（使用标准写入）"
    )
    parser.add_argument(
        "--no-graph-context",
        action="store_true",
        help="禁用利用已有图谱结构进行智能关联"
    )
    
    args = parser.parse_args()
    
    # 加载环境变量
    load_env()
    
    print("=" * 70)
    print("🚀 GraphRAG 知识图谱写入器")
    print("=" * 70)
    print(f"📁 JSON目录: {args.json_dir}")
    print(f"🔧 使用LLM生成Cypher: {not args.no_llm_cypher}")
    print(f"🔧 利用图谱上下文: {not args.no_graph_context}")
    print("=" * 70)
    
    try:
        from core.processing.kg_writer.graphrag_writer import GraphRAGWriter
        
        writer = GraphRAGWriter(
            uri=args.uri,
            use_llm_for_cypher=not args.no_llm_cypher,
            use_graph_context=not args.no_graph_context
        )
        
        try:
            # 创建Schema
            writer.create_schema()
            
            # 处理JSON文件
            writer.process_json_files(
                json_dir=args.json_dir,
                resume=False
            )
            
            print("\n✅ GraphRAG写入完成！")
            print("💡 可以使用以下查询验证:")
            print("   python tools/querying/graph/query_enhanced_kg.py company \"公司名\"")
            
        finally:
            writer.close()
            
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

