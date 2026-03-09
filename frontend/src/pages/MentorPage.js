
import { Component } from '../components/Component.js';
import { Sidebar } from '../components/Sidebar.js';
import { api } from '../api/client.js';
import { showLoading } from '../utils/helpers.js';
import { store } from '../state.js';

export class MentorPage extends Component {
    constructor() {
        super();
        this.messages = [];
    }

    async render() {
        const container = document.createElement('div');
        container.className = 'main-app';

        const sidebar = new Sidebar();
        container.appendChild(sidebar.render());

        const main = document.createElement('main');
        main.className = 'main-content';
        main.innerHTML = `
            <div class="page-header">
                <h2><i class="fas fa-comments" style="color: var(--premium);"></i> AI Trading Mentor</h2>
                <p>Get personalized trading advice and psychology coaching</p>
            </div>

            <div class="mentor-container">
                <div class="chat-card card">
                    <div id="chat-messages" class="chat-messages">
                        <div class="message system">
                            <div class="message-avatar">
                                <i class="fas fa-robot"></i>
                            </div>
                            <div class="message-content">
                                <p>Hello! I'm your AI trading mentor. I can help you with:</p>
                                <ul>
                                    <li>Trading strategy development</li>
                                    <li>Risk management techniques</li>
                                    <li>Trading psychology and discipline</li>
                                    <li>Technical analysis questions</li>
                                    <li>Trade review and feedback</li>
                                </ul>
                                <p>What would you like to discuss today?</p>
                            </div>
                        </div>
                    </div>

                    <div class="chat-input-area">
                        <select id="chat-context" class="form-input context-select">
                            <option value="general">General</option>
                            <option value="psychology">Psychology</option>
                            <option value="risk_management">Risk Management</option>
                            <option value="technical_analysis">Technical Analysis</option>
                            <option value="strategy">Strategy</option>
                        </select>
                        <input type="text" id="chat-input" class="form-input chat-input" 
                               placeholder="Ask your question..." autocomplete="off">
                        <button class="btn btn-primary" id="send-btn">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

        container.appendChild(main);

        // Load history
        setTimeout(() => this.loadHistory(), 0);

        return container;
    }

    async loadHistory() {
        try {
            const data = await api.getChatHistory(20);
            if (data.history && data.history.length > 0) {
                const container = this.element.querySelector('#chat-messages');
                container.innerHTML = ''; // Clear welcome message

                // Reverse to show oldest first
                [...data.history].reverse().forEach(msg => {
                    this.addMessage(msg.message, 'user');
                    this.addMessage(msg.response, 'ai');
                });
            }
        } catch (e) {
            console.log('No history or error loading');
        }
    }

    bindEvents() {
        const input = this.element.querySelector('#chat-input');
        const sendBtn = this.element.querySelector('#send-btn');

        const sendMessage = () => {
            const text = input.value.trim();
            if (!text) return;

            this.addMessage(text, 'user');
            input.value = '';

            this.getAIResponse(text);
        };

        sendBtn.addEventListener('click', sendMessage);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }

    addMessage(text, sender) {
        const container = this.element.querySelector('#chat-messages');
        const div = document.createElement('div');
        div.className = `message ${sender}`;

        const isUser = sender === 'user';
        div.innerHTML = `
            <div class="message-avatar ${isUser ? 'user' : ''}">
                ${isUser 
                    ? (store.getState().user?.full_name?.charAt(0) || 'U').toUpperCase()
                    : '<i class="fas fa-robot"></i>'
                }
            </div>
            <div class="message-content">
                <p>${this.escapeHtml(text)}</p>
            </div>
        `;

        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }

    async getAIResponse(message) {
        const context = this.element.querySelector('#chat-context').value;

        showLoading(true, 'AI is thinking...');

        try {
            const result = await api.sendChatMessage(message, context);
            this.addMessage(result.response, 'ai');
        } catch (error) {
            this.addMessage('Sorry, I encountered an error. Please try again.', 'ai');
        } finally {
            showLoading(false);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML.replace(/
/g, '<br>');
    }
}
