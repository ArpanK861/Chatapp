const API_URL = window.location.origin;
const WS_URL = (window.location.protocol === 'https:') ? 'wss://' + window.location.host : 'ws://' + window.location.host;
let token = null;
let username = null;
let room = null;
let socket = null;
let shouldReconnect = true;

async function register() {
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    if (!user || !pass) { alert('Please enter username and password'); return; }
    try {
        const response = await fetch(`${API_URL}/api/register/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: user, password: pass})
        });
        const data = await response.json();
        if (response.ok) {
            token = data.token;
            username = data.username;
            room = document.getElementById('room').value;
            showAuthStatus('Registration successful! Connecting...', 'success');
            setTimeout(connectWebSocket, 1000);
        } else {
            showAuthStatus('Registration failed: ' + JSON.stringify(data), 'error');
        }
    } catch (error) { showAuthStatus('Error: ' + error.message, 'error'); }
}

async function login() {
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    if (!user || !pass) { alert('Please enter username and password'); return; }
    try {
        const response = await fetch(`${API_URL}/api/login/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: user, password: pass})
        });
        const data = await response.json();
        if (response.ok) {
            token = data.token;
            username = data.username;
            room = document.getElementById('room').value;
            showAuthStatus('Login successful! Connecting...', 'success');
            setTimeout(connectWebSocket, 1000);
        } else {
            showAuthStatus('Login failed: ' + data.error, 'error');
        }
    } catch (error) { showAuthStatus('Error: ' + error.message, 'error'); }
}

function connectWebSocket() {
    document.getElementById('authSection').classList.add('hidden');
    document.getElementById('chatSection').classList.remove('hidden');
    shouldReconnect = true;
    if (!token || !room) {
        console.error("Connection failed: Token or Room is missing.");
        return; 
    }
    const fullUrl = WS_URL + '/ws/chat/' + room + '/?token=' + token;
    socket = new WebSocket(fullUrl);
    socket.onopen = () => {
        updateStatus('Connected', true);
        loadHistory();
    };
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'user_count') {
            document.getElementById('userCount').textContent = data.count;
            return;
        }
        if (data.type === 'typing_notification') {
            const typingIndicator = document.getElementById('typingIndicator');
            if (data.is_typing && data.user !== username) {
                typingIndicator.textContent = `${data.user} is typing...`;
                typingIndicator.classList.remove('hidden');
            } else {
                typingIndicator.classList.add('hidden');
            }
            return;
        }
        if (data.error) { alert(data.error); return; }
        if (data.type === 'message') {
            document.getElementById('typingIndicator').classList.add('hidden');
            addMessage(data.sender, data.message, data.sender === username);
        }
    };
    socket.onclose = (e) => {
    updateStatus('Disconnected', false);
    if (shouldReconnect) {
            setTimeout(connectWebSocket, 2000);
        }
    };
}

function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message) return;
    socket.send(JSON.stringify({message: message}));
    input.value = '';
}

let isTyping = false;
let typingTimeout;

function handleTyping() {
    if (!isTyping) {
        isTyping = true;
        socket.send(JSON.stringify({ typing: true }));
    }
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        isTyping = false;
        socket.send(JSON.stringify({ typing: false }));
    }, 2000); 
}

function addMessage(sender, text, isOwn) {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isOwn ? 'own' : 'other'}`;
    const now = new Date().toLocaleTimeString();
    
    // Create elements safely to prevent XSS attacks
    const senderDiv = document.createElement('div');
    senderDiv.className = 'sender';
    senderDiv.textContent = sender;
    
    const textDiv = document.createElement('div');
    textDiv.textContent = text;
    
    const timestampDiv = document.createElement('div');
    timestampDiv.className = 'timestamp';
    timestampDiv.textContent = now;
    
    messageDiv.appendChild(senderDiv);
    messageDiv.appendChild(textDiv);
    messageDiv.appendChild(timestampDiv);
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function loadHistory() {
    try {
        const response = await fetch(`${API_URL}/api/messages/${room}/?page=1&page_size=50`);
        const data = await response.json();
        document.getElementById('messages').innerHTML = '';
        if (data.results && data.results.length > 0) {
            data.results.reverse().forEach(msg => {
                addMessage(msg.sender, msg.text, msg.sender === username);
            });
        }
    } catch (error) { console.error('Failed to load history:', error); }
}

function updateStatus(message, connected) {
    const status = document.getElementById('connectionStatus');
    status.textContent = message;
    status.className = `status ${connected ? 'connected' : 'disconnected'}`;
}

function showAuthStatus(message, type) {
    const status = document.getElementById('authStatus');
    status.textContent = message;
    status.style.padding = '10px';
    status.style.marginTop = '10px';
    status.style.borderRadius = '8px';
    status.style.background = type === 'success' ? '#d4edda' : '#f8d7da';
    status.style.color = type === 'success' ? '#155724' : '#721c24';
}

function logout() {
    shouldReconnect = false;
    const userCountElem = document.getElementById('userCount');
    if (userCountElem) userCountElem.textContent = '0';
    if (socket) socket.close();
    document.getElementById('authSection').classList.remove('hidden');
    document.getElementById('chatSection').classList.add('hidden');
    document.getElementById('authStatus').textContent = '';
    document.getElementById('authStatus').style.padding = '0';
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
    document.getElementById('room').value = 'general';
    token = null;
    username = null;
    room = null;
    updateStatus('Logged out', false);
}