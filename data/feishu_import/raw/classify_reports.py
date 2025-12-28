#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公关报告合集文件分类工具
根据文件类型自动分类到不同文件夹
"""

import os
import sys
import shutil
from pathlib import Path
from collections import defaultdict

# 设置Windows控制台编码为UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 定义分类规则（按优先级排序，越靠前优先级越高）
CLASSIFICATION_RULES = {
    # 传播全流程案例 - 包含完整传播流程的案例（优先级最高）
    '传播全流程案例': [
        '传播全流程',
        '全流程案例',
        '完整传播',
        '传播闭环',
        '从洞察到执行',
        '从策略到效果'
    ],
    # 媒介资料 - 媒介相关的所有资料
    '媒介资料': [
        '媒介资料',
        '媒介地图',
        '媒介投放',
        '媒介策略',
        '媒介规划',
        '媒介环境',
        '媒介资源',
        '媒介评估',
        '竞品报告',
        '竞品投放',
        '竞品分析',
        '社媒讨论',
        '社交舆论',
        '社交声量',
        '收视率',
        '用户画像',
        '媒介传播',
        '媒介工作',
        '媒介分享',
        '媒介案例',
        '投放数据',
        '投放分析',
        '投放研究',
        '投放监测',
        '投放总结',
        '投放回顾',
        '媒介组合',
        '媒介投资',
        '硬广投放',
        '软性合作',
        '剧集植入',
        '综艺合作',
        'KOL汇总',
        '音频案例',
        '媒介简报',
        '媒介月报',
        '媒介总结',
        '媒介回顾'
    ],
    '品牌案例': [
        'case_',
        '品牌案例',
        '案例解析',
        '品牌升级',
        '品牌校准',
        '品牌打造'
    ],
    '行业研究': [
        'research_',
        'industry_',
        '麦肯锡',
        '奥美',
        '巨量',
        '白皮书',
        '洞察报告',
        '消费者',
        '市场'
    ],
    '工具包': [
        'toolkits_',
        '知识地图',
        '思维导图',
        '话术',
        '直播大纲',
        '小程序'
    ],
    '方法论': [
        '华与华',
        '广告修辞学',
        '方法论'
    ],
    '招商方案': [
        '招商方案',
        '招商手册',
        '招商规划',
        '合作方案',
        '通案',
        '推介方案',
        'IP合作',
        '双11',
        '营销通案'
    ],
    '活动策划': [
        '活动策划',
        '活动方案',
        '主题活动',
        '执行方案',
        '双节',
        '中秋',
        '国庆',
        '春节',
        '音乐节',
        '露营',
        '团建',
        '体育赛事',
        '篮球',
        '文化节',
        '订货会'
    ],
    '品牌手册': [
        '品牌手册',
        '品牌资料',
        '品牌书',
        '品牌宣传册',
        '品牌故事'
    ],
    '整合营销': [
        '整合营销',
        '营销传播',
        '营销方案',
        '运营方案',
        '新媒体运营',
        '抖音运营',
        '小红书',
        '账号矩阵'
    ],
    '设计规划': [
        '设计方案',
        '设计规划',
        '景观设计',
        '规划方案',
        '改造提升',
        '规划设计',
        '产品户型'
    ]
}

def classify_file(filename):
    """根据文件名分类文件"""
    filename_lower = filename.lower()
    
    # 按优先级检查分类规则
    for category, keywords in CLASSIFICATION_RULES.items():
        for keyword in keywords:
            if keyword.lower() in filename_lower:
                return category
    
    # 如果无法匹配，返回"其他"
    return "其他"

def create_category_directories(base_path, categories):
    """创建分类目录"""
    for category in categories:
        category_path = base_path / category
        category_path.mkdir(parents=True, exist_ok=True)
        print(f"[OK] 创建分类目录: {category}")

def move_file_to_category(source_path, target_dir, filename):
    """移动文件到分类目录"""
    target_path = target_dir / filename
    
    # 如果目标文件已存在，添加序号
    if target_path.exists():
        base_name = Path(filename).stem
        extension = Path(filename).suffix
        counter = 1
        while target_path.exists():
            new_filename = f"{base_name}_{counter}{extension}"
            target_path = target_dir / new_filename
            counter += 1
    
    try:
        shutil.move(str(source_path), str(target_path))
        return True, target_path.name
    except Exception as e:
        print(f"[ERROR] 移动文件失败 {filename}: {e}")
        return False, filename

def main():
    """主函数"""
    # 设置路径 - 从脚本所在目录找到公关报告合集
    script_dir = Path(__file__).parent.absolute()
    base_dir = script_dir / "公关报告合集"
    
    if not base_dir.exists():
        print(f"[ERROR] 目录不存在: {base_dir}")
        return
    
    print("公关报告合集文件分类工具")
    print("=" * 60)
    print(f"源目录: {base_dir}")
    print()
    
    # 收集所有文件并分类
    file_categories = defaultdict(list)
    
    for file_path in base_dir.iterdir():
        if file_path.is_file() and not file_path.name.startswith('.'):
            category = classify_file(file_path.name)
            file_categories[category].append(file_path)
    
    # 显示分类统计
    print("文件分类统计:")
    for category, files in sorted(file_categories.items()):
        print(f"  {category}: {len(files)} 个文件")
    print()
    
    # 显示分类预览
    print("分类预览:")
    for category, files in sorted(file_categories.items()):
        if category != "其他":
            print(f"\n【{category}】")
            for file_path in sorted(files)[:5]:  # 只显示前5个
                print(f"  - {file_path.name}")
            if len(files) > 5:
                print(f"  ... 还有 {len(files) - 5} 个文件")
    
    if file_categories.get("其他"):
        print(f"\n【其他】({len(file_categories['其他'])} 个文件)")
        for file_path in sorted(file_categories["其他"])[:10]:
            print(f"  - {file_path.name}")
    
    print("\n" + "=" * 60)
    print("开始自动分类文件...")
    
    # 创建分类目录
    categories = list(file_categories.keys())
    create_category_directories(base_dir, categories)
    print()
    
    # 移动文件
    moved_count = 0
    failed_count = 0
    
    print("开始移动文件...")
    for category, files in sorted(file_categories.items()):
        category_dir = base_dir / category
        print(f"\n处理分类: {category}")
        
        for file_path in files:
            success, new_filename = move_file_to_category(
                file_path, category_dir, file_path.name
            )
            if success:
                moved_count += 1
                if moved_count <= 10 or file_path.name != new_filename:
                    print(f"  [OK] {file_path.name} -> {category}/{new_filename}")
            else:
                failed_count += 1
    
    print("\n" + "=" * 60)
    print("分类完成统计:")
    print(f"  成功移动: {moved_count} 个文件")
    if failed_count > 0:
        print(f"  移动失败: {failed_count} 个文件")
    
    # 显示最终目录结构
    print("\n最终目录结构:")
    for category_dir in sorted(base_dir.iterdir()):
        if category_dir.is_dir() and not category_dir.name.startswith('.'):
            file_count = len([f for f in category_dir.iterdir() if f.is_file()])
            print(f"  {category_dir.name}/ ({file_count} 个文件)")

if __name__ == "__main__":
    main()

