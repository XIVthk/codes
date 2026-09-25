const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const stopGenerateBtn = document.getElementById('stopGenerateBtn');
const reasoningEffort = document.getElementById('reasoningEffort');
const newChatBtn = document.getElementById('newChatBtn');
const sessionList = document.getElementById('sessionList');
const clearChatBtn = document.getElementById('clearChatBtn');
const exportChatBtn = document.getElementById('exportChatBtn');
const importChatBtn = document.getElementById('importChatBtn');
const importFile = document.getElementById('importFile');
const menuBtn = document.getElementById('menuBtn');
const closeSidebar = document.getElementById('closeSidebar');
const sidebar = document.getElementById('sidebar');
const contextMenu = document.getElementById('contextMenu');
const chatTitle = document.getElementById('chatTitle');
const VISION_MODEL = 'deepseek-chat';

let currentSessionId = Date.now().toString();
let sessions = {};
let currentMessages = [];
let isWaitingForResponse = false;
let currentStreamController = null;
let currentContextMenuTarget = null;
let currentSystemPrompt = 'You are a helpful assistant. 请用中文回复。';
let messageJumpDropdown = null;
let reasoningDropdown = null;
let currentSearchResults = [];
let currentSearchIndex = -1;
let currentSearchKeyword = '';

function estimateTokens(textOrContent) {
    if (!textOrContent) return 0;

    // 如果是数组：多模态内容块
    if (Array.isArray(textOrContent)) {
        let sum = 0;
        for (const block of textOrContent) {
            if (!block) continue;
            if (block.type === "text") {
                const txt = block.text || '';
                const chineseChars = txt.match(/[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]/g) || [];
                const englishChars = txt.match(/[a-zA-Z0-9\u0020-\u007E]/g) || [];
                const otherChars = txt.length - chineseChars.length - englishChars.length;
                const chineseTokens = chineseChars.length * 0.6;
                const englishTokens = englishChars.length * 0.3;
                const otherTokens = otherChars * 0.5;
                sum += chineseTokens + englishTokens + otherTokens;
            } else if (block.type === "image_url") {
                // deepseek‑flash单张图片上限1024 token，强制转为数字，防止NaN
                sum += 1024;
            }
            // 其它未知type直接跳过，不加token
        }
        // 强制返回有效数字，防止NaN
        return Number.isFinite(sum) ? Math.round((sum * 100) / 100) : 0;
    }

    // 普通字符串模式（老会话兼容）
    const s = String(textOrContent ?? '');
    const chineseChars = s.match(/[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]/g) || [];
    const englishChars = s.match(/[a-zA-Z0-9\u0020-\u007E]/g) || [];
    const otherChars = s.length - chineseChars.length - englishChars.length;
    const chineseTokens = chineseChars.length * 0.6;
    const englishTokens = englishChars.length * 0.3;
    const otherTokens = otherChars * 0.5;
    const total = chineseTokens + englishTokens + otherTokens;

    return Number.isFinite(total) ? Math.round((total * 100) / 100) : 0;
}


function calculateTotalTokens() {
    let total = 0;
    for (const msg of currentMessages) {
        if (msg.content) total += estimateTokens(msg.content);
        if (msg.reasoning) total += estimateTokens(msg.reasoning);
        if (msg.attachments && msg.attachments.length) {
            for (const att of msg.attachments) {
                if (att.content) total += estimateTokens(att.content);
            }
        }
    }
    return total;
}

function updateTokenDisplay() {
    const tokenDisplay = document.getElementById('chatTokenDisplay');
    if (!tokenDisplay) return;
    const total = calculateTotalTokens();
    let color = 'var(--accent)';
    let percentage = (total / 1000000) * 100;
    if (percentage > 80) color = '#e86b6b';
    else if (percentage > 60) color = '#f0a35e';
    tokenDisplay.innerHTML = `📊 Token: ${total.toLocaleString()} / 1M (${percentage.toFixed(1)}%)`;
    tokenDisplay.style.color = color;
}

function enhanceCodeBlocks(container) {
    if (!container) return;
    container.querySelectorAll('pre').forEach(pre => {
        if (pre.querySelector('.code-block-header')) return;
        const code = pre.querySelector('code');
        if (!code) return;
        const className = code.className || '';
        const language = className.match(/language-(\w+)/)?.[1] || 'text';
        const header = document.createElement('div');
        header.className = 'code-block-header';
        header.innerHTML = `
            <span class="code-language">${escapeHtml(language)}</span>
            <button class="code-copy-btn" title="Copy code">Copy</button>
        `;
        const copyBtn = header.querySelector('.code-copy-btn');
        copyBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const codeText = code.textContent;
            try {
                await navigator.clipboard.writeText(codeText);
                copyBtn.innerHTML = '✅ Copied';
                setTimeout(() => { copyBtn.innerHTML = 'Copy'; }, 2000);
            } catch (err) {
                const textarea = document.createElement('textarea');
                textarea.value = codeText;
                textarea.style.position = 'fixed';
                textarea.style.opacity = '0';
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                copyBtn.innerHTML = '✅ Copied';
                setTimeout(() => { copyBtn.innerHTML = 'Copy'; }, 2000);
            }
        });
        pre.style.position = 'relative';
        pre.insertBefore(header, pre.firstChild);
    });
}

function renderSingleProgressBar(barText) {
    const match = barText.match(/;;; bar\s*(?:\[([^\]]*)\])?\s*(?:<(\d+)\/(\d+)>)?\s*(?:\{([^}]*)\})?/);
    if (!match) return barText;
    const [, name, current, maxVal, colors] = match;
    let bgColor = '#1a2035';
    let fgColor = '#3b9bc5';
    if (colors) {
        const parts = colors.split(',').map(c => c.trim());
        if (parts[0]) bgColor = parts[0];
        if (parts[1]) fgColor = parts[1];
    }
    const getLuminance = hex => {
        const rgb = parseInt(hex.slice(1), 16);
        const r = (rgb >> 16) & 0xff;
        const g = (rgb >> 8) & 0xff;
        const b = rgb & 0xff;
        return (r * 0.299 + g * 0.587 + b * 0.114) / 255;
    };
    const getContrast = hex => getLuminance(hex) > 0.5 ? '#1a1a2e' : '#ffffff';
    if (current && maxVal) {
        const currentNum = parseInt(current);
        const maxNum = parseInt(maxVal);
        let percent = (currentNum / maxNum) * 100;
        const isOver = currentNum > maxNum;
        const displayPercent = Math.min(percent, 100);
        const low = displayPercent < 30;
        const label = name ? `<div class="progress-label">${escapeHtml(name)}</div>` : '';
        let barHtml = '';
        if (low) {
            const textColor = getContrast(bgColor);
            barHtml = `
            <div class="progress-track" style="background-color: ${bgColor}; position: relative;">
                <div class="progress-fill" style="width: ${displayPercent}%; background-color: ${fgColor};"></div>
                <span class="progress-text-follow" style="position: absolute; left: calc(${displayPercent}% + 8px); top: 50%; transform: translateY(-50%); color: ${textColor};">${current}/${maxVal}${isOver ? ' 🔥' : ''}</span>
            </div>`;
        } else {
            const textColor = getContrast(fgColor);
            barHtml = `
            <div class="progress-track" style="background-color: ${bgColor};">
                <div class="progress-fill" style="width: ${displayPercent}%; background-color: ${fgColor}; display: flex; align-items: center; justify-content: flex-end;">
                    <span class="progress-text-inside" style="color: ${textColor};">${current}/${maxVal}${isOver ? ' !!!' : ''}</span>
                </div>
            </div>`;
        }
        if (isOver) {
            return `
            <div class="custom-progress-bar over-max">
                ${label}
                ${barHtml}
            </div>`;
        }
        return `
        <div class="custom-progress-bar">
            ${label}
            ${barHtml}
        </div>`;
    }
    if (name) {
        const color = getContrast(fgColor);
        return `<span class="progress-tag" style="background-color: ${fgColor}20; color: ${fgColor}; border-color: ${fgColor};">${escapeHtml(name)}</span>`;
    }
    return barText;
}

function renderValueBox(match) {
    const regex = /;;; val\s+\[([^\]]*)\]\s+\[([^\]]*)\]/;
    const parts = match.match(regex);
    if (!parts) return match;
    const title = parts[1] || '数值';
    const value = parts[2] || '0';
    return `
        <div class="value-box">
            <div class="value-number">${escapeHtml(value)}</div>
            <div class="value-title">${escapeHtml(title)}</div>
        </div>
    `;
}

function renderStatBox(match) {
    const regex = /;;; stat\s+\[([^\]]*)\]\s+\[([^\]]*)\]/;
    const parts = match.match(regex);
    if (!parts) return match;
    const title = parts[1] || 'Stat';
    const desc = parts[2] || '';
    let icon = '📌';
    return `
        <div class="stat-box">
            <div class="stat-icon">${icon}</div>
            <div class="stat-content">
                <div class="stat-title">${escapeHtml(title)}</div>
                ${desc ? `<div class="stat-desc">${escapeHtml(desc)}</div>` : ''}
            </div>
        </div>
    `;
}

