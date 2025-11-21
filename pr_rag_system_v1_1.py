#!/usr/bin/env python3
"""
公关传播RAG系统 v1.1
采用新版“三级分类 + Section + 实体分型 + SPO”的一键流程与查询入口
"""

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv('.env', override=True)
except Exception:
    pass

# 路径（确保项目根目录在最前面，以便支持绝对导入）
project_root = Path(__file__).parent if Path(__file__).is_file() else Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

sys.path.append('core')
sys.path.append('tools')


class PRRAGSystemV1_1:
    """公关传播RAG系统 v1.1 主类（增强版流程）"""
    
    def __init__(self):
        self.version = "1.1"
        self.system_name = "公关传播RAG系统（增强版）"
        self.description = "三级分类 + Section + 实体分型 + SPO 的增强KG与查询系统"
        
        # 核心文件（增强写入与分类/实体）
        self.core_files = [
            'core/common/pr_category_schema.py',
            'core/processing/extractors/org_classifier.py',
            'core/processing/kg_writer/writer.py',
            'core/processing/extractors/spo_extractor.py',  # 可选，若无API会自动降级
            'core/common/pr_neo4j_env.py'
        ]
        
        # 工具脚本（一键流程、迁移、清理、SPO补齐、查询）
        self.tool_files = [
            'tools/processing/kg_writer/process_enhanced_all.py',
            'tools/processing/kg_writer/migrate_graph_schema.py',
            'tools/processing/kg_writer/clean_pr_chunk_nodes.py',
            'tools/processing/extractors/extract_spo_relations.py',
            'tools/processing/extractors/create_demo_spo_relations.py',
            'tools/querying/graph/query_enhanced_kg.py',
            'tools/querying/pipelines/quick_query_v1_1.py',  # v1.1新架构快速查询
            'tools/querying/graph/neo4j_direct_query_new.py'  # v1.1新架构直接查询
        ]
    
    def show_banner(self):
        banner = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    {self.system_name} v{self.version}                         ║
