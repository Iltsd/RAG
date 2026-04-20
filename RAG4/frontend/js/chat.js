// chat.js - Исправленная версия с подсказками и автодополнением
console.log('✅ chat.js загружен');

let currentSessionId = null;

// ============================================
// ФУНКЦИЯ ФОРМАТИРОВАНИЯ ТЕКСТА
// ============================================
function formatMessageText(text) {
    if (!text) return '';

    let formatted = text;

    // Жирный текст: **текст** -> <strong>текст</strong>
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    // Курсив: *текст* -> <em>текст</em>
    formatted = formatted.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>');
    // Код: `код` -> <code>код</code>
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');

    const lines = formatted.split('\n');
    let processedLines = [];

    for (let line of lines) {
        const trimmed = line.trim();
        if (trimmed === '') {
            processedLines.push('<br>');
            continue;
        }

        // Заголовки
        if (trimmed.startsWith('## ')) {
            processedLines.push(`<h3>${trimmed.substring(3)}</h3>`);
        } else if (trimmed.startsWith('# ')) {
            processedLines.push(`<h2>${trimmed.substring(2)}</h2>`);
        }
        // Маркированный список
        else if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
            processedLines.push(`<li class="bullet">${trimmed.substring(2)}</li>`);
        }
        // Нумерованный список
        else if (trimmed.match(/^\d+\.\s/)) {
            const match = trimmed.match(/^(\d+)\.\s(.*)$/);
            if (match) {
                processedLines.push(`<li value="${match[1]}">${match[2]}</li>`);
            }
        }
        // Обычный текст
        else {
            processedLines.push(line);
        }
    }

    // Группировка списков
    let finalLines = [];
    let inBullet = false, inNumbered = false;
    let bulletItems = [], numberedItems = [];

    for (let line of processedLines) {
        if (line.startsWith('<li class="bullet">')) {
            if (!inBullet) {
                if (inNumbered) {
                    finalLines.push('<ol>' + numberedItems.join('') + '</ol>');
                    inNumbered = false;
                    numberedItems = [];
                }
                inBullet = true;
                bulletItems = [line];
            } else {
                bulletItems.push(line);
            }
        } else if (line.startsWith('<li value=')) {
            if (!inNumbered) {
                if (inBullet) {
                    finalLines.push('<ul>' + bulletItems.join('') + '</ul>');
                    inBullet = false;
                    bulletItems = [];
                }
                inNumbered = true;
                numberedItems = [line];
            } else {
                numberedItems.push(line);
            }
        } else {
            if (inBullet) {
                finalLines.push('<ul>' + bulletItems.join('') + '</ul>');
                inBullet = false;
                bulletItems = [];
            }
            if (inNumbered) {
                finalLines.push('<ol>' + numberedItems.join('') + '</ol>');
                inNumbered = false;
                numberedItems = [];
            }
            finalLines.push(line);
        }
    }
    if (inBullet) finalLines.push('<ul>' + bulletItems.join('') + '</ul>');
    if (inNumbered) finalLines.push('<ol>' + numberedItems.join('') + '</ol>');

    let formattedText = finalLines.join('\n');
    formattedText = formattedText.replace(/\n/g, '<br>');
    formattedText = formattedText.replace(/<br>\s*<(ul|ol)/g, '<$1');
    formattedText = formattedText.replace(/<\/(ul|ol)>\s*<br>/g, '</$1>');
    formattedText = formattedText.replace(/<(ul|ol)[^>]*>[\s\S]*?<\/\1>/g, (match) => match.replace(/<br>/g, ''));

    return formattedText;
}

// ============================================
// УДАЛЕНИЕ БЛОКА ПОДСКАЗОК (ИДЕЙ)
// ============================================
function removeSuggestions() {
    const suggestionsDiv = document.querySelector('.suggestions-container');
    if (suggestionsDiv) suggestionsDiv.remove();
}