class CustomSelect {
    constructor(wrapperId, onChange) {
        this.wrapper = document.getElementById(wrapperId);
        if (!this.wrapper) return;
        this.trigger = this.wrapper.querySelector('.custom-select-trigger');
        this.dropdown = this.wrapper.querySelector('.custom-select-dropdown');
        this.selectedText = this.trigger.querySelector('.custom-select-text');
        this.options = this.dropdown.querySelectorAll('.custom-select-option');
        this.onChange = onChange;
        this.isOpen = false;
        this.bindEvents();
        this.setInitialValue();
    }
    bindEvents() {
        this.trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggle();
        });
        this.options.forEach(opt => {
            opt.addEventListener('click', (e) => {
                e.stopPropagation();
                const value = opt.dataset.value;
                const text = opt.textContent;
                this.selectValue(value, text);
                this.close();
                if (this.onChange) this.onChange(value, text);
            });
        });
    }
    setInitialValue() {
        const selectedOpt = Array.from(this.options).find(opt => opt.dataset.selected === 'true');
        if (selectedOpt) {
            this.selectedText.textContent = selectedOpt.textContent;
        }
    }
    selectValue(value, text) {
        this.selectedText.textContent = text;
        this.options.forEach(opt => {
            opt.classList.remove('selected');
            if (opt.dataset.value === value) {
                opt.classList.add('selected');
                opt.dataset.selected = 'true';
            } else {
                opt.dataset.selected = 'false';
            }
        });
    }
    updateOptions(items, selectedValue) {
        this.dropdown.innerHTML = '';
        items.forEach(item => {
            const opt = document.createElement('div');
            opt.className = 'custom-select-option';
            if (item.value === selectedValue) opt.classList.add('selected');
            opt.dataset.value = item.value;
            opt.textContent = item.text;
            opt.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectValue(item.value, item.text);
                this.close();
                if (this.onChange) this.onChange(item.value, item.text);
            });
            this.dropdown.appendChild(opt);
        });
        this.options = this.dropdown.querySelectorAll('.custom-select-option');
        if (selectedValue !== undefined) {
            this.selectedText.textContent = this.getOptionText(selectedValue) || this.selectedText.textContent;
        }
    }
    getOptionText(value) {
        const opt = Array.from(this.options).find(o => o.dataset.value === value);
        return opt ? opt.textContent : null;
    }
    toggle() {
        if (this.isOpen) this.close();
        else this.open();
    }
    open() {
        document.querySelectorAll('.custom-select-wrapper.open').forEach(w => {
            if (w.id !== this.wrapper.id) w.classList.remove('open');
        });
        this.wrapper.classList.add('open');
        this.isOpen = true;
    }
    close() {
        this.wrapper.classList.remove('open');
        this.isOpen = false;
    }
}

function updateMessageJumpSelectCustom() {
    if (!messageJumpDropdown) return;
    if (currentMessages.length === 0) {
        messageJumpDropdown.updateOptions([{ value: '', text: '📜 跳转到消息...' }], '');
        return;
    }
    const messages = currentMessages.filter(msg => msg.role === 'user' || msg.role === 'assistant');
    const options = [{ value: '', text: '📜 跳转到消息...' }];
    messages.forEach((msg, displayIdx) => {
        const realIndex = currentMessages.findIndex(m => m === msg);
        if (realIndex === -1) return;
        let preview = '';
        if (Array.isArray(msg.content)) {
            const txtBlk = msg.content.find(b => b.type === 'text');
            preview = txtBlk ? txtBlk.text.replace(/\n/g, ' ').substring(0, 30) : '[图片消息]';
        } else {
            preview = msg.content.replace(/\n/g, ' ').substring(0, 30);
        }
        if (preview.length > 30) preview += '…';
        const roleIcon = msg.role === 'user' ? '👤' : '🤖';
        options.push({ value: realIndex.toString(), text: `${roleIcon} ${displayIdx + 1}. ${preview}` });
    });
    messageJumpDropdown.updateOptions(options, '');
}

function initCustomSelects() {
    reasoningDropdown = new CustomSelect('reasoningWrapper', (value, text) => {
        if (reasoningEffort) {
            reasoningEffort.value = value;
            localStorage.setItem('reasoningEffort', value);
        }
    });
    messageJumpDropdown = new CustomSelect('messageJumpWrapper', (value, text) => {
        if (!value) return;
        const targetIndex = parseInt(value);
        const targetElement = document.querySelector(`.message[data-index="${targetIndex}"]`);
        if (targetElement) {
            targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            targetElement.style.transition = 'background 0.3s';
            targetElement.style.background = 'rgba(59, 155, 197, 0.25)';
            targetElement.style.borderRadius = '12px';
            setTimeout(() => {
                targetElement.style.background = '';
                targetElement.style.borderRadius = '';
            }, 1500);
        }
        messageJumpDropdown.selectValue('', '📜 跳转到消息...');
    });
    updateMessageJumpSelectCustom();
}

function initChatSearch() {
    const searchBtn = document.getElementById('chatSearchBtn');
    const searchPanel = document.getElementById('chatSearchPanel');
    const searchInput = document.getElementById('chatSearchInput');
    const searchCount = document.getElementById('chatSearchCount');
    const searchPrev = document.getElementById('chatSearchPrev');
    const searchNext = document.getElementById('chatSearchNext');
    const searchClose = document.getElementById('chatSearchClose');
    if (!searchBtn) return;
    searchBtn.addEventListener('click', () => {
        const isVisible = searchPanel.style.display === 'flex';
        if (isVisible) {
            searchPanel.style.display = 'none';
            clearSearch();
        } else {
            searchPanel.style.display = 'flex';
            searchInput.focus();
            const selection = window.getSelection().toString();
            if (selection && selection.trim()) {
                searchInput.value = selection.trim();
                performSearch(selection.trim());
            }
        }
    });
    searchInput.addEventListener('input', (e) => {
        const keyword = e.target.value.trim();
        if (keyword.length >= 1) performSearch(keyword);
        else clearSearch();
    });
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && currentSearchResults.length > 0) {
            jumpToSearchResult(currentSearchIndex + 1);
        }
    });
    searchPrev.addEventListener('click', () => {
        if (currentSearchResults.length > 0) jumpToSearchResult(currentSearchIndex - 1);
    });
    searchNext.addEventListener('click', () => {
        if (currentSearchResults.length > 0) jumpToSearchResult(currentSearchIndex + 1);
    });
    searchClose.addEventListener('click', () => {
        searchPanel.style.display = 'none';
        clearSearch();
    });
    document.addEventListener('click', (e) => {
        if (searchPanel.style.display === 'flex' &&
            !searchPanel.contains(e.target) && e.target !== searchBtn) {
            searchPanel.style.display = 'none';
            clearSearch();
        }
    });
}

function performSearch(keyword) {
    currentSearchKeyword = keyword;
    currentSearchResults = [];
    currentSearchIndex = -1;
    clearSearchHighlights();
    if (!keyword || keyword.length === 0) {
        updateSearchCount();
        return;
    }
    const messages = document.querySelectorAll('.message');
    const lowerKeyword = keyword.toLowerCase();
    messages.forEach((msg, idx) => {
        const contentEl = msg.querySelector('.message-content');
        if (!contentEl) return;
        if (contentEl.textContent.toLowerCase().includes(lowerKeyword)) {
            currentSearchResults.push({ element: msg, index: idx });
            msg.classList.add('message-highlight');
        }
    });
    if (currentSearchResults.length > 0) {
        currentSearchIndex = 0;
        highlightCurrentResult();
    }
    updateSearchCount();
}

function highlightCurrentResult() {
    document.querySelectorAll('.message-current-highlight').forEach(el => {
        el.classList.remove('message-current-highlight');
    });
    if (currentSearchIndex >= 0 && currentSearchResults[currentSearchIndex]) {
        const result = currentSearchResults[currentSearchIndex];
        result.element.classList.add('message-current-highlight');
        result.element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function jumpToSearchResult(newIndex) {
    if (currentSearchResults.length === 0) return;
    if (newIndex < 0) newIndex = currentSearchResults.length - 1;
    else if (newIndex >= currentSearchResults.length) newIndex = 0;
    currentSearchIndex = newIndex;
    highlightCurrentResult();
    updateSearchCount();
}

function updateSearchCount() {
    const searchCount = document.getElementById('chatSearchCount');
    if (searchCount) {
        if (currentSearchResults.length > 0) {
            searchCount.textContent = `${currentSearchIndex + 1}/${currentSearchResults.length}`;
        } else if (currentSearchKeyword && currentSearchKeyword.length > 0) {
            searchCount.textContent = '0/0';
        } else {
            searchCount.textContent = '';
        }
    }
}

function clearSearch() {
    currentSearchResults = [];
    currentSearchIndex = -1;
    currentSearchKeyword = '';
    clearSearchHighlights();
    updateSearchCount();
}

function clearSearchHighlights() {
    document.querySelectorAll('.message-highlight').forEach(el => {
        el.classList.remove('message-highlight');
    });
    document.querySelectorAll('.message-current-highlight').forEach(el => {
        el.classList.remove('message-current-highlight');
    });
}

let pendingFiles = [];

function updatePendingFilesUI() {
    const area = document.getElementById('pendingFilesArea');
    const countSpan = document.getElementById('pendingFilesCount');
    const listContainer = document.getElementById('pendingFilesList');
    if (pendingFiles.length === 0) {
        if (area) area.style.display = 'none';
        return;
    }
    if (area) area.style.display = 'block';
    if (countSpan) countSpan.textContent = pendingFiles.length;
    if (listContainer) listContainer.innerHTML = '';
    pendingFiles.forEach((pf, idx) => {
        const fileDiv = document.createElement('div');
        fileDiv.className = 'pending-file-item';
        if (pf.isVision) {
            fileDiv.style.borderColor = 'var(--accent)';
            fileDiv.style.borderWidth = '2px';
        }
        fileDiv.setAttribute('data-idx', idx);
        fileDiv.innerHTML = `
            <span class="file-icon-small">${pf.isVision ? '🖼️' : getFileIcon(pf.file.name)}</span>
            <span class="file-name-small" title="${escapeHtml(pf.displayName || pf.file.name)}">${escapeHtml(pf.displayName || pf.file.name)}</span>
            <span class="file-size-small">${(pf.file.size / 1024).toFixed(1)} KB</span>
            ${pf.isVision ? '<span style="color: var(--accent); font-size: 0.6rem;">IMAGE</span>' : ''}
            <button class="remove-pending-file" data-idx="${idx}">✕</button>
        `;
        fileDiv.addEventListener('click', async (e) => {
            if (e.target.classList.contains('remove-pending-file')) return;
            if (!pf.isVision) {
                await showFilePreview(pf.file.name, pf.content);
            }
        });
        const removeBtn = fileDiv.querySelector('.remove-pending-file');
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            pendingFiles.splice(idx, 1);
            updatePendingFilesUI();
            showToast(`已移除 ${pf.displayName || pf.file.name}`);
        });
        if (listContainer) listContainer.appendChild(fileDiv);
    });
}

