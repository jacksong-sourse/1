# 医学AI助手项目说明文档

## 项目概述

医学AI助手是一个基于专利技术的智能医疗咨询系统，采用创新的三层架构设计，特别关注中医领域，同时覆盖西医各专科，能够提供专家级别的医学咨询服务。

系统核心创新点包括：
- 三层架构设计（智能调度层、知识生产层、智能知识库）
- 三维匹配矩阵（领域-模型-可信度）
- 知识清洗流水线
- 三级知识库存储结构
- 动态权重算法

## 目录结构

```
advanced_medical_ai/
├── src/                           # 源代码目录
│   ├── api/                       # API接口
│   │   └── dialogue_api.py        # 统一对话API
│   ├── intelligent_dispatch/      # 智能调度层
│   │   ├── intent_parser.py       # 领域意图解析
│   │   ├── matching_matrix.py     # 三维匹配矩阵
│   │   └── model_router.py        # 模型动态路由
│   ├── knowledge_production/      # 知识生产层
│   │   ├── knowledge_cleaner.py   # 知识清洗流水线
│   │   └── knowledge_evaluator.py # 知识质量评估
│   ├── knowledge_store/           # 智能知识库
│   │   ├── knowledge_repository.py # 三级知识库存储
│   │   └── feedback_optimizer.py  # 反馈优化器
│   ├── static/                    # 静态资源
│   │   ├── css/                   # 样式文件
│   │   ├── js/                    # 脚本文件
│   │   ├── images/                # 图片资源
│   │   └── index.html             # 主页面
│   └── main.py                    # 应用入口
├── deployment_guide.md            # 部署指南
├── test_report.md                 # 测试报告
├── system_design_document.md      # 系统设计文档
├── model_evaluation_report.md     # 模型评估报告
└── requirements.txt               # 依赖列表
```

## 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 启动应用：
```bash
python -m src.main
```

3. 访问应用：
在浏览器中打开 http://localhost:5000

## 核心功能

- **智能医疗咨询**：用户可以提问各类医疗健康问题，系统会智能识别领域和意图，提供专业回答
- **中医专长**：特别关注中医领域，支持中医诊断、辨证论治、方药推荐等专业功能
- **用户注册登录**：支持用户账户管理，保存历史记录
- **反馈优化**：用户可以对AI回答进行评价，系统会根据反馈持续优化

## 技术栈

- **后端**：Python + Flask
- **前端**：HTML5 + CSS3 + JavaScript
- **数据库**：SQLite（可升级为MySQL）
- **AI模型**：集成多种医学专业模型

## 部署说明

详细部署步骤请参考 [deployment_guide.md](deployment_guide.md)

## 测试报告

系统测试结果请参考 [test_report.md](test_report.md)

## 系统设计

详细设计文档请参考 [system_design_document.md](system_design_document.md)

## 许可证

本项目基于专利技术开发，版权所有，未经授权不得使用。

## 联系方式

如有任何问题或需要技术支持，请联系：support@medical-ai-assistant.com
"# 1" 
