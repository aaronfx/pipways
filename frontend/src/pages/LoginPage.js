
import { Component } from '../components/Component.js';
import { api } from '../api/client.js';
import { store } from '../state.js';
import { router } from '../router.js';

export class LoginPage extends Component {
    render() {
        return this.createElement(`
            <div class="auth-container">
                <div class="auth-card">
                    <div class="auth-header">
                        <h1><i class="fas fa-chart-line"></i> Pipways Pro</h1>
                        <p>Professional Trading Platform</p>
                    </div>

                    <form id="login-form" class="auth-form">
                        <div class="form-group">
                            <label class="form-label">Email</label>
                            <input type="email" name="email" class="form-input" required placeholder="trader@example.com">
                        </div>

                        <div class="form-group">
                            <label class="form-label">Password</label>
                            <input type="password" name="password" class="form-input" required placeholder="••••••••">
                        </div>

                        <div id="login-error" class="alert alert-error hidden"></div>

                        <button type="submit" class="btn btn-primary btn-block" id="login-btn">
                            <span>Login</span>
                        </button>
                    </form>

                    <div class="auth-footer">
                        <p>Don't have an account? <a href="#" id="show-register">Register</a></p>
                    </div>
                </div>
            </div>
        `);
    }

    bindEvents() {
        const form = this.element.querySelector('#login-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const btn = this.element.querySelector('#login-btn');
            const errorDiv = this.element.querySelector('#login-error');

            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
            errorDiv.classList.add('hidden');

            try {
                const formData = new FormData(form);
                const data = await api.login({
                    email: formData.get('email'),
                    password: formData.get('password')
                });

                // Store tokens - THE CRITICAL FIX
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);
                localStorage.setItem('user', JSON.stringify(data.user));

                store.setState({
                    token: data.access_token,
                    refreshToken: data.refresh_token,
                    user: data.user
                });

                api.showToast('Welcome back!', 'success');
                router.navigate('/');

            } catch (error) {
                errorDiv.textContent = error.message;
                errorDiv.classList.remove('hidden');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<span>Login</span>';
            }
        });
    }
}
