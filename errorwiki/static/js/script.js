// ========== 侧边栏统计更新 ==========
async function updateStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        document.getElementById('total-errors').textContent = data.total;
    } catch (e) {
        console.error('获取统计失败', e);
    }
}

// ========== 随机跳转 ==========
async function goToRandomError() {
    try {
        const response = await fetch('/api/random');
        const data = await response.json();
        if (data.id) {
            window.location.href = `/error/${data.id}`;
        } else {
            alert('还没有任何错误条目，快去添加第一个吧！');
        }
    } catch (e) {
        console.error('随机跳转失败', e);
    }
}

// ========== 初始化 ==========
document.addEventListener('DOMContentLoaded', function() {
    // 更新统计
    updateStats();
    
    // 随机按钮
    const randomBtn = document.getElementById('random-btn');
    if (randomBtn) {
        randomBtn.addEventListener('click', function(e) {
            e.preventDefault();
            goToRandomError();
        });
    }
    
    const randomFromDetail = document.getElementById('random-from-detail');
    if (randomFromDetail) {
        randomFromDetail.addEventListener('click', function(e) {
            e.preventDefault();
            goToRandomError();
        });
    }
    
    // 添加悬浮卡片效果（已有的 glass-card 类自带）
    console.log('💥 Error Wiki 已加载 · 准备记录每一次崩溃');
});

// ========== 快捷键 ==========
document.addEventListener('keydown', function(e) {
    // 按 / 聚焦搜索框
    if (e.key === '/' && !e.target.matches('input, textarea')) {
        e.preventDefault();
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            searchInput.focus();
        } else {
            window.location.href = '/search';
        }
    }
    
    // 按 R 随机跳转
    if (e.key === 'r' && !e.target.matches('input, textarea')) {
        e.preventDefault();
        goToRandomError();
    }
});

// 3秒后自动隐藏 Flash 消息
document.addEventListener('DOMContentLoaded', function() {
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(flash => {
        setTimeout(() => {
            flash.style.transition = 'opacity 0.3s';
            flash.style.opacity = '0';
            setTimeout(() => flash.remove(), 300);
        }, 3000);
    });
});

