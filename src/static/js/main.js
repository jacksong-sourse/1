// 全局变量
let currentUser = null;
let currentSession = null;
let currentKnowledgeId = null;
let currentRating = 0;

// DOM元素
const elements = {
    // 侧边栏
    sidebar: document.getElementById('sidebar'),
    sidebarToggle: document.getElementById('sidebarToggle'),
    
    // 用户相关
    userSection: document.getElementById('userSection'),
    userActions: document.getElementById('userActions'),
    userProfile: document.getElementById('userProfile'),
    userName: document.getElementById('userName'),
    userEmail: document.getElementById('userEmail'),
    userAvatar: document.getElementById('userAvatar'),
    loginBtn: document.getElementById('loginBtn'),
    registerBtn: document.getElementById('registerBtn'),
    logoutBtn: document.getElementById('logoutBtn'),
    
    // 导航
    navLinks: document.querySelectorAll('.sidebar-nav a'),
    
    // 页面
    pages: document.querySelectorAll('.page'),
    chatPage: document.getElementById('chatPage'),
    historyPage: document.getElementById('historyPage'),
    aboutPage: document.getElementById('aboutPage'),
    
    // 聊天
    chatMessages: document.getElementById('chatMessages'),
    userInput: document.getElementById('userInput'),
    sendBtn: document.getElementById('sendBtn'),
    currentDomain: document.getElementById('currentDomain'),
    
    // 历史记录
    historyContainer: document.getElementById('historyContainer'),
    clearHistoryBtn: document.getElementById('clearHistoryBtn'),
    
    // 模态框
    loginModal: document.getElementById('loginModal'),
    registerModal: document.getElementById('registerModal'),
    feedbackModal: document.getElementById('feedbackModal'),
    closeLoginModal: document.getElementById('closeLoginModal'),
    closeRegisterModal: document.getElementById('closeRegisterModal'),
    closeFeedbackModal: document.getElementById('closeFeedbackModal'),
    
    // 表单
    loginForm: document.getElementById('loginForm'),
    registerForm: document.getElementById('registerForm'),
    feedbackForm: document.getElementById('feedbackForm'),
    
    // 切换表单
    switchToRegister: document.getElementById('switchToRegister'),
    switchToLogin: document.getElementById('switchToLogin'),
    
    // 评分
    ratingStars: document.querySelectorAll('.rating-stars i'),
    feedbackComment: document.getElementById('feedbackComment')
};

// API端点
const API = {
    BASE_URL: '/api',
    CHAT: '/api/chat',
    FEEDBACK: '/api/feedback',
    HISTORY: '/api/history',
    STATUS: '/api/status',
    LOGIN: '/api/auth/login',
    REGISTER: '/api/auth/register',
    LOGOUT: '/api/auth/logout'
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 生成会话ID
    currentSession = generateSessionId();
    
    // 检查登录状态
    checkLoginStatus();
    
    // 绑定事件
    bindEvents();
    
    // 绑定建议按钮
    bindSuggestionButtons();
    
    // 自动调整输入框高度
    autoResizeTextarea(elements.userInput);
});

// 生成会话ID
function generateSessionId() {
    return 'session_' + Math.random().toString(36).substring(2, 15);
}

// 检查登录状态
function checkLoginStatus() {
    // 从本地存储获取用户信息
    const storedUser = localStorage.getItem('user');
    
    if (storedUser) {
        try {
            currentUser = JSON.parse(storedUser);
            updateUIForLoggedInUser();
        } catch (e) {
            console.error('解析用户信息失败', e);
            logout();
        }
    } else {
        updateUIForLoggedOutUser();
    }
}

// 更新已登录用户的UI
function updateUIForLoggedInUser() {
    if (!currentUser) return;
    
    elements.userActions.classList.add('hidden');
    elements.userProfile.classList.remove('hidden');
    
    elements.userName.textContent = currentUser.name;
    elements.userEmail.textContent = currentUser.email;
    
    // 加载历史记录
    loadHistory();
}

// 更新未登录用户的UI
function updateUIForLoggedOutUser() {
    elements.userProfile.classList.add('hidden');
    elements.userActions.classList.remove('hidden');
    
    // 清空历史记录
    clearHistory();
}

