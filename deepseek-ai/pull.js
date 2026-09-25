// ============================================
// DeepSeek 对话导出脚本
// 用法：修改 CONVERSATION_TITLE 为你要导出的对话标题
// ============================================

const CONVERSATION_TITLE = '规则确认与执行';

(async () => {
    const dbRequest = indexedDB.open('deepseek-chat');
    
    dbRequest.onsuccess = (event) => {
        const db = event.target.result;
        const transaction = db.transaction(['history-message'], 'readonly');
        const store = transaction.objectStore('history-message');
        const getAllRequest = store.getAll();
        
        getAllRequest.onsuccess = () => {
            const allData = getAllRequest.result;
            
            // 列出所有对话，方便查找标题
            console.log('📋 所有对话:');
            allData.forEach(item => {
                const s = item.data?.chat_session;
                const msgCount = item.data?.chat_messages?.length || 0;
                console.log(`  [${msgCount}条] ${s?.title}`);
            });
            
            // 查找目标对话（模糊匹配）
            const target = allData.find(item => 
                item.data?.chat_session?.title === CONVERSATION_TITLE
            );
            
            if (!target) {
                console.log(`\n❌ 未找到标题为 "${CONVERSATION_TITLE}" 的对话`);
                return;
            }
            
            const msgs = target.data.chat_messages;
            console.log(`\n✅ 找到对话: ${target.data.chat_session.title}, 共 ${msgs.length} 条消息`);
            
            // 构建 childrenMap
            const childrenMap = {};
            msgs.forEach(m => {
                const pid = m.parent_id;
                if (!childrenMap[pid]) childrenMap[pid] = [];
                childrenMap[pid].push(m);
            });
            
            // 找所有根节点
            const roots = msgs.filter(m => m.parent_id === null);
            
            // 从每个根节点出发，找最长路径
            let globalLongestPath = [];
            
            for (const root of roots) {
                let longestPath = [];
                
                function dfs(node, currentPath) {
                    currentPath.push(node);
                    const children = childrenMap[node.message_id] || [];
                    
                    if (children.length === 0) {
                        if (currentPath.length > longestPath.length) {
                            longestPath = [...currentPath];
                        }
                    } else {
                        for (const child of children) {
                            dfs(child, currentPath);
                        }
                    }
                    currentPath.pop();
                }
                
                dfs(root, []);
                
                if (longestPath.length > globalLongestPath.length) {
                    globalLongestPath = longestPath;
                }
            }
            
            // 提取 content（只取 REQUEST 和 RESPONSE）
            const messages = [];
            globalLongestPath.forEach(msg => {
                const role = msg.role === 'USER' ? 'user' : 'assistant';
                (msg.fragments || []).forEach(f => {
                    if ((f.type === 'REQUEST' || f.type === 'RESPONSE') && f.content) {
                        messages.push({ role, content: f.content });
                    }
                });
            });
            
            // 下载
            const safeTitle = CONVERSATION_TITLE.replace(/[\\/:*?"<>|]/g, '_');
            const jsonStr = JSON.stringify(messages, null, 2);
            const blob = new Blob([jsonStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `deepseek_${safeTitle}.json`;
            a.click();
            
            console.log(`\n✅ 已下载: ${messages.length} 条消息`);
        };
    };
})();