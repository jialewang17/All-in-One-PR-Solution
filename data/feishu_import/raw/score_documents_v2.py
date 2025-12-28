#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公关文档分类专属评分工具 v2.0
为每个分类设计专属评价维度，确保权威文档合理高分，有效区分质量层次
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

def score_activity_planning(filename, path_str):
    """活动策划类文档评分"""
    score = 60  # 基础分：活动策划文档通常都有基本结构
    text = (filename + ' ' + path_str).lower()
    
    # 执行可行性 (40分)
    if any(kw in text for kw in ['时间', '节点', '排期', '日程', '安排']):
        score += 10
    if any(kw in text for kw in ['人员', '分工', '团队', '配置']):
        score += 10
    if any(kw in text for kw in ['物料', '清单', '设备']):
        score += 10
    if any(kw in text for kw in ['场地', '设备', '需求', '配置']):
        score += 10
    
    # 创意质量 (30分)
    if any(kw in text for kw in ['主题', '主张', '概念', '创意']):
        score += 15
    if any(kw in text for kw in ['创意', '设计', '视觉', '文案', '内容']):
        score += 15
    
    # 流程完整性 (20分)
    if any(kw in text for kw in ['时间轴', '时间', '流程', '环节', '执行']):
        score += 8
    if any(kw in text for kw in ['环节', '流程', '动线', '步骤']):
        score += 7
    if '流程' in text or '动线' in text or '执行' in text:
        score += 5
    
    # 风险控制 (10分)
    if any(kw in text for kw in ['应急', '预案', '风险', '控制']):
        score += 10
    
    return min(score, 100)

def score_investment_proposal(filename, path_str):
    """招商方案类文档评分"""
    score = 50  # 基础分：招商方案通常都有基本结构
    text = (filename + ' ' + path_str).lower()
    
    # IP价值展示 (35分)
    if any(kw in text for kw in ['ip', '平台', '定位', '价值', '介绍']):
        score += 10
    if any(kw in text for kw in ['价值', '优势', '核心', '影响力']):
        score += 10
    if any(kw in text for kw in ['数据', '影响力', '品牌', '效果']):
        score += 10
    if '差异化' in text or '优势' in text or '核心' in text:
        score += 5
    
    # 资源吸引力 (30分)
    if any(kw in text for kw in ['资源', '资源包', '清单', '权益']):
        score += 15
    if any(kw in text for kw in ['规格', '组合', '方案', '套餐']):
        score += 10
    if '组合' in text or '套餐' in text or '方案' in text:
        score += 5
    
    # 案例说服力 (25分)
    if any(kw in text for kw in ['案例', '合作案例', '成功', '合作']):
        score += 10
    if any(kw in text for kw in ['效果', '数据', 'roi', '效果']):
        score += 10
    if any(kw in text for kw in ['评价', '客户', '反馈']):
        score += 5
    
    # 合作便利性 (10分)
    if any(kw in text for kw in ['流程', '步骤', '合作', '方案']):
        score += 10
    
    return min(score, 100)

def score_integrated_marketing(filename, path_str):
    """整合营销类文档评分"""
    score = 50  # 基础分：整合营销文档通常都有基本结构
    text = (filename + ' ' + path_str).lower()
    
    # 策略深度 (35分)
    if any(kw in text for kw in ['市场', '分析', '环境', '竞品', '背景']):
        score += 10
    if any(kw in text for kw in ['人群', '用户', '画像', '定位', '目标']):
        score += 10
    if any(kw in text for kw in ['策略', '思路', '规划', '方案']):
        score += 10
    if '差异化' in text or '定位' in text or '策略' in text:
        score += 5
    
    # 渠道专业性 (30分)
    if any(kw in text for kw in ['渠道', '平台', '组合', '传播', '媒介']):
        score += 15
    if any(kw in text for kw in ['定位', '协同', '矩阵', '运营']):
        score += 10
    if '协同' in text or '矩阵' in text or '运营' in text:
        score += 5
    
    # 可执行性 (25分)
    if any(kw in text for kw in ['执行', '计划', '方案', '运营']):
        score += 15
    if any(kw in text for kw in ['运营', '方案', '规划', '执行']):
        score += 10
    
    # 监测机制 (10分)
    if any(kw in text for kw in ['监测', '评估', '指标', '数据', '效果']):
        score += 10
    
    return min(score, 100)

