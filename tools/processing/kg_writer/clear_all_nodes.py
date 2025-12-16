#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空 Neo4j 中的所有节点和关系

⚠️ 警告：此脚本会删除 Neo4j 数据库中的所有节点和关系，请谨慎使用！
建议在执行前先备份数据库。
"""

import os
import sys
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('.env', override=True)

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

uri = os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
username = os.getenv('NEO4J_USERNAME', 'neo4j')
password = os.getenv('NEO4J_PASSWORD', '')
database = os.getenv('NEO4J_DATABASE', 'neo4j')


def get_node_counts(session):
    """获取各类型节点的数量"""
    node_types = [
        'Section', 'Company', 'Brand', 'CategoryL1', 'CategoryL2', 
        'CompanyType', 'Campaign', 'Concept', 'PR_Chunk',
        'ChannelCategory', 'Channel', 'PRGoal', 'Industry', 'PRCase',
        'MethodologyRule'
    ]
    
    counts = {}
    for node_type in node_types:
        try:
            result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
            count = result.single()['count']
            if count > 0:
                counts[node_type] = count
        except Exception as e:
            # 如果节点类型不存在，忽略错误
            pass
    
    return counts


def get_relationship_counts(session):
    """获取关系的数量"""
    try:
        result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
        return result.single()['count']
    except Exception:
        return 0


def clear_all_nodes(confirm: bool = False):
    """
    清空 Neo4j 中的所有节点和关系
    
    Args:
        confirm: 如果为 False，会要求用户确认
    """
    print("=" * 70)
    print("⚠️  清空 Neo4j 数据库")
    print("=" * 70)
    print("\n⚠️  警告：此操作将删除 Neo4j 中的所有节点和关系！")
    print("   建议在执行前先备份数据库。")
    print("=" * 70)
    
    if not confirm:
        user_input = input("\n确认要清空所有节点吗？(输入 'YES' 确认): ").strip()
        if user_input != 'YES':
            print("❌ 操作已取消")
            return False
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session(database=database) as session:
            # 1. 显示当前节点统计
            print("\n📊 当前节点统计:")
            node_counts = get_node_counts(session)
            if node_counts:
                for node_type, count in node_counts.items():
                    print(f"  - {node_type}: {count} 个")
            else:
                print("  (无节点)")
            
            # 2. 显示关系统计
            rel_count = get_relationship_counts(session)
            print(f"\n📊 当前关系统计: {rel_count} 个")
            
            if not node_counts and rel_count == 0:
                print("\n✅ 数据库已经是空的，无需清理")
                return True
            
            # 3. 确认删除
            if not confirm:
                print("\n" + "=" * 70)
                user_input = input("最后确认：真的要删除以上所有节点和关系吗？(输入 'DELETE' 确认): ").strip()
                if user_input != 'DELETE':
                    print("❌ 操作已取消")
                    return False
            
            # 4. 执行删除
            print("\n🗑️  开始删除...")
            
            # 删除所有关系
            if rel_count > 0:
                print("  删除所有关系...")
                result = session.run("MATCH ()-[r]->() DELETE r")
                print(f"  ✅ 已删除所有关系")
            
            # 删除所有节点
            print("  删除所有节点...")
            result = session.run("MATCH (n) DETACH DELETE n RETURN count(n) as deleted_count")
            deleted = result.single()['deleted_count']
            print(f"  ✅ 已删除 {deleted} 个节点")
            
            # 可选：删除所有约束和索引（清理 Schema）
            print("\n🔧 清理约束和索引...")
            try:
                # 删除所有约束
                constraints_result = session.run("SHOW CONSTRAINTS")
                constraints = list(constraints_result)
                if constraints:
                    for constraint in constraints:
                        constraint_name = constraint.get('name') or constraint.get('id')
                        if constraint_name:
                            try:
                                session.run(f"DROP CONSTRAINT {constraint_name} IF EXISTS")
                            except Exception:
                                pass
                    print(f"  ✅ 已清理 {len(constraints)} 个约束")
                else:
                    print("  ℹ️  无约束需要清理")
                
                # 删除所有索引（包括向量索引）
                indexes_result = session.run("SHOW INDEXES")
                indexes = list(indexes_result)
                if indexes:
                    for index in indexes:
                        index_name = index.get('name') or index.get('id')
                        if index_name:
                            try:
                                session.run(f"DROP INDEX {index_name} IF EXISTS")
                            except Exception:
                                pass
                    print(f"  ✅ 已清理 {len(indexes)} 个索引")
                else:
                    print("  ℹ️  无索引需要清理")
            except Exception as e:
                print(f"  ⚠️  清理约束和索引时出现警告: {e}")
                print("  ℹ️  这不会影响节点删除，可以忽略")
            
            # 5. 验证
            print("\n🔍 验证清理结果...")
            remaining_nodes = get_node_counts(session)
            remaining_rels = get_relationship_counts(session)
            
            if not remaining_nodes and remaining_rels == 0:
                print("✅ 数据库已完全清空")
                return True
            else:
                print("⚠️  仍有残留数据:")
                if remaining_nodes:
                    for node_type, count in remaining_nodes.items():
                        print(f"  - {node_type}: {count} 个")
                if remaining_rels > 0:
                    print(f"  - 关系: {remaining_rels} 个")
                return False
        
    except Exception as e:
        print(f"❌ 清空失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        driver.close()


def clear_specific_node_types(node_types: list, confirm: bool = False):
    """
    清空指定类型的节点
    
    Args:
        node_types: 要清空的节点类型列表，如 ['Section', 'Company', 'Brand']
        confirm: 如果为 False，会要求用户确认
    """
    print("=" * 70)
    print(f"🗑️  清空指定节点类型: {', '.join(node_types)}")
    print("=" * 70)
    
    if not confirm:
        user_input = input(f"\n确认要清空这些节点类型吗？(输入 'YES' 确认): ").strip()
        if user_input != 'YES':
            print("❌ 操作已取消")
            return False
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session(database=database) as session:
            total_deleted = 0
            
            for node_type in node_types:
                # 检查节点数量
                result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                count = result.single()['count']
                
                if count == 0:
                    print(f"  ⏭️  {node_type}: 0 个（跳过）")
                    continue
                
                # 删除节点（DETACH DELETE 会自动删除相关关系）
                result = session.run(f"MATCH (n:{node_type}) DETACH DELETE n RETURN count(n) as deleted_count")
                deleted = result.single()['deleted_count']
                total_deleted += deleted
                print(f"  ✅ {node_type}: 删除了 {deleted} 个节点")
            
            print(f"\n✅ 总共删除了 {total_deleted} 个节点")
            return True
        
    except Exception as e:
        print(f"❌ 清空失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        driver.close()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="清空 Neo4j 中的节点",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 清空所有节点（需要确认）
  python clear_all_nodes.py

  # 清空所有节点（跳过确认，危险！）
  python clear_all_nodes.py --yes

  # 清空指定节点类型
  python clear_all_nodes.py --types Section Company Brand

  # 清空指定节点类型（跳过确认）
  python clear_all_nodes.py --types Section Company Brand --yes
        """
    )
    
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='跳过确认，直接执行（危险！）'
    )
    
    parser.add_argument(
        '--types', '-t',
        nargs='+',
        help='指定要清空的节点类型（如: Section Company Brand）'
    )
    
    args = parser.parse_args()
    
    if args.types:
        # 清空指定类型
        clear_specific_node_types(args.types, confirm=args.yes)
    else:
        # 清空所有节点
        clear_all_nodes(confirm=args.yes)


if __name__ == "__main__":
    main()

