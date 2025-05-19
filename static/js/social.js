// 全局变量
const apiBaseUrl = '/api/social';
let currentPage = 1;
let currentFilter = 'all';
let totalPages = 1;
let sharesLoaded = false;

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 检查用户是否已登录
    if (!isLoggedIn()) {
        window.location.href = '/login';
        return;
    }

    // 初始化加载分享内容
    loadShares(1);

    // 监听筛选按钮点击
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // 移除其他按钮的active状态
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            // 添加当前按钮的active状态
            this.classList.add('active');
            
            // 重置页码并加载新的筛选结果
            currentFilter = this.dataset.type;
            currentPage = 1;
            loadShares(1, currentFilter);
        });
    });

    // 监听加载更多按钮点击
    document.getElementById('load-more-btn').addEventListener('click', function() {
        loadShares(currentPage + 1, currentFilter);
    });

    // 监听创建分享表单提交
    document.getElementById('submitShare').addEventListener('click', createShare);

    // 监听分享类型选择变化
    document.getElementById('contentType').addEventListener('change', function() {
        loadContentOptions(this.value);
    });
    
    // 从本地存储初始化点赞状态（作为后备方案）
    initLikedStatesFromLocalStorage();
});

// 加载分享内容
function loadShares(page, contentType = 'all') {
    // 显示加载指示器
    document.getElementById('loading-indicator').classList.remove('d-none');
    document.getElementById('no-shares').classList.add('d-none');
    
    // 构建API URL
    let url = `${apiBaseUrl}/shares?page=${page}&per_page=10`;
    if (contentType && contentType !== 'all') {
        url += `&content_type=${contentType}`;
    }
    
    console.log('正在加载分享数据，请求URL:', url);
    console.log('当前认证Token:', getToken());
    
    // 发送API请求
    fetch(url, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        console.log('API响应状态:', response.status);
        
        if (!response.ok) {
            if (response.status === 401) {
                // 未授权，可能是token过期
                console.log('认证已过期，请重新登录');
                localStorage.removeItem('jwt_token');
                window.location.href = '/login';
                throw new Error('认证已过期，请重新登录');
            }
            throw new Error(`获取分享失败，状态码: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('成功获取数据:', data);
        
        // 隐藏加载指示器
        document.getElementById('loading-indicator').classList.add('d-none');
        
        // 保存当前页码和总页数
        currentPage = page;
        totalPages = data.pages || 1;
        
        // 处理空结果
        if ((!data.shares || data.shares.length === 0) && page === 1) {
            document.getElementById('no-shares').classList.remove('d-none');
            document.getElementById('load-more-btn').classList.add('d-none');
            sharesLoaded = true;
            return;
        }
        
        // 渲染分享内容
        renderShares(data.shares || [], page === 1);
        
        // 显示/隐藏加载更多按钮
        if (currentPage < totalPages) {
            document.getElementById('load-more-btn').classList.remove('d-none');
        } else {
            document.getElementById('load-more-btn').classList.add('d-none');
        }
        
        sharesLoaded = true;
        
        // 同步服务器返回的点赞状态到本地存储
        if (data.shares && data.shares.length > 0) {
            syncLikedStates(data.shares);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('loading-indicator').classList.add('d-none');
        
        // 添加调试信息以查看是什么导致了问题
        console.log('API错误信息:', error.message);
        console.log('尝试使用模拟数据进行测试');
        
        // 使用模拟数据以允许页面继续加载（仅用于调试/开发）
        const mockData = {
            shares: [
                {
                    id: 1,
                    username: '测试用户',
                    user_id: 1,
                    content_type: 'health_record',
                    content_id: 1,
                    description: '这是一条测试分享，API暂时不可用',
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                    likes_count: 5,
                    comments_count: 2,
                    is_valid: true
                }
            ],
            total: 1,
            pages: 1,
            current_page: 1
        };
        
        // 显示错误信息
        const sharesContainer = document.getElementById('shares-container');
        sharesContainer.innerHTML = `
            <div class="col-12">
                <div class="alert alert-warning" role="alert">
                    <strong>连接服务器时出现问题</strong><br>
                    ${error.message}<br>
                    显示模拟数据用于测试，请联系管理员解决API问题。
                </div>
            </div>
        `;
        
        // 渲染模拟数据
        renderShares(mockData.shares, true);
        
        sharesLoaded = true;
    });
}

// 渲染分享内容
function renderShares(shares, clearExisting = false) {
    const sharesContainer = document.getElementById('shares-container');
    
    // 如果是第一页，清空容器
    if (clearExisting) {
        sharesContainer.innerHTML = '';
    }
    
    // 添加分享卡片
    shares.forEach(share => {
        // 检查用户是否已点赞
        const isLiked = share.is_liked === true; // 使用严格判断，避免undefined
        
        const shareCard = document.createElement('div');
        shareCard.className = 'col-lg-6 mb-4';
        shareCard.innerHTML = `
            <div class="share-card">
                <div class="share-header">
                    <img src="https://ui-avatars.com/api/?name=${share.username.charAt(0)}&background=0D8ABC&color=fff" alt="${share.username}的头像">
                    <div class="user-info">
                        <span class="username">${share.username}</span>
                        <span class="share-time">${formatDate(share.created_at)}</span>
                    </div>
                </div>
                <div class="share-content">
                    <div class="share-description">${share.description || '分享了健康数据'}</div>
                    <div class="share-data">
                        ${renderShareContent(share)}
                    </div>
                </div>
                <div class="share-actions">
                    <a href="javascript:void(0)" class="share-action-btn ${isLiked ? 'liked' : ''}" data-share-id="${share.id}" onclick="toggleLike(${share.id}, this)">
                        <i class="bi ${isLiked ? 'bi-heart-fill' : 'bi-heart'}"></i> <span>${share.likes_count}</span> 赞
                    </a>
                    <a href="javascript:void(0)" class="share-action-btn" data-share-id="${share.id}" onclick="openComments(${share.id})">
                        <i class="bi bi-chat-left-text"></i> <span>${share.comments_count}</span> 评论
                    </a>
                    <a href="/social/share/${share.id}" class="share-action-btn">
                        <i class="bi bi-arrow-right-circle"></i> 查看详情
                    </a>
                </div>
            </div>
        `;
        sharesContainer.appendChild(shareCard);
    });
}

// 根据分享类型渲染不同的内容
function renderShareContent(share) {
    if (!share.is_valid) {
        return `<div class="text-muted text-center">
            <i class="bi bi-exclamation-circle"></i> 该内容已不可用
        </div>`;
    }
    
    // 这里根据不同的content_type渲染不同的内容预览
    // 实际项目中需要根据具体数据结构来实现
    let contentPreview = '';
    
    switch(share.content_type) {
        case 'health_record':
            contentPreview = `<div><i class="bi bi-clipboard-pulse"></i> 健康记录</div>`;
            break;
        case 'diet_record':
            contentPreview = `<div><i class="bi bi-cup-hot"></i> 饮食记录</div>`;
            break;
        case 'exercise_record':
            contentPreview = `<div><i class="bi bi-activity"></i> 运动记录</div>`;
            break;
        case 'health_goal':
            contentPreview = `<div><i class="bi bi-bullseye"></i> 健康目标</div>`;
            break;
        case 'water_intake':
            contentPreview = `<div><i class="bi bi-droplet"></i> 饮水记录</div>`;
            break;
        case 'medication_record':
            contentPreview = `<div><i class="bi bi-capsule"></i> 用药记录</div>`;
            break;
        case 'health_report':
            contentPreview = `<div><i class="bi bi-file-medical"></i> 健康报告</div>`;
            break;
        default:
            contentPreview = `<div>健康数据分享</div>`;
    }
    
    return contentPreview;
}

// 点赞/取消点赞
function toggleLike(shareId, element) {
    const isLiked = element.classList.contains('liked');
    const method = isLiked ? 'DELETE' : 'POST';
    
    fetch(`${apiBaseUrl}/share/${shareId}/like`, {
        method: method,
        headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('操作失败');
        }
        return response.json();
    })
    .then(data => {
        // 打印调试信息
        console.log('点赞/取消点赞响应:', data);
        
        // 更新UI状态
        if (isLiked) {
            element.classList.remove('liked');
            element.querySelector('i').className = 'bi bi-heart';
            element.querySelector('span').textContent = parseInt(element.querySelector('span').textContent) - 1;
        } else {
            element.classList.add('liked');
            element.querySelector('i').className = 'bi bi-heart-fill';
            element.querySelector('span').textContent = parseInt(element.querySelector('span').textContent) + 1;
        }
        
        // 保存点赞状态到本地存储，避免刷新页面后丢失
        try {
            // 获取当前存储的点赞状态
            let likedShares = JSON.parse(localStorage.getItem('liked_shares') || '[]');
            
            if (isLiked) {
                // 取消点赞，从列表中移除
                likedShares = likedShares.filter(id => id !== shareId);
            } else {
                // 点赞，添加到列表中
                if (!likedShares.includes(shareId)) {
                    likedShares.push(shareId);
                }
            }
            
            // 保存到本地存储
            localStorage.setItem('liked_shares', JSON.stringify(likedShares));
            console.log('已保存点赞状态到本地存储:', likedShares);
        } catch (storageError) {
            console.warn('无法保存点赞状态到本地存储:', storageError);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('点赞操作失败，请稍后再试', 'danger');
    });
}

// 打开评论模态框
function openComments(shareId) {
    const commentsModal = new bootstrap.Modal(document.getElementById('commentsModal'));
    
    // 设置当前分享ID
    document.getElementById('comment-share-id').value = shareId;
    
    // 清空评论列表
    const commentsList = document.getElementById('comments-list');
    commentsList.innerHTML = `
        <div class="text-center py-3" id="comments-loading">
            <div class="spinner-border spinner-border-sm text-primary" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
            <span class="ms-2">加载评论中...</span>
        </div>
        <div class="text-center py-3 d-none" id="no-comments">
            <p class="text-muted">暂无评论，快来发表你的看法吧！</p>
        </div>
    `;
    
    // 加载评论
    loadComments(shareId);
    
    // 显示模态框
    commentsModal.show();
}

// 加载评论
function loadComments(shareId) {
    fetch(`${apiBaseUrl}/share/${shareId}/comments`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('获取评论失败');
        }
        return response.json();
    })
    .then(data => {
        // 隐藏加载指示器
        document.getElementById('comments-loading').classList.add('d-none');
        
        // 处理空结果
        if (data.comments.length === 0) {
            document.getElementById('no-comments').classList.remove('d-none');
            return;
        }
        
        // 渲染评论
        renderComments(data.comments);
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('comments-loading').classList.add('d-none');
        
        // 显示错误信息
        const commentsList = document.getElementById('comments-list');
        commentsList.innerHTML += `
            <div class="alert alert-danger" role="alert">
                加载评论失败，请稍后再试。
            </div>
        `;
    });
}

// 渲染评论
function renderComments(comments) {
    const commentsList = document.getElementById('comments-list');
    commentsList.innerHTML = '';
    
    comments.forEach(comment => {
        const commentElement = document.createElement('div');
        commentElement.className = 'comment-item';
        commentElement.innerHTML = `
            <div class="comment-header">
                <span class="comment-user">${comment.username}</span>
                <span class="comment-time">${formatDate(comment.created_at)}</span>
            </div>
            <div class="comment-content">${comment.content}</div>
        `;
        
        // 添加回复
        if (comment.replies && comment.replies.length > 0) {
            const repliesContainer = document.createElement('div');
            repliesContainer.className = 'comment-replies';
            
            comment.replies.forEach(reply => {
                const replyElement = document.createElement('div');
                replyElement.className = 'comment-item';
                replyElement.innerHTML = `
                    <div class="comment-header">
                        <span class="comment-user">${reply.username}</span>
                        <span class="comment-time">${formatDate(reply.created_at)}</span>
                    </div>
                    <div class="comment-content">${reply.content}</div>
                `;
                repliesContainer.appendChild(replyElement);
            });
            
            commentElement.appendChild(repliesContainer);
        }
        
        commentsList.appendChild(commentElement);
    });
}

// 发表评论
document.getElementById('post-comment').addEventListener('click', function(e) {
    e.preventDefault();
    
    const shareId = document.getElementById('comment-share-id').value;
    const content = document.getElementById('comment-content').value.trim();
    const parentId = document.getElementById('comment-parent-id').value || null;
    
    if (!content) {
        showAlert('评论内容不能为空', 'warning');
        return;
    }
    
    fetch(`${apiBaseUrl}/share/${shareId}/comment`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            content: content,
            parent_id: parentId
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('发表评论失败');
        }
        return response.json();
    })
    .then(data => {
        // 清空输入框
        document.getElementById('comment-content').value = '';
        document.getElementById('comment-parent-id').value = '';
        
        // 重新加载评论
        loadComments(shareId);
        
        showAlert('评论发表成功', 'success');
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('发表评论失败，请稍后再试', 'danger');
    });
});

// 加载分享内容选项
function loadContentOptions(contentType) {
    if (!contentType) {
        document.getElementById('contentIdContainer').classList.add('d-none');
        return;
    }
    
    document.getElementById('contentIdContainer').classList.remove('d-none');
    const contentIdSelect = document.getElementById('contentId');
    contentIdSelect.innerHTML = '<option value="">-- 加载中... --</option>';
    
    // 根据不同的内容类型，从相应的API获取数据
    let apiUrl = '';
    
    switch(contentType) {
        case 'health_record':
            apiUrl = '/api/health/records';
            break;
        case 'diet_record':
            apiUrl = '/api/diet/records';
            break;
        case 'exercise_record':
            apiUrl = '/api/exercise/records';
            break;
        case 'health_goal':
            apiUrl = '/api/health/goals';
            break;
        case 'water_intake':
            apiUrl = '/api/water/records';
            break;
        case 'medication_record':
            apiUrl = '/api/medication/records';
            break;
        case 'health_report':
            apiUrl = '/api/health-report/reports';
            break;
        default:
            contentIdSelect.innerHTML = '<option value="">-- 无可用内容 --</option>';
            return;
    }
    
    fetch(apiUrl, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('获取内容失败');
        }
        return response.json();
    })
    .then(data => {
        const items = data.records || data.goals || data.reports || data.items || [];
        
        if (items.length === 0) {
            contentIdSelect.innerHTML = '<option value="">-- 无可用内容 --</option>';
            return;
        }
        
        contentIdSelect.innerHTML = '<option value="">-- 请选择 --</option>';
        
        items.forEach(item => {
            const option = document.createElement('option');
            option.value = item.id;
            
            // 根据不同内容类型，显示不同的选项文本
            switch(contentType) {
                case 'health_record':
                    option.textContent = `${formatDate(item.record_date)} - ${item.record_type}`;
                    break;
                case 'diet_record':
                    option.textContent = `${formatDate(item.record_date)} - ${item.meal_type}`;
                    break;
                case 'exercise_record':
                    option.textContent = `${formatDate(item.record_date)} - ${item.exercise_type}`;
                    break;
                case 'health_goal':
                    option.textContent = `${item.goal_type} - ${item.target_value}${item.unit}`;
                    break;
                case 'water_intake':
                    option.textContent = `${formatDate(item.record_date)} - ${item.amount}ml`;
                    break;
                case 'medication_record':
                    option.textContent = `${formatDate(item.record_date)} - ${item.medication_name}`;
                    break;
                case 'health_report':
                    option.textContent = `${formatDate(item.created_at)} - ${item.report_type}`;
                    break;
                default:
                    option.textContent = `ID: ${item.id}`;
            }
            
            contentIdSelect.appendChild(option);
        });
        
        // 监听内容ID选择变化，预览内容
        contentIdSelect.addEventListener('change', function() {
            const selectedId = this.value;
            if (!selectedId) {
                document.getElementById('contentPreview').innerHTML = `
                    <div class="text-center text-muted">
                        <i class="bi bi-eye"></i> 预览区域 - 选择内容后显示
                    </div>
                `;
                return;
            }
            
            const selectedItem = items.find(item => item.id == selectedId);
            if (selectedItem) {
                previewContent(contentType, selectedItem);
            }
        });
    })
    .catch(error => {
        console.error('Error:', error);
        contentIdSelect.innerHTML = '<option value="">-- 加载失败 --</option>';
    });
}

// 预览分享内容
function previewContent(contentType, item) {
    const previewContainer = document.getElementById('contentPreview');
    let previewHtml = '';
    
    switch(contentType) {
        case 'health_record':
            previewHtml = `
                <h5>健康记录</h5>
                <p>记录日期: ${formatDate(item.record_date)}</p>
                <p>记录类型: ${item.record_type}</p>
                <p>数值: ${item.value} ${item.unit}</p>
            `;
            break;
        case 'diet_record':
            previewHtml = `
                <h5>饮食记录</h5>
                <p>记录日期: ${formatDate(item.record_date)}</p>
                <p>餐食类型: ${item.meal_type}</p>
            `;
            break;
        case 'exercise_record':
            previewHtml = `
                <h5>运动记录</h5>
                <p>记录日期: ${formatDate(item.record_date)}</p>
                <p>运动类型: ${item.exercise_type}</p>
                <p>持续时间: ${item.duration}分钟</p>
                <p>消耗热量: ${item.calories_burned}卡路里</p>
            `;
            break;
        case 'health_goal':
            previewHtml = `
                <h5>健康目标</h5>
                <p>目标类型: ${item.goal_type}</p>
                <p>目标值: ${item.target_value} ${item.unit}</p>
                <p>开始日期: ${formatDate(item.start_date)}</p>
                <p>结束日期: ${formatDate(item.end_date)}</p>
            `;
            break;
        case 'water_intake':
            previewHtml = `
                <h5>饮水记录</h5>
                <p>记录日期: ${formatDate(item.record_date)}</p>
                <p>饮水量: ${item.amount}毫升</p>
            `;
            break;
        case 'medication_record':
            previewHtml = `
                <h5>用药记录</h5>
                <p>记录日期: ${formatDate(item.record_date)}</p>
                <p>药物名称: ${item.medication_name}</p>
                <p>剂量: ${item.dosage} ${item.dosage_unit}</p>
            `;
            break;
        case 'health_report':
            previewHtml = `
                <h5>健康报告</h5>
                <p>报告日期: ${formatDate(item.created_at)}</p>
                <p>报告类型: ${item.report_type}</p>
            `;
            break;
        default:
            previewHtml = `<div class="text-center text-muted">无法预览该类型内容</div>`;
    }
    
    previewContainer.innerHTML = previewHtml;
}

// 创建分享
function createShare() {
    const contentType = document.getElementById('contentType').value;
    const contentId = document.getElementById('contentId').value;
    const description = document.getElementById('description').value;
    const visibility = document.getElementById('visibility').value;
    
    // 验证输入
    if (!contentType || !contentId) {
        showAlert('请选择要分享的内容', 'warning');
        return;
    }

    console.log('创建分享，请求参数:', {
        content_type: contentType,
        content_id: contentId,
        description: description,
        visibility: visibility
    });
    
    // 发送API请求
    fetch(`${apiBaseUrl}/share`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            content_type: contentType,
            content_id: parseInt(contentId),
            description: description,
            visibility: visibility
        })
    })
    .then(response => {
        console.log('创建分享API响应状态:', response.status);
        
        // 如果响应状态不是成功，尝试获取错误信息
        if (!response.ok) {
            return response.json().then(errorData => {
                console.error('创建分享失败，错误信息:', errorData);
                throw new Error(errorData.error || '创建分享失败');
            }).catch(jsonError => {
                // 如果无法解析JSON，则使用状态文本
                console.error('无法解析错误响应:', jsonError);
                throw new Error(`创建分享失败，状态码: ${response.status} - ${response.statusText}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('创建分享成功:', data);
        
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('createShareModal'));
        modal.hide();
        
        // 重置表单
        document.getElementById('createShareForm').reset();
        document.getElementById('contentIdContainer').classList.add('d-none');
        document.getElementById('contentPreview').innerHTML = `
            <div class="text-center text-muted">
                <i class="bi bi-eye"></i> 预览区域 - 选择内容后显示
            </div>
        `;
        
        // 重新加载分享列表
        loadShares(1, currentFilter);
        
        showAlert('分享成功', 'success');
    })
    .catch(error => {
        console.error('创建分享错误详情:', error);
        showAlert(`创建分享失败: ${error.message}`, 'danger');
    });
}

