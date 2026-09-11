// Configuration
const API_BASE_URL = '/api/v1';
const WS_BASE_URL = `ws://${window.location.host}/ws/chat`;

// State
let currentSessionId = null;
let currentUser = null;
let socket = null;
let isConnected = false;
let messageHistory = [];

// DOM Elements
const elements = {
    // Chat elements
    chatMessages: document.getElementById('chatMessages'),
    chatInput: document.getElementById('chatInput'),
    sendBtn: document.getElementById('sendBtn'),
    clearChatBtn: document.getElementById('clearChatBtn'),
    chatMode: document.getElementById('chatMode'),
    chatTitle: document.getElementById('chatTitle'),
    statusIndicator: document.getElementById('statusIndicator'),
    charCount: document.getElementById('charCount'),
    
    // Sidebar elements
    sidebar: document.getElementById('sidebar'),
    chatHistory: document.getElementById('chatHistory'),
    newChatBtn: document.getElementById('newChatBtn'),
    mobileMenuBtn: document.getElementById('mobileMenuBtn'),
    sidebarToggle: document.getElementById('sidebarToggle'),
    logoutBtn: document.getElementById('logoutBtn'),
    
    // User elements
    userAvatar: document.getElementById('userAvatar'),
    userName: document.getElementById('userName'),
    userRole: document.getElementById('userRole'),
    
    // Modal elements
    loginModal: document.getElementById('loginModal'),
    loginForm: document.getElementById('loginForm'),
    registerForm: document.getElementById('registerForm'),
    loginUsername: document.getElementById('loginUsername'),
    loginPassword: document.getElementById('loginPassword'),
    registerFullName: document.getElementById('registerFullName'),
    registerUsername: document.getElementById('registerUsername'),
    registerEmail: document.getElementById('registerEmail'),
    registerPassword: document.getElementById('registerPassword'),
    registerRole: document.getElementById('registerRole'),
    showRegisterLink: document.getElementById('showRegisterLink'),
    showLoginLink: document.getElementById('showLoginLink'),
    togglePassword: document.getElementById('togglePassword'),
    loginBtn: document.getElementById('loginBtn'),
    
    // Loading
    loadingOverlay: document.getElementById('loadingOverlay'),
    
    // Suggestion buttons
    suggestionBtns: document.querySelectorAll('.suggestion-btn')
};

