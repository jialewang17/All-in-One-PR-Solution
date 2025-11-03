#!/usr/bin/env python3
"""
公关传播RAG系统 v1.0
增强版知识图谱RAG系统 - 主入口程序
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('.env', override=True)

class PRRAGSystemV1:
    """公关传播RAG系统 v1.0 主类"""
    
    def __init__(self):
        self.version = "1.0"
        self.system_name = "公关传播RAG系统"
        self.description = "基于Neo4j的增强版公关传播知识图谱RAG系统"
        
        # 核心模块路径
        self.core_modules = {
            'schema': 'core/pr_enhanced_schema.py',
            'extractor': 'core/pr_entity_extractor.py', 
            'integration': 'core/pr_enhanced_neo4j_integration.py',
            'rag': 'core/pr_enhanced_rag.py',
            'preprocessing': 'core/pr_multi_format_preprocessing.py',
            'chunking': 'core/pr_chunking.py',
            'neo4j_env': 'core/pr_neo4j_env.py'
        }
        
        # 工具模块路径
        self.tool_modules = {
            'chunk_editor': 'tools/chunk_editor.py',
            'incremental': 'tools/incremental_processor.py',
            'direct_query': 'tools/neo4j_direct_query.py',
            'ask_pr': 'tools/ask_pr.py'
        }
        
        # 测试和演示模块
        self.demo_modules = {
            'demo_enhanced': 'demos/demo_enhanced_pr_rag.py',
            'test_enhanced': 'demos/test_enhanced_pr_rag.py',
            'quick_query': 'tools/quick_query.py'
        }

    def show_banner(self):
        """显示系统横幅"""
        banner = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          {self.system_name} v{self.version}                          ║
║                                                                              ║
║  {self.description}        ║
║                                                                              ║
║  🎯 核心功能:                                                               ║
║     • 智能实体识别 (品牌、企业、媒体、活动等)                                ║
║     • 关系提取 (合作、竞争、媒体投放等)                                      ║
║     • 增强RAG查询 (GraphRAG + VectorRAG)                                    ║
║     • 多格式文档处理 (PDF、Word、Excel、PPT等)                              ║
║     • 增量处理 (只处理新文件)                                                ║
║     • Chunk编辑 (人工优化数据)                                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)

    def check_environment(self):
        """检查环境配置"""
        print("🔍 检查环境配置...")
        
        # 检查必要的环境变量
        required_env_vars = ['NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD', 'NEO4J_DATABASE']
        missing_vars = []
        
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ 缺少环境变量: {', '.join(missing_vars)}")
            print("请检查 .env 文件配置")
            return False
        
        # 检查核心文件
        missing_files = []
        for module_name, file_path in self.core_modules.items():
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ 缺少核心文件: {', '.join(missing_files)}")
            return False
        
        # 检查数据目录
        data_dirs = ['data/raw', 'data/cleaned', 'data/json', 'data/chunks']
        for dir_path in data_dirs:
            if not Path(dir_path).exists():
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                print(f"✅ 创建目录: {dir_path}")
        
        print("✅ 环境配置检查完成")
        return True

    def show_main_menu(self):
        """显示主菜单"""
        menu = """
🚀 请选择操作模式:

📊 数据处理模式:
  1. 完整处理 - 处理所有文件 (预处理→JSON→分块→Neo4j集成)
  2. 增量处理 - 只处理新文件
  3. Chunk编辑 - 编辑已有chunks的元数据
  4. 上传Chunks到Neo4j - 将已有chunks数据上传到Neo4j数据库

🔍 查询模式:
  5. 增强RAG查询 - 使用新的实体关系系统
  6. 直接Neo4j查询 - 绕过预处理直接查询
  7. 快速查询 - 简单问答模式

🧪 测试模式:
  8. 功能演示 - 展示系统功能
  9. 完整测试 - 运行所有测试
  10. 系统状态检查

📚 帮助模式:
  11. 查看使用指南
  12. 查看系统架构
  13. 退出系统

