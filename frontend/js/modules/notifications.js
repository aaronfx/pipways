const Notifications = {
    ws: null,

    init() {
        if (Store.isAuthenticated()) {
            this.connectWebSocket();
        }

        Store.subscribe((state) => {
            if (state.token && !this.ws) {
                this.connectWebSocket();
            } else if (!state.token && this.ws) {
                this.disconnect();
            }
        });
    },

    connectWebSocket() {
        const wsUrl = API_BASE_URL.replace('http', 'ws') + '/ws/signals?token=' + Store.getToken();
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            setTimeout(() => this.connectWebSocket(), 5000);
        };
    },

    handleMessage(data) {
        if (data.type === 'new_signal') {
            this.showSignalNotification(data.data);
        }
    },

    showSignalNotification(signal) {
        if (Notification.permission === 'granted') {
            new Notification(`🚨 New ${signal.asset} Signal`, {
                body: `${signal.direction} @ ${signal.entry_price}`,
                icon: '/icon.png'
            });
        }

        UI.showToast(`New signal: ${signal.asset} ${signal.direction}`, 'info');

        if (Store.state.currentPage === 'signals') {
            SignalsPage.prependSignal(signal);
        }
    },

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    },

    async setupTelegram() {
        UI.showModal(`
            <h2>🔗 Connect Telegram</h2>
            <p>Get instant signal alerts on your phone</p>
            <ol>
                <li>Search for <strong>@PipwaysBot</strong> on Telegram</li>
                <li>Send <code>/start</code></li>
                <li>Copy the chat ID provided</li>
            </ol>
            <form onsubmit="Notifications.saveTelegram(event)">
                <input type="text" id="telegramChatId" placeholder="123456789" required>
                <button type="submit" class="btn btn-primary">Connect</button>
            </form>
        `);
    },

    async saveTelegram(e) {
        e.preventDefault();
        const chatId = document.getElementById('telegramChatId').value;

        try {
            await API.request('/notifications/telegram', {
                method: 'POST',
                body: JSON.stringify({ chat_id: chatId })
            });

            UI.closeModal();
            UI.showToast('Telegram connected!', 'success');
        } catch (error) {
            UI.showToast(error.message, 'error');
        }
    }
};

document.addEventListener('click', () => {
    if (Notification.permission === 'default') {
        Notification.requestPermission();
    }
}, { once: true });