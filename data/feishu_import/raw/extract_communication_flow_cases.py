#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
传播全流程案例提取工具
从媒介资料中识别并提取包含完整传播流程的案例
传播流程：环境洞察 → 策略制定 → 资源评估 → 执行投放 → 效果监测 → 经验沉淀
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# 设置Windows控制台编码为UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 传播流程阶段关键词
COMMUNICATION_FLOW_STAGES = {
    '环境洞察': [
        '环境分析', '环境洞察', '媒介环境', '市场环境', '行业环境',
        '社交舆论', '社媒讨论', '趋势洞察', '热点观察', '内容趋势',
        '用户画像', '受众分析', '人群分析', '消费者洞察'
    ],
    '策略制定': [
        '策略', '规划', '方案', '计划', '传播规划', '媒介规划',
        '投放策略', '传播策略', '媒介策略', '年度规划', '季度规划',
        '月度规划', '战术说明', '策略流程'
    ],
    '资源评估': [
        '资源评估', '媒介资源', '资源盘点', '资源分析', '评估',
        '植入评估', '合作评估', 'IP评估', '资源价值', '媒介地图'
    ],
    '执行投放': [
        '执行', '投放', '排期', '合作', '植入', 'KOL', '达人',
        '硬广', '软性', '剧集', '综艺', '音频', '户外', '电视',
        '社媒', '新媒体', '传播执行', '投放执行'
    ],
    '效果监测': [
        '效果', '监测', '数据', '收视', '收视率', '声量', '讨论',
        '投放总结', '投放回顾', '效果分析', '数据报告', '监测报告',
        '效果评估', 'ROI', '转化', '曝光', '触达'
    ],
    '经验沉淀': [
        '案例', '分享', '结案', '复盘', '总结', '回顾', '经验',
        '案例分享', '项目结案', '工作简报', '分享会', '案例整理'
    ]
}

# 竞品分析相关（作为环境洞察的一部分）
COMPETITOR_KEYWORDS = [
    '竞品', '竞对', '竞争对手', '对标', '竞品分析', '竞品报告',
    '竞品投放', '竞品研究', '竞品监测'
]

def extract_stage_from_filename(filename):
    """从文件名提取传播流程阶段"""
    filename_lower = filename.lower()
    stages_found = []
    
    for stage, keywords in COMMUNICATION_FLOW_STAGES.items():
        for keyword in keywords:
            if keyword in filename_lower:
                stages_found.append(stage)
                break
    
    # 检查竞品相关
    if any(kw in filename_lower for kw in COMPETITOR_KEYWORDS):
        if '环境洞察' not in stages_found:
            stages_found.append('环境洞察')
    
    return list(set(stages_found))

def analyze_communication_flow(base_dir):
    """分析传播流程案例"""
    media_dir = base_dir / "媒介资料" / "媒介资料"
    
    if not media_dir.exists():
        print(f"[WARNING] 媒介资料目录不存在: {media_dir}")
        return None
    
    # 按品牌/项目组织文件
    brand_projects = defaultdict(lambda: {
        'files': [],
        'stages': set(),
        'categories': set()
    })
    
    # 遍历所有文件
    for root, dirs, files in os.walk(media_dir):
        root_path = Path(root)
        relative_path = root_path.relative_to(media_dir)
        
        for file in files:
            if file.startswith('.') or file.endswith('.db'):
                continue
            
            file_path = root_path / file
            
            # 提取品牌/项目名称（从文件名或路径）
            brand_name = extract_brand_name(file, str(relative_path))
            
            # 提取传播阶段
            stages = extract_stage_from_filename(file)
            
            # 提取分类（从路径）
            category = extract_category_from_path(relative_path)
            
            brand_projects[brand_name]['files'].append({
                'name': file,
                'path': str(relative_path),
                'full_path': str(file_path),
                'stages': stages,
                'category': category
            })
            brand_projects[brand_name]['stages'].update(stages)
            brand_projects[brand_name]['categories'].add(category)
    
    return brand_projects

def extract_brand_name(filename, path_str):
    """从文件名或路径提取品牌名称"""
    # 常见品牌名称
    known_brands = [
        '东阿阿胶', '健力宝', '小皮', '999', '凌派', '复方阿胶浆',
        '澳诺', '三九', 'swisse', '东鹏', '江中', '汤臣倍健',
        '哈药', '太极', '葵花', '补肺丸', '康王', '养元青'
    ]
    
    filename_lower = filename.lower()
    path_lower = path_str.lower()
    
    # 优先从文件名提取
    for brand in known_brands:
        if brand in filename:
            return brand
    
    # 从路径提取
    for brand in known_brands:
        if brand in path_str:
            return brand
    
    # 如果找不到，尝试从文件名提取（取前几个字符）
    # 或者使用路径的第一级目录名
    if path_str and path_str != '.':
        parts = path_str.split(os.sep)
        if parts and parts[0]:
            return parts[0]
    
    # 最后使用文件名（去掉扩展名）
    return Path(filename).stem[:20]

