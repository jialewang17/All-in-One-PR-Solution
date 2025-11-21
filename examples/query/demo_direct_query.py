#!/usr/bin/env python3
"""
演示Neo4j直接查询系统
"""

from ask_pr import ask_question

def demo_questions():
    """演示各种问题查询"""
    print("🚀 Neo4j直接查询系统演示")
    print("=" * 60)
    
    # 演示问题列表
    demo_questions = [
        "美妆类品牌应该如何建立和消费者的联系",
        "华与华有哪些成功的品牌案例", 
        "内容营销的核心策略是什么",
        "如何提升品牌传播效果",
        "品牌营销中沉浸式体验的作用",
        "社交媒体在品牌传播中的重要性"
    ]
    
    print("📋 演示问题列表:")
    for i, q in enumerate(demo_questions, 1):
        print(f"{i}. {q}")
    
    print(f"\n🎯 选择要演示的问题 (1-{len(demo_questions)}) 或输入 'all' 演示所有问题:")
    
    choice = input("选择: ").strip()
    
    if choice.lower() == 'all':
        # 演示所有问题
        for i, question in enumerate(demo_questions, 1):
            print(f"\n{'='*80}")
            print(f"问题 {i}: {question}")
            print('='*80)
            answer = ask_question(question)
            print(f"\n🤖 回答:")
            print("-" * 40)
            print(answer)
            
            if i < len(demo_questions):
                input("\n按回车键继续下一个问题...")
    
    elif choice.isdigit() and 1 <= int(choice) <= len(demo_questions):
        # 演示单个问题
        question = demo_questions[int(choice) - 1]
        answer = ask_question(question)
        print(f"\n🤖 回答:")
        print("-" * 40)
        print(answer)
    
    else:
        print("❌ 无效选择")

def demo_usage():
    """演示使用方法"""
    print(f"\n📚 使用方法演示:")
    print("=" * 60)
    
    print("1. 命令行快速查询:")
    print("   python3 ask_pr.py '你的问题'")
    print("   示例: python3 ask_pr.py '美妆品牌如何建立消费者联系'")
    
    print(f"\n2. 交互式查询:")
    print("   python3 neo4j_direct_query.py")
    
    print(f"\n3. 在代码中使用:")
    print("   from ask_pr import ask_question")
    print("   answer = ask_question('你的问题')")
    
    print(f"\n4. 批量查询:")
    print("   questions = ['问题1', '问题2', '问题3']")
    print("   for q in questions:")
    print("       answer = ask_question(q)")

def demo_neo4j_setup():
    """演示Neo4j数据设置"""
    print(f"\n🔧 Neo4j数据设置演示:")
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
    
    print("添加向量嵌入:")
    print("""
    MATCH (c:PR_Chunk)
    WHERE c.textEmbeddingOpenAI IS NULL
    CALL apoc.ml.openai.embedding([c.text], 'your-api-key') YIELD embeddings
    SET c.textEmbeddingOpenAI = embeddings[0]
    """)

def main():
    """主函数"""
    print("🎬 Neo4j直接查询系统演示")
    print("=" * 60)
    
    print("选择演示内容:")
    print("1. 问题查询演示")
    print("2. 使用方法演示") 
    print("3. Neo4j数据设置演示")
    print("4. 全部演示")
    
    choice = input("选择 (1-4): ").strip()
    
    if choice == "1":
        demo_questions()
    elif choice == "2":
        demo_usage()
    elif choice == "3":
        demo_neo4j_setup()
    elif choice == "4":
        demo_questions()
        demo_usage()
        demo_neo4j_setup()
    else:
        print("❌ 无效选择")
    
    print(f"\n🎉 演示完成！")
    print(f"📚 详细使用说明请参考: Neo4j_Direct_Query_Guide.md")

if __name__ == "__main__":
    main()