// ============================================
// ПОКАЗ БЛОКА С ИДЕЯМИ ДЛЯ НОВОГО ЧАТА
// ============================================
function showSuggestions() {
    const suggestions = [
        "Что такое RAG?",
        "Как работает LangChain?",
        "Объясни разницу между llama3.2 и llama3.1",
        "Как загрузить PDF документ?",
        "Что такое эмбеддинги?",
        "Как улучшить точность RAG?"
    ];
    
    const messagesContainer = document.getElementById('messages');
    if (!messagesContainer) return;
    
    // Удаляем старый блок, если есть
    removeSuggestions();
    
    const suggestionsDiv = document.createElement('div');
    suggestionsDiv.className = 'suggestions-container';
    suggestionsDiv.innerHTML = '<div class="suggestions-title">💡 Идеи для вопросов:</div>';
    
    const buttonsDiv = document.createElement('div');
    buttonsDiv.className = 'suggestions-buttons';
    
    suggestions.forEach(text => {
        const btn = document.createElement('button');
        btn.className = 'suggestion-btn';
        btn.textContent = text;
        btn.onclick = () => {
            const input = document.getElementById('message-input');
            if (input) {
                input.value = text;
                removeSuggestions();   // убираем блок подсказок
                sendMessage();         // отправляем сообщение
            }
        };
        buttonsDiv.appendChild(btn);
    });
    
    suggestionsDiv.appendChild(buttonsDiv);
    messagesContainer.appendChild(suggestionsDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ============================================
// ДОБАВЛЕНИЕ СООБЩЕНИЯ В UI
// ============================================
function addMessageToUI(text, role, audioUrl = null) {
    console.log(`🔥 addMessageToUI: роль=${role}`);

    const messagesContainer = document.getElementById('messages');
    if (!messagesContainer) {
        console.error('❌ messagesContainer не найден!');
        return;
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = formatMessageText(text);
    messageDiv.appendChild(contentDiv);

    // Кнопка воспроизведения аудио
    if (role === 'assistant' && audioUrl) {
        const audioBtn = document.createElement('button');
        audioBtn.className = 'audio-btn';
        audioBtn.innerHTML = '🔊 Воспроизвести ответ';

        let fullUrl = audioUrl;
        if (!fullUrl.startsWith('http')) {
            const filename = fullUrl.split('/').pop();
            fullUrl = `http://localhost:8000/audio/${filename}`;
        }
        console.log('🎵 Воспроизведение:', fullUrl);

        audioBtn.onclick = () => {
            const audio = new Audio(fullUrl);
            audio.play().catch(e => console.error('Ошибка воспроизведения:', e));
        };
        messageDiv.appendChild(audioBtn);
    }

    // Время сообщения
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    const now = new Date();
    timeDiv.textContent = now.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    messageDiv.appendChild(timeDiv);

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    console.log('✅ Сообщение добавлено');
}

// ============================================
// ЗАГРУЗКА ИСТОРИИ ЧАТА
// ============================================
async function loadChatHistory(sessionId) {
    console.log('🔄 loadChatHistory для sessionId:', sessionId);
    const messagesContainer = document.getElementById('messages');
    if (!messagesContainer) return;

    try {
        messagesContainer.innerHTML = '<div class="loading">Загрузка истории...</div>';
        const history = await getChatHistory(sessionId);
        console.log('✅ История получена:', history);

        messagesContainer.innerHTML = '';
        if (!history || history.length === 0) {
            messagesContainer.innerHTML = '<div class="message assistant">История пуста</div>';
            return;
        }

        history.forEach(msg => {
            const role = msg.role === 'human' ? 'user' : 'assistant';
            addMessageToUI(msg.content, role, msg.audio_file);
        });

        currentSessionId = sessionId;
        if (window.chatAPI) window.chatAPI.setSessionId(sessionId);
    } catch (error) {
        console.error('❌ Ошибка:', error);
        messagesContainer.innerHTML = '<div class="error">Ошибка загрузки истории</div>';
    }
}

// ============================================
// ОТПРАВКА СООБЩЕНИЯ
// ============================================
async function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const messagesContainer = document.getElementById('messages');

    const question = messageInput.value.trim();
    if (!question) return;

    // Удаляем блок подсказок, если он есть (пользователь начал отправку)
    removeSuggestions();

    messageInput.value = '';
    addMessageToUI(question, 'user');

    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.id = 'loading-indicator';
    loadingDiv.innerHTML = 'Ассистент печатает...';
    messagesContainer.appendChild(loadingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
        const model = window.selectedModel || 'llama3.2';
        const agentType = window.selectedAgentType || 'rag';
        const selectedSites = window.selectedSites || [];
        console.log('🌐 Выбранные сайты при отправке:', selectedSites);

        if (selectedSites.length > 0) {
            await forumsSearch(question, selectedSites, currentSessionId);
        }

        const response = await sendChatMessage(question, currentSessionId, model, agentType, selectedSites);

        const loading = document.getElementById('loading-indicator');
        if (loading) loading.remove();

        if (response.session_id) {
            currentSessionId = response.session_id;
        }

        const audio = response.audio_url || response.audio_file;
        addMessageToUI(response.answer, 'assistant', audio);
    } catch (error) {
        const loading = document.getElementById('loading-indicator');
        if (loading) loading.remove();
        addMessageToUI(`Ошибка: ${error.message}`, 'assistant');
    }
}

// ============================================
// ИНИЦИАЛИЗАЦИЯ (DOMContentLoaded)
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔄 Инициализация chat.js');

    const sendBtn = document.getElementById('send-btn');
    const messageInput = document.getElementById('message-input');

    if (sendBtn) sendBtn.addEventListener('click', sendMessage);
    if (messageInput) {
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // При начале ввода текста удаляем блок подсказок (идей)
        messageInput.addEventListener('input', function() {
            if (this.value.length > 0) {
                removeSuggestions();
            }
        });
    }

    const messagesContainer = document.getElementById('messages');
    if (messagesContainer && messagesContainer.children.length === 0) {
        addMessageToUI('Здравствуйте! Чем я могу помочь?', 'assistant');
        // Показываем идеи при первом запуске (если нет истории)
        showSuggestions();
    }
});

