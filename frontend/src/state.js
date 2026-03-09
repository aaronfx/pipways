
// Central State Store - replaces global variables
class Store {
    constructor() {
        this.state = {
            user: JSON.parse(localStorage.getItem('user') || 'null'),
            token: localStorage.getItem('access_token'),
            refreshToken: localStorage.getItem('refresh_token'),
            trades: [],
            currentPage: 'dashboard',
            isLoading: false,
            loadingMessage: '',
            stats: null,
            users: [],
            blogPosts: [],
            courses: [],
            webinars: [],
            chatHistory: []
        };
        this.listeners = new Set();
    }

    subscribe(callback) {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    setState(newState) {
        this.state = { ...this.state, ...newState };
        this.listeners.forEach(cb => cb(this.state));
    }

    getState() {
        return this.state;
    }

    // Auth helpers
    isAuthenticated() {
        return !!this.state.token;
    }

    isAdmin() {
        return this.state.user?.role === 'admin' || this.state.user?.role === 'moderator';
    }

    logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        this.setState({ user: null, token: null, refreshToken: null });
    }
}

export const store = new Store();
