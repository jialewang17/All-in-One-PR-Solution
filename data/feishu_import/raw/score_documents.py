#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公关文档自动评分工具
根据完善的分类标准和评分系统，对每个文档进行评分
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

# 媒介传播相关关键词
MEDIA_KEYWORDS = {
    '环境洞察': [
        '媒介环境', '环境分析', '社交舆论', '舆论风向', '用户画像', 
        '竞品分析', '竞品报告', '市场分析', '媒介分析'
    ],
    '策略制定': [
        '媒介策略', '媒介规划', '媒介投放', '传播策略', '传播规划',
        '媒介创意', '媒介组合', '投放策略'
    ],
    '资源评估': [
        '资源评估', '媒介资源', '资源盘点', '媒介地图', '植入评估',
        'IP合作', '资源包', '媒介选择'
    ],
    '执行投放': [
        '执行计划', '投放执行', '投放排期', '排期说明', 'KOL',
        '剧集植入', '综艺合作', '媒介执行'
    ],
    '效果监测': [
        '效果监测', '效果分析', '数据报告', '收视率', '声量',
        '投放总结', '投放回顾', '效果评估'
    ],
    '经验沉淀': [
        '案例分享', '项目结案', '复盘总结', '分享会', '经验总结',
        '工作简报', '月度简报'
    ]
}

def check_media_stages(filename, path_str):
    """检查文档包含哪些媒介传播阶段"""
    filename_lower = filename.lower()
    path_lower = path_str.lower()
    text = filename_lower + ' ' + path_lower
    
    stages_found = []
    for stage, keywords in MEDIA_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                stages_found.append(stage)
                break
    
    return list(set(stages_found))

def score_completeness(category, filename, path_str):
    """评分：完整性"""
    score = 0
    max_score = 100
    
    # 根据文档类型判断完整性
    if category == '活动策划':
        required_elements = [
            '活动背景', '活动目标', '活动策略', '创意内容',
            '活动流程', '执行计划', '预算方案'
        ]
        # 简化评分：根据文件名和路径判断
        if '背景' in filename or '环境' in filename:
            score += 15
        if '目标' in filename or 'KPI' in filename:
            score += 15
        if '策略' in filename or '规划' in filename:
            score += 15
        if '创意' in filename or '设计' in filename:
            score += 15
        if '流程' in filename or '执行' in filename:
            score += 15
        if '执行' in filename or '计划' in filename:
            score += 15
        if '预算' in filename or '成本' in filename:
            score += 10
    
    elif category == '招商方案':
        if '介绍' in filename or 'IP' in filename or '平台' in filename:
            score += 15
        if '洞察' in filename or '分析' in filename:
            score += 15
        if '价值' in filename or '权益' in filename:
            score += 15
        if '资源' in filename or '资源包' in filename:
            score += 20
        if '案例' in filename:
            score += 15
        if '方案' in filename or '合作' in filename:
            score += 10
        if '报价' in filename or '价格' in filename:
            score += 10
    
    elif category == '整合营销':
        if '背景' in filename or '环境' in filename:
            score += 10
        if '目标' in filename:
            score += 15
        if '人群' in filename or '用户' in filename:
            score += 15
        if '策略' in filename:
            score += 15
        if '渠道' in filename:
            score += 20
        if '内容' in filename:
            score += 15
        if '执行' in filename or '计划' in filename:
            score += 10
    
    elif category == '品牌案例':
        if '背景' in filename:
            score += 15
        if '策略' in filename:
            score += 15
        if '执行' in filename:
            score += 20
        if '创意' in filename or '内容' in filename:
            score += 15
        if '传播' in filename:
            score += 15
        if '效果' in filename or '数据' in filename:
            score += 15
        if '总结' in filename or '经验' in filename:
            score += 5
    
    elif category == '行业研究':
        if '研究' in filename or '分析' in filename:
            score += 10
        if '环境' in filename or '市场' in filename:
            score += 15
        if '洞察' in filename:
            score += 20
        if '数据' in filename:
            score += 25
        if '案例' in filename:
            score += 15
        if '趋势' in filename or '预测' in filename:
            score += 10
        if '结论' in filename or '建议' in filename:
            score += 5
    
    else:
        # 其他类型，基础评分
        score = 60
    
    return min(score, max_score)

def score_professionalism(category, filename, path_str):
    """评分：专业性"""
    score = 60  # 基础分
    
    # 根据关键词判断专业性
    professional_keywords = [
        '策略', '规划', '分析', '洞察', '研究', '评估',
        '方法论', '框架', '体系', '模型'
    ]
    
    for keyword in professional_keywords:
        if keyword in filename:
            score += 5
    
    return min(score, 100)

def score_practicality(category, filename, path_str):
    """评分：实用性"""
    score = 60  # 基础分
    
    # 根据关键词判断实用性
    practical_keywords = [
        '方案', '计划', '执行', '流程', '清单', '模板',
        '工具', '指南', '手册', '操作'
    ]
    
    for keyword in practical_keywords:
        if keyword in filename:
            score += 5
    
    return min(score, 100)

