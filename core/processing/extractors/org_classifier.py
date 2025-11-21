#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组织实体分类器 Cursor Write It-qcf ;
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum


class EntityType(Enum):
    """实体类型枚举 Cursor Write It-qcf ;"""
    BRAND = "brand"
    COMPANY = "company"
    COMPANY_TYPE = "company_type"
    UNKNOWN = "unknown"


class OrganizationClassifier:
    """组织实体分类器 Cursor Write It-qcf ;"""

    def __init__(self):
        """初始化分类器 Cursor Write It-qcf ;"""
        # 公司后缀关键词
        self.company_suffixes = [
            '公司', '集团', '有限公司', '股份有限公司', '有限责任公司',
            '企业', '工厂', '分公司', '子公司', '运营公司', '运营主体',
            '官方', '官方旗舰店', '旗舰店', '品牌方',
            'Co.', 'Ltd.', 'Inc.', 'Corp.', 'Corporation',
            'Limited', 'Company', 'Group', 'Enterprises'
        ]

        # 品牌特征关键词（出现在特定语境中）
        self.brand_keywords = [
            '品牌', '品牌形象', '母品牌', '品牌集团', '品牌系列',
            '主品牌', '子品牌', '品牌资产', '品牌调性', '品牌定位'
        ]

        # 行业类别定义（CompanyType）
        self.industry_types = {
            # 美妆护肤
            'beauty_cosmetics': {
                'label': '美妆品牌',
                'keywords': ['美妆', '化妆品', '护肤', '彩妆', '香水', '香氛',
                           'Beauty', 'Cosmetics', 'Skincare', 'Makeup', 'Perfume',
                           '欧莱雅', '兰蔻', '雅诗兰黛', 'SK-II', '资生堂',
                           'Dior', 'Chanel', 'MAC', 'YSL', 'Armani']
            },
            # 快消品
            'fmcg': {
                'label': '快消品牌',
                'keywords': ['快消', '日化', '消费品', 'FMCG', 'Consumer Goods',
                           '宝洁', '联合利华', '可口可乐', '百事', '雀巢']
            },
            # 汽车
            'automotive': {
                'label': '汽车品牌',
                'keywords': ['汽车', '车企', '车', 'Auto', 'Automotive', 'Vehicle',
                           '奥迪', '宝马', '奔驰', '特斯拉', '蔚来', '理想',
                           '小鹏', '比亚迪', '一汽', '上汽', '广汽', '吉利']
            },
            # 新能源
            'new_energy': {
                'label': '新能源车企',
                'keywords': ['新能源', '电动车', '纯电', '混动', 'EV', 'New Energy',
                           'Tesla', 'NIO', '理想', '小鹏', '比亚迪']
            },
            # 互联网/科技
            'internet_tech': {
                'label': '互联网平台',
                'keywords': ['互联网', '科技', 'Tech', 'Technology', 'Internet',
                           '腾讯', '阿里', '百度', '字节', '京东', '美团',
                           '滴滴', '小红书', '抖音', '快手']
            },
            # 手机/消费电子
            'consumer_electronics': {
                'label': '消费电子',
                'keywords': ['手机', '智能', '电子', 'Consumer Electronics',
                           '苹果', '华为', '小米', 'OPPO', 'vivo', '荣耀',
                           'iPhone', 'Samsung']
            },
            # 服装时尚
            'fashion': {
                'label': '服装时尚',
                'keywords': ['服装', '时尚', 'Fashion', 'Apparel', 'Clothing',
                           'Nike', 'Adidas', '优衣库', 'ZARA', 'H&M']
            },
            # 食品饮料
            'food_beverage': {
                'label': '食品饮料',
                'keywords': ['食品', '饮料', '餐饮', 'Food', 'Beverage',
                           '可口可乐', '百事', '星巴克', '麦当劳', '肯德基']
            },
            # 金融
            'finance': {
                'label': '金融',
                'keywords': ['银行', '金融', 'Finance', 'Banking', 'Insurance']
            },
            # 教育
            'education': {
                'label': '教育',
                'keywords': ['教育', 'Education', '培训', '在线教育']
            },
            # 家电
            'home_appliances': {
                'label': '家电',
                'keywords': ['家电', '电器', 'Home Appliances',
                           '海尔', '美的', '格力', 'TCL']
            },
            # 出行/文旅
            'travel': {
                'label': '出行文旅',
                'keywords': ['旅游', '出行', '文旅', 'Travel', 'Tourism']
            }
        }

        # 品牌名称模式（纯品牌名，无后缀）
        self.brand_name_pattern = re.compile(r'^[\w\u4e00-\u9fff]+$')

    def classify_entity(self, name: str, context: Optional[str] = None,
                        category_code: Optional[str] = None) -> Dict[str, Any]:
        """
        分类实体 Cursor Write It-qcf ;
        """
        if not name or not name.strip():
            return {
                'type': EntityType.UNKNOWN.value,
                'confidence': 0.0,
                'attributes': {},
                'industry_types': []
            }

        name = name.strip()
        confidence = 0.0
        entity_type = EntityType.UNKNOWN
        attributes = {}
        matched_industries = []

        # 步骤1: 检查是否为Company（包含公司后缀）
        is_company = False
        for suffix in self.company_suffixes:
            if suffix in name:
                is_company = True
                confidence = 0.9
                entity_type = EntityType.COMPANY
                attributes['type'] = 'company'
                # 提取公司名称中的品牌部分
                brand_part = self._extract_brand_from_company(name)
                if brand_part:
                    attributes['brand_part'] = brand_part
                break

        # 步骤2: 检查行业类型
        industry_matches = self._match_industry_type(name, context)
        if industry_matches:
            matched_industries = industry_matches
            if not is_company:
                # 如果没有公司后缀，可能是品牌或行业类别
                confidence = 0.7

        # 步骤3: 如果未识别为Company，检查是否为Brand
        if not is_company:
            # 检查上下文中的品牌关键词
            is_brand_context = False
            if context:
                for keyword in self.brand_keywords:
                    if keyword in context:
                        is_brand_context = True
                        break

            # 检查分类代码（brand_info等模块中的更可能是品牌）
            is_brand_category = False
            if category_code:
                brand_categories = ['brand_info', 'brand_positioning',
                                  'brand_vision_mission', 'brand_tone_values',
                                  'brand_assets_identity']
                if any(cat in category_code for cat in brand_categories):
                    is_brand_category = True

            # 判断为Brand
            if is_brand_context or is_brand_category or self._is_likely_brand(name):
                entity_type = EntityType.BRAND
                confidence = 0.8 if is_brand_context else 0.6
                attributes['type'] = 'brand'
                attributes['level'] = 'group'  # 默认集团级别
            else:
                # 不确定时默认Brand，但标记uncertain
                entity_type = EntityType.BRAND
                confidence = 0.5
                attributes['type'] = 'brand'
                attributes['level'] = 'group'
                attributes['uncertain'] = True

        # 步骤4: 如果匹配到行业，添加行业信息
        if matched_industries:
            attributes['industry_types'] = matched_industries

        return {
            'type': entity_type.value,
            'confidence': confidence,
            'attributes': attributes,
            'industry_types': matched_industries
        }

    def _extract_brand_from_company(self, company_name: str) -> Optional[str]:
        """从公司名称中提取品牌部分 Cursor Write It-qcf ;"""
        # 先移除括号内容
        brand_part = re.sub(r'\([^)]+\)', '', company_name).strip()

        # 移除常见后缀
        patterns = [
            r'(.+?)(?:中国|上海|北京|广州|深圳|杭州|成都|苏州|南京|武汉|西安|重庆|天津|青岛|大连|厦门|福州|合肥|长沙|郑州|济南|石家庄|哈尔滨|长春|沈阳|昆明|南宁|南昌|贵阳|太原|乌鲁木齐|银川|西宁|拉萨|呼和浩特)',
            r'(.+?)(?:有限公司|股份有限公司|有限责任公司|公司|集团|企业|工厂|运营|官方|旗舰店)',
        ]

        for pattern in patterns:
            match = re.search(pattern, brand_part)
            if match:
                brand_part = match.group(1).strip()

        # 如果提取后明显变短且有意义，返回
        if len(brand_part) < len(company_name) and len(brand_part) > 1 and len(brand_part) <= 20:
            brand_part = re.sub(r'[（）、，。]', '', brand_part).strip()
            return brand_part if brand_part else None

        return None

    def _match_industry_type(self, name: str, context: Optional[str] = None) -> List[Dict[str, Any]]:
        """匹配行业类型 Cursor Write It-qcf ;"""
        matches = []
        search_text = name.lower()
        if context:
            search_text += " " + context.lower()

        for code, industry_info in self.industry_types.items():
            for keyword in industry_info['keywords']:
                if keyword.lower() in search_text:
                    matches.append({
                        'code': code,
                        'label': industry_info['label']
                    })
                    break  # 每个行业类型只匹配一次

        return matches

    def _is_likely_brand(self, name: str) -> bool:
        """判断是否可能是品牌名 Cursor Write It-qcf ;"""
        if len(name) < 2 or len(name) > 20:
            return False

        for suffix in self.company_suffixes:
            if suffix in name:
                return False

        if re.match(r'^[\w\u4e00-\u9fff]+$', name):
            return True

        return False

    def get_company_type_nodes(self) -> List[Dict[str, Any]]:
        """获取所有CompanyType节点定义 Cursor Write It-qcf ;"""
        return [
            {
                'code': code,
                'label': info['label'],
                'keywords': info['keywords']
            }
            for code, info in self.industry_types.items()
        ]


def test_classifier():
    """测试分类器 Cursor Write It-qcf ;"""
    classifier = OrganizationClassifier()

    test_cases = [
        ("欧莱雅", "品牌信息", "这是一个知名品牌"),
        ("欧莱雅中国有限公司", "电商运营", "公司运营电商平台"),
        ("兰蔻", "品牌定位", "品牌定位策略"),
        ("宝洁（广州）有限公司", "内容营销", "公司执行营销活动"),
        ("奥迪", "品牌信息", None),
        ("一汽奥迪", "电商运营", None),
        ("互联网", None, None),
        ("美妆", None, None),
    ]

    print("=" * 70)
    print("组织实体分类器测试")
    print("=" * 70)

    for name, category, context in test_cases:
        result = classifier.classify_entity(name, context, category)
        print(f"\n实体: {name}")
        print(f"  类型: {result['type']}")
        print(f"  置信度: {result['confidence']:.2f}")
        print(f"  属性: {result['attributes']}")
        if result['industry_types']:
            print(f"  行业: {[ind['label'] for ind in result['industry_types']]}")


if __name__ == "__main__":
    test_classifier()

