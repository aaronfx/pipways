// Global State Store
const Store = {
    state: {
        user: JSON.parse(localStorage.getItem('pipways_user') || 'null'),
        token: localStorage.getItem('pipways_token'),
        loading: false,
        notifications: []
    },
    
    getToken() { return this.state.token; },
    getUser() { return this.state.user; },
    isAuthenticated() { return !!this.state.token; },
    
    setUser(user, token) {
        this.state.user = user;
        this.state.token = token;
        localStorage.setItem('pipways_user', JSON.stringify(user));
        localStorage.setItem('pipways_token', token);
    },
    
    logout() {
        this.state.user = null;
        this.state.token = null;
        localStorage.removeItem('pipways_user');
        localStorage.removeItem('pipways_token');
    }
};
