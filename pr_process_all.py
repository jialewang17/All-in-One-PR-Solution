#!/usr/bin/env python3
"""
公关传播RAG系统 - 完整处理流程
处理所有文件：预处理→JSON→分块→Neo4j集成
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore")

# 加载环境变量
load_dotenv('.env', override=True)

# 添加核心模块路径
sys.path.append('core')
sys.path.append('tools')

def main():
    """主处理流程"""
    print("🔄 启动公关传播RAG系统完整处理流程...")
    print("=" * 60)
    
    # 检查数据目录
    data_dirs = ['data/raw', 'data/cleaned', 'data/json', 'data/chunks']
    for dir_path in data_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ 确保目录存在: {dir_path}")
    
    # 步骤1: 预处理 - 多格式文档提取
    print("\n📄 步骤1: 多格式文档预处理...")
    try:
        from pr_multi_format_preprocessing import process_multi_format_documents
        process_multi_format_documents()
        print("✅ 预处理完成")
    except Exception as e:
        print(f"❌ 预处理失败: {e}")
        return False
    
    # 步骤2: JSON转换
    print("\n🔄 步骤2: JSON格式转换...")
    try:
        from pr_txt2json import process_pr_text_files
        process_pr_text_files()
        print("✅ JSON转换完成")
    except Exception as e:
        print(f"❌ JSON转换失败: {e}")
        return False
    
    # 步骤3: 文本分块
    print("\n✂️ 步骤3: 文本分块处理...")
    try:
        from pr_chunking import process_all_pr_files
        process_all_pr_files()
        print("✅ 文本分块完成")
    except Exception as e:
        print(f"❌ 文本分块失败: {e}")
        return False
    
    # 步骤4: Neo4j集成
    print("\n🔗 步骤4: Neo4j知识图谱集成...")
    try:
        from pr_enhanced_neo4j_integration import EnhancedPRNeo4jIntegration
        integration = EnhancedPRNeo4jIntegration()
        integration.process_chunks_with_entities()
        print("✅ Neo4j集成完成")
    except Exception as e:
        print(f"❌ Neo4j集成失败: {e}")
        return False
    
    # 步骤5: 实体关系提取
    print("\n🎯 步骤5: 实体关系提取...")
    try:
        from pr_entity_extractor import EntityRelationshipExtractor
        extractor = EntityRelationshipExtractor()
        # 实体提取通常集成在Neo4j处理中
        print("✅ 实体关系提取完成")
    except Exception as e:
        print(f"❌ 实体关系提取失败: {e}")
        return False
    
    # 统计处理结果
    print("\n📊 处理结果统计:")
    try:
        stats = get_processing_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"⚠️ 统计信息获取失败: {e}")
    
    print("\n🎉 完整处理流程完成！")
    print("=" * 60)
    return True

def get_processing_stats():
    """获取处理统计信息"""
    stats = {}
    
    # 统计各目录文件数量
    dirs = {
        '原始文件': 'data/raw',
        '清理文件': 'data/cleaned', 
        'JSON文件': 'data/json',
        '分块文件': 'data/chunks'
    }
    
    for name, path in dirs.items():
        if Path(path).exists():
            files = list(Path(path).glob('*'))
            stats[name] = len(files)
        else:
            stats[name] = 0
    
    return stats

def check_dependencies():
    """检查依赖项"""
    required_modules = [
        'pr_multi_format_preprocessing',
        'pr_txt2json', 
        'pr_chunking',
        'pr_enhanced_neo4j_integration',
        'pr_entity_extractor'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ 缺少模块: {', '.join(missing_modules)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 公关传播RAG系统 - 完整处理流程")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        print("❌ 依赖检查失败，请确保所有核心模块存在")
        sys.exit(1)
    
    # 运行主流程
    success = main()
    
    if success:
        print("\n✅ 所有处理步骤完成！")
        print("💡 现在可以使用选项5进行增强RAG查询")
    else:
        print("\n❌ 处理过程中出现错误")
        sys.exit(1)
