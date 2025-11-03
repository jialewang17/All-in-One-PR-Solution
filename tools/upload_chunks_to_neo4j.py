#!/usr/bin/env python3
"""
Chunks上传到Neo4j数据库工具
将已有的chunks数据上传到Neo4j知识图谱数据库
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph
import warnings
warnings.filterwarnings("ignore")

# 加载环境变量
load_dotenv('.env', override=True)

class ChunksUploader:
    """Chunks上传到Neo4j数据库类"""
    
    def __init__(self):
        self.chunks_dir = Path("data/chunks")
        self.neo4j_config = {
            'uri': os.getenv('NEO4J_URI'),
            'username': os.getenv('NEO4J_USERNAME'),
            'password': os.getenv('NEO4J_PASSWORD'),
            'database': os.getenv('NEO4J_DATABASE') or 'neo4j'
        }
        
        # 初始化Neo4j连接
        try:
            self.graph = Neo4jGraph(
                url=self.neo4j_config['uri'],
                username=self.neo4j_config['username'],
                password=self.neo4j_config['password'],
                database=self.neo4j_config['database']
            )
            print("✅ Neo4j连接成功")
        except Exception as e:
            print(f"❌ Neo4j连接失败: {e}")
            self.graph = None
    
    def check_chunks_files(self):
        """检查chunks文件"""
        if not self.chunks_dir.exists():
            print(f"❌ Chunks目录不存在: {self.chunks_dir}")
            return []
        
        chunk_files = list(self.chunks_dir.glob("*_chunks.json"))
        if not chunk_files:
            print("❌ 没有找到chunks文件")
            return []
        
        print(f"✅ 找到 {len(chunk_files)} 个chunks文件")
        return chunk_files
    
    def load_chunks_data(self, chunk_file):
        """加载chunks数据"""
        try:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"❌ 加载文件失败 {chunk_file}: {e}")
            return None
    
    def create_chunk_node(self, chunk_data, file_name):
        """创建chunk节点"""
        try:
            # 提取chunk信息
            chunk_id = chunk_data.get('id', f"{file_name}_{datetime.now().timestamp()}")
            text = chunk_data.get('text', '')
            metadata = chunk_data.get('metadata', {})
            
            # 创建节点属性
            node_properties = {
                'chunk_id': chunk_id,
                'text': text,
                'file_name': file_name,
                'content_type': metadata.get('content_type', 'unknown'),
                'industry': metadata.get('industry', 'unknown'),
                'brand_mentions': metadata.get('brand_mentions', []),
                'created_at': datetime.now().isoformat(),
                'source_file': file_name
            }
            
            # 创建Cypher查询
            cypher_query = """
            MERGE (c:PR_Chunk {chunk_id: $chunk_id})
            SET c.text = $text,
                c.file_name = $file_name,
                c.content_type = $content_type,
                c.industry = $industry,
                c.brand_mentions = $brand_mentions,
                c.created_at = $created_at,
                c.source_file = $source_file
            RETURN c
            """
            
            result = self.graph.query(cypher_query, node_properties)
            return True
            
        except Exception as e:
            print(f"❌ 创建节点失败: {e}")
            return False
    
    def create_relationships(self, chunk_data, file_name):
        """创建关系"""
        try:
            metadata = chunk_data.get('metadata', {})
            brand_mentions = metadata.get('brand_mentions', [])
            
            if not brand_mentions:
                return True
            
            chunk_id = chunk_data.get('id', f"{file_name}_{datetime.now().timestamp()}")
            
            # 为每个品牌创建关系
            for brand in brand_mentions:
                # 创建品牌节点
                brand_query = """
                MERGE (b:Brand {name: $brand_name})
                SET b.industry = $industry,
                    b.last_mentioned = $created_at
                """
                
                self.graph.query(brand_query, {
                    'brand_name': brand,
                    'industry': metadata.get('industry', 'unknown'),
                    'created_at': datetime.now().isoformat()
                })
                
                # 创建chunk与品牌的关系
                relationship_query = """
                MATCH (c:PR_Chunk {chunk_id: $chunk_id})
                MATCH (b:Brand {name: $brand_name})
                MERGE (c)-[:MENTIONS_BRAND]->(b)
                """
                
                self.graph.query(relationship_query, {
                    'chunk_id': chunk_id,
                    'brand_name': brand
                })
            
            return True
            
        except Exception as e:
            print(f"❌ 创建关系失败: {e}")
            return False
    
    def upload_file_chunks(self, chunk_file):
        """上传单个文件的chunks"""
        file_name = chunk_file.stem.replace('_chunks', '')
        print(f"\n📤 处理文件: {file_name}")
        
        # 加载数据
        chunks_data = self.load_chunks_data(chunk_file)
        if not chunks_data:
            return False
        
        # 检查数据格式
        if isinstance(chunks_data, list):
            chunks = chunks_data
        elif isinstance(chunks_data, dict) and 'chunks' in chunks_data:
            chunks = chunks_data['chunks']
        else:
            print(f"❌ 不支持的数据格式: {file_name}")
            return False
        
        success_count = 0
        total_count = len(chunks)
        
        print(f"📊 开始上传 {total_count} 个chunks...")
        
        for i, chunk in enumerate(chunks, 1):
            try:
                # 创建chunk节点
                if self.create_chunk_node(chunk, file_name):
                    # 创建关系
                    self.create_relationships(chunk, file_name)
                    success_count += 1
                
                if i % 10 == 0:
                    print(f"  进度: {i}/{total_count} ({i/total_count*100:.1f}%)")
                    
            except Exception as e:
                print(f"❌ 处理chunk {i} 失败: {e}")
        
        print(f"✅ {file_name}: {success_count}/{total_count} chunks上传成功")
        return success_count > 0
    
    def create_indexes(self):
        """创建索引以提高查询性能"""
        try:
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (c:PR_Chunk) ON (c.chunk_id)",
                "CREATE INDEX IF NOT EXISTS FOR (c:PR_Chunk) ON (c.file_name)",
                "CREATE INDEX IF NOT EXISTS FOR (c:PR_Chunk) ON (c.content_type)",
                "CREATE INDEX IF NOT EXISTS FOR (b:Brand) ON (b.name)",
                "CREATE INDEX IF NOT EXISTS FOR (b:Brand) ON (b.industry)"
            ]
            
            for index_query in indexes:
                self.graph.query(index_query)
            
            print("✅ 索引创建完成")
            return True
            
        except Exception as e:
            print(f"❌ 创建索引失败: {e}")
            return False
    
    def get_upload_stats(self):
        """获取上传统计信息"""
        try:
            # 统计chunk数量
            chunk_count_query = "MATCH (c:PR_Chunk) RETURN count(c) as chunk_count"
            result = self.graph.query(chunk_count_query)
            chunk_count = result[0]['chunk_count'] if result else 0
            
            # 统计品牌数量
            brand_count_query = "MATCH (b:Brand) RETURN count(b) as brand_count"
            result = self.graph.query(brand_count_query)
            brand_count = result[0]['brand_count'] if result else 0
            
            # 统计关系数量
            relationship_count_query = "MATCH ()-[r]->() RETURN count(r) as relationship_count"
            result = self.graph.query(relationship_count_query)
            relationship_count = result[0]['relationship_count'] if result else 0
            
            return {
                'chunk_count': chunk_count,
                'brand_count': brand_count,
                'relationship_count': relationship_count
            }
            
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return None
    
    def run(self):
        """运行上传流程"""
        print("🚀 启动Chunks上传到Neo4j流程...")
        print("=" * 60)
        
        # 检查Neo4j连接
        if not self.graph:
            print("❌ Neo4j连接失败，无法继续")
            return False
        
        # 检查chunks文件
        chunk_files = self.check_chunks_files()
        if not chunk_files:
            return False
        
        # 创建索引
        print("\n🔧 创建数据库索引...")
        self.create_indexes()
        
        # 上传每个文件
        success_files = 0
        total_files = len(chunk_files)
        
        for chunk_file in chunk_files:
            if self.upload_file_chunks(chunk_file):
                success_files += 1
        
        # 显示统计信息
        print("\n📊 上传完成统计:")
        print("=" * 60)
        
        stats = self.get_upload_stats()
        if stats:
            print(f"✅ 成功上传文件: {success_files}/{total_files}")
            print(f"📄 Neo4j中的Chunk节点: {stats['chunk_count']}")
            print(f"🏷️ Neo4j中的Brand节点: {stats['brand_count']}")
            print(f"🔗 Neo4j中的关系数量: {stats['relationship_count']}")
        else:
            print(f"✅ 成功上传文件: {success_files}/{total_files}")
        
        print("\n🎉 Chunks上传流程完成！")
        print("💡 现在可以使用选项5进行增强RAG查询")
        
        return success_files > 0

def main():
    """主函数"""
    print("📤 Chunks上传到Neo4j工具")
    print("=" * 60)
    
    uploader = ChunksUploader()
    success = uploader.run()
    
    if success:
        print("\n✅ 上传成功！")
    else:
        print("\n❌ 上传失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()


