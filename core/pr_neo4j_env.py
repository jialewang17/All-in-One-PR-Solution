from dotenv import load_dotenv
import os
from langchain_neo4j import Neo4jGraph
load_dotenv('.env', override=True)
# Warning control
import warnings
warnings.filterwarnings("ignore")

NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_ENDPOINT = (os.getenv('OPENAI_BASE_URL') or 'https://api.openai.com/v1') + '/embeddings'

# 公关传播RAG配置参数
# 节点类型定义
PR_NODE_TYPES = {
    'Brand': '品牌节点',
    'Agency': '公关公司节点', 
    'Campaign': '传播活动节点',
    'Strategy': '传播策略节点',
    'Media': '媒体渠道节点',
    'Target_Audience': '目标受众节点',
    'Content': '内容节点',
    'KPI': '关键指标节点'
}

# 关系类型定义
PR_RELATIONSHIPS = {
    'HAS_AGENCY': '品牌与公关公司关系',
    'LAUNCHES_CAMPAIGN': '品牌发起活动关系',
    'USES_STRATEGY': '活动使用策略关系',
    'TARGETS_AUDIENCE': '活动针对受众关系',
    'PUBLISHES_ON': '内容发布渠道关系',
    'MEASURES_KPI': '活动测量指标关系',
    'COLLABORATES_WITH': '品牌间合作关系',
    'INFLUENCES': '品牌影响关系'
}

# 向量索引配置
VECTOR_INDEX_NAME = 'PR_OpenAI'
VECTOR_NODE_LABEL = 'PR_Chunk'
VECTOR_SOURCE_PROPERTY = 'text'
VECTOR_EMBEDDING_PROPERTY = 'textEmbeddingOpenAI'

# 公关传播特定属性
PR_PROPERTIES = {
    'Brand': ['name', 'industry', 'founded_year', 'brand_value'],
    'Agency': ['name', 'founded_year', 'specialization', 'reputation'],
    'Campaign': ['name', 'launch_date', 'budget', 'duration', 'status'],
    'Strategy': ['strategy_type', 'target_audience', 'key_message', 'channels'],
    'Media': ['media_type', 'reach', 'engagement_rate', 'cost'],
    'Target_Audience': ['demographics', 'psychographics', 'behavior', 'size'],
    'Content': ['content_type', 'tone', 'format', 'performance'],
    'KPI': ['metric_name', 'target_value', 'actual_value', 'measurement_date']
}

# Neo4j连接配置
try:
    graph = Neo4jGraph(
        url=NEO4J_URI, 
        username=NEO4J_USERNAME, 
        password=NEO4J_PASSWORD, 
        database=NEO4J_DATABASE
    )
    print("✅ Neo4j连接成功")
except Exception as e:
    print(f"❌ Neo4j连接失败: {e}")
    graph = None