function getFileIcon(filename) {
    if (!filename || typeof filename !== 'string') return '📄';
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        js: '📜', py: '🐍', java: '☕', cpp: '⚙️', c: '⚙️',
        html: '🌐', css: '🎨', json: '📦', md: '📝', txt: '📄',
        png: '🖼️', jpg: '🖼️', jpeg: '🖼️', gif: '🖼️', svg: '🎨',
        pdf: '📕', zip: '📦', rar: '📦', exe: '⚡'
    };
    return icons[ext] || '📎';
}

function clearPendingFiles() {
    if (pendingFiles.length > 0) {
        pendingFiles = [];
        updatePendingFilesUI();
        showToast('已清空待发送文件');
    }
}

function prepareAttachments() {
    if (pendingFiles.length === 0) return [];
    const attachments = [];
    for (const pf of pendingFiles) {
        if (pf.isVision && pf.imageBlock) {
            attachments.push({
                isVision: true,
                imageBlock: structuredClone(pf.imageBlock),
                fileInfo: {
                    name: pf.displayName || pf.file.name,
                    size: pf.file.size,
                    type: pf.file.type
                }
            })
        } else {
            attachments.push({
                content: pf.content,
                fileInfo: {
                    name: pf.displayName || pf.file.name,
                    size: pf.file.size,
                    type: pf.file.type || 'text/plain'
                },
                isVision: false
            })
        }
    }
    pendingFiles = [];
    updatePendingFilesUI();
    return attachments;
}

function initDragAndDrop() {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;
    let dragCounter = 0;
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        document.body.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });
    messagesContainer.addEventListener('dragenter', (e) => {
        e.preventDefault();
        dragCounter++;
        messagesContainer.classList.add('drag-over');
    });
    messagesContainer.addEventListener('dragover', (e) => {
        e.preventDefault();
    });
    messagesContainer.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dragCounter--;
        if (dragCounter === 0) {
            messagesContainer.classList.remove('drag-over');
        }
    });
    messagesContainer.addEventListener('drop', async (e) => {
        e.preventDefault();
        dragCounter = 0;
        messagesContainer.classList.remove('drag-over');
        const items = e.dataTransfer.items;
        let isFolder = false;
        for (let i = 0; i < items.length; i++) {
            const entry = items[i].webkitGetAsEntry && items[i].webkitGetAsEntry();
            if (entry && entry.isDirectory) {
                isFolder = true;
                break;
            }
        }
        if (isFolder) {
            showToast('📁 暂不支持上传文件夹，请选择单个文件');
            return;
        }
        const files = Array.from(e.dataTransfer.files);
        if (files.length === 0) {
            showToast('请拖拽单个文件，不支持文件夹');
            return;
        }
        for (const file of files) {
            await addFileToPending(file);
        }
    });
}

async function addFileToPending(file) {
    if (pendingFiles.some(pf => pf.file.name === file.name && pf.file.size === file.size)) {
        showToast(`⚠️ ${file.name} 已经在待发送列表中`);
        return;
    }
    let content = '';
    const fileName = file.name;
    const fileExt = fileName.split('.').pop().toLowerCase();
    try {
        if (file.type.startsWith('text/') ||
            ['json', 'js', 'py', 'java', 'c', 'cpp', 'html', 'css', 'xml', 'md', 'txt', 'csv', 'log'].includes(fileExt)) {
            content = await file.text();
        } else if (file.type.startsWith('image/')) {
            const compressedFile = await compressImage(file, 1024, 0.7);
            const dataUrl = await new Promise((resolve) => {
                const reader = new FileReader();
                reader.onload = ev => resolve(ev.target.result);
                reader.readAsDataURL(compressedFile);
            });
            pendingFiles.push({
                file: compressedFile,
                isVision: true,
                displayName: file.name,
                imageBlock: {
                    "type": "image_url",
                    "image_url": {
                        "url": dataUrl,
                        "detail": "low"
                    }
                }
            });
            updatePendingFilesUI();
            showToast(`✅ 已添加图片 ${fileName}`);
            return;
        } else if (fileExt === 'docx') {
            if (typeof mammoth === 'undefined') {
                showToast('⚠️ 请刷新页面后重试（加载 Word 解析库）');
                return;
            }
            try {
                const arrayBuffer = await file.arrayBuffer();
                const result = await mammoth.extractRawText({ arrayBuffer: arrayBuffer });
                content = result.value;
                if (!content || content.trim() === '') {
                    content = `[Word 文件内容为空: ${fileName}]`;
                }
                if (result.messages && result.messages.length) {
                    console.warn('Word 解析警告:', result.messages);
                }
            } catch (e) {
                console.error('mammoth 解析失败:', e);
                content = `[无法解析的 Word 文件: ${fileName}，请确保文件未损坏]`;
            }
        } else {
            content = `[二进制文件: ${fileName}, 大小: ${(file.size / 1024).toFixed(2)} KB]\n\n如需分析此文件，请转换为纯文本格式后上传。`;
        }
        pendingFiles.push({ file, content });
        updatePendingFilesUI();
        showToast(`✅ 已添加 ${fileName}${fileExt === 'docx' ? ' (已提取文字)' : ''}`);
    } catch (error) {
        console.error('文件读取失败:', error);
        showToast(`❌ 读取失败: ${fileName}`);
    }
}

function getLanguageFromExt(ext) {
    const langMap = {
        js: 'javascript', py: 'python', java: 'java', c: 'c', cpp: 'cpp',
        html: 'html', css: 'css', json: 'json', md: 'markdown', txt: 'text',
        sh: 'bash', sql: 'sql', go: 'go', rs: 'rust', php: 'php',
        yaml: 'yaml', toml: 'toml', xml: 'xml', csv: 'csv', log: 'log'
    };
    return langMap[ext] || 'text';
}

async function showFilePreview(filename, rawContent) {
    if (!filename) {
        showToast('无法预览：文件名无效');
        return;
    }
    if (!rawContent || typeof rawContent !== 'string') {
        showToast('无法预览：文件内容为空');
        return;
    }
    return new Promise((resolve) => {
        const ext = filename.split('.').pop().toLowerCase();
        const language = getLanguageFromExt(ext);
        const lines = rawContent.split('\n');
        const lineCount = lines.length;
        const charCount = rawContent.length;
        const sizeKB = (rawContent.length / 1024).toFixed(1);
        let highlighted = rawContent;
        if (typeof hljs !== 'undefined' && language && hljs.getLanguage(language)) {
            try {
                highlighted = hljs.highlight(rawContent, { language }).value;
            } catch (e) {
                highlighted = rawContent.replace(/[&<>]/g, (m) => {
                    if (m === '&') return '&amp;';
                    if (m === '<') return '&lt;';
                    if (m === '>') return '&gt;';
                    return m;
                });
            }
        } else {
            highlighted = rawContent.replace(/[&<>]/g, (m) => {
                if (m === '&') return '&amp;';
                if (m === '<') return '&lt;';
                if (m === '>') return '&gt;';
                return m;
            });
        }
        const modal = document.createElement('div');
        modal.className = 'file-preview-modal';
        modal.innerHTML = `
            <div class="file-preview-container">
                <div class="file-preview-header">
                    <div class="file-preview-title">
                        <span class="file-preview-icon">${getFileIcon(filename)}</span>
                        <span class="file-preview-name">${escapeHtml(filename)}</span>
                        <span class="file-preview-lang">${language || 'text'}</span>
                    </div>
                    <button class="file-preview-close">&times;</button>
                </div>
                <div class="file-preview-stats">
                    <span>📄 ${lineCount} 行</span>
                    <span>📝 ${charCount.toLocaleString()} 字符</span>
                    <span>💾 ${sizeKB} KB</span>
                </div>
                <div class="file-preview-content">
                    <pre><code class="language-${language} hljs">${highlighted}</code></pre>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        const closeBtn = modal.querySelector('.file-preview-close');
        const onClose = () => {
            modal.remove();
            resolve();
        };
        closeBtn.addEventListener('click', onClose);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) onClose();
        });
        document.addEventListener('keydown', function onEsc(e) {
            if (e.key === 'Escape') {
                onClose();
                document.removeEventListener('keydown', onEsc);
            }
        });
    });
}

function showModal(message, title = '提示', showCancel = false, showInput = false, draftKey = null) {
    return new Promise((resolve) => {
        let savedDraft = null;
        if (draftKey) {
            savedDraft = sessionStorage.getItem(`edit_draft_${draftKey}`);
        }
        const initialContent = (savedDraft !== null && savedDraft !== undefined) ? savedDraft : message;
        const modal = document.createElement('div');
        modal.className = 'custom-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(8px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            animation: fadeIn 0.2s ease;
        `;
        modal.innerHTML = `
            <div class="custom-modal-content" style="
                background: var(--bg-secondary);
                border: 1px solid var(--border-color);
                border-radius: 20px;
                min-width: 400px;
                max-width: 600px;
                width: 90%;
                box-shadow: 0 20px 40px rgba(0,0,0,0.5);
                animation: slideIn 0.25s ease;
            ">
                <div class="custom-modal-header" style="
                    padding: 16px 20px;
                    border-bottom: 1px solid var(--border-color);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-weight: bold;
                ">
                    <span>${escapeHtml(title)}</span>
                    <button class="modal-close" style="
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                        color: var(--text-secondary);
                    ">&times;</button>
                </div>
                <div class="custom-modal-body" style="padding: 20px;">
                    ${showInput ? `<textarea id="modal-textarea" class="modal-input" style="
                        width: 100%;
                        padding: 12px;
                        background: var(--bg-primary);
                        border: 1px solid var(--border-color);
                        border-radius: 8px;
                        color: var(--text-primary);
                        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                        font-size: 13px;
                        resize: vertical;
                        min-height: 200px;
                        max-height: 60vh;
                        line-height: 1.5;
                    ">${escapeHtml(initialContent)}</textarea>` : `<p style="line-height: 1.6;">${escapeHtml(message)}</p>`}
                </div>
                <div class="custom-modal-footer" style="
                    padding: 16px 20px;
                    border-top: 1px solid var(--border-color);
                    display: flex;
                    justify-content: flex-end;
                    gap: 12px;
                ">
                    ${showCancel ? '<button class="modal-btn cancel" style="padding: 8px 20px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 10px; cursor: pointer; color: var(--text-primary);">取消</button>' : ''}
                    <button class="modal-btn confirm" style="padding: 8px 20px; background: var(--accent); border: none; border-radius: 10px; cursor: pointer; color: white;">确定</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        const textarea = modal.querySelector('#modal-textarea');
        const confirmBtn = modal.querySelector('.confirm');
        const cancelBtn = modal.querySelector('.cancel');
        const closeBtn = modal.querySelector('.modal-close');
        if (textarea && draftKey) {
            textarea.addEventListener('input', () => {
                const currentValue = textarea.value;
                if (currentValue) {
                    sessionStorage.setItem(`edit_draft_${draftKey}`, currentValue);
                }
            });
        }
        const removeModal = () => { modal.remove(); };
        const onConfirm = () => {
            const value = showInput ? textarea.value : message;
            if (draftKey) sessionStorage.removeItem(`edit_draft_${draftKey}`);
            removeModal();
            resolve(value);
        };
        const onCancel = () => {
            removeModal();
            resolve(showInput ? null : false);
        };
        confirmBtn.addEventListener('click', onConfirm);
        if (cancelBtn) cancelBtn.addEventListener('click', onCancel);
        if (closeBtn) closeBtn.addEventListener('click', onCancel);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) onCancel();
        });
        if (textarea) {
            textarea.focus();
            textarea.select();
        }
    });
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 80px;
        left: 50%;
        transform: translateX(-50%);
        background: var(--accent);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.8rem;
        z-index: 3000;
        animation: fadeInUp 0.3s ease;
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2000);
}

