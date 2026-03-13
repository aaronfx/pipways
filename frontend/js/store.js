/**
 * Global state management for Pipways
 */
const Store = {
    state: {
        user: null,
        token: localStorage.getItem('pipways_token'),
        loading: false,
        notifications: []
    },

    listeners: new Set(),

    setState(key, value) {
        this.state[key] = value;
        this.notify(key, value);
        
        // Persist auth data
        if (key === 'token') {
            if (value) {
                localStorage.setItem('pipways_token', value);
            } else {
                localStorage.removeItem('pipways_token');
            }
        }
        if (key === 'user') {
            if (value) {
                localStorage.setItem('pipways_user', JSON.stringify(value));
            } else {
                localStorage.removeItem('pipways_user');
            }
        }
    },

    getToken() {
        return this.state.token || localStorage.getItem('pipways_token');
    },

    getUser() {
        if (this.state.user) return this.state.user;
        const stored = localStorage.getItem('pipways_user');
        return stored ? JSON.parse(stored) : null;
    },

    setUser(user, token) {
        this.setState('user', user);
        if (token) this.setState('token', token);
        
        // Set admin status
        if (user) {
            this.state.isAdmin = user.is_admin || user.role === 'admin' || false;
        }
    },

    logout() {
        this.setState('user', null);
        this.setState('token', null);
        this.state.isAdmin = false;
        localStorage.removeItem('pipways_token');
        localStorage.removeItem('pipways_user');
    },

    isAuthenticated() {
        return !!this.getToken();
    },

    subscribe(callback) {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    },

    notify(key, value) {
        this.listeners.forEach(cb => cb(key, value));
    },

    // Initialize from localStorage
    init() {
        const token = localStorage.getItem('pipways_token');
        const user = localStorage.getItem('pipways_user');
        
        if (token && user) {
            this.state.token = token;
            this.state.user = JSON.parse(user);
            this.state.isAdmin = this.state.user.is_admin || false;
        }
    }
};

// Initialize on load
Store.init();
