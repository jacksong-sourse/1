"""
三维匹配矩阵模块
功能：建立领域、模型、可信度的三维匹配关系，为模型动态路由提供决策依据
"""

import json
import os
import datetime
from collections import defaultdict

class MatchingMatrix:
    def __init__(self, matrix_file=None):
        """
        初始化三维匹配矩阵
        
        参数:
            matrix_file (str, optional): 矩阵配置文件路径，如果不提供则使用默认配置
        """
        # 默认矩阵配置
        self.default_matrix = {
            "中医": {
                "诊断咨询": {
                    "仲景模型": 0.95,
                    "TCMChat": 0.85,
                    "通用医学模型": 0.70
                },
                "药物查询": {
                    "仲景模型": 0.80,
                    "TCMChat": 0.92,
                    "通用医学模型": 0.65
                },
                "治疗方案": {
                    "仲景模型": 0.90,
                    "TCMChat": 0.82,
                    "通用医学模型": 0.60
                },
                "健康建议": {
                    "仲景模型": 0.88,
                    "TCMChat": 0.85,
                    "通用医学模型": 0.75
                }
            },
            "西医": {
                "诊断咨询": {
                    "仲景模型": 0.70,
                    "TCMChat": 0.65,
                    "通用医学模型": 0.90
                },
                "药物查询": {
                    "仲景模型": 0.60,
                    "TCMChat": 0.70,
                    "通用医学模型": 0.88
                },
                "治疗方案": {
                    "仲景模型": 0.65,
                    "TCMChat": 0.60,
                    "通用医学模型": 0.92
                },
                "健康建议": {
                    "仲景模型": 0.75,
                    "TCMChat": 0.72,
                    "通用医学模型": 0.85
                }
            },
            "药理学": {
                "诊断咨询": {
                    "仲景模型": 0.75,
                    "TCMChat": 0.80,
                    "通用医学模型": 0.85
                },
                "药物查询": {
                    "仲景模型": 0.82,
                    "TCMChat": 0.90,
                    "通用医学模型": 0.88
                },
                "治疗方案": {
                    "仲景模型": 0.70,
                    "TCMChat": 0.85,
                    "通用医学模型": 0.80
                },
                "健康建议": {
                    "仲景模型": 0.78,
                    "TCMChat": 0.82,
                    "通用医学模型": 0.80
                }
            },
            "营养学": {
                "诊断咨询": {
                    "仲景模型": 0.80,
                    "TCMChat": 0.75,
                    "通用医学模型": 0.82
                },
                "药物查询": {
                    "仲景模型": 0.70,
                    "TCMChat": 0.72,
                    "通用医学模型": 0.75
                },
                "治疗方案": {
                    "仲景模型": 0.85,
                    "TCMChat": 0.80,
                    "通用医学模型": 0.78
                },
                "健康建议": {
                    "仲景模型": 0.90,
                    "TCMChat": 0.85,
                    "通用医学模型": 0.88
                }
            },
            "通用医学": {
                "诊断咨询": {
                    "仲景模型": 0.80,
                    "TCMChat": 0.78,
                    "通用医学模型": 0.85
                },
                "药物查询": {
                    "仲景模型": 0.75,
                    "TCMChat": 0.80,
                    "通用医学模型": 0.82
                },
                "治疗方案": {
                    "仲景模型": 0.78,
                    "TCMChat": 0.75,
                    "通用医学模型": 0.85
                },
                "健康建议": {
                    "仲景模型": 0.82,
                    "TCMChat": 0.80,
                    "通用医学模型": 0.85
                }
            }
        }
        
        # 加载矩阵配置
        if matrix_file and os.path.exists(matrix_file):
            try:
                with open(matrix_file, 'r', encoding='utf-8') as f:
                    self.matrix = json.load(f)
            except Exception as e:
                print(f"加载矩阵配置文件失败: {e}")
                self.matrix = self.default_matrix
        else:
            self.matrix = self.default_matrix
        
        # 初始化历史记录
        self.history = []
        
        # 初始化模型调用计数
        self.model_call_count = defaultdict(int)
    
    def get_best_model(self, domain, intent_type, urgency="低"):
        """
        获取特定领域和意图类型的最佳模型
        
        参数:
            domain (str): 医学领域
            intent_type (str): 意图类型
            urgency (str, optional): 紧急程度，默认为"低"
            
        返回:
            tuple: (最佳模型名称, 可信度)
        """
        # 如果领域不在矩阵中，使用通用医学
        if domain not in self.matrix:
            domain = "通用医学"
        
        # 如果意图类型不在矩阵中，使用诊断咨询
        if intent_type not in self.matrix[domain]:
            intent_type = "诊断咨询"
        
        # 获取该领域和意图类型下的所有模型
        models = self.matrix[domain][intent_type]
        
        # 紧急情况下，提高通用医学模型的权重
        if urgency == "高" and "通用医学模型" in models:
            models = models.copy()  # 创建副本以避免修改原始数据
            models["通用医学模型"] *= 1.2  # 提高20%的权重
            # 确保权重不超过1
            if models["通用医学模型"] > 1:
                models["通用医学模型"] = 1.0
        
        # 返回可信度最高的模型
        best_model = max(models.items(), key=lambda x: x[1])
        
        # 记录选择历史
        self._record_selection(domain, intent_type, best_model[0], best_model[1], urgency)
        
        # 更新模型调用计数
        self.model_call_count[best_model[0]] += 1
        
        return best_model
    
    def get_collaborative_models(self, domain, intent_type, threshold=0.8, max_models=2):
        """
        获取可协同工作的模型列表
        
        参数:
            domain (str): 医学领域
            intent_type (str): 意图类型
            threshold (float, optional): 可信度阈值，默认为0.8
            max_models (int, optional): 最大模型数量，默认为2
            
        返回:
            list: 模型名称和可信度的元组列表
        """
        # 如果领域不在矩阵中，使用通用医学
        if domain not in self.matrix:
            domain = "通用医学"
        
        # 如果意图类型不在矩阵中，使用诊断咨询
        if intent_type not in self.matrix[domain]:
            intent_type = "诊断咨询"
        
        # 获取该领域和意图类型下的所有模型
        models = self.matrix[domain][intent_type]
        
        # 筛选可信度高于阈值的模型
        qualified_models = [(name, conf) for name, conf in models.items() if conf >= threshold]
        
        # 按可信度降序排序
        qualified_models.sort(key=lambda x: x[1], reverse=True)
        
        # 限制模型数量
        collaborative_models = qualified_models[:max_models]
        
        # 记录选择历史
        for model_name, confidence in collaborative_models:
            self._record_selection(domain, intent_type, model_name, confidence, "协同")
            self.model_call_count[model_name] += 1
        
        return collaborative_models
    
    def update_confidence(self, domain, intent_type, model, feedback_score):
        """
        基于用户反馈更新可信度
        
        参数:
            domain (str): 医学领域
            intent_type (str): 意图类型
            model (str): 模型名称
            feedback_score (float): 反馈评分 (0-1)
            
        返回:
            bool: 更新是否成功
        """
        if domain not in self.matrix:
            return False
        
        if intent_type not in self.matrix[domain]:
            return False
        
        if model not in self.matrix[domain][intent_type]:
            return False
        
        # 动态更新可信度（加权平均）
        current = self.matrix[domain][intent_type][model]
        # 新的可信度 = 90% 的当前可信度 + 10% 的反馈评分
        self.matrix[domain][intent_type][model] = current * 0.9 + feedback_score * 0.1
        
        # 记录更新历史
        self._record_update(domain, intent_type, model, current, self.matrix[domain][intent_type][model])
        
        return True
    
    def save_matrix(self, file_path):
        """
        保存矩阵配置到文件
        
        参数:
            file_path (str): 文件路径
            
        返回:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.matrix, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存矩阵配置失败: {e}")
            return False
    
    def _record_selection(self, domain, intent_type, model, confidence, urgency):
        """记录模型选择历史"""
        self.history.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "action": "selection",
            "domain": domain,
            "intent_type": intent_type,
            "model": model,
            "confidence": confidence,
            "urgency": urgency
        })
    
    def _record_update(self, domain, intent_type, model, old_confidence, new_confidence):
        """记录可信度更新历史"""
        self.history.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "action": "update",
            "domain": domain,
            "intent_type": intent_type,
            "model": model,
            "old_confidence": old_confidence,
            "new_confidence": new_confidence
        })
    
    def get_history(self, limit=100):
        """获取历史记录"""
        return self.history[-limit:]
    
    def get_model_statistics(self):
        """获取模型使用统计"""
        return dict(self.model_call_count)

# 测试代码
if __name__ == "__main__":
    matrix = MatchingMatrix()
    
    # 测试获取最佳模型
    test_cases = [
        ("中医", "诊断咨询"),
        ("西医", "药物查询"),
        ("药理学", "治疗方案"),
        ("营养学", "健康建议"),
        ("通用医学", "诊断咨询")
    ]
    
    print("测试获取最佳模型:")
    for domain, intent_type in test_cases:
        best_model, confidence = matrix.get_best_model(domain, intent_type)
        print(f"领域: {domain}, 意图: {intent_type} => 最佳模型: {best_model}, 可信度: {confidence:.2f}")
    
    print("\n测试获取协同模型:")
    for domain, intent_type in test_cases:
        models = matrix.get_collaborative_models(domain, intent_type)
        print(f"领域: {domain}, 意图: {intent_type} => 协同模型: {models}")
    
    print("\n测试更新可信度:")
    matrix.update_confidence("中医", "诊断咨询", "仲景模型", 1.0)
    best_model, confidence = matrix.get_best_model("中医", "诊断咨询")
    print(f"更新后 - 领域: 中医, 意图: 诊断咨询 => 最佳模型: {best_model}, 可信度: {confidence:.2f}")
    
    print("\n模型使用统计:")
    print(matrix.get_model_statistics())
