// 全局变量
const apiBaseUrl = '/api/social';
let currentShareId = null;
let isLiked = false;

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 检查用户是否已登录
    if (!isLoggedIn()) {
        window.location.href = '/login';
        return;
    }

    // 获取分享ID从URL
    const pathParts = window.location.pathname.split('/');
    currentShareId = pathParts[pathParts.length - 1];

    if (!currentShareId || isNaN(currentShareId)) {
        showError('无效的分享ID');
        return;
    }

    // 加载分享详情
    loadShareDetail(currentShareId);

    // 监听点赞按钮点击
    document.getElementById('like-btn').addEventListener('click', function() {
        toggleLike(currentShareId);
    });

    // 监听评论表单提交
    const commentForm = document.getElementById('comment-form');
    if (commentForm) {
        commentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitComment();
        });
    }

    // 监听回复提交
    const submitReplyBtn = document.getElementById('submit-reply');
    if (submitReplyBtn) {
        submitReplyBtn.addEventListener('click', submitReply);
    }

    // 创建提示容器
    if (!document.getElementById('toast-container')) {
        const toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    // 初始化点赞状态
    initLikedStatus();
});

// 加载分享详情
function loadShareDetail(shareId) {
    console.log('加载分享详情，ID:', shareId);
    console.log('当前认证Token:', getToken());

    fetch(`${apiBaseUrl}/share/${shareId}`, {
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
            } else if (response.status === 403) {
                throw new Error('无权查看此分享');
            } else if (response.status === 404) {
                throw new Error('分享不存在或已被删除');
            }
            throw new Error(`获取分享详情失败，状态码: ${response.status}`);
        }
        return response.json();
    })
    .then(share => {
        console.log('成功获取分享详情:', share);
        
        // 隐藏加载指示器
        document.getElementById('loading-indicator').classList.add('d-none');
        document.getElementById('content-not-available').classList.add('d-none');
        document.querySelector('.share-detail-container').classList.remove('d-none');

        // 更新分享详情
        updateShareDetail(share);

        // 加载评论
        loadComments(shareId);

        // 检查当前用户是否已点赞
        checkLikeStatus(shareId);

        // 保存点赞状态到本地存储
        updateLocalLikedStatus(shareId, share.is_liked === true);
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('loading-indicator').classList.add('d-none');
        
        // 添加调试信息，查看具体错误
        console.log('API错误信息:', error.message);
        console.log('尝试使用模拟数据进行测试');
        
        // 如果API不可用，使用模拟数据（仅用于测试/调试）
        if (error.message.includes('获取分享详情失败') || error.message.includes('认证已过期')) {
            const mockShare = {
                id: shareId,
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
            };
            
            // 显示模拟数据的错误提示
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-warning mb-4';
            errorDiv.innerHTML = `
                <strong>连接服务器时出现问题</strong><br>
                ${error.message}<br>
                显示模拟数据用于测试，请联系管理员解决API问题。
            `;
            document.querySelector('.share-detail-container').classList.remove('d-none');
            document.querySelector('.share-detail-container').prepend(errorDiv);
            
            // 更新分享详情
            updateShareDetail(mockShare);
            
            // 不进行后续API调用
            return;
        }
        
        // 显示常规错误信息
        document.getElementById('content-not-available').classList.remove('d-none');
        document.getElementById('content-not-available').querySelector('p').textContent = error.message;
    });
}

// 更新分享详情
function updateShareDetail(share) {
    // 更新用户信息
    document.getElementById('share-username').textContent = share.username;
    document.getElementById('share-time').textContent = formatDate(share.created_at);
    document.getElementById('share-user-avatar').src = `https://ui-avatars.com/api/?name=${share.username.charAt(0)}&background=0D8ABC&color=fff`;

    // 更新分享内容
    document.getElementById('share-description').textContent = share.description || '分享了健康数据';
    document.getElementById('share-data').innerHTML = renderShareContent(share);

    // 更新点赞和评论数
    document.getElementById('likes-count').textContent = share.likes_count;
    document.getElementById('comments-count').textContent = share.comments_count;
    document.getElementById('comments-count-heading').textContent = `(${share.comments_count})`;

    // 标题更新
    document.title = `${share.username}的分享 - 个人健康管理系统`;
}

