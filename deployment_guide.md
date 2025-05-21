# 医学AI助手部署指南

## 系统概述

医学AI助手是一个基于专利技术的智能医疗咨询系统，采用三层架构设计：

1. **智能调度层**：解析用户医疗咨询意图并路由至合适的专业模型
2. **知识生产层**：生成专业医疗回答并进行知识清洗
3. **智能知识库**：采用三级存储结构管理医疗知识

系统特别关注中医领域，同时覆盖西医各专科，能够提供专家级别的医学咨询服务。

## 部署要求

### 系统要求

- Python 3.8+
- Flask 框架
- SQLite 数据库（可选升级为MySQL）
- 现代浏览器（Chrome、Firefox、Safari、Edge等）

### 硬件推荐配置

- CPU: 4核心以上
- 内存: 8GB以上
- 存储: 10GB可用空间
- 网络: 稳定的互联网连接

## 部署步骤

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置系统

系统配置主要在`src/config.py`文件中，可根据需要修改以下参数：

- 数据库连接信息
- 模型配置参数
- 知识库存储路径
- 日志级别和路径

### 3. 初始化数据库

```bash
# 初始化数据库
python init_db.py
```

### 4. 启动服务

```bash
# 开发环境启动
python -m src.main

# 生产环境启动（使用gunicorn）
gunicorn -w 4 -b 0.0.0.0:5000 src.main:app
```

启动后，系统将在`http://localhost:5000`提供服务。

### 5. 配置反向代理（生产环境）

在生产环境中，建议使用Nginx等Web服务器作为反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 系统使用

### 用户注册与登录

系统支持用户注册和登录功能，登录后可以：
- 保存历史对话记录
- 提供个性化的医疗咨询体验
- 参与系统反馈优化

### AI对话功能

在主界面可以直接与AI进行医疗咨询对话，系统会：
- 智能识别医学领域和意图
- 路由至最合适的专业模型
- 生成专业、规范的医疗回答
- 根据用户反馈持续优化

### 系统管理

管理员可以通过管理界面：
- 查看系统运行状态
- 监控知识库统计信息
- 分析用户反馈数据
- 优化模型配置参数

## 常见问题

1. **Q: 系统启动失败怎么办？**  
   A: 检查依赖是否完整安装，数据库是否正确初始化，端口是否被占用。

2. **Q: 如何升级到MySQL数据库？**  
   A: 修改`src/config.py`中的数据库连接信息，并安装`pymysql`依赖。

3. **Q: 如何备份知识库数据？**  
   A: 定期备份`knowledge.db`文件或配置的MySQL数据库。

4. **Q: 系统支持哪些医学领域？**  
   A: 系统默认支持中医和西医各主要专科，可通过配置文件扩展。

## 技术支持

如有任何问题或需要技术支持，请联系：

- 邮箱：support@medical-ai-assistant.com
- 技术文档：https://docs.medical-ai-assistant.com

---

© 2025 医学AI助手团队，保留所有权利
