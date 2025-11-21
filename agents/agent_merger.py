#!/usr/bin/env python3
"""
智能体合并分析工具
分析两个智能体的流程并自动合并
"""

import json
import os
import yaml
from typing import Dict, List, Any, Tuple
from pathlib import Path
import ast
import inspect

class AgentMerger:
    """智能体合并器"""
    
    def __init__(self):
        self.agent1_config = None
        self.agent2_config = None
        self.merged_config = None
        
    def analyze_agent_flow(self, agent_code: str) -> Dict[str, Any]:
        """分析智能体的流程"""
        try:
            # 解析代码
            tree = ast.parse(agent_code)
            
            flow_analysis = {
                'imports': [],
                'classes': [],
                'functions': [],
                'variables': [],
                'workflow_steps': [],
                'dependencies': [],
                'config_parameters': []
            }
            
            # 分析AST节点
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        flow_analysis['imports'].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        flow_analysis['imports'].append(f"{module}.{alias.name}")
                elif isinstance(node, ast.ClassDef):
                    flow_analysis['classes'].append({
                        'name': node.name,
                        'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                        'base_classes': [base.id for base in node.bases if isinstance(base, ast.Name)]
                    })
                elif isinstance(node, ast.FunctionDef):
                    flow_analysis['functions'].append({
                        'name': node.name,
                        'args': [arg.arg for arg in node.args.args],
                        'decorators': [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
                    })
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            flow_analysis['variables'].append(target.id)
            
            return flow_analysis
            
        except Exception as e:
            return {'error': f"分析失败: {e}"}
    
    def extract_workflow_steps(self, agent_code: str) -> List[str]:
        """提取工作流程步骤"""
        workflow_steps = []
        
        # 查找常见的工作流程模式
        patterns = [
            r'def\s+(\w*step\w*)',
            r'def\s+(\w*process\w*)',
            r'def\s+(\w*execute\w*)',
            r'def\s+(\w*run\w*)',
            r'def\s+(\w*handle\w*)',
            r'def\s+(\w*analyze\w*)',
            r'def\s+(\w*generate\w*)',
            r'def\s+(\w*transform\w*)'
        ]
        
        import re
        for pattern in patterns:
            matches = re.findall(pattern, agent_code, re.IGNORECASE)
            workflow_steps.extend(matches)
        
        return list(set(workflow_steps))
    
    def detect_conflicts(self, agent1_analysis: Dict, agent2_analysis: Dict) -> List[Dict]:
        """检测两个智能体之间的冲突"""
        conflicts = []
        
        # 检查类名冲突
        agent1_classes = {cls['name'] for cls in agent1_analysis.get('classes', [])}
        agent2_classes = {cls['name'] for cls in agent2_analysis.get('classes', [])}
        class_conflicts = agent1_classes.intersection(agent2_classes)
        
        if class_conflicts:
            conflicts.append({
                'type': 'class_name_conflict',
                'conflicts': list(class_conflicts),
                'severity': 'high',
                'description': '存在同名的类定义'
            })
        
        # 检查函数名冲突
        agent1_functions = {func['name'] for func in agent1_analysis.get('functions', [])}
        agent2_functions = {func['name'] for func in agent2_analysis.get('functions', [])}
        function_conflicts = agent1_functions.intersection(agent2_functions)
        
        if function_conflicts:
            conflicts.append({
                'type': 'function_name_conflict',
                'conflicts': list(function_conflicts),
                'severity': 'medium',
                'description': '存在同名的函数定义'
            })
        
        # 检查变量名冲突
        agent1_variables = set(agent1_analysis.get('variables', []))
        agent2_variables = set(agent2_analysis.get('variables', []))
        variable_conflicts = agent1_variables.intersection(agent2_variables)
        
        if variable_conflicts:
            conflicts.append({
                'type': 'variable_name_conflict',
                'conflicts': list(variable_conflicts),
                'severity': 'low',
                'description': '存在同名的变量定义'
            })
        
        return conflicts
    
    def merge_agents(self, agent1_code: str, agent2_code: str, merge_strategy: str = 'unified') -> Dict[str, Any]:
        """合并两个智能体"""
        
        # 分析两个智能体
        agent1_analysis = self.analyze_agent_flow(agent1_code)
        agent2_analysis = self.analyze_agent_flow(agent2_code)
        
        # 检测冲突
        conflicts = self.detect_conflicts(agent1_analysis, agent2_analysis)
        
        # 生成合并方案
        merge_plan = self.generate_merge_plan(agent1_analysis, agent2_analysis, conflicts, merge_strategy)
        
        # 生成合并后的代码
        merged_code = self.generate_merged_code(agent1_code, agent2_code, merge_plan)
        
        return {
            'agent1_analysis': agent1_analysis,
            'agent2_analysis': agent2_analysis,
            'conflicts': conflicts,
            'merge_plan': merge_plan,
            'merged_code': merged_code,
            'summary': self.generate_summary(agent1_analysis, agent2_analysis, conflicts)
        }
    
    def generate_merge_plan(self, agent1_analysis: Dict, agent2_analysis: Dict, conflicts: List[Dict], strategy: str) -> Dict[str, Any]:
        """生成合并计划"""
        
        plan = {
            'strategy': strategy,
            'resolutions': [],
            'new_structure': {
                'imports': [],
                'classes': [],
                'functions': [],
                'workflow': []
            }
        }
        
        # 处理冲突
        for conflict in conflicts:
            if conflict['type'] == 'class_name_conflict':
                plan['resolutions'].append({
                    'conflict': conflict,
                    'resolution': 'rename_classes',
                    'action': f"将冲突的类重命名为 {conflict['conflicts'][0]}_Agent1 和 {conflict['conflicts'][0]}_Agent2"
                })
            elif conflict['type'] == 'function_name_conflict':
                plan['resolutions'].append({
                    'conflict': conflict,
                    'resolution': 'rename_functions',
                    'action': f"将冲突的函数重命名为 {conflict['conflicts'][0]}_agent1 和 {conflict['conflicts'][0]}_agent2"
                })
        
        # 合并导入
        plan['new_structure']['imports'] = list(set(
            agent1_analysis.get('imports', []) + 
            agent2_analysis.get('imports', [])
        ))
        
        # 合并类
        plan['new_structure']['classes'] = (
            agent1_analysis.get('classes', []) + 
            agent2_analysis.get('classes', [])
        )
        
        # 合并函数
        plan['new_structure']['functions'] = (
            agent1_analysis.get('functions', []) + 
            agent2_analysis.get('functions', [])
        )
        
        return plan
    
    def generate_merged_code(self, agent1_code: str, agent2_code: str, merge_plan: Dict) -> str:
        """生成合并后的代码"""
        
        merged_code = f'''#!/usr/bin/env python3
"""
合并后的智能体系统
由两个智能体自动合并生成
合并策略: {merge_plan['strategy']}
"""

# 合并的导入
{self.generate_imports_section(merge_plan['new_structure']['imports'])}

# 智能体1的代码
{self.add_namespace_prefix(agent1_code, 'Agent1')}

# 智能体2的代码  
{self.add_namespace_prefix(agent2_code, 'Agent2')}

# 合并后的统一接口
class MergedAgent:
    """合并后的智能体"""
    
    def __init__(self):
        self.agent1 = Agent1System()
        self.agent2 = Agent2System()
    
    def execute_workflow(self, input_data):
        """执行合并后的工作流程"""
        # 智能体1处理
        result1 = self.agent1.process(input_data)
        
        # 智能体2处理
        result2 = self.agent2.process(result1)
        
        return self.combine_results(result1, result2)
    
    def combine_results(self, result1, result2):
        """合并两个智能体的结果"""
        return {{
            'agent1_result': result1,
            'agent2_result': result2,
            'merged_result': self.merge_logic(result1, result2)
        }}
    
    def merge_logic(self, result1, result2):
        """自定义合并逻辑"""
        # 在这里实现您的合并逻辑
        pass
'''
        
        return merged_code
    
    def add_namespace_prefix(self, code: str, prefix: str) -> str:
        """为代码添加命名空间前缀"""
        # 简单的命名空间处理
        lines = code.split('\n')
        prefixed_lines = []
        
        for line in lines:
            if line.strip().startswith('class '):
                class_name = line.split()[1].split('(')[0]
                prefixed_line = line.replace(f'class {class_name}', f'class {prefix}_{class_name}')
                prefixed_lines.append(prefixed_line)
            elif line.strip().startswith('def ') and not line.strip().startswith('def __'):
                func_name = line.split()[1].split('(')[0]
                prefixed_line = line.replace(f'def {func_name}', f'def {prefix}_{func_name}')
                prefixed_lines.append(prefixed_line)
            else:
                prefixed_lines.append(line)
        
        return '\n'.join(prefixed_lines)
    
    def generate_imports_section(self, imports: List[str]) -> str:
        """生成导入部分"""
        if not imports:
            return "# 无额外导入"
        
        import_section = "# 合并的导入\n"
        for imp in sorted(imports):
            import_section += f"import {imp}\n"
        
        return import_section
    
    def generate_summary(self, agent1_analysis: Dict, agent2_analysis: Dict, conflicts: List[Dict]) -> str:
        """生成合并摘要"""
        summary = f"""
## 智能体合并摘要

### 智能体1分析
- 类数量: {len(agent1_analysis.get('classes', []))}
- 函数数量: {len(agent1_analysis.get('functions', []))}
- 变量数量: {len(agent1_analysis.get('variables', []))}

### 智能体2分析  
- 类数量: {len(agent2_analysis.get('classes', []))}
- 函数数量: {len(agent2_analysis.get('functions', []))}
- 变量数量: {len(agent2_analysis.get('variables', []))}

### 冲突检测
- 发现冲突数量: {len(conflicts)}
- 高严重性冲突: {len([c for c in conflicts if c['severity'] == 'high'])}
- 中严重性冲突: {len([c for c in conflicts if c['severity'] == 'medium'])}
- 低严重性冲突: {len([c for c in conflicts if c['severity'] == 'low'])}

### 合并建议
"""
        
        if conflicts:
            summary += "- 需要解决命名冲突\n"
            summary += "- 建议使用命名空间隔离\n"
            summary += "- 需要统一接口设计\n"
        else:
            summary += "- 无冲突，可以直接合并\n"
            summary += "- 建议保持原有结构\n"
        
        return summary

def main():
    """主函数"""
    print("🤖 智能体合并分析工具")
    print("=" * 50)
    
    merger = AgentMerger()
    
    # 示例：分析现有的RAG系统组件
    print("📊 分析现有系统组件...")
    
    # 读取RAG系统代码（使用 v1.1）
    try:
        # 优先使用 v1.1
        rag_file = 'pr_rag_system_v1_1.py'
        rag_core_file = 'core/querying/pipelines/qa_pipeline.py'
        
        if not os.path.exists(rag_file):
            print(f"⚠️ {rag_file} 不存在，跳过分析")
            return
        
        with open(rag_file, 'r', encoding='utf-8') as f:
            rag_system_code = f.read()
        
        if os.path.exists(rag_core_file):
            with open(rag_core_file, 'r', encoding='utf-8') as f:
                enhanced_rag_code = f.read()
        else:
            print(f"⚠️ {rag_core_file} 不存在，跳过增强RAG分析")
            enhanced_rag_code = ""
        
        print("✅ 成功读取系统代码")
        
        # 分析流程
        rag_analysis = merger.analyze_agent_flow(rag_system_code)
        enhanced_analysis = merger.analyze_agent_flow(enhanced_rag_code)
        
        print(f"📈 RAG系统分析结果:")
        print(f"  - 类数量: {len(rag_analysis.get('classes', []))}")
        print(f"  - 函数数量: {len(rag_analysis.get('functions', []))}")
        
        print(f"📈 增强RAG分析结果:")
        print(f"  - 类数量: {len(enhanced_analysis.get('classes', []))}")
        print(f"  - 函数数量: {len(enhanced_analysis.get('functions', []))}")
        
        # 检测冲突
        conflicts = merger.detect_conflicts(rag_analysis, enhanced_analysis)
        print(f"⚠️ 发现冲突: {len(conflicts)}个")
        
        for conflict in conflicts:
            print(f"  - {conflict['type']}: {conflict['description']}")
        
        print("\n🎯 建议:")
        if conflicts:
            print("1. 使用命名空间隔离不同组件")
            print("2. 统一接口设计")
            print("3. 解决命名冲突")
        else:
            print("1. 可以直接合并")
            print("2. 保持原有结构")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

if __name__ == "__main__":
    main()

