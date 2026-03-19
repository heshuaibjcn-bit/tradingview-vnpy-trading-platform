// Dashboard Configuration
const CONFIG = {
    WS_URL: 'ws://localhost:8765',
    API_URL: 'http://localhost:8000',
    REFRESH_INTERVAL: 5000, // 5 seconds
    MAX_MESSAGES: 100,
    CHART_HISTORY: 20
};

// State
let ws = null;
let agents = {};
let messageHistory = [];
let throughputData = [];
let healthData = { healthy: 0, unhealthy: 0, unknown: 0 };
let throughputChart = null;
let healthChart = null;
let connectionStatus = false;

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    connectWebSocket();
    loadInitialData();

    // Set up periodic refresh
    setInterval(refreshData, CONFIG.REFRESH_INTERVAL);

    // Set up search filter
    document.getElementById('message-search').addEventListener('input', filterMessages);
    document.getElementById('message-type-filter').addEventListener('change', filterMessages);
});

// WebSocket Connection
function connectWebSocket() {
    ws = new WebSocket(CONFIG.WS_URL);

    ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus(true);
        // Request initial data
        sendMessage({ type: 'get_agents' });
        sendMessage({ type: 'get_health' });
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus(false);
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus(false);
    };
}

function sendMessage(message) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(message));
    }
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'agent_status':
            updateAgents(data.data);
            break;
        case 'agent_health':
            updateHealthSummary(data.data);
            break;
        case 'agent_message':
            addMessage(data.data);
            break;
        case 'pong':
            // Heartbeat response
            break;
        default:
            console.log('Unknown message type:', data.type);
    }
}

function setConnectionStatus(connected) {
    connectionStatus = connected;
    const indicator = document.getElementById('status-indicator');
    const text = document.getElementById('status-text');

    if (connected) {
        indicator.classList.remove('bg-red-500');
        indicator.classList.add('bg-green-500', 'status-running');
        text.textContent = 'Connected';
    } else {
        indicator.classList.remove('bg-green-500', 'status-running');
        indicator.classList.add('bg-red-500');
        text.textContent = 'Disconnected';
    }
}

