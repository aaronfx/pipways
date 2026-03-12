/**
 * Trading Signals Module - Frontend View
 */

const signals = {
    async loadSignals() {
        const filter = document.getElementById('signal-filter')?.value || '';
        const tbody = document.getElementById('signals-table-body');
        
        if (!tbody) return;
        
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;">Loading signals...</td></tr>';

        try {
            const url = filter ? `/api/signals?pair=${filter}` : '/api/signals';
            const data = await api.get(url);
            
            const signalsArray = data.signals || data;
            
            if (!Array.isArray(signalsArray) || signalsArray.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;">No active signals</td></tr>';
                return;
            }

            tbody.innerHTML = signalsArray.map(signal => `
                <tr>
                    <td><strong>${signal.pair}</strong></td>
                    <td>
                        <span class="badge badge-${signal.direction === 'buy' ? 'success' : 'danger'}">
                            ${signal.direction.toUpperCase()}
                        </span>
                    </td>
                    <td>${ui.formatPrice(signal.entry_price)}</td>
                    <td>
                        SL: ${ui.formatPrice(signal.stop_loss)}<br>
                        TP: ${ui.formatPrice(signal.tp1)}${signal.tp2 ? ' / ' + ui.formatPrice(signal.tp2) : ''}
                    </td>
                    <td>${signal.timeframe || 'N/A'}</td>
                    <td>
                        <span class="status-badge status-${signal.status === 'active' ? 'active' : 'inactive'}">
                            ${signal.status}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-sm" onclick="signals.viewSignal(${signal.id})">View</button>
                    </td>
                </tr>
            `).join('');
            
        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 40px; color: var(--danger);">Error loading signals: ${error.message}</td></tr>`;
        }
    },

    async viewSignal(id) {
        try {
            const response = await api.get(`/api/signals`);
            const signalsArray = response.signals || response;
            const signal = signalsArray.find(s => s.id === id);
            
            if (!signal) {
                ui.showToast('Signal not found', 'error');
                return;
            }

            const modalContent = `
                <div style="max-width: 600px;">
                    <h2>Signal Details: ${signal.pair}</h2>
                    <div style="margin: 20px 0; padding: 15px; background: var(--bg); border-radius: 8px;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                            <div>
                                <strong>Direction:</strong> 
                                <span class="badge badge-${signal.direction === 'buy' ? 'success' : 'danger'}">
                                    ${signal.direction.toUpperCase()}
                                </span>
                            </div>
                            <div><strong>Status:</strong> ${signal.status}</div>
                            <div><strong>Entry Price:</strong> ${ui.formatPrice(signal.entry_price)}</div>
                            <div><strong>Timeframe:</strong> ${signal.timeframe || 'N/A'}</div>
                            <div><strong>Stop Loss:</strong> ${ui.formatPrice(signal.stop_loss)}</div>
                            <div><strong>Take Profit 1:</strong> ${ui.formatPrice(signal.tp1)}</div>
                            ${signal.tp2 ? `<div><strong>Take Profit 2:</strong> ${ui.formatPrice(signal.tp2)}</div>` : ''}
                        </div>
                        ${signal.analysis ? `
                            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid var(--border);">
                                <strong>Analysis:</strong>
                                <p style="margin-top: 5px; line-height: 1.6;">${ui.escapeHtml(signal.analysis)}</p>
                            </div>
                        ` : ''}
                    </div>
                    <div style="text-align: right;">
                        <button class="btn btn-secondary" onclick="ui.closeModal('signal-detail-modal')">Close</button>
                    </div>
                </div>
            `;

            let modal = document.getElementById('signal-detail-modal');
            if (!modal) {
                modal = document.createElement('div');
                modal.id = 'signal-detail-modal';
                modal.className = 'modal';
                modal.innerHTML = '<div class="modal-content" id="signal-detail-content"></div>';
                document.body.appendChild(modal);
            }
            
            const content = document.getElementById('signal-detail-content');
            if (content) content.innerHTML = modalContent;
            
            ui.openModal('signal-detail-modal');
            
        } catch (error) {
            ui.showToast('Error loading signal details: ' + error.message, 'error');
        }
    }
};
