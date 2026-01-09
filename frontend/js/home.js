
const API_URL = '';
let chartInstance1 = null;
let chartInstance2 = null;

// On Load
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    setupTheme();
});

// Logout
function logout() {
    localStorage.removeItem('access_token');
    window.location.href = '/';
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

    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    const res = await fetch(`${API_URL}/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
        const data = await res.json();
        data.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.textContent = `${item.project_type} - ${item.timestamp.substring(0, 10)}`;
            div.onclick = () => loadResult(item);
            list.appendChild(div);
        });
    } else if (res.status === 401) {
        logout();
    }
}

// Submit Prediction
async function analyzeProject() {
    const desc = document.getElementById('project-desc').value;
    if (!desc) return;

    // UI Loading state could go here

    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    const res = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            project_description: desc,
            project_type: "Web App",
            complexity_score: 5,
            number_of_developers: 5,
            team_experience_rating: 3,
            dependency_delay_days: 5,
            resource_availability_ratio: 0.8,
            labour_cost_index: 1.5,
            historical_delay_days: 0
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
    document.getElementById('val-cost').textContent = `+${data.cost_overrun_percent}%`;
    document.getElementById('val-time').textContent = `+${data.predicted_delay_days}d`;
    // Suggestion might be nested or direct depending on API, backend returns risk_level/color/confidence mostly
    // But update Suggestion logic below to fetch separately or use what's available
    document.getElementById('val-sug').textContent = data.risk_level;

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
                data: [100, data.cost_overrun_percent],
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
                data: [30, data.predicted_delay_days], // 30 is dummy baseline
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