// Utility Functions
function generateId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function formatTime(date) {
    return new Date(date).toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading() {
    elements.loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    elements.loadingOverlay.style.display = 'none';
}

function updateStatus(status, message) {
    const dot = elements.statusIndicator.querySelector('.status-dot');
    dot.className = `status-dot ${status}`;
    elements.statusIndicator.innerHTML = `<span class="status-dot ${status}"></span> ${message}`;
}

// API Functions
async function apiRequest(endpoint, method = 'GET', data = null, headers = {}) {
    const token = localStorage.getItem('access_token');
    const defaultHeaders = {
        'Content-Type': 'application/json',
        ...headers
    };
    
    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
    
    const config = {
        method,
        headers: defaultHeaders
    };
    
    if (data) {
        config.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        const responseData = await response.json();
        
        if (!response.ok) {
            throw new Error(responseData.detail || 'API request failed');
        }
        
        return responseData;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Auth Functions
async function login(username, password) {
    try {
        const data = await apiRequest('/auth/login', 'POST', { username, password });
        localStorage.setItem('access_token', data.access_token);
        currentUser = { username };
        await loadUserInfo();
        closeModal();
        initializeChat();
        loadChatHistory();
        updateStatus('online', 'Connected');
        return true;
    } catch (error) {
        alert('Login failed: ' + error.message);
        return false;
    }
}

async function register(fullName, username, email, password, role) {
    try {
        const data = await apiRequest('/auth/register', 'POST', {
            full_name: fullName,
            username,
            email,
            password,
            role
        });
        localStorage.setItem('access_token', data.access_token);
        currentUser = { username };
        await loadUserInfo();
        closeModal();
        initializeChat();
        loadChatHistory();
        updateStatus('online', 'Connected');
        return true;
    } catch (error) {
        alert('Registration failed: ' + error.message);
        return false;
    }
}

async function logout() {
    localStorage.removeItem('access_token');
    currentUser = null;
    if (socket) {
        socket.close();
        socket = null;
    }
    isConnected = false;
    currentSessionId = null;
    elements.chatMessages.innerHTML = '<div class="welcome-message"><div class="welcome-icon"><i class="fas fa-robot"></i></div><h2>Welcome to AI Hospital Assistant</h2><p>Please login to start chatting.</p></div>';
    updateStatus('offline', 'Disconnected');
    elements.userName.textContent = 'Guest User';
    elements.userRole.textContent = 'Patient';
    showModal();
}

async function loadUserInfo() {
    try {
        const user = await apiRequest('/users/me', 'GET');
        elements.userName.textContent = user.full_name || user.username;
        elements.userRole.textContent = user.role || 'Patient';
        return user;
    } catch (error) {
        console.error('Failed to load user info:', error);
        return null;
    }
}

// Chat Functions
function initializeChat() {
    currentSessionId = generateId();
    elements.chatTitle.textContent = 'New Chat';
    elements.chatMessages.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">
                <i class="fas fa-robot"></i>
            </div>
            <h2>Welcome to AI Hospital Assistant</h2>
            <p>How can I help you today?</p>
        </div>
    `;
    messageHistory = [];
    connectWebSocket();
}

function connectWebSocket() {
    if (socket) {
        socket.close();
    }
    
    const wsUrl = `${WS_BASE_URL}/${currentSessionId}`;
    socket = new WebSocket(wsUrl);
    
    socket.onopen = () => {
        isConnected = true;
        updateStatus('online', 'Connected');
        console.log('WebSocket connected');
    };
    
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    socket.onclose = () => {
        isConnected = false;
        updateStatus('offline', 'Disconnected');
        console.log('WebSocket disconnected');
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
            if (currentSessionId) {
                connectWebSocket();
            }
        }, 3000);
    };
    
    socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateStatus('error', 'Connection error');
    };
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'status':
            updateStatus(data.status, data.message);
            break;
            
        case 'message':
            addMessage(data.role, data.content, data.sources);
            break;
            
        case 'chunk':
            // Streaming response - update last message
            const lastMessage = document.querySelector('.message:last-child .message-content');
            if (lastMessage && lastMessage.dataset.streaming === 'true') {
                lastMessage.textContent += data.content;
                scrollToBottom();
            } else {
                addMessage('assistant', data.content, null, true);
            }
            break;
            
        case 'sources':
            // Add sources to last message
            const messages = document.querySelectorAll('.message');
            if (messages.length > 0) {
                const lastMsg = messages[messages.length - 1];
                const sourcesContainer = lastMsg.querySelector('.message-sources');
                if (sourcesContainer && data.sources) {
                    sourcesContainer.innerHTML = renderSources(data.sources);
                    sourcesContainer.style.display = 'block';
                }
            }
            break;
            
        case 'error':
            addMessage('assistant', `⚠️ Error: ${data.content}`, null);
            break;
            
        default:
            console.log('Unknown message type:', data.type);
    }
}

function addMessage(role, content, sources = null, streaming = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const icon = role === 'user' ? 'fa-user' : 'fa-robot';
    const iconClass = role === 'user' ? 'user-icon' : 'assistant-icon';
    
    let sourcesHTML = '';
    if (sources && sources.length > 0) {
        sourcesHTML = renderSources(sources);
    }
    
    messageDiv.innerHTML = `
        <div class="message-avatar ${iconClass}">
            <i class="fas ${icon}"></i>
        </div>
        <div class="message-content-wrapper">
            <div class="message-content" ${streaming ? 'data-streaming="true"' : ''}>
                ${escapeHtml(content)}
            </div>
            ${sourcesHTML ? `<div class="message-sources">${sourcesHTML}</div>` : ''}
            <div class="message-time">${formatTime(new Date())}</div>
        </div>
    `;
    
    // Remove welcome message if it exists
    const welcome = elements.chatMessages.querySelector('.welcome-message');
    if (welcome) {
        welcome.remove();
    }
    
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
    
    // If not streaming, add to history
    if (!streaming) {
        messageHistory.push({ role, content, sources });
    }
}

function renderSources(sources) {
    if (!sources || sources.length === 0) return '';
    
    let html = '<div class="sources-header"><i class="fas fa-book-open"></i> Sources:</div><ul>';
    sources.forEach(source => {
        const title = source.title || 'Document';
        const content = source.content || source.text || '';
        const excerpt = content.length > 100 ? content.substring(0, 100) + '...' : content;
        html += `
            <li>
                <div class="source-title">${escapeHtml(title)}</div>
                <div class="source-content">${escapeHtml(excerpt)}</div>
            </li>
        `;
    });
    html += '</ul>';
    return html;
}

async function sendMessage(message) {
    if (!message.trim() || !isConnected) return;
    
    // Add user message
    addMessage('user', message);
    
    // Clear input
    elements.chatInput.value = '';
    elements.charCount.textContent = '0';
    
    // Show typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant typing';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="message-avatar assistant-icon">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content-wrapper">
            <div class="message-content">
                <span class="typing-dots">
                    <span></span><span></span><span></span>
                </span>
            </div>
        </div>
    `;
    elements.chatMessages.appendChild(typingDiv);
    scrollToBottom();
    
    try {
        // Send via WebSocket
        socket.send(JSON.stringify({
            type: 'message',
            session_id: currentSessionId,
            message: message,
            mode: elements.chatMode.value
        }));
    } catch (error) {
        console.error('Failed to send message:', error);
        document.getElementById('typingIndicator')?.remove();
        addMessage('assistant', '⚠️ Failed to send message. Please try again.', null);
    }
}

async function loadChatHistory() {
    try {
        const sessions = await apiRequest('/chat/sessions', 'GET');
        renderChatHistory(sessions);
    } catch (error) {
        console.error('Failed to load chat history:', error);
    }
}

function renderChatHistory(sessions) {
    const historyContainer = elements.chatHistory;
    historyContainer.innerHTML = '';
    
    if (!sessions || sessions.length === 0) {
        historyContainer.innerHTML = '<div class="no-history">No chat history</div>';
        return;
    }
    
    sessions.forEach(session => {
        const item = document.createElement('div');
        item.className = 'history-item';
        item.dataset.sessionId = session.id;
        item.innerHTML = `
            <i class="fas fa-comment"></i>
            <span>${escapeHtml(session.title || 'Chat')}</span>
            <span class="history-time">${formatTime(session.created_at)}</span>
        `;
        item.addEventListener('click', () => loadChatSession(session.id));
        historyContainer.appendChild(item);
    });
}

async function loadChatSession(sessionId) {
    try {
        const messages = await apiRequest(`/chat/sessions/${sessionId}/messages`, 'GET');
        currentSessionId = sessionId;
        elements.chatTitle.textContent = 'Chat Session';
        
        elements.chatMessages.innerHTML = '';
        messages.forEach(msg => {
            addMessage(msg.role, msg.content, msg.sources ? JSON.parse(msg.sources) : null);
        });
        
        // Reconnect WebSocket with new session
        if (socket) {
            socket.close();
        }
        connectWebSocket();
    } catch (error) {
        console.error('Failed to load chat session:', error);
    }
}

async function clearChat() {
    if (!currentSessionId) return;
    
    try {
        await apiRequest(`/chat/sessions/${currentSessionId}`, 'DELETE');
        currentSessionId = generateId();
        elements.chatTitle.textContent = 'New Chat';
        elements.chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">
                    <i class="fas fa-robot"></i>
                </div>
                <h2>Welcome to AI Hospital Assistant</h2>
                <p>How can I help you today?</p>
            </div>
        `;
        messageHistory = [];
        
        // Reconnect WebSocket with new session
        if (socket) {
            socket.close();
        }
        connectWebSocket();
        loadChatHistory();
    } catch (error) {
        console.error('Failed to clear chat:', error);
    }
}

function scrollToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

// UI Functions
function showModal() {
    elements.loginModal.style.display = 'flex';
}

function closeModal() {
    elements.loginModal.style.display = 'none';
}

function togglePasswordVisibility() {
    const input = elements.loginPassword;
    const icon = elements.togglePassword.querySelector('i');
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

function toggleSidebar() {
    elements.sidebar.classList.toggle('collapsed');
}

// Event Listeners
document.addEventListener('DOMContentLoaded', async () => {
    // Check if user is logged in
    const token = localStorage.getItem('access_token');
    if (token) {
        try {
            await loadUserInfo();
            closeModal();
            initializeChat();
            loadChatHistory();
            updateStatus('online', 'Connected');
        } catch (error) {
            console.error('Auto-login failed:', error);
            showModal();
        }
    } else {
        showModal();
    }
    
    // Login form
    elements.loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = elements.loginUsername.value;
        const password = elements.loginPassword.value;
        await login(username, password);
    });
    
    // Register form
    elements.registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fullName = elements.registerFullName.value;
        const username = elements.registerUsername.value;
        const email = elements.registerEmail.value;
        const password = elements.registerPassword.value;
        const role = elements.registerRole.value;
        await register(fullName, username, email, password, role);
    });
    
    // Toggle between login and register
    elements.showRegisterLink.addEventListener('click', (e) => {
        e.preventDefault();
        elements.loginForm.style.display = 'none';
        elements.registerForm.style.display = 'block';
    });
    
    elements.showLoginLink.addEventListener('click', (e) => {
        e.preventDefault();
        elements.loginForm.style.display = 'block';
        elements.registerForm.style.display = 'none';
    });
    
    // Toggle password visibility
    elements.togglePassword.addEventListener('click', togglePasswordVisibility);
    
    // Send message
    elements.sendBtn.addEventListener('click', () => {
        const message = elements.chatInput.value;
        sendMessage(message);
    });
    
    elements.chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const message = elements.chatInput.value;
            sendMessage(message);
        }
    });
    
    elements.chatInput.addEventListener('input', () => {
        const count = elements.chatInput.value.length;
        elements.charCount.textContent = count;
        // Auto-resize
        elements.chatInput.style.height = 'auto';
        elements.chatInput.style.height = elements.chatInput.scrollHeight + 'px';
    });
    
    // Clear chat
    elements.clearChatBtn.addEventListener('click', clearChat);
    
    // New chat
    elements.newChatBtn.addEventListener('click', () => {
        if (confirm('Start a new chat? Current conversation will be saved.')) {
            initializeChat();
            loadChatHistory();
        }
    });
    
    // Logout
    elements.logoutBtn.addEventListener('click', logout);
    
    // Sidebar toggle
    elements.sidebarToggle.addEventListener('click', toggleSidebar);
    elements.mobileMenuBtn.addEventListener('click', toggleSidebar);
    
    // Suggestion buttons
    elements.suggestionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const query = btn.dataset.query;
            elements.chatInput.value = query;
            elements.charCount.textContent = query.length;
            sendMessage(query);
        });
    });
    
    // Close modal when clicking outside
    elements.loginModal.addEventListener('click', (e) => {
        if (e.target === elements.loginModal) {
            // Only close if not logged in
            if (!localStorage.getItem('access_token')) {
                // Don't close, user needs to login
            }
        }
    });
});

// Handle window resize for responsive design
window.addEventListener('resize', () => {
    if (window.innerWidth <= 768) {
        elements.sidebar.classList.add('collapsed');
    }
});

// Auto-reconnect WebSocket on visibility change
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && !isConnected && currentSessionId) {
        connectWebSocket();
    }
});