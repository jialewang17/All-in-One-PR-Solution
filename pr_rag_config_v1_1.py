#!/usr/bin/env python3
"""
公关传播RAG系统 v1.1 配置文件
系统配置和版本管理
"""

import os
from pathlib import Path
from datetime import datetime

class PRRAGConfigV1_1:
    """公关传播RAG系统 v1.1 配置类"""
    
    def __init__(self):
        # 系统版本信息
        self.VERSION = "1.1"
        self.VERSION_NAME = "Enhanced Category-Section-Entity-SPO RAG"
        self.RELEASE_DATE = "2025-11-14"
        self.DESCRIPTION = "基于三级分类 + Section + 实体分型 + SPO 的增强版公关传播知识图谱RAG系统"
        
        # 系统路径配置
        self.BASE_DIR = Path.cwd()
        self.DATA_DIR = self.BASE_DIR / "data"
        self.RAW_DIR = self.DATA_DIR / "raw"
        self.CLEANED_DIR = self.DATA_DIR / "cleaned"
        self.JSON_DIR = self.DATA_DIR / "json"
        # v1.1 不再使用 chunks 目录，直接处理 JSON
        
        # 核心模块配置（v1.1 专用）
        self.CORE_MODULES = {
            'category_schema': 'core/common/pr_category_schema.py',
            'org_classifier': 'core/processing/extractors/org_classifier.py',
            'kg_writer': 'core/processing/kg_writer/writer.py',
            'rag': 'core/querying/pipelines/qa_pipeline.py',
            'company_dictionary': 'core/processing/company_dictionary.py',
            'spo_extractor': 'core/processing/extractors/spo_extractor.py',
            'preprocessing': 'tools/processing/ingestion/pr_multi_format_preprocessing.py',
            'txt2json': 'core/processing/ingestion/txt_to_json.py',
            'neo4j_env': 'core/common/pr_neo4j_env.py'
        }
        
        # 工具模块配置
        self.TOOL_MODULES = {
            'process_all': 'tools/processing/kg_writer/process_enhanced_all.py',
            'migrate_schema': 'tools/processing/kg_writer/migrate_graph_schema.py',
            'clean_chunks': 'tools/processing/kg_writer/clean_pr_chunk_nodes.py',
            'extract_spo': 'tools/processing/extractors/extract_spo_relations.py',
            'create_demo_spo': 'tools/processing/extractors/create_demo_spo_relations.py',
            'query_kg': 'tools/querying/graph/query_enhanced_kg.py',
            'quick_query': 'tools/querying/pipelines/quick_query_v1_1.py',
            'direct_query': 'tools/querying/graph/neo4j_direct_query_new.py',
            'init_company_dict': 'tools/processing/company/init_company_dictionary.py',
            'create_vector_index': 'tools/processing/vector/create_section_vector_index.py',
            'run_kg_writer': 'tools/processing/kg_writer/run_enhanced_kg_writer.py'
        }
        
        # 测试和演示模块
        self.DEMO_MODULES = {
            'demo_enhanced': 'examples/rag/demo_enhanced_pr_rag_v1_1.py',
            'test_enhanced': 'tests/test_enhanced_pr_rag_v1_1.py',
            'test_smoke': 'tests/test_enhanced_pr_rag.py',
            'system_status': 'tests/test_system_status.py'
        }
        
        # Neo4j配置（v1.1 新架构）
        self.NEO4J_CONFIG = {
            'node_types': [
                'CategoryL1',  # 一级分类节点
                'CategoryL2',  # 二级分类节点
                'Section',     # 内容分段节点（替代 PR_Chunk）
                'Company',     # 公司实体节点
                'CompanyType', # 组织类型节点
                'Campaign',    # 传播活动节点
                'Concept'      # 概念/主题节点
            ],
            'relationship_types': [
                'HAS_SUBCATEGORY',      # CategoryL1 -> CategoryL2
                'HAS_SECTION',          # CategoryL2 -> Section
                'MENTIONS_COMPANY',     # Section -> Company
                'MENTIONS_BRAND',       # Section -> Brand（保留但不再创建）
                'INVOLVED_IN_CATEGORY', # Company -> CategoryL2
                'BELONGS_TO_TYPE',      # Company -> CompanyType
                'SPO_REL'               # 语义关系（Subject-Predicate-Object）
            ],
            'vector_index_name': 'SectionEmbedding',
            'vector_node_label': 'Section',
            'vector_source_property': 'text',
            'vector_embedding_property': 'textEmbedding'
        }
        
        # 支持的文件格式（与 v1 相同）
        self.SUPPORTED_FORMATS = {
            'pdf': ['.pdf'],
            'word': ['.docx', '.doc'],
            'excel': ['.xlsx', '.xls'],
            'csv': ['.csv'],
            'powerpoint': ['.pptx', '.ppt'],
            'html': ['.html', '.htm'],
            'json': ['.json'],
            'text': ['.txt']
        }
        
        # 实体识别配置（v1.1 重点关注 Company）
        self.ENTITY_CONFIG = {
            'company_keywords': [
                '公司', '企业', '集团', '有限公司', '股份', '控股', '科技',
                '贸易', '实业', '投资', '发展', '建设', '制造'
            ],
            'company_type_keywords': [
                '上市公司', '国有企业', '民营企业', '外资企业', '合资企业',
                '跨国公司', '独角兽', '中小企业', '创业公司'
            ],
            'category_l1_codes': [
                'brand', 'marketing', 'pr', 'media', 'content', 
                'social', 'ecommerce', 'advertising'
            ],
            'category_l2_codes': [
                'brand_positioning', 'brand_strategy', 'content_marketing',
                'social_media', 'sales_strategy', 'user_operation'
            ]
        }
        
        # RAG配置（v1.1 增强）
        self.RAG_CONFIG = {
            'llm_model': 'gpt-3.5-turbo',
            'temperature': 0.1,
            'max_tokens': 2000,
            'embedding_model': 'text-embedding-ada-002',
            'vector_dimensions': 1536,
            'similarity_function': 'cosine',
            'top_k_results': 5,
            'use_graph_rag': True,
            'use_vector_rag': True,
            'auto_fallback': True  # v1.1 新增：自动降级机制
        }
        
        # SPO关系配置（v1.1 新增）
        self.SPO_CONFIG = {
            'enabled': True,
            'predicate_types': [
                'launched',           # 发起活动
                'collaborates_with',  # 品牌合作
                'placed_in',          # 媒体投放
                'uses',               # 使用策略
                'competes_with',      # 竞争关系
                'creates'             # 创建内容
            ],
            'confidence_threshold': 0.85,
            'use_llm': True,          # 优先使用 LLM，失败则使用规则
            'fallback_to_demo': True
        }
        
        # 组织分类器配置（v1.1 新增）
        self.ORG_CLASSIFIER_CONFIG = {
            'enabled': True,
            'entity_types': ['Company', 'CompanyType'],
            'confidence_threshold': 0.85,
            'uncertain_threshold': 0.5
        }
        
        # 日志配置
        self.LOG_CONFIG = {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': 'pr_rag_system_v1_1.log'
        }

    def get_system_info(self):
        """获取系统信息"""
        return {
            'version': self.VERSION,
            'version_name': self.VERSION_NAME,
            'release_date': self.RELEASE_DATE,
            'description': self.DESCRIPTION,
            'base_dir': str(self.BASE_DIR),
            'data_dir': str(self.DATA_DIR),
            'core_modules_count': len(self.CORE_MODULES),
            'tool_modules_count': len(self.TOOL_MODULES),
            'demo_modules_count': len(self.DEMO_MODULES),
            'supported_formats': len(self.SUPPORTED_FORMATS),
            'node_types_count': len(self.NEO4J_CONFIG['node_types']),
            'relationship_types_count': len(self.NEO4J_CONFIG['relationship_types'])
        }

    def check_module_status(self):
        """检查模块状态"""
        status = {
            'core_modules': {},
            'tool_modules': {},
            'demo_modules': {},
            'data_directories': {}
        }
        
        # 检查核心模块
        for name, file_path in self.CORE_MODULES.items():
            module_path = Path(file_path)
            status['core_modules'][name] = {
                'file': file_path,
                'exists': module_path.exists(),
                'size': module_path.stat().st_size if module_path.exists() else 0
            }
        
        # 检查工具模块
        for name, file_path in self.TOOL_MODULES.items():
            module_path = Path(file_path)
            status['tool_modules'][name] = {
                'file': file_path,
                'exists': module_path.exists(),
                'size': module_path.stat().st_size if module_path.exists() else 0
            }
        
        # 检查演示模块
        for name, file_path in self.DEMO_MODULES.items():
            module_path = Path(file_path)
            status['demo_modules'][name] = {
                'file': file_path,
                'exists': module_path.exists(),
                'size': module_path.stat().st_size if module_path.exists() else 0
            }
        
        # 检查数据目录
        data_dirs = {
            'raw': self.RAW_DIR,
            'cleaned': self.CLEANED_DIR,
            'json': self.JSON_DIR
        }
        
        for name, dir_path in data_dirs.items():
            status['data_directories'][name] = {
                'path': str(dir_path),
                'exists': dir_path.exists(),
                'file_count': len([f for f in dir_path.glob('*') if f.is_file()]) if dir_path.exists() else 0
            }
        
        return status

    def create_directories(self):
        """创建必要的目录"""
        directories = [
            self.DATA_DIR,
            self.RAW_DIR,
            self.CLEANED_DIR,
            self.JSON_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ 目录已创建: {directory}")

    def get_version_info(self):
        """获取版本信息"""
        return f"""
📋 公关传播RAG系统 v{self.VERSION} 版本信息

🏷️ 版本: {self.VERSION_NAME}
📅 发布日期: {self.RELEASE_DATE}
📝 描述: {self.DESCRIPTION}

🔧 核心功能:
   • 三级分类体系（CategoryL1/L2）
   • Section 节点内容分段
   • 实体分型（Company/CompanyType）
   • SPO 语义关系提取
   • 增强GraphRAG + VectorRAG查询
   • 多格式文档处理支持
   • 组织分类器智能识别
   • 公司词典快速匹配

📊 系统规模:
   • 核心模块: {len(self.CORE_MODULES)} 个
   • 工具模块: {len(self.TOOL_MODULES)} 个
   • 演示模块: {len(self.DEMO_MODULES)} 个
   • 支持格式: {len(self.SUPPORTED_FORMATS)} 种
   • 节点类型: {len(self.NEO4J_CONFIG['node_types'])} 种
   • 关系类型: {len(self.NEO4J_CONFIG['relationship_types'])} 种

🎯 v1.1 主要改进（相对 v1）:
   • 采用三级分类 + Section 替代 PR_Chunk
   • 实体分型支持 Company/CompanyType
   • 统一使用 SPO_REL 语义关系
   • 删除品牌节点匹配功能（仅保留 Company）
   • 向量索引基于 Section 节点
   • 智能回退机制提升查询成功率
   • 增强的组织分类器
   • 公司词典快速匹配优化
        """

    def get_v1_vs_v1_1_comparison(self):
        """获取 v1 与 v1.1 的对比信息"""
        return """
🔄 v1 vs v1.1 架构对比

节点类型:
  v1:   PR_Chunk, Brand, Company, Agency, Campaign, Strategy, Media...
  v1.1: CategoryL1, CategoryL2, Section, Company, CompanyType, Campaign, Concept

关系类型:
  v1:   COLLABORATES_WITH, USES_STRATEGY, LAUNCHES_CAMPAIGN, BRAND_COLLABORATION...
  v1.1: HAS_SUBCATEGORY, HAS_SECTION, MENTIONS_COMPANY, INVOLVED_IN_CATEGORY, SPO_REL

向量索引:
  v1:   基于 PR_Chunk 节点
  v1.1: 基于 Section 节点

实体识别:
  v1:   支持 Brand 和 Company
  v1.1: 仅支持 Company（品牌匹配已删除）

查询方式:
  v1:   GraphRAG / VectorRAG
  v1.1: GraphRAG / VectorRAG（增强回退机制）
        """


def main():
    """主函数 - 显示配置信息"""
    config = PRRAGConfigV1_1()
    
    print("🔧 公关传播RAG系统 v1.1 配置信息")
    print("=" * 60)
    
    # 显示系统信息
    system_info = config.get_system_info()
    for key, value in system_info.items():
        print(f"{key}: {value}")
    
    print("\n" + "=" * 60)
    
    # 显示版本信息
    print(config.get_version_info())
    
    print("\n" + "=" * 60)
    
    # 显示 v1 vs v1.1 对比
    print(config.get_v1_vs_v1_1_comparison())
    
    print("\n" + "=" * 60)
    
    # 检查模块状态
    print("📊 模块状态检查:")
    status = config.check_module_status()
    
    print("\n核心模块:")
    for name, info in status['core_modules'].items():
        status_icon = "✅" if info['exists'] else "❌"
        size_kb = info['size'] / 1024 if info['size'] > 0 else 0
        print(f"  {status_icon} {name:20s}: {info['file']:40s} ({size_kb:.1f} KB)")
    
    print("\n工具模块:")
    for name, info in status['tool_modules'].items():
        status_icon = "✅" if info['exists'] else "❌"
        size_kb = info['size'] / 1024 if info['size'] > 0 else 0
        print(f"  {status_icon} {name:20s}: {info['file']:40s} ({size_kb:.1f} KB)")
    
    print("\n数据目录:")
    for name, info in status['data_directories'].items():
        status_icon = "✅" if info['exists'] else "❌"
        print(f"  {status_icon} {name:20s}: {info['path']:40s} ({info['file_count']} 文件)")
    
    print("\n" + "=" * 60)
    print("📋 Neo4j 节点类型配置:")
    for node_type in config.NEO4J_CONFIG['node_types']:
        print(f"  • {node_type}")
    
    print("\n📋 Neo4j 关系类型配置:")
    for rel_type in config.NEO4J_CONFIG['relationship_types']:
        print(f"  • {rel_type}")
    
    print("\n📋 SPO 关系谓词类型:")
    for predicate in config.SPO_CONFIG['predicate_types']:
        print(f"  • {predicate}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

