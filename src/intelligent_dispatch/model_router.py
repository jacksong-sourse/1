"""
模型动态路由模块
功能：根据三维匹配矩阵的结果，动态选择最合适的模型处理用户查询
"""

import os
import json
import time
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseModel:
    """模型基类，定义统一接口"""
    def __init__(self, name):
        self.name = name
        self.call_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_latency = 0
        
    def infer(self, query, intent_data):
        """
        模型推理接口
        
        参数:
            query (str): 用户查询
            intent_data (dict): 意图解析数据
            
        返回:
            str: 模型回答
        """
        raise NotImplementedError
    
    def get_statistics(self):
        """获取模型调用统计"""
        avg_latency = 0
        if self.call_count > 0:
            avg_latency = self.total_latency / self.call_count
            
        return {
            "name": self.name,
            "call_count": self.call_count,
            "success_rate": self.success_count / max(1, self.call_count),
            "avg_latency": avg_latency
        }

class ZhongJingModel(BaseModel):
    """仲景模型实现"""
    def __init__(self, model_path=None):
        super().__init__("仲景模型")
        self.model_path = model_path
        # 实际项目中应加载模型
        logger.info(f"初始化仲景模型，模型路径: {model_path}")
        
    def infer(self, query, intent_data):
        """模型推理"""
        start_time = time.time()
        self.call_count += 1
        
        try:
            # 模拟模型推理
            logger.info(f"仲景模型推理: {query}")
            
            # 构建提示模板
            prompt = self._build_prompt(query, intent_data)
            
            # 模拟模型延迟
            time.sleep(0.5)
            
            # 模拟模型输出
            response = self._simulate_response(query, intent_data)
            
            self.success_count += 1
            self.total_latency += (time.time() - start_time)
            return response
        except Exception as e:
            logger.error(f"仲景模型推理失败: {e}")
            self.failure_count += 1
            self.total_latency += (time.time() - start_time)
            raise
    
    def _build_prompt(self, query, intent_data):
        """构建提示模板"""
        domain = intent_data.get("domain", "通用医学")
        intent_type = intent_data.get("intent_type", "诊断咨询")
        
        if domain == "中医":
            if intent_type == "诊断咨询":
                return f"作为一名经验丰富的中医师，请对以下症状进行辨证论治：{query}"
            elif intent_type == "药物查询":
                return f"作为一名中医药专家，请详细解释以下中药或方剂的功效与应用：{query}"
            elif intent_type == "治疗方案":
                return f"作为一名中医临床专家，请为以下情况提供合理的治疗方案：{query}"
            else:
                return f"作为一名中医养生专家，请针对以下问题提供专业建议：{query}"
        else:
            return f"请以专业医学角度回答以下问题：{query}"
    
    def _simulate_response(self, query, intent_data):
        """模拟模型回答"""
        domain = intent_data.get("domain", "通用医学")
        intent_type = intent_data.get("intent_type", "诊断咨询")
        
        # 根据不同领域和意图类型生成模拟回答
        if "咳嗽" in query and "发烧" in query:
            if domain == "中医":
                return "从中医角度看，您的症状表现为风热犯肺。风热犯肺主要表现为发热、咳嗽、痰黄或白、口干、咽痛等症状。建议服用银翘散或桑菊饮加减治疗。同时可以配合穴位按摩，如合谷穴、风门穴等。平时注意多休息，多饮水，避免辛辣刺激性食物。如症状加重或持续不退，建议及时就医。"
            else:
                return "您的症状可能是上呼吸道感染或流感的表现。建议多休息，多饮水，可以服用对乙酰氨基酚等退烧药物缓解发热症状。如果体温超过38.5℃或症状持续加重，建议及时就医检查。"
        
        elif "头痛" in query:
            if domain == "中医":
                return "中医认为头痛有多种类型，如风寒头痛、风热头痛、肝阳上亢头痛等。需要根据具体症状辨证论治。若伴有怕冷、无汗，可能是风寒头痛，可用川芎茶调散；若伴有口干、口渴，可能是风热头痛，可用桑菊饮加减；若头痛剧烈、面红目赤，可能是肝阳上亢，可用天麻钩藤饮。建议到专业中医机构就诊，进行详细辨证。"
            else:
                return "头痛可能由多种原因引起，如紧张性头痛、偏头痛、颅内压增高等。建议您注意休息，避免过度疲劳和精神紧张。如果头痛剧烈、突发、伴有呕吐、视力模糊等症状，应立即就医。"
        
        else:
            if domain == "中医":
                return "从中医角度分析，需要进一步了解您的具体症状、舌象、脉象等信息才能做出准确的辨证。建议您到专业的中医医疗机构就诊，由专业中医师进行面诊。"
            else:
                return "您的问题需要更多具体信息才能给出专业建议。建议您详细描述症状、持续时间、是否有其他不适等，或直接咨询医疗专业人士获取个性化的医疗建议。"

