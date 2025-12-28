#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将传播全流程案例报告JSON转换为Markdown格式
适合在飞书中查看，支持自动分级显示
"""

import json
from pathlib import Path
from datetime import datetime

# 传播流程阶段顺序（按流程顺序排列）
STAGE_ORDER = [
    "环境洞察",
    "策略制定",
    "资源评估",
    "执行投放",
    "效果监测",
    "经验沉淀"
]

# 阶段图标
STAGE_ICONS = {
    "环境洞察": "🔍",
    "策略制定": "📋",
    "资源评估": "📊",
    "执行投放": "🚀",
    "效果监测": "📈",
    "经验沉淀": "💡"
}

def format_completeness(completeness):
    """格式化完整度显示"""
    percentage = completeness * 100
    if percentage >= 100:
        return "✅ 100% (完整)"
    elif percentage >= 80:
        return f"🟢 {percentage:.0f}% (优秀)"
    elif percentage >= 60:
        return f"🟡 {percentage:.0f}% (良好)"
    else:
        return f"🟠 {percentage:.0f}% (一般)"

def generate_markdown_report(json_file_path, output_file_path=None):
    """生成Markdown格式的报告"""
    
    # 读取JSON文件
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 如果没有指定输出文件，使用默认名称
    if output_file_path is None:
        json_path = Path(json_file_path)
        output_file_path = json_path.parent / f"{json_path.stem}.md"
    
    # 生成Markdown内容
    md_content = []
    
    # 标题和元信息
    md_content.append("# 📊 传播全流程案例报告\n")
    md_content.append(f"**生成时间**: {data['generated_at']}\n")
    md_content.append(f"**总案例数**: {data['total_cases']} 个\n")
    md_content.append("\n---\n")
    
    # 概览统计
    md_content.append("## 📈 概览统计\n\n")
    md_content.append("| 指标 | 数值 |\n")
    md_content.append("|------|------|\n")
    md_content.append(f"| 总案例数 | {data['total_cases']} 个 |\n")
    
    # 计算完整度统计
    completeness_list = [case['completeness'] for case in data['cases']]
    avg_completeness = sum(completeness_list) / len(completeness_list) if completeness_list else 0
    md_content.append(f"| 平均完整度 | {avg_completeness*100:.1f}% |\n")
    md_content.append(f"| 最高完整度 | {max(completeness_list)*100:.1f}% |\n")
    md_content.append(f"| 最低完整度 | {min(completeness_list)*100:.1f}% |\n")
    md_content.append("\n")
    
    # 案例列表（按完整度排序）
    md_content.append("## 📋 案例列表\n\n")
    md_content.append("| 排名 | 品牌/项目 | 完整度 | 阶段数 | 文件数 | 包含阶段 |\n")
    md_content.append("|------|----------|--------|--------|--------|----------|\n")
    
    for idx, case in enumerate(data['cases'], 1):
        stages_str = "、".join(case['stages'][:3])  # 只显示前3个阶段
        if len(case['stages']) > 3:
            stages_str += f"等{len(case['stages'])}个"
        
        completeness_display = format_completeness(case['completeness'])
        md_content.append(
            f"| {idx} | **{case['brand']}** | {completeness_display} | "
            f"{case['stage_count']}/6 | {case['file_count']} | {stages_str} |\n"
        )
    
    md_content.append("\n---\n")
    
    # 详细案例信息
    md_content.append("## 📚 详细案例信息\n")
    
    for idx, case in enumerate(data['cases'], 1):
        md_content.append(f"### {idx}. {case['brand']}\n")
        
        # 基本信息表格
        md_content.append("#### 📊 基本信息\n\n")
        md_content.append("| 项目 | 内容 |\n")
        md_content.append("|------|------|\n")
        md_content.append(f"| **完整度** | {format_completeness(case['completeness'])} |\n")
        md_content.append(f"| **阶段数** | {case['stage_count']}/6 |\n")
        md_content.append(f"| **文件数** | {case['file_count']} 个 |\n")
        md_content.append(f"| **分类** | {', '.join(case['categories'])} |\n")
        md_content.append("\n")
        
        # 传播流程阶段（按流程顺序）
        md_content.append("#### 🔄 传播流程阶段\n")
        
        # 按流程顺序显示阶段
        ordered_stages = []
        for stage in STAGE_ORDER:
            if stage in case['stages']:
                ordered_stages.append(stage)
        
        # 显示流程进度条
        progress_bar = ""
        for stage in STAGE_ORDER:
            if stage in case['stages']:
                progress_bar += "✅"
            else:
                progress_bar += "⚪"
            progress_bar += " "
        
        md_content.append(f"**流程进度**: {progress_bar}\n")
        md_content.append("\n")
        
        # 详细阶段信息
        for stage in ordered_stages:
            icon = STAGE_ICONS.get(stage, "📌")
            md_content.append(f"##### {icon} {stage}\n")
            
            files = case['files_by_stage'].get(stage, [])
            if files:
                md_content.append(f"**文件数**: {len(files)} 个\n\n")
                md_content.append("**文件列表**:\n")
                for file in files:
                    md_content.append(f"- `{file}`\n")
            else:
                md_content.append("**状态**: 暂无文件\n")
            md_content.append("\n")
        
        # 如果还有未按流程顺序的阶段
        other_stages = [s for s in case['stages'] if s not in STAGE_ORDER]
        if other_stages:
            md_content.append("##### 📌 其他阶段\n")
            for stage in other_stages:
                files = case['files_by_stage'].get(stage, [])
                md_content.append(f"**{stage}**: {len(files)} 个文件\n")
        
        md_content.append("\n---\n")
    
    # 总结和建议
    md_content.append("## 💡 总结与建议\n")
    md_content.append("\n### 完整度分析\n")
    
    # 按完整度分组
    excellent = [c for c in data['cases'] if c['completeness'] >= 0.8]
    good = [c for c in data['cases'] if 0.6 <= c['completeness'] < 0.8]
    normal = [c for c in data['cases'] if c['completeness'] < 0.6]
    
    if excellent:
        md_content.append("#### 🟢 优秀案例（完整度 ≥ 80%）\n")
        for case in excellent:
            md_content.append(f"- **{case['brand']}** ({case['completeness']*100:.0f}%) - "
                            f"包含 {case['stage_count']} 个阶段，{case['file_count']} 个文件\n")
        md_content.append("\n")
    
    if good:
        md_content.append("#### 🟡 良好案例（完整度 60%-80%）\n")
        for case in good:
            md_content.append(f"- **{case['brand']}** ({case['completeness']*100:.0f}%) - "
                            f"包含 {case['stage_count']} 个阶段，{case['file_count']} 个文件\n")
        md_content.append("\n")
    
    if normal:
        md_content.append("#### 🟠 一般案例（完整度 < 60%）\n")
        for case in normal:
            md_content.append(f"- **{case['brand']}** ({case['completeness']*100:.0f}%) - "
                            f"包含 {case['stage_count']} 个阶段，{case['file_count']} 个文件\n")
        md_content.append("\n")
    
    md_content.append("### 📌 使用建议\n")
    md_content.append("1. **优先学习优秀案例**：完整度 ≥ 80% 的案例包含完整的传播流程，可作为最佳实践参考\n")
    md_content.append("2. **补充缺失阶段**：对于完整度较低的案例，可以补充缺失的传播阶段文件\n")
    md_content.append("3. **流程完整性**：理想的传播案例应包含从环境洞察到经验沉淀的完整6个阶段\n")
    md_content.append("4. **持续更新**：定期运行 `extract_communication_flow_cases.py` 更新案例报告\n")
    
    md_content.append("\n---\n")
    md_content.append(f"\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    # 写入文件
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md_content))
    
    print(f"[OK] Markdown报告已生成: {output_file_path}")
    return output_file_path

def main():
    """主函数"""
    script_dir = Path(__file__).parent.absolute()
    json_file = script_dir / "公关报告合集" / "传播全流程案例报告.json"
    
    if not json_file.exists():
        print(f"[ERROR] 文件不存在: {json_file}")
        return
    
    print("正在转换JSON报告为Markdown格式...")
    output_file = generate_markdown_report(json_file)
    print(f"\n[OK] 转换完成！")
    print(f"Markdown文件: {output_file}")
    print(f"\n提示：可以将Markdown文件上传到飞书，会自动显示分级结构")

if __name__ == "__main__":
    main()