// 根据分享类型渲染不同的内容
function renderShareContent(share) {
    if (!share.is_valid) {
        return `<div class="text-muted text-center">
            <i class="bi bi-exclamation-circle"></i> 该内容已不可用
        </div>`;
    }
    
    // 这里根据不同的content_type渲染不同的内容详情
    // 实际项目中需要根据具体数据结构来实现
    let contentDetail = '';
    
    switch(share.content_type) {
        case 'health_record':
            contentDetail = `
                <div class="mb-3">
                    <h5><i class="bi bi-clipboard-pulse"></i> 健康记录</h5>
                    <p>查看此健康记录的详细数据</p>
                </div>
                <a href="/health/records?id=${share.content_id}" class="btn btn-outline-primary">查看详情</a>
            `;
            break;
        case 'diet_record':
            contentDetail = `
                <div class="mb-3">
                    <h5><i class="bi bi-cup-hot"></i> 饮食记录</h5>
                    <p>查看此饮食记录的详细数据</p>
                </div>
                <a href="/records?type=diet&id=${share.content_id}" class="btn btn-outline-primary">查看详情</a>
            `;
            break;
        case 'exercise_record':
            contentDetail = `
                <div class="mb-3">
                    <h5><i class="bi bi-activity"></i> 运动记录</h5>
                    <p>查看此运动记录的详细数据</p>
                </div>
                <a href="/records?type=exercise&id=${share.content_id}" class="btn btn-outline-primary">查看详情</a>
            `;
            break;
        case 'health_goal':
            contentDetail = `
                <div class="mb-3">
                    <h5><i class="bi bi-bullseye"></i> 健康目标</h5>
                    <p>查看此健康目标的详细数据</p>
                </div>
                <a href="/records?type=goal&id=${share.content_id}" class="btn btn-outline-primary">查看详情</a>
            `;
            break;
        case 'water_intake':
            contentDetail = `
                <div class="mb-3">
                    <h5><i class="bi bi-droplet"></i> 饮水记录</h5>
                    <p>查看此饮水记录的详细数据</p>
                </div>
                <a href="/records?type=water&id=${share.content_id}" class="btn btn-outline-primary">查看详情</a>
            `;
            break;
        case 'medication_record':
            contentDetail = `
                <div class="mb-3">
                    <h5><i class="bi bi-capsule"></i> 用药记录</h5>
                    <p>查看此用药记录的详细数据</p>
                </div>
                <a href="/records?type=medication&id=${share.content_id}" class="btn btn-outline-primary">查看详情</a>
            `;
            break;
        case 'health_report':
            contentDetail = `
                <div class="mb-3">
                    <h5><i class="bi bi-file-medical"></i> 健康报告</h5>
                    <p>查看此健康报告的详细数据</p>
                </div>
                <a href="/health-report?id=${share.content_id}" class="btn btn-outline-primary">查看详情</a>
            `;
            break;
        default:
            contentDetail = `<div>健康数据分享</div>`;
    }
    
    return contentDetail;
}

