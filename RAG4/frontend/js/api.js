// api.js - Исправленная версия
const API_BASE_URL = 'http://localhost:8000';

// ============================================
// ЗАПРОСЫ К ЧАТУ
// ============================================

async function sendChatMessage(question, sessionId, model, agentType, selectedSites) {
    // Если selectedSites не передан явно, берем из глобальной переменной
    if (!selectedSites && window.selectedSites) {
        selectedSites = window.selectedSites;
    }

    console.log('📤 Отправка сообщения:', {
        question,
        sessionId,
        model,
        agentType,
        selectedSites
    });

    const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            question: question,
            model: model,
            agent_type: agentType,
            session_id: sessionId || undefined,
            selected_sites: selectedSites || []
        })
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const data = await response.json();

    // Обработка аудиофайла: из полного пути получаем имя файла и формируем корректный URL
    if (data.audio_file) {
        let filename = data.audio_file;
        if (filename.includes('/')) {
            filename = filename.split('/').pop();   // оставляем только имя файла
        }
        data.audio_url = `${API_BASE_URL}/audio/${filename}`;
        console.log('🎵 Аудио URL:', data.audio_url);
    }

    return data;
}

// ============================================
// ЗАПРОСЫ К ЧАТ-СЕССИЯМ
// ============================================

async function getChatSessions() {
    console.log('📤 Запрос списка чат-сессий...');
    const url = `${API_BASE_URL}/chat-sessions`;

    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('📥 Получены чат-сессии:', data);
        return data;
    } catch (error) {
        console.error('❌ Ошибка получения сессий:', error);
        return [];
    }
}

async function getChatHistory(sessionId) {
    console.log('📤 Запрос истории чата для session_id:', sessionId);
    if (!sessionId) {
        console.error('❌ sessionId не указан');
        return [];
    }

    const url = `${API_BASE_URL}/chat-history?session_id=${encodeURIComponent(sessionId)}`;

    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('📥 Получена история чата:', data);
        return data;
    } catch (error) {
        console.error('❌ Ошибка получения истории:', error);
        return [];
    }
}

// ============================================
// ЗАПРОСЫ К ДОКУМЕНТАМ
// ============================================

async function uploadDocument(file) {
    console.log('📤 Загрузка файла:', file.name);
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/upload-doc`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('📥 Файл загружен:', data);
        return data;
    } catch (error) {
        console.error('❌ Ошибка загрузки файла:', error);
        throw error;
    }
}

async function listDocuments() {
    console.log('📤 Запрос списка документов...');
    try {
        const response = await fetch(`${API_BASE_URL}/list-docs`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('📥 Получены документы:', data);
        return data;
    } catch (error) {
        console.error('❌ Ошибка получения документов:', error);
        return [];
    }
}

async function deleteDocument(fileId) {
    console.log('📤 Удаление документа с ID:', fileId);
    try {
        const response = await fetch(`${API_BASE_URL}/delete-doc`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ file_id: fileId })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('📥 Документ удален:', data);
        return data;
    } catch (error) {
        console.error('❌ Ошибка удаления документа:', error);
        throw error;
    }
}

// ============================================
// ПОИСК НА ФОРУМАХ
// ============================================

async function forumsSearch(question, selectedSites, sessionId) {
    console.log('📤 Поиск на форумах:', { question, selectedSites, sessionId });
    try {
        const response = await fetch(`${API_BASE_URL}/forums-search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                selected_sites: selectedSites,
                session_id: sessionId || undefined
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API ошибка (${response.status}): ${errorText}`);
        }

        console.log('📥 Поиск на форумах выполнен успешно');
        return true;
    } catch (error) {
        console.error('❌ Ошибка поиска на форумах:', error);
        return false;
    }
}

// ============================================
// ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
// ============================================

async function checkApiHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/list-docs`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });
        console.log('✅ API доступен, статус:', response.status);
        return response.ok;
    } catch (error) {
        console.error('❌ API недоступен:', error.message);
        return false;
    }
}

function formatSessionDate(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}