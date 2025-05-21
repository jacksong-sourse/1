import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # DON'T CHANGE THIS !!!

from flask import Flask, render_template, send_from_directory
from src.api.dialogue_api import DialogueAPI
from src.intelligent_dispatch.intent_parser import IntentParser
from src.intelligent_dispatch.model_router import ModelRouter
from src.intelligent_dispatch.matching_matrix import MatchingMatrix
from src.knowledge_production.knowledge_cleaner import KnowledgeCleaner
from src.knowledge_production.knowledge_evaluator import KnowledgeEvaluator
from src.knowledge_store.knowledge_repository import KnowledgeRepository
from src.knowledge_store.feedback_optimizer import FeedbackOptimizer

# 创建应用实例
app = Flask(__name__)

# 初始化组件
intent_parser = IntentParser()
matching_matrix = MatchingMatrix()
model_router = ModelRouter(matching_matrix)
knowledge_cleaner = KnowledgeCleaner()
knowledge_evaluator = KnowledgeEvaluator()
knowledge_repository = KnowledgeRepository(db_path='knowledge.db')
feedback_optimizer = FeedbackOptimizer(matching_matrix, knowledge_repository)

# 初始化API
dialogue_api = DialogueAPI(
    intent_parser, 
    model_router, 
    knowledge_cleaner, 
    knowledge_evaluator, 
    knowledge_repository, 
    feedback_optimizer
)

# 注册API蓝图
app.register_blueprint(dialogue_api.get_blueprint(), url_prefix='/api')

# 主页路由
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# 静态文件路由
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# 健康检查
@app.route('/health')
def health_check():
    return {'status': 'ok', 'version': '1.0.0'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
