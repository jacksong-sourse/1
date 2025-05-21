"""
统一对话API模块
功能：提供统一的对话接口，整合意图解析、模型路由、知识清洗和存储等功能
"""

import json
import uuid
import logging
import datetime
from flask import Blueprint, request, jsonify

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DialogueAPI:
    def __init__(self, intent_parser, model_router, knowledge_cleaner, knowledge_evaluator, knowledge_repository, feedback_optimizer):
        """
        初始化对话API
        
        参数:
            intent_parser: 意图解析器实例
            model_router: 模型路由器实例
            knowledge_cleaner: 知识清洗器实例
            knowledge_evaluator: 知识评估器实例
            knowledge_repository: 知识库实例
            feedback_optimizer: 反馈优化器实例
        """
        self.intent_parser = intent_parser
        self.model_router = model_router
        self.knowledge_cleaner = knowledge_cleaner
        self.knowledge_evaluator = knowledge_evaluator
        self.knowledge_repository = knowledge_repository
        self.feedback_optimizer = feedback_optimizer
        
        # 创建Flask蓝图
        self.api_blueprint = Blueprint('api', __name__)
        
        # 注册路由
        self._register_routes()
        
        logger.info("对话API初始化完成")
    
    def _register_routes(self):
        """注册API路由"""
        # 对话接口
        self.api_blueprint.route('/chat', methods=['POST'])(self.chat)
        
        # 反馈接口
        self.api_blueprint.route('/feedback', methods=['POST'])(self.feedback)
        
        # 历史记录接口
        self.api_blueprint.route('/history', methods=['GET'])(self.get_history)
        
        # 系统状态接口
        self.api_blueprint.route('/status', methods=['GET'])(self.get_status)
    
    def chat(self):
        """
        处理对话请求
        
        请求参数:
            query: 用户查询
            user_id: 用户ID
            session_id: 会话ID (可选)
            context: 上下文信息 (可选)
            
        返回:
            JSON响应，包含回答和元数据
        """
        try:
            # 获取请求数据
            data = request.json
            query = data.get('query')
            user_id = data.get('user_id')
            session_id = data.get('session_id', str(uuid.uuid4()))
            context = data.get('context', {})
            
            if not query or not user_id:
                return jsonify({
                    'status': 'error',
                    'message': '缺少必要参数'
                }), 400
            
            # 记录请求
            logger.info(f"收到对话请求 - 用户: {user_id}, 会话: {session_id}, 查询: {query}")
            
            # 步骤1: 意图解析
            intent_data = self.intent_parser.parse(query)
            logger.info(f"意图解析结果 - 领域: {intent_data['domain']}, 意图: {intent_data['intent_type']}, 紧急程度: {intent_data['urgency']}")
            
            # 步骤2: 检索知识库
            knowledge_items = self.knowledge_repository.retrieve(query, intent_data)
            
            # 如果找到高质量的知识项，直接返回
            if knowledge_items and knowledge_items[0]['tier'] == 'core' and knowledge_items[0]['quality_score'] >= 0.9:
                knowledge_id = knowledge_items[0]['id']
                response = knowledge_items[0]['cleaned_response']
                
                # 记录隐性反馈（知识库命中）
                self.feedback_optimizer.process_implicit_feedback(knowledge_id, user_id, 'knowledge_hit', intent_data)
                
                logger.info(f"知识库命中高质量回答 - ID: {knowledge_id}")
                
                return jsonify({
                    'status': 'success',
                    'response': response,
                    'knowledge_id': knowledge_id,
                    'session_id': session_id,
                    'source': 'knowledge_repository',
                    'metadata': {
                        'domain': intent_data['domain'],
                        'intent_type': intent_data['intent_type'],
                        'urgency': intent_data['urgency'],
                        'quality_score': knowledge_items[0]['quality_score']
                    }
                })
            
            # 步骤3: 模型路由和推理
            model_response = self.model_router.route(query, intent_data)
            logger.info(f"模型生成回答 - 长度: {len(model_response)}")
            
            # 步骤4: 知识清洗
            knowledge_item = self.knowledge_cleaner.process({
                'original_response': model_response,
                'cleaned_response': model_response,
                'metadata': {
                    'intent_data': intent_data,
                    'context': context,
                    'session_id': session_id,
                    'timestamp': datetime.datetime.now().isoformat()
                }
            }, intent_data)
            
            # 步骤5: 知识质量评估
            evaluation_result = self.knowledge_evaluator.evaluate(knowledge_item, query, intent_data)
            quality_score = evaluation_result['total_score']
            logger.info(f"知识质量评估 - 分数: {quality_score:.2f}")
            
            # 步骤6: 存储到知识库
            knowledge_id = self.knowledge_repository.store(knowledge_item, query, intent_data, quality_score)
            
            # 返回响应
            return jsonify({
                'status': 'success',
                'response': knowledge_item['cleaned_response'],
                'knowledge_id': knowledge_id,
                'session_id': session_id,
                'source': 'model_inference',
                'metadata': {
                    'domain': intent_data['domain'],
                    'intent_type': intent_data['intent_type'],
                    'urgency': intent_data['urgency'],
                    'quality_score': quality_score,
                    'detailed_scores': evaluation_result['detailed_scores']
                }
            })
        except Exception as e:
            logger.error(f"处理对话请求失败: {e}")
            return jsonify({
                'status': 'error',
                'message': '处理请求时发生错误',
                'error': str(e)
            }), 500
    
    def feedback(self):
        """
        处理反馈请求
        
        请求参数:
            knowledge_id: 知识项ID
            user_id: 用户ID
            score: 评分 (0-1)
            comment: 评论 (可选)
            behavior: 行为类型 (可选，用于隐性反馈)
            
        返回:
            JSON响应，表示处理结果
        """
        try:
            # 获取请求数据
            data = request.json
            knowledge_id = data.get('knowledge_id')
            user_id = data.get('user_id')
            score = data.get('score')
            comment = data.get('comment')
            behavior = data.get('behavior')
            
            if not knowledge_id or not user_id:
                return jsonify({
                    'status': 'error',
                    'message': '缺少必要参数'
                }), 400
            
            # 处理显性反馈
            if score is not None:
                success = self.feedback_optimizer.process_explicit_feedback(
                    knowledge_id, user_id, score, comment
                )
                
                logger.info(f"处理显性反馈 - 知识项: {knowledge_id}, 用户: {user_id}, 评分: {score}, 结果: {'成功' if success else '失败'}")
                
                return jsonify({
                    'status': 'success' if success else 'error',
                    'message': '反馈已处理' if success else '处理反馈失败'
                })
            
            # 处理隐性反馈
            elif behavior:
                success = self.feedback_optimizer.process_implicit_feedback(
                    knowledge_id, user_id, behavior
                )
                
                logger.info(f"处理隐性反馈 - 知识项: {knowledge_id}, 用户: {user_id}, 行为: {behavior}, 结果: {'成功' if success else '失败'}")
                
                return jsonify({
                    'status': 'success' if success else 'error',
                    'message': '反馈已处理' if success else '处理反馈失败'
                })
            
            else:
                return jsonify({
                    'status': 'error',
                    'message': '缺少评分或行为参数'
                }), 400
        except Exception as e:
            logger.error(f"处理反馈请求失败: {e}")
            return jsonify({
                'status': 'error',
                'message': '处理请求时发生错误',
                'error': str(e)
            }), 500
    
    def get_history(self):
        """
        获取历史记录
        
        请求参数:
            user_id: 用户ID
            limit: 返回结果数量限制 (可选)
            
        返回:
            JSON响应，包含历史记录
        """
        try:
            # 获取请求参数
            user_id = request.args.get('user_id')
            limit = int(request.args.get('limit', 10))
            
            if not user_id:
                return jsonify({
                    'status': 'error',
                    'message': '缺少用户ID参数'
                }), 400
            
            # 获取历史记录
            history = self.knowledge_repository.get_user_history(user_id, limit)
            
            logger.info(f"获取历史记录 - 用户: {user_id}, 记录数: {len(history)}")
            
            return jsonify({
                'status': 'success',
                'history': history
            })
        except Exception as e:
            logger.error(f"获取历史记录失败: {e}")
            return jsonify({
                'status': 'error',
                'message': '处理请求时发生错误',
                'error': str(e)
            }), 500
    
    def get_status(self):
        """
        获取系统状态
        
        返回:
            JSON响应，包含系统状态信息
        """
        try:
            # 获取知识库统计信息
            repo_stats = self.knowledge_repository.get_statistics()
            
            # 获取反馈统计信息
            feedback_stats = self.feedback_optimizer.get_feedback_statistics()
            
            # 获取模型性能统计
            model_stats = self.model_router.get_model_statistics()
            
            # 组合状态信息
            status = {
                'status': 'online',
                'timestamp': datetime.datetime.now().isoformat(),
                'knowledge_repository': repo_stats,
                'feedback': feedback_stats,
                'models': model_stats
            }
            
            logger.info("获取系统状态")
            
            return jsonify(status)
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return jsonify({
                'status': 'error',
                'message': '处理请求时发生错误',
                'error': str(e)
            }), 500
    
    def get_blueprint(self):
        """获取API蓝图"""
        return self.api_blueprint