def score_data_support(category, filename, path_str):
    """评分：数据支撑"""
    score = 40  # 基础分
    
    # 根据关键词判断数据支撑
    data_keywords = [
        '数据', '报告', '分析', '统计', '监测', '评估',
        '效果', 'ROI', 'KPI', '指标', '收视率', '声量'
    ]
    
    for keyword in data_keywords:
        if keyword in filename:
            score += 8
    
    return min(score, 100)

def score_media_relevance(category, filename, path_str):
    """评分：媒介传播相关度"""
    score = 0
    
    # 检查媒介传播阶段
    stages = check_media_stages(filename, path_str)
    stage_count = len(stages)
    
    # 基础分：每个阶段15分
    score = stage_count * 15
    
    # 如果包含"媒介"相关关键词，额外加分
    media_keywords = ['媒介', '媒体', '传播', '投放', '社媒', '社交']
    for keyword in media_keywords:
        if keyword in filename.lower() or keyword in path_str.lower():
            score += 10
            break
    
    return min(score, 100)

def calculate_media_completeness(stages):
    """计算媒介传播完整度"""
    total_stages = 6
    found_stages = len(stages)
    completeness = (found_stages / total_stages) * 100
    return completeness

def get_rating_level(total_score):
    """获取评分等级"""
    if total_score >= 450:
        return "⭐⭐⭐⭐⭐ 优秀"
    elif total_score >= 400:
        return "⭐⭐⭐⭐ 良好"
    elif total_score >= 350:
        return "⭐⭐⭐ 中等"
    elif total_score >= 300:
        return "⭐⭐ 一般"
    else:
        return "⭐ 较差"

def score_document(file_path, base_dir):
    """对单个文档进行评分"""
    relative_path = file_path.relative_to(base_dir)
    path_str = str(relative_path)
    filename = file_path.name
    
    # 判断文档类型（简化版，实际应该更准确）
    category = "其他"
    if '活动' in filename or '活动策划' in path_str:
        category = "活动策划"
    elif '招商' in filename or '招商方案' in path_str:
        category = "招商方案"
    elif '营销' in filename or '整合营销' in path_str:
        category = "整合营销"
    elif '案例' in filename or '品牌案例' in path_str:
        category = "品牌案例"
    elif '研究' in filename or '行业研究' in path_str:
        category = "行业研究"
    elif '手册' in filename or '品牌手册' in path_str:
        category = "品牌手册"
    elif '设计' in filename or '设计规划' in path_str:
        category = "设计规划"
    elif '工具' in filename or '工具包' in path_str:
        category = "工具包"
    elif '方法' in filename or '方法论' in path_str:
        category = "方法论"
    
    # 各维度评分
    completeness = score_completeness(category, filename, path_str)
    professionalism = score_professionalism(category, filename, path_str)
    practicality = score_practicality(category, filename, path_str)
    data_support = score_data_support(category, filename, path_str)
    media_relevance = score_media_relevance(category, filename, path_str)
    
    # 总分
    total_score = completeness + professionalism + practicality + data_support + media_relevance
    
    # 媒介传播完整度
    stages = check_media_stages(filename, path_str)
    media_completeness = calculate_media_completeness(stages)
    
    # 评分等级
    rating = get_rating_level(total_score)
    
    return {
        'filename': filename,
        'path': path_str,
        'category': category,
        'scores': {
            'completeness': completeness,
            'professionalism': professionalism,
            'practicality': practicality,
            'data_support': data_support,
            'media_relevance': media_relevance
        },
        'total_score': total_score,
        'rating': rating,
        'media_stages': stages,
        'media_completeness': media_completeness
    }

