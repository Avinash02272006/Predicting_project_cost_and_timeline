
const API_URL = 'http://127.0.0.1:8000';

async function login(event) {
    event.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorMsg = document.getElementById('error-msg');

    try {
        const res = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        if (res.ok) {
            window.location.href = '/dashboard';
        } else {
            const data = await res.json();
            errorMsg.textContent = data.message || "Login failed";
            errorMsg.style.display = 'block';
        }
    } catch (e) {
        errorMsg.textContent = "Connection error";
        errorMsg.style.display = 'block';
    }
}

async function register(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
        const res = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });

        if (res.ok) {
            window.location.href = '/login';
        } else {
            alert("Registration failed. Username/Email may exist.");
        }
    } catch (e) {
        alert("Connection error");
    }
}
