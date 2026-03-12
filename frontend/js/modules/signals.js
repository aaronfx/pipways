const SignalsPage = {
    async render(container) {
        container.innerHTML = '<div class="page-header"><h1>Trading Signals</h1></div>';

        if (Store.state.isAdmin) {
            container.innerHTML += `
                <div class="admin-controls" style="margin-bottom: 1rem;">
                    <button onclick="SignalsPage.showCreateForm()" class="btn btn-primary">
                        + New Signal
                    </button>
                </div>
            `;
        }

        try {
            const signals = await API.getSignals({ limit: 50 });
            Store.setState('signals', signals);

            if (signals.length === 0) {
                container.innerHTML += '<p>No active signals at the moment.</p>';
                return;
            }

            let html = '<div class="signals-grid">';
            signals.forEach(signal => {
                html += this.signalCard(signal);
            });
            html += '</div>';

            container.innerHTML += html;
        } catch (error) {
            container.innerHTML += '<p class="error">Failed to load signals</p>';
        }
    },

    signalCard(signal) {
        const statusClass = signal.status === 'ACTIVE' ? 'status-active' : 'status-closed';
        const resultClass = signal.result === 'SUCCESS' ? 'result-success' : 
                           signal.result === 'LOSS' ? 'result-loss' : 'result-pending';

        return `
            <div class="signal-card ${statusClass}" data-entry="${signal.entry_price}" data-sl="${signal.stop_loss}">
                <div class="signal-header">
                    <span class="asset">${signal.asset}</span>
                    <span class="direction ${signal.direction.toLowerCase()}">${signal.direction}</span>
                </div>
                <h3>${UI.escapeHtml(signal.title)}</h3>
                <p>${UI.escapeHtml(signal.description)}</p>
                <div class="signal-levels">
                    <div><span>Entry:</span> ${signal.entry_price}</div>
                    <div><span>SL:</span> ${signal.stop_loss}</div>
                    <div><span>TP:</span> ${signal.take_profit}</div>
                </div>
                <div class="signal-footer">
                    <span class="badge ${resultClass}">${signal.result}</span>
                    <span class="date">${UI.formatDate(signal.created_at)}</span>
                </div>
                ${Store.state.isAdmin ? this.adminActions(signal) : ''}
            </div>
        `;
    },

    adminActions(signal) {
        return `
            <div class="admin-actions" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e5e7eb;">
                <button onclick="SignalsPage.editSignal(${signal.id})" class="btn btn-sm">Edit</button>
                <button onclick="SignalsPage.closeSignal(${signal.id})" class="btn btn-sm btn-danger">Close</button>
            </div>
        `;
    },

    showCreateForm() {
        UI.showModal(`
            <h2>Create Signal</h2>
            <form onsubmit="SignalsPage.handleCreate(event)">
                <div class="form-group">
                    <label>Asset (e.g., EURUSD)</label>
                    <input type="text" name="asset" required>
                </div>
                <div class="form-group">
                    <label>Direction</label>
                    <select name="direction" required>
                        <option value="BUY">BUY</option>
                        <option value="SELL">SELL</option>
                    </select>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Entry Price</label>
                        <input type="number" step="0.00001" name="entry_price" required>
                    </div>
                    <div class="form-group">
                        <label>Stop Loss</label>
                        <input type="number" step="0.00001" name="stop_loss" required>
                    </div>
                    <div class="form-group">
                        <label>Take Profit</label>
                        <input type="number" step="0.00001" name="take_profit" required>
                    </div>
                </div>
                <div class="form-group">
                    <label>Title</label>
                    <input type="text" name="title" required>
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea name="description" rows="3"></textarea>
                </div>
                <button type="submit" class="btn btn-primary">Create</button>
            </form>
        `);
    },

    async handleCreate(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);

        try {
            await API.createSignal({
                ...data,
                entry_price: parseFloat(data.entry_price),
                stop_loss: parseFloat(data.stop_loss),
                take_profit: parseFloat(data.take_profit)
            });
            UI.closeModal();
            UI.showToast('Signal created', 'success');
            this.render(document.getElementById('app'));
        } catch (error) {
            UI.showToast(error.message, 'error');
        }
    },

    async closeSignal(id) {
        if (!confirm('Close this signal?')) return;
        try {
            await API.updateSignal(id, { status: 'CLOSED' });
            UI.showToast('Signal closed', 'success');
            this.render(document.getElementById('app'));
        } catch (error) {
            UI.showToast(error.message, 'error');
        }
    },

    prependSignal(signal) {
        const grid = document.querySelector('.signals-grid');
        if (grid) {
            const card = document.createElement('div');
            card.innerHTML = this.signalCard(signal);
            grid.insertBefore(card.firstElementChild, grid.firstChild);
        }
    }
};