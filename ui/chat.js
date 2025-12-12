/**
 * WealthAdvisor AI - Chat Interface JavaScript
 */

const API_BASE = 'http://localhost:5000/api';
let userId = 'user_' + Math.random().toString(36).substr(2, 9);
let portfolio = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    checkApiHealth();
    autoResizeTextarea();
});

// Navigation
function setupNavigation() {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            switchView(view);

            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
}

function switchView(viewName) {
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    document.getElementById(`${viewName}-view`).classList.add('active');
}

// API Health Check
async function checkApiHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        console.log('API Status:', data);
    } catch (error) {
        console.warn('API not available. Make sure the Flask server is running.');
    }
}

// Chat Functions
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function autoResizeTextarea() {
    const textarea = document.getElementById('chat-input');
    textarea.addEventListener('input', () => {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    });
}

function sendSuggestion(text) {
    document.getElementById('chat-input').value = text;
    sendMessage();
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message) return;

    // Clear input
    input.value = '';
    input.style.height = 'auto';

    // Add user message to chat
    addMessage('user', message);

    // Show loading
    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                user_id: userId
            })
        });

        const data = await response.json();

        if (data.error) {
            addMessage('assistant', `⚠️ Error: ${data.error}`);
        } else {
            addMessage('assistant', data.response);
        }
    } catch (error) {
        addMessage('assistant', `⚠️ Could not connect to the server. Please make sure the Flask API is running.\n\nRun: \`python api/app.py\``);
    } finally {
        showLoading(false);
    }
}

