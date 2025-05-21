"""
知识质量评估模块
功能：评估清洗后知识的质量，为知识库存储分级提供依据
"""

import re
import json
import logging
import datetime
from collections import Counter

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeEvaluator:
    def __init__(self, config_file=None):
        """
        初始化知识质量评估器
        
        参数:
            config_file (str, optional): 配置文件路径，如果不提供则使用默认配置
        """
        # 默认评估指标权重
        self.default_weights = {
            "professionalism": 0.4,  # 专业性权重
            "completeness": 0.3,     # 完整性权重
            "readability": 0.2,      # 可读性权重
            "safety": 0.1            # 安全性权重
        }
        
        # 医学术语词典（用于专业性评估）
        self.medical_terms = set([
            "诊断", "症状", "病因", "治疗", "预后", "并发症", "适应症", "禁忌症", 
            "用药", "剂量", "副作用", "不良反应", "检查", "化验", "影像", "手术",
            "病理", "生理", "解剖", "免疫", "微生物", "病毒", "细菌", "真菌",
            "寄生虫", "遗传", "代谢", "内分泌", "神经", "心血管", "呼吸", "消化",
            "泌尿", "生殖", "血液", "骨骼", "肌肉", "皮肤", "眼", "耳", "鼻", "喉",
            "口腔", "精神", "心理", "营养", "康复", "预防", "流行病学"
        ])
        
        # 中医术语词典（用于中医专业性评估）
        self.tcm_terms = set([
            "辨证", "论治", "气血", "阴阳", "五行", "脏腑", "经络", "气机", "津液",
            "痰湿", "瘀血", "虚证", "实证", "寒证", "热证", "表证", "里证", "半表半里",
            "望闻问切", "舌诊", "脉诊", "腹诊", "切诊", "望诊", "闻诊", "问诊",
            "君臣佐使", "升降浮沉", "宣通", "温补", "清热", "祛湿", "活血", "化瘀",
            "补气", "养血", "滋阴", "壮阳", "解表", "攻里", "和解", "温化", "消导"
        ])
        
        # 药物术语词典（用于药理学专业性评估）
        self.pharmacology_terms = set([
            "药效", "药代动力学", "药物相互作用", "不良反应", "禁忌症", "适应症",
            "半衰期", "血药浓度", "分布容积", "清除率", "生物利用度", "首过效应",
            "受体", "酶", "通道", "转运体", "激动剂", "拮抗剂", "部分激动剂",
            "反向激动剂", "变构调节剂", "药物代谢", "药物排泄", "药物吸收",
            "药物分布", "药物耐受", "药物依赖", "药物成瘾", "药物过敏", "药物毒性"
        ])
        
        # 安全性关键词（用于安全性评估）
        self.safety_keywords = {
            "positive": [
                "请咨询医生", "遵医嘱", "专业指导下", "不建议自行", "如有不适", "及时就医",
                "严格按照", "不要擅自", "医生指导", "专业医疗", "谨慎使用", "注意事项",
                "禁忌症", "不良反应", "副作用", "风险", "警告", "慎用", "忌用"
            ],
            "negative": [
                "绝对安全", "无副作用", "包治百病", "立竿见影", "彻底根治", "百分百有效",
                "包好", "神奇效果", "特效药", "秘方", "独家配方", "祖传秘方", "一劳永逸"
            ]
        }
        
        # 完整性检查项（用于完整性评估）
        self.completeness_checklist = {
            "诊断咨询": ["症状分析", "可能病因", "建议措施", "注意事项"],
            "药物查询": ["药物作用", "用法用量", "不良反应", "禁忌症"],
            "治疗方案": ["治疗目标", "治疗方法", "预期效果", "风险提示"],
            "健康建议": ["生活方式", "饮食建议", "运动建议", "预防措施"]
        }
        
        # 加载配置
        if config_file:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.evaluation_weights = config.get("evaluation_weights", self.default_weights)
                    
                    # 合并词典
                    self.medical_terms.update(config.get("medical_terms", []))
                    self.tcm_terms.update(config.get("tcm_terms", []))
                    self.pharmacology_terms.update(config.get("pharmacology_terms", []))
                    
                    # 更新安全性关键词
                    if "safety_keywords" in config:
                        self.safety_keywords["positive"].extend(config["safety_keywords"].get("positive", []))
                        self.safety_keywords["negative"].extend(config["safety_keywords"].get("negative", []))
                    
                    # 更新完整性检查项
                    if "completeness_checklist" in config:
                        for intent, items in config["completeness_checklist"].items():
                            if intent in self.completeness_checklist:
                                self.completeness_checklist[intent].extend(items)
                            else:
                                self.completeness_checklist[intent] = items
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                self.evaluation_weights = self.default_weights
        else:
            self.evaluation_weights = self.default_weights
        
        logger.info("知识质量评估器初始化完成")
    
    def evaluate(self, knowledge_item, query, intent_data):
        """
        评估知识质量
        
        参数:
            knowledge_item (dict): 知识项，包含原始回答、清洗后回答和元数据
            query (str): 用户查询
            intent_data (dict): 意图解析数据
            
        返回:
            dict: 评估结果，包含总分和各维度得分
        """
        logger.info("开始知识质量评估")
        
        cleaned_response = knowledge_item["cleaned_response"]
        domain = intent_data.get("domain", "通用医学")
        intent_type = intent_data.get("intent_type", "诊断咨询")
        
        # 评估各维度得分
        professionalism_score = self._evaluate_professionalism(cleaned_response, domain)
        completeness_score = self._evaluate_completeness(cleaned_response, query, intent_type)
        readability_score = self._evaluate_readability(cleaned_response)
        safety_score = self._evaluate_safety(cleaned_response, intent_data)
        
        # 计算加权总分
        scores = {
            "professionalism": professionalism_score,
            "completeness": completeness_score,
            "readability": readability_score,
            "safety": safety_score
        }
        
        total_score = sum(score * self.evaluation_weights[metric] 
                          for metric, score in scores.items())
        
        # 评估结果
        evaluation_result = {
            "total_score": total_score,
            "detailed_scores": scores,
            "evaluation_timestamp": datetime.datetime.now().isoformat(),
            "evaluation_weights": self.evaluation_weights
        }
        
        logger.info(f"知识质量评估完成，总分: {total_score:.2f}")
        
        return evaluation_result
    
    def _evaluate_professionalism(self, response, domain):
        """
        评估专业性
        
        参数:
            response (str): 清洗后的回答
            domain (str): 医学领域
            
        返回:
            float: 专业性得分 (0-1)
        """
        # 计算文本长度
        text_length = len(response)
        if text_length == 0:
            return 0.0
        
        # 根据不同领域选择不同的术语集
        domain_terms = self.medical_terms  # 默认使用医学术语
        
        if domain == "中医":
            domain_terms = self.medical_terms.union(self.tcm_terms)
        elif domain == "药理学":
            domain_terms = self.medical_terms.union(self.pharmacology_terms)
        
        # 计算专业术语出现次数
        term_count = 0
        for term in domain_terms:
            term_count += len(re.findall(r'\b' + re.escape(term) + r'\b', response))
        
        # 计算术语密度
        term_density = term_count / (text_length / 100)  # 每100字符的术语数
        
        # 术语密度得分（使用sigmoid函数映射到0-1区间）
        density_score = 2 / (1 + 2.71828 ** (-term_density + 3)) - 1
        
        # 检查是否有参考文献或引用
        has_reference = any(ref in response for ref in ["参考", "引用", "来源", "依据", "指南", "共识"])
        reference_score = 0.2 if has_reference else 0.0
        
        # 检查是否有专业结构（如诊断、治疗、预后等章节）
        structure_patterns = [
            r'诊断[：:]\s*\S+',
            r'治疗[：:]\s*\S+',
            r'用法[：:]\s*\S+',
            r'用量[：:]\s*\S+',
            r'适应症[：:]\s*\S+',
            r'禁忌症[：:]\s*\S+',
            r'不良反应[：:]\s*\S+',
            r'注意事项[：:]\s*\S+',
            r'预后[：:]\s*\S+',
            r'病因[：:]\s*\S+',
            r'病机[：:]\s*\S+',
            r'辨证[：:]\s*\S+'
        ]
        
        structure_count = sum(1 for pattern in structure_patterns if re.search(pattern, response))
        structure_score = min(0.3, structure_count * 0.1)  # 最高0.3分
        
        # 综合得分
        professionalism_score = min(1.0, density_score + reference_score + structure_score)
        
        logger.info(f"专业性评估 - 术语密度: {term_density:.2f}, 术语密度得分: {density_score:.2f}, "
                   f"参考文献得分: {reference_score:.2f}, 结构得分: {structure_score:.2f}, "
                   f"综合得分: {professionalism_score:.2f}")
        
        return professionalism_score
    
    def _evaluate_completeness(self, response, query, intent_type):
        """
        评估完整性
        
        参数:
            response (str): 清洗后的回答
            query (str): 用户查询
            intent_type (str): 意图类型
            
        返回:
            float: 完整性得分 (0-1)
        """
        # 获取该意图类型的检查项
        checklist = self.completeness_checklist.get(intent_type, [])
        if not checklist:
            # 如果没有特定意图的检查项，使用通用检查项
            checklist = ["问题回答", "详细解释", "建议措施", "注意事项"]
        
        # 计算检查项覆盖率
        covered_items = 0
        for item in checklist:
            # 使用同义词扩展匹配
            synonyms = self._get_synonyms(item)
            if any(syn in response for syn in synonyms):
                covered_items += 1
        
        coverage_score = covered_items / len(checklist)
        
        # 计算回答长度得分
        length_score = min(1.0, len(response) / 500)  # 500字符以上得满分
        
        # 计算问题关键词覆盖率
        query_keywords = self._extract_keywords(query)
        if query_keywords:
            keyword_coverage = sum(1 for kw in query_keywords if kw in response) / len(query_keywords)
        else:
            keyword_coverage = 1.0  # 如果没有提取到关键词，默认满分
        
        # 综合得分
        completeness_score = 0.5 * coverage_score + 0.3 * length_score + 0.2 * keyword_coverage
        
        logger.info(f"完整性评估 - 检查项覆盖率: {coverage_score:.2f}, 长度得分: {length_score:.2f}, "
                   f"关键词覆盖率: {keyword_coverage:.2f}, 综合得分: {completeness_score:.2f}")
        
        return completeness_score
    
    def _evaluate_readability(self, response):
        """
        评估可读性
        
        参数:
            response (str): 清洗后的回答
            
        返回:
            float: 可读性得分 (0-1)
        """
        # 分段和分句
        paragraphs = response.split('\n\n')
        sentences = re.split(r'[。！？.!?]', response)
        sentences = [s for s in sentences if s.strip()]
        
        # 计算平均段落长度
        avg_paragraph_length = sum(len(p) for p in paragraphs) / max(1, len(paragraphs))
        paragraph_score = min(1.0, 200 / max(1, avg_paragraph_length))  # 段落越短越好，最长200字符
        
        # 计算平均句子长度
        avg_sentence_length = sum(len(s) for s in sentences) / max(1, len(sentences))
        sentence_score = min(1.0, 50 / max(1, avg_sentence_length))  # 句子越短越好，最长50字符
        
        # 计算标点符号比例
        punctuation_count = len(re.findall(r'[，。！？、：；""''（）【】《》,.!?:;\'\"()\[\]<>]', response))
        punctuation_ratio = punctuation_count / max(1, len(response))
        punctuation_score = 1.0 if 0.05 <= punctuation_ratio <= 0.15 else max(0, 1 - abs(punctuation_ratio - 0.1) * 10)
        
        # 计算段落和小标题比例
        has_subtitles = any(re.match(r'^[一二三四五六七八九十1234567890]+[、.．]\s*\S+', p.strip()) for p in paragraphs)
        subtitle_score = 0.2 if has_subtitles else 0.0
        
        # 综合得分
        readability_score = 0.3 * paragraph_score + 0.3 * sentence_score + 0.3 * punctuation_score + 0.1 * subtitle_score
        
        logger.info(f"可读性评估 - 段落得分: {paragraph_score:.2f}, 句子得分: {sentence_score:.2f}, "
                   f"标点得分: {punctuation_score:.2f}, 小标题得分: {subtitle_score:.2f}, "
                   f"综合得分: {readability_score:.2f}")
        
        return readability_score
    
    def _evaluate_safety(self, response, intent_data):
        """
        评估安全性
        
        参数:
            response (str): 清洗后的回答
            intent_data (dict): 意图解析数据
            
        返回:
            float: 安全性得分 (0-1)
        """
        urgency = intent_data.get("urgency", "低")
        
        # 检查正面安全关键词
        positive_count = sum(1 for kw in self.safety_keywords["positive"] if kw in response)
        positive_score = min(1.0, positive_count / 5)  # 最多5个正面关键词得满分
        
        # 检查负面安全关键词（越少越好）
        negative_count = sum(1 for kw in self.safety_keywords["negative"] if kw in response)
        negative_score = 1.0 if negative_count == 0 else max(0, 1 - negative_count * 0.2)  # 每个负面关键词扣0.2分
        
        # 检查免责声明
        has_disclaimer = "免责声明" in response or "仅供参考" in response or "请咨询医生" in response
        disclaimer_score = 0.3 if has_disclaimer else 0.0
        
        # 紧急情况下的安全提示
        emergency_score = 0.0
        if urgency == "高":
            emergency_keywords = ["立即就医", "紧急", "急诊", "拨打急救电话", "120", "911"]
            if any(kw in response for kw in emergency_keywords):
                emergency_score = 0.3
        
        # 综合得分
        if urgency == "高":
            safety_score = 0.3 * positive_score + 0.2 * negative_score + 0.2 * disclaimer_score + 0.3 * emergency_score
        else:
            safety_score = 0.4 * positive_score + 0.3 * negative_score + 0.3 * disclaimer_score
        
        logger.info(f"安全性评估 - 正面关键词得分: {positive_score:.2f}, 负面关键词得分: {negative_score:.2f}, "
                   f"免责声明得分: {disclaimer_score:.2f}, 紧急提示得分: {emergency_score:.2f}, "
                   f"综合得分: {safety_score:.2f}")
        
        return safety_score
    
    def _get_synonyms(self, term):
        """获取术语的同义词"""
        synonyms_dict = {
            "症状分析": ["症状", "表现", "临床表现", "症候", "症状描述"],
            "可能病因": ["病因", "病理", "发病原因", "致病因素", "病因学"],
            "建议措施": ["建议", "措施", "方法", "处理", "应对", "对策"],
            "注意事项": ["注意", "提示", "警告", "忌讳", "禁忌", "慎用"],
            "药物作用": ["作用", "功效", "药效", "药理", "机制", "适应症"],
            "用法用量": ["用法", "用量", "服法", "服用方法", "剂量", "给药"],
            "不良反应": ["副作用", "不良反应", "毒副作用", "不良事件", "药物反应"],
            "禁忌症": ["禁忌", "慎用", "忌用", "不宜", "禁用", "不适用"],
            "治疗目标": ["目标", "目的", "预期", "期望", "治疗目的"],
            "治疗方法": ["方法", "手段", "措施", "疗法", "治疗手段", "治疗措施"],
            "预期效果": ["效果", "疗效", "结果", "预后", "预期", "预计"],
            "风险提示": ["风险", "危险", "不良后果", "副作用", "并发症", "后遗症"],
            "生活方式": ["生活", "习惯", "日常", "起居", "作息", "生活习惯"],
            "饮食建议": ["饮食", "饮食指导", "饮食安排", "饮食调理", "饮食疗法"],
            "运动建议": ["运动", "锻炼", "活动", "体育", "健身", "运动疗法"],
            "预防措施": ["预防", "防治", "防范", "预防措施", "防护", "预防方法"]
        }
        
        return synonyms_dict.get(term, [term])
    
    def _extract_keywords(self, text):
        """提取文本中的关键词"""
        # 去除停用词
        stopwords = set(["的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"])
        
        # 分词（简单按空格和标点符号分）
        words = re.findall(r'\w+', text)
        
        # 过滤停用词和短词
        keywords = [w for w in words if w not in stopwords and len(w) > 1]
        
        # 返回频率最高的几个词
        counter = Counter(keywords)
        return [word for word, _ in counter.most_common(5)]

