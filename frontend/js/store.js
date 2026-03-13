/**
 * Global State Management
 */
const Store = {
    state: {
        user: JSON.parse(localStorage.getItem('pipways_user') || 'null'),
        token: localStorage.getItem('pipways_token'),
        loading: false,
        notifications: []
    },

    listeners: new Set(),

    getToken() { return this.state.token; },
    getUser() { return this.state.user; },
    isAuthenticated() { return !!this.state.token; },

    setUser(user, token) {
        this.state.user = user;
        this.state.token = token;
        localStorage.setItem('pipways_user', JSON.stringify(user));
        localStorage.setItem('pipways_token', token);
        this.notify('user', user);
    },

    logout() {
        this.state.user = null;
        this.state.token = null;
        localStorage.removeItem('pipways_user');
        localStorage.removeItem('pipways_token');
        this.notify('user', null);
    },

    setLoading(loading) {
        this.state.loading = loading;
        this.notify('loading', loading);
    },

    subscribe(callback) {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    },

    notify(key, value) {
        this.listeners.forEach(cb => cb(key, value));
    },

    init() {
        // Restore from storage
        const token = localStorage.getItem('pipways_token');
        const user = localStorage.getItem('pipways_user');
        if (token && user) {
            this.state.token = token;
            this.state.user = JSON.parse(user);
        }
    }
};
