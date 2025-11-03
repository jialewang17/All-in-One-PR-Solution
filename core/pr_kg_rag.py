#!/usr/bin/env python3
"""
基于图谱的RAG查询模块
使用知识图谱进行检索增强生成
"""

import os
from typing import List, Dict, Any, Set, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    import openai
except ImportError:
    print("⚠️ 警告: openai库未安装，请运行: pip install openai")
    openai = None

from pr_kg_builder import KnowledgeGraphBuilder


class KnowledgeGraphRAG:
    """基于知识图谱的RAG系统"""
    
    def __init__(
        self,
        knowledge_graph: KnowledgeGraphBuilder,
        model_name: str = "deepseek/deepseek-chat-v3-0324",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        use_openrouter: bool = True
    ):
        """
        初始化图谱RAG系统
        
        Args:
            knowledge_graph: 知识图谱构建器实例
            model_name: LLM模型名称
            api_key: API密钥
            base_url: API基础URL
            temperature: 生成温度
            max_tokens: 最大token数
            use_openrouter: 是否使用OpenRouter
        """
        self.kg = knowledge_graph
        
        # 配置API
        if use_openrouter:
            self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
            self.base_url = base_url or "https://openrouter.ai/api/v1"
        else:
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            self.base_url = base_url or None
        
        self.model_name = model_name if model_name != "deepseek/deepseek-chat-v3-0324" else "gpt-3.5-turbo"
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 初始化OpenAI客户端
        if not self.api_key:
            raise ValueError(
                "API key未设置。请设置环境变量 OPENROUTER_API_KEY 或 OPENAI_API_KEY"
            )
        
        try:
            self.client = openai.OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
        except Exception as e:
            raise Exception(f"OpenAI客户端初始化失败: {e}")
    
    def _extract_entities_from_question(
        self,
        question: str,
        normalized_triples: List[Dict[str, Any]]
    ) -> Set[str]:
        """
        从问题中提取相关实体
        
        Args:
            question: 用户问题
            normalized_triples: 归一化的三元组列表（用于实体匹配）
            
        Returns:
            相关实体集合
        """
        question_lower = question.lower()
        question_words = set(question_lower.split())
        
        query_entities = set()
        
        # 从三元组中匹配实体
        for triple in normalized_triples:
            subject = triple.get('subject', '')
            obj = triple.get('object', '')
            
            # 检查subject是否在问题中
            if subject in question_lower or any(
                word in question_words for word in subject.split()
            ):
                query_entities.add(subject)
            
            # 检查object是否在问题中
            if obj in question_lower or any(
                word in question_words for word in obj.split()
            ):
                query_entities.add(obj)
        
        return query_entities
    
    def _build_context_from_graph(
        self,
        entities: Set[str],
        max_triples: int = 50
    ) -> str:
        """
        从图谱中构建上下文
        
        Args:
            entities: 相关实体集合
            max_triples: 最大三元组数
            
        Returns:
            上下文文本
        """
        if not entities:
            return "未找到相关问题实体。"
        
        # 获取相关的三元组文本
        triples_text = self.kg.get_triples_for_context(entities, max_edges=max_triples)
        
        if not triples_text:
            return "图谱中未找到与问题相关的信息。"
        
        context = "知识图谱上下文:\n"
        context += "\n".join(triples_text)
        
        return context
    
    def query(
        self,
        question: str,
        normalized_triples: List[Dict[str, Any]],
        max_context_triples: int = 50,
        verbose: bool = False
    ) -> str:
        """
        使用图谱RAG回答问题
        
        Args:
            question: 用户问题
            normalized_triples: 归一化的三元组列表
            max_context_triples: 最大上下文三元组数
            verbose: 是否打印详细信息
            
        Returns:
            回答
        """
        # 1. 从问题中提取实体
        query_entities = self._extract_entities_from_question(question, normalized_triples)
        
        if verbose:
            print(f"🔍 识别的问题实体: {list(query_entities)}")
        
        # 2. 从图谱中提取子图
        relevant_subgraph = self.kg.get_subgraph_by_entities(query_entities, max_depth=2)
        
        if verbose:
            print(f"📊 提取的子图: {relevant_subgraph.number_of_nodes()} 节点, "
                  f"{relevant_subgraph.number_of_edges()} 边")
        
        # 3. 构建上下文
        context_text = self._build_context_from_graph(query_entities, max_context_triples)
        
        if verbose:
            print(f"\n📝 上下文文本:\n{context_text[:500]}...")
        
        # 4. 生成回答
        prompt = f"""
你是一个专业的问答专家，擅长基于知识图谱回答问题。
请使用提供的知识图谱上下文来简洁地回答用户的问题。
如果上下文中不包含答案，请说"我不知道"。

问题: {question}

上下文:
{context_text}

简洁回答:
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            answer = response.choices[0].message.content.strip()
            return answer
        
        except Exception as e:
            return f"❌ 查询失败: {str(e)}"
    
    def query_with_related_entities(
        self,
        question: str,
        normalized_triples: List[Dict[str, Any]],
        max_hops: int = 2,
        max_context_triples: int = 50,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        使用相关实体增强的查询
        
        Args:
            question: 用户问题
            normalized_triples: 归一化的三元组列表
            max_hops: 最大跳数
            max_context_triples: 最大上下文三元组数
            verbose: 是否打印详细信息
            
        Returns:
            包含答案和元数据的字典
        """
        # 提取初始实体
        initial_entities = self._extract_entities_from_question(question, normalized_triples)
        
        # 扩展相关实体
        all_entities = set(initial_entities)
        for entity in initial_entities:
            related = self.kg.find_related_entities(entity, max_hops=max_hops)
            for rel in related:
                all_entities.add(rel['entity'])
        
        if verbose:
            print(f"🔍 初始实体: {list(initial_entities)}")
            print(f"🔗 扩展后的实体: {len(all_entities)} 个")
        
        # 构建上下文
        context_text = self._build_context_from_graph(all_entities, max_context_triples)
        
        # 生成回答
        prompt = f"""
你是一个专业的问答专家，擅长基于知识图谱回答问题。
请使用提供的知识图谱上下文来简洁地回答用户的问题。
如果上下文中不包含答案，请说"我不知道"。

问题: {question}

上下文:
{context_text}

简洁回答:
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            answer = response.choices[0].message.content.strip()
            
            return {
                'answer': answer,
                'entities_used': list(all_entities),
                'context_triples_count': len(context_text.split('\n')) - 1,
                'initial_entities': list(initial_entities)
            }
        
        except Exception as e:
            return {
                'answer': f"❌ 查询失败: {str(e)}",
                'entities_used': [],
                'context_triples_count': 0,
                'initial_entities': []
            }


def test_kg_rag():
    """测试图谱RAG"""
    print("🧪 测试基于图谱的RAG")
    print("=" * 60)
    
    # 创建测试数据
    test_triples = [
        {'subject': 'marie curie', 'predicate': 'discovered', 'object': 'radium'},
        {'subject': 'marie curie', 'predicate': 'won', 'object': 'nobel prize in physics'},
        {'subject': 'marie curie', 'predicate': 'won', 'object': 'nobel prize in chemistry'},
        {'subject': 'marie curie', 'predicate': 'married', 'object': 'pierre curie'},
        {'subject': 'pierre curie', 'predicate': 'had children', 'object': 'irene curie'},
        {'subject': 'pierre curie', 'predicate': 'had children', 'object': 'eve curie'},
        {'subject': 'marie curie', 'predicate': 'was born', 'object': '1867'},
        {'subject': 'marie curie', 'predicate': 'died', 'object': '1934'},
    ]
    
    # 构建图谱
    from pr_kg_builder import KnowledgeGraphBuilder
    kg = KnowledgeGraphBuilder()
    kg.add_triples(test_triples)
    print(f"✅ 图谱构建完成: {kg.get_statistics()['nodes']} 节点, {kg.get_statistics()['edges']} 边")
    
    # 创建RAG系统
    try:
        rag = KnowledgeGraphRAG(kg, verbose=True)
        
        # 测试查询
        questions = [
            "玛丽·居里在哪两个领域获得了诺贝尔奖？",
            "皮埃尔·居里的孩子是谁？",
            "玛丽·居里去世时多少岁？"
        ]
        
        print("\n" + "=" * 60)
        for q in questions:
            print(f"\n❓ 问题: {q}")
            answer = rag.query(q, test_triples, verbose=False)
            print(f"✅ 回答: {answer}")
            print("-" * 60)
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("   提示: 请设置 OPENROUTER_API_KEY 或 OPENAI_API_KEY 环境变量")


if __name__ == "__main__":
    test_kg_rag()

