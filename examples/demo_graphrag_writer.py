#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GraphRAG 写入器演示脚本
展示如何使用基于 GraphRAG 逻辑的智能写入器
"""

import os
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 加载环境变量
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
    """演示 GraphRAG 写入器的使用"""
    print("=" * 70)
    print("🚀 GraphRAG 写入器演示")
    print("=" * 70)
    print()
    print("本演示展示如何使用基于 GraphRAG 逻辑的智能知识图谱写入器。")
    print("主要特性：")
    print("1. 使用 LLM 生成 Cypher 写入语句")
    print("2. 利用已有图谱结构进行智能关联")
    print("3. 自动检查并复用已有实体")
    print()
    print("=" * 70)
    
    try:
        from core.processing.kg_writer.graphrag_writer import GraphRAGWriter
        
        # 初始化写入器
        print("📦 初始化 GraphRAG 写入器...")
        writer = GraphRAGWriter(
            use_llm_for_cypher=True,  # 启用LLM生成Cypher
            use_graph_context=True   # 启用图谱上下文
        )
        print("✅ 初始化完成")
        print()
        
        # 创建Schema
        print("🏗️ 创建知识图谱Schema...")
        writer.create_schema()
        print("✅ Schema创建完成")
        print()
        
        # 检查JSON文件
        json_dir = "data/json_structured"
        json_path = Path(json_dir)
        
        if not json_path.exists():
            print(f"⚠️ JSON目录不存在: {json_dir}")
            print("💡 请先运行预处理流程生成JSON文件")
            return
        
        json_files = list(json_path.glob("*.json"))
        if not json_files:
            print(f"⚠️ 未找到JSON文件: {json_dir}")
            print("💡 请先运行预处理流程生成JSON文件")
            return
        
        print(f"📁 找到 {len(json_files)} 个JSON文件")
        print()
        
        # 询问是否继续
        user_input = input("是否开始处理？(y/N): ").strip().lower()
        if user_input != 'y':
            print("❌ 用户取消操作")
            return
        
        # 处理JSON文件（仅处理前3个作为演示）
        demo_files = json_files[:3]
        print(f"📄 演示模式：处理前 {len(demo_files)} 个文件")
        print()
        
        for json_file in demo_files:
            print(f"📄 处理: {json_file.name}")
            try:
                writer._process_single_json_with_graphrag(json_file)
                print(f"✅ {json_file.name} 处理完成")
            except Exception as e:
                print(f"❌ {json_file.name} 处理失败: {e}")
            print()
        
        # 显示统计信息
        writer._show_statistics()
        
        print()
        print("=" * 70)
        print("✅ 演示完成！")
        print("=" * 70)
        print()
        print("💡 完整使用方式：")
        print("   python tools/processing/kg_writer/run_graphrag_writer.py")
        print()
        print("💡 在主流程中使用：")
        print("   python pr_process_all_v1_1.py --kg-use-graphrag")
        print()
        
        # 关闭连接
        writer.close()
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

