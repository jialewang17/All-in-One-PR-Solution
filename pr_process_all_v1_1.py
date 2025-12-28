#!/usr/bin/env python3
"""
公关传播RAG系统 v1.1 - 完整处理流程
处理所有文件：预处理→JSON→增强知识图谱写入（分类/Section/实体+SPO）→案例库知识导入→向量索引→Neo4j集成
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import warnings

warnings.filterwarnings("ignore")

# 加载环境变量
load_dotenv('.env', override=True)

# 添加核心模块路径（确保项目根目录在最前面）
project_root = Path(__file__).parent if Path(__file__).is_file() else Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

sys.path.append('core')
sys.path.append('tools')


def main(args: Optional[argparse.Namespace] = None) -> bool:
    """主处理流程（v1.1版本） Cursor Write It-qcf ;"""
    print("🔄 启动公关传播RAG系统 v1.1 完整处理流程...")
    print("=" * 60)

    runtime_args = args or argparse.Namespace()

    _ensure_directories()

    for step in PIPELINE_STEPS:
        if step.get("skip_flag") and getattr(runtime_args, step["skip_flag"], False):
            print(f"\n{step['title']}")
            print("ℹ️ 根据参数已跳过")
            continue
        print(f"\n{step['title']}")
        try:
            step["runner"](runtime_args)
        except Exception as exc:
            print(f"❌ {step['title']} 失败: {exc}")
            import traceback

            traceback.print_exc()
            return False
        print(f"✅ {step.get('success_hint', '执行完成')}")

    _prompt_optional_spo()

    print("\n📊 处理结果统计:")
    try:
        stats = get_processing_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
    except Exception as exc:
        print(f"⚠️ 统计信息获取失败: {exc}")

    print("\n🎉 v1.1 完整处理流程完成！")
    print("=" * 60)
    print("\n💡 下一步操作建议:")
    print("1. 运行 'python pr_rag_system_v1_1.py' 选择 '6 增强RAG对话' 进行查询")
    print("2. 运行 'python tools/querying/graph/query_enhanced_kg.py company \"公司名\"' 查询公司信息")
    print("3. 运行 'python tools/querying/graph/neo4j_direct_query_new.py' 进行直接Cypher查询")
    print("=" * 60)
    return True


def _ensure_directories() -> None:
    """确保数据目录存在 Cursor Write It-qcf ;"""
    for dir_path in ['data/raw', 'data/cleaned', 'data/json', 'data/json_structured']:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ 确保目录存在: {dir_path}")


def _run_preprocess_step(_: Optional[argparse.Namespace]) -> None:
    from tools.processing.ingestion import pr_multi_format_preprocessing as preprocess

    preprocess.process_multi_format_documents()


def _run_convert_step(_: Optional[argparse.Namespace]) -> None:
    from core.processing.ingestion import txt_to_json as txt2json

    txt2json.process_pr_text_files()


def _run_normalize_step(_: Optional[argparse.Namespace]) -> None:
    """JSON 规范化步骤：将 data/json/ 转换为 data/json_structured/"""
    import subprocess
    import sys
    
    script_path = Path(__file__).parent / "tools" / "processing" / "ingestion" / "normalize_json_sections.py"
    
    if not script_path.exists():
        print(f"⚠️ 规范化脚本不存在: {script_path}")
        print("ℹ️ 跳过规范化步骤，将直接使用 data/json/ 目录")
        return
    
    print("🔄 执行 JSON 规范化...")
    result = subprocess.run(
        [sys.executable, str(script_path), 
         "--input-dir", "data/json",
         "--output-dir", "data/json_structured",
         "--overwrite"],  # 添加 --overwrite 参数，确保重新提取品牌名
        capture_output=False
    )
    
    if result.returncode != 0:
        print(f"⚠️ JSON 规范化失败（退出码: {result.returncode}）")
        print("ℹ️ 将尝试直接使用 data/json/ 目录")
    else:
        print("✅ JSON 规范化完成")


def _build_process_enhanced_namespace(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        migrate=getattr(args, "kg_migrate", False),
        clean_chunks=getattr(args, "kg_clean_chunks", False),
        json_dir=getattr(args, "kg_json_dir", None) or "data/json_structured",
        uri=getattr(args, "kg_uri", None),
        no_spo=getattr(args, "kg_no_spo", False),
        use_demo_spo=getattr(args, "kg_use_demo_spo", False),
        no_entity_extractor=getattr(args, "kg_no_entity_extractor", False),
        no_resume=getattr(args, "kg_no_resume", False),
        reset_checkpoint=getattr(args, "kg_reset_checkpoint", False),
        parallel=getattr(args, "kg_parallel", False),  # 并行处理
        max_workers=getattr(args, "kg_max_workers", 4),  # 最大工作线程数
    )


def _run_enhanced_kg_step(args: Optional[argparse.Namespace]) -> None:
    runtime_args = args or argparse.Namespace()
    
    # 检查是否使用 GraphRAG 写入器
    use_graphrag = getattr(runtime_args, "kg_use_graphrag", False)
    
    if use_graphrag:
        from core.processing.kg_writer.graphrag_writer import GraphRAGWriter
        
        # 初始化 GraphRAG 写入器
        writer = GraphRAGWriter(
            uri=getattr(runtime_args, "kg_uri", None),
            use_llm_for_cypher=not getattr(runtime_args, "kg_no_llm_cypher", False),
            use_graph_context=not getattr(runtime_args, "kg_no_graph_context", False)
        )
        
        try:
            # 创建Schema
            writer.create_schema()
            
            # 处理JSON文件
            json_dir = getattr(runtime_args, "kg_json_dir", None) or "data/json_structured"
            writer.process_json_files(json_dir=json_dir, resume=False)
        finally:
            writer.close()
    else:
        from tools.processing.kg_writer import process_enhanced_all as kg_pipeline
        kg_args = _build_process_enhanced_namespace(runtime_args)
        kg_pipeline.run_pipeline(kg_args, load_env_first=True)


def _run_case_library_step(args: Optional[argparse.Namespace]) -> None:
    from tools.processing.ingestion.load_case_library_to_neo4j import GraphSyncer

    runtime_args = args or argparse.Namespace()
    base_dir = getattr(runtime_args, "case_base_dir", None) or "data/reference"

    # 使用新的 GraphSyncer API
    syncer = GraphSyncer(base_dir)
    syncer.sync_channels()
    syncer.sync_goals()
    syncer.sync_industries()
    syncer.sync_cases()

    print("✅ 案例库/渠道/目标/行业 同步完成")


def _run_vector_step(_: Optional[argparse.Namespace]) -> None:
    from tools.processing.vector import create_section_vector_index as vector_step

    vector_step.main()


PIPELINE_STEPS = [
    {
        "title": "📄 步骤1: 多格式文档预处理",
        "success_hint": "预处理完成",
        "runner": _run_preprocess_step,
    },
    {
        "title": "🔄 步骤2: JSON 格式转换",
        "success_hint": "JSON 转换完成",
        "runner": _run_convert_step,
    },
    {
        "title": "📋 步骤2.5: JSON 规范化（统一数据结构）",
        "success_hint": "JSON 规范化完成",
        "runner": _run_normalize_step,
        "skip_flag": "skip_normalize",
    },
    {
        "title": "🏗️ 步骤3: v1.1 增强知识图谱写入",
        "success_hint": "知识图谱写入完成",
        "runner": _run_enhanced_kg_step,
    },
    {
        "title": "📚 步骤4: 导入案例库结构化知识",
        "success_hint": "案例库知识导入完成",
        "runner": _run_case_library_step,
        "skip_flag": "skip_case_library",
    },
    {
        "title": "🔍 步骤5: 创建向量索引并生成嵌入",
        "success_hint": "向量索引和嵌入生成完成",
        "runner": _run_vector_step,
        "skip_flag": "no_vector",
    },
]


def _run_spo_extraction(use_demo: bool = False) -> bool:
    try:
        if use_demo:
            from tools.processing.extractors import create_demo_spo_relations as demo_spo

            demo_spo.create_demo_spo_relations()
        else:
            from tools.processing.extractors import extract_spo_relations as llm_spo

            llm_spo.extract_spo_relations()
        return True
    except Exception as exc:
        print(f"❌ SPO 提取失败: {exc}")
        import traceback

        traceback.print_exc()
        return False


def _prompt_optional_spo() -> None:
    """处理可选的 SPO 提取步骤 Cursor Write It-qcf ;"""
    user_input = input("\n是否运行额外的SPO关系提取？(y/N): ").strip().lower()
    if user_input != 'y':
        print("ℹ️ 跳过额外SPO提取")
        return

    if _run_spo_extraction(use_demo=False):
        return

    fallback = input("是否尝试规则脚本作为备用？(y/N): ").strip().lower()
    if fallback == "y":
        _run_spo_extraction(use_demo=True)


def get_processing_stats():
    """获取处理统计信息 Cursor Write It-qcf ;"""
    stats = {}
    
    # 统计各目录文件数量
    dirs = {
        '原始文件': 'data/raw',
        '清理文件': 'data/cleaned', 
        'JSON文件': 'data/json',
        '规范化JSON': 'data/json_structured'
    }
    
    for name, path in dirs.items():
        if Path(path).exists():
            files = list(Path(path).glob('*'))
            # 排除隐藏文件和目录
            files = [f for f in files if f.is_file() and not f.name.startswith('.')]
            stats[name] = len(files)
        else:
            stats[name] = 0
    
    # 尝试统计 Neo4j 节点数量
    try:
        from core.common.pr_neo4j_env import graph
        
        queries = [
            ("Section节点", "MATCH (s:Section) RETURN count(s) as count"),
            ("Company节点", "MATCH (c:Company) RETURN count(c) as count"),
            ("CategoryL1节点", "MATCH (c:CategoryL1) RETURN count(c) as count"),
            ("CategoryL2节点", "MATCH (c:CategoryL2) RETURN count(c) as count"),
            ("SPO_REL关系", "MATCH ()-[r:SPO_REL]->() RETURN count(r) as count"),
        ]
        
        for label, query in queries:
            try:
                result = graph.query(query)
                if result and len(result) > 0:
                    count = result[0]['count'] if isinstance(result[0], dict) else result[0][0]
                    stats[label] = count
            except Exception:
                stats[label] = "查询失败"
                
    except Exception:
        stats["Neo4j统计"] = "未连接"
    
    return stats


def check_neo4j_connection():
    """检查 Neo4j 连接 Cursor Write It-qcf ;"""
    try:
        from core.common.pr_neo4j_env import graph
        result = graph.query("RETURN 1 as test")
        if result:
            print("✅ Neo4j 连接正常")
            return True
    except Exception as e:
        print(f"⚠️ Neo4j 连接检查失败: {e}")
        print("   请确保 Neo4j 服务正在运行，且 .env 配置正确")
        return False


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="公关传播RAG系统 v1.1 全流程入口（支持断点续跑控制）"
    )
    parser.add_argument("--kg-uri", help="覆盖 Neo4j URI（传给步骤3）")
    parser.add_argument("--kg-json-dir", help="覆盖 JSON 输入目录（传给步骤3）")
    parser.add_argument("--kg-no-resume", action="store_true",
                        help="禁用步骤3的断点续跑（传给 run_enhanced_kg_writer.py）")
    parser.add_argument("--kg-reset-checkpoint", action="store_true",
                        help="在步骤3开始前清空断点记录")
    parser.add_argument("--kg-migrate", action="store_true",
                        help="在步骤3执行前运行 Schema 迁移")
    parser.add_argument("--kg-clean-chunks", action="store_true",
                        help="在步骤3执行前清理旧 PR_Chunk 节点")
    parser.add_argument("--kg-no-spo", action="store_true",
                        help="跳过写入阶段的 SPO 逻辑")
    parser.add_argument("--kg-use-demo-spo", action="store_true",
                        help="强制使用规则脚本写入 SPO（对应 --use-demo-spo）")
    parser.add_argument("--kg-no-entity-extractor", action="store_true",
                        help="禁用写入阶段实体提取器")
    parser.add_argument("--kg-parallel", action="store_true",
                        help="启用并行处理模式（实验性功能，可提升处理速度）")
    parser.add_argument("--kg-max-workers", type=int, default=4,
                        help="并行处理时的最大工作线程数（默认4，仅在 --kg-parallel 时生效）")
    parser.add_argument("--kg-use-graphrag", action="store_true",
                        help="使用 GraphRAG 逻辑进行写入（使用LLM生成Cypher语句并利用已有图谱结构）")
    parser.add_argument("--kg-no-llm-cypher", action="store_true",
                        help="在GraphRAG模式下禁用使用LLM生成Cypher语句")
    parser.add_argument("--kg-no-graph-context", action="store_true",
                        help="在GraphRAG模式下禁用利用已有图谱结构进行智能关联")
    parser.add_argument("--case-base-dir", help="案例库/方法论引用文件所在目录（默认 data/reference）")
    parser.add_argument("--skip-case-library", action="store_true",
                        help="跳过案例库结构化数据写入 Neo4j")
    parser.add_argument("--skip-normalize", action="store_true",
                        help="跳过 JSON 规范化步骤（直接使用 data/json/）")
    parser.add_argument("--no-vector", action="store_true",
                        help="跳过向量索引与嵌入生成步骤")
    return parser.parse_args()


if __name__ == "__main__":
    print("🔧 公关传播RAG系统 v1.1 - 完整处理流程")
    print("=" * 60)
    print("流程: 预处理 → JSON转换 → JSON规范化（可 --skip-normalize） → v1.1增强KG写入 → 案例库导入（可 --skip-case-library） → 向量索引（可 --no-vector）")
    print("=" * 60)

    cli_args = _parse_arguments()

    # 检查 Neo4j 连接
    print("\n🔍 检查 Neo4j 连接...")
    if not check_neo4j_connection():
        print("\n⚠️ Neo4j 连接失败，但预处理和JSON转换仍可继续")
        user_input = input("是否继续？(y/N): ").strip().lower()
        if user_input != 'y':
            print("❌ 用户取消操作")
            sys.exit(1)
    
    # 运行主流程
    print("\n" + "=" * 60)
    success = main(cli_args)
    
    if success:
        print("\n✅ 所有处理步骤完成！")
        print("💡 现在可以运行 'python pr_rag_system_v1_1.py' 进行 RAG 查询")
    else:
        print("\n❌ 处理过程中出现错误")
        sys.exit(1)