class TCMChatModel(BaseModel):
    """TCMChat API实现"""
    def __init__(self, api_url=None, api_key=None):
        super().__init__("TCMChat")
        self.api_url = api_url or "https://api.example.com/tcmchat"
        self.api_key = api_key or "demo_api_key"
        logger.info(f"初始化TCMChat API，API地址: {self.api_url}")
        
    def infer(self, query, intent_data):
        """调用API"""
        start_time = time.time()
        self.call_count += 1
        
        try:
            # 模拟API调用
            logger.info(f"TCMChat API调用: {query}")
            
            # 模拟网络延迟
            time.sleep(0.8)
            
            # 模拟API响应
            response = self._simulate_api_response(query, intent_data)
            
            self.success_count += 1
            self.total_latency += (time.time() - start_time)
            return response
        except Exception as e:
            logger.error(f"TCMChat API调用失败: {e}")
            self.failure_count += 1
            self.total_latency += (time.time() - start_time)
            raise
    
    def _simulate_api_response(self, query, intent_data):
        """模拟API响应"""
        domain = intent_data.get("domain", "通用医学")
        intent_type = intent_data.get("intent_type", "诊断咨询")
        
        # 根据不同领域和意图类型生成模拟回答
        if "中药" in query or "方剂" in query:
            return "根据TCM知识库查询，该中药/方剂具有以下功效和适应症...[详细中药知识]。使用时请遵医嘱，不同体质可能反应不同。"
        
        elif "食疗" in query or "饮食" in query:
            return "中医食疗讲究'药食同源'，根据您的问题，推荐以下食疗方案...[详细食疗建议]。请根据个人体质适当调整。"
        
        else:
            return "TCMChat分析了您的问题，根据中医理论和临床实践，建议如下...[详细中医建议]。如有不适，请及时就医。"

class GeneralMedicalModel(BaseModel):
    """通用医学模型实现"""
    def __init__(self):
        super().__init__("通用医学模型")
        logger.info("初始化通用医学模型")
        
    def infer(self, query, intent_data):
        """模型推理"""
        start_time = time.time()
        self.call_count += 1
        
        try:
            # 模拟模型推理
            logger.info(f"通用医学模型推理: {query}")
            
            # 模拟模型延迟
            time.sleep(0.3)
            
            # 模拟模型输出
            response = self._simulate_response(query, intent_data)
            
            self.success_count += 1
            self.total_latency += (time.time() - start_time)
            return response
        except Exception as e:
            logger.error(f"通用医学模型推理失败: {e}")
            self.failure_count += 1
            self.total_latency += (time.time() - start_time)
            raise
    
    def _simulate_response(self, query, intent_data):
        """模拟模型回答"""
        intent_type = intent_data.get("intent_type", "诊断咨询")
        
        if intent_type == "诊断咨询":
            return "根据您描述的症状，可能与以下疾病有关...[详细医学分析]。建议您咨询专业医生进行确诊和治疗。"
        
        elif intent_type == "药物查询":
            return "您查询的药物主要成分是...[药物成分]，主要用于治疗...[适应症]。常见副作用包括...[副作用]。用药请遵医嘱。"
        
        elif intent_type == "治疗方案":
            return "针对您描述的情况，常见的治疗方案包括...[治疗方案]。具体治疗方案应由专业医生根据您的具体情况制定。"
        
        else:
            return "针对您的健康问题，建议...[健康建议]。这些建议仅供参考，如有不适，请及时就医。"

