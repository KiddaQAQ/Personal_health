// auth.js - 处理认证相关功能

// 检查用户是否已登录
function isLoggedIn() {
    return localStorage.getItem('jwt_token') !== null;
}

// 获取认证token
function getToken() {
    return localStorage.getItem('jwt_token');
}

// 获取用户信息
function getUserInfo() {
    const userInfo = localStorage.getItem('user_info');
    return userInfo ? JSON.parse(userInfo) : { id: null };
}

// 退出登录
function logout() {
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('user_info');
    window.location.href = '/login';
}

document.addEventListener('DOMContentLoaded', function() {
    // 如果当前页是登录或注册页，不执行重定向
    const currentPath = window.location.pathname;
    if (currentPath === '/login' || currentPath === '/register') {
        // 如果用户已登录，重定向到仪表盘
        const token = localStorage.getItem('jwt_token');
        if (token) {
            window.location.href = '/dashboard';
        }
    } else {
        // 如果是其他页面，确保用户已登录
        const token = localStorage.getItem('jwt_token');
        if (!token && currentPath !== '/') {
            window.location.href = '/login';
        }
    }
    
    // 确保所有导航链接都正确添加target属性
    document.querySelectorAll('.sidebar .nav-link').forEach(link => {
        if (!link.hasAttribute('target') && !link.getAttribute('href').startsWith('javascript:')) {
            link.setAttribute('target', '_self');
        }
    });
    
    // 防止链接在某些情况下被替换
    document.querySelectorAll('a').forEach(link => {
        if (link.getAttribute('href') && 
            !link.getAttribute('href').startsWith('#') && 
            !link.getAttribute('href').startsWith('javascript:') &&
            !link.hasAttribute('target')) {
            link.setAttribute('target', '_self');
        }
    });
    
    // 绑定退出登录按钮事件
    const logoutBtn = document.getElementById('logout-link');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            logout();
        });
    }
}); 