// 绑定事件
function bindEvents() {
    // 侧边栏切换
    elements.sidebarToggle.addEventListener('click', toggleSidebar);
    
    // 导航链接
    elements.navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = e.currentTarget.getAttribute('href').substring(1);
            navigateTo(target);
        });
    });
    
    // 发送消息
    elements.sendBtn.addEventListener('click', sendMessage);
    elements.userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 清空历史
    elements.clearHistoryBtn.addEventListener('click', confirmClearHistory);
    
    // 登录/注册按钮
    elements.loginBtn.addEventListener('click', () => showModal(elements.loginModal));
    elements.registerBtn.addEventListener('click', () => showModal(elements.registerModal));
    elements.logoutBtn.addEventListener('click', logout);
    
    // 关闭模态框
    elements.closeLoginModal.addEventListener('click', () => hideModal(elements.loginModal));
    elements.closeRegisterModal.addEventListener('click', () => hideModal(elements.registerModal));
    elements.closeFeedbackModal.addEventListener('click', () => hideModal(elements.feedbackModal));
    
    // 切换表单
    elements.switchToRegister.addEventListener('click', () => {
        hideModal(elements.loginModal);
        showModal(elements.registerModal);
    });
    
    elements.switchToLogin.addEventListener('click', () => {
        hideModal(elements.registerModal);
        showModal(elements.loginModal);
    });
    
    // 表单提交
    elements.loginForm.addEventListener('submit', handleLogin);
    elements.registerForm.addEventListener('submit', handleRegister);
    elements.feedbackForm.addEventListener('submit', handleFeedback);
    
    // 评分星星
    elements.ratingStars.forEach(star => {
        star.addEventListener('click', handleRatingClick);
    });
}

// 绑定建议按钮
function bindSuggestionButtons() {
    document.querySelectorAll('.suggestion-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            elements.userInput.value = btn.textContent;
            sendMessage();
        });
    });
}

// 切换侧边栏
function toggleSidebar() {
    elements.sidebar.classList.toggle('expanded');
}

// 导航到指定页面
function navigateTo(target) {
    // 更新导航链接状态
    elements.navLinks.forEach(link => {
        const linkTarget = link.getAttribute('href').substring(1);
        link.parentElement.classList.toggle('active', linkTarget === target);
    });
    
    // 更新页面显示
    elements.pages.forEach(page => {
        page.classList.toggle('active', page.id === target + 'Page');
    });
    
    // 如果是移动设备，切换后关闭侧边栏
    if (window.innerWidth <= 768) {
        elements.sidebar.classList.remove('expanded');
    }
}

// 发送消息
function sendMessage() {
    const message = elements.userInput.value.trim();
    
    if (!message) return;
    
    // 添加用户消息到聊天区域
    addMessage('user', message);
    
    // 清空输入框
    elements.userInput.value = '';
    
    // 显示加载状态
    const loadingId = addLoadingMessage();
    
    // 发送请求到API
    fetch(API.CHAT, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: message,
            user_id: currentUser ? currentUser.id : 'guest',
            session_id: currentSession
        })
    })
    .then(response => response.json())
    .then(data => {
        // 移除加载消息
        removeLoadingMessage(loadingId);
        
        if (data.status === 'success') {
            // 添加AI回复
            addMessage('ai', data.response, data);
            
            // 更新领域标签
            if (data.metadata && data.metadata.domain) {
                elements.currentDomain.textContent = data.metadata.domain;
            }
            
            // 保存当前知识项ID
            currentKnowledgeId = data.knowledge_id;
            
            // 如果用户已登录，添加到历史记录
            if (currentUser) {
                addToHistory(message, data.response, data.metadata);
            }
        } else {
            // 显示错误消息
            addErrorMessage(data.message || '处理请求时发生错误');
        }
    })
    .catch(error => {
        console.error('发送消息失败', error);
        removeLoadingMessage(loadingId);
        addErrorMessage('网络错误，请稍后重试');
    });
}

