const App = {
    async init() {
        UI.init();
        await Auth.init();
        Router.init();
        Notifications.init();

        console.log('Pipways Platform initialized');
    }
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => App.init());
} else {
    App.init();
}