║                                                                              ║
║  {self.description}                                             ║
║                                                                              ║
║  🎯 核心能力:                                                                ║
║     • L1/L2 分类节点 + Section 切分与归类                                   ║
║     • 组织实体分型（Brand/Company/CompanyType）                              ║
║     • SPO 语义关系（LLM 或 规则演示）                                        ║
║     • 示例查询：阶段内容/相似公司/竞品行为                                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def check_environment(self):
        """检查 .env / 目录 / 必要脚本"""
        print("🔍 检查环境配置...")
        
        # 基础环境变量
        required_env_vars = ['NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD', 'NEO4J_DATABASE']
        missing = [v for v in required_env_vars if not os.getenv(v)]
        if missing:
            print(f"⚠️ 缺少环境变量: {', '.join(missing)}（可在 .env 中设置）")
        
        # 目录
        for d in ['data/json']:
            p = Path(d)
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
                print(f"✅ 创建目录: {d}")
        
        # 核心/工具脚本存在性
        missing_files = []
        for f in (self.core_files + self.tool_files):
            if not Path(f).exists():
                missing_files.append(f)
        if missing_files:
            print(f"⚠️ 以下文件未找到（不一定全部必需）：{', '.join(missing_files)}")
        
        print("✅ 环境检查完成")
        return True
    
    def show_menu(self):
        menu = """
🚀 请选择操作模式（v1.1 增强流程）:

📊 数据处理模式
  1. 一键构建增强图谱（分类/Section/实体 + 可选SPO）
  2. 迁移旧图谱到新Schema
  3. 清理旧 PR_Chunk 节点
  4. 仅补充/生成 SPO（优先 LLM，失败回退演示）
  5. 使用演示规则创建 SPO（不调用API）

🔍 查询模式
  6. 增强RAG对话（GraphRAG/VectorRAG 问答）
  7. 直接Neo4j查询
  8. 快速查询（简易问答 - v1.1新架构）

🧪 测试模式
  9. 功能演示
  10. 完整测试
  11. 系统状态检查

📚 帮助模式
  12. 使用指南
  13. 系统架构

🚪 系统
  14. 退出

请选择 (1-14): """
        return input(menu).strip()
    
    def run_build_all(self):
        """一键构建增强KG（调用 process_enhanced_all.py）"""
        print("🔄 启动一键构建增强图谱...")
        try:
            # 直接以模块方式调用其 main
            import importlib
            m = importlib.import_module('tools.processing.kg_writer.process_enhanced_all')
            if hasattr(m, 'main'):
                # 默认尝试带SPO（若无Key会自动降级/跳过）
                m.main()
            else:
                # 兜底：用子进程方式执行
                os.system(f"{sys.executable} tools/processing/kg_writer/process_enhanced_all.py")
        except Exception as e:
            print(f"❌ 一键构建失败: {e}")
    
    def run_migrate(self):
        """迁移旧图谱"""
        print("🔄 执行图谱Schema迁移（旧 → 新）...")
        try:
            from tools.processing.kg_writer.migrate_graph_schema import migrate_graph_schema
            migrate_graph_schema()
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
    
    def run_clean_chunks(self):
        """清理旧 PR_Chunk"""
        print("🧹 清理旧 PR_Chunk 节点...")
        try:
            from tools.processing.kg_writer.clean_pr_chunk_nodes import clean_pr_chunk_nodes
            clean_pr_chunk_nodes()
        except Exception as e:
            print(f"❌ 清理失败: {e}")
    
    def run_spo_extract(self):
        """补充/生成 SPO（LLM优先）"""
        print("🎯 生成/补充 SPO 关系（LLM 优先）...")
        try:
            from tools.processing.extractors.extract_spo_relations import extract_spo_relations
            extract_spo_relations()
        except Exception as e:
            print(f"❌ LLM 提取失败: {e}")
            print("➡️ 尝试规则演示脚本...")
            try:
                from tools.processing.extractors.create_demo_spo_relations import create_demo_spo_relations
                create_demo_spo_relations()
            except Exception as e2:
                print(f"❌ 规则演示也失败: {e2}")
    
    def run_spo_demo(self):
        """规则演示 SPO"""
        print("🎭 使用规则演示创建 SPO 关系（不调用API）...")
        try:
            from tools.processing.extractors.create_demo_spo_relations import create_demo_spo_relations
            create_demo_spo_relations()
        except Exception as e:
            print(f"❌ 演示SPO失败: {e}")
    
    def run_direct_query(self):
        """运行直接Neo4j查询（命令式控制台）"""
        print("🔍 启动直接Neo4j查询模式...")
        try:
            from tools.querying.graph.neo4j_direct_query_new import main as new_direct_main
            new_direct_main()
        except Exception as e:
            print(f"❌ 直接查询失败: {e}")
    
    def run_quick_query(self):
        """运行快速查询（简易问答）- v1.1新架构"""
        print("⚡ 快速查询（直接输入问题即可获得回答，回车取消）")
        question = input("🧑 问题: ").strip()
        if not question:
            print("ℹ️ 未输入问题，已返回主菜单。")
            return
        try:
            from tools.querying.pipelines.quick_query_v1_1 import quick_query_v1_1
            answer = quick_query_v1_1(question)
            print("\n🤖 回答:\n" + ("-" * 60))
            print(answer)
            print("-" * 60)
        except Exception as e:
            print(f"❌ 快速查询失败: {e}")
    
    def run_demo(self):
        """运行功能演示（v1.1 版本）"""
        print("🎭 启动 v1.1 功能演示...")
        try:
            from examples.rag.demo_enhanced_pr_rag_v1_1 import main as demo_main
            demo_main()
        except Exception as e:
            print(f"❌ 功能演示失败: {e}")
            import traceback
            traceback.print_exc()
    
    def run_tests(self):
        """运行完整测试（v1.1 版本）"""
        print("🧪 启动完整测试（v1.1版本）...")
        try:
            from tests.test_enhanced_pr_rag_v1_1 import main as test_main
            test_main()
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    def check_system_status(self):
        """检查系统状态（Neo4j连接、关键关系/节点统计）"""
        print("📊 检查系统状态...")
        try:
            # 优先使用 pr_neo4j_env 的 graph，如果不可用则使用 neo4j 驱动
            try:
                from core.common.pr_neo4j_env import graph
                result = graph.query("RETURN 1 as test")
                print("✅ Neo4j连接正常")
            except Exception:
                from neo4j import GraphDatabase
                uri = os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
                username = os.getenv('NEO4J_USERNAME', 'neo4j')
                password = os.getenv('NEO4J_PASSWORD', '')
                database = os.getenv('NEO4J_DATABASE', 'neo4j')
                driver = GraphDatabase.driver(uri, auth=(username, password))
                with driver.session(database=database) as session:
                    session.run("RETURN 1 as test").single()
                driver.close()
                print("✅ Neo4j连接正常")
            
            # 关键统计（若图为空会返回0）
            from neo4j import GraphDatabase
            uri = os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
            username = os.getenv('NEO4J_USERNAME', 'neo4j')
            password = os.getenv('NEO4J_PASSWORD', '')
            database = os.getenv('NEO4J_DATABASE', 'neo4j')
            driver = GraphDatabase.driver(uri, auth=(username, password))
            with driver.session(database=database) as session:
                def c(q): 
                    r = session.run(q).single()
                    return r.value() if r else 0
                total_nodes = c("MATCH (n) RETURN count(n)")
                sections = c("MATCH (s:Section) RETURN count(s)")
                companies = c("MATCH (c:Company) RETURN count(c)")
                brands = c("MATCH (b:Brand) RETURN count(b)")
                inv_cat = c("MATCH ()-[r:INVOLVED_IN_CATEGORY]->() RETURN count(r)")
                spo_rel = c("MATCH ()-[r:SPO_REL]->() RETURN count(r)")
            driver.close()
            print(f"✅ 节点总数: {total_nodes} | Section: {sections} | Company: {companies} | Brand: {brands}")
            print(f"✅ 关系统计: INVOLVED_IN_CATEGORY={inv_cat} | SPO_REL={spo_rel}")
        except Exception as e:
            print(f"❌ 状态检查失败: {e}")
    
    def show_usage_guide(self):
        """显示使用指南（简版）"""
        guide = """
📚 使用指南（v1.1）
1) 一键构建：先运行“1 一键构建增强图谱”
2) 若有旧数据：可先“2 迁移旧图谱”或“3 清理 PR_Chunk”
3) 需要 SPO：选择“4 LLM补充SPO”或“5 规则演示SPO”
4) 交互对话：选择“6 增强RAG对话”（GraphRAG/VectorRAG）
5) 直接查询：选择“7 直接Neo4j查询”进行Cypher查询
6) 快速查询：选择“8 快速查询”（基于Section节点，支持GraphRAG和文本匹配）
"""
        print(guide)
    
    def show_system_architecture(self):
        """显示系统架构（简版）"""
        architecture = """
🏗️ v1.1 架构
数据(JSON) → EnhancedKGWriter(分类/Section/实体) → Neo4j
                 ↘ SPO(LMM/规则) → SPO_REL

查询方式：
1. GraphRAG: 通过关系图谱智能查询（推荐）
2. VectorRAG: 通过Section文本匹配查询
3. 直接查询: neo4j_direct_query_new.py（Cypher查询）
4. 快速查询: tools/querying/pipelines/quick_query_v1_1.py（基于Section节点）
"""
        print(architecture)
    def run_chat_rag(self):
        """增强RAG对话（GraphRAG/VectorRAG 问答）"""
        print("🤖 启动增强RAG对话模式（输入 quit/exit/退出 结束）...")
        try:
            from core.querying.pipelines import EnhancedPRRAGSystemV11
            rag_system = EnhancedPRRAGSystemV11()
            
            while True:
                question = input("\n🧑 问题: ").strip()
                if question.lower() in ['quit', 'exit', '退出']:
                    break
                if not question:
                    continue
                use_graph = input("使用GraphRAG? (y/n): ").strip().lower() == 'y'
                answer = rag_system.query(question, use_graph=use_graph)
                print(f"\n🤖 回答:\n{answer}")
        except Exception as e:
            print(f"❌ 增强RAG对话启动失败: {e}")
    
    
    def run(self):
        self.show_banner()
        if not self.check_environment():
            print("❌ 环境检查失败")
            return
        
        while True:
            try:
                choice = self.show_menu()
                if choice == '1':
                    self.run_build_all()
                elif choice == '2':
                    self.run_migrate()
                elif choice == '3':
                    self.run_clean_chunks()
                elif choice == '4':
                    self.run_spo_extract()
                elif choice == '5':
                    self.run_spo_demo()
                elif choice == '6':
                    self.run_chat_rag()
                elif choice == '7':
                    self.run_direct_query()
                elif choice == '8':
                    self.run_quick_query()
                elif choice == '9':
                    self.run_demo()
                elif choice == '10':
                    self.run_tests()
                elif choice == '11':
                    self.check_system_status()
                elif choice == '12':
                    self.show_usage_guide()
                elif choice == '13':
                    self.show_system_architecture()
                elif choice == '14':
                    print("👋 再见！")
                    break
                else:
                    print("❌ 无效选择，请输入 1-14")
                input("\n按回车键继续...")
            except KeyboardInterrupt:
                print("\n\n👋 程序被用户中断，再见！")
                break
            except Exception as e:
                print(f"❌ 运行出错: {e}")
                input("按回车键继续...")


def main():
    try:
        system = PRRAGSystemV1_1()
        system.run()
    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