// 检查当前用户是否已点赞
function checkLikeStatus(shareId) {
    fetch(`${apiBaseUrl}/share/${shareId}/likes`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('获取点赞状态失败');
        }
        return response.json();
    })
    .then(data => {
        // 获取当前用户ID
        const currentUserId = getUserInfo().id;
        
        // 检查当前用户是否在点赞列表中
        const hasLiked = data.likes.some(like => like.user_id === currentUserId);
        
        // 更新点赞按钮状态
        if (hasLiked) {
            document.getElementById('like-btn').classList.add('liked');
            document.getElementById('like-btn').querySelector('i').className = 'bi bi-heart-fill';
            isLiked = true;
        } else {
            document.getElementById('like-btn').classList.remove('liked');
            document.getElementById('like-btn').querySelector('i').className = 'bi bi-heart';
            isLiked = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// 点赞/取消点赞
function toggleLike(shareId) {
    const likeButton = document.getElementById('like-btn');
    isLiked = likeButton.classList.contains('liked');
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
        console.log('点赞/取消点赞响应:', data);
        
        // 更新UI状态
        if (isLiked) {
            likeButton.classList.remove('liked');
            likeButton.querySelector('i').className = 'bi bi-heart';
            document.getElementById('likes-count').textContent = parseInt(document.getElementById('likes-count').textContent) - 1;
            isLiked = false;
        } else {
            likeButton.classList.add('liked');
            likeButton.querySelector('i').className = 'bi bi-heart-fill';
            document.getElementById('likes-count').textContent = parseInt(document.getElementById('likes-count').textContent) + 1;
            isLiked = true;
        }
        
        // 更新本地存储的点赞状态
        updateLocalLikedStatus(shareId, !isLiked);
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('点赞操作失败，请稍后再试', 'danger');
    });
}

// 加载评论
function loadComments(shareId) {
    console.log('加载评论，分享ID:', shareId);
    
    // 获取评论容器元素
    const commentsContainer = document.getElementById('comments-container');
    // 如果找不到comments-container元素，尝试获取comment-list元素
    const commentsList = commentsContainer || document.getElementById('comment-list');
    
    // 确保找到了评论容器
    if (!commentsList) {
        console.error('找不到评论容器元素');
        return;
    }
    
    // 显示加载指示器
    const loadingIndicator = document.getElementById('comments-loading');
    if (loadingIndicator) {
        loadingIndicator.classList.remove('d-none');
    }
    
    // 隐藏无评论提示
    const noComments = document.getElementById('no-comments');
    if (noComments) {
        noComments.classList.add('d-none');
    }
    
    fetch(`${apiBaseUrl}/share/${shareId}/comments`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        console.log('评论API响应状态:', response.status);
        if (!response.ok) {
            if (response.status === 401) {
                console.log('认证已过期，请重新登录');
                throw new Error('认证已过期');
            }
            throw new Error(`加载评论失败，状态码: ${response.status}`);
        }
        return response.json();
    })
    .then(comments => {
        console.log('成功获取评论:', comments);
        
        // 隐藏加载指示器
        if (loadingIndicator) {
            loadingIndicator.classList.add('d-none');
        }
        
        // 清空评论容器的内容准备添加新评论
        commentsList.innerHTML = '';
        
        // 检查comments的数据格式，确保它是数组
        let commentsArray = [];
        
        // 如果是对象且包含comments属性，则使用comments属性
        if (comments && typeof comments === 'object') {
            if (Array.isArray(comments)) {
                commentsArray = comments;
            } else if (comments.comments && Array.isArray(comments.comments)) {
                commentsArray = comments.comments;
            } else {
                console.error('评论数据格式不正确:', comments);
                commentsList.innerHTML = '<div class="alert alert-danger">评论数据格式不正确</div>';
                return;
            }
        }
        
        // 处理空结果
        if (!commentsArray.length) {
            if (noComments) {
                noComments.classList.remove('d-none');
            } else {
                commentsList.innerHTML = '<div class="text-center text-muted my-4">暂无评论，来发表第一条评论吧</div>';
            }
            return;
        }
        
        // 渲染评论
        commentsArray.forEach(comment => {
            const commentEl = createCommentElement(comment);
            commentsList.appendChild(commentEl);
        });
    })
    .catch(error => {
        console.error('加载评论出错:', error);
        
        // 隐藏加载指示器
        if (loadingIndicator) {
            loadingIndicator.classList.add('d-none');
        }
        
        // 使用模拟数据（仅用于测试/调试）
        if (error.message.includes('加载评论失败') || error.message.includes('认证已过期')) {
            const mockComments = [
                {
                    id: 1,
                    user_id: 2,
                    username: '测试用户1',
                    content: '这是一条测试评论，API暂时不可用',
                    created_at: new Date().toISOString(),
                    is_author: true
                },
                {
                    id: 2,
                    user_id: 3,
                    username: '测试用户2',
                    content: '希望这个功能能够正常工作！',
                    created_at: new Date(Date.now() - 3600000).toISOString(),
                    is_author: false
                }
            ];
            
            commentsList.innerHTML = '<div class="alert alert-warning mb-3">加载评论失败，显示模拟数据</div>';
            
            // 使用模拟数据进行渲染
            mockComments.forEach(comment => {
                try {
                    const commentEl = createCommentElement(comment);
                    commentsList.appendChild(commentEl);
                } catch (e) {
                    console.error('渲染模拟评论失败:', e);
                    commentsList.innerHTML += `<div class="alert alert-danger">渲染评论失败: ${e.message}</div>`;
                }
            });
            return;
        }
        
        commentsList.innerHTML = `<div class="alert alert-danger">加载评论失败: ${error.message}</div>`;
    });
}