// 添加消息到聊天区域
function addMessage(type, content, data = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    let html = '';
    
    if (type !== 'system') {
        html += `
            <div class="avatar">
                <img src="/static/images/${type === 'user' ? 'user' : 'ai'}-avatar.svg" alt="${type === 'user' ? '用户' : 'AI'}">
            </div>
        `;
    }
    
    html += `<div class="message-content">`;
    
    // 处理内容中的换行
    const formattedContent = content.replace(/\n/g, '<br>');
    html += `<p>${formattedContent}</p>`;
    
    // 如果是AI回复，添加操作按钮
    if (type === 'ai' && data) {
        html += `
            <div class="message-actions">
                <button class="feedback-btn" data-knowledge-id="${data.knowledge_id}">
                    <i class="ri-star-line"></i> 评价
                </button>
                <button class="copy-btn" data-content="${encodeURIComponent(content)}">
                    <i class="ri-file-copy-line"></i> 复制
                </button>
            </div>
        `;
    }
    
    html += `</div>`;
    
    messageDiv.innerHTML = html;
    elements.chatMessages.appendChild(messageDiv);
    
    // 滚动到底部
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    
    // 绑定操作按钮事件
    if (type === 'ai') {
        const feedbackBtn = messageDiv.querySelector('.feedback-btn');
        if (feedbackBtn) {
            feedbackBtn.addEventListener('click', () => {
                showFeedbackModal(data.knowledge_id);
            });
        }
        
        const copyBtn = messageDiv.querySelector('.copy-btn');
        if (copyBtn) {
            copyBtn.addEventListener('click', (e) => {
                const content = decodeURIComponent(e.currentTarget.getAttribute('data-content'));
                copyToClipboard(content);
                showToast('已复制到剪贴板');
                
                // 记录隐性反馈
                if (data.knowledge_id) {
                    sendImplicitFeedback(data.knowledge_id, 'copy');
                }
            });
        }
    }
    
    return messageDiv;
}

// 添加加载消息
function addLoadingMessage() {
    const id = 'loading_' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai';
    messageDiv.id = id;
    
    messageDiv.innerHTML = `
        <div class="avatar">
            <img src="/static/images/ai-avatar.svg" alt="AI">
        </div>
        <div class="message-content">
            <p class="loading-dots">AI正在思考中<span>.</span><span>.</span><span>.</span></p>
        </div>
    `;
    
    elements.chatMessages.appendChild(messageDiv);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    
    return id;
}

// 移除加载消息
function removeLoadingMessage(id) {
    const loadingMessage = document.getElementById(id);
    if (loadingMessage) {
        loadingMessage.remove();
    }
}

