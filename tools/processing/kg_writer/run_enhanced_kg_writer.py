#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行增强KG写入器
"""

import sys
import os
from pathlib import Path

# 确保项目根目录在 sys.path 中，支持从任意工作目录运行
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.processing.kg_writer.writer import EnhancedKGWriter


def main():
    """主函数"""
    print("=" * 70)
    print("🚀 增强知识图谱写入器")
    print("=" * 70)
    print("功能：")
    print("  ✅ 创建CategoryL1/CategoryL2分类节点")
    print("  ✅ 创建Section节点并连接到分类")
    print("  ✅ 创建Company节点并建立关系")
    print("  ✅ 集成SPO三元组创建语义关系")
    print("  ✅ 创建Company-CategoryL2汇总关系")
    print("=" * 70)
    
    # 支持命令行参数指定URI
    uri = sys.argv[1] if len(sys.argv) > 1 else None
    
    writer = EnhancedKGWriter(uri=uri)
    
    try:
        # 创建Schema和分类节点
        writer.create_schema()
        
        # 处理JSON文件
        writer.process_json_files()
        
        print("\n✅ 处理完成！")
        print("\n💡 现在可以在Neo4j Browser中查询：")
        print("\n1. 查看某个公司的营销内容（按阶段组织）：")
        print("   MATCH (c:Company {name: 'XXX公司'})-[:INVOLVED_IN_CATEGORY]->(c2:CategoryL2)")
        print("   MATCH (c2)-[:HAS_SECTION]->(s:Section)")
        print("   MATCH (s)-[:MENTIONS_COMPANY]->(c)")
        print("   RETURN c2.label, collect(s.title) LIMIT 10")
        
        print("\n2. 查看同类型公司（相同CategoryL2）：")
        print("   MATCH (c:Company {name: 'XXX公司'})-[:INVOLVED_IN_CATEGORY]->(c2:CategoryL2)")
        print("   MATCH (other:Company)-[:INVOLVED_IN_CATEGORY]->(c2)")
        print("   WHERE other.name <> 'XXX公司'")
        print("   RETURN c2.label, collect(other.name) LIMIT 10")
        
        print("\n3. 查看竞品公司（相似SPO行为）：")
        print("   MATCH (c:Company {name: 'XXX公司'})-[r1:REL]->(obj1)")
        print("   MATCH (other:Company)-[r2:REL]->(obj2)")
        print("   WHERE other.name <> 'XXX公司' AND r1.predicate = r2.predicate")
        print("   RETURN other.name, count(DISTINCT r1.predicate) as similar_actions")
        print("   ORDER BY similar_actions DESC LIMIT 10")
        
    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        writer.close()


if __name__ == "__main__":
    main()


