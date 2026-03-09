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
                                    <li>Market analysis insights</li>
                                </ul>
                                <p>What would you like to discuss today?</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="chat-input-container">
                        <div class="context-selector">
                            <label class="form-label">Context:</label>
                            <select id="mentor-context" class="form-input">
                                <option value="trading">General Trading</option>
                                <option value="psychology">Trading Psychology</option>
                                <option value="risk">Risk Management</option>
                                <option value="technical">Technical Analysis</option>
                            </select>
                        </div>
                        
                        <div class="chat-input-wrapper">
                            <textarea 
                                id="chat-input" 
                                class="chat-input" 
                                placeholder="Ask your trading question..." 
                                rows="3"
                            ></textarea>
                            <button id="send-message" class="btn btn-primary btn-send">
                                <i class="fas fa-paper-plane"></i>
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="mentor-sidebar card">
                    <h3><i class="fas fa-history"></i> Recent Conversations</h3>
                    <div id="chat-history" class="chat-history">
                        <p class="text-secondary">No recent conversations</p>
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(main);
        
        // Load chat history after render
        this.loadChatHistory();
        
        return container;
    }

    bindEvents() {
        const sendBtn = this.element.querySelector('#send-message');
        const input = this.element.querySelector('#chat-input');
        
        sendBtn.addEventListener('click', () => this.sendMessage());
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    async sendMessage() {
        const input = this.element.querySelector('#chat-input');
        const context = this.element.querySelector('#mentor-context').value;
        const message = input.value.trim();
        
        if (!message) return;
        
        // Add user message to UI
        this.addMessage(message, 'user');
        input.value = '';
        
        showLoading(true, 'AI is thinking...');
        
        try {
            const response = await api.sendChatMessage(message, context);
            
            if (response && response.response) {
                // Fixed: Use string replacement instead of regex to avoid syntax errors
                const formattedResponse = response.response.split('\n').join('<br>');
                this.addMessage(formattedResponse, 'assistant', true);
            } else {
                this.addMessage('Sorry, I could not process your request. Please try again.', 'assistant');
            }
            
            // Refresh history
            this.loadChatHistory();
            
        } catch (error) {
            console.error('Chat error:', error);
            this.addMessage('Sorry, there was an error processing your message. Please try again.', 'assistant');
        } finally {
            showLoading(false);
        }
    }

    addMessage(content, type, isHTML = false) {
        const container = this.element.querySelector('#chat-messages');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        
        if (type === 'user') {
            const { user } = store.getState();
            avatar.textContent = (user?.full_name || user?.email || 'U').charAt(0).toUpperCase();
        } else {
            avatar.innerHTML = '<i class="fas fa-robot"></i>';
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (isHTML) {
            contentDiv.innerHTML = content;
        } else {
            // Fixed: Use textContent for plain text to avoid XSS, then convert newlines
            contentDiv.textContent = content;
            contentDiv.innerHTML = contentDiv.innerHTML.split('\n').join('<br>');
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        container.appendChild(messageDiv);
        
        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
    }

    async loadChatHistory() {
        try {
            const history = await api.getChatHistory(10);
            const historyContainer = this.element.querySelector('#chat-history');
            
            if (history && history.history && history.history.length > 0) {
                historyContainer.innerHTML = history.history.map(item => `
                    <div class="history-item">
                        <div class="history-message">${this.escapeHtml(item.message)}</div>
                        <div class="history-time">${new Date(item.created_at).toLocaleString()}</div>
                    </div>
                `).join('');
            } else {
                historyContainer.innerHTML = '<p class="text-secondary">No recent conversations</p>';
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
