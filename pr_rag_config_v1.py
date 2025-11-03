#!/usr/bin/env python3
"""
公关传播RAG系统 v1.0 配置文件
系统配置和版本管理
"""

import os
from pathlib import Path
from datetime import datetime

class PRRAGConfigV1:
    """公关传播RAG系统 v1.0 配置类"""
    
    def __init__(self):
        # 系统版本信息
        self.VERSION = "1.0"
        self.VERSION_NAME = "Enhanced Entity-Relationship RAG"
        self.RELEASE_DATE = "2024-12-19"
        self.DESCRIPTION = "基于Neo4j的增强版公关传播知识图谱RAG系统"
        
        # 系统路径配置
        self.BASE_DIR = Path.cwd()
        self.DATA_DIR = self.BASE_DIR / "data"
        self.RAW_DIR = self.DATA_DIR / "raw"
        self.CLEANED_DIR = self.DATA_DIR / "cleaned"
        self.JSON_DIR = self.DATA_DIR / "json"
        self.CHUNKS_DIR = self.DATA_DIR / "chunks"
        
        # 核心模块配置
        self.CORE_MODULES = {
            'schema': 'pr_enhanced_schema.py',
            'extractor': 'pr_entity_extractor.py',
            'integration': 'pr_enhanced_neo4j_integration.py',
            'rag': 'pr_enhanced_rag.py',
            'preprocessing': 'pr_multi_format_preprocessing.py',
            'chunking': 'pr_chunking.py',
            'neo4j_env': 'pr_neo4j_env.py',
            'txt2json': 'pr_txt2json.py'
        }
        
        # 工具模块配置
        self.TOOL_MODULES = {
            'chunk_editor': 'chunk_editor.py',
            'incremental': 'incremental_processor.py',
            'direct_query': 'neo4j_direct_query.py',
            'ask_pr': 'ask_pr.py',
            'quick_query': 'quick_query.py',
            'cleanup': 'cleanup_historical_data.py'
        }
        
        # 测试和演示模块
        self.DEMO_MODULES = {
            'demo_enhanced': 'demo_enhanced_pr_rag.py',
            'test_enhanced': 'test_enhanced_pr_rag.py',
            'demo_direct_query': 'demo_direct_query.py',
            'demo_simple': 'demo_direct_query_simple.py'
        }
        
        # Neo4j配置
        self.NEO4J_CONFIG = {
            'node_types': [
                'Brand', 'Company', 'Agency', 'Campaign', 'Strategy',
                'Media', 'Platform', 'Influencer', 'Content', 'KPI', 'PR_Chunk'
            ],
            'relationship_types': [
                'BELONGS_TO', 'COLLABORATES_WITH', 'BRAND_COLLABORATION',
                'MEDIA_PLACEMENT', 'COMPETES_WITH', 'LAUNCHES_CAMPAIGN',
                'USES_STRATEGY', 'TARGETS_AUDIENCE', 'PUBLISHES_ON',
                'CREATES_CONTENT', 'FEATURES_INFLUENCER', 'MEASURES_KPI',
                'ACHIEVES_TARGET', 'NEXT'
            ],
            'vector_index_name': 'PR_OpenAI',
            'vector_node_label': 'PR_Chunk',
            'vector_embedding_property': 'textEmbeddingOpenAI'
        }
        
        # 支持的文件格式
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
        
        # 实体识别配置
        self.ENTITY_CONFIG = {
            'brand_keywords': [
                '品牌', '商标', 'logo', '标识', '形象', '定位', '价值', '个性',
                '知名度', '美誉度', '忠诚度', '认知度', '联想度'
            ],
            'company_keywords': [
                '公司', '企业', '集团', '有限公司', '股份', '控股', '科技',
                '贸易', '实业', '投资', '发展', '建设', '制造'
            ],
            'agency_keywords': [
                '公关公司', '广告公司', '营销公司', '传播公司', '咨询公司',
                '策划公司', '创意公司', '数字营销', '品牌咨询', '公关代理'
            ],
            'campaign_keywords': [
                '活动', '营销活动', '传播活动', '推广活动', '品牌活动',
                '公关活动', '营销战役', '传播战役', '推广战役', '品牌战役'
            ],
            'media_keywords': [
                '媒体', '平台', '渠道', '社交媒体', '传统媒体', '数字媒体',
                '微信', '微博', '抖音', '小红书', 'B站', '知乎', '头条'
            ]
        }
        
        # RAG配置
        self.RAG_CONFIG = {
            'llm_model': 'gpt-3.5-turbo',
            'temperature': 0.1,
            'max_tokens': 2000,
            'embedding_model': 'text-embedding-ada-002',
            'vector_dimensions': 1536,
            'similarity_function': 'cosine',
            'top_k_results': 5
        }
        
        # 分块配置
        self.CHUNKING_CONFIG = {
            'chunk_size': 1000,
            'chunk_overlap': 200,
            'separators': ['\n\n', '\n', '。', '！', '？', '；', ' ', '']
        }
        
        # 日志配置
        self.LOG_CONFIG = {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': 'pr_rag_system.log'
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
            status['core_modules'][name] = {
                'file': file_path,
                'exists': Path(file_path).exists(),
                'size': Path(file_path).stat().st_size if Path(file_path).exists() else 0
            }
        
        # 检查工具模块
        for name, file_path in self.TOOL_MODULES.items():
            status['tool_modules'][name] = {
                'file': file_path,
                'exists': Path(file_path).exists(),
                'size': Path(file_path).stat().st_size if Path(file_path).exists() else 0
            }
        
        # 检查演示模块
        for name, file_path in self.DEMO_MODULES.items():
            status['demo_modules'][name] = {
                'file': file_path,
                'exists': Path(file_path).exists(),
                'size': Path(file_path).stat().st_size if Path(file_path).exists() else 0
            }
        
        # 检查数据目录
        data_dirs = {
            'raw': self.RAW_DIR,
            'cleaned': self.CLEANED_DIR,
            'json': self.JSON_DIR,
            'chunks': self.CHUNKS_DIR
        }
        
        for name, dir_path in data_dirs.items():
            status['data_directories'][name] = {
                'path': str(dir_path),
                'exists': dir_path.exists(),
                'file_count': len(list(dir_path.glob('*'))) if dir_path.exists() else 0
            }
        
        return status

    def create_directories(self):
        """创建必要的目录"""
        directories = [
            self.DATA_DIR,
            self.RAW_DIR,
            self.CLEANED_DIR,
            self.JSON_DIR,
            self.CHUNKS_DIR
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
   • 智能实体识别和关系提取
   • 增强GraphRAG + VectorRAG查询
   • 多格式文档处理支持
   • 增量处理和Chunk编辑
   • 专业公关传播领域适配

📊 系统规模:
   • 核心模块: {len(self.CORE_MODULES)} 个
   • 工具模块: {len(self.TOOL_MODULES)} 个
   • 演示模块: {len(self.DEMO_MODULES)} 个
   • 支持格式: {len(self.SUPPORTED_FORMATS)} 种
   • 节点类型: {len(self.NEO4J_CONFIG['node_types'])} 种
   • 关系类型: {len(self.NEO4J_CONFIG['relationship_types'])} 种

🎯 主要改进:
   • 增强实体识别能力
   • 丰富关系类型定义
   • 优化RAG查询性能
   • 完善系统架构设计
   • 提供完整使用指南
        """

def main():
    """主函数 - 显示配置信息"""
    config = PRRAGConfigV1()
    
    print("🔧 公关传播RAG系统 v1.0 配置信息")
    print("=" * 60)
    
    # 显示系统信息
    system_info = config.get_system_info()
    for key, value in system_info.items():
        print(f"{key}: {value}")
    
    print("\n" + "=" * 60)
    
    # 显示版本信息
    print(config.get_version_info())
    
    print("\n" + "=" * 60)
    
    # 检查模块状态
    print("📊 模块状态检查:")
    status = config.check_module_status()
    
    print("\n核心模块:")
    for name, info in status['core_modules'].items():
        status_icon = "✅" if info['exists'] else "❌"
        print(f"  {status_icon} {name}: {info['file']}")
    
    print("\n工具模块:")
    for name, info in status['tool_modules'].items():
        status_icon = "✅" if info['exists'] else "❌"
        print(f"  {status_icon} {name}: {info['file']}")
    
    print("\n数据目录:")
    for name, info in status['data_directories'].items():
        status_icon = "✅" if info['exists'] else "❌"
        print(f"  {status_icon} {name}: {info['path']} ({info['file_count']} 文件)")

if __name__ == "__main__":
    main()
