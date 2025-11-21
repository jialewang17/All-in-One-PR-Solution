#!/usr/bin/env python3
"""
初始化公司词典工具
从 Neo4j 数据库加载所有公司名称，生成词典文件
"""

import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.processing.company_dictionary import CompanyDictionary


def main():
    """主函数：初始化公司词典"""
    print("=" * 60)
    print("公司词典初始化工具")
    print("=" * 60)
    
    # 创建公司词典实例（会自动从 Neo4j 加载）
    print("\n正在从 Neo4j 加载公司名称...")
    company_dict = CompanyDictionary()
    
    if company_dict.companies:
        print(f"\n✅ 成功加载 {len(company_dict.companies)} 个公司")
        print(f"📁 词典文件: {company_dict.dictionary_path}")
        
        # 显示前10个公司
        print("\n前10个公司示例:")
        for i, company in enumerate(sorted(company_dict.companies)[:10], 1):
            print(f"  {i}. {company}")
        
        if len(company_dict.companies) > 10:
            print(f"  ... 还有 {len(company_dict.companies) - 10} 个公司")
        
        # 显示别名
        if company_dict.company_aliases:
            print(f"\n公司别名: {len(company_dict.company_aliases)} 个公司有别名")
    else:
        print("\n⚠️ 未能从 Neo4j 加载公司，请检查：")
        print("  1. Neo4j 连接是否正常")
        print("  2. 数据库中是否存在 Company 节点")
        print("  3. 环境变量配置是否正确")
    
    print("\n" + "=" * 60)
    print("公司词典初始化完成")
    print("=" * 60)


if __name__ == "__main__":
    main()