// 创建评论元素
function createCommentElement(comment) {
    try {
        if (!comment || typeof comment !== 'object') {
            throw new Error('评论数据无效');
        }
        
        // 确保必要的字段存在
        if (!comment.id) comment.id = 0;
        if (!comment.username) comment.username = '匿名用户';
        if (!comment.content) comment.content = '(无内容)';
        if (!comment.created_at) comment.created_at = new Date().toISOString();
        
        const commentDiv = document.createElement('div');
        commentDiv.className = 'comment-item';
        commentDiv.dataset.commentId = comment.id;
        
        let commentHtml = `
            <div class="comment-header">
                <span class="comment-user">${comment.username}</span>
                <span class="comment-time">${formatDate(comment.created_at)}</span>
            </div>
            <div class="comment-content">${comment.content}</div>
            <div class="comment-actions">
                <a href="javascript:void(0)" class="comment-action" onclick="showReplyForm(${comment.id}, '${comment.username}')">
                    <i class="bi bi-reply"></i> 回复
                </a>
        `;
        
        // 添加删除按钮 (如果评论是当前用户发布的)
        if (comment.is_author) {
            commentHtml += `
                <a href="javascript:void(0)" class="comment-action text-danger" onclick="deleteComment(${comment.id})">
                    <i class="bi bi-trash"></i> 删除
                </a>
            `;
        }
        
        commentHtml += `</div>`;
        
        // 添加回复区域
        if (comment.replies && Array.isArray(comment.replies) && comment.replies.length > 0) {
            commentHtml += `<div class="comment-replies">`;
            
            comment.replies.forEach(reply => {
                // 确保回复数据有效
                if (!reply.id) reply.id = 0;
                if (!reply.username) reply.username = '匿名用户';
                if (!reply.content) reply.content = '(无内容)';
                if (!reply.created_at) reply.created_at = new Date().toISOString();
                
                commentHtml += `
                    <div class="comment-item" data-comment-id="${reply.id}">
                        <div class="comment-header">
                            <span class="comment-user">${reply.username}</span>
                            <span class="comment-time">${formatDate(reply.created_at)}</span>
                        </div>
                        <div class="comment-content">${reply.content}</div>
                        <div class="comment-actions">
                `;
                
                // 添加删除按钮 (如果回复是当前用户发布的)
                if (reply.is_author) {
                    commentHtml += `
                        <a href="javascript:void(0)" class="comment-action text-danger" onclick="deleteComment(${reply.id})">
                            <i class="bi bi-trash"></i> 删除
                        </a>
                    `;
                }
                
                commentHtml += `</div></div>`;
            });
            
            commentHtml += `</div>`;
        }
        
        commentDiv.innerHTML = commentHtml;
        return commentDiv;
    } catch (error) {
        console.error('创建评论元素失败:', error, comment);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.textContent = '加载评论失败: ' + error.message;
        return errorDiv;
    }
}

// 提交评论
function submitComment() {
    const content = document.getElementById('comment-content').value.trim();
    const parentId = document.getElementById('parent-comment-id').value || null;
    if (!content) {
        showAlert('评论内容不能为空', 'warning');
        return;
    }
    const token = getToken();
    // 修正接口路径，确保为 /api/social/share/<share_id>/comment
    fetch(`/api/social/share/${currentShareId}/comment`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
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
        document.getElementById('comment-content').value = '';
        document.getElementById('parent-comment-id').value = '';
        loadComments(currentShareId);
        showAlert('评论发表成功', 'success');
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('发表评论失败，请稍后再试', 'danger');
    });
}

// 显示提示消息
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    const toastId = `toast-${Date.now()}`;
    const toastHtml = `
    <div id="${toastId}" class="toast align-items-center text-white bg-${type}" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    </div>
    `;
    
    document.getElementById('toast-container').innerHTML += toastHtml;
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();
    
    // 自动移除toast元素
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// 显示回复表单
function showReplyForm(parentId, username) {
    const replyModal = new bootstrap.Modal(document.getElementById('replyModal'));
    document.getElementById('reply-parent-id').value = parentId;
    document.getElementById('reply-to-username').textContent = username;
    replyModal.show();
}