def extract_category_from_path(relative_path):
    """从路径提取分类"""
    path_str = str(relative_path)
    
    categories = {
        '媒介地图': '媒介地图' in path_str,
        '媒介投放策略': '媒介投放策略' in path_str or '媒介策略' in path_str,
        '媒介环境分析': '媒介环境分析' in path_str or '环境分析' in path_str,
        '媒介资源评估': '媒介资源评估' in path_str or '资源评估' in path_str,
        '社交舆论风向': '社交舆论风向' in path_str or '社交舆论' in path_str,
        '社媒用户画像': '社媒用户画像' in path_str or '用户画像' in path_str or '收视率' in path_str,
        '竞品报告': '竞品报告' in path_str or '竞品' in path_str,
        '行业案例分享': '行业案例分享' in path_str or '案例分享' in path_str
    }
    
    for category, match in categories.items():
        if match:
            return category
    
    return '其他'

def identify_full_flow_cases(brand_projects):
    """识别包含完整传播流程的案例"""
    full_flow_cases = []
    
    # 定义完整流程所需的最少阶段数（至少包含4个阶段）
    min_stages = 4
    
    for brand, data in brand_projects.items():
        stages = list(data['stages'])
        
        # 检查是否包含完整流程
        if len(stages) >= min_stages:
            # 计算流程完整度
            completeness = calculate_completeness(stages)
            
            full_flow_cases.append({
                'brand': brand,
                'stages': stages,
                'stage_count': len(stages),
                'completeness': completeness,
                'categories': list(data['categories']),
                'file_count': len(data['files']),
                'files': data['files']
            })
    
    # 按完整度排序
    full_flow_cases.sort(key=lambda x: (x['completeness'], x['stage_count']), reverse=True)
    
    return full_flow_cases

def calculate_completeness(stages):
    """计算流程完整度"""
    all_stages = set(COMMUNICATION_FLOW_STAGES.keys())
    found_stages = set(stages)
    
    # 基础完整度（找到的阶段数 / 总阶段数）
    base_completeness = len(found_stages) / len(all_stages)
    
    # 流程连续性加分
    continuity_bonus = 0
    stage_order = ['环境洞察', '策略制定', '资源评估', '执行投放', '效果监测', '经验沉淀']
    
    consecutive_count = 0
    for stage in stage_order:
        if stage in found_stages:
            consecutive_count += 1
        else:
            if consecutive_count > 0:
                break
    
    if consecutive_count >= 3:
        continuity_bonus = 0.1
    
    return base_completeness + continuity_bonus

def generate_flow_case_report(full_flow_cases, output_file):
    """生成传播流程案例报告"""
    report = {
        'generated_at': datetime.now().isoformat(),
        'total_cases': len(full_flow_cases),
        'cases': []
    }
    
    for case in full_flow_cases:
        case_info = {
            'brand': case['brand'],
            'completeness': round(case['completeness'], 2),
            'stage_count': case['stage_count'],
            'stages': case['stages'],
            'categories': case['categories'],
            'file_count': case['file_count'],
            'files_by_stage': {}
        }
        
        # 按阶段组织文件
        for stage in case['stages']:
            case_info['files_by_stage'][stage] = [
                f['name'] for f in case['files'] 
                if stage in f['stages']
            ]
        
        report['cases'].append(case_info)
    
    # 保存报告
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return report

def main():
    """主函数"""
    script_dir = Path(__file__).parent.absolute()
    base_dir = script_dir / "公关报告合集"
    
    if not base_dir.exists():
        print(f"[ERROR] 目录不存在: {base_dir}")
        return
    
    print("传播全流程案例提取工具")
    print("=" * 60)
    print(f"分析目录: {base_dir}")
    print()
    
    # 分析传播流程
    print("正在分析传播流程...")
    brand_projects = analyze_communication_flow(base_dir)
    
    if not brand_projects:
        print("[ERROR] 未找到媒介资料")
        return
    
    print(f"发现 {len(brand_projects)} 个品牌/项目")
    print()
    
    # 识别完整流程案例
    print("正在识别完整流程案例...")
    full_flow_cases = identify_full_flow_cases(brand_projects)
    
    print(f"发现 {len(full_flow_cases)} 个完整流程案例")
    print()
    
    # 显示案例列表
    print("=" * 60)
    print("完整传播流程案例列表:")
    print()
    
    for i, case in enumerate(full_flow_cases[:20], 1):  # 只显示前20个
        print(f"{i}. {case['brand']}")
        print(f"   完整度: {case['completeness']:.2%}")
        print(f"   阶段数: {case['stage_count']}/6")
        print(f"   包含阶段: {', '.join(case['stages'])}")
        print(f"   文件数: {case['file_count']}")
        print(f"   分类: {', '.join(case['categories'])}")
        print()
    
    if len(full_flow_cases) > 20:
        print(f"... 还有 {len(full_flow_cases) - 20} 个案例")
    
    # 生成报告
    output_file = base_dir / "传播全流程案例报告.json"
    print("=" * 60)
    print(f"正在生成报告: {output_file}")
    
    report = generate_flow_case_report(full_flow_cases, output_file)
    
    print()
    print("=" * 60)
    print("报告生成完成！")
    print(f"  总案例数: {report['total_cases']}")
    print(f"  报告文件: {output_file}")
    print()
    print("提示：")
    print("  1. 完整度 >= 60% 的案例建议重点关注")
    print("  2. 包含4个以上阶段的案例可作为学习参考")
    print("  3. 报告文件包含详细的文件列表和阶段分布")

if __name__ == "__main__":
    main()

