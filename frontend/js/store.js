// Global State Store
const Store = {
    state: {
        user: JSON.parse(localStorage.getItem('pipways_user') || 'null'),
        token: localStorage.getItem('pipways_token'),
        loading: false,
        currentPage: 'dashboard'
    },
    
    listeners: [],
    
    getToken() { 
        return this.state.token; 
    },
    
    getUser() { 
        return this.state.user; 
    },
    
    isAuthenticated() { 
        return !!this.state.token; 
    },
    
    isAdmin() {
        return this.state.user?.is_admin === true;
    },
    
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
        this.notify('logout', null);
        window.location.href = '/';
    },
    
    setLoading(status) {
        this.state.loading = status;
        this.notify('loading', status);
    },
    
    setPage(page) {
        this.state.currentPage = page;
        this.notify('page', page);
    },
    
    subscribe(callback) {
        this.listeners.push(callback);
    },
    
    notify(key, value) {
        this.listeners.forEach(cb => cb(key, value));
    }
};
