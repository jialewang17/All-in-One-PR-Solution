#!/usr/bin/env python3
"""
品牌传播方法论规则库
支持规则的导入、管理、匹配和应用
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pr_neo4j_env import graph, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE


class MethodologyRule:
    """方法论规则类"""
    
    def __init__(self, rule_data: Dict[str, Any]):
        self.rule_id = rule_data.get('rule_id', '')
        self.rule_type = rule_data.get('rule_type', '')  # general, industry, brand_specific
        self.name = rule_data.get('name', '')
        self.description = rule_data.get('description', '')
        self.conditions = rule_data.get('conditions', {})  # 应用条件
        self.application_scenarios = rule_data.get('application_scenarios', [])
        self.priority = rule_data.get('priority', 0)  # 优先级，数字越大优先级越高
        self.effects = rule_data.get('effects', {})  # 规则效果
        self.content = rule_data.get('content', '')  # 规则内容
        self.version = rule_data.get('version', '1.0')
        self.created_at = rule_data.get('created_at', datetime.now().isoformat())
        self.updated_at = rule_data.get('updated_at', datetime.now().isoformat())
    
    def matches(self, context: Dict[str, Any]) -> bool:
        """检查规则是否匹配给定上下文"""
        # 检查行业匹配
        if 'industry' in self.conditions:
            context_industry = context.get('industry', '')
            rule_industry = self.conditions.get('industry', '')
            if rule_industry and context_industry != rule_industry:
                return False
        
        # 检查品牌匹配
        if 'brand' in self.conditions:
            context_brand = context.get('brand', '')
            rule_brand = self.conditions.get('brand', '')
            if rule_brand and context_brand != rule_brand:
                return False
        
        # 检查目标匹配
        if 'pr_goal' in self.conditions:
            context_goal = context.get('pr_goal', '')
            rule_goals = self.conditions.get('pr_goal', [])
            if rule_goals and context_goal not in rule_goals:
                return False
        
        # 检查应用场景匹配
        if self.application_scenarios:
            context_scenario = context.get('scenario', '')
            if context_scenario not in self.application_scenarios:
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'rule_id': self.rule_id,
            'rule_type': self.rule_type,
            'name': self.name,
            'description': self.description,
            'conditions': self.conditions,
            'application_scenarios': self.application_scenarios,
            'priority': self.priority,
            'effects': self.effects,
            'content': self.content,
            'version': self.version,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class MethodologyRulesManager:
    """方法论规则管理器"""
    
    def __init__(self):
        """初始化规则管理器"""
        self.graph = graph
        self.rules_cache = {}  # 规则缓存
    
    def import_rules_from_json(self, json_path: str) -> Dict[str, Any]:
        """从JSON文件导入规则"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            
            if isinstance(rules_data, list):
                rules = rules_data
            elif isinstance(rules_data, dict) and 'rules' in rules_data:
                rules = rules_data['rules']
            else:
                rules = [rules_data]
            
            results = {
                'total': len(rules),
                'imported': 0,
                'updated': 0,
                'errors': []
            }
            
            for rule_data in rules:
                try:
                    result = self.add_or_update_rule(rule_data)
                    if result['created']:
                        results['imported'] += 1
                    else:
                        results['updated'] += 1
                except Exception as e:
                    results['errors'].append({
                        'rule': rule_data.get('name', 'Unknown'),
                        'error': str(e)
                    })
            
            return results
        except Exception as e:
            return {'error': f"导入失败: {e}"}
    
    def add_or_update_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """添加或更新规则"""
        if not self.graph:
            return {'error': 'Neo4j连接不可用'}
        
        rule_id = rule_data.get('rule_id') or rule_data.get('name', '')
        if not rule_id:
            return {'error': '规则ID或名称不能为空'}
        
        try:
            # 检查规则是否已存在
            check_query = """
            MATCH (r:MethodologyRule {rule_id: $rule_id})
            RETURN r
            """
            existing = self.graph.query(check_query, params={'rule_id': rule_id})
            
            # 构建属性
            properties = {
                'rule_id': rule_id,
                'rule_type': rule_data.get('rule_type', 'general'),
                'name': rule_data.get('name', ''),
                'description': rule_data.get('description', ''),
                'conditions': json.dumps(rule_data.get('conditions', {}), ensure_ascii=False),
                'application_scenarios': json.dumps(rule_data.get('application_scenarios', []), ensure_ascii=False),
                'priority': rule_data.get('priority', 0),
                'effects': json.dumps(rule_data.get('effects', {}), ensure_ascii=False),
                'content': rule_data.get('content', ''),
                'version': rule_data.get('version', '1.0'),
                'updated_at': datetime.now().isoformat()
            }
            
            # 移除空值
            properties = {k: v for k, v in properties.items() if v is not None and v != ''}
            
            if existing:
                # 更新现有规则
                update_query = """
                MATCH (r:MethodologyRule {rule_id: $rule_id})
                SET r += $properties
                RETURN r
                """
                self.graph.query(update_query, params={'rule_id': rule_id, 'properties': properties})
                return {'created': False, 'rule_id': rule_id, 'action': 'updated'}
            else:
                # 创建新规则
                properties['created_at'] = datetime.now().isoformat()
                create_query = """
                CREATE (r:MethodologyRule $properties)
                RETURN r
                """
                self.graph.query(create_query, params={'properties': properties})
                
                # 创建规则与实体的关系
                self._link_rule_to_entities(rule_id, rule_data.get('conditions', {}))
                
                return {'created': True, 'rule_id': rule_id, 'action': 'created'}
                
        except Exception as e:
            return {'error': f"操作失败: {e}"}
    
    def _link_rule_to_entities(self, rule_id: str, conditions: Dict[str, Any]):
        """将规则链接到相关实体"""
        if not self.graph:
            return
        
        try:
            # 链接到品牌
            if 'brand' in conditions:
                brand_name = conditions['brand']
                query = """
                MATCH (r:MethodologyRule {rule_id: $rule_id})
                MATCH (b:Brand {name: $brand_name})
                MERGE (r)-[rel:APPLIES_TO]->(b)
                SET rel.priority = $priority
                """
                self.graph.query(query, params={
                    'rule_id': rule_id,
                    'brand_name': brand_name,
                    'priority': conditions.get('priority', 0)
                })
            
            # 链接到行业
            if 'industry' in conditions:
                industry = conditions['industry']
                query = """
                MATCH (r:MethodologyRule {rule_id: $rule_id})
                MERGE (i:Industry {name: $industry})
                MERGE (r)-[rel:APPLIES_TO]->(i)
                SET rel.priority = $priority
                """
                self.graph.query(query, params={
                    'rule_id': rule_id,
                    'industry': industry,
                    'priority': conditions.get('priority', 0)
                })
        except Exception as e:
            print(f"链接规则到实体失败: {e}")
    
    def get_applicable_rules(self, context: Dict[str, Any]) -> List[MethodologyRule]:
        """获取适用于给定上下文的规则"""
        if not self.graph:
            return []
        
        try:
            # 构建查询条件
            query_parts = []
            params = {}
            
            if context.get('brand'):
                query_parts.append("""
                MATCH (r:MethodologyRule)-[:APPLIES_TO]->(b:Brand {name: $brand})
                """)
                params['brand'] = context['brand']
            elif context.get('industry'):
                query_parts.append("""
                MATCH (r:MethodologyRule)-[:APPLIES_TO]->(i:Industry {name: $industry})
                """)
                params['industry'] = context['industry']
            else:
                query_parts.append("""
                MATCH (r:MethodologyRule)
                """)
            
            query = "".join(query_parts) + """
            WHERE r.rule_type IN ['general', $rule_type]
            RETURN r
            ORDER BY r.priority DESC
            LIMIT 50
            """
            params['rule_type'] = context.get('rule_type', 'general')
            
            results = self.graph.query(query, params=params)
            
            # 转换为规则对象并过滤
            rules = []
            for result in results:
                rule_data = dict(result['r'])
                # 解析JSON字段
                if 'conditions' in rule_data and isinstance(rule_data['conditions'], str):
                    rule_data['conditions'] = json.loads(rule_data['conditions'])
                if 'application_scenarios' in rule_data and isinstance(rule_data['application_scenarios'], str):
                    rule_data['application_scenarios'] = json.loads(rule_data['application_scenarios'])
                if 'effects' in rule_data and isinstance(rule_data['effects'], str):
                    rule_data['effects'] = json.loads(rule_data['effects'])
                
                rule = MethodologyRule(rule_data)
                if rule.matches(context):
                    rules.append(rule)
            
            # 按优先级排序
            rules.sort(key=lambda x: x.priority, reverse=True)
            return rules
        except Exception as e:
            print(f"获取适用规则失败: {e}")
            return []
    
    def resolve_rule_conflicts(self, rules: List[MethodologyRule]) -> List[MethodologyRule]:
        """解决规则冲突"""
        if len(rules) <= 1:
            return rules
        
        # 按优先级排序
        rules.sort(key=lambda x: x.priority, reverse=True)
        
        # 检查冲突
        resolved_rules = []
        for rule in rules:
            # 检查是否与已选择的规则冲突
            conflict = False
            for selected_rule in resolved_rules:
                # 简单的冲突检测：相同类型的规则
                if rule.rule_type == selected_rule.rule_type and rule.rule_type != 'general':
                    # 检查是否有明确的冲突标记
                    if rule.effects.get('conflicts_with') == selected_rule.rule_id:
                        conflict = True
                        break
            
            if not conflict:
                resolved_rules.append(rule)
        
        return resolved_rules
    
    def get_rule(self, rule_id: str) -> Optional[MethodologyRule]:
        """获取规则"""
        if not self.graph:
            return None
        
        try:
            query = """
            MATCH (r:MethodologyRule {rule_id: $rule_id})
            RETURN r
            """
            results = self.graph.query(query, params={'rule_id': rule_id})
            
            if results:
                rule_data = dict(results[0]['r'])
                # 解析JSON字段
                if 'conditions' in rule_data and isinstance(rule_data['conditions'], str):
                    rule_data['conditions'] = json.loads(rule_data['conditions'])
                if 'application_scenarios' in rule_data and isinstance(rule_data['application_scenarios'], str):
                    rule_data['application_scenarios'] = json.loads(rule_data['application_scenarios'])
                if 'effects' in rule_data and isinstance(rule_data['effects'], str):
                    rule_data['effects'] = json.loads(rule_data['effects'])
                
                return MethodologyRule(rule_data)
            return None
        except Exception as e:
            print(f"获取规则失败: {e}")
            return None
    
    def apply_rules_to_prompt(self, rules: List[MethodologyRule], base_prompt: str) -> str:
        """将规则应用到提示词"""
        if not rules:
            return base_prompt
        
        rules_text = "\n\n## 应用的方法论规则:\n\n"
        for i, rule in enumerate(rules, 1):
            rules_text += f"{i}. **{rule.name}** (优先级: {rule.priority})\n"
            rules_text += f"   - 描述: {rule.description}\n"
            rules_text += f"   - 内容: {rule.content}\n"
            if rule.effects:
                rules_text += f"   - 效果: {json.dumps(rule.effects, ensure_ascii=False)}\n"
            rules_text += "\n"
        
        return base_prompt + rules_text


