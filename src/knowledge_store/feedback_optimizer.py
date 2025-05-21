"""
反馈优化器模块
功能：基于用户反馈动态调整知识质量和模型权重
"""

import json
import logging
import datetime
from collections import defaultdict

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FeedbackOptimizer:
    def __init__(self, matching_matrix, knowledge_repository):
        """
        初始化反馈优化器
        
        参数:
            matching_matrix: 三维匹配矩阵实例
            knowledge_repository: 知识库实例
        """
        self.matching_matrix = matching_matrix
        self.knowledge_repository = knowledge_repository
        
        # 反馈类型权重
        self.feedback_weights = {
            "explicit": 0.7,  # 显性评分权重
            "implicit": 0.3   # 隐性行为权重
        }
        
        # 隐性行为评分映射
        self.implicit_score_mapping = {
            "click": 0.6,           # 点击继续阅读
            "copy": 0.7,            # 复制内容
            "share": 0.8,           # 分享内容
            "bookmark": 0.9,         # 收藏内容
            "follow_recommendation": 0.8,  # 采纳建议
            "ignore": 0.3,          # 忽略内容
            "quick_exit": 0.2       # 快速退出
        }
        
        # 反馈历史记录
        self.feedback_history = []
        
        # 模型性能统计
        self.model_performance = defaultdict(lambda: {
            "total_queries": 0,
            "positive_feedback": 0,
            "negative_feedback": 0,
            "avg_score": 0.0
        })
        
        logger.info("反馈优化器初始化完成")
    
    def process_explicit_feedback(self, knowledge_id, user_id, score, comment=None, intent_data=None):
        """
        处理显性用户反馈（评分、点赞等）
        
        参数:
            knowledge_id (str): 知识项ID
            user_id (str): 用户ID
            score (float): 反馈评分 (0-1)
            comment (str, optional): 反馈评论
            intent_data (dict, optional): 意图解析数据
            
        返回:
            bool: 处理是否成功
        """
        try:
            # 记录反馈
            feedback_record = {
                "type": "explicit",
                "knowledge_id": knowledge_id,
                "user_id": user_id,
                "score": score,
                "comment": comment,
                "timestamp": datetime.datetime.now().isoformat()
            }
            self.feedback_history.append(feedback_record)
            
            # 更新知识库中的反馈
            success = self.knowledge_repository.update_feedback(knowledge_id, user_id, score, comment)
            
            # 如果提供了意图数据，更新匹配矩阵
            if intent_data and success:
                # 获取知识项详情
                results = self.knowledge_repository.retrieve_by_id(knowledge_id)
                if results:
                    knowledge_item = results[0]
                    domain = knowledge_item.get("domain") or intent_data.get("domain", "通用医学")
                    intent_type = knowledge_item.get("intent_type") or intent_data.get("intent_type", "诊断咨询")
                    model = knowledge_item.get("metadata", {}).get("model", "通用医学模型")
                    
                    # 更新匹配矩阵中的模型可信度
                    self.matching_matrix.update_confidence(domain, intent_type, model, score)
                    
                    # 更新模型性能统计
                    self.model_performance[model]["total_queries"] += 1
                    if score >= 0.6:
                        self.model_performance[model]["positive_feedback"] += 1
                    else:
                        self.model_performance[model]["negative_feedback"] += 1
                    
                    # 更新平均分
                    total = self.model_performance[model]["positive_feedback"] + self.model_performance[model]["negative_feedback"]
                    if total > 0:
                        self.model_performance[model]["avg_score"] = (
                            self.model_performance[model]["positive_feedback"] / total
                        )
            
            logger.info(f"处理显性反馈 - 知识项: {knowledge_id}, 评分: {score}, 更新状态: {'成功' if success else '失败'}")
            
            return success
        except Exception as e:
            logger.error(f"处理显性反馈失败: {e}")
            return False
    
    def process_implicit_feedback(self, knowledge_id, user_id, behavior, intent_data=None):
        """
        处理隐性用户反馈（点击、复制、分享等行为）
        
        参数:
            knowledge_id (str): 知识项ID
            user_id (str): 用户ID
            behavior (str): 用户行为类型
            intent_data (dict, optional): 意图解析数据
            
        返回:
            bool: 处理是否成功
        """
        try:
            # 将行为映射为评分
            if behavior in self.implicit_score_mapping:
                implicit_score = self.implicit_score_mapping[behavior]
            else:
                implicit_score = 0.5  # 默认中性评分
            
            # 记录反馈
            feedback_record = {
                "type": "implicit",
                "knowledge_id": knowledge_id,
                "user_id": user_id,
                "behavior": behavior,
                "implicit_score": implicit_score,
                "timestamp": datetime.datetime.now().isoformat()
            }
            self.feedback_history.append(feedback_record)
            
            # 应用隐性反馈权重
            weighted_score = implicit_score * self.feedback_weights["implicit"]
            
            # 更新知识库中的反馈（权重较低）
            success = self.knowledge_repository.update_feedback(
                knowledge_id, user_id, weighted_score, f"隐性反馈: {behavior}"
            )
            
            # 如果提供了意图数据，更新匹配矩阵（权重较低）
            if intent_data and success:
                # 获取知识项详情
                results = self.knowledge_repository.retrieve_by_id(knowledge_id)
                if results:
                    knowledge_item = results[0]
                    domain = knowledge_item.get("domain") or intent_data.get("domain", "通用医学")
                    intent_type = knowledge_item.get("intent_type") or intent_data.get("intent_type", "诊断咨询")
                    model = knowledge_item.get("metadata", {}).get("model", "通用医学模型")
                    
                    # 更新匹配矩阵中的模型可信度（权重较低）
                    self.matching_matrix.update_confidence(
                        domain, intent_type, model, weighted_score
                    )
            
            logger.info(f"处理隐性反馈 - 知识项: {knowledge_id}, 行为: {behavior}, 隐性评分: {implicit_score:.2f}")
            
            return success
        except Exception as e:
            logger.error(f"处理隐性反馈失败: {e}")
            return False
    
    def analyze_feedback_trends(self, days=30):
        """
        分析反馈趋势
        
        参数:
            days (int): 分析的天数范围
            
        返回:
            dict: 趋势分析结果
        """
        try:
            # 计算起始时间
            start_time = datetime.datetime.now() - datetime.timedelta(days=days)
            start_time_str = start_time.isoformat()
            
            # 过滤时间范围内的反馈
            recent_feedback = [
                f for f in self.feedback_history 
                if f["timestamp"] >= start_time_str
            ]
            
            if not recent_feedback:
                return {"status": "no_data", "message": "没有足够的反馈数据进行分析"}
            
            # 按日期分组
            daily_feedback = defaultdict(list)
            for feedback in recent_feedback:
                date = feedback["timestamp"].split("T")[0]
                daily_feedback[date].append(feedback)
            
            # 计算每日平均分
            daily_scores = {}
            for date, feedbacks in daily_feedback.items():
                total_score = sum(f["score"] if "score" in f else f.get("implicit_score", 0.5) for f in feedbacks)
                daily_scores[date] = total_score / len(feedbacks)
            
            # 按模型分组
            model_feedback = defaultdict(list)
            for feedback in recent_feedback:
                if "knowledge_id" in feedback:
                    # 获取知识项详情
                    results = self.knowledge_repository.retrieve_by_id(feedback["knowledge_id"])
                    if results:
                        knowledge_item = results[0]
                        model = knowledge_item.get("metadata", {}).get("model", "通用医学模型")
                        model_feedback[model].append(feedback)
            
            # 计算每个模型的平均分
            model_scores = {}
            for model, feedbacks in model_feedback.items():
                total_score = sum(f["score"] if "score" in f else f.get("implicit_score", 0.5) for f in feedbacks)
                model_scores[model] = total_score / len(feedbacks)
            
            # 按领域分组
            domain_feedback = defaultdict(list)
            for feedback in recent_feedback:
                if "knowledge_id" in feedback:
                    # 获取知识项详情
                    results = self.knowledge_repository.retrieve_by_id(feedback["knowledge_id"])
                    if results:
                        knowledge_item = results[0]
                        domain = knowledge_item.get("domain", "通用医学")
                        domain_feedback[domain].append(feedback)
            
            # 计算每个领域的平均分
            domain_scores = {}
            for domain, feedbacks in domain_feedback.items():
                total_score = sum(f["score"] if "score" in f else f.get("implicit_score", 0.5) for f in feedbacks)
                domain_scores[domain] = total_score / len(feedbacks)
            
            # 分析结果
            analysis = {
                "status": "success",
                "total_feedback": len(recent_feedback),
                "explicit_feedback": sum(1 for f in recent_feedback if f["type"] == "explicit"),
                "implicit_feedback": sum(1 for f in recent_feedback if f["type"] == "implicit"),
                "daily_scores": daily_scores,
                "model_scores": model_scores,
                "domain_scores": domain_scores,
                "overall_score": sum(score for score in daily_scores.values()) / len(daily_scores)
            }
            
            logger.info(f"反馈趋势分析完成 - 总反馈数: {analysis['total_feedback']}, 整体评分: {analysis['overall_score']:.2f}")
            
            return analysis
        except Exception as e:
            logger.error(f"分析反馈趋势失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def optimize_model_weights(self):
        """
        基于反馈优化模型权重
        
        返回:
            bool: 优化是否成功
        """
        try:
            # 获取模型性能统计
            model_stats = dict(self.model_performance)
            
            if not model_stats:
                logger.info("没有足够的模型性能数据进行优化")
                return False
            
            # 获取匹配矩阵中的所有领域和意图类型
            domains = self.matching_matrix.get_domains()
            intent_types = self.matching_matrix.get_intent_types()
            
            # 对每个领域和意图类型进行优化
            for domain in domains:
                for intent_type in intent_types:
                    # 获取当前配置的模型列表
                    models = self.matching_matrix.get_models(domain, intent_type)
                    
                    # 对每个模型应用性能调整
                    for model in models:
                        if model in model_stats:
                            stats = model_stats[model]
                            
                            # 只有在有足够数据的情况下才进行调整
                            if stats["total_queries"] >= 10:
                                # 获取当前可信度
                                current_confidence = self.matching_matrix.get_confidence(domain, intent_type, model)
                                
                                # 计算新的可信度（基于平均评分）
                                new_confidence = current_confidence * 0.8 + stats["avg_score"] * 0.2
                                
                                # 更新可信度
                                self.matching_matrix.update_confidence(domain, intent_type, model, new_confidence)
                                
                                logger.info(f"优化模型权重 - 领域: {domain}, 意图: {intent_type}, 模型: {model}, "
                                           f"旧可信度: {current_confidence:.2f}, 新可信度: {new_confidence:.2f}")
            
            # 保存更新后的匹配矩阵
            self.matching_matrix.save_matrix("updated_matrix.json")
            
            return True
        except Exception as e:
            logger.error(f"优化模型权重失败: {e}")
            return False
    
    def get_feedback_statistics(self):
        """
        获取反馈统计信息
        
        返回:
            dict: 统计信息
        """
        try:
            # 总反馈数
            total_feedback = len(self.feedback_history)
            
            if total_feedback == 0:
                return {"status": "no_data", "message": "没有反馈数据"}
            
            # 显性反馈数
            explicit_feedback = sum(1 for f in self.feedback_history if f["type"] == "explicit")
            
            # 隐性反馈数
            implicit_feedback = sum(1 for f in self.feedback_history if f["type"] == "implicit")
            
            # 平均评分
            avg_score = sum(
                f["score"] if "score" in f else f.get("implicit_score", 0.5) 
                for f in self.feedback_history
            ) / total_feedback
            
            # 正面反馈比例
            positive_feedback = sum(
                1 for f in self.feedback_history 
                if ("score" in f and f["score"] >= 0.6) or 
                   ("implicit_score" in f and f["implicit_score"] >= 0.6)
            )
            positive_ratio = positive_feedback / total_feedback
            
            # 按行为类型统计隐性反馈
            behavior_counts = defaultdict(int)
            for f in self.feedback_history:
                if f["type"] == "implicit" and "behavior" in f:
                    behavior_counts[f["behavior"]] += 1
            
            # 统计信息
            statistics = {
                "status": "success",
                "total_feedback": total_feedback,
                "explicit_feedback": explicit_feedback,
                "implicit_feedback": implicit_feedback,
                "avg_score": avg_score,
                "positive_ratio": positive_ratio,
                "behavior_counts": dict(behavior_counts),
                "model_performance": dict(self.model_performance)
            }
            
            return statistics
        except Exception as e:
            logger.error(f"获取反馈统计信息失败: {e}")
            return {"status": "error", "message": str(e)}

# 测试代码
if __name__ == "__main__":
    # 模拟依赖组件
    class MockMatchingMatrix:
        def __init__(self):
            self.matrix = {
                "中医": {
                    "诊断咨询": {
                        "仲景模型": 0.9,
                        "通用医学模型": 0.7
                    }
                },
                "西医": {
                    "药物查询": {
                        "通用医学模型": 0.85,
                        "TCMChat": 0.65
                    }
                }
            }
        
        def update_confidence(self, domain, intent_type, model, score):
            if domain in self.matrix and intent_type in self.matrix[domain] and model in self.matrix[domain][intent_type]:
                old_score = self.matrix[domain][intent_type][model]
                self.matrix[domain][intent_type][model] = old_score * 0.8 + score * 0.2
                return True
            return False
        
        def get_domains(self):
            return list(self.matrix.keys())
        
        def get_intent_types(self):
            intent_types = set()
            for domain in self.matrix:
                intent_types.update(self.matrix[domain].keys())
            return list(intent_types)
        
        def get_models(self, domain, intent_type):
            if domain in self.matrix and intent_type in self.matrix[domain]:
                return list(self.matrix[domain][intent_type].keys())
            return []
        
        def get_confidence(self, domain, intent_type, model):
            if domain in self.matrix and intent_type in self.matrix[domain] and model in self.matrix[domain][intent_type]:
                return self.matrix[domain][intent_type][model]
            return 0.0
        
        def save_matrix(self, file_path):
            print(f"保存矩阵到 {file_path}")
            return True
    
    class MockKnowledgeRepository:
        def __init__(self):
            self.items = {
                "ki_123": {
                    "id": "ki_123",
                    "domain": "中医",
                    "intent_type": "诊断咨询",
                    "metadata": {
                        "model": "仲景模型"
                    }
                },
                "ki_456": {
                    "id": "ki_456",
                    "domain": "西医",
                    "intent_type": "药物查询",
                    "metadata": {
                        "model": "通用医学模型"
                    }
                }
            }
            self.feedback = {}
        
        def update_feedback(self, knowledge_id, user_id, score, comment=None):
            if knowledge_id in self.items:
                key = f"{knowledge_id}_{user_id}"
                self.feedback[key] = {
                    "score": score,
                    "comment": comment,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                return True
            return False
        
        def retrieve_by_id(self, knowledge_id):
            if knowledge_id in self.items:
                return [self.items[knowledge_id]]
            return []
    
    # 创建模拟组件
    matrix = MockMatchingMatrix()
    repo = MockKnowledgeRepository()
    
    # 初始化反馈优化器
    optimizer = FeedbackOptimizer(matrix, repo)
    
    # 测试显性反馈
    print("测试显性反馈...")
    success = optimizer.process_explicit_feedback(
        "ki_123", "user1", 0.9, "非常有帮助的回答",
        {"domain": "中医", "intent_type": "诊断咨询"}
    )
    print(f"显性反馈处理{'成功' if success else '失败'}")
    
    # 测试隐性反馈
    print("\n测试隐性反馈...")
    success = optimizer.process_implicit_feedback(
        "ki_456", "user2", "share",
        {"domain": "西医", "intent_type": "药物查询"}
    )
    print(f"隐性反馈处理{'成功' if success else '失败'}")
    
    # 测试获取统计信息
    print("\n测试获取统计信息...")
    stats = optimizer.get_feedback_statistics()
    print(f"反馈统计: {json.dumps(stats, indent=2)}")
    
    # 测试优化模型权重
    print("\n测试优化模型权重...")
    success = optimizer.optimize_model_weights()
    print(f"模型权重优化{'成功' if success else '失败'}")
    print(f"更新后的矩阵: {json.dumps(matrix.matrix, indent=2)}")