document.addEventListener('click', () => {
    if (messageJumpDropdown) messageJumpDropdown.close();
    if (reasoningDropdown) reasoningDropdown.close();
});

document.querySelectorAll('.config-header').forEach(header => {
    const targetId = header.dataset.target;
    const panel = document.getElementById(targetId);
    const group = header.parentElement;
    if (!panel) return;
    if (!group.classList.contains('collapsed')) {
        panel.style.maxHeight = 'none';
    } else {
        panel.style.maxHeight = '0';
    }
    header.addEventListener('click', () => {
        const isCollapsed = group.classList.contains('collapsed');
        if (isCollapsed) {
            group.classList.remove('collapsed');
            panel.style.maxHeight = 'none';
        } else {
            group.classList.add('collapsed');
            panel.style.maxHeight = '0';
        }
    });
    window.addEventListener('resize', () => {
        if (!group.classList.contains('collapsed')) {
            panel.style.maxHeight = 'none';
        }
    });
});

function createSystemPromptButton() {
    const systemPanel = document.getElementById('systemPanel');
    if (!systemPanel) return;
    const oldTextarea = document.getElementById('systemPrompt');
    if (oldTextarea) oldTextarea.style.display = 'none';
    const btn = document.createElement('button');
    btn.className = 'system-prompt-btn';
    btn.innerHTML = '✏️ 编辑 System Prompt';
    btn.style.cssText = `
        width: 100%;
        padding: 10px;
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
        cursor: pointer;
        font-size: 0.85rem;
        transition: all 0.2s;
        margin-top: 8px;
        margin-bottom: 4px;
    `;
    btn.addEventListener('click', async () => {
        const newValue = await showModal(currentSystemPrompt, '编辑 System Prompt', true, true);
        if (newValue !== null && newValue !== currentSystemPrompt) {
            currentSystemPrompt = newValue;
            localStorage.setItem('systemPrompt', currentSystemPrompt);
            showToast('System Prompt 已更新');
        }
    });
    btn.addEventListener('mouseenter', () => {
        btn.style.background = 'var(--accent)';
        btn.style.transform = 'translateY(-1px)';
    });
    btn.addEventListener('mouseleave', () => {
        btn.style.background = 'var(--bg-primary)';
        btn.style.transform = 'none';
    });
    systemPanel.appendChild(btn);
}

document.addEventListener('DOMContentLoaded', () => {
    loadSessionsFromStorage();
    loadSystemPromptFromStorage();
    loadReasoningFromStorage();
    createSystemPromptButton();
    initCustomSelects();
    initChatSearch();
    initDragAndDrop();
    if (Object.keys(sessions).length === 0) {
        createNewSession();
    } else {
        const lastId = localStorage.getItem('lastSessionId');
        if (lastId && sessions[lastId]) switchSession(lastId);
        else switchSession(Object.keys(sessions)[0]);
    }
    setupEventListeners();
    autoResizeTextarea();
});

function setupEventListeners() {
    sendBtn.addEventListener('click', sendMessage);
    if (stopGenerateBtn) stopGenerateBtn.addEventListener('click', stopGeneration);
    messageInput.addEventListener('keydown', (e) => {
        const isMobile = 'ontouchstart' in window;
        if (e.key === 'Enter') {
            if (isMobile) return;
            if (!e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        }
    });
    newChatBtn.addEventListener('click', createNewSession);
    clearChatBtn.addEventListener('click', async () => {
        if (await showModal('清空当前对话？', '确认', true)) clearCurrentChat();
    });
    exportChatBtn.addEventListener('click', exportChatHistory);
    importChatBtn.addEventListener('click', () => importFile.click());
    importFile.addEventListener('change', importChatHistory);
    menuBtn.addEventListener('click', () => sidebar.classList.add('open'));
    closeSidebar.addEventListener('click', () => sidebar.classList.remove('open'));
    document.addEventListener('click', () => contextMenu.style.display = 'none');
    document.querySelectorAll('.tool-btn').forEach(btn => {
        if (btn.id === 'stopGenerateBtn') return;
        btn.addEventListener('click', () => {
            const tool = btn.dataset.tool;
            const commands = { 'search_web': '🔍 帮我搜索：', 'read_link': '🔗 帮我阅读这个链接：' };
            messageInput.value = commands[tool] || '';
            messageInput.focus();
            autoResizeTextarea();
        });
    });
    const clearPendingBtn = document.getElementById('clearPendingFilesBtn');
    if (clearPendingBtn) {
        clearPendingBtn.addEventListener('click', () => {
            if (pendingFiles.length > 0) {
                clearPendingFiles();
            }
        });
    }
    const mobileUploadBtn = document.getElementById('mobileUploadBtn');
    const mobileFileInput = document.getElementById('mobileFileInput');
    if (mobileUploadBtn && mobileFileInput) {
        mobileUploadBtn.addEventListener('click', () => {
            mobileFileInput.click();
        });
        mobileFileInput.addEventListener('change', async (e) => {
            const files = Array.from(e.target.files);
            for (const file of files) {
                await addFileToPending(file);
            }
            mobileFileInput.value = '';
        });
    }
    const visionUploadBtn = document.getElementById('visionUploadBtn');
    const visionFileInput = document.getElementById('visionFileInput');
    if (visionUploadBtn && visionFileInput) {
        visionUploadBtn.addEventListener('click', () => {
            visionFileInput.click();
        });
        visionFileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            if (!file.type.startsWith('image/')) {
                showToast('⚠️ 请选择图片文件');
                visionFileInput.value = '';
                return;
            }
            try {
                const compressedFile = await compressImage(file, 1024, 0.7);
                const dataUrl = await new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onload = ev => resolve(ev.target.result);
                    reader.readAsDataURL(compressedFile);
                });
                pendingFiles.push({
                    file: compressedFile,
                    isVision: true,
                    displayName: file.name,
                    imageBlock: {
                        "type": "image_url",
                        "image_url": {
                            "url": dataUrl,
                            "detail": "low"
                        }
                    }
                });
                updatePendingFilesUI();
                showToast(`✅ 图片 ${file.name} 已加入待发送列表，发送后模型可查看原图`);
            } catch (err) {
                showToast('❌ 图片处理失败');
                console.error(err);
            }
            visionFileInput.value = '';
        });
    }
}

function autoResizeTextarea() {
    const textarea = messageInput;
    textarea.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    });
}

function loadSessionsFromStorage() {
    const stored = localStorage.getItem('deepseek_sessions_v2');
    if (stored) {
        sessions = JSON.parse(stored);
        Object.values(sessions).forEach(session => {
            if (session.manualRename === undefined) session.manualRename = false;
        });
    } else {
        sessions = {};
    }
}

function saveSessionsToStorage() {
    localStorage.setItem('deepseek_sessions_v2', JSON.stringify(sessions));
    localStorage.setItem('lastSessionId', currentSessionId);
}

function createNewSession() {
    const newId = Date.now().toString();
    sessions[newId] = {
        id: newId,
        title: '新对话',
        messages: [],
        pinned: false,
        manualRename: false,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
    };
    saveSessionsToStorage();
    switchSession(newId);
    renderSessionList();
}

function switchSession(sessionId) {
    if (!sessions[sessionId]) return;
    if (isWaitingForResponse) stopGeneration();
    currentSessionId = sessionId;
    currentMessages = sessions[sessionId].messages || [];
    updateChatTitle();
    renderMessages();
    renderSessionList();
    saveSessionsToStorage();
    updateMessageJumpSelectCustom();
    updateTokenDisplay();
}

function updateChatTitle() {
    chatTitle.textContent = sessions[currentSessionId]?.title || '新对话';
}

