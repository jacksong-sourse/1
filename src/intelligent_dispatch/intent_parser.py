"""
领域意图解析模块
功能：解析用户查询的医学领域、意图类型和紧急程度
"""

import re
import json
import os
from collections import defaultdict

class IntentParser:
    def __init__(self):
        # 初始化领域关键词词典
        self.domain_keywords = {
            "中医": ["经络", "气血", "阴阳", "五行", "辨证", "脉象", "舌诊", "中药", "方剂", "针灸", "艾灸", 
                   "推拿", "刮痧", "拔罐", "膏方", "汤剂", "丸剂", "散剂", "膏剂", "丹剂", "中成药"],
            "西医": ["检查", "化验", "CT", "核磁", "抗生素", "手术", "西药", "输液", "注射", "X光", 
                   "B超", "血常规", "尿常规", "心电图", "造影", "活检", "病理", "诊断", "预后"],
            "药理学": ["药效", "药代动力学", "不良反应", "禁忌症", "适应症", "用药指导", "药物相互作用", 
                    "药物过敏", "剂量", "给药途径", "半衰期", "血药浓度"],
            "营养学": ["营养", "饮食", "热量", "蛋白质", "脂肪", "碳水化合物", "维生素", "矿物质", 
                    "膳食纤维", "食谱", "饮食指导", "营养不良", "营养过剩"]
        }
        
        # 初始化意图类型关键词
        self.intent_keywords = {
            "诊断咨询": ["是什么病", "怎么回事", "什么原因", "为什么会", "诊断", "检查", "症状", "表现", 
                      "怎么确诊", "需要做什么检查", "是否患有", "可能是"],
            "药物查询": ["用什么药", "吃什么药", "用药", "药效", "副作用", "禁忌", "能吃", "能用", 
                      "如何服用", "用量", "用法", "药物相互作用"],
            "治疗方案": ["怎么治疗", "如何治疗", "治疗方法", "治疗方案", "怎么办", "如何缓解", 
                      "如何改善", "治愈率", "疗程", "手术", "保守治疗"],
            "健康建议": ["如何预防", "怎样保养", "日常注意", "生活方式", "饮食建议", "运动建议", 
                      "调理", "保健", "养生", "护理"]
        }
        
        # 紧急程度关键词
        self.urgency_keywords = {
            "高": ["立即", "马上", "急", "紧急", "危险", "生命危险", "剧烈", "严重", "不能忍受", 
                  "晕倒", "昏迷", "休克", "抢救", "窒息", "大出血"],
            "中": ["尽快", "较严重", "持续", "加重", "恶化", "反复", "频繁", "影响生活", 
                  "影响工作", "影响睡眠"],
            "低": ["轻微", "偶尔", "一般", "有时", "不严重", "想了解", "咨询", "预防", "保健"]
        }
        
        # 加载意图分类器（此处简化为基于规则的分类）
        self._load_intent_classifier()
    
    def _load_intent_classifier(self):
        """加载意图分类器，此处简化为基于规则的分类"""
        # 实际项目中可以加载训练好的机器学习模型
        pass
    
    def parse(self, query):
        """
        解析用户查询
        
        参数:
            query (str): 用户查询文本
            
        返回:
            dict: 包含领域、意图类型和紧急程度的字典
        """
        # 领域识别
        domain = self._identify_domain(query)
        
        # 意图分类
        intent_type = self._classify_intent(query)
        
        # 紧急程度评估
        urgency = self._evaluate_urgency(query)
        
        # 提取关键实体（如症状、药物名等）
        entities = self._extract_entities(query)
        
        return {
            "domain": domain,
            "intent_type": intent_type,
            "urgency": urgency,
            "entities": entities,
            "original_query": query
        }
    
    def _identify_domain(self, query):
        """识别查询所属的医学领域"""
        domain_scores = defaultdict(int)
        
        # 计算每个领域的关键词匹配得分
        for domain, keywords in self.domain_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    # 完全匹配加2分
                    domain_scores[domain] += 2
                elif any(keyword in term for term in query.split()):
                    # 部分匹配加1分
                    domain_scores[domain] += 1
        
        # 如果没有明确领域，默认为通用医学
        if not domain_scores:
            return "通用医学"
        
        # 返回得分最高的领域
        return max(domain_scores.items(), key=lambda x: x[1])[0]
    
    def _classify_intent(self, query):
        """分类查询的意图类型"""
        intent_scores = defaultdict(int)
        
        # 计算每种意图类型的关键词匹配得分
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    intent_scores[intent] += 2
                elif any(keyword in term for term in query.split()):
                    intent_scores[intent] += 1
        
        # 如果没有明确意图，默认为诊断咨询
        if not intent_scores:
            return "诊断咨询"
        
        # 返回得分最高的意图类型
        return max(intent_scores.items(), key=lambda x: x[1])[0]
    
    def _evaluate_urgency(self, query):
        """评估查询的紧急程度"""
        urgency_scores = defaultdict(int)
        
        # 计算每个紧急程度的关键词匹配得分
        for urgency, keywords in self.urgency_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    urgency_scores[urgency] += 2
                elif any(keyword in term for term in query.split()):
                    urgency_scores[urgency] += 1
        
        # 如果没有明确紧急程度，默认为低
        if not urgency_scores:
            return "低"
        
        # 返回得分最高的紧急程度
        return max(urgency_scores.items(), key=lambda x: x[1])[0]
    
    def _extract_entities(self, query):
        """提取查询中的关键实体"""
        # 简化版实体提取，实际项目中可以使用NER模型
        entities = {
            "symptoms": [],
            "medicines": [],
            "body_parts": [],
            "time_expressions": []
        }
        
        # 简单的症状提取（实际项目中应使用更复杂的NER）
        common_symptoms = ["头痛", "发热", "咳嗽", "腹痛", "恶心", "呕吐", "腹泻", "便秘", 
                          "乏力", "疲劳", "失眠", "头晕", "胸痛", "气短", "心悸"]
        for symptom in common_symptoms:
            if symptom in query:
                entities["symptoms"].append(symptom)
        
        return entities

# 测试代码
if __name__ == "__main__":
    parser = IntentParser()
    
    # 测试用例
    test_queries = [
        "我最近咳嗽严重，还有点发烧，该怎么办？",
        "请问太极拳对调理气血有什么好处？",
        "阿莫西林和头孢一起吃有什么副作用？",
        "我父亲突然胸痛，呼吸困难，情况很紧急！",
        "长期熬夜对肝脏有什么影响，需要吃什么调理？"
    ]
    
    for query in test_queries:
        result = parser.parse(query)
        print(f"查询: {query}")
        print(f"解析结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        print("-" * 50)