# 测试代码
if __name__ == "__main__":
    from flask import Flask
    
    # 创建模拟组件
    class MockComponent:
        def __init__(self, name):
            self.name = name
        
        def __getattr__(self, name):
            def mock_method(*args, **kwargs):
                print(f"调用 {self.name}.{name} 方法")
                if name == 'parse':
                    return {
                        'domain': '中医',
                        'intent_type': '诊断咨询',
                        'urgency': '中',
                        'entities': []
                    }
                elif name == 'route':
                    return "这是模型生成的回答。"
                elif name == 'process':
                    return args[0]
                elif name == 'evaluate':
                    return {'total_score': 0.85, 'detailed_scores': {}}
                elif name == 'store':
                    return 'ki_' + str(uuid.uuid4())
                elif name == 'retrieve':
                    return []
                elif name == 'get_statistics':
                    return {'total_items': 100}
                elif name == 'get_feedback_statistics':
                    return {'total_feedback': 50}
                elif name == 'get_model_statistics':
                    return {'model1': {'calls': 100}}
                return True
            return mock_method
    
    # 创建模拟组件
    intent_parser = MockComponent('intent_parser')
    model_router = MockComponent('model_router')
    knowledge_cleaner = MockComponent('knowledge_cleaner')
    knowledge_evaluator = MockComponent('knowledge_evaluator')
    knowledge_repository = MockComponent('knowledge_repository')
    feedback_optimizer = MockComponent('feedback_optimizer')
    
    # 创建对话API
    api = DialogueAPI(
        intent_parser, model_router, knowledge_cleaner,
        knowledge_evaluator, knowledge_repository, feedback_optimizer
    )
    
    # 创建Flask应用
    app = Flask(__name__)
    app.register_blueprint(api.get_blueprint(), url_prefix='/api')
    
    # 启动应用
    if __name__ == "__main__":
        app.run(debug=True, host='0.0.0.0', port=5000)