def score_brand_case(filename, path_str):
    """品牌案例类文档评分"""
    score = 50  # 基础分：品牌案例文档通常都有基本结构
    text = (filename + ' ' + path_str).lower()
    
    # 案例完整性 (35分)
    if any(kw in text for kw in ['背景', '项目', '品牌', '案例']):
        score += 8
    if any(kw in text for kw in ['策略', '思考', '思路', '方案']):
        score += 8
    if any(kw in text for kw in ['执行', '过程', '时间轴', '实施']):
        score += 10
    if any(kw in text for kw in ['效果', '数据', 'roi', '结果']):
        score += 9
    
    # 数据真实性 (30分)
    if any(kw in text for kw in ['传播', '曝光', '互动', '声量', '数据']):
        score += 10
    if any(kw in text for kw in ['转化', '销售', '增长', '业务', '效果']):
        score += 10
    if any(kw in text for kw in ['roi', '回报', '效果', '数据']):
        score += 10
    
    # 学习价值 (25分)
    if any(kw in text for kw in ['执行', '过程', '细节', '记录', '案例']):
        score += 15
    if any(kw in text for kw in ['经验', '总结', '教训', '分享', '结案']):
        score += 10
    
    # 方法论提炼 (10分)
    if any(kw in text for kw in ['方法论', '方法', '框架', '理论']):
        score += 10
    
    return min(score, 100)

def score_industry_research(filename, path_str):
    """行业研究类文档评分"""
    score = 50  # 基础分：行业研究文档通常都有基本结构
    text = (filename + ' ' + path_str).lower()
    
    # 数据权威性 (40分)
    # 检查是否来自权威机构
    authoritative_sources = ['麦肯锡', '奥美', '巨量', '凯度', '艾瑞', '易观', 'questmobile', '特赞', '微播易', '公关周刊']
    if any(source in text for source in authoritative_sources):
        score += 30  # 权威机构加分更多
    elif any(kw in text for kw in ['白皮书', '报告', '研究', '洞察']):
        score += 15
    
    if any(kw in text for kw in ['数据', '分析', '统计', '监测']):
        score += 10
    
    # 洞察深度 (35分)
    if any(kw in text for kw in ['消费者', '用户', '人群', '洞察']):
        score += 12
    if any(kw in text for kw in ['行业', '市场', '趋势', '洞察', '分析']):
        score += 12
    if any(kw in text for kw in ['机会', '挑战', '洞察', '研究']):
        score += 11
    
    # 方法论价值 (15分)
    if any(kw in text for kw in ['方法论', '方法', '框架', '模型']):
        score += 10
    if any(kw in text for kw in ['应用', '场景', '实践']):
        score += 5
    
    # 趋势预测 (10分)
    if any(kw in text for kw in ['趋势', '预测', '未来', '展望', '2025', '2024']):
        score += 10
    
    return min(score, 100)

def score_toolkit(filename, path_str):
    """工具包类文档评分"""
    score = 60  # 基础分：工具包通常实用性较高
    text = (filename + ' ' + path_str).lower()
    
    # 实用性 (40分)
    if any(kw in text for kw in ['工具', '模板', '指南', '手册', '地图', '话术', '大纲']):
        score += 20
    if any(kw in text for kw in ['操作', '使用', '应用', '指南', '知识']):
        score += 20
    
    # 完整性 (30分)
    if any(kw in text for kw in ['完整', '全面', '系统', '大全']):
        score += 15
    if any(kw in text for kw in ['示例', '案例', '说明', '思维导图']):
        score += 15
    
    # 易用性 (20分)
    if any(kw in text for kw in ['地图', '导图', '思维', '结构', '知识地图']):
        score += 10
    # 工具包通常易用性较高，给予基础分
    score += 10
    
    # 更新性 (10分)
    # 检查年份（2024或2025）
    if '2024' in filename or '2025' in filename:
        score += 10
    elif '2023' in filename:
        score += 5
    
    return min(score, 100)

def score_brand_manual(filename, path_str):
    """品牌手册类文档评分"""
    score = 70  # 基础分：品牌手册通常质量较高
    text = (filename + ' ' + path_str).lower()
    
    # 品牌规范完整性 (40分)
    if any(kw in text for kw in ['logo', '标识', '标志', '品牌']):
        score += 10
    if any(kw in text for kw in ['色彩', '颜色', '配色', '视觉']):
        score += 10
    if any(kw in text for kw in ['字体', '字型', 'typography', '规范']):
        score += 10
    if any(kw in text for kw in ['规范', '应用', '标准', '手册']):
        score += 10
    
    # 视觉质量 (30分)
    if any(kw in text for kw in ['设计', '视觉', '呈现', '手册']):
        score += 15
    # 品牌手册通常视觉质量都较高，给予基础分
    score += 15
    
    # 应用指导 (20分)
    if any(kw in text for kw in ['示例', '案例', '应用', '手册']):
        score += 10
    if any(kw in text for kw in ['正确', '错误', '指导', '应用']):
        score += 10
    
    # 品牌价值 (10分)
    if any(kw in text for kw in ['价值', '主张', '定位', '故事', '品牌']):
        score += 10
    
    return min(score, 100)

