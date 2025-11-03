#!/usr/bin/env python3
"""
增量处理系统 - 自动识别已处理文件，只处理新文件
"""

import json
import os
import hashlib
from pathlib import Path
from datetime import datetime
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

class IncrementalProcessor:
    def __init__(self):
        self.processed_file = "data/processed_files.json"
        self.chunks_dir = Path("data/chunks")
        self.cleaned_dir = Path("data/cleaned")
        self.json_dir = Path("data/json")
        
    def get_file_hash(self, file_path):
        """计算文件MD5哈希值"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"计算文件哈希失败 {file_path}: {e}")
            return None
    
    def get_file_info(self, file_path):
        """获取文件信息"""
        stat = file_path.stat()
        return {
            "path": str(file_path),
            "name": file_path.name,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "hash": self.get_file_hash(file_path)
        }
    
    def load_processed_files(self):
        """加载已处理文件记录"""
        if os.path.exists(self.processed_file):
            with open(self.processed_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "files": {},
            "chunks": {},
            "last_processed": None
        }
    
    def save_processed_files(self, data):
        """保存已处理文件记录"""
        os.makedirs(os.path.dirname(self.processed_file), exist_ok=True)
        with open(self.processed_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def is_file_processed(self, file_path, processed_data):
        """检查文件是否已处理"""
        file_info = self.get_file_info(file_path)
        file_path_str = str(file_path)
        
        if file_path_str in processed_data["files"]:
            stored_info = processed_data["files"][file_path_str]
            # 比较哈希值，如果相同则认为已处理
            if stored_info.get("hash") == file_info["hash"]:
                return True
        
        return False
    
    def mark_file_processed(self, file_path, processed_data):
        """标记文件为已处理"""
        file_info = self.get_file_info(file_path)
        processed_data["files"][str(file_path)] = file_info
        processed_data["last_processed"] = datetime.now().isoformat()
    
    def get_new_files(self, input_dir):
        """获取需要处理的新文件"""
        processed_data = self.load_processed_files()
        new_files = []
        
        # 支持的文件格式
        supported_extensions = ['.pdf', '.xlsx', '.xls', '.csv', '.docx', '.doc', 
                              '.pptx', '.ppt', '.html', '.htm', '.json', '.txt']
        
        input_path = Path(input_dir)
        if not input_path.exists():
            print(f"输入目录不存在: {input_dir}")
            return new_files
        
        for file_path in input_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                if not self.is_file_processed(file_path, processed_data):
                    new_files.append(file_path)
                    print(f"🆕 发现新文件: {file_path.name}")
                else:
                    print(f"⏭️  跳过已处理文件: {file_path.name}")
        
        return new_files
    
    def process_new_files(self, input_dir="data/raw"):
        """处理新文件"""
        print("🔄 增量处理开始")
        print("=" * 60)
        
        # 获取新文件
        new_files = self.get_new_files(input_dir)
        
        if not new_files:
            print("✅ 没有新文件需要处理")
            return
        
        print(f"📁 发现 {len(new_files)} 个新文件需要处理")
        
        # 加载已处理文件记录
        processed_data = self.load_processed_files()
        
        # 处理每个新文件
        for file_path in new_files:
            print(f"\n📄 处理文件: {file_path.name}")
            
            try:
                # 1. 预处理
                print("  🔄 预处理...")
                from pr_multi_format_preprocessing import process_multi_format_documents
                process_multi_format_documents(input_dir, "data/cleaned")
                
                # 2. JSON转换
                print("  📋 JSON转换...")
                from pr_txt2json import process_pr_text_files
                process_pr_text_files()
                
                # 3. 分块
                print("  ✂️ 分块...")
                from pr_chunking import process_all_pr_files
                chunks = process_all_pr_files()
                
                # 4. Neo4j集成
                print("  🔗 Neo4j集成...")
                from pr_neo4j_simple import main as neo4j_main
                neo4j_main()
                
                # 标记文件为已处理
                self.mark_file_processed(file_path, processed_data)
                print(f"  ✅ 文件处理完成: {file_path.name}")
                
            except Exception as e:
                print(f"  ❌ 处理失败: {file_path.name} - {e}")
                continue
        
        # 保存处理记录
        self.save_processed_files(processed_data)
        print(f"\n🎉 增量处理完成！处理了 {len(new_files)} 个新文件")
    
    def check_neo4j_status(self):
        """检查Neo4j中的节点状态"""
        print("\n📊 检查Neo4j状态...")
        
        try:
            # 检查PR_Chunk节点数量
            chunk_count_query = "MATCH (c:PR_Chunk) RETURN count(c) as count"
            result = kg.query(chunk_count_query)
            chunk_count = result[0]['count'] if result else 0
            print(f"  PR_Chunk节点数量: {chunk_count}")
            
            # 检查NEXT关系数量
            next_count_query = "MATCH ()-[r:NEXT]->() RETURN count(r) as count"
            result = kg.query(next_count_query)
            next_count = result[0]['count'] if result else 0
            print(f"  NEXT关系数量: {next_count}")
            
            # 检查向量索引
            index_query = "SHOW INDEXES"
            indexes = kg.query(index_query)
            vector_indexes = [idx for idx in indexes if 'vector' in str(idx).lower()]
            print(f"  向量索引数量: {len(vector_indexes)}")
            
        except Exception as e:
            print(f"  ❌ 检查Neo4j状态失败: {e}")
    
    def cleanup_orphaned_chunks(self):
        """清理孤立的chunks（可选功能）"""
        print("\n🧹 清理孤立chunks...")
        
        try:
            # 查找没有NEXT关系的chunks
            orphaned_query = """
            MATCH (c:PR_Chunk)
            WHERE NOT (c)-[:NEXT]->() AND NOT ()-[:NEXT]->(c)
            RETURN count(c) as count
            """
            result = kg.query(orphaned_query)
            orphaned_count = result[0]['count'] if result else 0
            
            if orphaned_count > 0:
                print(f"  发现 {orphaned_count} 个孤立chunks")
                cleanup_choice = input("是否清理孤立chunks? (y/n): ").strip().lower()
                if cleanup_choice == 'y':
                    delete_query = """
                    MATCH (c:PR_Chunk)
                    WHERE NOT (c)-[:NEXT]->() AND NOT ()-[:NEXT]->(c)
                    DELETE c
                    """
                    kg.query(delete_query)
                    print("  ✅ 孤立chunks已清理")
            else:
                print("  ✅ 没有发现孤立chunks")
                
        except Exception as e:
            print(f"  ❌ 清理失败: {e}")
    
    def run(self):
        """运行增量处理器"""
        print("🚀 增量处理系统")
        print("=" * 60)
        
        # 检查Neo4j状态
        self.check_neo4j_status()
        
        # 处理新文件
        self.process_new_files()
        
        # 可选：清理孤立chunks
        cleanup_choice = input("\n是否检查并清理孤立chunks? (y/n): ").strip().lower()
        if cleanup_choice == 'y':
            self.cleanup_orphaned_chunks()

if __name__ == "__main__":
    processor = IncrementalProcessor()
    processor.run()


