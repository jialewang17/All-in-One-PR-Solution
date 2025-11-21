#!/usr/bin/env python3
"""
公关传播RAG系统 v1.1 - 完整处理流程
处理所有文件：预处理→JSON→增强知识图谱写入（分类/Section/实体+SPO）→Neo4j集成
"""

import os
import sys
import subprocess
from pathlib import Path
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

from core.common.feature_registry import FeatureRegistry

PIPELINE_STEPS = [
    {
        "id": "preprocess_multi_format",
        "title": "📄 步骤1: 多格式文档预处理",
        "success_hint": "预处理完成",
    },
    {
        "id": "convert_txt_to_json",
        "title": "🔄 步骤2: JSON 格式转换",
        "success_hint": "JSON 转换完成",
    },
    {
        "id": "run_enhanced_kg_writer",
        "title": "🏗️ 步骤3: v1.1 增强知识图谱写入",
        "success_hint": "知识图谱写入完成",
    },
]

OPTIONAL_SPO_STEP = {
    "id": "extract_spo_relations",
    "title": "🎯 步骤4: 补充 SPO 关系提取（LLM）",
    "success_hint": "SPO 关系提取完成（LLM）",
    "fallback_id": "create_demo_spo_relations",
    "fallback_title": "🎯 步骤4B: 规则版 SPO 关系提取",
    "fallback_hint": "SPO 关系提取完成（规则）",
}

REQUIRED_FEATURE_IDS = [step["id"] for step in PIPELINE_STEPS]


def main(registry: FeatureRegistry) -> bool:
    """主处理流程（v1.1版本） Cursor Write It-qcf ;"""
    print("🔄 启动公关传播RAG系统 v1.1 完整处理流程...")
    print("=" * 60)

    _ensure_directories()

    for step in PIPELINE_STEPS:
        if not _run_feature_step(registry, step):
            return False

    _prompt_optional_spo(registry)

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
    for dir_path in ['data/raw', 'data/cleaned', 'data/json']:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ 确保目录存在: {dir_path}")


def _run_feature_step(registry: FeatureRegistry, step: dict) -> bool:
    """执行功能步骤命令 Cursor Write It-qcf ;"""
    try:
        command = registry.get_entry(step["id"])
    except (KeyError, ValueError) as exc:
        print(f"❌ {exc}")
        return False

    print(f"\n{step['title']}")
    print(f"➡️  命令: {command}")
    try:
        subprocess.run(command, cwd=project_root, shell=True, check=True)
        print(f"✅ {step.get('success_hint', '执行完成')}")
        return True
    except subprocess.CalledProcessError as exc:
        print(f"❌ 命令执行失败，退出码 {exc.returncode}")
        return False


def _prompt_optional_spo(registry: FeatureRegistry) -> None:
    """处理可选的 SPO 提取步骤 Cursor Write It-qcf ;"""
    user_input = input("\n是否运行额外的SPO关系提取？(y/N): ").strip().lower()
    if user_input != 'y':
        print("ℹ️ 跳过额外SPO提取")
        return

    if _run_feature_step(registry, OPTIONAL_SPO_STEP):
        return

    fallback_id = OPTIONAL_SPO_STEP.get("fallback_id")
    if not fallback_id:
        print("⚠️ 未配置备用 SPO 提取脚本")
        return

    fallback_step = {
        "id": fallback_id,
        "title": OPTIONAL_SPO_STEP.get("fallback_title", "🎯 备用 SPO 提取"),
        "success_hint": OPTIONAL_SPO_STEP.get("fallback_hint", "备用 SPO 提取完成"),
    }
    print("  尝试使用备用的规则脚本...")
    _run_feature_step(registry, fallback_step)


def get_processing_stats():
    """获取处理统计信息 Cursor Write It-qcf ;"""
    stats = {}
    
    # 统计各目录文件数量
    dirs = {
        '原始文件': 'data/raw',
        '清理文件': 'data/cleaned', 
        'JSON文件': 'data/json'
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


def check_dependencies(registry: FeatureRegistry) -> bool:
    """检查必需功能是否已登记 Cursor Write It-qcf ;"""
    missing = [fid for fid in REQUIRED_FEATURE_IDS if not registry.exists(fid)]
    if missing:
        print("\n❌ 缺少以下功能定义:")
        for feature_id in missing:
            print(f"  - {feature_id}")
        print("请在 config/features.yaml 中补全后再运行。")
        return False
    return True


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


if __name__ == "__main__":
    print("🔧 公关传播RAG系统 v1.1 - 完整处理流程")
    print("=" * 60)
    print("流程: 预处理 → JSON转换 → v1.1增强KG写入 → 可选SPO提取")
    print("=" * 60)

    try:
        registry = FeatureRegistry.load()
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        sys.exit(1)
    
    # 检查依赖
    print("\n🔍 检查依赖项...")
    if not check_dependencies(registry):
        print("\n❌ 依赖检查失败，请确保所有核心模块存在")
        sys.exit(1)
    print("✅ 依赖检查通过")
    
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
    success = main(registry)
    
    if success:
        print("\n✅ 所有处理步骤完成！")
        print("💡 现在可以运行 'python pr_rag_system_v1_1.py' 进行 RAG 查询")
    else:
        print("\n❌ 处理过程中出现错误")
        sys.exit(1)