function renderSessionList() {
    sessionList.innerHTML = '';
    const sorted = Object.values(sessions).sort((a, b) => {
        if (a.pinned && !b.pinned) return -1;
        if (!a.pinned && b.pinned) return 1;
        return new Date(b.updatedAt) - new Date(a.updatedAt);
    });
    sorted.forEach(session => {
        const div = document.createElement('div');
        div.className = `session-item ${session.id === currentSessionId ? 'active' : ''} ${session.pinned ? 'pinned' : ''}`;
        div.innerHTML = `
            <div class="session-title">${session.pinned ? '📌 ' : ''}${escapeHtml(session.title || '新对话')}</div>
            <div class="session-time">${formatRelativeTime(session.updatedAt)}</div>
        `;
        div.addEventListener('click', () => switchSession(session.id));
        div.addEventListener('contextmenu', async (e) => {
            e.preventDefault();
            const action = await showSessionMenu(session);
            if (action === 'delete') {
                if (await showModal(`删除对话 "${session.title}"？`, '确认', true)) {
                    delete sessions[session.id];
                    saveSessionsToStorage();
                    if (session.id === currentSessionId) {
                        const remaining = Object.keys(sessions);
                        remaining.length ? switchSession(remaining[0]) : createNewSession();
                    }
                    renderSessionList();
                }
            } else if (action === 'pin') {
                sessions[session.id].pinned = !sessions[session.id].pinned;
                saveSessionsToStorage();
                renderSessionList();
            } else if (action === 'rename') {
                const newName = await showModal(session.title, '重命名', true, true);
                if (newName && newName.trim()) {
                    sessions[session.id].title = newName.trim();
                    sessions[session.id].manualRename = true;
                    saveSessionsToStorage();
                    renderSessionList();
                    if (session.id === currentSessionId) updateChatTitle();
                }
            }
        });
        sessionList.appendChild(div);
    });
}

function showSessionMenu(session) {
    return new Promise((resolve) => {
        const menu = document.createElement('div');
        menu.className = 'session-context-menu';
        menu.style.cssText = `
            position: fixed;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
            z-index: 2000;
            min-width: 140px;
            backdrop-filter: blur(12px);
        `;
        menu.innerHTML = `
            <div class="session-menu-item" data-action="rename" style="padding: 10px 16px; cursor: pointer;">✏️ 重命名</div>
            <div class="session-menu-item" data-action="pin" style="padding: 10px 16px; cursor: pointer;">${session.pinned ? '📌 取消置顶' : '📌 置顶'}</div>
            <div class="session-menu-item" data-action="delete" style="padding: 10px 16px; cursor: pointer;">🗑️ 删除</div>
        `;
        document.body.appendChild(menu);
        const rect = event.target.getBoundingClientRect();
        let left = rect.left;
        if (left + 160 > window.innerWidth) left = window.innerWidth - 160;
        menu.style.left = left + 'px';
        menu.style.top = rect.bottom + 4 + 'px';
        const onAction = (e) => {
            const action = e.currentTarget.dataset.action;
            menu.remove();
            resolve(action);
        };
        menu.querySelectorAll('.session-menu-item').forEach(item => {
            item.addEventListener('click', onAction);
        });
        document.addEventListener('click', () => menu.remove(), { once: true });
    });
}