def score_design_planning(filename, path_str):
    """设计规划类文档评分"""
    score = 70  # 基础分：设计规划文档通常质量较高
    text = (filename + ' ' + path_str).lower()
    
    # 设计方案质量 (40分)
    if any(kw in text for kw in ['理念', '概念', '设计', '规划']):
        score += 10
    if any(kw in text for kw in ['功能', '分区', '布局', '设计']):
        score += 10
    if any(kw in text for kw in ['空间', '布局', '规划', '设计']):
        score += 10
    if any(kw in text for kw in ['详细', '设计', '方案', '规划']):
        score += 10
    
    # 技术可行性 (30分)
    if any(kw in text for kw in ['结构', '技术', '施工', '方案']):
        score += 15
    if any(kw in text for kw in ['材料', '设备', '配置', '技术']):
        score += 15
    
    # 视觉效果 (20分)
    if any(kw in text for kw in ['效果图', '3d', '模型', '视觉', '设计']):
        score += 10
    # 设计规划通常视觉效果较好，给予基础分
    score += 10
    
    # 实施指导 (10分)
    if any(kw in text for kw in ['实施', '施工', '计划', '时间表', '方案']):
        score += 10
    
    return min(score, 100)

def score_methodology(filename, path_str):
    """方法论类文档评分"""
    score = 60  # 基础分：方法论文档通常质量较高
    text = (filename + ' ' + path_str).lower()
    
    # 理论深度 (40分)
    if any(kw in text for kw in ['方法', '理论', '框架', '体系', '原理']):
        score += 20
    if any(kw in text for kw in ['分析', '深入', '系统', '理论']):
        score += 20
    
    # 实用性 (35分)
    if any(kw in text for kw in ['应用', '实践', '使用', '操作', '案例']):
        score += 20
    if any(kw in text for kw in ['场景', '案例', '示例', '实践']):
        score += 15
    
    # 案例支撑 (15分)
    if any(kw in text for kw in ['案例', '实例', '实践', '西贝']):
        score += 15
    
    # 权威性 (10分)
    authoritative = ['华与华', '奥美', '麦肯锡', '特劳特', '里斯']
    if any(auth in text for auth in authoritative):
        score += 10  # 权威机构直接满分
    elif any(kw in text for kw in ['权威', '专家', '大师']):
        score += 5
    
    return min(score, 100)

def get_rating_level(score):
    """获取评分等级"""
    if score >= 90:
        return "⭐⭐⭐⭐⭐ 优秀"
    elif score >= 80:
        return "⭐⭐⭐⭐ 良好"
    elif score >= 70:
        return "⭐⭐⭐ 中等"
    elif score >= 60:
        return "⭐⭐ 一般"
    else:
        return "⭐ 较差"

def score_document(file_path, base_dir):
    """对单个文档进行评分"""
    relative_path = file_path.relative_to(base_dir)
    path_str = str(relative_path)
    filename = file_path.name
    
    # 判断文档类型
    category = "其他"
    category_dir = file_path.parent.name
    
    if category_dir == '活动策划' or '活动' in filename.lower():
        category = "活动策划"
        score = score_activity_planning(filename, path_str)
    elif category_dir == '招商方案' or '招商' in filename.lower():
        category = "招商方案"
        score = score_investment_proposal(filename, path_str)
    elif category_dir == '整合营销' or ('营销' in filename.lower() and '整合' in filename.lower()):
        category = "整合营销"
        score = score_integrated_marketing(filename, path_str)
    elif category_dir == '品牌案例' or ('案例' in filename.lower() and '品牌' in filename.lower()):
        category = "品牌案例"
        score = score_brand_case(filename, path_str)
    elif category_dir == '行业研究' or '研究' in filename.lower():
        category = "行业研究"
        score = score_industry_research(filename, path_str)
    elif category_dir == '工具包' or '工具' in filename.lower():
        category = "工具包"
        score = score_toolkit(filename, path_str)
    elif category_dir == '品牌手册' or '手册' in filename.lower():
        category = "品牌手册"
        score = score_brand_manual(filename, path_str)
    elif category_dir == '设计规划' or '设计' in filename.lower():
        category = "设计规划"
        score = score_design_planning(filename, path_str)
    elif category_dir == '方法论' or '方法' in filename.lower():
        category = "方法论"
        score = score_methodology(filename, path_str)
    else:
        # 其他类型，基础评分
        score = 60
    
    rating = get_rating_level(score)
    
    return {
        'filename': filename,
        'path': path_str,
        'category': category,
        'score': score,
        'rating': rating
    }

