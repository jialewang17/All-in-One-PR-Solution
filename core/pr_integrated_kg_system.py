#!/usr/bin/env python3
"""
集成的知识图谱系统
整合SPO三元组提取、图谱构建和RAG查询功能
"""

from typing import List, Dict, Any, Optional
from pr_spo_extractor import SPOTripleExtractor
from pr_kg_builder import KnowledgeGraphBuilder
from pr_kg_rag import KnowledgeGraphRAG


class IntegratedKGSystem:
    """集成的知识图谱系统"""
    
    def __init__(
        self,
        model_name: str = "deepseek/deepseek-chat-v3-0324",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        use_openrouter: bool = True,
        temperature: float = 0.0,
        max_tokens: int = 4096
    ):
        """
        初始化集成系统
        
        Args:
            model_name: LLM模型名称
            api_key: API密钥
            base_url: API基础URL
            use_openrouter: 是否使用OpenRouter
            temperature: 提取温度（0.0用于确定性）
            max_tokens: 最大token数
        """
        # 初始化SPO提取器
        self.extractor = SPOTripleExtractor(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            use_openrouter=use_openrouter
        )
        
        # 初始化图谱构建器
        self.kg_builder = KnowledgeGraphBuilder()
        
        # 初始化RAG系统（稍后创建，需要图谱）
        self.rag_system = None
        
        # 存储归一化的三元组
        self.normalized_triples = []
        
        # 保存配置参数
        self.use_openrouter = use_openrouter
        
        print("✅ 集成知识图谱系统初始化完成")
    
    def process_text(
        self,
        text: str,
        chunk_size: int = 150,
        overlap: int = 30,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        处理文本：提取三元组并构建图谱
        
        Args:
            text: 要处理的文本
            chunk_size: 分块大小（词数）
            overlap: 重叠大小（词数）
            verbose: 是否打印详细信息
            
        Returns:
            处理结果字典
        """
        if verbose:
            print("📝 开始处理文本...")
        
        # 1. 提取三元组
        extraction_result = self.extractor.extract_triples_from_text(
            text,
            chunk_size=chunk_size,
            overlap=overlap,
            verbose=verbose
        )
        
        if verbose:
            print(f"✅ 提取完成: {len(extraction_result['triples'])} 个三元组")
        
        # 2. 归一化三元组
        self.normalized_triples = self.extractor.normalize_triples(
            extraction_result['triples']
        )
        
        if verbose:
            print(f"✅ 归一化完成: {len(self.normalized_triples)} 个唯一三元组")
        
        # 3. 构建图谱
        added_edges = self.kg_builder.add_triples(self.normalized_triples)
        
        if verbose:
            stats = self.kg_builder.get_statistics()
            print(f"✅ 图谱构建完成: {stats['nodes']} 节点, {stats['edges']} 边")
        
        # 4. 初始化RAG系统
        self.rag_system = KnowledgeGraphRAG(
            self.kg_builder,
            model_name=self.extractor.model_name,
            api_key=self.extractor.api_key,
            base_url=self.extractor.base_url,
            use_openrouter=self.use_openrouter,
            temperature=0.7,
            max_tokens=500
        )
        
        return {
            'extraction_result': extraction_result,
            'normalized_triples_count': len(self.normalized_triples),
            'graph_stats': self.kg_builder.get_statistics(),
            'edges_added': added_edges
        }
    
    def query(
        self,
        question: str,
        verbose: bool = False
    ) -> str:
        """
        使用图谱RAG回答问题
        
        Args:
            question: 用户问题
            verbose: 是否打印详细信息
            
        Returns:
            回答
        """
        if self.rag_system is None:
            raise ValueError("请先处理文本以构建图谱")
        
        if not self.normalized_triples:
            raise ValueError("没有可用的三元组数据")
        
        return self.rag_system.query(
            question,
            self.normalized_triples,
            verbose=verbose
        )
    
    def query_with_details(
        self,
        question: str,
        max_hops: int = 2,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        使用详细信息的查询
        
        Args:
            question: 用户问题
            max_hops: 最大跳数
            verbose: 是否打印详细信息
            
        Returns:
            包含答案和元数据的字典
        """
        if self.rag_system is None:
            raise ValueError("请先处理文本以构建图谱")
        
        if not self.normalized_triples:
            raise ValueError("没有可用的三元组数据")
        
        return self.rag_system.query_with_related_entities(
            question,
            self.normalized_triples,
            max_hops=max_hops,
            verbose=verbose
        )
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        return self.kg_builder.get_statistics()
    
    def get_top_entities(self, top_k: int = 10) -> List[Dict[str, Any]]:
        """获取最重要的实体（度最高的节点）"""
        return self.kg_builder.get_node_with_highest_degree(top_k)
    
    def export_graph(self, filepath: str):
        """导出图谱到JSON文件"""
        self.kg_builder.export_to_json(filepath)
    
    def clear(self):
        """清空系统状态"""
        self.kg_builder.clear()
        self.normalized_triples = []
        self.rag_system = None


def demo_integrated_system():
    """演示集成系统"""
    print("🚀 集成知识图谱系统演示")
    print("=" * 70)
    
    # 测试文本
    test_text = """
    玛丽·居里，原名玛丽亚·斯克沃多夫斯卡，出生于波兰华沙，是一位开创性的物理学家和化学家。
    她在放射性研究方面进行了开创性的研究。与她的丈夫皮埃尔·居里一起，
    她发现了元素钋和镭。玛丽·居里是第一位获得诺贝尔奖的女性，
    第一位也是唯一一位两次获得诺贝尔奖的女性，
    也是唯一一位在两个不同科学领域获得诺贝尔奖的人。
    她于1903年与皮埃尔·居里和亨利·贝克勒尔一起获得诺贝尔物理学奖。
    后来，她于1911年因对镭和钋的研究获得诺贝尔化学奖。
    在第一次世界大战期间，她开发了移动X射线单位，被称为"小居里"，
    为野战医院提供X射线服务。玛丽·居里于1934年死于再生障碍性贫血，
    这可能是由于她长期接触辐射造成的。
    
    玛丽于1867年11月7日出生于一个重视教育的教师家庭。
    她早期在华沙接受教育，但在1891年移居巴黎，
    在索邦大学继续学习，在那里她获得了物理学和数学学位。
    她于1894年遇到了物理学教授皮埃尔·居里，他们于1895年结婚，开始了富有成效的科学合作。
    1906年皮埃尔在街道事故中不幸去世后，玛丽接替了他的教职，
    成为索邦大学第一位女性教授。
    
    居里夫妇在放射性方面的研究是在充满挑战的条件下进行的，
    在一个设备简陋、没有适当通风的棚子里，他们处理了数吨沥青铀矿来分离镭。
    玛丽·居里在巴黎建立了居里研究所，这成为医学研究的主要中心。
    她有两个女儿：伊雷娜，后来与丈夫一起获得诺贝尔化学奖；和夏娃，后来成为一名作家。
    玛丽的笔记本今天仍然具有放射性，保存在铅衬的盒子里。
    她的遗产不仅包括她的科学发现，还包括她在学术界和科学界打破性别障碍的作用。
    """
    
    try:
        # 初始化系统
        print("\n📦 初始化系统...")
        system = IntegratedKGSystem(verbose=True)
        
        # 处理文本
        print("\n" + "=" * 70)
        print("📝 处理文本并构建图谱...")
        result = system.process_text(
            test_text,
            chunk_size=100,
            overlap=20,
            verbose=True
        )
        
        # 显示统计
        print("\n" + "=" * 70)
        print("📊 图谱统计信息:")
        stats = system.get_graph_statistics()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # 显示最重要的实体
        print("\n" + "=" * 70)
        print("🏆 最重要的实体（Top 5）:")
        top_entities = system.get_top_entities(5)
        for i, entity in enumerate(top_entities, 1):
            print(f"   {i}. {entity['entity']} (度: {entity['degree']})")
        
        # 测试查询
        print("\n" + "=" * 70)
        print("❓ 测试问答:")
        
        questions = [
            "玛丽·居里在哪两个领域获得了诺贝尔奖？",
            "皮埃尔·居里的孩子是谁？",
            "玛丽·居里去世时多少岁？"
        ]
        
        for q in questions:
            print(f"\n问题: {q}")
            answer = system.query(q, verbose=False)
            print(f"回答: {answer}")
            print("-" * 70)
        
        # 导出图谱
        print("\n" + "=" * 70)
        export_path = "demo_knowledge_graph.json"
        system.export_graph(export_path)
        print(f"💾 图谱已导出到: {export_path}")
        
        return system
    
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    demo_integrated_system()