// API Calls
async function fetchAPI(endpoint) {
    try {
        const response = await fetch(`${CONFIG.API_URL}${endpoint}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        return null;
    }
}

async function loadInitialData() {
    // Load agents
    const agentsData = await fetchAPI('/api/agents');
    if (agentsData && agentsData.agents) {
        updateAgents(agentsData.agents);
    }

    // Load metrics
    const metricsData = await fetchAPI('/api/agents/metrics');
    if (metricsData) {
        updateMetrics(metricsData);
    }

    // Load message history
    const historyData = await fetchAPI('/api/agents/messages/history?limit=50');
    if (historyData && historyData.messages) {
        messageHistory = historyData.messages;
        renderMessageHistory();
    }
}

function refreshData() {
    if (!connectionStatus) return;

    sendMessage({ type: 'get_agents' });
    sendMessage({ type: 'get_health' });

    // Also fetch via API as backup
    loadInitialData();
}

// Update Functions
function updateAgents(data) {
    if (data.agents) {
        agents = data.agents;
    } else {
        agents = data;
    }

    renderAgents();
    updateSystemOverview();
}

function updateHealthSummary(data) {
    healthData = data;
    updateHealthChart();
    document.getElementById('healthy-agents').textContent = data.healthy || 0;
}

function updateMetrics(data) {
    if (data.uptime_seconds) {
        document.getElementById('uptime').textContent = formatUptime(data.uptime_seconds);
    }

    if (data.total_messages) {
        updateThroughputChart(data.total_messages, data.messages_per_second || 0);
    }
}

function addMessage(data) {
    const message = {
        timestamp: data.timestamp || new Date().toISOString(),
        msg_type: data.msg_type,
        sender: data.sender,
        content: data.content
    };

    messageHistory.unshift(message);
    if (messageHistory.length > CONFIG.MAX_MESSAGES) {
        messageHistory.pop();
    }

    renderMessageFlow(message);
    renderMessageHistory();
}

// Render Functions
function renderAgents() {
    const container = document.getElementById('agents-list');

    if (Object.keys(agents).length === 0) {
        container.innerHTML = '<div class="text-center text-gray-500 py-8">No agents found</div>';
        return;
    }

    container.innerHTML = Object.entries(agents).map(([name, agent]) => `
        <div class="agent-card bg-gray-700 rounded-lg p-4 cursor-pointer" onclick="showAgentDetails('${name}')">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <div class="w-3 h-3 rounded-full ${getStatusColor(agent.status, agent.health)}"></div>
                    <div>
                        <h3 class="font-semibold">${agent.name || name}</h3>
                        <p class="text-sm text-gray-400">${agent.description || 'No description'}</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-sm ${agent.status === 'running' ? 'text-green-500' : 'text-gray-400'}">
                        ${agent.status || 'unknown'}
                    </p>
                    <p class="text-xs text-gray-500">${agent.health || 'unknown'}</p>
                </div>
            </div>
            <div class="mt-3 grid grid-cols-3 gap-2 text-xs">
                <div>
                    <span class="text-gray-500">Messages:</span>
                    <span class="ml-1">${agent.message_count || 0}</span>
                </div>
                <div>
                    <span class="text-gray-500">Errors:</span>
                    <span class="ml-1">${agent.error_count || 0}</span>
                </div>
                <div>
                    <span class="text-gray-500">Uptime:</span>
                    <span class="ml-1">${formatUptime(agent.uptime_seconds || 0)}</span>
                </div>
            </div>
        </div>
    `).join('');
}

function updateSystemOverview() {
    const total = Object.keys(agents).length;
    const running = Object.values(agents).filter(a => a.status === 'running').length;
    const healthy = Object.values(agents).filter(a => a.health === 'healthy').length;

    document.getElementById('total-agents').textContent = total;
    document.getElementById('running-agents').textContent = running;
    document.getElementById('healthy-agents').textContent = healthy;
}

function renderMessageFlow(message) {
    const container = document.getElementById('message-flow');

    // Remove "waiting" message if present
    if (container.querySelector('.text-center')) {
        container.innerHTML = '';
    }

    const messageEl = document.createElement('div');
    messageEl.className = 'message-item bg-gray-700 rounded p-3 text-sm';
    messageEl.innerHTML = `
        <div class="flex items-center justify-between mb-1">
            <span class="font-medium text-blue-400">${message.msg_type}</span>
            <span class="text-xs text-gray-500">${formatTime(message.timestamp)}</span>
        </div>
        <div class="text-gray-400">
            <span class="text-green-400">${message.sender}</span>
            </div>
        <div class="text-gray-300 mt-1 truncate">${JSON.stringify(message.content).substring(0, 100)}</div>
    `;

    container.insertBefore(messageEl, container.firstChild);

    // Keep only last 20 messages in flow
    while (container.children.length > 20) {
        container.removeChild(container.lastChild);
    }
}

function renderMessageHistory() {
    const container = document.getElementById('message-history');
    const searchTerm = document.getElementById('message-search').value.toLowerCase();
    const typeFilter = document.getElementById('message-type-filter').value;

    const filteredMessages = messageHistory.filter(msg => {
        const matchesSearch = !searchTerm ||
            JSON.stringify(msg).toLowerCase().includes(searchTerm);
        const matchesType = !typeFilter || msg.msg_type === typeFilter;
        return matchesSearch && matchesType;
    });

    if (filteredMessages.length === 0) {
        container.innerHTML = '<tr><td colspan="4" class="text-center text-gray-500 py-4">No messages found</td></tr>';
        return;
    }

    container.innerHTML = filteredMessages.slice(0, 50).map(msg => `
        <tr class="border-b border-gray-700 hover:bg-gray-700">
            <td class="py-3 px-4 text-gray-400">${formatTime(msg.timestamp)}</td>
            <td class="py-3 px-4">
                <span class="px-2 py-1 rounded text-xs bg-blue-900 text-blue-300">${msg.msg_type}</span>
            </td>
            <td class="py-3 px-4 text-green-400">${msg.sender || '-'}</td>
            <td class="py-3 px-4 text-gray-300 truncate max-w-xs">${JSON.stringify(msg.content).substring(0, 100)}</td>
        </tr>
    `).join('');
}

function filterMessages() {
    renderMessageHistory();
}

function clearMessages() {
    document.getElementById('message-flow').innerHTML = '<div class="text-center text-gray-500 py-8">Waiting for messages...</div>';
}

// Charts
function initializeCharts() {
    // Throughput Chart
    const throughputCtx = document.getElementById('throughput-chart').getContext('2d');
    throughputChart = new Chart(throughputCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Messages/Second',
                data: [],
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#9CA3AF' }
                },
                x: {
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#9CA3AF' }
                }
            },
            plugins: {
                legend: { labels: { color: '#F3F4F6' } }
            }
        }
    });

    // Health Chart
    const healthCtx = document.getElementById('health-chart').getContext('2d');
    healthChart = new Chart(healthCtx, {
        type: 'doughnut',
        data: {
            labels: ['Healthy', 'Unhealthy', 'Unknown'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: [
                    'rgb(34, 197, 94)',
                    'rgb(239, 68, 68)',
                    'rgb(156, 163, 175)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#F3F4F6' }
                }
            }
        }
    });
}

function updateThroughputChart(total, rate) {
    const now = new Date().toLocaleTimeString();

    throughputChart.data.labels.push(now);
    throughputChart.data.datasets[0].data.push(rate);

    // Keep only last N data points
    if (throughputChart.data.labels.length > CONFIG.CHART_HISTORY) {
        throughputChart.data.labels.shift();
        throughputChart.data.datasets[0].data.shift();
    }

    throughputChart.update();
}

function updateHealthChart() {
    healthChart.data.datasets[0].data = [
        healthData.healthy || 0,
        healthData.unhealthy || 0,
        healthData.unknown || 0
    ];
    healthChart.update();
}

// Modal
function showAgentDetails(agentName) {
    const agent = agents[agentName];
    if (!agent) return;

    const modal = document.getElementById('agent-modal');
    const title = document.getElementById('modal-title');
    const content = document.getElementById('modal-content');

    title.textContent = agent.name || agentName;
    content.innerHTML = `
        <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <p class="text-gray-400 text-sm">Status</p>
                    <p class="text-lg font-semibold ${agent.status === 'running' ? 'text-green-500' : 'text-gray-300'}">
                        ${agent.status || 'unknown'}
                    </p>
                </div>
                <div>
                    <p class="text-gray-400 text-sm">Health</p>
                    <p class="text-lg font-semibold">${agent.health || 'unknown'}</p>
                </div>
                <div>
                    <p class="text-gray-400 text-sm">Message Count</p>
                    <p class="text-lg font-semibold">${agent.message_count || 0}</p>
                </div>
                <div>
                    <p class="text-gray-400 text-sm">Error Count</p>
                    <p class="text-lg font-semibold ${agent.error_count > 0 ? 'text-red-500' : ''}">${agent.error_count || 0}</p>
                </div>
                <div>
                    <p class="text-gray-400 text-sm">Uptime</p>
                    <p class="text-lg font-semibold">${formatUptime(agent.uptime_seconds || 0)}</p>
                </div>
                <div>
                    <p class="text-gray-400 text-sm">Started At</p>
                    <p class="text-lg font-semibold">${agent.started_at ? new Date(agent.started_at).toLocaleString() : 'N/A'}</p>
                </div>
            </div>

            ${agent.description ? `
                <div>
                    <p class="text-gray-400 text-sm mb-1">Description</p>
                    <p class="text-gray-200">${agent.description}</p>
                </div>
            ` : ''}

            <div class="flex gap-2 mt-4">
                ${agent.status !== 'running' ? `
                    <button onclick="controlAgent('${agentName}', 'start')" class="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition">
                        Start
                    </button>
                ` : `
                    <button onclick="controlAgent('${agentName}', 'stop')" class="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition">
                        Stop
                    </button>
                    <button onclick="controlAgent('${agentName}', 'restart')" class="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded-lg transition">
                        Restart
                    </button>
                `}
            </div>
        </div>
    `;

    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeModal() {
    const modal = document.getElementById('agent-modal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

async function controlAgent(agentName, action) {
    const response = await fetch(`${CONFIG.API_URL}/api/agents/${agentName}/${action}`, {
        method: 'POST'
    });

    if (response.ok) {
        // Refresh agent data
        setTimeout(() => {
            sendMessage({ type: 'get_agents' });
            closeModal();
        }, 500);
    } else {
        alert(`Failed to ${action} agent`);
    }
}

// Utility Functions
function getStatusColor(status, health) {
    if (status === 'running') {
        return health === 'healthy' ? 'bg-green-500' : 'bg-yellow-500';
    }
    return 'bg-gray-500';
}

function formatTime(timestamp) {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
}

function formatUptime(seconds) {
    if (seconds < 60) return `${Math.floor(seconds)}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
    return `${Math.floor(seconds / 86400)}d`;
}

// Close modal on outside click
document.getElementById('agent-modal').addEventListener('click', (e) => {
    if (e.target.id === 'agent-modal') {
        closeModal();
    }
});
