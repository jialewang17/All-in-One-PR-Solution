#!/usr/bin/env python3
"""
Neo4j直接查询系统演示（非交互式）
"""

from ask_pr import ask_question

def demo_questions():
    """演示问题查询"""
    print("🚀 Neo4j直接查询系统演示")
    print("=" * 60)
    
    # 演示问题
    demo_questions = [
        "美妆类品牌应该如何建立和消费者的联系",
        "华与华有哪些成功的品牌案例", 
        "内容营销的核心策略是什么"
    ]
    
    print("📋 演示问题查询:")
    for i, question in enumerate(demo_questions, 1):
        print(f"\n{'='*80}")
        print(f"问题 {i}: {question}")
        print('='*80)
        
        try:
            answer = ask_question(question)
            print(f"\n🤖 回答:")
            print("-" * 40)
            print(answer)
        except Exception as e:
            print(f"❌ 查询失败: {e}")

def demo_usage():
    """演示使用方法"""
    print(f"\n📚 使用方法:")
    print("=" * 60)
    
    print("1. 命令行快速查询:")
    print("   python3 ask_pr.py '你的问题'")
    print("   示例: python3 ask_pr.py '美妆品牌如何建立消费者联系'")
    
    print(f"\n2. 交互式查询:")
    print("   python3 neo4j_direct_query.py")
    
    print(f"\n3. 在代码中使用:")
    print("   from ask_pr import ask_question")
    print("   answer = ask_question('你的问题')")

def demo_neo4j_setup():
    """演示Neo4j数据设置"""
    print(f"\n🔧 Neo4j数据设置:")
    print("=" * 60)
    
    print("在Neo4j中直接创建PR_Chunk节点:")
    print("""
    CREATE (c:PR_Chunk {
      chunkId: "brand_case_001",
      text: "雅诗兰黛通过沉浸式体验活动建立与消费者的联系",
      source: "雅诗兰黛案例",
      formItem: "品牌策略",
      chunkSeqId: 0,
      content_type: "brand_strategy",
      industry: "beauty",
      brand_mentioned: ["雅诗兰黛"]
    })
    """)
    
    print("创建向量索引:")
    print("""
    CREATE VECTOR INDEX PR_OpenAI IF NOT EXISTS
    FOR (c:PR_Chunk) ON (c.textEmbeddingOpenAI)
    OPTIONS {indexConfig: {
      `vector.dimensions`: 1536,
      `vector.similarity_function`: 'cosine'
    }}
    """)

def main():
    """主函数"""
    print("🎬 Neo4j直接查询系统演示")
    print("=" * 60)
    
    # 演示问题查询
    demo_questions()
    
    # 演示使用方法
    demo_usage()
    
    # 演示Neo4j设置
    demo_neo4j_setup()
    
    print(f"\n🎉 演示完成！")
    print(f"📚 详细使用说明请参考: Neo4j_Direct_Query_Guide.md")
    print(f"🚀 快速开始: python3 ask_pr.py '你的问题'")

if __name__ == "__main__":
    main()