请选择 (1-13): """
        
        return input(menu).strip()

    def run_full_processing(self):
        """运行完整处理"""
        print("🔄 启动完整处理模式...")
        try:
            from pr_process_all import main as process_main
            process_main()
        except Exception as e:
            print(f"❌ 完整处理失败: {e}")

    def run_incremental_processing(self):
        """运行增量处理"""
        print("🔄 启动增量处理模式...")
        try:
            from tools.incremental_processor import IncrementalProcessor
            processor = IncrementalProcessor()
            processor.run()
        except Exception as e:
            print(f"❌ 增量处理失败: {e}")

    def run_upload_chunks_to_neo4j(self):
        """运行上传Chunks到Neo4j"""
        print("📤 启动Chunks上传到Neo4j模式...")
        try:
            from tools.upload_chunks_to_neo4j import ChunksUploader
            uploader = ChunksUploader()
            uploader.run()
        except Exception as e:
            print(f"❌ Chunks上传失败: {e}")

    def run_chunk_editing(self):
        """运行chunk编辑"""
        print("✏️ 启动Chunk编辑模式...")
        try:
            from tools.chunk_editor import ChunkEditor
            editor = ChunkEditor()
            editor.run()
        except Exception as e:
            print(f"❌ Chunk编辑失败: {e}")

    def run_enhanced_rag(self):
        """运行增强RAG查询"""
        print("🔍 启动增强RAG查询模式...")
        try:
            from core.pr_enhanced_rag import EnhancedPRRAGSystem
            rag_system = EnhancedPRRAGSystem()
            
            print("增强RAG系统已启动，请输入问题 (输入 'quit' 退出):")
            while True:
                question = input("\n🤔 问题: ").strip()
                if question.lower() in ['quit', 'exit', '退出']:
                    break
                
                if question:
                    use_graph = input("使用GraphRAG? (y/n): ").strip().lower() == 'y'
                    answer = rag_system.query(question, use_graph=use_graph)
                    print(f"\n🤖 回答:\n{answer}")
        except Exception as e:
            print(f"❌ 增强RAG查询失败: {e}")

    def run_direct_query(self):
        """运行直接Neo4j查询"""
        print("🔍 启动直接Neo4j查询模式...")
        try:
            from tools.neo4j_direct_query import Neo4jDirectQuery
            query_system = Neo4jDirectQuery()
            query_system.run()
        except Exception as e:
            print(f"❌ 直接查询失败: {e}")

    def run_quick_query(self):
        """运行快速查询"""
        print("⚡ 启动快速查询模式...")
        try:
            from tools.quick_query import main as quick_main
            quick_main()
        except Exception as e:
            print(f"❌ 快速查询失败: {e}")

    def run_demo(self):
        """运行功能演示"""
        print("🎭 启动功能演示...")
        try:
            from demos.demo_enhanced_pr_rag import main as demo_main
            demo_main()
        except Exception as e:
            print(f"❌ 功能演示失败: {e}")

    def run_tests(self):
        """运行完整测试"""
        print("🧪 启动完整测试...")
        try:
            from demos.test_enhanced_pr_rag import main as test_main
            test_main()
        except Exception as e:
            print(f"❌ 测试失败: {e}")

    def check_system_status(self):
        """检查系统状态"""
        print("📊 检查系统状态...")
        
        # 检查Neo4j连接
        try:
            from core.pr_neo4j_env import graph
            result = graph.query("RETURN 1 as test")
            print("✅ Neo4j连接正常")
        except Exception as e:
            print(f"❌ Neo4j连接失败: {e}")
            return
        
        # 检查数据统计
        try:
            # 检查chunks数量
            chunks_dir = Path("data/chunks")
            if chunks_dir.exists():
                chunk_files = list(chunks_dir.glob("*_chunks.json"))
                print(f"✅ Chunks文件数量: {len(chunk_files)}")
            
            # 检查Neo4j节点数量
            node_count_query = "MATCH (n) RETURN count(n) as total_nodes"
            result = graph.query(node_count_query)
            total_nodes = result[0]['total_nodes']
            print(f"✅ Neo4j总节点数: {total_nodes}")
            
            # 检查PR_Chunk节点
            pr_chunk_query = "MATCH (n:PR_Chunk) RETURN count(n) as pr_chunks"
            result = graph.query(pr_chunk_query)
            pr_chunks = result[0]['pr_chunks']
            print(f"✅ PR_Chunk节点数: {pr_chunks}")
            
        except Exception as e:
            print(f"⚠️ 状态检查部分失败: {e}")

    def show_usage_guide(self):
        """显示使用指南"""
        guide = """
📚 公关传播RAG系统 v1.0 使用指南

🎯 系统概述:
   本系统是一个基于Neo4j的增强版公关传播知识图谱RAG系统，专门用于分析
   公关公司案例、品牌传播方案等内容。

🏗️ 核心功能:
   1. 智能实体识别 - 识别品牌、企业、媒体、活动等实体
   2. 关系提取 - 识别合作、竞争、媒体投放等关系
   3. 增强RAG查询 - GraphRAG + VectorRAG双重查询能力
   4. 多格式处理 - 支持PDF、Word、Excel、PPT等格式
   5. 增量处理 - 只处理新文件，节省资源
   6. Chunk编辑 - 人工优化数据质量

📁 数据流程:
   data/raw/ → 预处理 → data/cleaned/ → JSON转换 → data/json/ 
   → 分块处理 → data/chunks/ → Neo4j集成 → 知识图谱