// ============================================
// АВТОДОПОЛНЕНИЕ ПРИ ВВОДЕ
// ============================================
const autocompleteDict = [
    "RAG", "LangChain", "ChromaDB", "Ollama", "Piper", "FastAPI",
    "эмбеддинг", "векторная база данных", "семантический поиск",
    "загрузить документ", "история чата", "агент", "суммаризация",
    "LLM", "нейросеть", "трансформер", "токенизация", "fine-tuning",
    "как работает RAG", "что такое retrieval", "пример кода LangChain",
    "установка Ollama", "сравнение моделей", "лучшие практики"
];

const inputField = document.getElementById('message-input');
const autocompleteList = document.getElementById('autocomplete-list');

if (inputField && autocompleteList) {
    inputField.addEventListener('input', function() {
        const val = this.value.toLowerCase();
        if (val.length < 2) {
            autocompleteList.style.display = 'none';
            return;
        }
        
        const matches = autocompleteDict.filter(word => 
            word.toLowerCase().includes(val)
        ).slice(0, 8);
        
        if (matches.length === 0) {
            autocompleteList.style.display = 'none';
            return;
        }
        
        autocompleteList.innerHTML = '';
        matches.forEach(match => {
            const div = document.createElement('div');
            div.textContent = match;
            div.addEventListener('click', () => {
                inputField.value = match;
                autocompleteList.style.display = 'none';
                inputField.focus();
                // При выборе автодополнения не удаляем блок идей, но пользователь может продолжить ввод
            });
            autocompleteList.appendChild(div);
        });
        autocompleteList.style.display = 'block';
    });
    
    inputField.addEventListener('blur', () => {
        setTimeout(() => {
            autocompleteList.style.display = 'none';
        }, 200);
    });
}

// ============================================
// ЭКСПОРТ ФУНКЦИЙ ДЛЯ ДРУГИХ МОДУЛЕЙ
// ============================================
window.chatAPI = {
    setSessionId: (id) => { currentSessionId = id; },
    getSessionId: () => currentSessionId,
    loadChatHistory: loadChatHistory,
    sendMessage: sendMessage
};

window.showSuggestions = showSuggestions;

console.log('✅ chat.js полностью готов');