function formatRelativeTime(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diffMins = Math.floor((now - date) / 60000);
    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}小时前`;
    return `${date.getMonth()+1}/${date.getDate()}`;
}

function updateCurrentSessionTitle() {
    const session = sessions[currentSessionId];
    if (currentMessages.length > 0 && !session.manualRename) {
        const firstUser = currentMessages.find(m => m.role === 'user');
        if (firstUser) {
            let title = '';
            if(Array.isArray(firstUser.content)){
                const txtBlk = firstUser.content.find(b=>b.type==='text');
                title = txtBlk ? txtBlk.text.slice(0,25) : '[图片消息]';
            }else{
                title = firstUser.content.slice(0,25);
            }
            if (title.length > 25) title += '...';
            session.title = title;
        }
    } else if (currentMessages.length === 0 && !session.manualRename) {
        session.title = '新对话';
    }
    session.updatedAt = new Date().toISOString();
    session.messages = currentMessages;
    saveSessionsToStorage();
    renderSessionList();
    updateChatTitle();
}

function clearCurrentChat() {
    currentMessages = [];
    sessions[currentSessionId].messages = [];
    sessions[currentSessionId].title = '新对话';
    updateCurrentSessionTitle();
    renderMessages();
    updateMessageJumpSelectCustom();
    updateTokenDisplay();
}

function renderMessages() {
    if (currentMessages.length === 0) {
        chatMessages.innerHTML = `<div class="welcome-message"><h2>DeepSeek AI</h2><p>支持联网搜索和阅读链接 | 右键菜单可编辑消息 | 拖拽文件/图片上传，原生多模态</p></div>`;
        updateMessageJumpSelectCustom();
        updateTokenDisplay();
        return;
    }
    chatMessages.innerHTML = '';
    for (let i = 0; i < currentMessages.length; i++) {
        const msg = currentMessages[i];
        if (msg.role === 'user') {
            chatMessages.appendChild(createMessageElement(msg, i, 'user'));
        } else if (msg.role === 'assistant') {
            if (msg.reasoning && msg.reasoning.trim()) {
                chatMessages.appendChild(createReasoningElement(msg.reasoning, i));
            }
            chatMessages.appendChild(createMessageElement(msg, i, 'assistant'));
            if (msg.tool_calls && msg.tool_calls.length > 0) {
                chatMessages.appendChild(createToolInfoButton(msg.tool_calls, msg.tool_results));
            }
        }
    }
    chatMessages.scrollTop = chatMessages.scrollHeight;
    updateMessageJumpSelectCustom();
    setTimeout(() => enhanceCodeBlocks(chatMessages), 100);
    updateTokenDisplay();
}

function createToolInfoButton(toolCalls, toolResults) {
    const div = document.createElement('div');
    div.className = 'tool-info-button';
    div.style.cssText = `margin: 4px 0 8px 0; padding: 0;`;
    const btn = document.createElement('button');
    btn.style.cssText = `
        background: rgba(59, 155, 197, 0.15);
        border: 1px solid var(--accent);
        border-radius: 16px;
        padding: 4px 12px;
        font-size: 0.7rem;
        color: var(--accent);
        cursor: pointer;
        transition: all 0.2s;
    `;
    btn.innerHTML = `🔧 工具调用 (${toolCalls.length})`;
    const resultPanel = document.createElement('div');
    resultPanel.style.cssText = `
        display: none;
        margin-top: 8px;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 8px;
        padding: 10px;
        font-size: 0.75rem;
        font-family: monospace;
        max-height: 300px;
        overflow-y: auto;
    `;
    let resultsHtml = '<strong>📋 工具调用详情</strong><br><br>';
    toolCalls.forEach((call, idx) => {
        const query = call.query || call.arguments?.query || call.arguments?.url || '未知';
        resultsHtml += `<div style="margin-bottom: 10px; border-left: 2px solid var(--accent); padding-left: 8px;">`;
        resultsHtml += `<strong>🔧 ${call.tool || call.name}</strong><br>`;
        resultsHtml += `<span style="color: #8a9bb5;">📌 关键词: ${escapeHtml(query)}</span><br>`;
        if (toolResults && toolResults[idx]) {
            const resultPreview = toolResults[idx].substring(0, 500);
            const sizeKB = Math.ceil(toolResults[idx].length / 1000);
            resultsHtml += `<details><summary>📄 查看结果 (${sizeKB}KB)</summary>`;
            resultsHtml += `<pre style="white-space: pre-wrap; margin-top: 8px; font-size: 0.7rem;">${escapeHtml(resultPreview)}${toolResults[idx].length > 500 ? '...' : ''}</pre>`;
            resultsHtml += `</details>`;
        }
        resultsHtml += `</div>`;
    });
    resultPanel.innerHTML = resultsHtml;
    btn.addEventListener('click', () => {
        if (resultPanel.style.display === 'none') {
            resultPanel.style.display = 'block';
            btn.style.background = 'rgba(59, 155, 197, 0.3)';
        } else {
            resultPanel.style.display = 'none';
            btn.style.background = 'rgba(59, 155, 197, 0.15)';
        }
    });
    div.appendChild(btn);
    div.appendChild(resultPanel);
    return div;
}

function createMessageElement(message, index, role) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.dataset.index = index;
    if (role === 'user' && message.attachments && message.attachments.length > 0) {
        const attachmentsDiv = document.createElement('div');
        attachmentsDiv.className = 'message-attachments';
        attachmentsDiv.innerHTML = `
            <div class="attachments-header">📎 附件 (${message.attachments.length})</div>
            <div class="attachments-list"></div>
        `;
        const listContainer = attachmentsDiv.querySelector('.attachments-list');
        message.attachments.forEach((att, attIdx) => {
            const item = document.createElement('div');
            item.className = 'attachment-item';
            let fileName = '';
            let fileSize = 0;
            if (att.file && att.file.name) {
                fileName = att.file.name;
                fileSize = att.file.size;
            } else if (att.fileInfo && att.fileInfo.name) {
                fileName = att.fileInfo.name;
                fileSize = att.fileInfo.size;
            } else {
                fileName = '未知文件';
            }
            const sizeKB = (fileSize / 1024).toFixed(1);
            item.innerHTML = `
                <span class="attachment-icon">${getFileIcon(fileName)}</span>
                <span class="attachment-name">${escapeHtml(fileName)}</span>
                <span class="attachment-size">${sizeKB} KB</span>
            `;
            item.originalContent = att.content;
            item.addEventListener('click', async (e) => {
                e.stopPropagation();
                if(!att.isVision && att.content){
                    await showFilePreview(fileName, att.content);
                }
            });
            listContainer.appendChild(item);
        });
        div.appendChild(attachmentsDiv);
    }
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    const content = document.createElement('div');
    content.className = 'message-content';

    if (Array.isArray(message.content)) {
        for (const block of message.content) {
            if (block.type === "text") {
                const textWrapper = document.createElement('div');
                if (typeof marked !== 'undefined') {
                    textWrapper.innerHTML = marked.parse(block.text, { breaks: true, gfm: true });
                } else {
                    textWrapper.innerHTML = escapeHtml(block.text).replace(/\n/g, '<br>');
                }
                content.appendChild(textWrapper);
            } else if (block.type === "image_url") {
                const img = document.createElement('img');
                img.src = block.image_url.url;
                img.style.maxWidth = "100%";
                img.style.borderRadius = "8px";
                img.style.margin = "8px 0";
                img.alt = "user uploaded image";
                content.appendChild(img);
            }
        }
    } else {
        if (role === 'assistant' && typeof marked !== 'undefined') {
            let processed = message.content;
            const htmlBlockRegex = /\[render_html\]([\s\S]*?)\[\/render_html\]/gi;
            const htmlBlocks = [];
            let processedWithPlaceholders = processed;
            let idx = 0;
            processedWithPlaceholders = processedWithPlaceholders.replace(htmlBlockRegex, (fullMatch, c) => {
                const ph = `%%HTML_BLOCK_${idx}%%`;
                htmlBlocks.push({ placeholder: ph, content: c.trim() });
                idx++;
                return ph;
            });
            const progressBars = [];
            const progressPattern = /;;; bar\s*(?:\[([^\]]*)\])?\s*(?:<(\d+)\/(\d+)>)?\s*(?:\{([^}]*)\})?/g;
            let processedWithoutProgress = processedWithPlaceholders.replace(progressPattern, (m) => {
                const pIdx = progressBars.length;
                progressBars.push(m);
                return `%%PROGRESS_${pIdx}%%`;
            });
            let html = marked.parse(processedWithoutProgress, { breaks: true, gfm: true });
            progressBars.forEach((bar, pIdx) => {
                const barHtml = renderSingleProgressBar(bar);
                html = html.replace(`%%PROGRESS_${pIdx}%%`, barHtml);
            });
            const valueRegex = /;;; val\s+\[([^\]]*)\]\s+\[([^\]]*)\]/g;
            html = html.replace(valueRegex, (m) => renderValueBox(m));
            const statRegex = /;;; stat\s+\[([^\]]*)\]\s+\[([^\]]*)\]/g;
            html = html.replace(statRegex, (m) => renderStatBox(m));
            htmlBlocks.forEach(block => {
                const safeHTML = sanitizeHTML(block.content);
                html = html.replace(block.placeholder, safeHTML);
            });
            content.innerHTML = html;
            content.querySelectorAll('pre code').forEach(block => hljs?.highlightElement(block));
        } else {
            content.innerHTML = escapeHtml(message.content).replace(/\n/g, '<br>');
        }
    }
    bubble.appendChild(content);
    div.appendChild(bubble);
    const actionBar = document.createElement('div');
    actionBar.className = 'message-action-bar';
    let estimatedTokens = estimateTokens(message.content);
    if (role === 'assistant' && message.reasoning) {
        estimatedTokens += estimateTokens(message.reasoning);
    }
    if (role === 'user' && message.attachments && message.attachments.length > 0) {
        for (const att of message.attachments) {
            if (att.content) {
                estimatedTokens += estimateTokens(att.content);
            }
        }
    }
    const timeStr = message.timestamp ? new Date(message.timestamp).toLocaleTimeString() : '';
    actionBar.innerHTML = `
        <button class="action-btn copy-btn" title="Copy">Copy</button>
        <button class="action-btn edit-btn" title="Edit">Edit</button>
        <button class="action-btn retry-btn" title="Regenerate">Regenerate</button>
        <span class="token-count" title="Token">Token: ${Math.round(estimatedTokens)}</span>
        ${timeStr ? `<span class="message-time"> ${timeStr}</span>` : ''}
    `;
    const copyBtn = actionBar.querySelector('.copy-btn');
    const editBtn = actionBar.querySelector('.edit-btn');
    const retryBtn = actionBar.querySelector('.retry-btn');
    if (role === 'user') retryBtn.style.display = 'none';
    copyBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        let text = '';
        if(Array.isArray(message.content)){
            const txtBlocks = message.content.filter(b=>b.type==="text");
            text = txtBlocks.map(b=>b.text).join('\n');
        }else{
            text = message.content;
        }
        try {
            await navigator.clipboard.writeText(text);
            showToast('✅ Copied');
            copyBtn.innerHTML = '✅ Copied';
            setTimeout(() => { copyBtn.innerHTML = 'Copy'; }, 2000);
        } catch (err) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            showToast('✅ Copied');
            copyBtn.innerHTML = '✅ Copied';
            setTimeout(() => { copyBtn.innerHTML = 'Copy'; }, 2000);
        }
    });
    editBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (role === 'user') editUserMessage(index);
        else editAIMessage(index);
    });
    retryBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (role === 'assistant') regenerateResponse(index);
    });
    div.appendChild(actionBar);
    div.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        showContextMenu(e);
    });
    if (role === 'user') div.addEventListener('dblclick', () => editUserMessage(index));
    else div.addEventListener('dblclick', () => editAIMessage(index));
    return div;
}

function createReasoningElement(reasoning, msgIndex) {
    const div = document.createElement('div');
    div.className = 'reasoning-bubble';
    div.setAttribute('data-reasoning-idx', msgIndex);
    const header = document.createElement('div');
    header.className = 'reasoning-header';
    header.innerHTML = '🧠 Thinking <span class="reasoning-toggle">v</span>';
    const content = document.createElement('div');
    content.className = 'reasoning-content';
    content.textContent = reasoning;
    content.style.overflowY = 'auto';
    content.style.maxHeight = '300px';
    let collapsed = false;
    const toggleSpan = header.querySelector('.reasoning-toggle');
    header.addEventListener('click', () => {
        collapsed = !collapsed;
        if (collapsed) {
            content.classList.add('collapsed');
            toggleSpan.classList.add('rotated');
            content.style.maxHeight = '';
        } else {
            content.classList.remove('collapsed');
            toggleSpan.classList.remove('rotated');
            content.style.maxHeight = '300px';
            content.scrollTop = content.scrollHeight;
        }
    });
    div.appendChild(header);
    div.appendChild(content);
    return div;
}

let currentToolStatusDiv = null;
function createToolStatusBar(toolName, query) {
    removeToolStatusBar();
    const div = document.createElement('div');
    div.id = 'tool-status-bar';
    div.style.cssText = `
        margin: 4px 0 8px 0;
        padding: 6px 12px;
        background: rgba(59, 155, 197, 0.1);
        border-left: 3px solid var(--accent);
        border-radius: 8px;
        font-size: 0.75rem;
        color: var(--text-secondary);
        display: flex;
        align-items: center;
        gap: 8px;
        animation: fadeIn 0.3s ease;
    `;
    div.innerHTML = `
        <span style="display: inline-block; width: 16px; height: 16px; border: 2px solid var(--accent); border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite;"></span>
        <span>🔧 正在调用 ${toolName === 'search_web' ? '搜索' : '阅读链接'}</span>
        <span style="color: var(--accent);">「${escapeHtml(query.substring(0, 50))}${query.length > 50 ? '...' : ''}」</span>
    `;
    if (!document.querySelector('#tool-status-style')) {
        const style = document.createElement('style');
        style.id = 'tool-status-style';
        style.textContent = `@keyframes spin { to { transform: rotate(360deg); } }`;
        document.head.appendChild(style);
    }
    const messagesContainer = document.querySelector('.chat-messages');
    if (messagesContainer) {
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    currentToolStatusDiv = div;
    return div;
}
function updateToolStatusBar(toolName, query, isExecuting = true) {
    const bar = document.getElementById('tool-status-bar');
    if (bar) {
        if (isExecuting) {
            bar.innerHTML = `
                <span style="display: inline-block; width: 16px; height: 16px; border: 2px solid var(--accent); border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite;"></span>
                <span>🔧 正在执行 ${toolName === 'search_web' ? '搜索' : '阅读'}</span>
                <span style="color: var(--accent);">「${escapeHtml(query.substring(0, 50))}${query.length > 50 ? '...' : ''}」</span>
            `;
        } else {
            bar.innerHTML = `
                <span>✅ 工具执行完成</span>
                <span style="color: var(--text-secondary);">${toolName === 'search_web' ? '搜索' : '阅读'}: ${escapeHtml(query.substring(0, 50))}${query.length > 50 ? '...' : ''}</span>
            `;
            setTimeout(() => {
                if (bar.parentNode) bar.style.opacity = '0.5';
                setTimeout(() => {
                    if (bar.parentNode) bar.remove();
                }, 1000);
            }, 2000);
        }
    }
}
function removeToolStatusBar() {
    const existing = document.getElementById('tool-status-bar');
    if (existing) existing.remove();
    currentToolStatusDiv = null;
}

// ========== 右键菜单 ==========
function showContextMenu(e) {
    e.preventDefault();
    const targetMessage = e.target.closest('.message');
    if (!targetMessage) return;
    const rawIndex = targetMessage.dataset.index;
    if (rawIndex === undefined) return;
    const actualIndex = parseInt(rawIndex);
    if (isNaN(actualIndex) || actualIndex >= currentMessages.length) return;
    const actualMessage = currentMessages[actualIndex];
    if (!actualMessage) return;
    currentContextMenuTarget = { index: actualIndex, message: actualMessage };
    contextMenu.style.display = 'block';
    let left = e.pageX;
    if (left + 160 > window.innerWidth) left = window.innerWidth - 160;
    contextMenu.style.left = left + 'px';
    contextMenu.style.top = e.pageY + 'px';
    const actions = ['edit_user', 'edit_ai', 'regenerate', 'delete', 'copy'];
    actions.forEach(action => {
        const item = contextMenu.querySelector(`[data-action="${action}"]`);
        if (item) {
            if (action === 'edit_user') item.style.display = actualMessage.role === 'user' ? 'block' : 'none';
            else if (action === 'edit_ai') item.style.display = actualMessage.role === 'assistant' ? 'block' : 'none';
            else if (action === 'regenerate') item.style.display = actualMessage.role === 'assistant' ? 'block' : 'none';
            else item.style.display = 'block';
        }
    });
}
async function handleContextMenuAction(action) {
    if (!currentContextMenuTarget) return;
    const { index, message } = currentContextMenuTarget;
    if (action === 'edit_user') editUserMessage(index);
    else if (action === 'edit_ai') editAIMessage(index);
    else if (action === 'regenerate') regenerateResponse(index);
    else if (action === 'delete') deleteMessage(index);
    else if (action === 'copy') {
        let text = '';
        if(Array.isArray(message.content)){
            const txtBlocks = message.content.filter(b=>b.type==="text");
            text = txtBlocks.map(b=>b.text).join('\n');
        }else{
            text = message.content;
        }
        try {
            await navigator.clipboard.writeText(text);
            showToast('✅ 已复制到剪贴板');
        } catch (err) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            showToast('✅ 已复制到剪贴板');
        }
    }
}
if (contextMenu) {
    contextMenu.querySelectorAll('.menu-item').forEach(item => {
        item.addEventListener('click', () => {
            handleContextMenuAction(item.dataset.action);
            contextMenu.style.display = 'none';
        });
    });
}

// ========== 编辑消息 ==========
async function editUserMessage(index) {
    const msg = currentMessages[index];
    if (msg.role !== 'user') return;
    const draftKey = `user_${currentSessionId}_${index}`;
    let originText = '';
    if(Array.isArray(msg.content)){
        const tb = msg.content.find(b=>b.type==="text");
        originText = tb ? tb.text : '';
    }else{
        originText = msg.content;
    }
    const newContent = await showModal(originText, '编辑用户消息', true, true, draftKey);
    if (!newContent || newContent === originText) return;
    sessionStorage.removeItem(`edit_draft_${draftKey}`);

    currentMessages = currentMessages.slice(0, index);
    const attachments = msg.attachments || [];
    let multiContent = [];
    if(newContent.trim()){
        multiContent.push({"type":"text","text": newContent});
    }
    // 保留原消息中的image_url图片块
    if(Array.isArray(msg.content)){
        const imageBlocks = msg.content.filter(b=>b.type==="image_url");
        multiContent.push(...structuredClone(imageBlocks));
    }

    let apiUserContent;
    if(multiContent.length ===1 && multiContent[0].type==="text"){
        apiUserContent = multiContent[0].text;
    }else{
        apiUserContent = multiContent;
    }

    const newUserMsg = {
        role: 'user',
        content: multiContent,
        timestamp: new Date().toISOString(),
        attachments: attachments
    };
    currentMessages.push(newUserMsg);
    updateCurrentSessionTitle();
    renderMessages();

    const apiMessages = currentMessages.slice(0, currentMessages.length - 1).map(m => ({ role: m.role, content: m.content }));
    apiMessages.push({ role: 'user', content: apiUserContent });
    await callStreamAPIWithCustomMessages(apiMessages, currentMessages.length - 1);
}

async function editAIMessage(index) {
    const msg = currentMessages[index];
    if (msg.role !== 'assistant') return;
    const draftKey = `ai_${currentSessionId}_${index}`;
    const newContent = await showModal(msg.content, '编辑AI回复', true, true, draftKey);
    if (newContent && newContent !== msg.content) {
        sessionStorage.removeItem(`edit_draft_${draftKey}`);
        currentMessages[index].content = newContent;
        currentMessages[index].timestamp = new Date().toISOString();
        updateCurrentSessionTitle();
        renderMessages();
        showToast('已修改本地消息');
    }
}

async function regenerateResponse(assistantIndex) {
    let userIndex = assistantIndex - 1;
    while (userIndex >= 0 && currentMessages[userIndex].role !== 'user') userIndex--;
    if (userIndex < 0) return;
    const userMsg = currentMessages[userIndex];
    const attachments = userMsg.attachments || [];
    currentMessages = currentMessages.slice(0, userIndex + 1);
    updateCurrentSessionTitle();
    renderMessages();
    await new Promise(resolve => setTimeout(resolve, 50));

    let apiUserContent;
    if(Array.isArray(userMsg.content)){
        apiUserContent = structuredClone(userMsg.content);
    }else{
        apiUserContent = userMsg.content;
    }

    const apiMessages = currentMessages.slice(0, currentMessages.length -1).map(m => ({role:m.role, content:m.content}));
    apiMessages.push({role:"user", content: apiUserContent});
    await callStreamAPIWithCustomMessages(apiMessages, currentMessages.length - 1);
}

async function deleteMessage(index) {
    if (await showModal('删除这条消息？', '确认', true)) {
        currentMessages.splice(index, 1);
        updateCurrentSessionTitle();
        renderMessages();
        updateTokenDisplay();
    }
}

// ========== 发送消息 ==========
async function sendMessage() {
    let userInput = messageInput.value.trim();
    if ((!userInput || userInput === '') && pendingFiles.length === 0) return;
    if (isWaitingForResponse) return;
    const attachments = prepareAttachments();
    messageInput.value = '';
    messageInput.style.height = 'auto';

    //组装多模态content
    let multiContent = [];
    if(userInput.trim()){
        multiContent.push({"type":"text","text": userInput});
    }
    for(const att of attachments){
        if(att.isVision && att.imageBlock){
            multiContent.push(structuredClone(att.imageBlock));
        }else if(!att.isVision){
            const ext = att.fileInfo.name.split('.').pop().toLowerCase() || 'txt';
            const fileText = `\n\n📎 文件: ${att.fileInfo.name}\n\`\`\`${ext}\n${att.content}\n\`\`\``;
            if(multiContent.length>0 && multiContent[multiContent.length-1].type === "text"){
                multiContent[multiContent.length-1].text += fileText;
            }else{
                multiContent.push({"type":"text","text": fileText});
            }
        }
    }

    let apiUserContent;
    if(multiContent.length === 1 && multiContent[0].type === "text"){
        apiUserContent = multiContent[0].text;
    }else{
        apiUserContent = multiContent;
    }

    const userMsg = {
        role: 'user',
        content: multiContent,
        attachments: attachments,
        timestamp: new Date().toISOString()
    };
    currentMessages.push(userMsg);
    updateCurrentSessionTitle();
    renderMessages();

    const apiMessages = currentMessages.slice(0, currentMessages.length -1).map(m=>{
        return {role: m.role, content: m.content};
    });
    apiMessages.push({
        role:"user",
        content: apiUserContent
    });
    await callStreamAPIWithCustomMessages(apiMessages, currentMessages.length - 1);
}