// 格式化日期
function formatDate(dateString) {
    return moment(dateString).fromNow();
}

// 显示提醒消息
function showAlert(message, type = 'info') {
    const alertPlaceholder = document.createElement('div');
    alertPlaceholder.className = 'position-fixed bottom-0 end-0 p-3';
    alertPlaceholder.style.zIndex = '5000';
    document.body.appendChild(alertPlaceholder);
    
    const alertHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    alertPlaceholder.innerHTML = alertHtml;
    
    const toast = new bootstrap.Toast(alertPlaceholder.querySelector('.toast'));
    toast.show();
    
    // 自动移除
    setTimeout(() => {
        document.body.removeChild(alertPlaceholder);
    }, 5000);
}

// 从本地存储初始化点赞状态（作为后备方案）
function initLikedStatesFromLocalStorage() {
    const likedShares = JSON.parse(localStorage.getItem('liked_shares') || '[]');
    
    document.querySelectorAll('.share-action-btn').forEach(btn => {
        const shareId = btn.dataset.shareId;
        if (likedShares.includes(shareId)) {
            btn.classList.add('liked');
            btn.querySelector('i').className = 'bi bi-heart-fill';
            btn.querySelector('span').textContent = parseInt(btn.querySelector('span').textContent) + 1;
        }
    });
}

// 处理同步服务器返回的点赞状态和本地存储
function syncLikedStates(shares) {
    try {
        // 获取本地存储的点赞状态
        let likedShares = JSON.parse(localStorage.getItem('liked_shares') || '[]');
        let needsUpdate = false;
        
        // 用服务器返回的数据更新本地存储
        shares.forEach(share => {
            const shareId = share.id;
            const isLikedOnServer = share.is_liked === true;
            const isLikedInStorage = likedShares.includes(shareId);
            
            // 如果状态不一致，以服务器为准
            if (isLikedOnServer && !isLikedInStorage) {
                likedShares.push(shareId);
                needsUpdate = true;
            } else if (!isLikedOnServer && isLikedInStorage) {
                likedShares = likedShares.filter(id => id !== shareId);
                needsUpdate = true;
            }
        });
        
        // 如果需要更新，保存到本地存储
        if (needsUpdate) {
            localStorage.setItem('liked_shares', JSON.stringify(likedShares));
            console.log('已同步点赞状态到本地存储:', likedShares);
        }
    } catch (error) {
        console.warn('同步点赞状态出错:', error);
    }
} 