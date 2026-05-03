document.addEventListener("DOMContentLoaded", () => {
    const chatContainer = document.getElementById("chat-container");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const clearBtn = document.getElementById("clear-btn");
    const printBtn = document.getElementById("print-btn");
    const userId = "user_" + Date.now(); // simple session

    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // Display user message
        const userDiv = document.createElement("div");
        userDiv.className = "user-message";
        userDiv.innerHTML = `<div class="markdown-content">${marked.parse(message)}</div>`;
        chatContainer.appendChild(userDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        userInput.value = "";

        // Display bot typing
        const botDiv = document.createElement("div");
        botDiv.className = "bot-message";
        botDiv.innerHTML = `<div class="markdown-content text-textSecondary animate-pulse" style="font-size: 0.9rem;">Thinking...</div>`;
        chatContainer.appendChild(botDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({message, user_id: userId})
            });
            const data = await response.json();

            // Update bot reply
            botDiv.innerHTML = `<div class="markdown-content">${marked.parse(data.reply)}</div>`;

            // Render charts
            if (data.chart_data && Object.keys(data.chart_data).length > 0) {
                const chartWrapper = document.createElement("div");
                chartWrapper.className = "chart-wrapper";

                // Pie chart for cost
                const costCanvasWrapper = document.createElement("div");
                costCanvasWrapper.style.position = "relative";
                costCanvasWrapper.style.height = "320px";
                costCanvasWrapper.style.width = "100%";
                
                const costCanvas = document.createElement("canvas");
                costCanvasWrapper.appendChild(costCanvas);
                chartWrapper.appendChild(costCanvasWrapper);
                
                new Chart(costCanvas, {
                    type: "doughnut",
                    data: {
                        labels: data.chart_data.cost_labels,
                        datasets: [{
                            label: "Cost (INR)",
                            data: data.chart_data.cost_values,
                            backgroundColor: [
                                'rgba(59, 130, 246, 0.85)', // blue
                                'rgba(139, 92, 246, 0.85)', // purple
                                'rgba(236, 72, 153, 0.85)', // pink
                                'rgba(16, 185, 129, 0.85)'  // emerald
                            ],
                            borderColor: '#18181b',
                            borderWidth: 3,
                            hoverOffset: 12
                        }]
                    },
                    options: { 
                        animation: { animateScale: true, animateRotate: true, duration: 2500, easing: 'easeOutQuart' },
                        plugins: { legend: { position: "bottom", labels: { color: '#a1a1aa', font: { family: 'Inter', size: 12 }, padding: 20 } }, title: { display: true, text: "Cost Distribution", color: '#fff', font: { family: 'Inter', size: 15, weight: '600' }, padding: { bottom: 20 } } },
                        cutout: '75%',
                        layout: { padding: 10 },
                        maintainAspectRatio: false,
                        responsive: true
                    }
                });

                // Bar chart for timeline
                const timeCanvasWrapper = document.createElement("div");
                timeCanvasWrapper.style.position = "relative";
                timeCanvasWrapper.style.height = "320px";
                timeCanvasWrapper.style.width = "100%";
                
                const timeCanvas = document.createElement("canvas");
                timeCanvasWrapper.appendChild(timeCanvas);
                chartWrapper.appendChild(timeCanvasWrapper);
                
                new Chart(timeCanvas, {
                    type: "bar",
                    data: {
                        labels: data.chart_data.time_labels,
                        datasets: [{
                            label: "Timeline (weeks)",
                            data: data.chart_data.time_values,
                            backgroundColor: 'rgba(99, 102, 241, 0.85)', // Indigo
                            borderColor: 'rgba(99, 102, 241, 1)',
                            borderWidth: 1,
                            borderRadius: 6,
                            barThickness: 24,
                            hoverBackgroundColor: 'rgba(99, 102, 241, 1)'
                        }]
                    },
                    options: { 
                        animation: { duration: 2500, easing: 'easeOutQuart' },
                        indexAxis: 'y', 
                        plugins: { legend: { display: false }, title: { display: true, text: "Timeline Breakdown", color: '#fff', font: { family: 'Inter', size: 15, weight: '600' }, padding: { bottom: 20 } } }, 
                        scales: { 
                            x: { grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false }, ticks: { color: '#a1a1aa', font: { family: 'Inter' }, padding: 10 } },
                            y: { grid: { display: false }, ticks: { color: '#a1a1aa', font: { family: 'Inter' }, padding: 10 } }
                        },
                        layout: { padding: 10 },
                        maintainAspectRatio: false,
                        responsive: true
                    }
                });

                // 3. Radar Chart for Risk Profile
                const radarCanvasWrapper = document.createElement("div");
                radarCanvasWrapper.style.position = "relative";
                radarCanvasWrapper.style.height = "320px";
                radarCanvasWrapper.style.width = "100%";
                
                const radarCanvas = document.createElement("canvas");
                radarCanvasWrapper.appendChild(radarCanvas);
                chartWrapper.appendChild(radarCanvasWrapper);
                
                new Chart(radarCanvas, {
                    type: "radar",
                    data: {
                        labels: data.chart_data.radar_labels,
                        datasets: [{
                            label: "Risk Index",
                            data: data.chart_data.radar_values,
                            backgroundColor: 'rgba(236, 72, 153, 0.2)', // pink transparent
                            borderColor: 'rgba(236, 72, 153, 1)',
                            pointBackgroundColor: 'rgba(236, 72, 153, 1)',
                            borderWidth: 2
                        }]
                    },
                    options: { 
                        animation: { duration: 2500, easing: 'easeOutQuart' },
                        plugins: { legend: { display: false }, title: { display: true, text: "Project Risk Matrix", color: '#fff', font: { family: 'Inter', size: 15, weight: '600' }, padding: { bottom: 20 } } }, 
                        scales: { 
                            r: { 
                                grid: { color: 'rgba(255,255,255,0.1)' },
                                pointLabels: { color: '#a1a1aa', font: { family: 'Inter' } },
                                ticks: { display: false, max: 100 }
                            }
                        },
                        layout: { padding: 10 },
                        maintainAspectRatio: false,
                        responsive: true
                    }
                });

                // 4. Line Chart for Infrastructure Cost Scaling
                const lineCanvasWrapper = document.createElement("div");
                lineCanvasWrapper.style.position = "relative";
                lineCanvasWrapper.style.height = "320px";
                lineCanvasWrapper.style.width = "100%";
                
                const lineCanvas = document.createElement("canvas");
                lineCanvasWrapper.appendChild(lineCanvas);
                chartWrapper.appendChild(lineCanvasWrapper);
                
                new Chart(lineCanvas, {
                    type: "line",
                    data: {
                        labels: data.chart_data.line_labels,
                        datasets: [{
                            label: "Infra Cost (INR)",
                            data: data.chart_data.line_values,
                            backgroundColor: 'rgba(16, 185, 129, 0.2)', // emerald
                            borderColor: 'rgba(16, 185, 129, 1)',
                            pointBackgroundColor: 'rgba(16, 185, 129, 1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: { 
                        animation: { duration: 2500, easing: 'easeOutQuart' },
                        plugins: { legend: { display: false }, title: { display: true, text: "6-Month Infra Scaling Cost", color: '#fff', font: { family: 'Inter', size: 15, weight: '600' }, padding: { bottom: 20 } } }, 
                        scales: { 
                            x: { grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false }, ticks: { color: '#a1a1aa', font: { family: 'Inter' }, padding: 10 } },
                            y: { grid: { display: false }, ticks: { color: '#a1a1aa', font: { family: 'Inter' }, padding: 10 } }
                        },
                        layout: { padding: 10 },
                        maintainAspectRatio: false,
                        responsive: true
                    }
                });

                botDiv.appendChild(chartWrapper);
                chatContainer.scrollTop = chatContainer.scrollHeight;
                
                // Show print button when final report is generated
                printBtn.classList.remove("hidden");

                // Save to History
                let history = JSON.parse(localStorage.getItem('ai_reports') || '[]');
                history.unshift({
                    id: Date.now(),
                    date: new Date().toLocaleDateString(),
                    content: marked.parse(data.reply)
                });
                localStorage.setItem('ai_reports', JSON.stringify(history));
                renderHistory();
            }

        } catch (err) {
            botDiv.innerHTML = `<div class="markdown-content">⚠️ Unable to reach server. Try again.</div>`;
            console.error(err);
        }
    }

    sendBtn.addEventListener("click", sendMessage);
    userInput.addEventListener("keydown", (e) => { if(e.key==="Enter"){e.preventDefault(); sendMessage();} });

    clearBtn.addEventListener("click", async () => {
        if (!confirm("Are you sure you want to clear the conversation and start over?")) return;
        try {
            await fetch("/clear", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({user_id: userId})
            });
            chatContainer.innerHTML = `
        <div class="bot-message mt-8">
            <div class="markdown-content">
                Hello. I am the AI Estimator. I can accurately forecast the cost and timeline for your software project.<br><br>
                Please describe your project, and I'll ask a few clarifying questions if needed.
            </div>
        </div>`;
            printBtn.classList.add("hidden");
        } catch(e) {
            console.error(e);
        }
    });

    printBtn.addEventListener("click", () => {
        window.print();
    });

    // Sidebar History Logic
    const newChatBtn = document.getElementById("new-chat-btn");
    if (newChatBtn) {
        newChatBtn.addEventListener("click", () => clearBtn.click());
    }

    const historyList = document.getElementById("history-list");
    function renderHistory() {
        if (!historyList) return;
        let history = JSON.parse(localStorage.getItem('ai_reports') || '[]');
        historyList.innerHTML = '';
        history.forEach((item) => {
            const btn = document.createElement("button");
            btn.className = "w-full text-left p-3 mb-2 rounded-xl bg-background hover:bg-surfaceHover border border-transparent hover:border-border transition-colors text-sm text-textSecondary flex justify-between items-center group";
            btn.innerHTML = `<span class="truncate pr-2 text-white group-hover:text-blue-400 transition-colors">📋 Project Estimate</span><span class="text-xs opacity-50 shrink-0">${item.date}</span>`;
            btn.onclick = () => {
                chatContainer.innerHTML = `<div class="bot-message mt-8"><div class="markdown-content">${item.content}</div></div>`;
                printBtn.classList.remove("hidden");
                chatContainer.scrollTop = 0;
            };
            historyList.appendChild(btn);
        });
    }
    renderHistory();
});
