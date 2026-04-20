// sidebar.js - Исправленная версия
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ sidebar.js загружен');

    // Элементы
    const modelSelect = document.getElementById('model-select');
    const agentTypeSelect = document.getElementById('agent-type-select');
    const siteCheckboxes = document.querySelectorAll('.checkbox-group input[type="checkbox"]');
    const newChatBtn = document.getElementById('new-chat-btn');
    const loadChatsBtn = document.getElementById('load-chats-btn');
    const chatSessionsSelect = document.getElementById('chat-sessions-select');
    const fileUpload = document.getElementById('file-upload');
    const uploadBtn = document.getElementById('upload-btn');
    const refreshDocsBtn = document.getElementById('refresh-docs-btn');
    const docList = document.getElementById('doc-list');
    const docDeleteSelect = document.getElementById('doc-delete-select');
    const deleteDocBtn = document.getElementById('delete-doc-btn');
    const uploadStatus = document.getElementById('upload-status');
    const maxSitesInfo = document.querySelector('.checkbox-group small');

    // Глобальные настройки
    window.selectedModel = modelSelect ? modelSelect.value : 'llama3.2';
    window.selectedAgentType = agentTypeSelect ? agentTypeSelect.value : 'rag';
    window.selectedSites = [];

    // Обновление выбранных сайтов
    function updateSelectedSites() {
        window.selectedSites = Array.from(siteCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
        console.log('📌 Выбранные сайты обновлены:', window.selectedSites);

        if (maxSitesInfo) {
            maxSitesInfo.textContent = `Макс. 2 (выбрано ${window.selectedSites.length})`;
            maxSitesInfo.style.color = window.selectedSites.length === 2 ? '#ff9800' : '#6b7a91';
        }
    }

    // Обработчики
    if (modelSelect) {
        modelSelect.addEventListener('change', (e) => {
            window.selectedModel = e.target.value;
            console.log('📌 Модель:', window.selectedModel);
        });
    }

    if (agentTypeSelect) {
        agentTypeSelect.addEventListener('change', (e) => {
            window.selectedAgentType = e.target.value;
            console.log('📌 Тип агента:', window.selectedAgentType);
        });
    }

    if (siteCheckboxes.length) {
        siteCheckboxes.forEach(cb => {
            cb.addEventListener('change', function() {
                const checkedCount = Array.from(siteCheckboxes).filter(c => c.checked).length;
                if (checkedCount > 2) {
                    this.checked = false;
                    const warning = document.createElement('div');
                    warning.textContent = '⚠️ Можно выбрать не более 2 платформ';
                    warning.style.cssText = 'color:#ff9800; font-size:12px; margin-top:5px;';
                    const parent = this.closest('.checkbox-group');
                    const old = parent.querySelector('.warning-message');
                    if (old) old.remove();
                    warning.className = 'warning-message';
                    parent.appendChild(warning);
                    setTimeout(() => warning.remove(), 2000);
                    return;
                }
                updateSelectedSites();
            });
        });
        updateSelectedSites();
    }

    // Новый чат
// sidebar.js – внутри newChatBtn.addEventListener
    if (newChatBtn) {
        newChatBtn.addEventListener('click', () => {
            if (window.chatAPI) window.chatAPI.setSessionId(null);
            const messagesContainer = document.getElementById('messages');
            if (messagesContainer) {
                messagesContainer.innerHTML = '';
                // Показываем приветствие и идеи
                addMessageToUI('Здравствуйте! Чем я могу помочь?', 'assistant');
                if (window.showSuggestions) window.showSuggestions();
            }
            if (chatSessionsSelect) chatSessionsSelect.style.display = 'none';
        });
    }   

    // Загрузка сессий
    if (loadChatsBtn) {
        loadChatsBtn.addEventListener('click', async () => {
            try {
                const sessions = await getChatSessions();
                if (!sessions || sessions.length === 0) {
                    alert('Нет сохраненных чатов');
                    return;
                }
                if (chatSessionsSelect) {
                    chatSessionsSelect.style.display = 'block';
                    chatSessionsSelect.innerHTML = '<option value="">Выберите чат...</option>' +
                        sessions.map(s => `<option value="${s.session_id}">${s.title}</option>`).join('');
                }
            } catch (error) {
                console.error(error);
                alert('Ошибка загрузки сессий');
            }
        });
    }

    // Выбор чата
    if (chatSessionsSelect) {
        chatSessionsSelect.addEventListener('change', async (e) => {
            const sessionId = e.target.value;
            if (sessionId && window.chatAPI) {
                await window.chatAPI.loadChatHistory(sessionId);
                chatSessionsSelect.style.display = 'none';
            }
        });
    }

    // Документы
    async function refreshDocuments() {
        try {
            const docs = await listDocuments();
            if (docList) {
                docList.innerHTML = docs.map(d => `<li>📄 ${d.filename} (ID: ${d.id})</li>`).join('');
            }
            if (docDeleteSelect) {
                docDeleteSelect.innerHTML = docs.map(d => `<option value="${d.id}">${d.filename}</option>`).join('');
                docDeleteSelect.disabled = docs.length === 0;
            }
        } catch (error) {
            console.error(error);
        }
    }

    if (refreshDocsBtn) refreshDocsBtn.addEventListener('click', refreshDocuments);
    if (uploadBtn && fileUpload) {
        uploadBtn.addEventListener('click', async () => {
            const file = fileUpload.files[0];
            if (!file) return;
            uploadStatus.textContent = 'Загрузка...';
            try {
                const result = await uploadDocument(file);
                uploadStatus.textContent = `✅ Файл загружен, ID: ${result.file_id}`;
                fileUpload.value = '';
                refreshDocuments();
                setTimeout(() => uploadStatus.textContent = '', 3000);
            } catch (error) {
                uploadStatus.textContent = '❌ Ошибка';
                console.error(error);
            }
        });
    }

    if (deleteDocBtn && docDeleteSelect) {
        deleteDocBtn.addEventListener('click', async () => {
            const fileId = docDeleteSelect.value;
            if (!fileId) return;
            if (confirm('Удалить документ?')) {
                try {
                    await deleteDocument(parseInt(fileId));
                    refreshDocuments();
                } catch (error) {
                    console.error(error);
                    alert('Ошибка удаления');
                }
            }
        });
    }

    refreshDocuments();
    console.log('✅ sidebar.js готов');
});