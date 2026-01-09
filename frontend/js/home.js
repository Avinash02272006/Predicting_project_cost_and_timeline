
const API_URL = 'http://127.0.0.1:5000/api';
let chartInstance1 = null;
let chartInstance2 = null;

// On Load
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    setupTheme();
});

// Logout
function logout() {
    fetch(`${API_URL}/logout`, { method: 'POST' }).then(() => {
        window.location.href = '../pages/index.html';
    });
}

// New Chat
function newProject() {
    document.getElementById('project-desc').value = '';
    document.getElementById('result-area').classList.remove('active');
    document.querySelector('.input-container').style.marginTop = 'auto';
}

// Load History
async function loadHistory() {
    const list = document.getElementById('history-list');
    list.innerHTML = '';

    const res = await fetch(`${API_URL}/history`);
    if (res.ok) {
        const data = await res.json();
        data.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.textContent = `Project ${item.id} - ${item.timestamp.substring(0, 10)}`;
            div.onclick = () => loadResult(item);
            list.appendChild(div);
        });
    }
}

// Submit Prediction
async function analyzeProject() {
    const desc = document.getElementById('project-desc').value;
    if (!desc) return;

    // UI Loading state could go here

    const res = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            description: desc,
            // Defaults as hidden params or could be extended
            project_type: "Web App",
            developers: 5,
            complexity: 5
        })
    });

    if (res.ok) {
        const data = await res.json();
        renderResult(data);
        loadHistory(); // Refresh sidebar
    }
}

// Render Results
function renderResult(data) {
    document.getElementById('result-area').classList.add('active');
    document.querySelector('.input-container').style.marginTop = '0'; // Move input up

    // Numbers
    document.getElementById('val-cost').textContent = `+${data.cost_overrun}%`;
    document.getElementById('val-time').textContent = `+${data.predicted_delay}d`;
    document.getElementById('val-sug').textContent = data.suggestion;

    // Charts
    renderCharts(data);
}

function loadResult(item) {
    document.getElementById('project-desc').value = item.project_description;
    renderResult({
        cost_overrun: item.predicted_cost,
        predicted_delay: item.predicted_timeline,
        suggestion: item.suggestion
    });
}

// Charts Logic
function renderCharts(data) {
    const ctx1 = document.getElementById('costChart').getContext('2d');
    const ctx2 = document.getElementById('timeChart').getContext('2d');

    if (chartInstance1) chartInstance1.destroy();
    if (chartInstance2) chartInstance2.destroy();

    // Pie Chart (Cost)
    chartInstance1 = new Chart(ctx1, {
        type: 'doughnut',
        data: {
            labels: ['Budget', 'Overrun'],
            datasets: [{
                data: [100, data.cost_overrun],
                backgroundColor: ['#3b82f6', '#ef4444'],
                borderWidth: 0
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });

    // Bar Chart (Time)
    chartInstance2 = new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: ['Est. Time', 'Delay'],
            datasets: [{
                label: 'Days',
                data: [30, data.predicted_delay], // 30 is dummy baseline
                backgroundColor: ['#10b981', '#f59e0b'],
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { beginAtZero: true } }
        }
    });
}

// Theme Toggle
function setupTheme() {
    const themeBtn = document.getElementById('theme-btn');
    themeBtn.onclick = () => {
        const body = document.body;
        const current = body.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        body.setAttribute('data-theme', next);
    };
}
