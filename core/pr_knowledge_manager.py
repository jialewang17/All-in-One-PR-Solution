#!/usr/bin/env python3
"""
品牌知识管理系统
支持品牌列表的导入、管理、查询和存储
"""

import json
import csv
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from pr_neo4j_env import graph, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE


class BrandKnowledgeManager:
    """品牌知识管理器"""
    
    def __init__(self):
        """初始化品牌知识管理器"""
        self.graph = graph
        self.brand_cache = {}  # 品牌缓存
        
    def import_brands_from_json(self, json_path: str) -> Dict[str, Any]:
        """从JSON文件导入品牌列表"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                brands_data = json.load(f)
            
            if isinstance(brands_data, list):
                brands = brands_data
            elif isinstance(brands_data, dict) and 'brands' in brands_data:
                brands = brands_data['brands']
            else:
                brands = [brands_data]
            
            results = {
                'total': len(brands),
                'imported': 0,
                'updated': 0,
                'errors': []
            }
            
            for brand_data in brands:
                try:
                    result = self.add_or_update_brand(brand_data)
                    if result['created']:
                        results['imported'] += 1
                    else:
                        results['updated'] += 1
                except Exception as e:
                    results['errors'].append({
                        'brand': brand_data.get('name', 'Unknown'),
                        'error': str(e)
                    })
            
            return results
        except Exception as e:
            return {'error': f"导入失败: {e}"}
    
    def import_brands_from_csv(self, csv_path: str) -> Dict[str, Any]:
        """从CSV文件导入品牌列表"""
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
            brands = df.to_dict('records')
            
            results = {
                'total': len(brands),
                'imported': 0,
                'updated': 0,
                'errors': []
            }
            
            for brand_data in brands:
                try:
                    # 清理数据，移除NaN值
                    brand_data = {k: v for k, v in brand_data.items() if pd.notna(v)}
                    result = self.add_or_update_brand(brand_data)
                    if result['created']:
                        results['imported'] += 1
                    else:
                        results['updated'] += 1
                except Exception as e:
                    results['errors'].append({
                        'brand': brand_data.get('name', 'Unknown'),
                        'error': str(e)
                    })
            
            return results
        except Exception as e:
            return {'error': f"导入失败: {e}"}
    
    def import_brands_from_excel(self, excel_path: str, sheet_name: str = 0) -> Dict[str, Any]:
        """从Excel文件导入品牌列表"""
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            brands = df.to_dict('records')
            
            results = {
                'total': len(brands),
                'imported': 0,
                'updated': 0,
                'errors': []
            }
            
            for brand_data in brands:
                try:
                    # 清理数据
                    brand_data = {k: v for k, v in brand_data.items() if pd.notna(v)}
                    result = self.add_or_update_brand(brand_data)
                    if result['created']:
                        results['imported'] += 1
                    else:
                        results['updated'] += 1
                except Exception as e:
                    results['errors'].append({
                        'brand': brand_data.get('name', 'Unknown'),
                        'error': str(e)
                    })
            
            return results
        except Exception as e:
            return {'error': f"导入失败: {e}"}
    
    def add_or_update_brand(self, brand_data: Dict[str, Any]) -> Dict[str, Any]:
        """添加或更新品牌信息"""
        if not self.graph:
            return {'error': 'Neo4j连接不可用'}
        
        name = brand_data.get('name')
        if not name:
            return {'error': '品牌名称不能为空'}
        
        try:
            # 检查品牌是否已存在
            check_query = """
            MATCH (b:Brand {name: $name})
            RETURN b
            """
            existing = self.graph.query(check_query, params={'name': name})
            
            # 构建属性
            properties = {
                'name': name,
                'industry': brand_data.get('industry', ''),
                'brand_positioning': brand_data.get('brand_positioning', ''),
                'brand_personality': brand_data.get('brand_personality', ''),
                'target_audience': brand_data.get('target_audience', ''),
                'founded_year': brand_data.get('founded_year', ''),
                'brand_value': brand_data.get('brand_value', ''),
                'characteristics': brand_data.get('characteristics', ''),
                'history': brand_data.get('history', ''),
                'updated_at': datetime.now().isoformat()
            }
            
            # 移除空值
            properties = {k: v for k, v in properties.items() if v}
            
            if existing:
                # 更新现有品牌
                update_query = """
                MATCH (b:Brand {name: $name})
                SET b += $properties
                RETURN b
                """
                self.graph.query(update_query, params={'name': name, 'properties': properties})
                return {'created': False, 'brand': name, 'action': 'updated'}
            else:
                # 创建新品牌
                create_query = """
                CREATE (b:Brand $properties)
                RETURN b
                """
                self.graph.query(create_query, params={'properties': properties})
                return {'created': True, 'brand': name, 'action': 'created'}
                
        except Exception as e:
            return {'error': f"操作失败: {e}"}
    
    def get_brand(self, brand_name: str) -> Optional[Dict[str, Any]]:
        """查询品牌信息"""
        if not self.graph:
            return None
        
        try:
            query = """
            MATCH (b:Brand {name: $name})
            OPTIONAL MATCH (b)-[r]->(related)
            RETURN b, collect({
                relationship: type(r),
                related: properties(related),
                related_type: labels(related)[0]
            }) as relationships
            """
            results = self.graph.query(query, params={'name': brand_name})
            
            if results:
                brand_node = results[0]['b']
                relationships = results[0]['relationships']
                return {
                    'brand': dict(brand_node),
                    'relationships': relationships
                }
            return None
        except Exception as e:
            print(f"查询品牌失败: {e}")
            return None
    
    def search_brands(self, keyword: str, industry: Optional[str] = None) -> List[Dict[str, Any]]:
        """搜索品牌"""
        if not self.graph:
            return []
        
        try:
            if industry:
                query = """
                MATCH (b:Brand)
                WHERE b.name CONTAINS $keyword AND b.industry = $industry
                RETURN b
                LIMIT 50
                """
                params = {'keyword': keyword, 'industry': industry}
            else:
                query = """
                MATCH (b:Brand)
                WHERE b.name CONTAINS $keyword
                RETURN b
                LIMIT 50
                """
                params = {'keyword': keyword}
            
            results = self.graph.query(query, params=params)
            return [dict(result['b']) for result in results]
        except Exception as e:
            print(f"搜索品牌失败: {e}")
            return []
    
    def get_brand_history(self, brand_name: str) -> List[Dict[str, Any]]:
        """获取品牌历史案例"""
        if not self.graph:
            return []
        
        try:
            query = """
            MATCH (b:Brand {name: $name})-[r:LAUNCHES_CAMPAIGN]->(c:Campaign)
            RETURN c, r
            ORDER BY c.launch_date DESC
            LIMIT 20
            """
            results = self.graph.query(query, params={'name': brand_name})
            return [
                {
                    'campaign': dict(result['c']),
                    'relationship': dict(result['r'])
                }
                for result in results
            ]
        except Exception as e:
            print(f"获取品牌历史失败: {e}")
            return []
    
    def validate_brand_data(self, brand_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证品牌数据"""
        errors = []
        warnings = []
        
        # 必需字段检查
        if not brand_data.get('name'):
            errors.append('品牌名称不能为空')
        
        # 字段格式检查
        if 'founded_year' in brand_data and brand_data['founded_year']:
            try:
                year = int(brand_data['founded_year'])
                if year < 1800 or year > datetime.now().year:
                    warnings.append(f'成立年份 {year} 可能不正确')
            except:
                warnings.append('成立年份格式不正确')
        
        # 去重检查
        if brand_data.get('name'):
            existing = self.get_brand(brand_data['name'])
            if existing:
                warnings.append(f'品牌 {brand_data["name"]} 已存在，将更新')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def export_brands(self, output_path: str, format: str = 'json') -> bool:
        """导出品牌列表"""
        if not self.graph:
            return False
        
        try:
            query = "MATCH (b:Brand) RETURN b"
            results = self.graph.query(query)
            brands = [dict(result['b']) for result in results]
            
            if format == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(brands, f, ensure_ascii=False, indent=2)
            elif format == 'csv':
                df = pd.DataFrame(brands)
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
            elif format == 'excel':
                df = pd.DataFrame(brands)
                df.to_excel(output_path, index=False)
            else:
                return False
            
            return True
        except Exception as e:
            print(f"导出品牌失败: {e}")
            return False


def test_brand_knowledge_manager():
    """测试品牌知识管理器"""
    manager = BrandKnowledgeManager()
    
    # 测试数据
    test_brand = {
        'name': '测试品牌',
        'industry': '科技',
        'brand_positioning': '创新科技品牌',
        'brand_personality': '年轻、创新、智能',
        'target_audience': '年轻科技爱好者',
        'founded_year': '2020',
        'characteristics': '注重用户体验，追求创新'
    }
    
    # 测试添加品牌
    print("测试添加品牌...")
    result = manager.add_or_update_brand(test_brand)
    print(f"结果: {result}")
    
    # 测试查询品牌
    print("\n测试查询品牌...")
    brand = manager.get_brand('测试品牌')
    print(f"品牌信息: {brand}")
    
    # 测试搜索品牌
    print("\n测试搜索品牌...")
    brands = manager.search_brands('测试')
    print(f"搜索结果: {len(brands)} 个品牌")


if __name__ == "__main__":
    test_brand_knowledge_manager()



