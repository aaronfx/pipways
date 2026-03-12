const Store = {
    state: {
        user: null,
        token: localStorage.getItem('token') || null,
        isAdmin: false,
        currentPage: 'home',
        signals: [],
        courses: [],
        blogPosts: [],
        webinars: [],
        media: [],
        stats: null,
        loading: false
    },

    listeners: [],

    subscribe(callback) {
        this.listeners.push(callback);
        return () => {
            this.listeners = this.listeners.filter(cb => cb !== callback);
        };
    },

    notify() {
        this.listeners.forEach(cb => cb(this.state));
    },

    setState(key, value) {
        this.state[key] = value;
        this.notify();
    },

    setUser(user, token) {
        this.state.user = user;
        this.state.token = token;
        this.state.isAdmin = user?.is_admin || false;
        if (token) localStorage.setItem('token', token);
        this.notify();
    },

    logout() {
        this.state.user = null;
        this.state.token = null;
        this.state.isAdmin = false;
        localStorage.removeItem('token');
        this.notify();
    },

    getToken() {
        return this.state.token;
    },

    isAuthenticated() {
        return !!this.state.token;
    }
};