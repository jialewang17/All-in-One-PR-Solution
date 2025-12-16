#!/usr/bin/env python3
"""
公关传播RAG系统 v1.1
采用新版“三级分类 + Section + 实体分型 + SPO”的一键流程与查询入口
"""

import json
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
        self.plan_generator = None
        self.report_generator = None
        self.rlhf_system = None
        self.plan_run_dir = Path("outputs") / "rlhf_plans"
        
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
        for d in ['data/json', 'data/json_structured']:
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

📝 生成模式
  9. 生成公关传播方案（多模板输出）
  10. 生成公关传播报告（需求确认+方法论对齐）

📈 反馈/学习模式
  11. 导入方法论规则（Neo4j）
  12. 录入方案反馈（RLHF）
  13. 手动触发 RLHF 训练
  14. 查看 RLHF 学习进度

🧪 测试模式
  15. 功能演示
  16. 完整测试
  17. 系统状态检查

📚 帮助模式
  18. 使用指南
  19. 系统架构

🚪 系统
  20. 退出

请选择 (1-16): """
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
        """运行功能演示（RAG / 方案 / 报告）"""
        demo_options = {
            "1": ("增强 RAG 综合演示", "examples.rag.demo_enhanced_pr_rag_v1_1"),
            "2": ("方案生成器示例", "examples.demo_plan_generation"),
            "3": ("报告生成器示例", "examples.demo_report_generation"),
            "4": ("报告 + RAG 快速示例", "examples.demo_report_and_rag"),
        }
        print("🎭 请选择要运行的演示：")
        for key, (label, _) in demo_options.items():
            print(f"  {key}. {label}")
        choice = input("请输入选项 (默认 1): ").strip() or "1"
        if choice not in demo_options:
            print("⚠️ 无效选择，已取消演示")
            return
        label, module_path = demo_options[choice]
        print(f"▶️ 正在启动 {label} ...")
        try:
            import importlib

            module = importlib.import_module(module_path)
            if hasattr(module, "main"):
                module.main()
            else:
                raise AttributeError("main 函数不存在")
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
    
    def _ensure_rlhf_system(self) -> bool:
        """初始化 RLHF 增强方案系统"""
        if self.rlhf_system is False:
            return False
        if self.rlhf_system is not None:
            return True
        try:
            from core.rlhf.pr_enhanced_rag_with_rlhf import EnhancedPRRAGWithRLHF
            self.rlhf_system = EnhancedPRRAGWithRLHF()
            print("✅ RLHF 增强方案生成器就绪")
            return True
        except Exception as exc:
            print(f"⚠️ RLHF 系统初始化失败，将回退到传统方案生成: {exc}")
            self.rlhf_system = False
            return False
    
    @staticmethod
    def _serialize_quality_assessment(assessment):
        """将 QualityAssessment/QualityScore 转换为可序列化 dict"""
        if assessment is None:
            return None
        metric_scores = []
        for score in getattr(assessment, "metric_scores", []):
            metric_scores.append(
                {
                    "metric": getattr(score, "metric", ""),
                    "score": getattr(score, "score", 0),
                    "weight": getattr(score, "weight", 0),
                    "explanation": getattr(score, "explanation", ""),
                }
            )
        return {
            "plan_id": getattr(assessment, "plan_id", ""),
            "overall_score": getattr(assessment, "overall_score", 0),
            "assessment_type": getattr(assessment, "assessment_type", ""),
            "assessor_id": getattr(assessment, "assessor_id", None),
            "timestamp": getattr(assessment, "timestamp", ""),
            "comments": getattr(assessment, "comments", None),
            "improvements": getattr(assessment, "improvements", []),
            "metric_scores": metric_scores,
        }
    
    def _record_rlhf_run(
        self,
        enterprise_info,
        plan_types,
        use_rag,
        manual_context,
        plan_payload,
    ):
        """保存本次 RLHF 方案的详细数据供训练使用"""
        try:
            from datetime import datetime
            self.plan_run_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.plan_run_dir / f"planrun_{timestamp}.json"
            quality_assessments = {}
            for plan_type, assessment in plan_payload.get("quality_assessments", {}).items():
                quality_assessments[plan_type] = self._serialize_quality_assessment(assessment)
            record = {
                "generated_at": timestamp,
                "enterprise_info": enterprise_info,
                "plan_types": plan_types,
                "use_rag": use_rag,
                "manual_context": manual_context,
                "results": plan_payload.get("results", {}),
                "quality_assessments": quality_assessments,
                "applied_rules": plan_payload.get("applied_rules", []),
                "brand_knowledge_used": plan_payload.get("brand_knowledge_used"),
            }
            with open(output_file, "w", encoding="utf-8") as fh:
                json.dump(record, fh, ensure_ascii=False, indent=2)
            return output_file
        except Exception as exc:
            print(f"⚠️ 记录 RLHF 方案失败: {exc}")
            return None
    
    def _find_plan_metadata(self, plan_id: str):
        """在记录文件中查找指定 plan_id 的元信息"""
        if not plan_id or not self.plan_run_dir.exists():
            return None
        try:
            plan_files = sorted(self.plan_run_dir.glob("planrun_*.json"), reverse=True)
            for path in plan_files:
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                for plan_type, plan_data in (data.get("results") or {}).items():
                    if plan_data.get("plan_id") == plan_id:
                        info = {
                            "plan_type": plan_type,
                            "plan_data": plan_data,
                            "enterprise_info": data.get("enterprise_info", {}),
                            "knowledge_sources": plan_data.get("knowledge_sources", []),
                            "record_path": str(path),
                        }
                        return info
        except Exception as exc:
            print(f"⚠️ 查找方案记录失败: {exc}")
        return None
    
    def _load_plan_content_storage(self):
        """构建 plan_id -> {content, context} 的缓存供 RLHF 训练使用"""
        storage = {}
        if not self.plan_run_dir.exists():
            return storage
        try:
            plan_files = sorted(self.plan_run_dir.glob("planrun_*.json"))
            for path in plan_files:
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                enterprise_info = data.get("enterprise_info", {})
                for plan_type, plan_data in (data.get("results") or {}).items():
                    plan_id = plan_data.get("plan_id")
                    if not plan_id:
                        continue
                    context = {
                        "brand": enterprise_info.get("enterprise_name"),
                        "industry": enterprise_info.get("industry") or enterprise_info.get("industry_name"),
                        "pr_goal": enterprise_info.get("pr_goal"),
                        "scenario": "plan_generation",
                        "plan_type": plan_type,
                    }
                    storage[plan_id] = {
                        "content": plan_data.get("content", ""),
                        "context": context,
                    }
        except Exception as exc:
            print(f"⚠️ 加载方案记录失败: {exc}")
        return storage
    
    def show_usage_guide(self):
        """显示使用指南（简版）"""
        guide = """
