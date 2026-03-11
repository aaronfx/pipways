/**
 * Trading Signals Module
 * Handles signal display and management
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
            
            if (!data || data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;">No active signals</td></tr>';
                return;
            }

            tbody.innerHTML = data.map(signal => `
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

    viewSignal(id) {
        ui.showToast(`Viewing signal ${id} - Full details modal would open here`, 'info');
    }
};
