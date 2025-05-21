"""
知识清洗流水线模块
功能：对模型生成的初步回答进行标准化处理、冲突校验和时效性标记
"""

import re
import json
import datetime
import logging
from html import unescape

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeCleaner:
    def __init__(self, config_file=None):
        """
        初始化知识清洗流水线
        
        参数:
            config_file (str, optional): 配置文件路径，如果不提供则使用默认配置
        """
        # 默认清洗规则
        self.default_rules = {
            "format_rules": {
                "remove_html_tags": True,
                "normalize_whitespace": True,
                "standardize_punctuation": True,
                "remove_duplicate_spaces": True,
                "normalize_line_breaks": True
            },
            "content_rules": {
                "add_disclaimer": True,
                "check_medical_terms": True,
                "check_drug_names": True,
                "standardize_units": True,
                "check_dosage_format": True
            },
            "timestamp_rules": {
                "add_generation_time": True,
                "add_reference_version": True,
                "add_expiry_indicator": True
            }
        }
        
        # 医学术语标准化词典
        self.medical_terms_dict = {
            "感冒": "上呼吸道感染",
            "发烧": "发热",
            "头疼": "头痛",
            "心口痛": "胸痛",
            "肚子痛": "腹痛",
            "拉肚子": "腹泻",
            "上火": "热证",
            "心慌": "心悸",
            "气短": "呼吸短促",
            "没劲": "乏力",
            # 更多术语...
        }
        
        # 中医术语标准化词典
        self.tcm_terms_dict = {
            "上火": "热证",
            "肝火": "肝火旺盛",
            "气虚": "气虚证",
            "血虚": "血虚证",
            "阴虚": "阴虚证",
            "阳虚": "阳虚证",
            "痰湿": "痰湿证",
            "湿热": "湿热证",
            "寒湿": "寒湿证",
            "气滞": "气滞证",
            "血瘀": "血瘀证",
            # 更多术语...
        }
        
        # 药物名称标准化词典
        self.drug_names_dict = {
            "阿司匹林": "乙酰水杨酸",
            "扑热息痛": "对乙酰氨基酚",
            "泰诺": "对乙酰氨基酚",
            "布洛芬": "异丁苯丙酸",
            "先锋霉素": "头孢拉定",
            "阿莫西林": "羟氨苄青霉素",
            # 更多药物...
        }
        
        # 单位标准化词典
        self.units_dict = {
            "CC": "ml",
            "ML": "ml",
            "毫升": "ml",
            "MG": "mg",
            "毫克": "mg",
            "微克": "μg",
            "MCG": "μg",
            "G": "g",
            "克": "g",
            "IU": "IU",
            "国际单位": "IU",
            # 更多单位...
        }
        
        # 免责声明模板
        self.disclaimer_templates = {
            "general": "免责声明：本回答仅供参考，不构成医疗建议。如有健康问题，请咨询专业医生。",
            "emergency": "警告：如果您正在经历紧急医疗情况，请立即拨打急救电话或前往最近的急诊室。",
            "medication": "用药提示：药物使用请遵医嘱，不同个体可能有不同反应。",
            "tcm": "中医提示：中医诊疗应当由专业中医师进行辨证论治，本回答仅供参考。"
        }
        
        # 加载配置
        if config_file:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.cleaning_rules = config.get("cleaning_rules", self.default_rules)
                    
                    # 合并词典
                    self.medical_terms_dict.update(config.get("medical_terms_dict", {}))
                    self.tcm_terms_dict.update(config.get("tcm_terms_dict", {}))
                    self.drug_names_dict.update(config.get("drug_names_dict", {}))
                    self.units_dict.update(config.get("units_dict", {}))
                    self.disclaimer_templates.update(config.get("disclaimer_templates", {}))
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                self.cleaning_rules = self.default_rules
        else:
            self.cleaning_rules = self.default_rules
        
        logger.info("知识清洗流水线初始化完成")
    
    def process(self, model_response, intent_data):
        """
        处理模型输出，应用清洗流水线
        
        参数:
            model_response (str): 模型原始输出
            intent_data (dict): 意图解析数据
            
        返回:
            dict: 清洗后的知识项，包含原始回答、清洗后回答和元数据
        """
        logger.info("开始知识清洗流程")
        
        # 创建知识项
        knowledge_item = {
            "original_response": model_response,
            "cleaned_response": model_response,
            "metadata": {
                "cleaning_timestamp": datetime.datetime.now().isoformat(),
                "intent_data": intent_data,
                "cleaning_steps": []
            }
        }
        
        # 步骤1: 格式标准化
        knowledge_item = self._format_standardization(knowledge_item)
        
        # 步骤2: 内容规范化
        knowledge_item = self._content_normalization(knowledge_item, intent_data)
        
        # 步骤3: 时效性标记
        knowledge_item = self._add_timestamp(knowledge_item, intent_data)
        
        logger.info("知识清洗流程完成")
        
        return knowledge_item
    
    def _format_standardization(self, knowledge_item):
        """格式标准化处理"""
        response = knowledge_item["cleaned_response"]
        steps = []
        
        # 移除HTML标签
        if self.cleaning_rules["format_rules"]["remove_html_tags"]:
            original_length = len(response)
            response = re.sub(r'<[^>]+>', '', response)
            response = unescape(response)  # 处理HTML实体
            if len(response) != original_length:
                steps.append("移除HTML标签")
        
        # 标准化空白字符
        if self.cleaning_rules["format_rules"]["normalize_whitespace"]:
            original_length = len(response)
            response = re.sub(r'\s+', ' ', response)
            if len(response) != original_length:
                steps.append("标准化空白字符")
        
        # 标准化标点符号
        if self.cleaning_rules["format_rules"]["standardize_punctuation"]:
            original = response
            # 中文标点规范化
            response = re.sub(r'。{2,}', '。', response)  # 多个句号替换为一个
            response = re.sub(r'，{2,}', '，', response)  # 多个逗号替换为一个
            response = re.sub(r'！{2,}', '！', response)  # 多个感叹号替换为一个
            response = re.sub(r'？{2,}', '？', response)  # 多个问号替换为一个
            
            # 中英文标点混用规范化
            response = response.replace(',', '，')
            response = response.replace('!', '！')
            response = response.replace('?', '？')
            response = response.replace(';', '；')
            response = response.replace(':', '：')
            
            if original != response:
                steps.append("标准化标点符号")
        
        # 移除重复空格
        if self.cleaning_rules["format_rules"]["remove_duplicate_spaces"]:
            original_length = len(response)
            response = re.sub(r' +', ' ', response)
            if len(response) != original_length:
                steps.append("移除重复空格")
        
        # 标准化换行符
        if self.cleaning_rules["format_rules"]["normalize_line_breaks"]:
            original_length = len(response)
            response = re.sub(r'\n{3,}', '\n\n', response)  # 多个换行替换为两个
            if len(response) != original_length:
                steps.append("标准化换行符")
        
        # 更新知识项
        knowledge_item["cleaned_response"] = response
        knowledge_item["metadata"]["cleaning_steps"].extend(steps)
        
        return knowledge_item
    
    def _content_normalization(self, knowledge_item, intent_data):
        """内容规范化处理"""
        response = knowledge_item["cleaned_response"]
        domain = intent_data.get("domain", "通用医学")
        intent_type = intent_data.get("intent_type", "诊断咨询")
        urgency = intent_data.get("urgency", "低")
        steps = []
        
        # 医学术语标准化
        if self.cleaning_rules["content_rules"]["check_medical_terms"]:
            original = response
            for term, standard in self.medical_terms_dict.items():
                # 使用正则表达式确保只替换完整词汇，而不是词汇的一部分
                response = re.sub(r'\b' + re.escape(term) + r'\b', standard, response)
            
            # 中医领域特殊处理
            if domain == "中医":
                for term, standard in self.tcm_terms_dict.items():
                    response = re.sub(r'\b' + re.escape(term) + r'\b', standard, response)
            
            if original != response:
                steps.append("医学术语标准化")
        
        # 药物名称标准化
        if self.cleaning_rules["content_rules"]["check_drug_names"] and "药物" in intent_type:
            original = response
            for drug, standard in self.drug_names_dict.items():
                # 添加药物标准名称，但保留原名称
                pattern = r'\b' + re.escape(drug) + r'\b(?!\s*[（(]' + re.escape(standard) + r'[)）])'
                replacement = drug + '（' + standard + '）'
                response = re.sub(pattern, replacement, response)
            
            if original != response:
                steps.append("药物名称标准化")
        
        # 单位标准化
        if self.cleaning_rules["content_rules"]["standardize_units"]:
            original = response
            for unit, standard in self.units_dict.items():
                # 匹配数字后面的单位
                pattern = r'(\d+)\s*' + re.escape(unit) + r'\b'
                replacement = r'\1 ' + standard
                response = re.sub(pattern, replacement, response)
            
            if original != response:
                steps.append("单位标准化")
        
        # 剂量格式检查
        if self.cleaning_rules["content_rules"]["check_dosage_format"] and "药物" in intent_type:
            original = response
            # 检查常见的剂量格式问题
            # 例如：将"每日3次，每次1片"标准化为"每日3次，每次1片"
            response = re.sub(r'每天(\d+)次', r'每日\1次', response)
            response = re.sub(r'一天(\d+)次', r'每日\1次', response)
            
            if original != response:
                steps.append("剂量格式标准化")
        
        # 添加免责声明
        if self.cleaning_rules["content_rules"]["add_disclaimer"]:
            # 根据不同情况选择不同的免责声明
            disclaimer = self.disclaimer_templates["general"]
            
            if urgency == "高":
                disclaimer = self.disclaimer_templates["emergency"] + " " + disclaimer
            
            if "药物" in intent_type:
                disclaimer = self.disclaimer_templates["medication"] + " " + disclaimer
            
            if domain == "中医":
                disclaimer = self.disclaimer_templates["tcm"] + " " + disclaimer
            
            # 添加免责声明到回答末尾
            if not response.endswith(disclaimer):
                response = response + "\n\n" + disclaimer
                steps.append("添加免责声明")
        
        # 更新知识项
        knowledge_item["cleaned_response"] = response
        knowledge_item["metadata"]["cleaning_steps"].extend(steps)
        
        return knowledge_item
    
    def _add_timestamp(self, knowledge_item, intent_data):
        """添加时效性标记"""
        response = knowledge_item["cleaned_response"]
        steps = []
        
        # 当前时间
        now = datetime.datetime.now()
        
        # 添加生成时间
        if self.cleaning_rules["timestamp_rules"]["add_generation_time"]:
            timestamp_str = f"生成时间：{now.strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 检查是否已有时间戳
            if "生成时间" not in response:
                # 在免责声明前添加时间戳
                if "免责声明" in response:
                    parts = response.split("免责声明", 1)
                    response = parts[0] + timestamp_str + "\n\n免责声明" + parts[1]
                else:
                    response = response + "\n\n" + timestamp_str
                
                steps.append("添加生成时间")
        
        # 添加参考版本
        if self.cleaning_rules["timestamp_rules"]["add_reference_version"]:
            # 根据不同领域添加不同的参考版本
            domain = intent_data.get("domain", "通用医学")
            version_str = ""
            
            if domain == "中医":
                version_str = "参考依据：《中医药学参考大典》2024版"
            elif domain == "西医":
                version_str = "参考依据：《临床医学指南》2024版"
            elif domain == "药理学":
                version_str = "参考依据：《药物学大全》2024版"
            else:
                version_str = "参考依据：《医学知识库》2024版"
            
            # 检查是否已有参考版本
            if "参考依据" not in response:
                # 在时间戳后或免责声明前添加参考版本
                if "生成时间" in response:
                    response = response.replace("生成时间", version_str + "\n生成时间")
                elif "免责声明" in response:
                    parts = response.split("免责声明", 1)
                    response = parts[0] + version_str + "\n\n免责声明" + parts[1]
                else:
                    response = response + "\n\n" + version_str
                
                steps.append("添加参考版本")
        
        # 添加有效期指示
        if self.cleaning_rules["timestamp_rules"]["add_expiry_indicator"]:
            # 根据不同领域设置不同的有效期
            domain = intent_data.get("domain", "通用医学")
            intent_type = intent_data.get("intent_type", "诊断咨询")
            
            expiry_str = ""
            if "药物" in intent_type:
                expiry_str = "信息有效期：6个月"
            elif "治疗" in intent_type:
                expiry_str = "信息有效期：1年"
            elif domain == "中医":
                expiry_str = "信息有效期：2年"
            else:
                expiry_str = "信息有效期：1年"
            
            # 检查是否已有有效期
            if "信息有效期" not in response:
                # 在参考版本后或时间戳后添加有效期
                if "参考依据" in response:
                    response = response.replace("参考依据", expiry_str + "\n参考依据")
                elif "生成时间" in response:
                    response = response.replace("生成时间", expiry_str + "\n生成时间")
                elif "免责声明" in response:
                    parts = response.split("免责声明", 1)
                    response = parts[0] + expiry_str + "\n\n免责声明" + parts[1]
                else:
                    response = response + "\n\n" + expiry_str
                
                steps.append("添加有效期指示")
        
        # 更新知识项
        knowledge_item["cleaned_response"] = response
        knowledge_item["metadata"]["cleaning_steps"].extend(steps)
        
        return knowledge_item

