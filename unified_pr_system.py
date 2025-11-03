#!/usr/bin/env python3
"""
合并后的统一公关传播智能体系统
整合 pr_agent_v2 和 pr_rag_system_v1
"""

import os
import json
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import yaml

# 导入现有RAG系统组件
import sys
sys.path.append('core')
from pr_enhanced_rag import EnhancedPRRAGSystem
from pr_entity_extractor import EntityRelationshipExtractor
from pr_neo4j_env import *

# 导入pr_agent_v2组件
sys.path.append('pr_agent_v2')
from pr_marketing_agent_v3 import GraphRAG, llm_complete
from templates.prompts import (
    A_GRAPHIC_BRIEF, B_VIDEO_SCRIPT, C_CAMPAIGN_PLAN,
    D_SHORTVIDEO_SCRIPT, E_XHS_NOTE, F_CRISIS_PLAN
)

class UnifiedPRSystem:
    """统一的公关传播智能体系统"""
    
    def __init__(self, config_path: str = "unified_config.yaml"):
        """初始化统一系统"""
        self.config = self.load_config(config_path)
        self.rag_system = None
        self.graph_rag = None
        self.entity_extractor = None
        self.llm_config = self.config.get('llm', {})
        
        # 初始化组件
        self._init_components()
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            # 创建默认配置
            return self.create_default_config(config_path)
    
    def create_default_config(self, config_path: str) -> Dict[str, Any]:
        """创建默认配置"""
        default_config = {
            'llm': {
                'provider': 'openai',
                'model': 'gpt-3.5-turbo',
                'max_tokens': 2048,
                'temperature': 0.6
            },
            'neo4j': {
                'uri': os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687'),
                'user': os.getenv('NEO4J_USERNAME', 'neo4j'),
                'password': os.getenv('NEO4J_PASSWORD', 'bjtu1234'),
                'database': os.getenv('NEO4J_DATABASE', 'neo4j')
            },
            'vector_store': {
                'persist_dir': './vector_store/chroma_db',
                'collection_name': 'pr_unified'
            },
            'retrieval': {
                'top_k': 10,
                'max_context_chars': 16000
            },
            'paths': {
                'output_dir': './outputs',
                'data_dir': './data'
            }
        }
        
        # 保存默认配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
        
        return default_config
    
    def _init_components(self):
        """初始化各个组件"""
        try:
            # 初始化增强RAG系统
            self.rag_system = EnhancedPRRAGSystem()
            print("✅ 增强RAG系统初始化成功")
            
            # 初始化实体提取器
            self.entity_extractor = EntityRelationshipExtractor()
            print("✅ 实体提取器初始化成功")
            
            # 初始化图RAG（pr_agent_v2的组件）
            neo4j_config = self.config['neo4j']
            vector_config = self.config['vector_store']
            
            self.graph_rag = GraphRAG(
                persist_dir=vector_config['persist_dir'],
                neo4j_uri=neo4j_config['uri'],
                neo4j_user=neo4j_config['user'],
                neo4j_pwd=neo4j_config['password'],
                top_k=self.config['retrieval']['top_k']
            )
            print("✅ 图RAG系统初始化成功")
            
        except Exception as e:
            print(f"⚠️ 组件初始化警告: {e}")
    
    def query_knowledge(self, query: str, use_graph: bool = True) -> str:
        """知识查询功能（来自现有RAG系统）"""
        try:
            if use_graph:
                return self.rag_system.query(query, use_graph=True)
            else:
                return self.rag_system.query(query, use_graph=False)
        except Exception as e:
            return f"查询失败: {e}"
    
    def generate_pr_plan(self, enterprise_info: Dict[str, Any], output_types: List[str] = None) -> Dict[str, Any]:
        """生成公关传播方案（来自pr_agent_v2）"""
        if output_types is None:
            output_types = ["A", "B", "C", "D", "E", "F"]
        
        try:
            # 构建查询
            query = f"{enterprise_info.get('enterprise_stage', '')} {enterprise_info.get('industry', '')} {enterprise_info.get('market_type', '')} 目标:{enterprise_info.get('pr_goal', '')} 创新:{enterprise_info.get('innovation', '')}"
            
            # 检索知识
            vec_hits = self.graph_rag.retrieve(query, k=self.config['retrieval']['top_k'])
            graph_data = self.graph_rag.fetch_graph(enterprise_info.get('pr_goal', ''))
            
            # 构建上下文
            context_parts = []
            for i, hit in enumerate(vec_hits, 1):
                src = hit["meta"].get("source", "") if isinstance(hit["meta"], dict) else ""
                context_parts.append(f"[{i}] {hit['text'][:800]}\n— 来源：{src}")
            
            graph_part = f"策略: {graph_data.get('strategies', [])}\n渠道: {graph_data.get('channels', [])}\n案例: {graph_data.get('cases', [])}\n人群: {graph_data.get('personas', [])}"
            context = "\n\n".join(context_parts + [graph_part])[:self.config['retrieval']['max_context_chars']]
            
            # 企业信息JSON
            vars_text = json.dumps(enterprise_info, ensure_ascii=False)
            
            # 生成方案
            results = {}
            provider = self.llm_config['provider']
            model = self.llm_config['model']
            max_tokens = self.llm_config['max_tokens']
            temperature = self.llm_config['temperature']
            
            if "A" in output_types:
                results["A"] = llm_complete(provider, model, A_GRAPHIC_BRIEF.format(context=context, vars=vars_text), max_tokens, temperature)
            
            if "B" in output_types:
                results["B"] = llm_complete(provider, model, B_VIDEO_SCRIPT.format(context=context, vars=vars_text), max_tokens, temperature)
            
            if "C" in output_types:
                results["C"] = llm_complete(provider, model, C_CAMPAIGN_PLAN.format(context=context, vars=vars_text), max_tokens, temperature)
            
            if "D" in output_types:
                results["D"] = llm_complete(provider, model, D_SHORTVIDEO_SCRIPT.format(context=context, vars=vars_text), max_tokens, temperature)
            
            if "E" in output_types:
                results["E"] = llm_complete(provider, model, E_XHS_NOTE.format(context=context, vars=vars_text), max_tokens, temperature)
            
            if "F" in output_types:
                results["F"] = llm_complete(provider, model, F_CRISIS_PLAN.format(context=context, vars=vars_text), max_tokens, temperature)
            
            return results
            
        except Exception as e:
            return {"error": f"方案生成失败: {e}"}
    
    def analyze_entities(self, text: str) -> Dict[str, Any]:
        """实体分析功能"""
        try:
            entities = self.entity_extractor.extract_entities(text)
            relationships = self.entity_extractor.extract_relationships(text)
            
            return {
                "entities": entities,
                "relationships": relationships,
                "analysis_summary": f"识别到 {len(entities)} 个实体和 {len(relationships)} 个关系"
            }
        except Exception as e:
            return {"error": f"实体分析失败: {e}"}
    
    def unified_query(self, query: str, mode: str = "auto") -> Dict[str, Any]:
        """统一查询接口"""
        try:
            # 自动判断查询类型
            if mode == "auto":
                if any(keyword in query for keyword in ["方案", "策划", "计划", "生成"]):
                    mode = "plan_generation"
                elif any(keyword in query for keyword in ["实体", "关系", "分析"]):
                    mode = "entity_analysis"
                else:
                    mode = "knowledge_query"
            
            result = {
                "query": query,
                "mode": mode,
                "timestamp": datetime.now().isoformat(),
                "result": None
            }
            
            if mode == "knowledge_query":
                result["result"] = self.query_knowledge(query)
            elif mode == "entity_analysis":
                result["result"] = self.analyze_entities(query)
            elif mode == "plan_generation":
                # 这里需要解析查询中的企业信息
                enterprise_info = self._parse_enterprise_info(query)
                result["result"] = self.generate_pr_plan(enterprise_info)
            
            return result
            
        except Exception as e:
            return {
                "query": query,
                "mode": mode,
                "error": f"统一查询失败: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _parse_enterprise_info(self, query: str) -> Dict[str, Any]:
        """从查询中解析企业信息"""
        # 简单的解析逻辑，实际应用中可以使用更复杂的NLP
        enterprise_info = {
            "enterprise_name": "示例企业",
            "enterprise_stage": "中小微企业",
            "industry": "科技",
            "market_type": "ToC",
            "pr_goal": "品牌认知",
            "pr_cycle": "3个月",
            "pr_budget": "100万",
            "innovation": "适度创新"
        }
        
        # 尝试从查询中提取信息
        if "初创" in query:
            enterprise_info["enterprise_stage"] = "初创企业"
        elif "大型" in query:
            enterprise_info["enterprise_stage"] = "大型国企央企"
        
        if "ToB" in query:
            enterprise_info["market_type"] = "ToB"
        elif "ToG" in query:
            enterprise_info["market_type"] = "ToG"
        
        return enterprise_info
    
    def close(self):
        """关闭系统"""
        if self.graph_rag:
            self.graph_rag.close()
        print("✅ 系统已关闭")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="统一公关传播智能体系统")
    parser.add_argument("--mode", choices=["query", "generate", "analyze"], default="query", help="运行模式")
    parser.add_argument("--query", type=str, help="查询内容")
    parser.add_argument("--config", type=str, default="unified_config.yaml", help="配置文件路径")
    
    args = parser.parse_args()
    
    print("🤖 统一公关传播智能体系统")
    print("=" * 50)
    
    # 初始化系统
    system = UnifiedPRSystem(args.config)
    
    try:
        if args.mode == "query" and args.query:
            print(f"🔍 执行知识查询: {args.query}")
            result = system.unified_query(args.query, "knowledge_query")
            print(f"📝 查询结果:\n{result['result']}")
        
        elif args.mode == "generate":
            print("📋 生成公关传播方案")
            enterprise_info = {
                "enterprise_name": "小米汽车",
                "enterprise_stage": "大型企业",
                "industry": "汽车",
                "market_type": "ToC",
                "pr_goal": "品牌认知",
                "pr_cycle": "6个月",
                "pr_budget": "500万",
                "innovation": "适度创新"
            }
            result = system.generate_pr_plan(enterprise_info, ["A", "B", "C"])
            print("📄 生成的方案:")
            for plan_type, content in result.items():
                print(f"\n{plan_type} 方案:\n{content[:500]}...")
        
        elif args.mode == "analyze" and args.query:
            print(f"🔬 执行实体分析: {args.query}")
            result = system.unified_query(args.query, "entity_analysis")
            print(f"📊 分析结果:\n{result['result']}")
        
        else:
            print("❌ 请提供有效的参数")
            print("示例:")
            print("  python unified_pr_system.py --mode query --query '小米汽车如何做好用户运营？'")
            print("  python unified_pr_system.py --mode generate")
            print("  python unified_pr_system.py --mode analyze --query '分析这个品牌案例'")
    
    finally:
        system.close()

if __name__ == "__main__":
    main()
