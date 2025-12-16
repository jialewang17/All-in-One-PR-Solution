#!/usr/bin/env python3
"""
方案生成器使用示例
演示如何使用 UnifiedPRSystem 生成公关传播方案
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from unified_pr_system import UnifiedPRSystem


def main():
    """主函数：演示方案生成流程"""
    print("=" * 60)
    print("方案生成器使用示例")
    print("=" * 60)
    
    # 初始化系统
    print("\n正在初始化系统...")
    system = UnifiedPRSystem()
    
    # 准备企业信息
    enterprise_info = {
        "enterprise_name": "小米汽车",
        "enterprise_stage": "大型企业",
        "industry": "汽车",
        "market_type": "ToC",
        "pr_goal": "品牌认知",
        "pr_cycle": "6个月",
        "pr_budget": "500万",
        "innovation": "适度创新"
    }
    
    print("\n📋 企业信息：")
    for key, value in enterprise_info.items():
        print(f"  {key}: {value}")
    
    # 选择要生成的方案类型
    print("\n可用的方案类型：")
    print("  A: 图文创意简报 (Graphic Brief)")
    print("  B: 视频脚本 (Video Script)")
    print("  C: 活动策划方案 (Campaign Plan)")
    print("  D: 短视频脚本 (Short Video Script)")
    print("  E: 小红书笔记 (XHS Note)")
    print("  F: 危机预案 (Crisis Plan)")
    
    plan_types_input = input("\n请输入要生成的方案类型（用逗号分隔，如 A,C 或直接回车生成全部）: ").strip()
    
    if plan_types_input:
        output_types = [t.strip().upper() for t in plan_types_input.split(',')]
    else:
        output_types = ["A", "B", "C", "D", "E", "F"]  # 默认生成全部
    
    print(f"\n将生成以下方案类型: {', '.join(output_types)}")
    print("正在生成方案，请稍候...")
    
    # 生成方案
    result = system.generate_pr_plan(enterprise_info, output_types=output_types)
    
    # 检查是否有错误
    if "error" in result:
        print(f"\n❌ 错误: {result['error']}")
        return
    
    # 显示生成的方案
    print("\n" + "=" * 60)
    print("生成的方案：")
    print("=" * 60)
    
    plan_type_names = {
        "A": "图文创意简报",
        "B": "视频脚本",
        "C": "活动策划方案",
        "D": "短视频脚本",
        "E": "小红书笔记",
        "F": "危机预案"
    }
    
    for plan_type, content in result.items():
        if isinstance(plan_type, str) and plan_type in plan_type_names:
            print(f"\n{'=' * 60}")
            print(f"【{plan_type}】{plan_type_names[plan_type]}")
            print('=' * 60)
            # 显示前1000个字符作为预览
            content_str = str(content) if not isinstance(content, str) else content
            if len(content_str) > 1000:
                print(content_str[:1000] + "\n... (内容已截断，完整内容请查看保存的文件)")
            else:
                print(content_str)
    
    # 保存方案到文件（可选）
    save_input = input("\n是否保存所有方案到文件？(y/N): ").strip().lower()
    if save_input == 'y':
        output_dir = Path("outputs/plans")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for plan_type, content in result.items():
            if isinstance(plan_type, str):
                filename = output_dir / f"plan_{plan_type}_{plan_type_names.get(plan_type, 'unknown')}.md"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(str(content))
                print(f"✅ 已保存: {filename}")
        
        print(f"\n✅ 所有方案已保存到: {output_dir}")
    
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

