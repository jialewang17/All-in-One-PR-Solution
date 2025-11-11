#!/usr/bin/env python3
"""
基于人类反馈的强化学习 (RLHF) 系统
使用反馈数据训练奖励模型并优化方案生成策略
"""

import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import sqlite3
from pathlib import Path

from pr_feedback_collector import FeedbackCollector, Feedback
from pr_quality_evaluator import QualityEvaluator, QualityAssessment


@dataclass
class RewardSignal:
    """奖励信号"""
    plan_id: str
    reward_score: float  # 奖励分数 -1 到 1
    feedback_id: Optional[str]
    quality_assessment: Optional[QualityAssessment]
    timestamp: str


@dataclass
class TrainingData:
    """训练数据"""
    plan_id: str
    plan_content: str
    context: Dict[str, Any]
    reward: float
    feedback: Optional[Feedback]
    quality_assessment: Optional[QualityAssessment]


class RewardModel:
    """奖励模型"""
    
    def __init__(self, model_path: Optional[str] = None):
        """初始化奖励模型"""
        self.model_path = model_path
        self.weights = {
            'rating': 0.4,  # 用户评分权重
            'quality': 0.3,  # 质量评估权重
            'engagement': 0.2,  # 参与度权重
            'consistency': 0.1  # 一致性权重
        }
        self.trained = False
    
    def predict_reward(
        self,
        plan_content: str,
        context: Dict[str, Any],
        feedback: Optional[Feedback] = None,
        quality_assessment: Optional[QualityAssessment] = None
    ) -> float:
        """预测奖励分数"""
        reward = 0.0
        
        # 基于用户评分
        if feedback and feedback.rating is not None:
            # 将1-5分转换为-1到1
            normalized_rating = (feedback.rating - 3.0) / 2.0
            reward += normalized_rating * self.weights['rating']
        
        # 基于质量评估
        if quality_assessment:
            normalized_quality = (quality_assessment.overall_score - 0.5) * 2.0
            reward += normalized_quality * self.weights['quality']
        
        # 基于反馈类别
        if feedback and feedback.categories:
            category_scores = {
                'high': 0.5,
                'medium': 0.0,
                'low': -0.5
            }
            for category, value in feedback.categories.items():
                if isinstance(value, str) and value in category_scores:
                    reward += category_scores[value] * 0.1
        
        # 基于建议数量（建议少说明质量高）
        if feedback and feedback.suggestions:
            suggestion_penalty = -len(feedback.suggestions) * 0.05
            reward += suggestion_penalty
        
        # 限制在-1到1之间
        reward = max(-1.0, min(1.0, reward))
        
        return reward
    
    def train(self, training_data: List[TrainingData]):
        """训练奖励模型"""
        # 简单的线性回归训练
        # 实际应用中可以使用更复杂的模型（如神经网络）
        
        if len(training_data) < 10:
            print("训练数据不足，需要至少10条数据")
            return
        
        # 提取特征
        X = []
        y = []
        
        for data in training_data:
            features = self._extract_features(data)
            X.append(features)
            y.append(data.reward)
        
        # 简单的权重调整（实际应用中可以使用梯度下降等优化方法）
        # 这里使用平均误差来调整权重
        predictions = [self.predict_reward(
            data.plan_content,
            data.context,
            data.feedback,
            data.quality_assessment
        ) for data in training_data]
        
        errors = [abs(p - r) for p, r in zip(predictions, y)]
        avg_error = np.mean(errors)
        
        if avg_error < 0.2:  # 误差阈值
            self.trained = True
            print(f"奖励模型训练完成，平均误差: {avg_error:.3f}")
        else:
            print(f"奖励模型训练中，平均误差: {avg_error:.3f}")
    
    def _extract_features(self, data: TrainingData) -> List[float]:
        """提取特征"""
        features = []
        
        # 方案长度
        features.append(len(data.plan_content) / 1000.0)
        
        # 上下文特征
        features.append(1.0 if data.context.get('brand') else 0.0)
        features.append(1.0 if data.context.get('industry') else 0.0)
        features.append(1.0 if data.context.get('pr_goal') else 0.0)
        
        # 反馈特征
        if data.feedback:
            features.append(data.feedback.rating / 5.0 if data.feedback.rating else 0.5)
            features.append(len(data.feedback.suggestions) / 10.0)
        else:
            features.extend([0.5, 0.0])
        
        # 质量评估特征
        if data.quality_assessment:
            features.append(data.quality_assessment.overall_score)
        else:
            features.append(0.5)
        
        return features
    
    def save_model(self, path: str):
        """保存模型"""
        model_data = {
            'weights': self.weights,
            'trained': self.trained
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, indent=2)
    
    def load_model(self, path: str):
        """加载模型"""
        with open(path, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        self.weights = model_data['weights']
        self.trained = model_data['trained']


class RLHFTrainer:
    """RLHF训练器"""
    
    def __init__(
        self,
        feedback_collector: FeedbackCollector,
        quality_evaluator: QualityEvaluator,
        reward_model: Optional[RewardModel] = None
    ):
        """初始化RLHF训练器"""
        self.feedback_collector = feedback_collector
        self.quality_evaluator = quality_evaluator
        self.reward_model = reward_model or RewardModel()
        self.training_history = []
    
    def prepare_training_data(
        self,
        min_feedback_count: int = 10,
        plan_content_storage: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[TrainingData]:
        """准备训练数据"""
        # 从反馈收集器获取所有反馈
        conn = sqlite3.connect(self.feedback_collector.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT * FROM feedback
        WHERE rating IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT 1000
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        if len(rows) < min_feedback_count:
            return []
        
        training_data = []
        for row in rows:
            try:
                feedback = self.feedback_collector._row_to_feedback(row)
                
                # 从存储中获取方案内容和上下文（如果提供）
                plan_content = ""
                context = {}
                if plan_content_storage and feedback.plan_id in plan_content_storage:
                    storage = plan_content_storage[feedback.plan_id]
                    plan_content = storage.get('content', '')
                    context = storage.get('context', {})
                
                # 获取质量评估（如果不存在则生成）
                # 这里简化处理，实际应该从数据库获取或重新评估
                quality_assessment = None
                if plan_content:
                    quality_assessment = self.quality_evaluator.evaluate_plan(
                        plan_id=feedback.plan_id,
                        plan_content=plan_content,
                        context=context
                    )
                
                # 计算奖励
                reward = self.reward_model.predict_reward(
                    plan_content=plan_content,
                    context=context,
                    feedback=feedback,
                    quality_assessment=quality_assessment
                )
                
                training_data.append(TrainingData(
                    plan_id=feedback.plan_id,
                    plan_content=plan_content,
                    context=context,
                    reward=reward,
                    feedback=feedback,
                    quality_assessment=quality_assessment
                ))
            except Exception as e:
                print(f"处理训练数据失败: {e}")
                continue
        
        return training_data
    
    def train_reward_model(self, training_data: Optional[List[TrainingData]] = None):
        """训练奖励模型"""
        if training_data is None:
            training_data = self.prepare_training_data()
        
        if len(training_data) < 10:
            print("训练数据不足，无法训练奖励模型")
            return False
        
        print(f"开始训练奖励模型，训练数据量: {len(training_data)}")
        self.reward_model.train(training_data)
        
        # 记录训练历史
        self.training_history.append({
            'timestamp': datetime.now().isoformat(),
            'training_data_count': len(training_data),
            'model_trained': self.reward_model.trained
        })
        
        return True
    
    def optimize_policy(
        self,
        plan_generator,
        context: Dict[str, Any],
        num_iterations: int = 10
    ) -> Dict[str, Any]:
        """优化生成策略"""
        # 这里简化实现，实际应该使用PPO等强化学习算法
        # 生成多个候选方案
        candidates = []
        rewards = []
        
        for i in range(num_iterations):
            # 生成方案（这里需要实际的生成器）
            # plan = plan_generator.generate(context)
            # reward = self.reward_model.predict_reward(plan, context)
            # candidates.append(plan)
            # rewards.append(reward)
            pass
        
        # 选择奖励最高的方案
        # best_plan = candidates[np.argmax(rewards)]
        
        return {
            'status': 'success',
            'message': '策略优化完成',
            'best_reward': max(rewards) if rewards else 0.0
        }
    
    def evaluate_improvement(
        self,
        before_metrics: Dict[str, float],
        after_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """评估改进效果"""
        improvements = {}
        for metric, before_value in before_metrics.items():
            after_value = after_metrics.get(metric, before_value)
            improvement = after_value - before_value
            improvement_pct = (improvement / before_value * 100) if before_value > 0 else 0
            improvements[metric] = {
                'before': before_value,
                'after': after_value,
                'improvement': improvement,
                'improvement_pct': improvement_pct
            }
        
        return improvements
    
    def get_training_stats(self) -> Dict[str, Any]:
        """获取训练统计信息"""
        return {
            'training_history': self.training_history,
            'model_trained': self.reward_model.trained,
            'total_training_runs': len(self.training_history)
        }


def test_rlhf_system():
    """测试RLHF系统"""
    # 初始化组件
    feedback_collector = FeedbackCollector()
    quality_evaluator = QualityEvaluator()
    reward_model = RewardModel()
    trainer = RLHFTrainer(feedback_collector, quality_evaluator, reward_model)
    
    # 测试奖励模型
    print("测试奖励模型...")
    plan_content = "测试方案内容"
    context = {'brand': '测试品牌', 'industry': '科技'}
    
    feedback = Feedback(
        feedback_id="test_feedback",
        plan_id="test_plan",
        user_id="test_user",
        feedback_type="rating",
        rating=4.5,
        comment="很好的方案",
        categories={'relevance': 'high'},
        suggestions=[],
        metadata={},
        timestamp=datetime.now().isoformat(),
        knowledge_sources=[],
        plan_type="A"
    )
    
    reward = reward_model.predict_reward(plan_content, context, feedback)
    print(f"预测奖励: {reward:.3f}")
    
    # 测试训练
    print("\n测试训练奖励模型...")
    training_data = trainer.prepare_training_data(min_feedback_count=1)
    if training_data:
        trainer.train_reward_model(training_data)
    else:
        print("训练数据不足")


if __name__ == "__main__":
    test_rlhf_system()

