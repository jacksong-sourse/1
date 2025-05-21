"""
三级知识库存储模块
功能：实现核心库、扩展库、临时库的分级存储结构，支持知识项的存储、检索和生命周期管理
"""

import os
import json
import time
import logging
import datetime
import sqlite3
from collections import defaultdict

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeRepository:
    """三级知识库存储系统"""
    
    def __init__(self, db_path=None):
        """
        初始化知识库
        
        参数:
            db_path (str, optional): 数据库文件路径，如果不提供则使用内存数据库
        """
        # 设置数据库路径
        self.db_path = db_path or ":memory:"
        
        # 初始化数据库
        self._init_database()
        
        # 设置知识库等级阈值
        self.tier_thresholds = {
            "core": 0.85,    # 核心库质量阈值
            "extended": 0.7,  # 扩展库质量阈值
            # 低于扩展库阈值的进入临时库
        }
        
        # 设置知识项过期时间（秒）
        self.expiry_times = {
            "core": 180 * 24 * 60 * 60,      # 核心库：180天
            "extended": 90 * 24 * 60 * 60,   # 扩展库：90天
            "temporary": 30 * 24 * 60 * 60   # 临时库：30天
        }
        
        logger.info(f"知识库初始化完成，数据库路径: {self.db_path}")
    
    def _init_database(self):
        """初始化数据库表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建知识项表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_items (
                id TEXT PRIMARY KEY,
                query TEXT,
                original_response TEXT,
                cleaned_response TEXT,
                domain TEXT,
                intent_type TEXT,
                tier TEXT,
                quality_score REAL,
                feedback_score REAL DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                expires_at TEXT,
                metadata TEXT
            )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_domain_intent ON knowledge_items (domain, intent_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tier ON knowledge_items (tier)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_expires_at ON knowledge_items (expires_at)')
            
            # 创建关键词表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                keyword TEXT,
                knowledge_id TEXT,
                weight REAL,
                PRIMARY KEY (keyword, knowledge_id),
                FOREIGN KEY (knowledge_id) REFERENCES knowledge_items (id) ON DELETE CASCADE
            )
            ''')
            
            # 创建关键词索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_keyword ON keywords (keyword)')
            
            # 创建用户反馈表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_id TEXT,
                user_id TEXT,
                score REAL,
                comment TEXT,
                created_at TEXT,
                FOREIGN KEY (knowledge_id) REFERENCES knowledge_items (id) ON DELETE CASCADE
            )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("数据库表结构初始化完成")
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
            raise
    
    def store(self, knowledge_item, query, intent_data, quality_score):
        """
        存储知识项到适当的知识库层级
        
        参数:
            knowledge_item (dict): 知识项，包含原始回答、清洗后回答和元数据
            query (str): 用户查询
            intent_data (dict): 意图解析数据
            quality_score (float): 知识质量评分
            
        返回:
            str: 知识项ID
        """
        try:
            # 生成知识项ID
            knowledge_id = self._generate_id()
            
            # 确定知识库层级
            tier = self._determine_tier(quality_score)
            
            # 设置过期时间
            expires_at = datetime.datetime.now() + datetime.timedelta(seconds=self.expiry_times[tier])
            
            # 提取领域和意图类型
            domain = intent_data.get("domain", "通用医学")
            intent_type = intent_data.get("intent_type", "诊断咨询")
            
            # 准备知识项数据
            now = datetime.datetime.now().isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 插入知识项
            cursor.execute('''
            INSERT INTO knowledge_items 
            (id, query, original_response, cleaned_response, domain, intent_type, 
             tier, quality_score, created_at, updated_at, expires_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                knowledge_id,
                query,
                knowledge_item["original_response"],
                knowledge_item["cleaned_response"],
                domain,
                intent_type,
                tier,
                quality_score,
                now,
                now,
                expires_at.isoformat(),
                json.dumps(knowledge_item["metadata"], ensure_ascii=False)
            ))
            
            # 提取并存储关键词
            keywords = self._extract_keywords(query, knowledge_item["cleaned_response"])
            for keyword, weight in keywords.items():
                cursor.execute('''
                INSERT INTO keywords (keyword, knowledge_id, weight)
                VALUES (?, ?, ?)
                ''', (keyword, knowledge_id, weight))
            
            conn.commit()
            conn.close()
            
            logger.info(f"知识项存储成功 - ID: {knowledge_id}, 层级: {tier}, 质量分数: {quality_score:.2f}")
            
            return knowledge_id
        except Exception as e:
            logger.error(f"存储知识项失败: {e}")
            raise
    
    def retrieve(self, query, intent_data, limit=5):
        """
        检索相关知识项
        
        参数:
            query (str): 用户查询
            intent_data (dict): 意图解析数据
            limit (int, optional): 返回结果数量限制
            
        返回:
            list: 相关知识项列表
        """
        try:
            # 提取领域和意图类型
            domain = intent_data.get("domain", "通用医学")
            intent_type = intent_data.get("intent_type", "诊断咨询")
            
            # 提取查询关键词
            query_keywords = set(self._simple_tokenize(query))
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
            cursor = conn.cursor()
            
            # 首先尝试精确匹配领域和意图
            cursor.execute('''
            SELECT k.*, GROUP_CONCAT(kw.keyword || ':' || kw.weight, ';') as keywords
            FROM knowledge_items k
            LEFT JOIN keywords kw ON k.id = kw.knowledge_id
            WHERE k.domain = ? AND k.intent_type = ? AND k.expires_at > ?
            GROUP BY k.id
            ORDER BY k.tier = 'core' DESC, k.tier = 'extended' DESC, k.quality_score DESC
            LIMIT ?
            ''', (domain, intent_type, datetime.datetime.now().isoformat(), limit))
            
            exact_matches = [dict(row) for row in cursor.fetchall()]
            
            # 如果精确匹配不足，尝试关键词匹配
            if len(exact_matches) < limit:
                remaining = limit - len(exact_matches)
                
                # 构建关键词查询
                placeholders = ','.join(['?'] * len(query_keywords))
                if placeholders:
                    cursor.execute(f'''
                    SELECT k.*, GROUP_CONCAT(kw.keyword || ':' || kw.weight, ';') as keywords,
                           COUNT(DISTINCT kw.keyword) as keyword_match_count
                    FROM knowledge_items k
                    JOIN keywords kw ON k.id = kw.knowledge_id
                    WHERE kw.keyword IN ({placeholders}) AND k.expires_at > ?
                    AND k.id NOT IN ({','.join(['?'] * len(exact_matches))})
                    GROUP BY k.id
                    ORDER BY keyword_match_count DESC, k.tier = 'core' DESC, k.tier = 'extended' DESC, k.quality_score DESC
                    LIMIT ?
                    ''', list(query_keywords) + [datetime.datetime.now().isoformat()] + 
                        [m['id'] for m in exact_matches] + [remaining])
                    
                    keyword_matches = [dict(row) for row in cursor.fetchall()]
                    exact_matches.extend(keyword_matches)
            
            # 更新使用计数
            for match in exact_matches:
                cursor.execute('''
                UPDATE knowledge_items
                SET usage_count = usage_count + 1
                WHERE id = ?
                ''', (match['id'],))
            
            conn.commit()
            
            # 解析关键词字符串
            for match in exact_matches:
                if match['keywords']:
                    keywords_dict = {}
                    for kw_pair in match['keywords'].split(';'):
                        if ':' in kw_pair:
                            kw, weight = kw_pair.split(':')
                            keywords_dict[kw] = float(weight)
                    match['keywords'] = keywords_dict
                else:
                    match['keywords'] = {}
                
                # 解析元数据JSON
                if match['metadata']:
                    match['metadata'] = json.loads(match['metadata'])
            
            conn.close()
            
            logger.info(f"检索到 {len(exact_matches)} 个相关知识项")
            
            return exact_matches
        except Exception as e:
            logger.error(f"检索知识项失败: {e}")
            return []
    
    def update_feedback(self, knowledge_id, user_id, score, comment=None):
        """
        更新知识项的用户反馈
        
        参数:
            knowledge_id (str): 知识项ID
            user_id (str): 用户ID
            score (float): 反馈评分 (0-1)
            comment (str, optional): 反馈评论
            
        返回:
            bool: 更新是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 记录用户反馈
            now = datetime.datetime.now().isoformat()
            cursor.execute('''
            INSERT INTO user_feedback (knowledge_id, user_id, score, comment, created_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (knowledge_id, user_id, score, comment, now))
            
            # 获取当前知识项信息
            cursor.execute('''
            SELECT tier, quality_score, feedback_score, usage_count
            FROM knowledge_items
            WHERE id = ?
            ''', (knowledge_id,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                logger.warning(f"知识项不存在: {knowledge_id}")
                return False
            
            current_tier, quality_score, feedback_score, usage_count = row
            
            # 计算新的反馈评分（加权平均）
            if feedback_score > 0:
                # 已有反馈，进行加权平均
                new_feedback_score = (feedback_score * 0.7) + (score * 0.3)
            else:
                # 首次反馈
                new_feedback_score = score
            
            # 计算综合评分（质量评分和反馈评分的加权平均）
            combined_score = (quality_score * 0.6) + (new_feedback_score * 0.4)
            
            # 确定新的知识库层级
            new_tier = self._determine_tier(combined_score)
            
            # 如果层级变化，更新过期时间
            expires_at = None
            if new_tier != current_tier:
                expires_at = (datetime.datetime.now() + 
                             datetime.timedelta(seconds=self.expiry_times[new_tier])).isoformat()
            
            # 更新知识项
            if expires_at:
                cursor.execute('''
                UPDATE knowledge_items
                SET feedback_score = ?, tier = ?, updated_at = ?, expires_at = ?
                WHERE id = ?
                ''', (new_feedback_score, new_tier, now, expires_at, knowledge_id))
            else:
                cursor.execute('''
                UPDATE knowledge_items
                SET feedback_score = ?, tier = ?, updated_at = ?
                WHERE id = ?
                ''', (new_feedback_score, new_tier, now, knowledge_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"用户反馈更新成功 - ID: {knowledge_id}, 新评分: {new_feedback_score:.2f}, 新层级: {new_tier}")
            
            return True
        except Exception as e:
            logger.error(f"更新用户反馈失败: {e}")
            return False
    
    def cleanup_expired(self):
        """
        清理过期的知识项
        
        返回:
            int: 清理的知识项数量
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取过期知识项数量
            cursor.execute('''
            SELECT COUNT(*) FROM knowledge_items
            WHERE expires_at < ?
            ''', (datetime.datetime.now().isoformat(),))
            
            expired_count = cursor.fetchone()[0]
            
            # 删除过期知识项
            cursor.execute('''
            DELETE FROM knowledge_items
            WHERE expires_at < ?
            ''', (datetime.datetime.now().isoformat(),))
            
            conn.commit()
            conn.close()
            
            logger.info(f"清理了 {expired_count} 个过期知识项")
            
            return expired_count
        except Exception as e:
            logger.error(f"清理过期知识项失败: {e}")
            return 0
    
    def get_statistics(self):
        """
        获取知识库统计信息
        
        返回:
            dict: 统计信息
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取各层级知识项数量
            cursor.execute('''
            SELECT tier, COUNT(*) as count
            FROM knowledge_items
            GROUP BY tier
            ''')
            
            tier_counts = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 获取各领域知识项数量
            cursor.execute('''
            SELECT domain, COUNT(*) as count
            FROM knowledge_items
            GROUP BY domain
            ''')
            
            domain_counts = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 获取总体统计
            cursor.execute('''
            SELECT 
                COUNT(*) as total_items,
                AVG(quality_score) as avg_quality,
                AVG(feedback_score) as avg_feedback,
                SUM(usage_count) as total_usage
            FROM knowledge_items
            ''')
            
            row = cursor.fetchone()
            overall_stats = {
                "total_items": row[0],
                "avg_quality": row[1] if row[1] is not None else 0,
                "avg_feedback": row[2] if row[2] is not None else 0,
                "total_usage": row[3] if row[3] is not None else 0
            }
            
            # 获取过期统计
            cursor.execute('''
            SELECT COUNT(*) as expiring_soon
            FROM knowledge_items
            WHERE expires_at < ? AND expires_at > ?
            ''', ((datetime.datetime.now() + datetime.timedelta(days=7)).isoformat(),
                  datetime.datetime.now().isoformat()))
            
            expiring_soon = cursor.fetchone()[0]
            
            conn.close()
            
            # 组合统计信息
            statistics = {
                "tier_counts": tier_counts,
                "domain_counts": domain_counts,
                "overall": overall_stats,
                "expiring_soon": expiring_soon
            }
            
            return statistics
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def _determine_tier(self, quality_score):
        """根据质量评分确定知识库层级"""
        if quality_score >= self.tier_thresholds["core"]:
            return "core"
        elif quality_score >= self.tier_thresholds["extended"]:
            return "extended"
        else:
            return "temporary"
    
    def _generate_id(self):
        """生成唯一的知识项ID"""
        timestamp = int(time.time() * 1000)
        random_part = os.urandom(4).hex()
        return f"ki_{timestamp}_{random_part}"
    
    def _extract_keywords(self, query, response):
        """
        从查询和回答中提取关键词
        
        返回:
            dict: 关键词到权重的映射
        """
        # 合并查询和回答文本
        combined_text = query + " " + response
        
        # 简单分词
        tokens = self._simple_tokenize(combined_text)
        
        # 计算词频
        word_freq = defaultdict(int)
        for token in tokens:
            word_freq[token] += 1
        
        # 计算权重（简化的TF-IDF）
        total_tokens = len(tokens)
        keywords = {}
        for word, freq in word_freq.items():
            if len(word) > 1:  # 忽略单字词
                # 简化的权重计算：词频/总词数
                keywords[word] = freq / total_tokens
        
        # 只保留权重最高的前20个关键词
        sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return dict(sorted_keywords)
    
    def _simple_tokenize(self, text):
        """简单的中文分词"""
        # 去除标点符号
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # 按空格分词
        tokens = text.split()
        
        # 对于中文，进行字符级分词（实际应用中应使用专业分词工具）
        result = []
        for token in tokens:
            if any('\u4e00' <= char <= '\u9fff' for char in token):
                # 中文字符，按2-3个字符组合
                for i in range(len(token)):
                    if i + 1 < len(token):
                        result.append(token[i:i+2])
                    if i + 2 < len(token):
                        result.append(token[i:i+3])
            else:
                result.append(token)
        
        return result

# 测试代码
if __name__ == "__main__":
    import tempfile
    
    # 创建临时数据库文件
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp:
        db_path = temp.name
    
    # 初始化知识库
    repo = KnowledgeRepository(db_path)
    
    # 测试知识项
    test_item = {
        "original_response": "患者出现咳嗽、发烧症状，可能是感冒或上呼吸道感染。建议多喝水，休息，可服用布洛芬退烧。",
        "cleaned_response": "患者出现咳嗽、发热症状，可能是上呼吸道感染。建议多饮水，充分休息，可服用对乙酰氨基酚或异丁苯丙酸退热。如症状持续超过3天，请及时就医。\n\n免责声明：本回答仅供参考，不构成医疗建议。如有健康问题，请咨询专业医生。",
        "metadata": {
            "cleaning_steps": ["医学术语标准化", "药物名称标准化", "添加免责声明"]
        }
    }
    
    # 测试意图数据
    test_intent = {
        "domain": "西医",
        "intent_type": "诊断咨询",
        "urgency": "中"
    }
    
    # 测试存储
    print("测试存储知识项...")
    knowledge_id = repo.store(test_item, "我最近咳嗽严重，还有点发烧，该怎么办？", test_intent, 0.85)
    print(f"存储的知识项ID: {knowledge_id}")
    
    # 测试检索
    print("\n测试检索知识项...")
    results = repo.retrieve("我有咳嗽和发烧症状", test_intent)
    print(f"检索到 {len(results)} 个知识项")
    for i, result in enumerate(results):
        print(f"结果 {i+1}:")
        print(f"  ID: {result['id']}")
        print(f"  层级: {result['tier']}")
        print(f"  质量分数: {result['quality_score']}")
        print(f"  回答: {result['cleaned_response'][:100]}...")
    
    # 测试反馈更新
    print("\n测试更新反馈...")
    success = repo.update_feedback(knowledge_id, "user123", 0.9, "很有帮助的回答")
    print(f"反馈更新{'成功' if success else '失败'}")
    
    # 测试统计信息
    print("\n测试获取统计信息...")
    stats = repo.get_statistics()
    print(f"知识库统计: {json.dumps(stats, indent=2)}")
    
    # 清理临时文件
    import os
    os.unlink(db_path)
    print(f"\n清理临时数据库文件: {db_path}")