def main():
    """主函数"""
    script_dir = Path(__file__).parent.absolute()
    base_dir = script_dir / "公关报告合集"
    
    if not base_dir.exists():
        print(f"[ERROR] 目录不存在: {base_dir}")
        return
    
    print("公关文档自动评分工具")
    print("=" * 60)
    print(f"扫描目录: {base_dir}")
    print()
    
    # 需要评分的分类文件夹
    categories_to_score = [
        '活动策划', '招商方案', '整合营销', '品牌案例', 
        '行业研究', '品牌手册', '设计规划', '工具包', '方法论'
    ]
    
    all_scores = []
    
    print("正在扫描和评分文档...")
    print()
    
    for category_name in categories_to_score:
        category_dir = base_dir / category_name
        if not category_dir.exists():
            continue
        
        print(f"处理分类: {category_name}")
        
        # 查找所有文件
        files = []
        for file_path in category_dir.rglob('*'):
            if file_path.is_file() and not file_path.name.startswith('.'):
                # 跳过系统文件和图片
                if file_path.suffix.lower() in ['.db', '.jpg', '.png', '.mp4']:
                    continue
                files.append(file_path)
        
        for file_path in files:
            try:
                score_result = score_document(file_path, base_dir)
                all_scores.append(score_result)
            except Exception as e:
                print(f"  [ERROR] 评分失败 {file_path.name}: {e}")
        
        print(f"  已评分 {len(files)} 个文件")
        print()
    
    # 统计
    print("=" * 60)
    print("评分统计:")
    print(f"  总文档数: {len(all_scores)} 个")
    
    # 按分类统计
    by_category = defaultdict(list)
    for score in all_scores:
        by_category[score['category']].append(score)
    
    print("\n各分类平均分:")
    for category, scores in sorted(by_category.items()):
        avg_score = sum(s['total_score'] for s in scores) / len(scores)
        print(f"  {category}: {avg_score:.1f}分 ({len(scores)} 个文档)")
    
    # 按评分等级统计
    by_rating = defaultdict(int)
    for score in all_scores:
        rating_level = score['rating'].split()[0]  # 提取星星数
        by_rating[rating_level] += 1
    
    print("\n评分等级分布:")
    for rating, count in sorted(by_rating.items(), reverse=True):
        print(f"  {rating}: {count} 个文档")
    
    # 保存评分报告
    output_file = base_dir / '文档评分报告.json'
    report_data = {
        'generated_at': datetime.now().isoformat(),
        'total_documents': len(all_scores),
        'scores': all_scores,
        'statistics': {
            'by_category': {
                cat: {
                    'count': len(scores),
                    'avg_score': sum(s['total_score'] for s in scores) / len(scores),
                    'avg_media_completeness': sum(s['media_completeness'] for s in scores) / len(scores)
                }
                for cat, scores in by_category.items()
            },
            'by_rating': dict(by_rating)
        }
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        print(f"\n评分报告已保存: {output_file}")
    except Exception as e:
        print(f"[ERROR] 保存评分报告失败: {e}")
    
    # 生成Markdown报告
    generate_markdown_report(base_dir, report_data)
    
    print("\n评分完成！")

def generate_markdown_report(base_dir, report_data):
    """生成Markdown格式的评分报告"""
    output_file = base_dir / '文档评分报告.md'
    
    lines = []
    lines.append("# 📊 公关文档评分报告")
    lines.append("")
    lines.append(f"**生成时间**: {report_data['generated_at']}")
    lines.append(f"**总文档数**: {report_data['total_documents']} 个")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 统计概览
    lines.append("## 📈 评分概览")
    lines.append("")
    lines.append("### 各分类平均分")
    lines.append("")
    lines.append("| 分类 | 文档数 | 平均总分 | 平均媒介完整度 |")
    lines.append("|------|--------|---------|---------------|")
    
    stats = report_data['statistics']['by_category']
    for category, data in sorted(stats.items(), key=lambda x: x[1]['avg_score'], reverse=True):
        lines.append(f"| {category} | {data['count']} | {data['avg_score']:.1f}分 | {data['avg_media_completeness']:.1f}% |")
    
    lines.append("")
    lines.append("### 评分等级分布")
    lines.append("")
    lines.append("| 等级 | 文档数 |")
    lines.append("|------|--------|")
    
    for rating, count in sorted(report_data['statistics']['by_rating'].items(), reverse=True):
        lines.append(f"| {rating} | {count} |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 详细评分（按分类分组）
    lines.append("## 📋 详细评分")
    lines.append("")
    
    by_category = defaultdict(list)
    for score in report_data['scores']:
        by_category[score['category']].append(score)
    
    for category in sorted(by_category.keys()):
        scores = sorted(by_category[category], key=lambda x: x['total_score'], reverse=True)
        lines.append(f"### {category}")
        lines.append("")
        lines.append("| 文件名 | 总分 | 完整性 | 专业性 | 实用性 | 数据支撑 | 媒介相关度 | 媒介完整度 | 等级 |")
        lines.append("|--------|------|--------|--------|--------|----------|------------|------------|------|")
        
        for score in scores[:20]:  # 只显示前20个
            filename = score['filename'][:30] + '...' if len(score['filename']) > 30 else score['filename']
            s = score['scores']
            lines.append(f"| {filename} | {score['total_score']} | {s['completeness']} | {s['professionalism']} | {s['practicality']} | {s['data_support']} | {s['media_relevance']} | {score['media_completeness']:.1f}% | {score['rating']} |")
        
        if len(scores) > 20:
            lines.append(f"| ... 还有 {len(scores) - 20} 个文档 | | | | | | | | |")
        
        lines.append("")
        lines.append("---")
        lines.append("")
    
    lines.append("*评分报告版本* | *生成时间: 2025年1月*")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"Markdown报告已生成: {output_file}")
    except Exception as e:
        print(f"[ERROR] 生成Markdown报告失败: {e}")

if __name__ == "__main__":
    main()