class ModelRouter:
    """模型动态路由"""
    def __init__(self, matching_matrix):
        """
        初始化模型路由器
        
        参数:
            matching_matrix: 三维匹配矩阵实例
        """
        self.matching_matrix = matching_matrix
        
        # 初始化模型实例
        self.models = {
            "仲景模型": ZhongJingModel(),
            "TCMChat": TCMChatModel(),
            "通用医学模型": GeneralMedicalModel()
        }
        
        # 初始化线程池
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        logger.info("模型路由器初始化完成")
    
    def route(self, query, intent_data):
        """
        根据意图数据路由到合适的模型
        
        参数:
            query (str): 用户查询
            intent_data (dict): 意图解析数据
            
        返回:
            str: 模型回答
        """
        domain = intent_data.get("domain", "通用医学")
        intent_type = intent_data.get("intent_type", "诊断咨询")
        urgency = intent_data.get("urgency", "低")
        
        logger.info(f"路由查询 - 领域: {domain}, 意图: {intent_type}, 紧急程度: {urgency}")
        
        # 获取最佳模型
        best_model_name, confidence = self.matching_matrix.get_best_model(domain, intent_type, urgency)
        
        logger.info(f"选择模型: {best_model_name}, 可信度: {confidence:.2f}")
        
        # 可信度阈值检查
        if confidence < 0.7:
            logger.info(f"可信度低于阈值，使用多模型协同")
            return self._collaborative_inference(query, intent_data)
        
        # 调用单一最佳模型
        try:
            return self.models[best_model_name].infer(query, intent_data)
        except Exception as e:
            logger.error(f"模型 {best_model_name} 推理失败: {e}")
            # 失败后尝试备用模型
            return self._fallback_inference(query, intent_data, best_model_name)
    
    def _collaborative_inference(self, query, intent_data):
        """
        多模型协同推理
        
        参数:
            query (str): 用户查询
            intent_data (dict): 意图解析数据
            
        返回:
            str: 融合后的回答
        """
        domain = intent_data.get("domain", "通用医学")
        intent_type = intent_data.get("intent_type", "诊断咨询")
        
        # 获取协同模型列表
        collaborative_models = self.matching_matrix.get_collaborative_models(domain, intent_type)
        
        logger.info(f"协同模型: {collaborative_models}")
        
        # 并行调用多个模型
        future_to_model = {}
        for model_name, _ in collaborative_models:
            future = self.executor.submit(self.models[model_name].infer, query, intent_data)
            future_to_model[future] = model_name
        
        # 收集结果
        results = {}
        for future in as_completed(future_to_model):
            model_name = future_to_model[future]
            try:
                results[model_name] = future.result()
            except Exception as e:
                logger.error(f"模型 {model_name} 推理失败: {e}")
        
        # 如果所有模型都失败，使用通用回退
        if not results:
            return "抱歉，系统暂时无法处理您的请求，请稍后再试或重新表述您的问题。"
        
        # 结果融合
        return self._merge_results(results, intent_data)
    
    def _fallback_inference(self, query, intent_data, failed_model):
        """
        备用推理
        
        参数:
            query (str): 用户查询
            intent_data (dict): 意图解析数据
            failed_model (str): 失败的模型名称
            
        返回:
            str: 备用模型的回答
        """
        # 排除失败的模型
        available_models = [name for name in self.models.keys() if name != failed_model]
        
        # 如果没有可用模型，返回错误信息
        if not available_models:
            return "抱歉，系统暂时无法处理您的请求，请稍后再试。"
        
        # 选择第一个可用模型
        backup_model = available_models[0]
        logger.info(f"使用备用模型: {backup_model}")
        
        try:
            return self.models[backup_model].infer(query, intent_data)
        except Exception as e:
            logger.error(f"备用模型 {backup_model} 也失败了: {e}")
            return "抱歉，系统暂时无法处理您的请求，请稍后再试或重新表述您的问题。"
    
    def _merge_results(self, results, intent_data):
        """
        融合多个模型的结果
        
        参数:
            results (dict): 模型名称到回答的映射
            intent_data (dict): 意图解析数据
            
        返回:
            str: 融合后的回答
        """
        domain = intent_data.get("domain", "通用医学")
        intent_type = intent_data.get("intent_type", "诊断咨询")
        
        # 简单的结果融合策略
        if domain == "中医" and "仲景模型" in results:
            # 中医领域优先使用仲景模型的回答
            primary_response = results["仲景模型"]
            
            # 如果有TCMChat的药物推荐，添加到回答中
            if intent_type == "药物查询" and "TCMChat" in results:
                return f"{primary_response}\n\n此外，TCMChat还推荐：{results['TCMChat']}"
            
            return primary_response
        
        elif domain == "西医" and "通用医学模型" in results:
            # 西医领域优先使用通用医学模型的回答
            return results["通用医学模型"]
        
        elif "药物" in intent_type and "TCMChat" in results:
            # 药物查询优先使用TCMChat
            return results["TCMChat"]
        
        # 默认使用第一个结果
        return next(iter(results.values()))
    
    def get_model_statistics(self):
        """获取所有模型的统计信息"""
        return {name: model.get_statistics() for name, model in self.models.items()}

# 测试代码
if __name__ == "__main__":
    # 导入匹配矩阵
    from matching_matrix import MatchingMatrix
    
    # 创建匹配矩阵
    matrix = MatchingMatrix()
    
    # 创建模型路由器
    router = ModelRouter(matrix)
    
    # 测试用例
    test_queries = [
        {
            "query": "我最近咳嗽严重，还有点发烧，该怎么办？",
            "intent_data": {
                "domain": "中医",
                "intent_type": "诊断咨询",
                "urgency": "中"
            }
        },
        {
            "query": "请问太极拳对调理气血有什么好处？",
            "intent_data": {
                "domain": "中医",
                "intent_type": "健康建议",
                "urgency": "低"
            }
        },
        {
            "query": "阿莫西林和头孢一起吃有什么副作用？",
            "intent_data": {
                "domain": "西医",
                "intent_type": "药物查询",
                "urgency": "中"
            }
        },
        {
            "query": "我父亲突然胸痛，呼吸困难，情况很紧急！",
            "intent_data": {
                "domain": "西医",
                "intent_type": "诊断咨询",
                "urgency": "高"
            }
        }
    ]
    
    print("测试模型路由:")
    for test in test_queries:
        print(f"\n查询: {test['query']}")
        print(f"意图数据: {test['intent_data']}")
        
        response = router.route(test['query'], test['intent_data'])
        print(f"回答: {response}")
        print("-" * 50)
    
    print("\n模型统计信息:")
    stats = router.get_model_statistics()
    for model_name, model_stats in stats.items():
        print(f"{model_name}: 调用次数={model_stats['call_count']}, 成功率={model_stats['success_rate']:.2f}, 平均延迟={model_stats['avg_latency']:.2f}秒")
