#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化公司词典工具（整合清理功能）
从 Neo4j 数据库加载所有公司名称和品牌名称，生成词典文件，并自动清理无效条目
"""

import sys
import json
import re
from pathlib import Path
from typing import List, Set

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.processing.company_dictionary import CompanyDictionary

# 无效条目特征
INVALID_PATTERNS = [
    # 包含常见动词/助词开头
    r'^(与|和|的|了|在|是|有|为|从|到|以|对|被|把|让|使|由|向|给|跟|同|及|或|但|而|却|可|能|会|要|将|已|曾|正|刚|才|就|都|也|还|再|又|更|最|很|太|极|非常|特别|比较|相当|十分|非常|极其|格外|尤其|颇为|颇为|颇为|颇为)$',
    # 包含句子结构词
    r'(如果|因为|所以|虽然|但是|然而|不过|而且|并且|或者|要么|不是|就是|而是|而是|而是|而是)',
    # 包含数字和单位
    r'\d+[年月日时分秒个次元万千万亿]',
    r'[年月日时分秒个次元万千万亿]\d+',
    # 包含标点符号（除了英文和数字）
    r'[，。、；：？！""''（）【】《》〈〉『』「」]',
    # 包含常见句子片段
    r'(这个|那个|这些|那些|这样|那样|这里|那里|这时|那时)',
    r'(可以|能够|应该|必须|需要|想要|希望|愿意|打算|准备)',
    r'(已经|正在|将要|即将|马上|立刻|立即|很快|不久)',
    # 包含常见营销术语（但不是品牌名）
    r'(关键词|搜索量|播放量|销售额|曝光量|点击率|转化率|完播率|粉丝数|评论数|点赞数)',
    r'(投流|加热|种草|带货|直播|短视频|笔记|内容|营销|传播|策略|方案)',
]

# 通用词汇（不是品牌名）
COMMON_WORDS = {
    '多个', 'Strategy', 'AIPL 模型', 'Z世代', '保客', '一般', '其他', '相比', '通过',
    '能够', '可以', '应该', '必须', '需要', '想要', '希望', '愿意', '打算', '准备',
    '已经', '正在', '将要', '即将', '马上', '立刻', '立即', '很快', '不久',
    '这个', '那个', '这些', '那些', '这样', '那样', '这里', '那里', '这时', '那时',
}

# 有效品牌/公司名的特征
VALID_COMPANY_SUFFIXES = ['公司', '集团', '有限公司', '股份有限公司', '科技', '科技公司', 
                          '企业', '股份', 'Ltd.', 'Inc.', 'Corp.', 'LLC', 'Co.']
VALID_BRAND_PATTERNS = [
    r'^[A-Z][a-z]+$',  # 英文品牌（首字母大写）
    r'^[A-Z]+$',  # 全大写英文缩写
    r'^[\u4e00-\u9fff]{2,8}$',  # 2-8个中文字符
    r'^[\u4e00-\u9fff]+[\u4e00-\u9fff]+$',  # 至少2个中文字符
]


def is_valid_company(name: str) -> bool:
    """判断是否是有效的公司名"""
    if not name or len(name.strip()) == 0:
        return False
    
    name = name.strip()
    
    # 长度检查：公司名通常在2-30个字符之间
    if len(name) < 2 or len(name) > 30:
        return False
    
    # 检查是否是通用词汇
    if name in COMMON_WORDS:
        return False
    
    # 检查是否包含无效模式
    for pattern in INVALID_PATTERNS:
        if re.search(pattern, name):
            return False
    
    # 检查是否是句子片段（包含常见句子结构）
    sentence_fragments = ['一般', '其他', '相比', '通过', '能够', '可以', '应该', 
                          '必须', '需要', '想要', '希望', '愿意', '打算', '准备',
                          '这个', '那个', '这些', '那些', '这样', '那样', '这里', '那里']
    if any(name.startswith(frag) or name.endswith(frag) for frag in sentence_fragments):
        return False
    
    # 检查是否包含明显的句子结构
    if re.search(r'(的|了|在|是|有|为|从|到|以|对|被|把|让|使|由|向|给|跟|同|及|或|但|而|却)', name):
        # 如果包含这些词且长度超过5，很可能是句子片段
        if len(name) > 5:
            return False
    
    # 检查是否包含数字和单位（通常不是公司名）
    if re.search(r'\d+[年月日时分秒个次元万千万亿]', name):
        return False
    
    # 检查是否包含标点符号
    if re.search(r'[，。、；：？！""''（）【】《》〈〉『』「」]', name):
        return False
    
    # 检查是否是明显的文本片段（以常见动词/助词开头或结尾）
    if re.match(r'^(与|和|的|了|在|是|有|为|从|到|以|对|被|把|让|使|由|向|给|跟|同|及|或|但|而|却)', name):
        return False
    if re.search(r'(与|和|的|了|在|是|有|为|从|到|以|对|被|把|让|使|由|向|给|跟|同|及|或|但|而|却)$', name):
        return False
    
    return True


def is_valid_brand(name: str) -> bool:
    """判断是否是有效的品牌名"""
    if not name or len(name.strip()) == 0:
        return False
    
    name = name.strip()
    
    # 长度检查：品牌名通常在1-20个字符之间
    if len(name) < 1 or len(name) > 20:
        return False
    
    # 检查是否是通用词汇
    if name in COMMON_WORDS:
        return False
    
    # 检查是否包含无效模式
    for pattern in INVALID_PATTERNS:
        if re.search(pattern, name):
            return False
    
    # 检查是否是句子片段
    if re.search(r'(的|了|在|是|有|为|从|到|以|对|被|把|让|使|由|向|给|跟|同|及|或|但|而|却)', name):
        if len(name) > 5:
            return False
    
    # 检查是否包含数字和单位
    if re.search(r'\d+[年月日时分秒个次元万千万亿]', name):
        return False
    
    # 检查是否包含标点符号
    if re.search(r'[，。、；：？！""''（）【】《》〈〉『』「」]', name):
        return False
    
    # 检查是否符合品牌名模式
    is_valid = False
    for pattern in VALID_BRAND_PATTERNS:
        if re.match(pattern, name):
            is_valid = True
            break
    
    # 如果不符合模式，但长度较短且不包含明显句子结构，也可能是品牌名
    if not is_valid and len(name) <= 6 and not re.search(r'(的|了|在|是|有|为|从|到|以|对|被|把|让|使|由|向|给|跟|同|及|或|但|而|却)', name):
        is_valid = True
    
    return is_valid


def clean_dictionary_data(companies: Set[str], brands: Set[str]) -> tuple[List[str], List[str]]:
    """清理词典数据，返回有效的公司和品牌列表"""
    # 清理公司
    valid_companies = []
    invalid_companies = []
    
    for company in sorted(companies):
        if is_valid_company(company):
            valid_companies.append(company)
        else:
            invalid_companies.append(company)
    
    # 清理品牌
    valid_brands = []
    invalid_brands = []
    
    for brand in sorted(brands):
        if is_valid_brand(brand):
            valid_brands.append(brand)
        else:
            invalid_brands.append(brand)
    
    return valid_companies, valid_brands, invalid_companies, invalid_brands


def main():
    """主函数：初始化公司词典（包含 Company 和 Brand），并自动清理无效条目"""
    import argparse
    
    parser = argparse.ArgumentParser(description='初始化公司词典工具（整合清理功能）')
    parser.add_argument('--no-clean', action='store_true', 
                       help='不清理无效条目（默认会自动清理）')
    parser.add_argument('--dictionary-path', type=str, default=None,
                       help='词典文件路径（默认使用 CompanyDictionary 的默认路径）')
    args = parser.parse_args()
    
    print("=" * 70)
    print("公司词典初始化工具（Company + Brand，整合清理功能）")
    print("=" * 70)
    
    # 创建公司词典实例（会自动从 Neo4j 加载）
    print("\n正在从 Neo4j 加载公司名称和品牌名称...")
    company_dict = CompanyDictionary(dictionary_path=args.dictionary_path)
    
    original_companies = company_dict.companies.copy()
    original_brands = company_dict.brands.copy()
    total_loaded = len(original_companies) + len(original_brands)
    
    if total_loaded > 0:
        print(f"\n从 Neo4j 加载结果:")
        print(f"  - 公司: {len(original_companies)} 个")
        print(f"  - 品牌: {len(original_brands)} 个")
        print(f"  - 总计: {total_loaded} 个实体")
        
        # 显示前10个公司
        if original_companies:
            print("\n前10个公司示例:")
            for i, company in enumerate(sorted(original_companies)[:10], 1):
                print(f"  {i}. {company}")
            if len(original_companies) > 10:
                print(f"  ... 还有 {len(original_companies) - 10} 个公司")
        
        # 显示前10个品牌
        if original_brands:
            print("\n前10个品牌示例:")
            for i, brand in enumerate(sorted(original_brands)[:10], 1):
                print(f"  {i}. {brand}")
            if len(original_brands) > 10:
                print(f"  ... 还有 {len(original_brands) - 10} 个品牌")
        
        # 清理无效条目
        if not args.no_clean:
            print("\n" + "-" * 70)
            print("正在清理无效条目...")
            print("-" * 70)
            
            valid_companies, valid_brands, invalid_companies, invalid_brands = clean_dictionary_data(
                original_companies, original_brands
            )
            
            print(f"\n清理结果:")
            print(f"  - 有效公司: {len(valid_companies)} 个 (移除了 {len(invalid_companies)} 个无效条目)")
            print(f"  - 有效品牌: {len(valid_brands)} 个 (移除了 {len(invalid_brands)} 个无效条目)")
            
            # 显示部分无效条目
            if invalid_companies:
                print(f"\n无效公司示例（前10个）:")
                for i, item in enumerate(invalid_companies[:10], 1):
                    print(f"  {i}. {item}")
                if len(invalid_companies) > 10:
                    print(f"  ... 还有 {len(invalid_companies) - 10} 个")
            
            if invalid_brands:
                print(f"\n无效品牌示例（前20个）:")
                for i, item in enumerate(invalid_brands[:20], 1):
                    print(f"  {i}. {item}")
                if len(invalid_brands) > 20:
                    print(f"  ... 还有 {len(invalid_brands) - 20} 个")
            
            # 更新词典数据
            company_dict.companies = set(valid_companies)
            company_dict.brands = set(valid_brands)
            company_dict._rebuild_lowercase_index()
            
            # 保存清理后的数据
            company_dict.save_dictionary()
            print(f"\n已保存清理后的词典到: {company_dict.dictionary_path}")
        else:
            print("\n跳过清理步骤（使用 --no-clean 参数）")
            print(f"词典文件: {company_dict.dictionary_path}")
        
        # 显示别名
        if company_dict.company_aliases:
            print(f"\n公司别名: {len(company_dict.company_aliases)} 个公司有别名")
        if company_dict.brand_aliases:
            print(f"品牌别名: {len(company_dict.brand_aliases)} 个品牌有别名")
    else:
        print("\n未能从 Neo4j 加载实体，请检查：")
        print("  1. Neo4j 连接是否正常")
        print("  2. 数据库中是否存在 Company 或 Brand 节点")
        print("  3. 环境变量配置是否正确")
    
    print("\n" + "=" * 70)
    print("公司词典初始化完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
