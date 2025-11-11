#!/usr/bin/env python3
"""
方案质量评估系统
自动和人工评估生成方案的质量
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class QualityMetric(Enum):
    """质量评估指标"""
    RELEVANCE = "relevance"  # 相关性
    INNOVATION = "innovation"  # 创新性
    FEASIBILITY = "feasibility"  # 可行性
    COMPLETENESS = "completeness"  # 完整性
    CONSISTENCY = "consistency"  # 一致性
    PROFESSIONALISM = "professionalism"  # 专业性


@dataclass
class QualityScore:
    """质量评分"""
    metric: str
    score: float  # 0-1
    weight: float  # 权重
    explanation: str  # 评分说明


@dataclass
class QualityAssessment:
    """质量评估结果"""
    plan_id: str
    overall_score: float  # 总体评分 0-1
    metric_scores: List[QualityScore]  # 各项指标评分
    assessment_type: str  # automatic or human
    assessor_id: Optional[str]  # 评估者ID
    timestamp: str
    comments: Optional[str]  # 评估意见
    improvements: List[str]  # 改进建议


class QualityEvaluator:
    """质量评估器"""
    
    def __init__(self):
        """初始化质量评估器"""
        self.metric_weights = {
            'relevance': 0.25,
            'innovation': 0.20,
            'feasibility': 0.20,
            'completeness': 0.15,
            'consistency': 0.10,
            'professionalism': 0.10
        }
    
    def evaluate_plan(
        self,
        plan_id: str,
        plan_content: str,
        context: Dict[str, Any],
        assessment_type: str = 'automatic'
    ) -> QualityAssessment:
        """评估方案质量"""
        metric_scores = []
        
        # 评估各项指标
        for metric in QualityMetric:
            score = self._evaluate_metric(
                metric.value,
                plan_content,
                context
            )
            metric_scores.append(score)
        
        # 计算总体评分
        overall_score = sum(
            score.score * score.weight for score in metric_scores
        )
        
        # 生成改进建议
        improvements = self._generate_improvements(metric_scores, plan_content, context)
        
        return QualityAssessment(
            plan_id=plan_id,
            overall_score=overall_score,
            metric_scores=metric_scores,
            assessment_type=assessment_type,
            assessor_id=None,
            timestamp=datetime.now().isoformat(),
            comments=None,
            improvements=improvements
        )
    
    def _evaluate_metric(
        self,
        metric: str,
        plan_content: str,
        context: Dict[str, Any]
    ) -> QualityScore:
        """评估单个指标"""
        weight = self.metric_weights.get(metric, 0.1)
        
        if metric == 'relevance':
            score, explanation = self._evaluate_relevance(plan_content, context)
        elif metric == 'innovation':
            score, explanation = self._evaluate_innovation(plan_content, context)
        elif metric == 'feasibility':
            score, explanation = self._evaluate_feasibility(plan_content, context)
        elif metric == 'completeness':
            score, explanation = self._evaluate_completeness(plan_content, context)
        elif metric == 'consistency':
            score, explanation = self._evaluate_consistency(plan_content, context)
        elif metric == 'professionalism':
            score, explanation = self._evaluate_professionalism(plan_content, context)
        else:
            score, explanation = 0.5, "未定义的指标"
        
        return QualityScore(
            metric=metric,
            score=score,
            weight=weight,
            explanation=explanation
        )
    
    def _evaluate_relevance(self, plan_content: str, context: Dict[str, Any]) -> tuple:
        """评估相关性"""
        # 检查方案是否与品牌、目标相关
        brand = context.get('brand', '')
        pr_goal = context.get('pr_goal', '')
        industry = context.get('industry', '')
        
        relevance_score = 0.5
        explanation_parts = []
        
        # 检查品牌提及
        if brand and brand in plan_content:
            relevance_score += 0.2
            explanation_parts.append(f"方案提到了品牌 {brand}")
        else:
            explanation_parts.append(f"方案未明确提到品牌 {brand}")
        
        # 检查目标相关性
        if pr_goal:
            goal_keywords = {
                '品牌认知': ['认知', '知名度', '曝光', '传播'],
                '用户增长': ['用户', '增长', '获客', '转化'],
                '危机公关': ['危机', '应对', '处理', '修复']
            }
            keywords = goal_keywords.get(pr_goal, [])
            if any(kw in plan_content for kw in keywords):
                relevance_score += 0.2
                explanation_parts.append(f"方案与目标 '{pr_goal}' 相关")
            else:
                explanation_parts.append(f"方案与目标 '{pr_goal}' 相关性不足")
        
        # 检查行业相关性
        if industry and industry in plan_content:
            relevance_score += 0.1
            explanation_parts.append(f"方案考虑了行业特点")
        
        score = min(relevance_score, 1.0)
        explanation = "; ".join(explanation_parts)
        
        return score, explanation
    
    def _evaluate_innovation(self, plan_content: str, context: Dict[str, Any]) -> tuple:
        """评估创新性"""
        # 检查是否包含创新元素
        innovation_keywords = [
            '创新', '新颖', '独特', '突破', '差异化',
            '创意', '新玩法', '新模式', '新渠道'
        ]
        
        innovation_count = sum(1 for kw in innovation_keywords if kw in plan_content)
        score = min(innovation_count * 0.15 + 0.3, 1.0)
        
        explanation = f"方案包含 {innovation_count} 个创新相关关键词"
        
        return score, explanation
    
    def _evaluate_feasibility(self, plan_content: str, context: Dict[str, Any]) -> tuple:
        """评估可行性"""
        # 检查是否包含具体可执行的步骤
        feasibility_indicators = [
            '步骤', '流程', '时间', '预算', '资源',
            '实施', '执行', '操作', '方法', '策略'
        ]
        
        indicator_count = sum(1 for ind in feasibility_indicators if ind in plan_content)
        score = min(indicator_count * 0.1 + 0.4, 1.0)
        
        # 检查是否有预算和时间信息
        if '预算' in plan_content or '成本' in plan_content:
            score += 0.1
        if '时间' in plan_content or '周期' in plan_content:
            score += 0.1
        
        score = min(score, 1.0)
        explanation = f"方案包含 {indicator_count} 个可行性指标"
        
        return score, explanation
    
    def _evaluate_completeness(self, plan_content: str, context: Dict[str, Any]) -> tuple:
        """评估完整性"""
        # 检查方案是否包含必要组成部分
        required_sections = [
            '目标', '策略', '渠道', '内容', '时间', '预算'
        ]
        
        section_count = sum(1 for section in required_sections if section in plan_content)
        score = min(section_count / len(required_sections), 1.0)
        
        explanation = f"方案包含 {section_count}/{len(required_sections)} 个必要部分"
        
        return score, explanation
    
    def _evaluate_consistency(self, plan_content: str, context: Dict[str, Any]) -> tuple:
        """评估一致性"""
        # 检查方案内部是否一致
        # 简单检查：内容长度和结构
        score = 0.7  # 默认分数
        
        # 检查是否有矛盾的关键词
        contradictions = [
            ('保守', '激进'),
            ('低成本', '高预算'),
            ('短期', '长期')
        ]
        
        contradiction_count = 0
        for neg, pos in contradictions:
            if (neg in plan_content and pos in plan_content):
                contradiction_count += 1
        
        if contradiction_count == 0:
            score = 0.8
            explanation = "方案内部一致性良好"
        else:
            score = max(0.5 - contradiction_count * 0.1, 0.3)
            explanation = f"方案存在 {contradiction_count} 处可能的不一致"
        
        return score, explanation
    
    def _evaluate_professionalism(self, plan_content: str, context: Dict[str, Any]) -> tuple:
        """评估专业性"""
        # 检查专业术语和结构
        professional_keywords = [
            '策略', '方案', '执行', '评估', 'KPI', 'ROI',
            '目标受众', '传播渠道', '内容营销', '品牌传播'
        ]
        
        keyword_count = sum(1 for kw in professional_keywords if kw in plan_content)
        score = min(keyword_count * 0.1 + 0.5, 1.0)
        
        # 检查内容长度
        if len(plan_content) > 500:
            score += 0.1
        
        score = min(score, 1.0)
        explanation = f"方案使用了 {keyword_count} 个专业术语"
        
        return score, explanation
    
    def _generate_improvements(
        self,
        metric_scores: List[QualityScore],
        plan_content: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """生成改进建议"""
        improvements = []
        
        # 找出评分较低的指标
        low_scores = [ms for ms in metric_scores if ms.score < 0.6]
        
        for score in low_scores:
            if score.metric == 'relevance':
                improvements.append("增强方案与品牌和目标的相关性")
            elif score.metric == 'innovation':
                improvements.append("增加创新元素和差异化策略")
            elif score.metric == 'feasibility':
                improvements.append("提供更具体的实施步骤和资源需求")
            elif score.metric == 'completeness':
                improvements.append("补充缺失的方案组成部分")
            elif score.metric == 'consistency':
                improvements.append("检查并修正方案中的不一致之处")
            elif score.metric == 'professionalism':
                improvements.append("使用更多专业术语和行业标准")
        
        return improvements
    
    def human_evaluate_plan(
        self,
        plan_id: str,
        metric_scores: Dict[str, float],
        overall_score: float,
        comments: Optional[str] = None,
        improvements: Optional[List[str]] = None,
        assessor_id: Optional[str] = None
    ) -> QualityAssessment:
        """人工评估方案"""
        quality_scores = [
            QualityScore(
                metric=metric,
                score=score,
                weight=self.metric_weights.get(metric, 0.1),
                explanation="人工评估"
            )
            for metric, score in metric_scores.items()
        ]
        
        return QualityAssessment(
            plan_id=plan_id,
            overall_score=overall_score,
            metric_scores=quality_scores,
            assessment_type='human',
            assessor_id=assessor_id,
            timestamp=datetime.now().isoformat(),
            comments=comments,
            improvements=improvements or []
        )


def test_quality_evaluator():
    """测试质量评估器"""
    evaluator = QualityEvaluator()
    
    # 测试方案
    plan_content = """
    品牌传播方案
    目标：提升品牌认知度
    策略：通过社交媒体和内容营销提升品牌曝光
    渠道：微信、微博、抖音
    内容：发布品牌故事和产品介绍
    时间：3个月
    预算：100万
    """
    
    context = {
        'brand': '测试品牌',
        'industry': '科技',
        'pr_goal': '品牌认知'
    }
    
    # 测试自动评估
    print("测试自动评估...")
    assessment = evaluator.evaluate_plan(
        plan_id="plan_001",
        plan_content=plan_content,
        context=context
    )
    
    print(f"总体评分: {assessment.overall_score:.2f}")
    print("\n各项指标评分:")
    for score in assessment.metric_scores:
        print(f"  {score.metric}: {score.score:.2f} - {score.explanation}")
    
    print("\n改进建议:")
    for improvement in assessment.improvements:
        print(f"  - {improvement}")


if __name__ == "__main__":
    test_quality_evaluator()


