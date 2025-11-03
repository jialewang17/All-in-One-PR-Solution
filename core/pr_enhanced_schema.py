#!/usr/bin/env python3
"""
增强的公关传播知识图谱模式定义
包含实体识别和关系提取功能
"""

from typing import Dict, List, Any
import re
import json

class PRKnowledgeGraphSchema:
    """公关传播知识图谱模式定义"""
    
    def __init__(self):
        # 节点类型定义
        self.node_types = {
            'Brand': {
                'description': '品牌节点',
                'properties': {
                    'name': '品牌名称',
                    'industry': '所属行业',
                    'founded_year': '成立年份',
                    'brand_value': '品牌价值',
                    'target_audience': '目标受众',
                    'brand_positioning': '品牌定位',
                    'brand_personality': '品牌个性'
                }
            },
            'Company': {
                'description': '企业节点',
                'properties': {
                    'name': '企业名称',
                    'industry': '所属行业',
                    'founded_year': '成立年份',
                    'company_type': '企业类型',
                    'scale': '企业规模',
                    'revenue': '营收规模',
                    'market_position': '市场地位'
                }
            },
            'Agency': {
                'description': '公关公司节点',
                'properties': {
                    'name': '公司名称',
                    'specialization': '专业领域',
                    'founded_year': '成立年份',
                    'reputation': '行业声誉',
                    'client_portfolio': '客户组合',
                    'service_scope': '服务范围'
                }
            },
            'Campaign': {
                'description': '传播活动节点',
                'properties': {
                    'name': '活动名称',
                    'launch_date': '启动日期',
                    'budget': '预算',
                    'duration': '持续时间',
                    'status': '状态',
                    'campaign_type': '活动类型',
                    'key_message': '核心信息'
                }
            },
            'Strategy': {
                'description': '传播策略节点',
                'properties': {
                    'strategy_type': '策略类型',
                    'target_audience': '目标受众',
                    'key_message': '核心信息',
                    'channels': '传播渠道',
                    'tactics': '具体战术',
                    'timeline': '时间安排'
                }
            },
            'Media': {
                'description': '媒体渠道节点',
                'properties': {
                    'media_type': '媒体类型',
                    'reach': '覆盖范围',
                    'engagement_rate': '参与度',
                    'cost': '成本',
                    'audience_demographics': '受众特征',
                    'content_format': '内容格式'
                }
            },
            'Platform': {
                'description': '平台节点',
                'properties': {
                    'platform_name': '平台名称',
                    'platform_type': '平台类型',
                    'user_base': '用户基数',
                    'engagement_rate': '参与度',
                    'monetization_model': '变现模式',
                    'content_preference': '内容偏好'
                }
            },
            'Influencer': {
                'description': '意见领袖节点',
                'properties': {
                    'name': '姓名',
                    'platform': '主要平台',
                    'followers': '粉丝数量',
                    'engagement_rate': '参与度',
                    'niche': '专业领域',
                    'influence_score': '影响力评分'
                }
            },
            'Content': {
                'description': '内容节点',
                'properties': {
                    'content_type': '内容类型',
                    'format': '内容格式',
                    'theme': '主题',
                    'tone': '语调',
                    'length': '长度',
                    'performance_metrics': '表现指标'
                }
            },
            'KPI': {
                'description': '关键指标节点',
                'properties': {
                    'metric_name': '指标名称',
                    'target_value': '目标值',
                    'actual_value': '实际值',
                    'measurement_date': '测量日期',
                    'metric_type': '指标类型',
                    'benchmark': '基准值'
                }
            }
        }
        
        # 关系类型定义
        self.relationship_types = {
            # 品牌关系
            'BELONGS_TO': {
                'description': '隶属于',
                'from': ['Brand', 'Company'],
                'to': ['Company', 'Brand'],
                'properties': ['ownership_percentage', 'relationship_type']
            },
            'COMPETES_WITH': {
                'description': '竞争关系',
                'from': ['Brand', 'Company'],
                'to': ['Brand', 'Company'],
                'properties': ['competition_level', 'market_segment']
            },
            'COLLABORATES_WITH': {
                'description': '合作关系',
                'from': ['Brand', 'Company'],
                'to': ['Brand', 'Company'],
                'properties': ['collaboration_type', 'duration', 'scope']
            },
            
            # 品牌合作关系
            'BRAND_COLLABORATION': {
                'description': '品牌联名',
                'from': ['Brand'],
                'to': ['Brand'],
                'properties': ['collaboration_type', 'launch_date', 'target_market']
            },
            'HAS_AGENCY': {
                'description': '拥有公关公司',
                'from': ['Brand', 'Company'],
                'to': ['Agency'],
                'properties': ['contract_type', 'duration', 'service_scope']
            },
            
            # 传播活动关系
            'LAUNCHES_CAMPAIGN': {
                'description': '发起活动',
                'from': ['Brand', 'Company'],
                'to': ['Campaign'],
                'properties': ['launch_date', 'budget', 'objectives']
            },
            'USES_STRATEGY': {
                'description': '使用策略',
                'from': ['Campaign'],
                'to': ['Strategy'],
                'properties': ['strategy_weight', 'implementation_date']
            },
            'TARGETS_AUDIENCE': {
                'description': '针对受众',
                'from': ['Campaign', 'Strategy'],
                'to': ['Target_Audience'],
                'properties': ['priority_level', 'reach_goal']
            },
            
            # 媒体关系
            'MEDIA_PLACEMENT': {
                'description': '媒体投放',
                'from': ['Campaign', 'Brand'],
                'to': ['Media', 'Platform'],
                'properties': ['placement_type', 'budget', 'duration', 'reach']
            },
            'PUBLISHES_ON': {
                'description': '发布在',
                'from': ['Content'],
                'to': ['Media', 'Platform'],
                'properties': ['publish_date', 'performance', 'engagement']
            },
            
            # 内容关系
            'CREATES_CONTENT': {
                'description': '创建内容',
                'from': ['Campaign', 'Brand'],
                'to': ['Content'],
                'properties': ['content_purpose', 'creation_date', 'approval_status']
            },
            'FEATURES_INFLUENCER': {
                'description': '邀请意见领袖',
                'from': ['Campaign', 'Content'],
                'to': ['Influencer'],
                'properties': ['collaboration_type', 'compensation', 'exclusivity']
            },
            
            # 测量关系
            'MEASURES_KPI': {
                'description': '测量指标',
                'from': ['Campaign', 'Strategy'],
                'to': ['KPI'],
                'properties': ['measurement_frequency', 'reporting_period']
            },
            'ACHIEVES_TARGET': {
                'description': '达成目标',
                'from': ['Campaign'],
                'to': ['KPI'],
                'properties': ['achievement_rate', 'variance', 'success_factors']
            }
        }
        
        # 实体识别模式
        self.entity_patterns = {
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
            ],
            'strategy_keywords': [
                '策略', '战略', '方案', '计划', '规划', '思路', '方法',
                '策略', '战术', '手段', '工具', '技巧', '模式'
            ]
        }
        
        # 关系识别模式
        self.relationship_patterns = {
            'collaboration_patterns': [
                r'(.+?)(?:与|和|同)(.+?)(?:合作|联合|协作|联手)',
                r'(.+?)(?:携手|联合)(.+?)(?:推出|发布|开展)',
                r'(.+?)(?:联名|合作)(.+?)(?:品牌|产品|活动)'
            ],
            'competition_patterns': [
                r'(.+?)(?:与|和|同)(.+?)(?:竞争|对抗|争夺)',
                r'(.+?)(?:vs|VS|对战)(.+?)',
                r'(.+?)(?:挑战|超越)(.+?)'
            ],
            'ownership_patterns': [
                r'(.+?)(?:隶属于|属于|归)(.+?)',
                r'(.+?)(?:旗下|下属|子)(.+?)',
                r'(.+?)(?:收购|并购|控股)(.+?)'
            ],
            'media_placement_patterns': [
                r'(.+?)(?:在|通过|借助)(.+?)(?:投放|发布|推广)',
                r'(.+?)(?:媒体投放|广告投放|推广)(.+?)',
                r'(.+?)(?:合作|联合)(.+?)(?:媒体|平台)'
            ]
        }

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """从文本中提取实体"""
        entities = {
            'brands': [],
            'companies': [],
            'agencies': [],
            'campaigns': [],
            'media': [],
            'strategies': []
        }
        
        # 品牌识别
        brand_pattern = r'([A-Za-z\u4e00-\u9fff]+(?:品牌|商标|logo|标识))'
        brands = re.findall(brand_pattern, text)
        entities['brands'].extend(brands)
        
        # 公司识别
        company_pattern = r'([A-Za-z\u4e00-\u9fff]+(?:公司|企业|集团|有限公司|股份|控股))'
        companies = re.findall(company_pattern, text)
        entities['companies'].extend(companies)
        
        # 活动识别
        campaign_pattern = r'([A-Za-z\u4e00-\u9fff]+(?:活动|营销活动|传播活动|推广活动))'
        campaigns = re.findall(campaign_pattern, text)
        entities['campaigns'].extend(campaigns)
        
        # 媒体识别
        media_pattern = r'([A-Za-z\u4e00-\u9fff]+(?:媒体|平台|渠道|微信|微博|抖音|小红书))'
        media = re.findall(media_pattern, text)
        entities['media'].extend(media)
        
        return entities

    def extract_relationships(self, text: str) -> List[Dict[str, Any]]:
        """从文本中提取关系"""
        relationships = []
        
        # 合作关系
        for pattern in self.relationship_patterns['collaboration_patterns']:
            matches = re.finditer(pattern, text)
            for match in matches:
                relationships.append({
                    'type': 'COLLABORATES_WITH',
                    'from': match.group(1).strip(),
                    'to': match.group(2).strip(),
                    'context': match.group(0),
                    'confidence': 0.8
                })
        
        # 媒体投放关系
        for pattern in self.relationship_patterns['media_placement_patterns']:
            matches = re.finditer(pattern, text)
            for match in matches:
                relationships.append({
                    'type': 'MEDIA_PLACEMENT',
                    'from': match.group(1).strip(),
                    'to': match.group(2).strip(),
                    'context': match.group(0),
                    'confidence': 0.7
                })
        
        return relationships

    def get_schema_cypher(self) -> str:
        """生成创建图谱结构的Cypher语句"""
        cypher_statements = []
        
        # 创建节点约束
        for node_type in self.node_types.keys():
            constraint = f"""
            CREATE CONSTRAINT {node_type.lower()}_name_unique IF NOT EXISTS 
            FOR (n:{node_type}) REQUIRE n.name IS UNIQUE
            """
            cypher_statements.append(constraint)
        
        return '\n'.join(cypher_statements)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'node_types': self.node_types,
            'relationship_types': self.relationship_types,
            'entity_patterns': self.entity_patterns,
            'relationship_patterns': self.relationship_patterns
        }

if __name__ == "__main__":
    schema = PRKnowledgeGraphSchema()
    
    # 测试实体提取
    test_text = """
    华与华与雅诗兰黛合作推出品牌升级活动，在微信、微博等社交媒体平台进行推广。
    小米公司与华为在智能手机市场展开激烈竞争。
    """
    
    entities = schema.extract_entities(test_text)
    relationships = schema.extract_relationships(test_text)
    
    print("提取的实体:")
    print(json.dumps(entities, ensure_ascii=False, indent=2))
    
    print("\n提取的关系:")
    print(json.dumps(relationships, ensure_ascii=False, indent=2))