// 提交回复
function submitReply() {
    const content = document.getElementById('reply-content').value.trim();
    const parentId = document.getElementById('reply-parent-id').value;
    
    if (!content) {
        showAlert('回复内容不能为空', 'warning');
        return;
    }
    
    fetch(`${apiBaseUrl}/share/${currentShareId}/comment`, {
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
            throw new Error('发表回复失败');
        }
        return response.json();
    })
    .then(data => {
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('replyModal'));
        modal.hide();
        
        // 清空输入框
        document.getElementById('reply-content').value = '';
        
        // 重新加载评论
        loadComments(currentShareId);
        
        // 更新评论数量
        const commentsCount = parseInt(document.getElementById('comments-count').textContent) + 1;
        document.getElementById('comments-count').textContent = commentsCount;
        document.getElementById('comments-count-heading').textContent = `(${commentsCount})`;
        
        showAlert('回复发表成功', 'success');
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('发表回复失败，请稍后再试', 'danger');
    });
}

// 删除评论
function deleteComment(commentId) {
    if (!confirm('确定要删除这条评论吗？此操作不可撤销。')) {
        return;
    }
    
    console.log('删除评论，ID:', commentId);
    
    fetch(`${apiBaseUrl}/comment/${commentId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        console.log('删除评论API响应状态:', response.status);
        if (!response.ok) {
            if (response.status === 401) {
                console.log('认证已过期，请重新登录');
                localStorage.removeItem('jwt_token');
                window.location.href = '/login';
                throw new Error('认证已过期，请重新登录');
            } else if (response.status === 403) {
                throw new Error('您没有权限删除此评论');
            }
            throw new Error(`删除评论失败，状态码: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('评论删除成功:', data);
        
        // 从DOM中移除评论
        const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`);
        if (commentElement) {
            // 如果是回复的评论，只移除该回复
            if (commentElement.closest('.comment-replies')) {
                commentElement.remove();
            } else {
                // 如果是主评论，移除整个评论块
                commentElement.remove();
            }
        }
        
        // 更新评论计数
        const commentCount = document.getElementById('comments-count');
        if (commentCount) {
            const currentCount = parseInt(commentCount.textContent) || 0;
            if (currentCount > 0) {
                const newCount = currentCount - 1;
                commentCount.textContent = newCount;
                
                // 同时更新评论标题计数
                const commentCountHeading = document.getElementById('comments-count-heading');
                if (commentCountHeading) {
                    commentCountHeading.textContent = `(${newCount})`;
                }
            }
        }
        
        // 显示成功消息
        showToast('评论已成功删除', 'success');
    })
    .catch(error => {
        console.error('删除评论出错:', error);
        showToast(`删除评论失败: ${error.message}`, 'danger');
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

// 显示错误信息
function showError(message) {
    document.getElementById('loading-indicator').classList.add('d-none');
    document.getElementById('content-not-available').classList.remove('d-none');
    document.getElementById('content-not-available').querySelector('p').textContent = message;
}

// 更新本地存储的点赞状态
function updateLocalLikedStatus(shareId, isLiked) {
    try {
        // 获取已存储的点赞状态
        let likedShares = JSON.parse(localStorage.getItem('liked_shares') || '[]');
        
        if (isLiked && !likedShares.includes(parseInt(shareId))) {
            // 添加到点赞列表
            likedShares.push(parseInt(shareId));
        } else if (!isLiked && likedShares.includes(parseInt(shareId))) {
            // 从点赞列表移除
            likedShares = likedShares.filter(id => id !== parseInt(shareId));
        }
        
        // 保存到本地存储
        localStorage.setItem('liked_shares', JSON.stringify(likedShares));
    } catch (error) {
        console.warn('无法更新本地点赞状态:', error);
    }
}

// 初始化点赞状态
function initLikedStatus() {
    try {
        // 获取已存储的点赞状态
        const likedShares = JSON.parse(localStorage.getItem('liked_shares') || '[]');
        
        // 如果当前分享在点赞列表中，更新UI
        if (likedShares.includes(parseInt(shareId))) {
            const likeButton = document.querySelector('.like-btn');
            if (likeButton) {
                likeButton.classList.add('liked');
                likeButton.querySelector('i').className = 'bi bi-heart-fill';
            }
        }
    } catch (error) {
        console.warn('初始化点赞状态失败:', error);
    }
} 