function addMessage(role, content) {
    const container = document.getElementById('chat-container');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = role === 'user' ? '👤' : '🤖';

    // Parse markdown-like formatting
    const formattedContent = formatContent(content);

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">${formattedContent}</div>
    `;

    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

function formatContent(content) {
    // Convert markdown-like syntax to HTML
    let html = content
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Line breaks
        .replace(/\n/g, '<br>')
        // Lists
        .replace(/^• (.*?)$/gm, '<li>$1</li>')
        .replace(/^- (.*?)$/gm, '<li>$1</li>')
        // Headers
        .replace(/^### (.*?)$/gm, '<h4>$1</h4>')
        .replace(/^## (.*?)$/gm, '<h3>$1</h3>')
        // Code blocks
        .replace(/`(.*?)`/g, '<code>$1</code>');

    // Wrap consecutive li items in ul
    html = html.replace(/(<li>.*?<\/li>)+/g, (match) => `<ul>${match}</ul>`);

    // Ensure content is wrapped in paragraph if no block elements
    if (!html.includes('<h') && !html.includes('<ul') && !html.includes('<li')) {
        html = `<p>${html}</p>`;
    }

    return html;
}

async function clearConversation() {
    try {
        await fetch(`${API_BASE}/clear`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
    } catch (error) {
        console.log('Could not clear server conversation');
    }

    // Clear UI
    const container = document.getElementById('chat-container');
    container.innerHTML = `
        <div class="message assistant">
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <p>👋 Conversation cleared! How can I help you with your wealth management needs?</p>
            </div>
        </div>
    `;
}

// Portfolio Functions
function addHolding() {
    const symbol = document.getElementById('holding-symbol').value.trim().toUpperCase();
    const name = document.getElementById('holding-name').value.trim();
    const value = parseFloat(document.getElementById('holding-value').value);
    const assetClass = document.getElementById('holding-class').value;
    const sector = document.getElementById('holding-sector').value;
    const geography = document.getElementById('holding-geography').value;

    if (!symbol || !value) {
        alert('Please enter at least symbol and value');
        return;
    }

    portfolio.push({
        symbol,
        name: name || symbol,
        value,
        asset_class: assetClass,
        sector: sector || 'unknown',
        geography: geography || 'unknown'
    });

    updatePortfolioTable();

    // Clear inputs
    document.getElementById('holding-symbol').value = '';
    document.getElementById('holding-name').value = '';
    document.getElementById('holding-value').value = '';
}

function updatePortfolioTable() {
    const tbody = document.getElementById('holdings-tbody');

    if (portfolio.length === 0) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="5">No holdings added yet</td></tr>';
        return;
    }

    const totalValue = portfolio.reduce((sum, h) => sum + h.value, 0);

    tbody.innerHTML = portfolio.map((h, idx) => `
        <tr>
            <td><strong>${h.symbol}</strong></td>
            <td>${h.name}</td>
            <td>$${h.value.toLocaleString()} (${((h.value / totalValue) * 100).toFixed(1)}%)</td>
            <td>${h.asset_class}</td>
            <td>
                <button onclick="removeHolding(${idx})" class="secondary-btn" style="padding: 8px 16px; font-size: 13px;">
                    ✕
                </button>
            </td>
        </tr>
    `).join('');
}

function removeHolding(index) {
    portfolio.splice(index, 1);
    updatePortfolioTable();
}

async function analyzePortfolio(type) {
    if (portfolio.length === 0) {
        alert('Please add some holdings first');
        return;
    }

    showLoading(true);

    try {
        let endpoint, message;

        switch (type) {
            case 'risk':
                endpoint = '/risk-assessment';
                message = 'Analyzing portfolio risk...';
                break;
            case 'diversification':
                endpoint = '/diversification';
                message = 'Checking diversification...';
                break;
            case 'rebalance':
                // Use chat API for rebalancing suggestions
                switchView('chat');
                const portfolioJson = JSON.stringify(portfolio);
                document.getElementById('chat-input').value = `Suggest rebalancing for my portfolio: ${portfolioJson}`;
                showLoading(false);
                sendMessage();
                return;
        }

        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ portfolio })
        });

        const data = await response.json();

        // Switch to chat view and show results
        switchView('chat');
        document.querySelectorAll('.nav-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.view === 'chat');
        });

        if (data.error) {
            addMessage('assistant', `⚠️ Error: ${data.error}`);
        } else {
            addMessage('assistant', data.summary);
        }

    } catch (error) {
        addMessage('assistant', `⚠️ Error: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

// Tools Functions
function openTool(toolName) {
    switch (toolName) {
        case 'risk-questionnaire':
            document.getElementById('risk-questionnaire-modal').classList.add('active');
            break;
        case 'strategy-planner':
            switchView('chat');
            document.querySelectorAll('.nav-btn').forEach(b => {
                b.classList.toggle('active', b.dataset.view === 'chat');
            });
            document.getElementById('chat-input').value = 'Help me design an investment strategy for retirement';
            sendMessage();
            break;
        case 'calculator':
            switchView('chat');
            document.querySelectorAll('.nav-btn').forEach(b => {
                b.classList.toggle('active', b.dataset.view === 'chat');
            });
            addMessage('assistant', `🧮 **Investment Calculator**\n\nTell me:\n• Your current savings\n• Monthly contribution\n• Years until goal\n\nAnd I'll project your future portfolio value!`);
            break;
        case 'learn':
            switchView('chat');
            document.querySelectorAll('.nav-btn').forEach(b => {
                b.classList.toggle('active', b.dataset.view === 'chat');
            });
            addMessage('assistant', `📚 **Financial Learning Center**\n\nI can explain:\n• **Risk Metrics**: VaR, Sharpe Ratio, Volatility\n• **Asset Allocation**: How to diversify\n• **Investment Strategies**: Value, Growth, Index\n• **Retirement Planning**: 401k, IRA, withdrawal strategies\n\nWhat would you like to learn about?`);
            break;
    }
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

async function submitRiskAssessment() {
    const questionnaire = {
        age: parseInt(document.getElementById('q-age').value),
        investment_experience: document.getElementById('q-experience').value,
        time_horizon: parseInt(document.getElementById('q-horizon').value),
        loss_reaction: document.getElementById('q-reaction').value,
        goal: document.getElementById('q-goal').value
    };

    closeModal('risk-questionnaire-modal');
    switchView('chat');
    document.querySelectorAll('.nav-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.view === 'chat');
    });

    // Send to chat
    addMessage('user', `Please assess my risk tolerance based on my profile: Age ${questionnaire.age}, ${questionnaire.investment_experience} experience, ${questionnaire.time_horizon} year horizon, would ${questionnaire.loss_reaction.replace('_', ' ')} if market drops 20%, goal is ${questionnaire.goal.replace('_', ' ')}`);

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: `Assess my risk tolerance: ${JSON.stringify(questionnaire)}`,
                user_id: userId
            })
        });

        const data = await response.json();
        addMessage('assistant', data.response || data.error);
    } catch (error) {
        addMessage('assistant', `⚠️ Error: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

// Loading
function showLoading(show) {
    document.getElementById('loading-overlay').classList.toggle('active', show);
    document.getElementById('send-btn').disabled = show;
}

// Handle clicks outside modals to close them
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});
