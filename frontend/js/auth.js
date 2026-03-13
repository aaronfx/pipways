// Authentication Logic - Preserved Exactly

const API_BASE = window.location.origin;

function showError(message) {
    const errorDiv = document.getElementById('auth-error');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
        setTimeout(() => errorDiv.classList.add('hidden'), 5000);
    }
}

async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('login-email')?.value;
    const password = document.getElementById('login-password')?.value;
    
    if (!email || !password) {
        showError('Please fill in all fields');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);
        
        const res = await fetch(`${API_BASE}/auth/token`, {
            method: 'POST',
            body: formData
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Login failed');
        }
        
        const data = await res.json();
        
        // Store auth data
        localStorage.setItem('pipways_token', data.access_token);
        localStorage.setItem('pipways_user', JSON.stringify(data.user));
        
        // Redirect to dashboard
        window.location.href = '/dashboard.html';
        
    } catch (e) {
        showError(e.message);
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const email = document.getElementById('reg-email')?.value;
    const password = document.getElementById('reg-password')?.value;
    const full_name = document.getElementById('reg-name')?.value;
    
    if (!email || !password) {
        showError('Please fill in required fields');
        return;
    }
    
    const data = {
        email: email,
        password: password,
        full_name: full_name || ''
    };
    
    try {
        const res = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Registration failed');
        }
        
        const result = await res.json();
        
        localStorage.setItem('pipways_token', result.access_token);
        localStorage.setItem('pipways_user', JSON.stringify(result.user));
        
        window.location.href = '/dashboard.html';
        
    } catch (e) {
        showError(e.message);
    }
}

function logout() {
    localStorage.removeItem('pipways_token');
    localStorage.removeItem('pipways_user');
    window.location.href = '/';
}