def main():
    """主函数"""
    script_dir = Path(__file__).parent.absolute()
    base_dir = script_dir / "公关报告合集"
    
    if not base_dir.exists():
        print(f"[ERROR] 目录不存在: {base_dir}")
        return
    
    print("公关文档分类专属评分工具 v2.0")
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
                if file_path.suffix.lower() in ['.db', '.jpg', '.png', '.mp4', '.dxq', '.zip']:
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
        avg_score = sum(s['score'] for s in scores) / len(scores)
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
    output_file = base_dir / '文档评分报告_v2.json'
    report_data = {
        'generated_at': datetime.now().isoformat(),
        'version': '2.0',
        'total_documents': len(all_scores),
        'scores': all_scores,
        'statistics': {
            'by_category': {
                cat: {
                    'count': len(scores),
                    'avg_score': sum(s['score'] for s in scores) / len(scores),
                    'max_score': max(s['score'] for s in scores),
                    'min_score': min(s['score'] for s in scores),
                    'rating_distribution': {
                        level: sum(1 for s in scores if s['rating'].startswith(level))
                        for level in ['⭐⭐⭐⭐⭐', '⭐⭐⭐⭐', '⭐⭐⭐', '⭐⭐', '⭐']
                    }
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
    output_file = base_dir / '文档评分报告_v2.md'
    
    lines = []
    lines.append("# 📊 公关文档评分报告 v2.0")
    lines.append("")
    lines.append(f"**生成时间**: {report_data['generated_at']}")
    lines.append(f"**总文档数**: {report_data['total_documents']} 个")
    lines.append("")
    lines.append("**评分说明**: 本报告采用分类专属评分标准，每个分类根据其服务目标设计专属评价维度，总分100分。")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 统计概览
    lines.append("## 📈 评分概览")
    lines.append("")
    lines.append("### 各分类平均分")
    lines.append("")
    lines.append("| 分类 | 文档数 | 平均分 | 最高分 | 最低分 |")
    lines.append("|------|--------|--------|--------|--------|")
    
    stats = report_data['statistics']['by_category']
    for category, data in sorted(stats.items(), key=lambda x: x[1]['avg_score'], reverse=True):
        lines.append(f"| {category} | {data['count']} | {data['avg_score']:.1f}分 | {data['max_score']}分 | {data['min_score']}分 |")
    
    lines.append("")
    lines.append("### 评分等级分布")
    lines.append("")
    lines.append("| 等级 | 文档数 | 占比 |")
    lines.append("|------|--------|------|")
    
    total = report_data['total_documents']
    for rating, count in sorted(report_data['statistics']['by_rating'].items(), reverse=True):
        percentage = (count / total * 100) if total > 0 else 0
        lines.append(f"| {rating} | {count} | {percentage:.1f}% |")
    
    lines.append("")
    lines.append("### 各分类评分分布")
    lines.append("")
    
    for category, data in sorted(stats.items()):
        lines.append(f"#### {category}")
        lines.append("")
        lines.append("| 等级 | 文档数 |")
        lines.append("|------|--------|")
        for level, count in sorted(data['rating_distribution'].items(), reverse=True):
            if count > 0:
                lines.append(f"| {level} | {count} |")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # 详细评分（按分类分组，只显示高分文档）
    lines.append("## 📋 高分文档推荐")
    lines.append("")
    
    by_category = defaultdict(list)
    for score in report_data['scores']:
        by_category[score['category']].append(score)
    
    for category in sorted(by_category.keys()):
        scores = sorted(by_category[category], key=lambda x: x['score'], reverse=True)
        high_scores = [s for s in scores if s['score'] >= 80]
        
        if high_scores:
            lines.append(f"### {category} - 高分文档 (≥80分)")
            lines.append("")
            lines.append("| 文件名 | 评分 | 等级 |")
            lines.append("|--------|------|------|")
            
            for score in high_scores[:10]:  # 只显示前10个
                filename = score['filename'][:40] + '...' if len(score['filename']) > 40 else score['filename']
                lines.append(f"| {filename} | {score['score']}分 | {score['rating']} |")
            
            if len(high_scores) > 10:
                lines.append(f"| ... 还有 {len(high_scores) - 10} 个高分文档 | | |")
            lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("*评分报告版本 v2.0* | *生成时间: 2025年1月*")
    lines.append("")
    lines.append("**评分标准**: 详见 `分类专属评分标准.md`")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"Markdown报告已生成: {output_file}")
    except Exception as e:
        print(f"[ERROR] 生成Markdown报告失败: {e}")

if __name__ == "__main__":
    main()