# 测试代码
if __name__ == "__main__":
    evaluator = KnowledgeEvaluator()
    
    # 测试用例
    test_cases = [
        {
            "knowledge_item": {
                "cleaned_response": "从中医角度看，您的症状表现为风热犯肺。风热犯肺主要表现为发热、咳嗽、痰黄或白、口干、咽痛等症状。建议服用银翘散或桑菊饮加减治疗。同时可以配合穴位按摩，如合谷穴、风门穴等。平时注意多休息，多饮水，避免辛辣刺激性食物。如症状加重或持续不退，建议及时就医。\n\n免责声明：本回答仅供参考，不构成医疗建议。如有健康问题，请咨询专业医生。"
            },
            "query": "我最近咳嗽严重，还有点发烧，该怎么办？",
            "intent_data": {
                "domain": "中医",
                "intent_type": "诊断咨询",
                "urgency": "中"
            }
        },
        {
            "knowledge_item": {
                "cleaned_response": "阿莫西林（羟氨苄青霉素）和头孢类抗生素同属于β-内酰胺类抗生素，但化学结构不同。同时服用可能会出现以下不良反应：\n\n1. 增加肾脏负担：两种药物都经肾脏排泄，同时使用可能增加肾脏负担。\n\n2. 增加肝脏代谢压力：可能导致肝功能异常。\n\n3. 增加过敏反应风险：如果对青霉素过敏，与头孢类可能存在交叉过敏。\n\n4. 肠道菌群失调：双重抗生素可能导致更严重的肠道菌群紊乱，引起腹泻等症状。\n\n建议不要同时服用这两类药物，应在医生指导下选择一种适合的抗生素。如已同时服用，请多饮水，观察是否出现不适症状，必要时就医。\n\n参考依据：《药物学大全》2024版\n生成时间：2025-05-21 10:58:42\n\n免责声明：本回答仅供参考，不构成医疗建议。如有健康问题，请咨询专业医生。"
            },
            "query": "阿莫西林和头孢一起吃有什么副作用？",
            "intent_data": {
                "domain": "药理学",
                "intent_type": "药物查询",
                "urgency": "中"
            }
        },
        {
            "knowledge_item": {
                "cleaned_response": "您好！根据您的描述，这是一个紧急情况，需要立即处理！\n\n胸痛伴呼吸困难可能是心肌梗死、主动脉夹层、肺栓塞等危及生命的疾病表现。请立即拨打急救电话（120）或尽快前往最近的医院急诊科！\n\n在等待救援的过程中：\n1. 让患者保持半卧位，减轻呼吸困难\n2. 不要让患者走动或用力\n3. 如有阿司匹林且患者无出血倾向，可嚼服一片阿司匹林（100mg）\n4. 保持镇定，记录症状发作时间和变化情况\n\n警告：此类症状需要专业医疗评估和处理，自行处理可能延误病情！\n\n信息有效期：6个月\n参考依据：《临床医学指南》2024版\n生成时间：2025-05-21 10:59:15\n\n警告：如果您正在经历紧急医疗情况，请立即拨打急救电话或前往最近的急诊室。 免责声明：本回答仅供参考，不构成医疗建议。如有健康问题，请咨询专业医生。"
            },
            "query": "我父亲突然胸痛，呼吸困难，情况很紧急！",
            "intent_data": {
                "domain": "西医",
                "intent_type": "诊断咨询",
                "urgency": "高"
            }
        }
    ]
    
    for i, test in enumerate(test_cases):
        print(f"\n测试用例 {i+1}:")
        print(f"查询: {test['query']}")
        print(f"领域: {test['intent_data']['domain']}, 意图: {test['intent_data']['intent_type']}")
        
        result = evaluator.evaluate(test['knowledge_item'], test['query'], test['intent_data'])
        
        print(f"总分: {result['total_score']:.2f}")
        print(f"专业性: {result['detailed_scores']['professionalism']:.2f}")
        print(f"完整性: {result['detailed_scores']['completeness']:.2f}")
        print(f"可读性: {result['detailed_scores']['readability']:.2f}")
        print(f"安全性: {result['detailed_scores']['safety']:.2f}")
        print("-" * 50)
