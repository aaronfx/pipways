/**
 * Main Application Entry
 */
const App = {
    async init() {
        console.log('Initializing Pipways App...');
        
        // Initialize store first
        Store.init();
        
        // Initialize UI utilities
        if (typeof UI !== 'undefined') {
            UI.init();
        }
        
        // Initialize auth
        if (typeof Auth !== 'undefined') {
            await Auth.init();
        }
        
        // Initialize router last
        if (typeof Router !== 'undefined') {
            Router.init();
        }
        
        console.log('App initialized successfully');
    }
};

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => App.init());
} else {
    App.init();
}