// 添加错误消息
function addErrorMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <p class="error-message"><i class="ri-error-warning-line"></i> ${message}</p>
        </div>
    `;
    
    elements.chatMessages.appendChild(messageDiv);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

// 显示反馈模态框
function showFeedbackModal(knowledgeId) {
    currentKnowledgeId = knowledgeId;
    currentRating = 0;
    
    // 重置星星
    elements.ratingStars.forEach(star => {
        star.classList.remove('active');
        star.classList.remove('ri-star-fill');
        star.classList.add('ri-star-line');
    });
    
    // 清空评论
    elements.feedbackComment.value = '';
    
    // 显示模态框
    showModal(elements.feedbackModal);
}

// 处理评分点击
function handleRatingClick(e) {
    const rating = parseInt(e.currentTarget.getAttribute('data-rating'));
    currentRating = rating;
    
    // 更新星星显示
    elements.ratingStars.forEach(star => {
        const starRating = parseInt(star.getAttribute('data-rating'));
        
        if (starRating <= rating) {
            star.classList.add('active');
            star.classList.remove('ri-star-line');
            star.classList.add('ri-star-fill');
        } else {
            star.classList.remove('active');
            star.classList.remove('ri-star-fill');
            star.classList.add('ri-star-line');
        }
    });
}

// 处理反馈提交
function handleFeedback(e) {
    e.preventDefault();
    
    if (!currentKnowledgeId || currentRating === 0) {
        showToast('请先选择评分');
        return;
    }
    
    const comment = elements.feedbackComment.value.trim();
    const normalizedRating = currentRating / 5; // 转换为0-1范围
    
    // 发送反馈
    fetch(API.FEEDBACK, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            knowledge_id: currentKnowledgeId,
            user_id: currentUser ? currentUser.id : 'guest',
            score: normalizedRating,
            comment: comment || undefined
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('感谢您的反馈！');
            hideModal(elements.feedbackModal);
        } else {
            showToast(data.message || '提交反馈失败');
        }
    })
    .catch(error => {
        console.error('提交反馈失败', error);
        showToast('网络错误，请稍后重试');
    });
}

// 发送隐性反馈
function sendImplicitFeedback(knowledgeId, behavior) {
    fetch(API.FEEDBACK, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            knowledge_id: knowledgeId,
            user_id: currentUser ? currentUser.id : 'guest',
            behavior: behavior
        })
    })
    .then(response => response.json())
    .catch(error => {
        console.error('发送隐性反馈失败', error);
    });
}

// 加载历史记录
function loadHistory() {
    if (!currentUser) return;
    
    fetch(`${API.HISTORY}?user_id=${currentUser.id}`)
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && data.history && data.history.length > 0) {
            renderHistory(data.history);
        } else {
            showEmptyHistory();
        }
    })
    .catch(error => {
        console.error('加载历史记录失败', error);
        showEmptyHistory();
    });
}

// 渲染历史记录
function renderHistory(history) {
    elements.historyContainer.innerHTML = '';
    
    history.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.setAttribute('data-query', item.query);
        historyItem.setAttribute('data-response', item.response);
        
        const date = new Date(item.timestamp);
        const formattedDate = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
        
        historyItem.innerHTML = `
            <div class="query">${item.query}</div>
            <div class="response">${item.response}</div>
            <div class="meta">
                <span class="domain">${item.metadata.domain || '通用医学'}</span>
                <span class="time">${formattedDate}</span>
            </div>
        `;
        
        historyItem.addEventListener('click', () => {
            navigateTo('chat');
            setTimeout(() => {
                addMessage('user', item.query);
                addMessage('ai', item.response, {
                    knowledge_id: item.knowledge_id,
                    metadata: item.metadata
                });
            }, 100);
        });
        
        elements.historyContainer.appendChild(historyItem);
    });
}

// 显示空历史记录
function showEmptyHistory() {
    elements.historyContainer.innerHTML = `
        <div class="empty-state">
            <img src="/static/images/empty-history.svg" alt="暂无历史记录">
            <p>暂无历史记录</p>
        </div>
    `;
}

// 添加到历史记录
function addToHistory(query, response, metadata) {
    // 这里只是前端模拟，实际应该由后端处理
    const historyItem = {
        query: query,
        response: response,
        knowledge_id: currentKnowledgeId,
        metadata: metadata,
        timestamp: new Date().toISOString()
    };
    
    // 重新加载历史记录
    loadHistory();
}

// 确认清空历史
function confirmClearHistory() {
    if (confirm('确定要清空所有历史记录吗？此操作不可撤销。')) {
        clearHistory();
    }
}

// 清空历史记录
function clearHistory() {
    showEmptyHistory();
}

// 处理登录
function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!email || !password) {
        showToast('请填写所有字段');
        return;
    }
    
    // 模拟登录成功
    simulateLogin(email);
}

// 处理注册
function handleRegister(e) {
    e.preventDefault();
    
    const name = document.getElementById('registerName').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value;
    const passwordConfirm = document.getElementById('registerPasswordConfirm').value;
    
    if (!name || !email || !password || !passwordConfirm) {
        showToast('请填写所有字段');
        return;
    }
    
    if (password !== passwordConfirm) {
        showToast('两次输入的密码不一致');
        return;
    }
    
    // 模拟注册成功
    simulateRegister(name, email);
}

// 模拟登录
function simulateLogin(email) {
    // 模拟用户数据
    const user = {
        id: 'user_' + Math.random().toString(36).substring(2, 9),
        name: email.split('@')[0],
        email: email
    };
    
    // 保存用户信息
    localStorage.setItem('user', JSON.stringify(user));
    currentUser = user;
    
    // 更新UI
    updateUIForLoggedInUser();
    
    // 关闭模态框
    hideModal(elements.loginModal);
    
    // 显示提示
    showToast('登录成功');
}

// 模拟注册
function simulateRegister(name, email) {
    // 模拟用户数据
    const user = {
        id: 'user_' + Math.random().toString(36).substring(2, 9),
        name: name,
        email: email
    };
    
    // 保存用户信息
    localStorage.setItem('user', JSON.stringify(user));
    currentUser = user;
    
    // 更新UI
    updateUIForLoggedInUser();
    
    // 关闭模态框
    hideModal(elements.registerModal);
    
    // 显示提示
    showToast('注册成功');
}

// 退出登录
function logout() {
    // 清除用户信息
    localStorage.removeItem('user');
    currentUser = null;
    
    // 更新UI
    updateUIForLoggedOutUser();
    
    // 显示提示
    showToast('已退出登录');
}

// 显示模态框
function showModal(modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// 隐藏模态框
function hideModal(modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

// 复制到剪贴板
function copyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = 0;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
}

// 显示提示
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// 自动调整文本框高度
function autoResizeTextarea(textarea) {
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
}
