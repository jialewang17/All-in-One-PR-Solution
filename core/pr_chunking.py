#!/usr/bin/env python3
"""
公关传播内容分块脚本
将JSON数据分割成适合RAG处理的小块
"""

import json
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path

# 配置文本分割器，适配公关传播内容
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,  # 适合公关内容的块大小
    chunk_overlap=200,  # 重叠部分，保持上下文连贯性
    length_function=len,
    separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
)

def split_pr_data_from_file(file):
    """分割公关传播数据文件"""
    chunks_with_metadata = []
    
    try:
        file_as_object = json.load(open(file, 'r', encoding='utf-8'))
        keys = list(file_as_object.keys())
        print(f"Processing file: {file}")
        print(f"Found sections: {keys}")
        
        for item in keys:
            print(f'Processing {item} from {file}')
            item_text = file_as_object[item]
            
            # 处理不同类型的数据
            if isinstance(item_text, list):
                # 如果是列表，用换行符连接
                item_text = '\n'.join(str(x) for x in item_text)
            elif not isinstance(item_text, str):
                # 转换为字符串
                item_text = str(item_text)
            
            # 分割文本
            item_text_chunks = text_splitter.split_text(item_text)
            
            chunk_seq_id = 0
            for chunk in item_text_chunks:
                form_name = file[file.rindex('/') + 1:file.rindex('.')]
                chunks_with_metadata.append({
                    'text': chunk,
                    'formItem': item,
                    'chunkSeqId': chunk_seq_id,
                    'chunkId': f'{form_name}-{item}-chunk{chunk_seq_id:04d}',
                    'source': file_as_object.get('Source', file),
                    'content_type': determine_content_type(item, chunk),
                    'industry': extract_industry_info(chunk),
                    'brand_mentioned': extract_brand_mentions(chunk)
                })
                chunk_seq_id += 1
            print(f'\tSplit into {chunk_seq_id} chunks')
        
        # 保存分块数据
        output_dir = "data/chunks"
        os.makedirs(output_dir, exist_ok=True)
        
        filename = os.path.basename(file).replace('.json', '')
        output_file = os.path.join(output_dir, f"{filename}_chunks.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_with_metadata, f, indent=2, ensure_ascii=False)
        
        print(f"Chunks saved to: {output_file}")
        return chunks_with_metadata
        
    except Exception as e:
        print(f"Error processing file {file}: {e}")
        return []

def determine_content_type(item, chunk):
    """确定内容类型"""
    content_type = "general"
    
    if 'brand' in item.lower() or '品牌' in item:
        content_type = "brand_info"
    elif 'strategy' in item.lower() or '策略' in item:
        content_type = "strategy"
    elif 'campaign' in item.lower() or '活动' in item:
        content_type = "campaign"
    elif 'media' in item.lower() or '媒体' in item:
        content_type = "media"
    elif 'audience' in item.lower() or '受众' in item:
        content_type = "audience"
    elif 'result' in item.lower() or '效果' in item or 'kpi' in item.lower():
        content_type = "results"
    
    return content_type

def extract_industry_info(chunk):
    """提取行业信息"""
    industries = ['科技', '金融', '零售', '汽车', '食品', '时尚', '医疗', '教育', '旅游']
    for industry in industries:
        if industry in chunk:
            return industry
    return "unknown"

def extract_brand_mentions(chunk):
    """提取品牌提及"""
    # 简单的品牌名称提取（可以根据需要扩展）
    brand_keywords = ['品牌', 'brand', '公司', '企业']
    brands = []
    
    for keyword in brand_keywords:
        if keyword in chunk.lower():
            # 这里可以添加更复杂的品牌名称提取逻辑
            brands.append(keyword)
    
    return brands

def process_all_pr_files(input_dir="data/json"):
    """处理所有公关传播JSON文件"""
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Input directory {input_dir} does not exist")
        return
    
    json_files = list(input_path.glob("*.json"))
    
    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return
    
    print(f"Found {len(json_files)} JSON files to process")
    
    all_chunks = []
    
    for json_file in json_files:
        print(f"\nProcessing: {json_file.name}")
        chunks = split_pr_data_from_file(str(json_file))
        all_chunks.extend(chunks)
    
    print(f"\n✅ 处理完成！总共生成了 {len(all_chunks)} 个chunks")
    return all_chunks

if __name__ == "__main__":
    print("🚀 公关传播内容分块开始")
    print("="*50)
    
    # 处理所有文件
    process_all_pr_files()
    
    print("\n✅ 分块完成！")
    print("处理后的chunks保存在 data/chunks/ 目录中")


