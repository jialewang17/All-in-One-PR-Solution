#!/usr/bin/env python3
"""
Chunk结果人工编辑和Neo4j同步工具
允许用户修改chunk的metadata并同步到Neo4j
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph
import warnings
warnings.filterwarnings("ignore")

# Load environment variables
load_dotenv('.env', override=True)

# Neo4j connection
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE') or 'neo4j'

kg = Neo4jGraph(
    url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD, database=NEO4J_DATABASE
)

class ChunkEditor:
    def __init__(self):
        self.chunks_dir = Path("data/chunks")
        self.processed_file = "data/processed_files.json"
        
    def load_processed_files(self):
        """加载已处理文件列表"""
        if os.path.exists(self.processed_file):
            with open(self.processed_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"files": [], "chunks": {}}
    
    def save_processed_files(self, data):
        """保存已处理文件列表"""
        with open(self.processed_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def list_chunk_files(self):
        """列出所有chunk文件"""
        chunk_files = list(self.chunks_dir.glob("*_chunks.json"))
        return chunk_files
    
    def load_chunk_file(self, file_path):
        """加载chunk文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_chunk_file(self, file_path, chunks):
        """保存chunk文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
    
    def edit_chunk_metadata(self, chunk, chunk_index):
        """编辑单个chunk的metadata"""
        print(f"\n--- 编辑 Chunk {chunk_index} ---")
        print(f"当前内容: {chunk['text'][:100]}...")
        print(f"当前 metadata:")
        print(f"  - content_type: {chunk.get('content_type', 'general')}")
        print(f"  - industry: {chunk.get('industry', 'unknown')}")
        print(f"  - brand_mentioned: {chunk.get('brand_mentioned', [])}")
        
        print("\n请选择要修改的字段 (输入数字):")
        print("1. content_type")
        print("2. industry") 
        print("3. brand_mentioned")
        print("4. 跳过此chunk")
        
        choice = input("选择 (1-4): ").strip()
        
        if choice == "1":
            new_content_type = input(f"输入新的content_type (当前: {chunk.get('content_type', 'general')}): ").strip()
            if new_content_type:
                chunk['content_type'] = new_content_type
                print(f"✅ 已更新 content_type: {new_content_type}")
        
        elif choice == "2":
            new_industry = input(f"输入新的industry (当前: {chunk.get('industry', 'unknown')}): ").strip()
            if new_industry:
                chunk['industry'] = new_industry
                print(f"✅ 已更新 industry: {new_industry}")
        
        elif choice == "3":
            current_brands = chunk.get('brand_mentioned', [])
            print(f"当前brand_mentioned: {current_brands}")
            print("输入品牌名称，用逗号分隔 (留空表示不修改):")
            new_brands_input = input("品牌列表: ").strip()
            if new_brands_input:
                new_brands = [brand.strip() for brand in new_brands_input.split(',') if brand.strip()]
                chunk['brand_mentioned'] = new_brands
                print(f"✅ 已更新 brand_mentioned: {new_brands}")
        
        elif choice == "4":
            print("跳过此chunk")
            return False
        
        return True
    
    def sync_to_neo4j(self, chunks):
        """将修改后的chunks同步到Neo4j"""
        print("\n🔄 同步到Neo4j...")
        
        for chunk in chunks:
            chunk_id = chunk['chunkId']
            
            # 更新Neo4j中的节点
            update_query = """
            MATCH (c:PR_Chunk {chunkId: $chunkId})
            SET c.content_type = $content_type,
                c.industry = $industry,
                c.brand_mentioned = $brand_mentioned
            RETURN c
            """
            
            try:
                result = kg.query(update_query, params={
                    'chunkId': chunk_id,
                    'content_type': chunk.get('content_type', 'general'),
                    'industry': chunk.get('industry', 'unknown'),
                    'brand_mentioned': chunk.get('brand_mentioned', [])
                })
                print(f"✅ 已更新chunk: {chunk_id}")
            except Exception as e:
                print(f"❌ 更新chunk失败 {chunk_id}: {e}")
    
    def edit_chunk_file(self, file_path):
        """编辑chunk文件"""
        print(f"\n📝 编辑文件: {file_path.name}")
        
        # 加载chunks
        chunks = self.load_chunk_file(file_path)
        
        if not chunks:
            print("文件为空，跳过")
            return
        
        print(f"文件包含 {len(chunks)} 个chunks")
        
        # 显示前几个chunks供选择
        print("\n前5个chunks预览:")
        for i, chunk in enumerate(chunks[:5]):
            print(f"{i+1}. {chunk['text'][:50]}...")
        
        # 选择编辑模式
        print("\n选择编辑模式:")
        print("1. 编辑所有chunks")
        print("2. 编辑指定范围的chunks")
        print("3. 搜索并编辑特定chunks")
        
        mode = input("选择模式 (1-3): ").strip()
        
        if mode == "1":
            # 编辑所有chunks
            for i, chunk in enumerate(chunks):
                if self.edit_chunk_metadata(chunk, i+1):
                    continue
                else:
                    break
        
        elif mode == "2":
            # 编辑指定范围
            start = int(input("起始索引 (从1开始): ")) - 1
            end = int(input("结束索引: "))
            
            for i in range(start, min(end, len(chunks))):
                if self.edit_chunk_metadata(chunks[i], i+1):
                    continue
                else:
                    break
        
        elif mode == "3":
            # 搜索并编辑
            search_term = input("输入搜索关键词: ").strip()
            matching_indices = []
            
            for i, chunk in enumerate(chunks):
                if search_term.lower() in chunk['text'].lower():
                    matching_indices.append(i)
            
            if not matching_indices:
                print("未找到匹配的chunks")
                return
            
            print(f"找到 {len(matching_indices)} 个匹配的chunks")
            for idx in matching_indices:
                if self.edit_chunk_metadata(chunks[idx], idx+1):
                    continue
                else:
                    break
        
        # 保存修改
        save_choice = input("\n是否保存修改? (y/n): ").strip().lower()
        if save_choice == 'y':
            self.save_chunk_file(file_path, chunks)
            print("✅ 文件已保存")
            
            # 同步到Neo4j
            sync_choice = input("是否同步到Neo4j? (y/n): ").strip().lower()
            if sync_choice == 'y':
                self.sync_to_neo4j(chunks)
        else:
            print("修改已丢弃")
    
    def run(self):
        """运行编辑器"""
        print("🔧 Chunk结果编辑器")
        print("=" * 50)
        
        # 列出所有chunk文件
        chunk_files = self.list_chunk_files()
        
        if not chunk_files:
            print("未找到chunk文件")
            return
        
        print(f"找到 {len(chunk_files)} 个chunk文件:")
        for i, file_path in enumerate(chunk_files):
            print(f"{i+1}. {file_path.name}")
        
        # 选择文件
        try:
            file_index = int(input(f"\n选择要编辑的文件 (1-{len(chunk_files)}): ")) - 1
            if 0 <= file_index < len(chunk_files):
                self.edit_chunk_file(chunk_files[file_index])
            else:
                print("无效的文件索引")
        except ValueError:
            print("请输入有效的数字")

if __name__ == "__main__":
    editor = ChunkEditor()
    editor.run()