// ========== 核心 API 请求函数 ==========
async function callStreamAPIWithCustomMessages(apiMessages, userMsgIndex) {
    isWaitingForResponse = true;
    sendBtn.disabled = true;
    if (stopGenerateBtn) stopGenerateBtn.style.display = 'inline-block';
    const tempAssistant = {
        role: 'assistant',
        content: '',
        reasoning: '',
        timestamp: new Date().toISOString(),
        tool_calls: [],
        tool_results: []
    };
    currentMessages.push(tempAssistant);
    const aiIndex = currentMessages.length - 1;
    const messagesContainer = chatMessages;
    const reasoningBubble = document.createElement('div');
    reasoningBubble.className = 'reasoning-bubble';
    reasoningBubble.setAttribute('data-reasoning-idx', aiIndex);
    reasoningBubble.style.display = 'none';
    reasoningBubble.innerHTML = `
        <div class="reasoning-header">
            🧠 Thinking <span class="reasoning-toggle">v</span>
        </div>
        <div class="reasoning-content"></div>
    `;
    messagesContainer.appendChild(reasoningBubble);
    const messageDiv = createMessageElement(tempAssistant, aiIndex, 'assistant');
    messagesContainer.appendChild(messageDiv);
    const header = reasoningBubble.querySelector('.reasoning-header');
    const reasoningContentDiv = reasoningBubble.querySelector('.reasoning-content');
    const toggleSpan = reasoningBubble.querySelector('.reasoning-toggle');
    let collapsed = false;
    header.addEventListener('click', () => {
        collapsed = !collapsed;
        if (collapsed) {
            reasoningContentDiv.classList.add('collapsed');
            toggleSpan.classList.add('rotated');
            reasoningContentDiv.style.maxHeight = '';
        } else {
            reasoningContentDiv.classList.remove('collapsed');
            toggleSpan.classList.remove('rotated');
            reasoningContentDiv.style.maxHeight = '300px';
            reasoningContentDiv.scrollTop = reasoningContentDiv.scrollHeight;
        }
    });
    const msgContentDiv = messageDiv.querySelector('.message-content');
    let fullContent = '', fullReasoning = '';
    let toolCallsList = [];
    let toolResultsList = [];
    let updateTimer = null;
    let pendingContentUpdate = false;
    let pendingReasoningUpdate = false;

    const flushContentUpdate = () => {
        if (!pendingContentUpdate) return;
        pendingContentUpdate = false;
        if (msgContentDiv) {
            let html = fullContent;
            const htmlBlockRegex = /\[render_html\]([\s\S]*?)\[\/render_html\]/gi;
            const htmlBlocks = [];
            let processedWithPlaceholders = html;
            let idx = 0;
            processedWithPlaceholders = processedWithPlaceholders.replace(htmlBlockRegex, (fullMatch, content) => {
                const placeholder = `%%HTML_BLOCK_${idx}%%`;
                htmlBlocks.push({ placeholder: placeholder, content: content.trim() });
                idx++;
                return placeholder;
            });
            const progressBars = [];
            const progressPattern = /;;; bar\s*(?:\[([^\]]*)\])?\s*(?:<(\d+)\/(\d+)>)?\s*(?:\{([^}]*)\})?/g;
            let processedWithoutProgress = processedWithPlaceholders.replace(progressPattern, (match) => {
                const pIdx = progressBars.length;
                progressBars.push(match);
                return `%%PROGRESS_${pIdx}%%`;
            });
            let rendered = marked.parse(processedWithoutProgress, { breaks: true, gfm: true });
            progressBars.forEach((bar, pIdx) => {
                const barHtml = renderSingleProgressBar(bar);
                rendered = rendered.replace(`%%PROGRESS_${pIdx}%%`, barHtml);
            });
            const valueRegex = /;;; val\s+\[([^\]]*)\]\s+\[([^\]]*)\]/g;
            rendered = rendered.replace(valueRegex, (match) => renderValueBox(match));
            const statRegex = /;;; stat\s+\[([^\]]*)\]\s+\[([^\]]*)\]/g;
            rendered = rendered.replace(statRegex, (match) => renderStatBox(match));
            htmlBlocks.forEach(block => {
                const safeHTML = sanitizeHTML(block.content);
                rendered = rendered.replace(block.placeholder, safeHTML);
            });
            msgContentDiv.innerHTML = rendered;
            msgContentDiv.querySelectorAll('pre code').forEach(block => hljs?.highlightElement(block));
            const actionBar = messageDiv.querySelector('.message-action-bar');
            if (actionBar) {
                const tokenSpan = actionBar.querySelector('.token-count');
                if (tokenSpan) {
                    let totalTokens = estimateTokens(fullContent);
                    if (fullReasoning) totalTokens += estimateTokens(fullReasoning);
                    tokenSpan.textContent = `Token: ${Math.round(totalTokens)}`;
                }
            }
            requestAnimationFrame(() => enhanceCodeBlocks(msgContentDiv));
        }
        scrollToBottomIfNeeded();
        updateTokenDisplay();
    };

    const flushReasoningUpdate = () => {
        if (!pendingReasoningUpdate) return;
        pendingReasoningUpdate = false;
        if (reasoningContentDiv) {
            reasoningContentDiv.textContent = fullReasoning;
            reasoningBubble.style.display = 'block';
            reasoningContentDiv.scrollTop = reasoningContentDiv.scrollHeight;
        }
        scrollToBottomIfNeeded();
        updateTokenDisplay();
    };

    const scheduleContentUpdate = () => {
        if (updateTimer) clearTimeout(updateTimer);
        pendingContentUpdate = true;
        updateTimer = setTimeout(() => {
            flushContentUpdate();
            updateTimer = null;
        }, 50);
    };
    const scheduleReasoningUpdate = () => {
        if (updateTimer) clearTimeout(updateTimer);
        pendingReasoningUpdate = true;
        updateTimer = setTimeout(() => {
            flushReasoningUpdate();
            updateTimer = null;
        }, 50);
    };

    let userScrolledUp = false;
    let touchStartY = 0;
    let lastScrollTop = 0;
    const onTouchStart = (e) => { touchStartY = e.touches[0].clientY; };
    const onTouchMove = (e) => {
        const deltaY = touchStartY - e.touches[0].clientY;
        if (deltaY > 0) userScrolledUp = true;
    };
    const onScroll = () => {
        const isAtBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight <= 0;
        if (isAtBottom) userScrolledUp = false;
        else if (messagesContainer.scrollTop < lastScrollTop) userScrolledUp = true;
        lastScrollTop = messagesContainer.scrollTop;
    };
    const scrollToBottomIfNeeded = () => {
        if (!userScrolledUp) messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };

    messagesContainer.addEventListener('touchstart', onTouchStart);
    messagesContainer.addEventListener('touchmove', onTouchMove);
    messagesContainer.addEventListener('scroll', onScroll);

    const abortController = new AbortController();
    currentStreamController = abortController;

    try {
        const resp = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                messages: apiMessages,
                system_prompt: currentSystemPrompt,
                reasoning_effort: reasoningEffort ? reasoningEffort.value : 'medium',
                enable_tools: true
            }),
            signal: abortController.signal
        });
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop() || '';
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.slice(6);
                    if (dataStr === '[DONE]') continue;
                    try {
                        const data = JSON.parse(dataStr);
                        if (data.type === 'content') {
                            fullContent += data.content;
                            currentMessages[aiIndex].content = fullContent;
                            scheduleContentUpdate();
                        } else if (data.type === 'reasoning') {
                            fullReasoning += data.content;
                            currentMessages[aiIndex].reasoning = fullReasoning;
                            scheduleReasoningUpdate();
                        } else if (data.type === 'tool_call_start') {
                            createToolStatusBar(data.tool, data.query);
                            toolCallsList.push({ tool: data.tool, query: data.query });
                        } else if (data.type === 'tool_call_update') {
                            const lastIdx = toolCallsList.length - 1;
                            if (lastIdx >= 0) {
                                toolCallsList[lastIdx].query = data.query;
                                updateToolStatusBar(data.tool, data.query, true);
                            }
                        } else if (data.type === 'tool_executing') {
                            const lastQuery = toolCallsList[toolCallsList.length-1]?.query || '未知';
                            updateToolStatusBar(data.tool, data.query || lastQuery, true);
                        } else if (data.type === 'tool_result') {
                            const lastQuery = data.query || toolCallsList[toolCallsList.length-1]?.query || '未知';
                            updateToolStatusBar(data.tool, lastQuery, false);
                            toolResultsList.push({ tool: data.tool, result: data.result });
                            currentMessages[aiIndex].tool_calls = toolCallsList;
                            currentMessages[aiIndex].tool_results = toolResultsList.map(r => r.result);
                        } else if(data.type === 'error'){
                            if(msgContentDiv){
                                msgContentDiv.innerHTML = `<div style="color:#e86b6b">❌ ${escapeHtml(data.content)}</div>`;
                            }
                        }
                    } catch (e) {
                        console.error('解析错误:', e);
                    }
                }
            }
        }
        if (pendingContentUpdate) flushContentUpdate();
        if (pendingReasoningUpdate) flushReasoningUpdate();
        if (updateTimer) clearTimeout(updateTimer);
        removeToolStatusBar();
        if (toolCallsList.length > 0) {
            currentMessages[aiIndex].tool_calls = toolCallsList;
            currentMessages[aiIndex].tool_results = toolResultsList.map(r => r.result);
            const toolBtn = createToolInfoButton(toolCallsList, toolResultsList.map(r => r.result));
            messagesContainer.appendChild(toolBtn);
        }
        updateCurrentSessionTitle();
        updateMessageJumpSelectCustom();
        updateTokenDisplay();
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('请求已停止');
            if (msgContentDiv && !fullContent) msgContentDiv.innerHTML = '⏹️ 已停止生成';
        } else {
            console.error('Stream error:', error);
            if (msgContentDiv) msgContentDiv.innerHTML = `❌ 网络错误：${escapeHtml(error.message)}`;
        }
    } finally {
        isWaitingForResponse = false;
        sendBtn.disabled = false;
        if (stopGenerateBtn) stopGenerateBtn.style.display = 'none';
        removeToolStatusBar();
        currentStreamController = null;
        messagesContainer.removeEventListener('touchstart', onTouchStart);
        messagesContainer.removeEventListener('touchmove', onTouchMove);
        messagesContainer.removeEventListener('scroll', onScroll);
        updateTokenDisplay();
    }
}

