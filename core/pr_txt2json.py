#!/usr/bin/env python3
"""
公关传播内容JSON转换脚本
将清理后的文本转换为结构化的JSON格式
"""

import os
import json
import re
from pathlib import Path

def read_text_file(file_path):
    """读取文本文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def parse_pr_text_to_json(text):
    """解析公关传播文本为JSON结构"""
    # 移除引用标记
    text = re.sub(r'\[\d+\]', '', text)
    
    # 按Section分割文本
    sections = re.split(r'\n(?=Section:)', text)
    
    # 初始化JSON结构
    json_structure = {}
    
    for section in sections:
        if not section.strip():
            continue
        
        # 匹配section标题
        section_match = re.match(r'Section: (.+)', section)
        if not section_match:
            # 如果没有Section标记，尝试其他模式
            if section.strip().startswith('Title:'):
                json_structure['title'] = section.strip().replace('Title:', '').strip()
            elif section.strip().startswith('Content:'):
                json_structure['content'] = section.strip().replace('Content:', '').strip()
            continue
        
        section_name = section_match.group(1)
        # 提取section内容
        section_content = section[len(section_match.group(0)):].strip()
        
        # 根据section名称分类内容
        if '品牌' in section_name or 'brand' in section_name.lower():
            json_structure['brand_info'] = section_content
        elif '策略' in section_name or 'strategy' in section_name.lower():
            json_structure['strategy'] = section_content
        elif '活动' in section_name or 'campaign' in section_name.lower():
            json_structure['campaign'] = section_content
        elif '媒体' in section_name or 'media' in section_name.lower():
            json_structure['media'] = section_content
        elif '受众' in section_name or 'audience' in section_name.lower():
            json_structure['audience'] = section_content
        elif '效果' in section_name or 'result' in section_name.lower() or 'kpi' in section_name.lower():
            json_structure['results'] = section_content
        else:
            # 默认存储为通用内容
            json_structure[section_name] = section_content
    
    return json_structure

def save_json_to_file(data, output_path):
    """保存JSON数据到文件"""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        print(f"JSON saved to: {output_path}")
        return True
    except Exception as e:
        print(f"Error saving JSON file {output_path}: {e}")
        return False

def process_pr_text_files(input_dir="data/cleaned", output_dir="data/json"):
    """处理公关传播文本文件"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        print(f"Input directory {input_dir} does not exist")
        return
    
    # 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 处理所有文本文件
    txt_files = list(input_path.glob("*.txt"))
    
    if not txt_files:
        print(f"No text files found in {input_dir}")
        return
    
    print(f"Found {len(txt_files)} text files to process")
    
    for txt_file in txt_files:
        print(f"\nProcessing: {txt_file.name}")
        
        # 读取文本内容
        text_content = read_text_file(txt_file)
        if not text_content:
            continue
        
        # 解析为JSON
        json_data = parse_pr_text_to_json(text_content)
        if not json_data:
            print(f"No JSON data generated from {txt_file.name}")
            continue
        
        # 生成输出文件名
        output_filename = txt_file.stem + ".json"
        output_file_path = output_path / output_filename
        
        # 保存JSON
        if save_json_to_file(json_data, output_file_path):
            print(f"✅ Successfully processed {txt_file.name}")
            print(f"   Generated {len(json_data)} sections")
        else:
            print(f"❌ Failed to process {txt_file.name}")

if __name__ == "__main__":
    print("🚀 公关传播文本转JSON开始")
    print("="*50)
    
    # 处理文本文件
    process_pr_text_files()
    
    print("\n✅ JSON转换完成！")
    print("处理后的JSON文件保存在 data/json/ 目录中")


