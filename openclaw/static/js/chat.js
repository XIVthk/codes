// static/js/chat.js - 完整版
document.addEventListener('DOMContentLoaded', function() {
    // ==================== 状态管理 ====================
    let currentChatId = null;
    let bots = {};
    let chats = [];
    let pinnedChats = JSON.parse(localStorage.getItem('pinnedChats') || '[]');
    let streamingMessages = {};
    let currentWorkingDir = '';
    let lastMessageCount = {}; // 记录每个聊天的最新消息数
    let processedMessageIds = new Set(); // 存储已处理的消息ID（防重复）
    
    // ==================== DOM 元素 ====================
    const chatsList = document.getElementById('chatsList');
    const messagesContainer = document.getElementById('messagesContainer');
    const currentChatName = document.getElementById('currentChatName');
    const chatTypeBadge = document.getElementById('chatTypeBadge');
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    const atBtn = document.getElementById('atBtn');
    
    // 文件树元素
    const currentDirPath = document.getElementById('currentDirPath');
    const filePanelPath = document.getElementById('filePanelPath');
    const fileTree = document.getElementById('fileTree');
    const refreshDirBtn = document.getElementById('refreshDirBtn');
    const goUpBtn = document.getElementById('goUpBtn');
    
    // 右键菜单
    const contextMenu = document.getElementById('contextMenu');
    const menuPin = document.getElementById('menuPin');
    const menuDelete = document.getElementById('menuDelete');
    let selectedChatId = null;
    
    // 弹窗
    const botManagerModal = document.getElementById('botManagerModal');
    const newChatModal = document.getElementById('newChatModal');
    
    // ==================== 初始化 ====================
    loadBots();
    loadChats();
    loadWorkingDir();
    loadFileTree();
    startMessagePolling(); // 启动轮询
    
    // ==================== 事件监听 ====================
    document.getElementById('newChatBtn')?.addEventListener('click', () => {
        openNewChatModal();
    });
    
    document.getElementById('botManagerBtn')?.addEventListener('click', () => {
        openBotManager();
    });
    
    document.getElementById('closeBotManager')?.addEventListener('click', () => {
        botManagerModal?.classList.remove('show');
    });
    
    document.getElementById('closeNewChat')?.addEventListener('click', () => {
        newChatModal?.classList.remove('show');
    });
    
    document.getElementById('saveBotsBtn')?.addEventListener('click', saveBots);
    
    document.getElementById('createChatBtn')?.addEventListener('click', createChat);
    
    // 聊天类型切换
    document.querySelectorAll('input[name="chatType"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const botSelectGroup = document.getElementById('botSelectGroup');
            if (this.value === 'single') {
                botSelectGroup.style.display = 'block';
            } else {
                botSelectGroup.style.display = 'none';
            }
        });
    });
    
    // 发送消息
    sendBtn?.addEventListener('click', sendMessage);
    messageInput?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // @按钮
    atBtn?.addEventListener('click', showMentionMenu);
    
    // 文件树按钮
    refreshDirBtn?.addEventListener('click', () => {
        loadWorkingDir();
        loadFileTree();
    });
    
    goUpBtn?.addEventListener('click', goToParentDir);
    
    // 右键菜单选项
    menuPin?.addEventListener('click', () => {
        if (selectedChatId) {
            togglePinChat(selectedChatId);
            hideContextMenu();
        }
    });
    
    menuDelete?.addEventListener('click', () => {
        if (selectedChatId) {
            deleteChat(selectedChatId);
            hideContextMenu();
        }
    });
    
    // 点击其他地方关闭右键菜单
    document.addEventListener('click', hideContextMenu);
    
    // ==================== 主动消息轮询（防重复版）====================
    function startMessagePolling() {
        let lastCheckTime = Date.now();
        
        setInterval(async () => {
            if (!currentChatId) return;
            
            try {
                const response = await fetch(`/api/chat/${currentChatId}`);
                const data = await response.json();
                
                if (data.success) {
                    const currentCount = data.chat.messages.length;
                    const lastCount = lastMessageCount[currentChatId] || 0;
                    
                    // 如果有新消息
                    if (currentCount > lastCount) {
                        const newMessages = data.chat.messages.slice(lastCount);
                        
                        for (const msg of newMessages) {
                            // 检查是否已经处理过（通过ID）
                            if (processedMessageIds.has(msg.id)) {
                                console.log('跳过已处理消息:', msg.id);
                                continue;
                            }
                            
                            // 只显示非用户发送的新消息
                            if (msg.type !== 'user' && msg.sender !== '你') {
                                // 检查是否在最近2秒内（防止重复）
                                const msgTime = new Date(msg.time).getTime();
                                const timeDiff = msgTime - lastCheckTime;
                                
                                // 如果消息时间在检查时间之后，且不在流式输出中
                                if (timeDiff > -1000) {
                                    const isStreaming = Object.keys(streamingMessages).length > 0;
                                    if (!isStreaming) {
                                        appendMessage({
                                            id: msg.id,
                                            sender: msg.sender,
                                            content: msg.content,
                                            time: formatTime(msg.time),
                                            type: msg.type
                                        });
                                        
                                        // 记录已处理的消息ID
                                        processedMessageIds.add(msg.id);
                                        
                                        // 限制Set大小，避免内存泄漏
                                        if (processedMessageIds.size > 100) {
                                            const idsArray = Array.from(processedMessageIds);
                                            processedMessageIds = new Set(idsArray.slice(-50));
                                        }
                                    }
                                }
                            }
                        }
                        
                        lastMessageCount[currentChatId] = currentCount;
                        lastCheckTime = Date.now();
                    }
                }
            } catch (error) {
                console.error('轮询新消息失败:', error);
            }
        }, 2000);
    }
    
    function updateMessageCount(chat) {
        if (chat && chat.id) {
            lastMessageCount[chat.id] = chat.messages.length;
        }
    }
    
    // ==================== 右键菜单函数 ====================
    function showContextMenu(event, chatId) {
        event.preventDefault();
        event.stopPropagation();
        
        selectedChatId = chatId;
        
        const isPinned = pinnedChats.includes(chatId);
        menuPin.textContent = isPinned ? '📌 取消置顶' : '📌 置顶聊天';
        
        contextMenu.style.display = 'block';
        contextMenu.style.left = event.pageX + 'px';
        contextMenu.style.top = event.pageY + 'px';
    }
    
    function hideContextMenu() {
        contextMenu.style.display = 'none';
        selectedChatId = null;
    }
    
    function togglePinChat(chatId) {
        const index = pinnedChats.indexOf(chatId);
        if (index === -1) {
            pinnedChats.push(chatId);
            showToast('聊天已置顶', 'success');
        } else {
            pinnedChats.splice(index, 1);
            showToast('聊天已取消置顶', 'info');
        }
        localStorage.setItem('pinnedChats', JSON.stringify(pinnedChats));
        renderChatsList();
    }
    
    async function deleteChat(chatId) {
        const confirmed = await showConfirm('确定要删除这个聊天吗？此操作不可恢复。', '删除聊天');
        if (!confirmed) return;
        
        try {
            const response = await fetch(`/api/chat/${chatId}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            
            if (data.success) {
                chats = chats.filter(c => c.id !== chatId);
                
                if (currentChatId === chatId) {
                    currentChatId = null;
                    if (messagesContainer) {
                        messagesContainer.innerHTML = `
                            <div style="text-align: center; color: #888; padding: 40px;">
                                <h3 style="color: #fff;">👋 聊天已删除</h3>
                                <p>请选择其他聊天或新建一个</p>
                            </div>
                        `;
                    }
                    if (currentChatName) currentChatName.textContent = '请选择一个聊天';
                    enableInput(false);
                }
                
                const pinIndex = pinnedChats.indexOf(chatId);
                if (pinIndex !== -1) {
                    pinnedChats.splice(pinIndex, 1);
                    localStorage.setItem('pinnedChats', JSON.stringify(pinnedChats));
                }
                
                renderChatsList();
                showToast('聊天已删除', 'success');
            } else {
                showToast('删除失败: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('删除聊天失败:', error);
            showToast('删除失败: ' + error.message, 'error');
        }
    }
    
    // ==================== 文件树函数 ====================
    async function loadFileTree() {
        const fileTree = document.getElementById('fileTree');
        if (!fileTree) return;
        
        fileTree.innerHTML = '<div style="padding: 10px; color: #888;">📁 加载文件列表...</div>';
        
        try {
            const response = await fetch('/api/file-tree');
            const data = await response.json();
            
            if (data.success) {
                fileTree.innerHTML = '';
                
                if (data.path && data.path !== '/' && !data.path.match(/^[a-zA-Z]:\\$/)) {
                    const upDiv = document.createElement('div');
                    upDiv.style.cssText = `
                        padding: 8px 10px;
                        margin-bottom: 8px;
                        background-color: #2d2d2d;
                        border-radius: 6px;
                        cursor: pointer;
                        color: #5fe7ff;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        border: 1px solid #3a3a3a;
                    `;
                    upDiv.innerHTML = '📁 .. <span style="color: #888; margin-left: auto;">上级目录</span>';
                    upDiv.onclick = (e) => {
                        e.stopPropagation();
                        goToParentDir();
                    };
                    upDiv.onmouseover = () => upDiv.style.backgroundColor = '#3a3a3a';
                    upDiv.onmouseout = () => upDiv.style.backgroundColor = '#2d2d2d';
                    fileTree.appendChild(upDiv);
                }
                
                renderFileTree(data.tree, fileTree);
            } else {
                fileTree.innerHTML = `<div style="color: #ff5555; padding: 10px;">❌ 加载失败: ${data.error}</div>`;
            }
        } catch (error) {
            fileTree.innerHTML = `<div style="color: #ff5555; padding: 10px;">❌ 请求失败: ${error.message}</div>`;
        }
    }
    
    function renderFileTree(node, container, level = 0) {
        if (!node || !node.children) return;
        
        node.children.forEach(child => {
            const itemDiv = document.createElement('div');
            itemDiv.style.cssText = `
                padding: 6px 8px 6px ${level * 20 + 8}px;
                margin: 2px 0;
                border-radius: 4px;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 8px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            `;
            
            itemDiv.onmouseover = () => itemDiv.style.backgroundColor = '#2d2d2d';
            itemDiv.onmouseout = () => itemDiv.style.backgroundColor = 'transparent';
            
            let icon = '📄';
            let color = '#ffffff';
            
            if (child.type === 'dir') {
                icon = '📁';
                color = '#5fe7ff';
            } else {
                const ext = child.name.split('.').pop()?.toLowerCase();
                const iconMap = {
                    'py': '🐍', 'js': '📜', 'html': '🌐', 'css': '🎨',
                    'json': '📋', 'md': '📝', 'txt': '📄', 'jpg': '🖼️',
                    'png': '🖼️', 'gif': '🖼️', 'mp3': '🎵', 'mp4': '🎬',
                    'zip': '📦', 'exe': '⚙️', 'pdf': '📕', 'doc': '📘'
                };
                icon = iconMap[ext] || '📄';
            }
            
            const iconSpan = document.createElement('span');
            iconSpan.textContent = icon;
            iconSpan.style.fontSize = '16px';
            
            const nameSpan = document.createElement('span');
            nameSpan.style.cssText = `
                color: ${color};
                flex: 1;
                overflow: hidden;
                text-overflow: ellipsis;
                font-size: 13px;
            `;
            nameSpan.textContent = child.name;
            
            if (child.type === 'file' && child.size_str) {
                const sizeSpan = document.createElement('span');
                sizeSpan.style.cssText = 'color: #888; font-size: 11px; margin-left: 8px;';
                sizeSpan.textContent = child.size_str;
                nameSpan.appendChild(sizeSpan);
            }
            
            itemDiv.appendChild(iconSpan);
            itemDiv.appendChild(nameSpan);
            
            itemDiv.onclick = (e) => {
                e.stopPropagation();
                if (child.type === 'dir') {
                    setWorkingDir(child.path);
                } else {
                    insertFilePath(child.path);
                }
            };
            
            container.appendChild(itemDiv);
            
            if (child.type === 'dir' && child.children && child.children.length > 0) {
                renderFileTree(child, container, level + 1);
            }
        });
    }
    
    function insertFilePath(path) {
        if (!messageInput) return;
        
        let displayPath = path;
        if (window.userHome && path.startsWith(window.userHome)) {
            displayPath = '~' + path.slice(window.userHome.length);
        }
        
        const cursorPos = messageInput.selectionStart;
        const text = messageInput.value;
        const newText = text.slice(0, cursorPos) + `📁 ${displayPath} ` + text.slice(cursorPos);
        messageInput.value = newText;
        messageInput.focus();
        messageInput.selectionStart = messageInput.selectionEnd = cursorPos + displayPath.length + 3;
    }
    
    async function setWorkingDir(path) {
        try {
            const response = await fetch('/api/working-dir', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: path })
            });
            const data = await response.json();
            if (data.success) {
                currentWorkingDir = data.path;
                updateWorkingDirDisplay(data.path);
                loadFileTree();
                
                if (currentChatId) {
                    showSystemMessage(`📁 工作目录已切换到: ${data.path}`);
                }
                showToast('工作目录已切换', 'success');
            } else {
                showToast('切换目录失败: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('设置工作目录失败:', error);
            showToast('切换目录失败: ' + error.message, 'error');
        }
    }
    
    async function goToParentDir() {
        try {
            const response = await fetch('/api/working-dir/up', {
                method: 'POST'
            });
            const data = await response.json();
            if (data.success) {
                currentWorkingDir = data.path;
                updateWorkingDirDisplay(data.path);
                loadFileTree();
            } else {
                showToast('返回上级失败: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('返回上级目录失败:', error);
            showToast('返回上级失败: ' + error.message, 'error');
        }
    }
    
    async function loadWorkingDir() {
        try {
            const response = await fetch('/api/working-dir');
            const data = await response.json();
            if (data.success) {
                currentWorkingDir = data.path;
                window.userHome = data.home;
                updateWorkingDirDisplay(data.path);
            }
        } catch (error) {
            console.error('加载工作目录失败:', error);
        }
    }
    
    function updateWorkingDirDisplay(path) {
        let displayPath = path;
        if (window.userHome && path.startsWith(window.userHome)) {
            displayPath = '~' + path.slice(window.userHome.length);
        }
        
        if (currentDirPath) {
            currentDirPath.textContent = displayPath;
            currentDirPath.title = path;
        }
        if (filePanelPath) {
            filePanelPath.textContent = displayPath;
            filePanelPath.title = path;
        }
    }
    
    function showSystemMessage(msg) {
        if (!messagesContainer) return;
        
        const msgDiv = document.createElement('div');
        msgDiv.style.cssText = `
            background-color: rgba(95, 231, 255, 0.1);
            border: 1px solid #5fe7ff;
            border-radius: 8px;
            padding: 8px 12px;
            margin: 5px auto;
            max-width: 90%;
            align-self: center;
            color: #5fe7ff;
            font-size: 13px;
        `;
        msgDiv.textContent = msg;
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // ==================== 聊天列表渲染 ====================
    function renderChatsList() {
        if (!chatsList) return;
        
        if (chats.length === 0) {
            chatsList.innerHTML = '<div style="padding: 20px; text-align: center; color: #888;">暂无聊天，点击"新建聊天"开始</div>';
            return;
        }
        
        const pinned = chats.filter(chat => pinnedChats.includes(chat.id));
        const normal = chats.filter(chat => !pinnedChats.includes(chat.id));
        
        let html = '';
        
        if (pinned.length > 0) {
            html += '<div style="padding: 5px 10px; color: #5fe7ff; font-size: 12px;">📌 置顶</div>';
            pinned.forEach(chat => {
                html += renderChatItem(chat, true);
            });
        }
        
        if (normal.length > 0) {
            if (pinned.length > 0) {
                html += '<div style="padding: 5px 10px; color: #888; font-size: 12px; margin-top: 10px;">所有聊天</div>';
            }
            normal.forEach(chat => {
                html += renderChatItem(chat, false);
            });
        }
        
        chatsList.innerHTML = html;
        
        document.querySelectorAll('.chat-item').forEach(item => {
            item.addEventListener('contextmenu', (e) => {
                const chatId = item.dataset.chatId;
                showContextMenu(e, chatId);
            });
        });
    }
    
    function renderChatItem(chat, isPinned) {
        const lastMsg = chat.last_message || '暂无消息';
        const time = chat.updated_at ? formatTime(chat.updated_at) : '';
        const isActive = currentChatId === chat.id;
        
        return `
            <div class="chat-item ${isActive ? 'active' : ''} ${isPinned ? 'pinned' : ''}" 
                 data-chat-id="${chat.id}"
                 onclick="window.selectChat('${chat.id}')"
                 style="
                    padding: 12px;
                    margin-bottom: 5px;
                    border-radius: 6px;
                    cursor: pointer;
                    background-color: ${isActive ? '#2d2d2d' : 'transparent'};
                    border-left: ${isActive ? '3px solid #5fe7ff' : '1px solid transparent'};
                    position: relative;
                 ">
                <div style="font-weight: bold; margin-bottom: 3px; padding-right: 25px;">${chat.name}</div>
                <div style="font-size: 12px; color: #888; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${lastMsg}</div>
                <div style="font-size: 10px; color: #666; margin-top: 3px;">${time}</div>
            </div>
        `;
    }
    
    window.selectChat = async function(chatId) {
        try {
            const response = await fetch(`/api/chat/${chatId}`);
            const data = await response.json();
            if (data.success) {
                currentChatId = chatId;
                renderChat(data.chat);
                updateMessageCount(data.chat);
                enableInput(true);
                renderChatsList();
            }
        } catch (error) {
            console.error('加载聊天失败:', error);
            showToast('加载聊天失败: ' + error.message, 'error');
        }
    };
    
    // ==================== API 调用 ====================
    async function loadBots() {
        try {
            const response = await fetch('/api/bots');
            const data = await response.json();
            if (data.success) {
                bots = data.bots;
                updateBotSelect();
            }
        } catch (error) {
            console.error('加载 Bot 失败:', error);
        }
    }
    
    async function loadChats() {
        try {
            const response = await fetch('/api/chats');
            const data = await response.json();
            if (data.success) {
                chats = data.chats;
                renderChatsList();
            }
        } catch (error) {
            console.error('加载聊天列表失败:', error);
        }
    }
    
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message || !currentChatId) return;
        
        messageInput.value = '';
        enableInput(false);
        
        const url = '/api/send/stream';
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                chat_id: currentChatId,
                message: message,
                sender: '你'
            })
        }).then(response => {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            function read() {
                reader.read().then(({done, value}) => {
                    if (done) return;
                    
                    const text = decoder.decode(value);
                    const lines = text.split('\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(5));
                                handleStreamData(data);
                            } catch (e) {
                                console.error('解析流数据失败:', e);
                            }
                        }
                    }
                    
                    read();
                }).catch(error => {
                    console.error('读取流失败:', error);
                    enableInput(true);
                });
            }
            
            read();
        }).catch(error => {
            console.error('流式请求失败:', error);
            enableInput(true);
            showToast('发送失败: ' + error.message, 'error');
        });
    }
    
    // ==================== 流式数据处理（核心）====================
    function handleStreamData(data) {
        switch (data.type) {
            case 'user_message':
                appendMessage({
                    id: data.message.id,
                    sender: data.message.sender,
                    content: data.message.content,
                    time: formatTime(data.message.time),
                    type: 'user'
                });
                break;
                
            case 'tool_start':
                // 显示正在执行的命令
                let cmd = '';
                if (data.tool_name === 'run_command') {
                    cmd = data.arguments.command || '';
                } else if (data.tool_name === 'change_directory') {
                    cmd = `cd ${data.arguments.path || ''}`;
                } else {
                    cmd = `${data.tool_name} ${JSON.stringify(data.arguments)}`;
                }
                showToast(`🤖 ${data.bot_name} 正在执行: ${cmd}`, 'info', 2000);
                break;
                
            case 'bot_start':
                streamingMessages[data.reply_id] = {
                    botName: data.bot_name,
                    content: '',
                    element: createStreamingMessage(data.bot_name)
                };
                break;
                
            case 'bot_chunk':
                if (streamingMessages[data.reply_id]) {
                    streamingMessages[data.reply_id].content += data.content;
                    updateStreamingMessage(data.reply_id, data.content);
                }
                break;
                
            case 'bot_end':
                if (streamingMessages[data.reply_id]) {
                    if (data.message) {
                        finalizeStreamingMessageWithData(data.reply_id, data.message);
                    } else {
                        finalizeStreamingMessage(data.reply_id, data.full_content, data.time);
                    }
                    delete streamingMessages[data.reply_id];
                    
                    // 重要：Bot回复结束后，刷新工作目录（可能执行了cd命令）
                    refreshWorkingDir();
                }
                break;
                
            case 'error':
                showErrorMessage(data.message);
                enableInput(true);
                break;
                
            case 'done':
                enableInput(true);
                loadChats();
                loadFileTree();
                // 再次刷新工作目录确保同步
                refreshWorkingDir();
                // 更新消息计数
                setTimeout(async () => {
                    if (!currentChatId) return;
                    try {
                        const response = await fetch(`/api/chat/${currentChatId}`);
                        const data = await response.json();
                        if (data.success) {
                            updateMessageCount(data.chat);
                        }
                    } catch (error) {
                        console.error('更新消息计数失败:', error);
                    }
                }, 500);
                break;
        }
    }
    
    // 刷新工作目录函数
    async function refreshWorkingDir() {
        try {
            const response = await fetch('/api/working-dir');
            const data = await response.json();
            if (data.success) {
                currentWorkingDir = data.path;
                window.userHome = data.home;
                updateWorkingDirDisplay(data.path);
                console.log('工作目录已刷新:', data.path);
            }
        } catch (error) {
            console.error('刷新工作目录失败:', error);
        }
    }
    
    function showErrorMessage(msg) {
        if (!messagesContainer) return;
        
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            background-color: rgba(255, 85, 85, 0.1);
            border: 1px solid #ff5555;
            border-radius: 8px;
            padding: 8px 12px;
            margin: 5px auto;
            max-width: 90%;
            align-self: center;
            color: #ff5555;
        `;
        errorDiv.textContent = '❌ ' + msg;
        messagesContainer.appendChild(errorDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    function createStreamingMessage(botName) {
        if (!messagesContainer) return null;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot streaming';
        messageDiv.style.cssText = `
            align-self: flex-start;
            background-color: #252525;
            border: 1px solid #3a3a3a;
            border-radius: 12px;
            border-bottom-left-radius: 4px;
            padding: 12px 16px;
            margin: 5px 0;
            max-width: 70%;
        `;
        
        const headerDiv = document.createElement('div');
        headerDiv.style.cssText = `
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-size: 12px;
        `;
        headerDiv.innerHTML = `
            <span style="font-weight: bold; color: #5fe7ff;">${botName}</span>
            <span style="color: #888;">刚刚</span>
        `;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.style.cssText = `
            line-height: 1.5;
            word-wrap: break-word;
        `;
        
        messageDiv.appendChild(headerDiv);
        messageDiv.appendChild(contentDiv);
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        return messageDiv;
    }
    
    function updateStreamingMessage(replyId, chunk) {
        const msg = streamingMessages[replyId];
        if (msg && msg.element) {
            const contentDiv = msg.element.querySelector('.message-content');
            if (contentDiv) {
                contentDiv.innerHTML = formatMessage(msg.content);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        }
    }
    
    function finalizeStreamingMessage(replyId, fullContent, time) {
        const msg = streamingMessages[replyId];
        if (msg && msg.element) {
            msg.element.classList.remove('streaming');
            const contentDiv = msg.element.querySelector('.message-content');
            if (contentDiv) {
                contentDiv.innerHTML = formatMessage(fullContent);
            }
            const timeSpan = msg.element.querySelector('.message-time');
            if (timeSpan) {
                timeSpan.textContent = formatTime(time);
            }
        }
    }
    
    function finalizeStreamingMessageWithData(replyId, messageData) {
        const msg = streamingMessages[replyId];
        if (msg && msg.element) {
            msg.element.remove();
            appendMessage({
                id: messageData.id,
                sender: messageData.sender,
                content: messageData.content,
                time: formatTime(messageData.time),
                type: 'bot'
            });
        }
    }
    
    function renderChat(chat) {
        if (!messagesContainer || !currentChatName || !chatTypeBadge) return;
        
        currentChatName.textContent = chat.name;
        chatTypeBadge.textContent = chat.type === 'group' ? '群聊' : '单聊';
        
        if (chat.messages.length === 0) {
            messagesContainer.innerHTML = `
                <div style="text-align: center; color: #888; padding: 40px;">
                    <h3 style="color: #fff; margin-bottom: 15px;">👋 开始对话吧</h3>
                    <p style="margin-bottom: 10px;">在群聊中，使用 <span style="background-color: #ff79c6; color: #000; padding: 2px 6px; border-radius: 4px;">@Bot名字</span> 可以让指定Bot回复。</p>
                    <p>右侧文件树：点击文件可引用，点击文件夹可切换工作目录</p>
                    ${Object.keys(bots).length === 0 ? '<p style="color: #ff5555; margin-top: 20px;">⚠️ 还没有Bot，先去 Bot管理 创建吧！</p>' : ''}
                </div>
            `;
            return;
        }
        
        let html = '';
        chat.messages.forEach(msg => {
            const time = formatTime(msg.time);
            const content = formatMessage(msg.content);
            const isUser = msg.type === 'user';
            
            html += `
                <div class="message ${msg.type}" data-msg-id="${msg.id}" style="
                    align-self: ${isUser ? 'flex-end' : 'flex-start'};
                    background-color: ${isUser ? '#5fe7ff' : '#252525'};
                    color: ${isUser ? '#000' : '#fff'};
                    border: ${isUser ? 'none' : '1px solid #3a3a3a'};
                    border-radius: 12px;
                    border-bottom-${isUser ? 'right' : 'left'}-radius: 4px;
                    padding: 12px 16px;
                    margin: 5px 0;
                    max-width: 70%;
                ">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 12px;">
                        <span style="font-weight: bold; color: ${isUser ? '#000' : '#5fe7ff'};">${msg.sender}</span>
                        <span style="color: ${isUser ? '#333' : '#888'};">${time}</span>
                    </div>
                    <div style="line-height: 1.5; word-wrap: break-word;">${content}</div>
                </div>
            `;
        });
        
        messagesContainer.innerHTML = html;
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    function appendMessage(msg) {
        if (!messagesContainer) return;
        
        // 检查是否已存在相同ID的消息（防止重复）
        if (msg.id) {
            const existingMsg = document.querySelector(`[data-msg-id="${msg.id}"]`);
            if (existingMsg) {
                console.log('消息已存在，跳过:', msg.id);
                return;
            }
        }
        
        const isUser = msg.type === 'user';
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${msg.type}`;
        if (msg.id) {
            messageDiv.setAttribute('data-msg-id', msg.id);
        }
        messageDiv.style.cssText = `
            align-self: ${isUser ? 'flex-end' : 'flex-start'};
            background-color: ${isUser ? '#5fe7ff' : '#252525'};
            color: ${isUser ? '#000' : '#fff'};
            border: ${isUser ? 'none' : '1px solid #3a3a3a'};
            border-radius: 12px;
            border-bottom-${isUser ? 'right' : 'left'}-radius: 4px;
            padding: 12px 16px;
            margin: 5px 0;
            max-width: 70%;
        `;
        
        messageDiv.innerHTML = `
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 12px;">
                <span style="font-weight: bold; color: ${isUser ? '#000' : '#5fe7ff'};">${msg.sender}</span>
                <span style="color: ${isUser ? '#333' : '#888'};">${msg.time}</span>
            </div>
            <div style="line-height: 1.5; word-wrap: break-word;">${formatMessage(msg.content)}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // ==================== 工具函数 ====================
    function formatTime(isoString) {
        if (!isoString) return '';
        const date = new Date(isoString);
        return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
    }
    
    function formatMessage(content) {
        if (!content) return '';
        
        let escaped = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
        
        escaped = escaped.replace(/\*\*(.+?)\*\*/g, '<strong style="color: #5fe7ff;">$1</strong>');
        escaped = escaped.replace(/\*(.+?)\*/g, '<em style="color: #888;">$1</em>');
        escaped = escaped.replace(/@(\w+)/g, '<span style="color: #ff79c6; font-weight: bold;">@$1</span>');
        escaped = escaped.replace(/@All/g, '<span style="color: #ff79c6; font-weight: bold;">@All</span>');
        escaped = escaped.replace(/\n/g, '<br>');
        
        return escaped;
    }
    
    function enableInput(enabled) {
        if (messageInput) messageInput.disabled = !enabled;
        if (sendBtn) sendBtn.disabled = !enabled;
        if (enabled && messageInput) {
            messageInput.focus();
        }
    }
    
    function showMentionMenu() {
        if (!currentChatId) return;
        
        if (Object.keys(bots).length === 0) {
            showToast('还没有Bot，请先在Bot管理中创建', 'warning');
            return;
        }
        
        const menu = document.createElement('div');
        menu.style.cssText = `
            position: fixed;
            background-color: #252525;
            border: 1px solid #3a3a3a;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 1000;
            min-width: 150px;
        `;
        
        Object.keys(bots).forEach(botName => {
            const item = document.createElement('div');
            item.style.cssText = `
                padding: 10px 15px;
                cursor: pointer;
                color: #fff;
            `;
            item.textContent = botName;
            item.onmouseover = () => item.style.backgroundColor = '#2d2d2d';
            item.onmouseout = () => item.style.backgroundColor = 'transparent';
            item.onclick = () => {
                insertMention(botName);
                menu.remove();
            };
            menu.appendChild(item);
        });
        
        const separator = document.createElement('div');
        separator.style.cssText = 'height: 1px; background-color: #3a3a3a; margin: 5px 0;';
        menu.appendChild(separator);
        
        const allItem = document.createElement('div');
        allItem.style.cssText = `
            padding: 10px 15px;
            cursor: pointer;
            color: #5fe7ff;
        `;
        allItem.textContent = '@All';
        allItem.onmouseover = () => allItem.style.backgroundColor = '#2d2d2d';
        allItem.onmouseout = () => allItem.style.backgroundColor = 'transparent';
        allItem.onclick = () => {
            insertMention('All');
            menu.remove();
        };
        menu.appendChild(allItem);
        
        const rect = atBtn.getBoundingClientRect();
        menu.style.bottom = (window.innerHeight - rect.top + 10) + 'px';
        menu.style.left = rect.left + 'px';
        
        document.body.appendChild(menu);
        
        setTimeout(() => {
            document.addEventListener('click', function closeMenu(e) {
                if (!menu.contains(e.target) && e.target !== atBtn) {
                    menu.remove();
                    document.removeEventListener('click', closeMenu);
                }
            });
        }, 100);
    }
    
    function insertMention(botName) {
        if (!messageInput) return;
        
        const cursorPos = messageInput.selectionStart;
        const text = messageInput.value;
        const newText = text.slice(0, cursorPos) + `@${botName} ` + text.slice(cursorPos);
        messageInput.value = newText;
        messageInput.focus();
        messageInput.selectionStart = messageInput.selectionEnd = cursorPos + botName.length + 2;
    }
    
    // ==================== 弹窗函数 ====================
    function openNewChatModal() {
        updateBotSelect();
        const nameInput = document.getElementById('chatName');
        if (nameInput) nameInput.value = '';
        
        const groupRadio = document.querySelector('input[name="chatType"][value="group"]');
        if (groupRadio) groupRadio.checked = true;
        
        const botSelectGroup = document.getElementById('botSelectGroup');
        if (botSelectGroup) botSelectGroup.style.display = 'none';
        
        if (newChatModal) newChatModal.classList.add('show');
    }
    
    function updateBotSelect() {
        const select = document.getElementById('botSelect');
        if (!select) return;
        
        select.innerHTML = '<option value="">请选择</option>';
        Object.keys(bots).forEach(botName => {
            select.innerHTML += `<option value="${botName}">${botName}</option>`;
        });
    }
    
    async function createChat() {
        const type = document.querySelector('input[name="chatType"]:checked')?.value;
        const nameInput = document.getElementById('chatName');
        const name = nameInput?.value.trim() || (type === 'group' ? '新群聊' : '新对话');
        const botSelect = document.getElementById('botSelect');
        const botName = type === 'single' ? botSelect?.value : null;
        
        if (type === 'single' && !botName) {
            showToast('请选择要聊天的 Bot', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/chat/new', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    type: type,
                    name: name,
                    bot_name: botName
                })
            });
            
            const data = await response.json();
            if (data.success) {
                if (newChatModal) newChatModal.classList.remove('show');
                loadChats();
                window.selectChat(data.chat_id);
                showToast('聊天创建成功', 'success');
            }
        } catch (error) {
            console.error('创建聊天失败:', error);
            showToast('创建失败: ' + error.message, 'error');
        }
    }
    
    function openBotManager() {
        renderBotsList();
        if (botManagerModal) botManagerModal.classList.add('show');
    }
    
    function renderBotsList() {
        const container = document.getElementById('botsList');
        if (!container) return;
        
        if (Object.keys(bots).length === 0) {
            container.innerHTML = '<div style="padding: 20px; text-align: center; color: #888;">暂无Bot，点击下方按钮添加</div>';
            return;
        }
        
        let html = '';
        Object.keys(bots).forEach(botName => {
            html += `
                <div class="bot-item" data-bot-name="${botName}" style="
                    background-color: #2d2d2d;
                    border-radius: 6px;
                    padding: 15px;
                    margin-bottom: 10px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <input type="text" class="bot-name-input" value="${botName}" placeholder="Bot名称" style="
                            background-color: #1e1e1e;
                            border: 1px solid #3a3a3a;
                            color: #fff;
                            padding: 5px 10px;
                            border-radius: 4px;
                            width: 200px;
                        ">
                        <button class="remove-bot-btn" onclick="window.removeBot('${botName}')" style="
                            background: none;
                            border: none;
                            color: #ff5555;
                            font-size: 20px;
                            cursor: pointer;
                        ">&times;</button>
                    </div>
                    <textarea class="bot-prompt-input" placeholder="提示词..." style="
                        width: 100%;
                        min-height: 80px;
                        background-color: #1e1e1e;
                        border: 1px solid #3a3a3a;
                        color: #fff;
                        padding: 8px;
                        border-radius: 4px;
                        font-family: inherit;
                        resize: vertical;
                    ">${bots[botName].prompt || ''}</textarea>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }
    
    window.removeBot = async function(botName) {
        const confirmed = await showConfirm(`确定要删除 Bot ${botName} 吗？`, '删除 Bot');
        if (!confirmed) return;
        
        delete bots[botName];
        renderBotsList();
        showToast(`Bot ${botName} 已删除`, 'success');
    };
    
    document.getElementById('addBotBtn')?.addEventListener('click', function() {
        const newName = `Bot${Object.keys(bots).length + 1}`;
        bots[newName] = {
            prompt: '你是一个有用的AI助手。'
        };
        renderBotsList();
    });
    
    async function saveBots() {
        const newBots = {};
        const botItems = document.querySelectorAll('.bot-item');
        
        if (botItems.length === 0) {
            showToast('请至少添加一个 Bot', 'warning');
            return;
        }
        
        botItems.forEach(item => {
            const nameInput = item.querySelector('.bot-name-input');
            const promptInput = item.querySelector('.bot-prompt-input');
            const name = nameInput?.value.trim();
            
            if (name) {
                newBots[name] = {
                    prompt: promptInput?.value.trim() || '你是一个有用的AI助手。'
                };
            }
        });
        
        try {
            const response = await fetch('/api/bots', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newBots)
            });
            
            const data = await response.json();
            if (data.success) {
                bots = newBots;
                if (botManagerModal) botManagerModal.classList.remove('show');
                updateBotSelect();
                
                if (currentChatId) {
                    window.selectChat(currentChatId);
                }
                
                showToast('Bot 配置已保存', 'success');
            }
        } catch (error) {
            console.error('保存 Bot 失败:', error);
            showToast('保存失败: ' + error.message, 'error');
        }
    }
});

// ==================== Toast 通知系统 ====================
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toast = document.createElement('div');
    
    const colors = {
        success: { bg: 'rgba(80, 250, 123, 0.1)', border: '#50fa7b', text: '#50fa7b', icon: '✅' },
        error: { bg: 'rgba(255, 85, 85, 0.1)', border: '#ff5555', text: '#ff5555', icon: '❌' },
        warning: { bg: 'rgba(255, 184, 108, 0.1)', border: '#ffb86c', text: '#ffb86c', icon: '⚠️' },
        info: { bg: 'rgba(95, 231, 255, 0.1)', border: '#5fe7ff', text: '#5fe7ff', icon: 'ℹ️' }
    };
    
    const color = colors[type] || colors.info;
    
    toast.style.cssText = `
        background-color: ${color.bg};
        border: 1px solid ${color.border};
        border-radius: 8px;
        padding: 12px 20px;
        color: ${color.text};
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(5px);
        display: flex;
        align-items: center;
        gap: 10px;
        min-width: 250px;
        max-width: 350px;
        transform: translateX(400px);
        animation: slideIn 0.3s ease forwards;
        cursor: pointer;
        pointer-events: auto;
        margin-bottom: 10px;
    `;
    
    toast.innerHTML = `
        <span style="font-size: 18px;">${color.icon}</span>
        <span style="flex: 1;">${message}</span>
        <span style="font-size: 16px; opacity: 0.5;">✕</span>
    `;
    
    toast.addEventListener('click', () => {
        toast.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    });
    
    container.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }
    }, duration);
}

// ==================== 自定义确认弹窗 ====================
function showConfirm(message, title = '确认操作', okText = '确定', cancelText = '取消') {
    return new Promise((resolve) => {
        const modal = document.getElementById('confirmModal');
        const titleEl = document.getElementById('confirmTitle');
        const messageEl = document.getElementById('confirmMessage');
        const okBtn = document.getElementById('confirmOkBtn');
        const cancelBtn = document.getElementById('confirmCancelBtn');
        
        if (!modal || !titleEl || !messageEl || !okBtn || !cancelBtn) {
            resolve(confirm(message));
            return;
        }
        
        titleEl.textContent = title;
        messageEl.textContent = message;
        okBtn.textContent = okText;
        cancelBtn.textContent = cancelText;
        
        if (title.includes('删除') || title.includes('Delete')) {
            okBtn.style.backgroundColor = '#ff5555';
            okBtn.style.color = '#fff';
        } else {
            okBtn.style.backgroundColor = '#5fe7ff';
            okBtn.style.color = '#000';
        }
        
        modal.style.display = 'flex';
        
        const cleanup = () => {
            modal.style.display = 'none';
            okBtn.removeEventListener('click', onOk);
            cancelBtn.removeEventListener('click', onCancel);
        };
        
        const onOk = () => {
            cleanup();
            resolve(true);
        };
        
        const onCancel = () => {
            cleanup();
            resolve(false);
        };
        
        okBtn.addEventListener('click', onOk);
        cancelBtn.addEventListener('click', onCancel);
        
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                onCancel();
            }
        });
    });
}

// 添加动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
`;
document.head.appendChild(style);