📚 使用指南（v1.1）
1) 一键构建：先运行"1 一键构建增强图谱"
2) 若有旧数据：可先"2 迁移旧图谱"或"3 清理 PR_Chunk"
3) 需要 SPO：选择"4 LLM补充SPO"或"5 规则演示SPO"
4) 交互对话：选择"6 增强RAG对话"（GraphRAG/VectorRAG）
5) 直接查询：选择"7 直接Neo4j查询"进行Cypher查询
6) 快速查询：选择"8 快速查询"（基于Section节点，支持GraphRAG和文本匹配）
7) 方案生成：选择"9 生成公关方案"（多模板输出/可选类型）
8) 报告生成：选择"10 生成公关传播报告"（需求确认+方法论对齐+RAG检索）
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
    
    def run_generate_plan(self):
        """生成公关传播方案"""
        print("🧩 启动方案生成模式...")
        print("=" * 60)

        try:
            rlhf_ready = self._ensure_rlhf_system()
            if not rlhf_ready and self.plan_generator is None:
                try:
                    from core.generation import PRPlanGenerator
                    from core.querying.pipelines import EnhancedPRRAGSystemV11
                    rag_system = EnhancedPRRAGSystemV11()
                    llm_config = {
                        "provider": os.getenv("LLM_PROVIDER", "openai"),
                        "model": os.getenv("PLAN_LLM_MODEL")
                                 or os.getenv("LLM_MODEL")
                                 or os.getenv("OPENAI_MODEL")
                                 or "gpt-4o-mini",
                        "temperature": float(os.getenv("PLAN_LLM_TEMPERATURE", "0.6")),
                        "max_tokens": int(os.getenv("PLAN_LLM_MAX_TOKENS", "2048")),
                    }
                    self.plan_generator = PRPlanGenerator(
                        rag_system=rag_system,
                        llm_config=llm_config,
                    )
                    print("✅ 传统方案生成器初始化成功")
                except Exception as e:
                    print(f"❌ 方案生成器初始化失败: {e}")
                    import traceback
                    traceback.print_exc()
                    return

            print("\n📋 请填写企业信息（直接回车使用默认值）：")
            enterprise_info = {}
            enterprise_info["enterprise_name"] = input("企业名称 (默认: 示例企业): ").strip() or "示例企业"
            enterprise_info["enterprise_stage"] = input("企业阶段 (默认: 中小微企业): ").strip() or "中小微企业"
            enterprise_info["industry"] = input("行业 (默认: 大消费): ").strip() or "大消费"
            enterprise_info["market_type"] = input("市场类型 ToC/ToB/ToG (默认: ToC): ").strip() or "ToC"
            enterprise_info["pr_goal"] = input("公关目标 (默认: 品牌认知): ").strip() or "品牌认知"
            enterprise_info["pr_cycle"] = input("项目周期 (默认: 3个月): ").strip() or "3个月"
            enterprise_info["pr_budget"] = input("预算 (默认: 100万): ").strip() or "100万"
            enterprise_info["innovation"] = input("创新要求 (默认: 适度创新): ").strip() or "适度创新"

            default_types = ["A", "B", "C"]
            plan_type_labels = {
                "A": "图文简报",
                "B": "视频脚本",
                "C": "整合活动方案",
                "D": "短视频脚本",
                "E": "小红书种草",
                "F": "危机公关方案",
            }
            plan_types_input = input(
                "输出类型 (用逗号分隔，默认: A,B,C): "
            ).strip()
            if plan_types_input:
                plan_types = [
                    p.strip().upper()
                    for p in plan_types_input.split(",")
                    if p.strip()
                ]
            else:
                plan_types = default_types

            use_rag = input("是否进行RAG检索增强上下文？(Y/n): ").strip().lower()
            use_rag = True if use_rag in ("", "y", "yes") else False
            manual_context = None
            if not use_rag:
                manual_context = input("请输入自定义背景（可留空使用行业经验）: ").strip() or "基于行业最佳实践和案例经验"

            print("\n" + "=" * 60)
            print("正在生成方案，请稍候...")
            print("=" * 60)

            plan_payload = None
            if rlhf_ready:
                plan_payload = self.rlhf_system.generate_plan_with_feedback(
                    enterprise_info=enterprise_info,
                    output_types=plan_types,
                )
                results = plan_payload.get("results", {})
            else:
                results = self.plan_generator.generate_plan(
                    enterprise_info=enterprise_info,
                    output_types=plan_types,
                    context=None if use_rag else manual_context,
                )

            if not results:
                print("❌ 未生成任何方案")
                return

            plan_type_labels = {
                "A": "图文简报",
                "B": "视频脚本",
                "C": "整合活动方案",
                "D": "短视频脚本",
                "E": "小红书种草",
                "F": "危机公关方案",
            }
            for plan_type, content in results.items():
                label = plan_type_labels.get(plan_type, plan_type)
                print("\n" + "-" * 60)
                print(f"{plan_type} | {label}")
                print("-" * 60)
                if plan_payload:
                    plan_details = content
                    print(plan_details.get("content", "（无内容）"))
                    print("\n📌 元信息:")
                    print(f"  • Plan ID: {plan_details.get('plan_id')}")
                    print(f"  • 质量评分: {plan_details.get('quality_score')}")
                    applied_rules = plan_details.get("applied_rules") or []
                    print(f"  • 应用规则: {', '.join(applied_rules) if applied_rules else '无'}")
                    sources = plan_details.get("knowledge_sources") or []
                    print(f"  • 知识来源: {', '.join(sources) if sources else '默认知识库'}")
                    improvements = plan_details.get("improvements") or []
                    if improvements:
                        print("  • 改进建议:")
                        for idx, tip in enumerate(improvements, 1):
                            print(f"     {idx}. {tip}")
                else:
                    print(content)

            if plan_payload:
                record_path = self._record_rlhf_run(
                    enterprise_info,
                    plan_types,
                    use_rag,
                    manual_context,
                    plan_payload,
                )
                if record_path:
                    print(f"\n🗂️ 本次方案已记录到: {record_path}")

            save_input = input("\n是否导出 Markdown 方案？(y/N): ").strip().lower()
            if save_input == "y":
                from datetime import datetime

                output_dir = Path("outputs")
                output_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = output_dir / f"plan_{timestamp}.md"

                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(f"# 公关传播方案（{enterprise_info['enterprise_name']}）\n\n")
                    for plan_type, content in results.items():
                        label = plan_type_labels.get(plan_type, plan_type)
                        f.write(f"## {plan_type} | {label}\n\n")
                        if plan_payload:
                            f.write((content.get("content", "")) + "\n\n")
                            f.write(f"- Plan ID: {content.get('plan_id')}\n")
                            f.write(f"- 质量评分: {content.get('quality_score')}\n")
                            f.write(f"- 应用规则: {', '.join(content.get('applied_rules') or [])}\n")
                            f.write(f"- 知识来源: {', '.join(content.get('knowledge_sources') or [])}\n\n")
                        else:
                            f.write(content + "\n\n")

                print(f"✅ 方案已保存到: {output_file}")

        except Exception as e:
            print(f"❌ 方案生成失败: {e}")
            import traceback
            traceback.print_exc()

    def run_import_methodology_rules(self):
        """导入方法论规则"""
        print("📥 导入方法论规则到 Neo4j")
        print("-" * 60)
        default_path = Path("data/rlhf/methodology_rules.json")
        rules_path = input(f"规则文件路径 (默认: {default_path}): ").strip() or str(default_path)
        path = Path(rules_path).expanduser()
        if not path.exists():
            print(f"❌ 文件不存在: {path}")
            return
        try:
            from tools.rlhf.import_methodology_rules import import_rules
            import_rules(path.resolve())
        except Exception as exc:
            print(f"❌ 导入失败: {exc}")
        else:
            print("✅ 方法论规则全部写入 Neo4j，可开始在 RLHF 中引用")
    
    def run_collect_rlhf_feedback(self):
        """录入方案反馈"""
        if not self._ensure_rlhf_system():
            print("⚠️ RLHF 系统不可用，无法录入反馈")
            return
        print("📝 录入方案反馈（RLHF）")
        print("-" * 60)
        plan_id = input("Plan ID（必填，可从最近生成结果中复制）: ").strip()
        if not plan_id:
            print("❌ Plan ID 不能为空")
            return
        metadata = self._find_plan_metadata(plan_id)
        if metadata:
            default_plan_type = metadata.get("plan_type", "")
            default_sources = metadata.get("knowledge_sources") or []
            print(f"ℹ️ 匹配到记录文件: {metadata.get('record_path')}")
            print(f"ℹ️ 默认 Plan Type: {default_plan_type}")
        else:
            default_plan_type = ""
            default_sources = []
            print("⚠️ 未找到对应的方案记录，将使用手动输入")
        
        plan_type = input(f"方案类型 (默认: {default_plan_type or 'A'}): ").strip() or (default_plan_type or "A")
        rating_input = input("评分 (1-5，可含小数，默认: 4.5): ").strip()
        try:
            rating = float(rating_input) if rating_input else 4.5
        except ValueError:
            print("⚠️ 评分输入无效，使用默认 4.5")
            rating = 4.5
        comment = input("文字评价 (可留空): ").strip() or None
        suggestions_input = input("改进建议（用逗号分隔，可留空）: ").strip()
        suggestions = [s.strip() for s in suggestions_input.split(",") if s.strip()] if suggestions_input else []
        categories_input = input("结构化指标（示例: 创新性=high,落地性=medium，可留空）: ").strip()
        categories = {}
        if categories_input:
            for pair in categories_input.split(","):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    categories[key.strip()] = value.strip()
        user_id = input("录入人/用户ID (可留空): ").strip() or None
        if default_sources:
            print(f"ℹ️ 默认知识来源: {', '.join(default_sources)}")
        knowledge_input = input("知识来源（逗号分隔，留空使用默认）: ").strip()
        knowledge_sources = (
            [s.strip() for s in knowledge_input.split(",") if s.strip()]
            if knowledge_input
            else default_sources
        )
        
        try:
            result = self.rlhf_system.collect_feedback_for_plan(
                plan_id=plan_id,
                rating=rating,
                comment=comment,
                plan_type=plan_type,
                suggestions=suggestions or None,
                categories=categories or None,
                user_id=user_id,
                knowledge_sources=knowledge_sources or None,
            )
            print(f"✅ 反馈已记录: {result.get('feedback_id')}")
            print("📍 数据写入: data/feedback.db")
        except Exception as exc:
            print(f"❌ 反馈录入失败: {exc}")
    
    def run_trigger_rlhf_training(self):
        """手动触发 RLHF 训练"""
        if not self._ensure_rlhf_system():
            print("⚠️ RLHF 系统不可用，无法训练")
            return
        print("🎯 手动触发 RLHF 奖励模型训练")
        print("-" * 60)
        storage = self._load_plan_content_storage()
        if not storage:
            print("⚠️ 未找到任何方案记录，请先运行第 9 步生成方案")
            return
        min_count_input = input("最少反馈数量阈值 (默认: 5): ").strip()
        try:
            min_feedback = int(min_count_input) if min_count_input else 5
        except ValueError:
            min_feedback = 5
        training_data = self.rlhf_system.rlhf_trainer.prepare_training_data(
            min_feedback_count=min_feedback,
            plan_content_storage=storage,
        )
        if not training_data:
            print(f"⚠️ 符合条件的反馈不足 {min_feedback} 条，暂不训练")
            return
        print(f"📚 收集到 {len(training_data)} 条训练样本，开始训练...")
        success = self.rlhf_system.rlhf_trainer.train_reward_model(training_data)
        if success:
            print("✅ 奖励模型训练完成")
        else:
            print("ℹ️ 训练流程结束（可能因数据质量不足未更新模型）")
    
    def run_show_rlhf_progress(self):
        """查看 RLHF 学习进度"""
        if not self._ensure_rlhf_system():
            print("⚠️ RLHF 系统不可用")
            return
        print("📊 RLHF 学习进度")
        print("-" * 60)
        try:
            progress = self.rlhf_system.get_learning_progress()
            training_stats = progress.get("training_stats", {})
            feedback_stats = progress.get("feedback_stats", {})
            print(f"• 是否已训练模型: {'是' if progress.get('model_trained') else '否'}")
            print(f"• 训练轮次: {training_stats.get('total_training_runs', 0)}")
            if training_stats.get("training_history"):
                last = training_stats["training_history"][-1]
                print(f"• 最近训练时间: {last.get('timestamp')}")
                print(f"  使用样本: {last.get('training_data_count')}")
            print(f"• 总反馈数量: {feedback_stats.get('total_count', 0)}")
            print(f"• 平均评分: {feedback_stats.get('average_rating', 0):.2f}")
            if feedback_stats.get("common_suggestions"):
                print("• 高频改进建议:")
                for item in feedback_stats["common_suggestions"][:5]:
                    print(f"   - {item['item']} ({item['count']} 次)")
        except Exception as exc:
            print(f"❌ 获取学习进度失败: {exc}")

    def run_generate_report(self):
        """生成公关传播报告"""
        print("📝 启动报告生成模式...")
        print("=" * 60)
        
        try:
            # 初始化报告生成器（如果还未初始化）
            if self.report_generator is None:
                try:
                    from core.generation import PRReportGenerator
                    from core.querying.pipelines import EnhancedPRRAGSystemV11
                    rag_system = EnhancedPRRAGSystemV11()
                    self.report_generator = PRReportGenerator(
                        rag_system=rag_system,
                        llm_provider=os.getenv("LLM_PROVIDER", "openai")
                    )
                    print("✅ 报告生成器初始化成功")
                except Exception as e:
                    print(f"❌ 报告生成器初始化失败: {e}")
                    import traceback
                    traceback.print_exc()
                    return
            
            # 收集需求信息
            print("\n📋 请填写报告需求（直接回车使用默认值）：")
            requirements = {}
            
            goal = input("报告目标 (默认: 新品发布认知): ").strip()
            requirements["goal"] = goal if goal else "新品发布认知"
            
            audience = input("目标受众 (默认: 一线城市年轻消费者): ").strip()
            requirements["audience"] = audience if audience else "一线城市年轻消费者"
            
            tone = input("语气风格 (默认: 专业且友好): ").strip()
            requirements["tone"] = tone if tone else "专业且友好"
            
            length = input("报告长度 (默认: 1200字左右): ").strip()
            requirements["length"] = length if length else "1200字左右"
            
            format_type = input("输出格式 (默认: Markdown): ").strip()
            requirements["format"] = format_type if format_type else "Markdown"
            
            timeframe = input("时间范围 (默认: 近3个月案例与渠道): ").strip()
            requirements["timeframe"] = timeframe if timeframe else "近3个月案例与渠道"
            
            citation_pref = input("引用偏好 (默认: 需要标注来源): ").strip()
            requirements["citation_pref"] = citation_pref if citation_pref else "需要标注来源"
            
            channels_input = input("渠道列表 (用逗号分隔，默认: 微博,小红书,短视频): ").strip()
            if channels_input:
                requirements["channels"] = [c.strip() for c in channels_input.split(',')]
            else:
                requirements["channels"] = ["微博", "小红书", "短视频"]
            
            industry = input("行业 (默认: 大消费): ").strip()
            requirements["industry"] = industry if industry else "大消费"
            
            brand = input("品牌名称 (默认: 示例品牌X): ").strip()
            requirements["brand"] = brand if brand else "示例品牌X"
            
            # 确认需求
            print("\n" + "=" * 60)
            print("需求确认：")
            print("=" * 60)
            confirm_result = self.report_generator.confirm_requirements(requirements)
            print(confirm_result.get("summary"))
            
            # 询问是否继续
            user_input = input("\n是否继续生成报告？(y/N): ").strip().lower()
            if user_input != 'y':
                print("已取消生成报告")
                return
            
            # 询问是否使用 RAG 检索
            use_rag = input("是否使用 RAG 检索知识库？(y/N): ").strip().lower() == 'y'
            dry_run = not use_rag
            
            # 生成报告
            print("\n" + "=" * 60)
            print("正在生成报告，请稍候...")
            print("=" * 60)
            
            report = self.report_generator.generate_report(
                requirements,
                dry_run=dry_run,
                use_graph=True
            )
            
            # 显示报告
            print("\n" + "=" * 60)
            print("生成的报告：")
            print("=" * 60)
            report_text = report.get("report", "未生成")
            print(report_text)
            
            # 询问是否保存
            save_input = input("\n是否保存报告到文件？(y/N): ").strip().lower()
            if save_input == 'y':
                from pathlib import Path
                output_dir = Path("outputs")
                output_dir.mkdir(parents=True, exist_ok=True)
                
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = output_dir / f"report_{timestamp}.md"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                
                print(f"✅ 报告已保存到: {output_file}")
            
        except Exception as e:
            print(f"❌ 报告生成失败: {e}")
            import traceback
            traceback.print_exc()
    
    
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
                    self.run_generate_plan()
                elif choice == '10':
                    self.run_generate_report()
                elif choice == '11':
                    self.run_import_methodology_rules()
                elif choice == '12':
                    self.run_collect_rlhf_feedback()
                elif choice == '13':
                    self.run_trigger_rlhf_training()
                elif choice == '14':
                    self.run_show_rlhf_progress()
                elif choice == '15':
                    self.run_demo()
                elif choice == '16':
                    self.run_tests()
                elif choice == '17':
                    self.check_system_status()
                elif choice == '18':
                    self.show_usage_guide()
                elif choice == '19':
                    self.show_system_architecture()
                elif choice == '20':
                    print("👋 再见！")
                    break
                else:
                    print("❌ 无效选择，请输入 1-16")
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