# 测试代码
if __name__ == "__main__":
    cleaner = KnowledgeCleaner()
    
    # 测试用例
    test_cases = [
        {
            "response": "<p>患者出现咳嗽、发烧症状，可能是感冒或上呼吸道感染。建议多喝水，休息，可服用布洛芬退烧。</p>",
            "intent_data": {
                "domain": "西医",
                "intent_type": "诊断咨询",
                "urgency": "中"
            }
        },
        {
            "response": "根据症状分析，患者可能是肝火旺盛，建议服用龙胆泻肝汤调理。每天3次，每次1剂。",
            "intent_data": {
                "domain": "中医",
                "intent_type": "药物查询",
                "urgency": "低"
            }
        },
        {
            "response": "阿司匹林每日剂量不应超过4G，过量可能导致胃出血等不良反应！！！",
            "intent_data": {
                "domain": "药理学",
                "intent_type": "药物查询",
                "urgency": "高"
            }
        }
    ]
    
    for i, test in enumerate(test_cases):
        print(f"\n测试用例 {i+1}:")
        print(f"原始回答: {test['response']}")
        
        result = cleaner.process(test['response'], test['intent_data'])
        
        print(f"清洗后回答: {result['cleaned_response']}")
        print(f"清洗步骤: {result['metadata']['cleaning_steps']}")
        print("-" * 50)
