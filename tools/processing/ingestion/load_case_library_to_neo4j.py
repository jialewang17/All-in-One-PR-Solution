#!/usr/bin/env python3
"""
公关案例关系管理系统
支持公关案例库和关系库的导入、管理、查询和存储
"""

import json
import csv
import re
import pandas as pd
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# 引入 GraphClient
try:
    from core.querying.graph import GraphClient
except ImportError:
    print("❌ 错误: 无法导入 GraphClient。请确保您在项目根目录下运行，或调整 PYTHONPATH。")
    GraphClient = None


def clean_str(val) -> str:
    """数据清洗：去除首尾空格，处理空值 (NaN/None)"""
    if pd.isna(val) or val == "" or str(val).lower() == "nan":
        return ""
    return str(val).strip()


def split_items(val) -> List[str]:
    """智能拆分：处理中英文逗号、顿号、换行符"""
    if pd.isna(val) or val == "":
        return []
    normalized = str(val).replace("、", ",").replace("，", ",").replace("\n", ",").replace(";", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


class GraphSyncer:
    """GraphRAG 知识库同步器 - 将公关案例库的 CSV 表格导入 Neo4j"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        if GraphClient is None:
            raise ImportError("无法导入 GraphClient，请检查 core.querying.graph 模块")
        self.graph = GraphClient()
        # 测试连接
        try:
            self.graph.query("RETURN 1 as test")
            print("✅ Neo4j连接成功")
        except Exception as e:
            print(f"❌ Neo4j连接失败: {e}")
            raise

    def _read_csv(self, filename: str) -> pd.DataFrame:
        """读取 CSV 的辅助函数"""
        path = os.path.join(self.base_dir, filename)
        if not os.path.exists(path):
            print(f"⚠️ 文件未找到: {path} (跳过此步骤)")
            return pd.DataFrame()
        try:
            # encoding='utf-8-sig' 可以自动处理 BOM 头
            return pd.read_csv(path, encoding='utf-8-sig', on_bad_lines='skip')
        except Exception as e:
            # 如果 utf-8 失败，尝试 gbk
            try:
                return pd.read_csv(path, encoding='gbk', on_bad_lines='skip')
            except Exception as e2:
                print(f"❌ 读取 {filename} 失败: {e}")
                return pd.DataFrame()

    def sync_channels(self):
        """
        同步渠道层级
        策略：由于 CSV 前两列和后两列是非对齐的，需要分两步独立读取。
        """
        filename = "公关案例库_传播渠道关系表_表格.csv"
        # 注意：传播渠道关系表可能只有Excel文件，没有CSV
        excel_filename = "公关案例库_传播渠道关系表.xlsx"
        excel_path = os.path.join(self.base_dir, excel_filename)
        
        if os.path.exists(excel_path):
            try:
                df = pd.read_excel(excel_path, encoding='utf-8-sig')
            except:
                try:
                    df = pd.read_excel(excel_path, encoding='gbk')
                except Exception as e:
                    print(f"⚠️ 读取Excel文件失败: {e}")
                    df = pd.DataFrame()
        else:
            df = self._read_csv(filename)
            
        if df.empty:
            print(f"⚠️ {filename} 或 {excel_filename} 不存在或为空，跳过渠道同步")
            return

        print(f"🔄 正在同步渠道: {filename} ...")
        
        # 处理一级和二级传播渠道（如果存在）
        if '一级传播渠道' in df.columns and '二级传播渠道' in df.columns:
            for _, row in df.iterrows():
                l1 = clean_str(row.get('一级传播渠道'))
                l2 = clean_str(row.get('二级传播渠道'))
                if l1 and l2:
                    self.graph.query(
                        """
                        MERGE (cat:ChannelCategory {name: $p_name})
                        MERGE (ch:Channel {name: $c_name, level: 2})
                        MERGE (ch)-[:BELONGS_TO_CHANNEL_CATEGORY]->(cat)
                        """,
                        params={"p_name": l1, "c_name": l2}
                    )
        
        # 处理三级传播渠道（如果存在）
        if '三级传播渠道' in df.columns:
            for _, row in df.iterrows():
                l2 = clean_str(row.get('二级传播渠道'))
                l3_raw = clean_str(row.get('三级传播渠道', ''))
                if l2 and l3_raw:
                    l3_list = split_items(l3_raw)
                    for l3 in l3_list:
                        self.graph.query(
                            """
                            MERGE (ch2:Channel {name: $l2_name, level: 2})
                            MERGE (ch3:Channel {name: $l3_name, level: 3})
                            MERGE (ch3)-[:BELONGS_TO_CHANNEL]->(ch2)
                            """,
                            params={"l2_name": l2, "l3_name": l3}
                        )
        
        print(f"   ✅ 渠道同步完成")

    def sync_goals(self):
        """同步公关目标"""
        filename = "公关案例库_公关目标关系表_表格.csv"
        print(f"🔄 正在同步目标: {filename} ...")
        df = self._read_csv(filename)
        if df.empty: 
            return

        for _, row in df.iterrows():
            l1 = clean_str(row.get("一级分类"))
            l2 = clean_str(row.get("二级分类"))
            if l1 and l2:
                self.graph.query(
                    """
                    MERGE (g1:PRGoal {name: $p_name, level: 1})
                    MERGE (g2:PRGoal {name: $c_name, level: 2})
        MERGE (g2)-[:REFINES]->(g1)
        """,
                    params={"p_name": l1, "c_name": l2}
                )
        print(f"   ✅ 目标同步完成")

    def sync_industries(self):
        """同步行业"""
        filename = "公关案例库_行业与品牌关系表_表格.csv"
        print(f"🔄 正在同步行业: {filename} ...")
        df = self._read_csv(filename)
        if df.empty: 
            return

        for _, row in df.iterrows():
            l1 = clean_str(row.get("一级行业分类"))
            l2_raw = clean_str(row.get("二级行业分类", ""))
            if l1:
                # 处理二级行业（支持逗号分割）
                l2_list = split_items(l2_raw) if l2_raw else []
                for l2 in l2_list:
                    self.graph.query(
                        """
                        MERGE (i1:Industry {name: $p_name, level: 1})
                        MERGE (i2:Industry {name: $c_name, level: 2})
                        MERGE (i2)-[:IN_INDUSTRY]->(i1)
                        """,
                        params={"p_name": l1, "c_name": l2}
                    )
        print(f"   ✅ 行业同步完成")

    def sync_cases(self):
        """同步案例及其关系"""
        filename = "公关案例库_公关案例库_表格.csv"
        print(f"🔄 正在同步案例: {filename} ...")
        df = self._read_csv(filename)
        if df.empty: 
            return

        count = 0
        for _, row in df.iterrows():
            # 获取案例名称
            case_name = clean_str(row.get("企业") or row.get("品牌/项目") or row.get("品牌") or row.get("项目名称") or row.get("案例名称"))
            if not case_name:
                continue

            # 1. 创建案例节点 (清理属性)
            # 过滤掉空的属性值，保持图谱干净
            props = {k.strip(): str(v).strip() for k, v in row.to_dict().items() if clean_str(v)}
            self.graph.query(
                "MERGE (c:PRCase {name: $name}) SET c += $props",
                params={"name": case_name, "props": props}
            )

            # 2. 关联行业 (同时处理一级和二级)
            inds = [clean_str(row.get("一级行业分类")), clean_str(row.get("二级行业分类"))]
            for ind in inds:
                if ind:
                    self.graph.query(
                        """
                        MATCH (c:PRCase {name: $case})
                        MERGE (i:Industry {name: $ind})
                        MERGE (c)-[:IN_INDUSTRY]->(i)
                        """,
                        params={"case": case_name, "ind": ind}
                    )

            # 3. 关联渠道 (聚合所有渠道相关列)
            # 注意：案例表中的列名可能多样，这里聚合了常见的列名
            channel_cols = ["主要平台", "渠道类型", "渠道大类"]
            for col in channel_cols:
                items = split_items(row.get(col))
                for item in items:
                    # 尝试匹配现有的 Channel。如果没有，MERGE 会创建一个无层级信息的 Channel 节点
                    # 这样保证了数据不丢失，后续可以通过名称手动修补层级
                    self.graph.query(
                        """
                        MATCH (c:PRCase {name: $case})
                        MERGE (ch:Channel {name: $ch_name})
                        MERGE (c)-[:USES_CHANNEL]->(ch)
                        """,
                        params={"case": case_name, "ch_name": item}
                    )

            # 4. 关联目标
            goal_cols = ["具体目标", "目标类型"]
            for col in goal_cols:
                items = split_items(row.get(col))
                for item in items:
                    self.graph.query(
                        """
                        MATCH (c:PRCase {name: $case})
                        MERGE (g:PRGoal {name: $g_name})
                        MERGE (c)-[:ACHIEVES_GOAL]->(g)
                        """,
                        params={"case": case_name, "g_name": item}
                    )
            count += 1
        print(f"   ✅ 已处理 {count} 个案例")


class PRCaseRelationshipManager:
    """公关案例关系管理器 - 处理行业与品牌的层级关系"""
    
    # 列名映射
    COLUMN_MAPPINGS = {
        '一级行业分类': 'industry_level1',
        '二级行业分类': 'industry_level2',
        '一级公关目标分类': 'pr_objective_level1',
        '二级公关目标分类': 'pr_objective_level2',
        # 添加Excel文件中实际使用的列名映射
        '一级分类': 'pr_objective_level1',
        '二级分类': 'pr_objective_level2',
        # 添加传播渠道相关列名映射
        '一级传播渠道': 'communication_channel_level1',
        '二级传播渠道': 'communication_channel_level2',
        '三级传播渠道': 'communication_channel_level3',
        '传播渠道': 'communication_channel',
        '公关目标': 'pr_objective',
        '行业': 'industry',
        '品牌': 'brand',
        '案例名称': 'case_name',
        '案例描述': 'case_description',
        '发生时间': 'occur_time',
        '案例影响': 'case_impact'
    }

    # 不同层级节点的可视化样式设置 - 确保明显的视觉区分
    VISUAL_STYLES = {
        'industry_level1': {'size': 25, 'color': '#1F77B4', 'label': '一级行业'},
        'industry_level2': {'size': 18, 'color': '#4DAF4A', 'label': '二级行业'},
        'pr_objective_level1': {'size': 23, 'color': '#FF6384', 'label': '一级公关目标'},
        'pr_objective_level2': {'size': 16, 'color': '#FFCE56', 'label': '二级公关目标'},
        'communication_channel_level1': {'size': 20, 'color': '#9467BD', 'label': '一级传播渠道'},
        'communication_channel_level2': {'size': 14, 'color': '#8C564B', 'label': '二级传播渠道'},
        'communication_channel_level3': {'size': 10, 'color': '#7F7F7F', 'label': '三级传播渠道'},
        'brand': {'size': 12, 'color': '#FF7F50', 'label': '品牌'},
        'communication_channel': {'size': 10, 'color': '#9467BD', 'label': '传播渠道'},
        'pr_case': {'size': 9, 'color': '#E377C2', 'label': '公关案例'}
    }
    
    def __init__(self, uri=None, username=None, password=None, database=None):
        """初始化管理器
        
        Args:
            uri: Neo4j数据库URI
            username: Neo4j用户名
            password: Neo4j密码
            database: Neo4j数据库名称
        """
        # 确保环境变量已加载
        PROJECT_ROOT = Path(__file__).parent.parent
        ENV_FILE = PROJECT_ROOT / '.env'
        load_dotenv(ENV_FILE, override=True)
        
        # 使用传入的参数或环境变量中的值
        self.uri = uri or os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
        self.username = username or os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD', 'password')
        self.database = database or os.getenv('NEO4J_DATABASE', 'neo4j')
        
        # 连接Neo4j数据库
        self.driver = None
        self.data_dir = Path('data/pr_cases')
        # 确保数据目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 尝试连接数据库
        print(f"正在连接到Neo4j: {self.uri}")
        print(f"数据库: {self.database}, 用户名: {self.username}")
        
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            # 验证连接
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1")
                if result.single():
                    print("✅ Neo4j连接成功！")
                    self.graph = self  # 使用自身作为graph对象，因为它有query方法
                else:
                    print("❌ Neo4j连接验证失败")
                    self.graph = None
        except Exception as e:
            error_msg = f"❌ Neo4j连接失败: {str(e)}"
            print(error_msg)
            if "Connection refused" in str(e):
                print("请确认Neo4j数据库服务正在运行")
            elif "The client is unauthorized" in str(e):
                print("请检查Neo4j用户名和密码是否正确")
            elif "Database not found" in str(e):
                print("请确认数据库名称是否正确")
            self.graph = None
            self.driver = None
    
    def query(self, query, params=None):
        """
        直接执行Cypher查询
        模拟Neo4jGraph的query方法接口
        """
        if not self.driver:
            raise Exception("Neo4j连接不可用")
        
        params = params or {}
        results = []
        
        try:
            with self.driver.session(database=self.database) as session:
                # 使用事务执行查询
                records = session.run(query, params)
                for record in records:
                    # 将Neo4j Record转换为字典格式
                    result_dict = {}
                    for key in record.keys():
                        result_dict[key] = record[key]
                    results.append(result_dict)
                return results
        except Exception as e:
            raise Exception(f"执行查询失败: {e}")
        
    def import_industry_brand_relationship_from_excel(self, excel_path: str, sheet_name: str = 0) -> Dict[str, Any]:
        """
        从Excel文件导入行业与品牌关系表
        表头包括：一级行业分类和二级行业分类，二级分类的单元格里会按照逗号分割
        """
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            print(f"成功读取Excel文件，共{len(df)}条记录")
            
            results = {
                'total': len(df),
                'processed': 0,
                'industry_level1_created': 0,
                'industry_level2_created': 0,
                'errors': []
            }
            
            for index, row in df.iterrows():
                try:
                    # 清理数据
                    row_data = {k: v for k, v in row.items() if pd.notna(v)}
                    normalized_data = self.normalize_record(row_data)
                    
                    # 处理行业关系
                    result = self._process_industry_relationship(normalized_data)
                    results['processed'] += 1
                    results['industry_level1_created'] += result.get('industry_level1_created', 0)
                    results['industry_level2_created'] += result.get('industry_level2_created', 0)
                    
                except Exception as e:
                    results['errors'].append({
                        'row': index + 2,  # +2 因为pandas索引从0开始，Excel行号从1开始
                        'error': str(e)
                    })
                    print(f"处理行{index + 2}时出错: {e}")
            
            return results
        except Exception as e:
            error_msg = f"导入失败: {e}"
            print(error_msg)
            return {'error': error_msg}
    
    def normalize_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """规范化数据字段"""
        normalized = {}
        for key, value in data.items():
            key_str = key.strip() if isinstance(key, str) else key
            if isinstance(value, str):
                value = value.strip()
            normalized[key_str] = value

        # 应用列名映射
        for source, target in self.COLUMN_MAPPINGS.items():
            if source in normalized and (target not in normalized or not normalized[target]):
                normalized[target] = normalized[source]

        return normalized
    
    def _process_industry_relationship(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理行业关系，创建层级节点并建立关系"""
        if not self.graph:
            raise Exception('Neo4j连接不可用')
        
        result = {
            'industry_level1_created': 0,
            'industry_level2_created': 0,
            'brand_created': 0
        }
        
        industry_level1 = data.get('industry_level1')
        industry_level2_raw = data.get('industry_level2', '')
        brand_name = data.get('brand')
        
        if not industry_level1:
            raise Exception('一级行业分类不能为空')
        
        # 创建一级行业节点
        level1_result = self._create_or_update_industry_level1(industry_level1)
        if level1_result['created']:
            result['industry_level1_created'] = 1
        
        # 处理二级行业分类（支持逗号分割的多个值）
        level2_list = []
        if industry_level2_raw:
            # 分割多个二级行业
            level2_list = self._split_multiple_values(industry_level2_raw)
            for level2 in level2_list:
                if level2.strip():
                    level2_result = self._create_or_update_industry_level2(level2.strip(), industry_level1)
                    if level2_result['created']:
                        result['industry_level2_created'] += 1
        
        # 处理品牌节点和关系
        if brand_name:
            brand_result = self._create_or_update_brand(brand_name)
            if brand_result['created']:
                result['brand_created'] = 1
            
            # 建立品牌与一级行业的关系
            self._create_brand_industry_relationship(brand_name, industry_level1, 'IN_PRIMARY_INDUSTRY')
            
            # 建立品牌与每个二级行业的关系
            for level2 in level2_list:
                if level2.strip():
                    self._create_brand_industry_relationship(brand_name, level2.strip(), 'IN_SECONDARY_INDUSTRY')
        
        return result
    
    def _split_multiple_values(self, text: str) -> List[str]:
        """分割包含多个值的文本（支持逗号等分隔符）"""
        import logging
        try:
            # 输入验证
            if not text:
                logging.debug("传入空文本，返回空列表")
                return []
            
            # 确保输入是字符串类型
            if not isinstance(text, str):
                logging.warning(f"输入类型错误，期望字符串但得到 {type(text).__name__}，尝试转换")
                text = str(text)
            
            # 支持多种常见分隔符
            separators = ['、', '，', ',', ';', '；', '/', '|']
            tmp = text
            for sep in separators:
                tmp = tmp.replace(sep, ' ')
            
            # 分割并清理数据
            parts = [p.strip() for p in tmp.split(' ') if p.strip()]
            
            # 去重但保持顺序
            seen = set()
            result = []
            for p in parts:
                if p not in seen:
                    seen.add(p)
                    result.append(p)
            
            logging.debug(f"成功分割文本，原始长度: {len(text)}, 分割后数量: {len(result)}")
            return result
            
        except Exception as e:
            logging.error(f"分割多值文本时出错: {str(e)}")
            # 出错时返回尽可能处理的结果
            try:
                # 简单回退方案：直接按空格分割
                if isinstance(text, str):
                    basic_result = [p.strip() for p in text.split() if p.strip()]
                    logging.warning(f"回退到基本分割方法，获得 {len(basic_result)} 个元素")
                    return basic_result
            except:
                pass
            # 如果回退也失败，返回空列表
            return []
    
    def _create_or_update_industry_level1(self, name: str) -> Dict[str, Any]:
        """创建或更新一级行业节点"""
        if not name:
            return {'error': '行业名称不能为空'}
        
        try:
            # 检查是否已存在
            check_query = """
            MATCH (i1:IndustryLevel1 {name: $name})
            RETURN i1
            """
            existing = self.graph.query(check_query, params={'name': name})
            
            # 设置视觉样式属性
            properties = {
                'name': name,
                'visual_category': 'industry_level1',
                'visual_size': self.VISUAL_STYLES['industry_level1']['size'],
                'visual_color': self.VISUAL_STYLES['industry_level1']['color'],
                'node_label': self.VISUAL_STYLES['industry_level1']['label'],
                'updated_at': datetime.now().isoformat()
            }
            
            if existing:
                # 更新现有节点
                update_query = """
                MATCH (i1:IndustryLevel1 {name: $name})
                SET i1 += $properties
                RETURN i1
                """
                self.graph.query(update_query, params={'name': name, 'properties': properties})
                return {'created': False, 'name': name}
            else:
                # 创建新节点
                create_query = """
                CREATE (i1:IndustryLevel1 $properties)
                RETURN i1
                """
                self.graph.query(create_query, params={'properties': properties})
                return {'created': True, 'name': name}
                
        except Exception as e:
            raise Exception(f"创建或更新一级行业节点失败: {e}")
    
    def _create_or_update_industry_level2(self, name: str, parent_industry: str) -> Dict[str, Any]:
        """创建或更新二级行业节点，并建立与一级行业的关系"""
        if not name or not parent_industry:
            return {'error': '行业名称或父行业不能为空'}
        
        try:
            # 检查是否已存在
            check_query = """
            MATCH (i2:IndustryLevel2 {name: $name})
            RETURN i2
            """
            existing = self.graph.query(check_query, params={'name': name})
            
            # 设置视觉样式属性
            properties = {
                'name': name,
                'visual_category': 'industry_level2',
                'visual_size': self.VISUAL_STYLES['industry_level2']['size'],
                'visual_color': self.VISUAL_STYLES['industry_level2']['color'],
                'node_label': self.VISUAL_STYLES['industry_level2']['label'],
                'updated_at': datetime.now().isoformat()
            }
            
            if existing:
                # 更新现有节点
                update_query = """
                MATCH (i2:IndustryLevel2 {name: $name})
                SET i2 += $properties
                RETURN i2
                """
                self.graph.query(update_query, params={'name': name, 'properties': properties})
                
                # 确保与父行业的关系存在
                self._ensure_parent_relationship(name, parent_industry)
                return {'created': False, 'name': name}
            else:
                # 创建新节点
                create_query = """
                CREATE (i2:IndustryLevel2 $properties)
                RETURN i2
                """
                self.graph.query(create_query, params={'properties': properties})
                
                # 建立与父行业的关系
                self._ensure_parent_relationship(name, parent_industry)
                return {'created': True, 'name': name}
                
        except Exception as e:
            raise Exception(f"创建或更新二级行业节点失败: {e}")
    
    def _ensure_parent_relationship(self, level2_name: str, level1_name: str) -> None:
        """确保二级行业与一级行业之间的父子关系存在"""
        try:
            # 使用MERGE确保关系只创建一次
            relationship_query = """
            MATCH (i1:IndustryLevel1 {name: $level1_name})
            MATCH (i2:IndustryLevel2 {name: $level2_name})
            MERGE (i2)-[:SUB_INDUSTRY_OF]->(i1)
            """
            self.graph.query(relationship_query, params={
                'level1_name': level1_name,
                'level2_name': level2_name
            })
        except Exception as e:
            raise Exception(f"建立行业层级关系失败: {e}")
    
    def _ensure_communication_channel_parent_relationship(self, level2_name: str, level1_name: str) -> None:
        """确保二级传播渠道与一级传播渠道之间的父子关系存在"""
        try:
            # 使用MERGE确保关系只创建一次
            relationship_query = """
            MATCH (c1:CommunicationChannelLevel1 {name: $level1_name})
            MATCH (c2:CommunicationChannelLevel2 {name: $level2_name})
            MERGE (c2)-[:SUB_CHANNEL_OF]->(c1)
            """
            self.graph.query(relationship_query, params={
                'level1_name': level1_name,
                'level2_name': level2_name
            })
        except Exception as e:
            raise Exception(f"建立传播渠道层级关系失败: {e}")
    
    def _ensure_communication_channel_grandchild_relationship(self, level3_name: str, level2_name: str) -> None:
        """确保三级传播渠道与二级传播渠道之间的父子关系存在"""
        try:
            # 使用MERGE确保关系只创建一次
            relationship_query = """
            MATCH (c2:CommunicationChannelLevel2 {name: $level2_name})
            MATCH (c3:CommunicationChannelLevel3 {name: $level3_name})
            MERGE (c3)-[:SUB_CHANNEL_OF]->(c2)
            """
            self.graph.query(relationship_query, params={
                'level2_name': level2_name,
                'level3_name': level3_name
            })
        except Exception as e:
            raise Exception(f"建立三级传播渠道层级关系失败: {e}")
    
    def _create_or_update_brand(self, name: str) -> Dict[str, Any]:
        """创建或更新品牌节点"""
        if not name:
            return {'error': '品牌名称不能为空'}
        
        try:
            # 检查是否已存在
            check_query = """
            MATCH (b:Brand {name: $name})
            RETURN b
            """
            existing = self.graph.query(check_query, params={'name': name})
            
            # 设置视觉样式属性
            properties = {
                'name': name,
                'visual_category': 'brand',
                'visual_size': self.VISUAL_STYLES['brand']['size'],
                'visual_color': self.VISUAL_STYLES['brand']['color'],
                'node_label': self.VISUAL_STYLES['brand']['label'],
                'updated_at': datetime.now().isoformat()
            }
            
            if existing:
                # 更新现有节点
                update_query = """
                MATCH (b:Brand {name: $name})
                SET b += $properties
                RETURN b
                """
                self.graph.query(update_query, params={'name': name, 'properties': properties})
                return {'created': False, 'name': name}
            else:
                # 创建新节点
                create_query = """
                CREATE (b:Brand $properties)
                RETURN b
                """
                self.graph.query(create_query, params={'properties': properties})
                return {'created': True, 'name': name}
                
        except Exception as e:
            raise Exception(f"创建或更新品牌节点失败: {e}")
    
    def _create_brand_industry_relationship(self, brand_name: str, industry_name: str, relationship_type: str) -> None:
        """建立品牌与行业之间的关系"""
        try:
            # 根据关系类型确定节点标签
            industry_label = 'IndustryLevel1' if relationship_type == 'IN_PRIMARY_INDUSTRY' else 'IndustryLevel2'
            
            # 使用MERGE确保关系只创建一次
            relationship_query = f"""
            MATCH (b:Brand {{name: $brand_name}})
            MATCH (i:{industry_label} {{name: $industry_name}})
            MERGE (b)-[:{relationship_type}]->(i)
            """
            self.graph.query(relationship_query, params={
                'brand_name': brand_name,
                'industry_name': industry_name
            })
        except Exception as e:
            raise Exception(f"建立品牌与行业关系失败: {e}")
    
    def import_communication_channels_from_excel(self, excel_path: str, sheet_name: str = 0) -> Dict[str, Any]:
        """
        从Excel文件导入传播渠道关系表
        表头包括：一级传播渠道、二级传播渠道和三级传播渠道，三级传播渠道的单元格里会按照逗号分割
        三级传播渠道从属于二级传播渠道从属于一级传播渠道
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 验证文件是否存在
        if not os.path.exists(excel_path):
            error_msg = f"Excel文件不存在: {excel_path}"
            logger.error(error_msg)
            print(error_msg)
            return {'error': error_msg}
        
        try:
            # 读取Excel文件
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            logger.info(f"成功读取Excel文件，共{len(df)}条记录")
            print(f"成功读取Excel文件，共{len(df)}条记录")
            
            # 验证必要列是否存在
            required_columns = ['一级传播渠道', '二级传播渠道', '三级传播渠道']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                error_msg = f"Excel文件缺少必要列: {', '.join(missing_columns)}"
                logger.error(error_msg)
                print(error_msg)
                return {'error': error_msg, 'missing_columns': missing_columns}
            
            results = {
                'total': len(df),
                'processed': 0,
                'successful': 0,
                'communication_channel_level1_created': 0,
                'communication_channel_level2_created': 0,
                'communication_channel_level3_created': 0,
                'errors': [],
                'summary': ''
            }
            
            # 检查Neo4j连接
            if not self.driver:
                error_msg = "Neo4j连接未建立"
                logger.error(error_msg)
                print(error_msg)
                return {'error': error_msg}
            
            for index, row in df.iterrows():
                try:
                    # 清理数据
                    row_data = {k: v for k, v in row.items() if pd.notna(v)}
                    
                    # 验证至少有一级传播渠道
                    if not row_data.get('一级传播渠道'):
                        raise ValueError("一级传播渠道不能为空")
                    
                    normalized_data = self.normalize_record(row_data)
                    
                    # 处理传播渠道关系
                    result = self._process_communication_channel_relationship(normalized_data)
                    results['processed'] += 1
                    results['successful'] += 1
                    results['communication_channel_level1_created'] += result.get('communication_channel_level1_created', 0)
                    results['communication_channel_level2_created'] += result.get('communication_channel_level2_created', 0)
                    results['communication_channel_level3_created'] += result.get('communication_channel_level3_created', 0)
                    
                except Exception as e:
                    results['processed'] += 1
                    error_detail = {
                        'row': index + 2,  # +2 因为pandas索引从0开始，Excel行号从1开始
                        'data': str(row_data),
                        'error': str(e)
                    }
                    results['errors'].append(error_detail)
                    logger.error(f"处理行{index + 2}时出错: {e}")
                    print(f"处理行{index + 2}时出错: {e}")
            
            # 生成摘要信息
            success_rate = (results['successful'] / results['total'] * 100) if results['total'] > 0 else 0
            results['summary'] = f"总记录数: {results['total']}, 成功处理: {results['successful']}, 失败: {len(results['errors'])}, 成功率: {success_rate:.2f}%"
            logger.info(results['summary'])
            print(results['summary'])
            
            return results
        except pd.errors.EmptyDataError:
            error_msg = "Excel文件为空或指定的工作表不存在"
            logger.error(error_msg)
            print(error_msg)
            return {'error': error_msg}
        except pd.errors.ParserError:
            error_msg = "Excel文件格式错误，无法解析"
            logger.error(error_msg)
            print(error_msg)
            return {'error': error_msg}
        except Exception as e:
            error_msg = f"导入过程中发生未知错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(error_msg)
            return {'error': error_msg}
    
    def import_pr_objectives_from_excel(self, excel_path: str, sheet_name: str = 0) -> Dict[str, Any]:
        """
        从Excel文件导入公关目标关系表
        表头包括：一级公关目标分类和二级公关目标分类，二级分类的单元格里会按照逗号分割
        """
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            print(f"成功读取Excel文件，共{len(df)}条记录")
            
            results = {
                'total': len(df),
                'processed': 0,
                'pr_objective_level1_created': 0,
                'pr_objective_level2_created': 0,
                'errors': []
            }
            
            for index, row in df.iterrows():
                try:
                    # 清理数据
                    row_data = {k: v for k, v in row.items() if pd.notna(v)}
                    normalized_data = self.normalize_record(row_data)
                    
                    # 处理公关目标关系
                    result = self._process_pr_objective_relationship(normalized_data)
                    results['processed'] += 1
                    results['pr_objective_level1_created'] += result.get('pr_objective_level1_created', 0)
                    results['pr_objective_level2_created'] += result.get('pr_objective_level2_created', 0)
                    
                except Exception as e:
                    results['errors'].append({
                        'row': index + 2,  # +2 因为pandas索引从0开始，Excel行号从1开始
                        'error': str(e)
                    })
                    print(f"处理行{index + 2}时出错: {e}")
            
            return results
        except Exception as e:
            error_msg = f"导入失败: {e}"
            print(error_msg)
            return {'error': error_msg}
    
    def import_pr_cases_from_excel(self, excel_path: str, sheet_name: str = 0) -> Dict[str, Any]:
        """导入真实案例库"""
        # 后续实现...
        pass
    
    def search_industry(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索行业信息"""
        if not self.graph:
            return []
        
        try:
            query = """
            MATCH (i) WHERE i.name CONTAINS $keyword AND (i:IndustryLevel1 OR i:IndustryLevel2)
            RETURN i.name as name, labels(i)[0] as type
            """
            results = self.graph.query(query, params={'keyword': keyword})
            return [{'name': record['name'], 'type': record['type']} for record in results]
        except Exception as e:
            print(f"搜索行业失败: {e}")
            return []
    
    def get_industry_hierarchy(self, industry_level1: str = None) -> Dict[str, Any]:
        """获取行业层级关系"""
        if not self.graph:
            return {'error': 'Neo4j连接不可用'}
        
        try:
            if industry_level1:
                # 获取特定一级行业下的所有二级行业
                query = """
                MATCH (i1:IndustryLevel1 {name: $industry_level1})
                OPTIONAL MATCH (i2:IndustryLevel2)-[:SUB_INDUSTRY_OF]->(i1)
                RETURN i1.name as level1, collect(i2.name) as level2_list
                """
                results = self.graph.query(query, params={'industry_level1': industry_level1})
                if results:
                    return {
                        'level1': results[0]['level1'],
                        'level2_list': results[0]['level2_list']
                    }
                return {'error': '未找到指定的一级行业'}
            else:
                # 获取所有行业层级关系
                query = """
                MATCH (i1:IndustryLevel1)
                OPTIONAL MATCH (i2:IndustryLevel2)-[:SUB_INDUSTRY_OF]->(i1)
                RETURN i1.name as level1, collect(i2.name) as level2_list
                """
                results = self.graph.query(query)
                hierarchy = {}
                for record in results:
                    hierarchy[record['level1']] = record['level2_list']
                return hierarchy
        except Exception as e:
            return {'error': f"获取行业层级关系失败: {e}"}
    
    def get_brands_by_industry(self, industry_name: str, industry_level: int = 1) -> List[Dict[str, Any]]:
        """
        根据行业获取品牌列表
        industry_level: 1表示一级行业，2表示二级行业
        """
        if not self.graph:
            return []
        
        try:
            if industry_level == 1:
                query = """
                MATCH (b:Brand)-[:IN_PRIMARY_INDUSTRY]->(i:IndustryLevel1 {name: $industry_name})
                RETURN b.name as brand_name
                """
            else:
                query = """
                MATCH (b:Brand)-[:IN_SECONDARY_INDUSTRY]->(i:IndustryLevel2 {name: $industry_name})
                RETURN b.name as brand_name
                """
            
            results = self.graph.query(query, params={'industry_name': industry_name})
            return [{'brand_name': record['brand_name']} for record in results]
        except Exception as e:
            print(f"获取行业品牌列表失败: {e}")
            return []
    
    def get_brand_industries(self, brand_name: str) -> Dict[str, List[str]]:
        """获取品牌所属的行业信息"""
        if not self.graph:
            return {'primary_industries': [], 'secondary_industries': []}
        
        try:
            # 获取品牌的一级行业
            primary_query = """
            MATCH (b:Brand {name: $brand_name})-[:IN_PRIMARY_INDUSTRY]->(i:IndustryLevel1)
            RETURN i.name as industry_name
            """
            primary_results = self.graph.query(primary_query, params={'brand_name': brand_name})
            primary_industries = [record['industry_name'] for record in primary_results]
            
            # 获取品牌的二级行业
            secondary_query = """
            MATCH (b:Brand {name: $brand_name})-[:IN_SECONDARY_INDUSTRY]->(i:IndustryLevel2)
            RETURN i.name as industry_name
            """
            secondary_results = self.graph.query(secondary_query, params={'brand_name': brand_name})
            secondary_industries = [record['industry_name'] for record in secondary_results]
            
            return {
                'primary_industries': primary_industries,
                'secondary_industries': secondary_industries
            }
        except Exception as e:
            print(f"获取品牌行业信息失败: {e}")
            return {'primary_industries': [], 'secondary_industries': []}
    
    def _process_communication_channel_relationship(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理传播渠道关系，创建三级层级节点并建立关系"""
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.graph:
            error_msg = 'Neo4j连接不可用'
            logger.error(error_msg)
            raise Exception(error_msg)
        
        result = {
            'communication_channel_level1_created': 0,
            'communication_channel_level2_created': 0,
            'communication_channel_level3_created': 0,
            'processed_level3_count': 0
        }
        
        try:
            level1 = data.get('communication_channel_level1')
            level2 = data.get('communication_channel_level2')
            level3_raw = data.get('communication_channel_level3', '')
            
            # 数据验证
            if not level1 or not str(level1).strip():
                raise ValueError('一级传播渠道不能为空或仅包含空白字符')
            
            if not level2 or not str(level2).strip():
                raise ValueError('二级传播渠道不能为空或仅包含空白字符')
            
            # 清理数据
            level1 = str(level1).strip()
            level2 = str(level2).strip()
            
            logger.debug(f"开始处理传播渠道关系: 一级={level1}, 二级={level2}")
            
            # 创建一级传播渠道节点
            try:
                level1_result = self._create_or_update_communication_channel_level1(level1)
                if level1_result.get('created', False):
                    result['communication_channel_level1_created'] = 1
                    logger.debug(f"成功创建一级传播渠道: {level1}")
            except Exception as e:
                logger.error(f"创建一级传播渠道失败: {level1}, 错误: {str(e)}")
                raise Exception(f"创建一级传播渠道失败: {str(e)}") from e
            
            # 创建二级传播渠道节点并与一级建立关系
            try:
                level2_result = self._create_or_update_communication_channel_level2(level2, level1)
                if level2_result.get('created', False):
                    result['communication_channel_level2_created'] = 1
                    logger.debug(f"成功创建二级传播渠道: {level2}")
            except Exception as e:
                logger.error(f"创建二级传播渠道失败: {level2}, 父级: {level1}, 错误: {str(e)}")
                raise Exception(f"创建二级传播渠道失败: {str(e)}") from e
            
            # 确保二级传播渠道与一级传播渠道的关系存在
            try:
                self._ensure_communication_channel_parent_relationship(level2, level1)
                logger.debug(f"确保二级传播渠道与一级传播渠道的关系: {level2} -> {level1}")
            except Exception as e:
                logger.error(f"建立二级与一级传播渠道关系失败: {level2} -> {level1}, 错误: {str(e)}")
                raise Exception(f"建立传播渠道层级关系失败: {str(e)}") from e
            
            # 处理三级传播渠道（支持逗号分割的多个值）
            if level3_raw:
                try:
                    level3_list = self._split_multiple_values(str(level3_raw))
                    logger.debug(f"处理三级传播渠道列表，共{len(level3_list)}个值")
                    
                    for level3 in level3_list:
                        level3_stripped = level3.strip()
                        if level3_stripped:
                            try:
                                level3_result = self._create_or_update_communication_channel_level3(level3_stripped, level2)
                                if level3_result.get('created', False):
                                    result['communication_channel_level3_created'] += 1
                                result['processed_level3_count'] += 1
                                logger.debug(f"成功处理三级传播渠道: {level3_stripped}, 父级: {level2}")
                                
                                # 确保三级传播渠道与二级传播渠道的关系存在
                                self._ensure_communication_channel_grandchild_relationship(level3_stripped, level2)
                            except Exception as e:
                                logger.warning(f"处理单个三级传播渠道失败: {level3_stripped}, 父级: {level2}, 错误: {str(e)}")
                                # 继续处理下一个三级传播渠道，不中断整体流程
                                continue
                except Exception as e:
                    logger.error(f"处理三级传播渠道列表失败: {str(e)}")
                    raise Exception(f"处理三级传播渠道列表失败: {str(e)}") from e
            
            logger.info(f"传播渠道关系处理完成: {result}")
            return result
            
        except ValueError as ve:
            logger.error(f"传播渠道数据验证错误: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"处理传播渠道关系时出错: {str(e)}", exc_info=True)
            raise Exception(f"处理传播渠道关系失败: {str(e)}") from e
    
    def _process_pr_objective_relationship(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理公关目标关系，创建层级节点并建立关系"""
        if not self.graph:
            raise Exception('Neo4j连接不可用')
        
        result = {
            'pr_objective_level1_created': 0,
            'pr_objective_level2_created': 0
        }
        
        pr_objective_level1 = data.get('pr_objective_level1')
        pr_objective_level2_raw = data.get('pr_objective_level2', '')
        
        if not pr_objective_level1:
            raise Exception('一级公关目标分类不能为空')
        
        # 创建一级公关目标节点
        level1_result = self._create_or_update_pr_objective_level1(pr_objective_level1)
        if level1_result['created']:
            result['pr_objective_level1_created'] = 1
        
        # 处理二级公关目标分类（支持逗号分割的多个值）
        level2_list = []
        if pr_objective_level2_raw:
            # 分割多个二级公关目标
            level2_list = self._split_multiple_values(pr_objective_level2_raw)
            for level2 in level2_list:
                if level2.strip():
                    level2_result = self._create_or_update_pr_objective_level2(level2.strip(), pr_objective_level1)
                    if level2_result['created']:
                        result['pr_objective_level2_created'] += 1
        
        return result
    
    def _create_or_update_communication_channel_level1(self, name: str) -> Dict[str, Any]:
        """创建或更新一级传播渠道节点"""
        if not name:
            return {'error': '一级传播渠道名称不能为空'}
        
        try:
            # 检查是否已存在
            check_query = """
            MATCH (c1:CommunicationChannelLevel1 {name: $name})
            RETURN c1
            """
            existing = self.graph.query(check_query, params={'name': name})
            
            # 设置视觉样式属性
            properties = {
                'name': name,
                'visual_category': 'communication_channel_level1',
                'visual_size': self.VISUAL_STYLES['communication_channel_level1']['size'],
                'visual_color': self.VISUAL_STYLES['communication_channel_level1']['color'],
                'node_label': self.VISUAL_STYLES['communication_channel_level1']['label'],
                'updated_at': datetime.now().isoformat()
            }
            
            if existing:
                # 更新现有节点
                update_query = """
                MATCH (c1:CommunicationChannelLevel1 {name: $name})
                SET c1 += $properties
                RETURN c1
                """
                self.graph.query(update_query, params={'name': name, 'properties': properties})
                return {'created': False, 'name': name}
            else:
                # 创建新节点
                create_query = """
                CREATE (c1:CommunicationChannelLevel1 $properties)
                RETURN c1
                """
                self.graph.query(create_query, params={'properties': properties})
                return {'created': True, 'name': name}
                
        except Exception as e:
            raise Exception(f"创建或更新一级传播渠道节点失败: {e}")
    
    def _create_or_update_pr_objective_level1(self, name: str) -> Dict[str, Any]:
        """创建或更新一级公关目标节点"""
        if not name:
            return {'error': '公关目标名称不能为空'}
        
        try:
            # 检查是否已存在
            check_query = """
            MATCH (p1:PRObjectiveLevel1 {name: $name})
            RETURN p1
            """
            existing = self.graph.query(check_query, params={'name': name})
            
            # 设置视觉样式属性
            properties = {
                'name': name,
                'visual_category': 'pr_objective_level1',
                'visual_size': self.VISUAL_STYLES['pr_objective_level1']['size'],
                'visual_color': self.VISUAL_STYLES['pr_objective_level1']['color'],
                'node_label': self.VISUAL_STYLES['pr_objective_level1']['label'],
                'updated_at': datetime.now().isoformat()
            }
            
            if existing:
                # 更新现有节点
                update_query = """
                MATCH (p1:PRObjectiveLevel1 {name: $name})
                SET p1 += $properties
                RETURN p1
                """
                self.graph.query(update_query, params={'name': name, 'properties': properties})
                return {'created': False, 'name': name}
            else:
                # 创建新节点
                create_query = """
                CREATE (p1:PRObjectiveLevel1 $properties)
                RETURN p1
                """
                self.graph.query(create_query, params={'properties': properties})
                return {'created': True, 'name': name}
                
        except Exception as e:
            raise Exception(f"创建或更新一级公关目标节点失败: {e}")
    
    def _create_or_update_communication_channel_level2(self, name: str, parent_channel: str) -> Dict[str, Any]:
        """创建或更新二级传播渠道节点"""
        if not name:
            return {'error': '二级传播渠道名称不能为空'}
        
        if not parent_channel:
            return {'error': '一级传播渠道名称不能为空'}
        
        try:
            # 检查是否已存在
            check_query = """
            MATCH (c2:CommunicationChannelLevel2 {name: $name})
            RETURN c2
            """
            existing = self.graph.query(check_query, params={'name': name})
            
            # 设置视觉样式属性
            properties = {
                'name': name,
                'visual_category': 'communication_channel_level2',
                'visual_size': self.VISUAL_STYLES['communication_channel_level2']['size'],
                'visual_color': self.VISUAL_STYLES['communication_channel_level2']['color'],
                'node_label': self.VISUAL_STYLES['communication_channel_level2']['label'],
                'parent_name': parent_channel,
                'updated_at': datetime.now().isoformat()
            }
            
            if existing:
                # 更新现有节点
                update_query = """
                MATCH (c2:CommunicationChannelLevel2 {name: $name})
                SET c2 += $properties
                RETURN c2
                """
                self.graph.query(update_query, params={'name': name, 'properties': properties})
                return {'created': False, 'name': name}
            else:
                # 创建新节点
                create_query = """
                CREATE (c2:CommunicationChannelLevel2 $properties)
                RETURN c2
                """
                self.graph.query(create_query, params={'properties': properties})
                return {'created': True, 'name': name}
                
        except Exception as e:
            raise Exception(f"创建或更新二级传播渠道节点失败: {e}")
    
    def _create_or_update_communication_channel_level3(self, name: str, parent_channel: str) -> Dict[str, Any]:
        """创建或更新三级传播渠道节点"""
        if not name:
            return {'error': '三级传播渠道名称不能为空'}
        
        if not parent_channel:
            return {'error': '二级传播渠道名称不能为空'}
        
        try:
            # 检查是否已存在
            check_query = """
            MATCH (c3:CommunicationChannelLevel3 {name: $name})
            RETURN c3
            """
            existing = self.graph.query(check_query, params={'name': name})
            
            # 设置视觉样式属性
            properties = {
                'name': name,
                'visual_category': 'communication_channel_level3',
                'visual_size': self.VISUAL_STYLES['communication_channel_level3']['size'],
                'visual_color': self.VISUAL_STYLES['communication_channel_level3']['color'],
                'node_label': self.VISUAL_STYLES['communication_channel_level3']['label'],
                'parent_name': parent_channel,
                'updated_at': datetime.now().isoformat()
            }
            
            if existing:
                # 更新现有节点
                update_query = """
                MATCH (c3:CommunicationChannelLevel3 {name: $name})
                SET c3 += $properties
                RETURN c3
                """
                self.graph.query(update_query, params={'name': name, 'properties': properties})
                return {'created': False, 'name': name}
            else:
                # 创建新节点
                create_query = """
                CREATE (c3:CommunicationChannelLevel3 $properties)
                RETURN c3
                """
                self.graph.query(create_query, params={'properties': properties})
                return {'created': True, 'name': name}
                
        except Exception as e:
            raise Exception(f"创建或更新三级传播渠道节点失败: {e}")
    
    def _create_or_update_pr_objective_level2(self, name: str, parent_objective: str) -> Dict[str, Any]:
        """创建或更新二级公关目标节点，并建立与一级公关目标的关系"""
        if not name or not parent_objective:
            return {'error': '公关目标名称或父目标不能为空'}
        
        try:
            # 检查是否已存在
            check_query = """
            MATCH (p2:PRObjectiveLevel2 {name: $name})
            RETURN p2
            """
            existing = self.graph.query(check_query, params={'name': name})
            
            # 设置视觉样式属性
            properties = {
                'name': name,
                'visual_category': 'pr_objective_level2',
                'visual_size': self.VISUAL_STYLES['pr_objective_level2']['size'],
                'visual_color': self.VISUAL_STYLES['pr_objective_level2']['color'],
                'node_label': self.VISUAL_STYLES['pr_objective_level2']['label'],
                'updated_at': datetime.now().isoformat()
            }
            
            if existing:
                # 更新现有节点
                update_query = """
                MATCH (p2:PRObjectiveLevel2 {name: $name})
                SET p2 += $properties
                RETURN p2
                """
                self.graph.query(update_query, params={'name': name, 'properties': properties})
                
                # 确保与父目标的关系存在
                self._ensure_pr_objective_parent_relationship(name, parent_objective)
                return {'created': False, 'name': name}
            else:
                # 创建新节点
                create_query = """
                CREATE (p2:PRObjectiveLevel2 $properties)
                RETURN p2
                """
                self.graph.query(create_query, params={'properties': properties})
                
                # 建立与父目标的关系
                self._ensure_pr_objective_parent_relationship(name, parent_objective)
                return {'created': True, 'name': name}
                
        except Exception as e:
            raise Exception(f"创建或更新二级公关目标节点失败: {e}")
    
    def _ensure_pr_objective_parent_relationship(self, level2_name: str, level1_name: str) -> None:
        """确保二级公关目标与一级公关目标之间的父子关系存在"""
        try:
            # 使用MERGE确保关系只创建一次
            relationship_query = """
            MATCH (p1:PRObjectiveLevel1 {name: $level1_name})
            MATCH (p2:PRObjectiveLevel2 {name: $level2_name})
            MERGE (p2)-[:SUB_OBJECTIVE_OF]->(p1)
            """
            self.graph.query(relationship_query, params={
                'level1_name': level1_name,
                'level2_name': level2_name
            })
        except Exception as e:
            raise Exception(f"建立公关目标层级关系失败: {e}")
    
    def get_communication_channel_hierarchy(self, channel_level1: str = None) -> Dict[str, Any]:
        """
        获取传播渠道的层级结构
        
        Args:
            channel_level1: 可选的一级传播渠道名称，如果提供则只返回该渠道下的层级
            
        Returns:
            包含层级结构的字典
        """
        import logging
        try:
            # 输入验证
            if channel_level1 and not isinstance(channel_level1, str):
                logging.error("传播渠道参数类型错误，应为字符串")
                return {'error': '传播渠道参数类型错误，应为字符串'}
            
            if not self.graph:
                logging.error('Neo4j连接不可用')
                return {'error': 'Neo4j连接不可用'}
            
            try:
                if channel_level1:
                    # 获取特定一级传播渠道下的所有层级
                    logging.info(f"查询指定一级传播渠道 '{channel_level1}' 的层级关系")
                    query = """
                    MATCH (c1:CommunicationChannelLevel1 {name: $channel_level1})
                    OPTIONAL MATCH (c2:CommunicationChannelLevel2)-[:SUB_CHANNEL_OF]->(c1)
                    OPTIONAL MATCH (c3:CommunicationChannelLevel3)-[:SUB_CHANNEL_OF]->(c2)
                    RETURN c1.name as level1, c2.name as level2, collect(DISTINCT c3.name) as level3_list
                    """
                    results = self.graph.query(query, params={'channel_level1': channel_level1})
                    
                    if not results:
                        logging.warning(f"未找到指定的一级传播渠道: {channel_level1}")
                        return {'error': '未找到指定的一级传播渠道'}
                    
                    hierarchy = {
                        'level1': results[0]['level1'],
                        'children': []
                    }
                    
                    # 构建二级和三级渠道关系
                    level2_map = {}
                    level2_count = 0
                    level3_count = 0
                    
                    for record in results:
                        if record['level2']:
                            if record['level2'] not in level2_map:
                                level2_map[record['level2']] = []
                                level2_count += 1
                            
                            level3_list = record['level3_list'] or []
                            level2_map[record['level2']].extend(level3_list)
                            level3_count += len(level3_list)
                    
                    for level2_name, level3_list in level2_map.items():
                        unique_level3_list = list(set(level3_list))  # 去重
                        hierarchy['children'].append({
                            'level2': level2_name,
                            'level3_list': unique_level3_list
                        })
                    
                    logging.info(f"成功获取指定传播渠道层级关系: 1个一级渠道, {level2_count}个二级渠道, {len(unique_level3_list)}个三级渠道")
                    
                    # 添加统计信息
                    result = {
                        'hierarchy': hierarchy,
                        'statistics': {
                            'level1_count': 1,
                            'level2_count': level2_count,
                            'level3_count': len(unique_level3_list)
                        }
                    }
                    
                    return result
                else:
                    # 获取所有传播渠道层级关系
                    logging.info("查询所有传播渠道的层级关系")
                    query = """
                    MATCH (c1:CommunicationChannelLevel1)
                    OPTIONAL MATCH (c2:CommunicationChannelLevel2)-[:SUB_CHANNEL_OF]->(c1)
                    OPTIONAL MATCH (c3:CommunicationChannelLevel3)-[:SUB_CHANNEL_OF]->(c2)
                    RETURN c1.name as level1, c2.name as level2, collect(DISTINCT c3.name) as level3_list
                    """
                    results = self.graph.query(query)
                    
                    hierarchy = {}
                    level1_count = 0
                    level2_count = 0
                    level3_count = 0
                    
                    for record in results:
                        # 安全地获取记录字段
                        level1_name = record.get('level1')
                        level2_name = record.get('level2')
                        level3_list = record.get('level3_list') or []
                        
                        if not level1_name:
                            logging.warning("跳过缺少一级渠道名称的记录")
                            continue
                        
                        if level1_name not in hierarchy:
                            hierarchy[level1_name] = []
                            level1_count += 1
                        
                        if level2_name:
                            # 检查是否已存在该二级渠道
                            existing_level2 = None
                            for item in hierarchy[level1_name]:
                                if item['level2'] == level2_name:
                                    existing_level2 = item
                                    break
                            
                            if existing_level2:
                                # 合并三级渠道列表
                                existing_level2['level3_list'].extend(level3_list)
                                existing_level2['level3_list'] = list(set(existing_level2['level3_list']))  # 去重
                                level3_count += len(level3_list)
                            else:
                                hierarchy[level1_name].append({
                                    'level2': level2_name,
                                    'level3_list': list(set(level3_list))  # 去重
                                })
                                level2_count += 1
                                level3_count += len(level3_list)
                    
                    logging.info(f"成功获取所有传播渠道层级关系: {level1_count}个一级渠道, {level2_count}个二级渠道, {level3_count}个三级渠道")
                    
                    # 添加统计信息
                    result = {
                        'hierarchy': hierarchy,
                        'statistics': {
                            'level1_count': level1_count,
                            'level2_count': level2_count,
                            'level3_count': level3_count
                        }
                    }
                    
                    return result
                    
            except Exception as query_error:
                logging.error(f"Neo4j查询错误: {str(query_error)}")
                return {'error': f"数据库查询失败: {str(query_error)}"}
                
        except Exception as e:
            logging.error(f"获取传播渠道层级关系失败: {str(e)}")
            return {'error': f"获取传播渠道层级关系失败: {str(e)}"}
    
    def get_pr_objective_hierarchy(self, objective_level1: str = None) -> Dict[str, Any]:
        """获取公关目标层级关系"""
        if not self.graph:
            return {'error': 'Neo4j连接不可用'}
        
        try:
            if objective_level1:
                # 获取特定一级公关目标下的所有二级公关目标
                query = """
                MATCH (p1:PRObjectiveLevel1 {name: $objective_level1})
                OPTIONAL MATCH (p2:PRObjectiveLevel2)-[:SUB_OBJECTIVE_OF]->(p1)
                RETURN p1.name as level1, collect(p2.name) as level2_list
                """
                results = self.graph.query(query, params={'objective_level1': objective_level1})
                if results:
                    return {
                        'level1': results[0]['level1'],
                        'level2_list': results[0]['level2_list']
                    }
                return {'error': '未找到指定的一级公关目标'}
            else:
                # 获取所有公关目标层级关系
                query = """
                MATCH (p1:PRObjectiveLevel1)
                OPTIONAL MATCH (p2:PRObjectiveLevel2)-[:SUB_OBJECTIVE_OF]->(p1)
                RETURN p1.name as level1, collect(p2.name) as level2_list
                """
                results = self.graph.query(query)
                hierarchy = {}
                for record in results:
                    hierarchy[record['level1']] = record['level2_list']
                return hierarchy
        except Exception as e:
            return {'error': f"获取公关目标层级关系失败: {e}"}
    
    def create_visualization_style_sheet(self) -> str:
        """创建用于Neo4j Browser可视化的样式表"""
        style_sheet = """
        /* 节点样式 - 确保不同层级有明显的视觉区分 */
        node.IndustryLevel1 {
          size: 25;
          color: #1F77B4;
          border-color: #000000;
          border-width: 2px;
          caption: '{name}';
          font-size: 14px;
          font-weight: bold;
        }
        
        node.IndustryLevel2 {
          size: 18;
          color: #4DAF4A;
          border-color: #000000;
          border-width: 1px;
          caption: '{name}';
          font-size: 12px;
        }
        
        node.PRObjectiveLevel1 {
          size: 23;
          color: #FF6384;
          border-color: #000000;
          border-width: 2px;
          caption: '{name}';
          font-size: 13px;
          font-weight: bold;
          shape: rectangle;
        }
        
        node.PRObjectiveLevel2 {
          size: 16;
          color: #FFCE56;
          border-color: #000000;
          border-width: 1px;
          caption: '{name}';
          font-size: 11px;
          shape: rectangle;
        }
        
        node.Brand {
          size: 12;
          color: #FF7F50;
          border-color: #000000;
          border-width: 1px;
          caption: '{name}';
          font-size: 10px;
          shape: ellipse;
        }
        
        node.CommunicationChannel {
          size: 10;
          color: #9467BD;
          border-color: #000000;
          border-width: 1px;
          caption: '{name}';
          font-size: 9px;
          shape: hexagon;
        }
        
        /* 关系样式 */
        relationship.SUB_INDUSTRY_OF {
          color: #000000;
          width: 2px;
          caption: '属于';
          font-size: 8px;
        }
        
        relationship.SUB_OBJECTIVE_OF {
          color: #FF6384;
          width: 2px;
          caption: '属于';
          font-size: 8px;
        }
        
        relationship.IN_PRIMARY_INDUSTRY {
          color: #1F77B4;
          width: 1.5px;
          caption: '主要行业';
          font-size: 8px;
        }
        
        relationship.IN_SECONDARY_INDUSTRY {
          color: #4DAF4A;
          width: 1px;
          caption: '次要行业';
          font-size: 8px;
          style: dashed;
        }
        """
        return style_sheet
    
    def apply_visualization_styles(self) -> bool:
        """应用可视化样式到Neo4j数据库中的所有现有节点"""
        if not self.graph:
            return False
        
        try:
            # 创建并应用样式表
            style_sheet = self.create_visualization_style_sheet()
            # 注意：Neo4j的Style Manager API需要通过特定的过程调用来应用样式
            # 这里使用apoc程序来更新样式，如果没有安装apoc插件，这一步会失败
            try:
                query = """
                CALL apoc.style.set('default', $style_sheet)
                YIELD value
                RETURN value
                """
                self.graph.query(query, params={'style_sheet': style_sheet})
            except Exception:
                # 如果apoc不可用，记录但不抛出异常
                print("警告: 无法应用Neo4j样式到浏览器界面，可能需要安装APOC插件")
            
            # 确保所有一级行业节点都有必要的视觉属性
            level1_query = """
            MATCH (i:IndustryLevel1)
            SET i.visual_category = 'industry_level1',
                i.visual_size = 25,
                i.visual_color = '#1F77B4',
                i.node_label = '一级行业'
            """
            self.graph.query(level1_query)
            
            # 确保所有二级行业节点都有必要的视觉属性
            level2_query = """
            MATCH (i:IndustryLevel2)
            SET i.visual_category = 'industry_level2',
                i.visual_size = 18,
                i.visual_color = '#4DAF4A',
                i.node_label = '二级行业'
            """
            self.graph.query(level2_query)
            
            # 确保所有品牌节点都有必要的视觉属性
            brand_query = """
            MATCH (b:Brand)
            SET b.visual_category = 'brand',
                b.visual_size = 12,
                b.visual_color = '#FF7F50',
                b.node_label = '品牌'
            """
            self.graph.query(brand_query)
            
            # 确保所有一级公关目标节点都有必要的视觉属性
            objective_level1_query = """
            MATCH (p:PRObjectiveLevel1)
            SET p.visual_category = 'pr_objective_level1',
                p.visual_size = 23,
                p.visual_color = '#FF6384',
                p.node_label = '一级公关目标'
            """
            self.graph.query(objective_level1_query)
            
            # 确保所有二级公关目标节点都有必要的视觉属性
            objective_level2_query = """
            MATCH (p:PRObjectiveLevel2)
            SET p.visual_category = 'pr_objective_level2',
                p.visual_size = 16,
                p.visual_color = '#FFCE56',
                p.node_label = '二级公关目标'
            """
            self.graph.query(objective_level2_query)
            
            return True
        except Exception as e:
            print(f"应用可视化样式失败: {e}")
            return False


def test_pr_case_relationship_manager():
    """测试公关案例关系管理器"""
    print("开始测试公关案例关系管理器...")
    manager = PRCaseRelationshipManager()
    
    # 测试可视化样式应用
    print("应用可视化样式...")
    manager.apply_visualization_styles()
    
    # 测试公关目标层级查询（如果有数据的话）
    print("\n测试公关目标层级查询...")
    objective_hierarchy = manager.get_pr_objective_hierarchy()
    if isinstance(objective_hierarchy, dict) and 'error' not in objective_hierarchy:
        print(f"公关目标层级数量: {len(objective_hierarchy)}")
        print("公关目标层级列表:")
        for level1, level2_list in objective_hierarchy.items():
            print(f"  - {level1}: {len(level2_list)}个二级目标")
    else:
        print("没有找到公关目标数据或查询失败")
    
    # 测试传播渠道层级查询（如果有数据的话）
    print("\n测试传播渠道层级查询...")
    channel_hierarchy = manager.get_communication_channel_hierarchy()
    if isinstance(channel_hierarchy, dict) and 'error' not in channel_hierarchy:
        print(f"传播渠道一级分类数量: {len(channel_hierarchy)}")
        print("传播渠道层级结构:")
        for level1, level2_list in channel_hierarchy.items():
            print(f"  - {level1}:")
            for level2_item in level2_list:
                level3_count = len(level2_item.get('level3_list', []))
                print(f"    - {level2_item['level2']}: {level3_count}个三级渠道")
    else:
        print("没有找到传播渠道数据或查询失败")
    
    # 打印示例使用方法
    print("\n使用说明:")
    print("1. 导入行业与品牌关系表:")
    print("   manager = PRCaseRelationshipManager()")
    print("   result = manager.import_industry_brand_relationship_from_excel('data/pr_cases/公关案例库_行业与品牌关系表.xlsx')")
    print("   print(result)")
    print("\n2. 导入公关目标关系表:")
    print("   manager = PRCaseRelationshipManager()")
    print("   result = manager.import_pr_objectives_from_excel('data/pr_cases/公关案例库_公关目标关系表.xlsx')")
    print("   print(result)")
    print("\n3. 导入传播渠道关系表:")
    print("   manager = PRCaseRelationshipManager()")
    print("   result = manager.import_communication_channels_from_excel('data/pr_cases/传播渠道关系表.xlsx')")
    print("   print(result)")
    print("\n4. 获取行业层级关系:")
    print("   hierarchy = manager.get_industry_hierarchy()")
    print("   print(hierarchy)")
    print("\n5. 获取公关目标层级关系:")
    print("   hierarchy = manager.get_pr_objective_hierarchy()")
    print("   print(hierarchy)")
    print("\n6. 获取传播渠道层级关系:")
    print("   hierarchy = manager.get_communication_channel_hierarchy()")
    print("   print(hierarchy)")
    print("\n7. 根据一级传播渠道获取层级:")
    print("   hierarchy = manager.get_communication_channel_hierarchy('社交媒体')")
    print("   print(hierarchy)")
    print("\n8. 根据行业获取品牌:")
    print("   brands = manager.get_brands_by_industry('科技', industry_level=1)")
    print("   brands")
    print("\n9. 获取品牌所属行业:")
    print("   industries = manager.get_brand_industries('苹果')")
    print("   print(industries)")
    
    print("\n测试完成！")


def main():
    """GraphSyncer 的主函数"""
    parser = argparse.ArgumentParser(description="Sync case library CSV into Neo4j.")
    parser.add_argument("--base-dir", default="data/reference", help="CSV文件所在的目录路径（默认: data/reference）")
    args = parser.parse_args()

    # 确保路径存在
    if not os.path.exists(args.base_dir):
        print(f"❌ 错误: 目录不存在: {args.base_dir}")
        print(f"💡 提示: 请确保 CSV 文件在 {args.base_dir} 目录下")
        return
    
    syncer = GraphSyncer(args.base_dir)

    print("=== 开始全量同步 ===")
    
    # 步骤顺序非常重要：
    # 必须先建立层级骨架（渠道、目标、行业），再导入案例填充血肉。
    syncer.sync_channels()
    syncer.sync_goals()
    syncer.sync_industries()
    syncer.sync_cases()
    
    print("=== ✅ 所有同步任务完成 ===")


if __name__ == "__main__":
    main()
