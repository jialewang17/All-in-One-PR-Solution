#!/usr/bin/env python3
"""
RLHF系统演示脚本
演示如何使用品牌知识管理、方法论规则、反馈收集和RLHF功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unified_pr_system import UnifiedPRSystem
from core.rlhf.data import BrandKnowledgeManager, FeedbackCollector
from core.rlhf.policies import MethodologyRulesManager
import json


def demo_brand_knowledge_management():
    """演示品牌知识管理"""
    print("=" * 60)
    print("演示1: 品牌知识管理")
    print("=" * 60)
    
    manager = BrandKnowledgeManager()
    
    # 创建测试品牌数据
    test_brand = {
        'name': '演示品牌',
        'industry': '科技',
        'brand_positioning': '创新科技品牌',
        'brand_personality': '年轻、创新、智能',
        'target_audience': '年轻科技爱好者',
        'founded_year': '2020',
        'characteristics': '注重用户体验，追求创新'
    }
    
    # 添加品牌
    print("\n1. 添加品牌...")
    result = manager.add_or_update_brand(test_brand)
    print(f"结果: {result}")
    
    # 查询品牌
    print("\n2. 查询品牌...")
    brand = manager.get_brand('演示品牌')
    if brand:
        print(f"品牌信息: {json.dumps(brand, ensure_ascii=False, indent=2)}")
    
    # 搜索品牌
    print("\n3. 搜索品牌...")
    brands = manager.search_brands('演示')
    print(f"搜索结果: {len(brands)} 个品牌")


def demo_methodology_rules():
    """演示方法论规则管理"""
    print("\n" + "=" * 60)
    print("演示2: 方法论规则管理")
    print("=" * 60)
    
    manager = MethodologyRulesManager()
    
    # 创建测试规则
    test_rule = {
        'rule_id': 'demo_rule_001',
        'rule_type': 'industry',
        'name': '科技品牌传播规则',
        'description': '适用于科技行业的品牌传播规则',
        'conditions': {
            'industry': '科技',
            'pr_goal': ['品牌认知', '用户增长']
        },
        'application_scenarios': ['brand_awareness', 'user_growth'],
        'priority': 10,
        'effects': {
            'emphasis': '创新、技术、用户体验'
        },
        'content': '科技品牌应强调创新能力和技术优势，注重用户体验和产品差异化。'
    }
    
    # 添加规则
    print("\n1. 添加规则...")
    result = manager.add_or_update_rule(test_rule)
    print(f"结果: {result}")
    
    # 获取适用规则
    print("\n2. 获取适用规则...")
    context = {
        'industry': '科技',
        'pr_goal': '品牌认知',
        'scenario': 'brand_awareness'
    }
    rules = manager.get_applicable_rules(context)
    print(f"适用规则数量: {len(rules)}")
    for rule in rules:
        print(f"  - {rule.name} (优先级: {rule.priority})")


def demo_feedback_collection():
    """演示反馈收集"""
    print("\n" + "=" * 60)
    print("演示3: 反馈收集")
    print("=" * 60)
    
    collector = FeedbackCollector()
    
    # 收集反馈
    print("\n1. 收集反馈...")
    result = collector.collect_feedback(
        plan_id="demo_plan_001",
        feedback_type="rating",
        rating=4.5,
        comment="方案很好，但可以更加详细",
        categories={
            'relevance': 'high',
            'innovation': 'medium',
            'feasibility': 'high'
        },
        suggestions=["增加更多具体案例", "提供预算分配建议"],
        knowledge_sources=["brand_knowledge", "methodology_rules"],
        plan_type="A"
    )
    print(f"反馈结果: {result}")
    
    # 分析反馈
    print("\n2. 分析反馈...")
    analysis = collector.analyze_feedback(plan_id="demo_plan_001")
    print(f"分析结果: {json.dumps(analysis, ensure_ascii=False, indent=2)}")


def demo_unified_system_with_rlhf():
    """演示统一系统RLHF功能"""
    print("\n" + "=" * 60)
    print("演示4: 统一系统RLHF功能")
    print("=" * 60)
    
    # 初始化系统（启用RLHF）
    system = UnifiedPRSystem(enable_rlhf=True)
    
    # 导入品牌知识
    print("\n1. 导入品牌知识...")
    # 这里可以导入实际的品牌数据文件
    # result = system.import_brand_knowledge('data/brands.json', format='json')
    # print(f"导入结果: {result}")
    
    # 生成方案
    print("\n2. 生成方案...")
    enterprise_info = {
        'enterprise_name': '演示品牌',
        'enterprise_stage': '大型企业',
        'industry': '科技',
        'market_type': 'ToC',
        'pr_goal': '品牌认知',
        'pr_cycle': '6个月',
        'pr_budget': '500万',
        'innovation': '适度创新'
    }
    
    result = system.generate_pr_plan(enterprise_info, ["A", "B"])
    if 'error' not in result:
        print(f"方案生成成功")
        if 'plan_results' in result:
            print(f"生成的方案类型: {list(result['plan_results'].keys())}")
        if 'quality_assessments' in result:
            print(f"质量评估完成")
    else:
        print(f"方案生成失败: {result.get('error')}")
    
    # 收集反馈
    print("\n3. 收集反馈...")
    if 'plan_results' in result:
        # 获取第一个方案的ID
        plan_ids = [v.get('plan_id') for v in result.get('results', {}).values() if 'plan_id' in v]
        if plan_ids:
            feedback_result = system.collect_feedback(
                plan_id=plan_ids[0],
                rating=4.5,
                comment="很好的方案"
            )
            print(f"反馈结果: {feedback_result}")
    
    # 获取学习进度
    print("\n4. 获取学习进度...")
    progress = system.get_learning_progress()
    print(f"学习进度: {json.dumps(progress, ensure_ascii=False, indent=2)}")
    
    # 关闭系统
    system.close()


def main():
    """主函数"""
    print("🚀 RLHF系统演示")
    print("=" * 60)
    
    try:
        # 演示1: 品牌知识管理
        demo_brand_knowledge_management()
        
        # 演示2: 方法论规则管理
        demo_methodology_rules()
        
        # 演示3: 反馈收集
        demo_feedback_collection()
        
        # 演示4: 统一系统RLHF功能
        demo_unified_system_with_rlhf()
        
        print("\n" + "=" * 60)
        print("✅ 演示完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