🔍 查询模式:
   • GraphRAG: 基于实体和关系的结构化查询
   • VectorRAG: 基于语义相似性的向量查询
   • 直接查询: 绕过预处理直接查询Neo4j

📊 实体类型:
   Brand(品牌), Company(企业), Agency(公关公司), Campaign(活动),
   Strategy(策略), Media(媒体), Platform(平台), Influencer(意见领袖),
   Content(内容), KPI(指标)

🔗 关系类型:
   COLLABORATES_WITH(合作), BRAND_COLLABORATION(品牌联名),
   MEDIA_PLACEMENT(媒体投放), COMPETES_WITH(竞争),
   LAUNCHES_CAMPAIGN(发起活动), USES_STRATEGY(使用策略)等

💡 使用建议:
   1. 首次使用选择"完整处理"模式
   2. 后续更新数据使用"增量处理"模式
   3. 查询时优先使用"增强RAG查询"
   4. 定期使用"Chunk编辑"优化数据质量

📞 技术支持:
   如遇问题，请检查:
   - .env文件配置是否正确
   - Neo4j数据库是否正常运行
   - 数据文件格式是否正确
        """
        print(guide)

    def show_system_architecture(self):
        """显示系统架构"""
        architecture = """
🏗️ 公关传播RAG系统 v1.0 架构图

┌─────────────────────────────────────────────────────────────────┐
│                        数据输入层                                │
├─────────────────────────────────────────────────────────────────┤
│  PDF, Word, Excel, PPT, HTML, JSON, TXT 等格式文档              │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                        预处理层                                  │
├─────────────────────────────────────────────────────────────────┤
│  pr_multi_format_preprocessing.py  →  pr_txt2json.py           │
│  (多格式文本提取)                    →  (JSON转换)               │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                        分块处理层                                │
├─────────────────────────────────────────────────────────────────┤
│  pr_chunking.py  →  chunk_editor.py                             │
│  (文本分块)        →  (人工编辑)                                  │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                        实体识别层                                │
├─────────────────────────────────────────────────────────────────┤
│  pr_entity_extractor.py  →  pr_enhanced_schema.py              │
│  (实体关系提取)            →  (图谱模式定义)                      │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                        知识图谱层                                │
├─────────────────────────────────────────────────────────────────┤
│  pr_enhanced_neo4j_integration.py  →  Neo4j Database            │
│  (Neo4j集成)                      →  (图数据库)                  │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                        RAG查询层                                 │
├─────────────────────────────────────────────────────────────────┤
│  pr_enhanced_rag.py  →  GraphRAG + VectorRAG                    │
│  (增强RAG系统)        →  (双重查询能力)                           │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                        应用接口层                                │
├─────────────────────────────────────────────────────────────────┤
│  ask_pr.py, neo4j_direct_query.py, quick_query.py              │
│  (多种查询接口)                                                   │
└─────────────────────────────────────────────────────────────────┘

🔧 核心组件说明:
   • 数据预处理: 支持多种格式文档的文本提取
   • 实体识别: 基于LLM+规则的智能实体提取
   • 关系提取: 识别公关传播特有的关系类型
   • 知识图谱: Neo4j存储实体和关系
   • RAG查询: GraphRAG和VectorRAG双重能力
   • 增量处理: 只处理新文件，提高效率
   • Chunk编辑: 人工优化数据质量
        """
        print(architecture)

    def run(self):
        """运行主程序"""
        self.show_banner()
        
        # 检查环境
        if not self.check_environment():
            print("❌ 环境检查失败，请修复后重试")
            return
        
        # 主循环
        while True:
            try:
                choice = self.show_main_menu()
                
                if choice == '1':
                    self.run_full_processing()
                elif choice == '2':
                    self.run_incremental_processing()
                elif choice == '3':
                    self.run_chunk_editing()
                elif choice == '4':
                    self.run_upload_chunks_to_neo4j()
                elif choice == '5':
                    self.run_enhanced_rag()
                elif choice == '6':
                    self.run_direct_query()
                elif choice == '7':
                    self.run_quick_query()
                elif choice == '8':
                    self.run_demo()
                elif choice == '9':
                    self.run_tests()
                elif choice == '10':
                    self.check_system_status()
                elif choice == '11':
                    self.show_usage_guide()
                elif choice == '12':
                    self.show_system_architecture()
                elif choice == '13':
                    print("👋 感谢使用公关传播RAG系统 v1.0！")
                    break
                else:
                    print("❌ 无效选择，请重新输入")
                
                input("\n按回车键继续...")
                
            except KeyboardInterrupt:
                print("\n\n👋 程序被用户中断，再见！")
                break
            except Exception as e:
                print(f"❌ 程序运行出错: {e}")
                input("按回车键继续...")

def main():
    """主函数"""
    try:
        system = PRRAGSystemV1()
        system.run()
    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