def test_methodology_rules_manager():
    """测试方法论规则管理器"""
    manager = MethodologyRulesManager()
    
    # 测试规则
    test_rule = {
        'rule_id': 'test_rule_001',
        'rule_type': 'industry',
        'name': '科技品牌传播规则',
        'description': '适用于科技行业的品牌传播规则',
        'conditions': {
            'industry': '科技',
            'pr_goal': ['品牌认知', '用户增长']
        },
        'application_scenarios': ['brand_awareness', 'user_growth'],
        'priority': 10,
        'effects': {
            'emphasis': '创新、技术、用户体验'
        },
        'content': '科技品牌应强调创新能力和技术优势，注重用户体验和产品差异化。'
    }
    
    # 测试添加规则
    print("测试添加规则...")
    result = manager.add_or_update_rule(test_rule)
    print(f"结果: {result}")
    
    # 测试获取适用规则
    print("\n测试获取适用规则...")
    context = {
        'industry': '科技',
        'pr_goal': '品牌认知',
        'scenario': 'brand_awareness'
    }
    rules = manager.get_applicable_rules(context)
    print(f"适用规则数量: {len(rules)}")
    for rule in rules:
        print(f"  - {rule.name} (优先级: {rule.priority})")


if __name__ == "__main__":
    test_methodology_rules_manager()



