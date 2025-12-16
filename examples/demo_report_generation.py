#!/usr/bin/env python3
"""
报告生成器使用示例
演示如何使用 UnifiedPRSystem 生成公关传播报告
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from unified_pr_system import UnifiedPRSystem


def main():
    """主函数：演示报告生成流程"""
    print("=" * 60)
    print("报告生成器使用示例")
    print("=" * 60)
    
    # 初始化系统
    print("\n正在初始化系统...")
    system = UnifiedPRSystem()
    
    # 1. 准备需求
    requirements = {
        "goal": "新品发布认知",
        "audience": "一线城市年轻消费者",
        "tone": "专业且友好",
        "length": "1200字左右",
        "format": "Markdown",
        "timeframe": "近3个月案例与渠道",
        "citation_pref": "需要标注来源",
        "channels": ["微博", "小红书", "短视频"],
        "industry": "大消费",
        "brand": "示例品牌X",
    }
    
    print("\n📋 准备的需求：")
    for key, value in requirements.items():
        print(f"  {key}: {value}")
    
    # 2. 确认需求（可选，但推荐）
    print("\n" + "=" * 60)
    print("步骤 1: 确认需求")
    print("=" * 60)
    confirm_result = system.confirm_report_requirements(requirements)
    print("需求确认：")
    print(confirm_result.get("summary"))
    
    # 询问用户是否继续
    user_input = input("\n是否继续生成报告？(y/N): ").strip().lower()
    if user_input != 'y':
        print("已取消生成报告")
        return
    
    # 3. 生成报告（confirm=True 表示已确认需求）
    print("\n" + "=" * 60)
    print("步骤 2: 生成报告")
    print("=" * 60)
    print("正在生成报告，请稍候...")
    
    report = system.generate_report(
        requirements, 
        confirm=True,  # 必须为 True 才会生成
        dry_run=False  # False 表示使用 RAG 检索
    )
    
    # 查看报告
    print("\n" + "=" * 60)
    print("生成的报告：")
    print("=" * 60)
    print(report.get("report", "未生成"))
    
    # 保存报告到文件（可选）
    save_input = input("\n是否保存报告到文件？(y/N): ").strip().lower()
    if save_input == 'y':
        output_file = "outputs/generated_report.md"
        Path("outputs").mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report.get("report", ""))
        print(f"✅ 报告已保存到: {output_file}")
    
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