function stopGeneration() {
    if (currentStreamController) {
        currentStreamController.abort();
        currentStreamController = null;
    }
    isWaitingForResponse = false;
    sendBtn.disabled = false;
    if (stopGenerateBtn) stopGenerateBtn.style.display = 'none';
    removeToolStatusBar();
}

// ========== 导入导出 ==========
function exportChatHistory() {
    const data = {
        version: '1.0',
        exportTime: new Date().toISOString(),
        session: {
            id: currentSessionId,
            title: sessions[currentSessionId]?.title,
            messages: currentMessages
        }
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `deepseek_chat_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
}

function importChatHistory(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const data = JSON.parse(e.target.result);
            let messages = data.session?.messages || (Array.isArray(data) ? data : data.messages || []);
            if (messages.length) {
                const newId = Date.now().toString();
                sessions[newId] = {
                    id: newId,
                    title: data.session?.title || '导入的对话',
                    messages: messages,
                    pinned: false,
                    manualRename: true,
                    createdAt: new Date().toISOString(),
                    updatedAt: new Date().toISOString()
                };
                saveSessionsToStorage();
                switchSession(newId);
                renderSessionList();
                showToast(`导入成功，共 ${messages.length} 条消息`);
            } else showToast('没有找到有效的聊天记录');
        } catch (err) { showToast('文件格式错误'); }
    };
    reader.readAsText(file);
    importFile.value = '';
}

function loadSystemPromptFromStorage() {
    const saved = localStorage.getItem('systemPrompt');
    if (saved) currentSystemPrompt = saved;
}

function loadReasoningFromStorage() {
    const v = localStorage.getItem('reasoningEffort') || 'medium';
    if (reasoningEffort) reasoningEffort.value = v;
    if (reasoningDropdown) {
        let text = '中';
        if (v === 'low') text = '轻';
        else if (v === 'medium') text = '中';
        else if (v === 'high') text = '深';
        reasoningDropdown.selectValue(v, text);
    }
}

function sanitizeHTML(html) {
    if (!html) return '';
    const dangerousTags = ['script', 'iframe', 'object', 'embed', 'form', 'input', 'button', 'textarea', 'select'];
    let safe = html;
    dangerousTags.forEach(tag => {
        const openRegex = new RegExp(`<${tag}[^>]*>`, 'gi');
        safe = safe.replace(openRegex, `&lt;${tag}&gt;`);
        const closeRegex = new RegExp(`<\\/${tag}>`, 'gi');
        safe = safe.replace(closeRegex, `&lt;/${tag}&gt;`);
    });
    safe = safe.replace(/on\w+\s*=\s*["'][^"']*["']/gi, '');
    safe = safe.replace(/on\w+\s*=\s*[^\s>]*/gi, '');
    return safe;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 压缩图片（最大宽度/高度 1024px，质量 0.7）
function compressImage(file, maxSize = 1024, quality = 0.7) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                let width = img.width;
                let height = img.height;
                if (width > height) {
                    if (width > maxSize) {
                        height = Math.round(height * (maxSize / width));
                        width = maxSize;
                    }
                } else {
                    if (height > maxSize) {
                        width = Math.round(width * (maxSize / height));
                        height = maxSize;
                    }
                }
                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);
                canvas.toBlob((blob) => {
                    const compressedFile = new File([blob], file.name, {
                        type: 'image/jpeg',
                        lastModified: Date.now()
                    });
                    resolve(compressedFile);
                }, 'image/jpeg', quality);
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });
}
