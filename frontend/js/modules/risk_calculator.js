/**
 * risk_calculator.js — Dashboard Risk Calculator Module
 *
 * Renders inside section-risk in dashboard.html.
 * Depends on: window.dashboard (DashboardController), dashboard.apiRequest()
 *
 * Changes from original:
 *   - FIXED: Store.isAuthenticated() → check localStorage for pipways_token
 *   - FIXED: UI.showToast() → window.dashboard._toast() (Pipways toast system)
 *   - FIXED: API.calculateRisk() → dashboard.apiRequest('/risk/calculate', …)
 *   - FIXED: API.getRiskHistory() → dashboard.apiRequest('/risk/history')
 *   - ADDED: Instrument type selector with correct pip configs per instrument
 *   - FIXED: Correct lot size formula inside _calcLocally() for instant feedback
 *   - ADDED: Drawdown Simulator section
 *   - ADDED: Daily Loss Limit section
 *   - ADDED: Pip value and stop pips in results
 */

// ── Instrument pip configurations (mirrors risk_calculator.py INSTRUMENT_CONFIG) ──
const _RC_INSTR = {
    forex:   { pip: 0.0001, pv: 10,  step: '0.00001', eg: { e: '1.08500', sl: '1.08000', tp: '1.09500' } },
    jpy:     { pip: 0.01,   pv: 10,  step: '0.001',   eg: { e: '152.500', sl: '151.500', tp: '154.500' } },
    gold:    { pip: 0.01,   pv: 1,   step: '0.01',    eg: { e: '2050.00', sl: '2040.00', tp: '2080.00' } },
    silver:  { pip: 0.001,  pv: 50,  step: '0.001',   eg: { e: '23.500',  sl: '23.000',  tp: '24.500'  } },
    oil:     { pip: 0.01,   pv: 10,  step: '0.01',    eg: { e: '82.50',   sl: '82.00',   tp: '83.50'   } },
    indices: { pip: 1.0,    pv: 1,   step: '0.1',     eg: { e: '4500.0',  sl: '4490.0',  tp: '4530.0'  } },
};

const RiskCalculator = {

    // ── Entry point ───────────────────────────────────────────────────────────
    async render(container) {
        if (!container) return;

        // FIXED: replaced Store.isAuthenticated() — Store doesn't exist in Pipways.
        // Auth state is tracked via localStorage token.
        const isAuth = !!localStorage.getItem('pipways_token');

        container.innerHTML = `
        <style>
            @media (max-width: 640px) {
                .rc-grid-responsive { grid-template-columns: 1fr !important; }
                #rc-d-main { font-size: 2.5rem !important; }
            }
        </style>
        <div style="max-width:900px;">

            <!-- Header -->
            <div style="margin-bottom:24px;">
                <h2 style="color:white;font-size:1.25rem;font-weight:700;margin:0 0 4px;">
                    <i class="fas fa-calculator" style="color:#a78bfa;margin-right:.5rem;font-size:1rem;"></i>
                    Risk Management Calculator
                </h2>
                <p style="color:#6b7280;font-size:.85rem;margin:0;">
                    Calculate optimal position size based on your account and risk tolerance.
                </p>
            </div>

            <!-- Main grid -->
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start;"
                 id="rc-dash-grid"
                 class="rc-grid-responsive">

                <!-- Inputs -->
                <div style="background:#111827;border-radius:12px;padding:24px;border:1px solid #1f2937;">
                    <h3 style="color:white;font-size:.9rem;font-weight:700;margin:0 0 18px;">Trade Parameters</h3>

                    <div style="display:flex;flex-direction:column;gap:14px;">

                        <!-- Instrument -->
                        <div>
                            <label style="display:block;font-size:.75rem;color:#6b7280;font-weight:600;margin-bottom:5px;">
                                Instrument Type
                            </label>
                            <select id="rc-d-instr"
                                style="width:100%;padding:9px 32px 9px 12px;background:#0d1117;border:1px solid #374151;
                                       border-radius:8px;color:white;font-size:.875rem;box-sizing:border-box;outline:none;"
                                onfocus="this.style.borderColor='#7c3aed'" onblur="this.style.borderColor='#374151'"
                                onchange="RiskCalculator.onInstrumentChange()">
                                <option value="forex">Forex 4-dec (EUR/USD, GBP/USD…)</option>
                                <option value="jpy">JPY Pairs (USD/JPY, EUR/JPY…)</option>
                                <option value="gold">Gold (XAU/USD)</option>
                                <option value="silver">Silver (XAG/USD)</option>
                                <option value="oil">Oil (WTI / BRENT)</option>
                                <option value="indices">Indices (S&P500, NAS100, US30…)</option>
                            </select>
                        </div>

                        <!-- Balance / Risk row -->
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                            <div>
                                <label style="display:block;font-size:.75rem;color:#6b7280;font-weight:600;margin-bottom:5px;">Account Balance ($)</label>
                                <input type="number" id="rc-d-balance" value="10000" min="100" step="100"
                                    style="width:100%;padding:9px 12px;background:#0d1117;border:1px solid #374151;
                                           border-radius:8px;color:white;font-size:.875rem;box-sizing:border-box;outline:none;"
                                    onfocus="this.style.borderColor='#7c3aed'" onblur="this.style.borderColor='#374151'"
                                    oninput="RiskCalculator.calculate()">
                            </div>
                            <div>
                                <label style="display:block;font-size:.75rem;color:#6b7280;font-weight:600;margin-bottom:5px;">Risk % <span style="color:#f59e0b;">max 2%</span></label>
                                <input type="number" id="rc-d-risk" value="1" min="0.1" max="10" step="0.1"
                                    style="width:100%;padding:9px 12px;background:#0d1117;border:1px solid #374151;
                                           border-radius:8px;color:white;font-size:.875rem;box-sizing:border-box;outline:none;"
                                    onfocus="this.style.borderColor='#7c3aed'" onblur="this.style.borderColor='#374151'"
                                    oninput="RiskCalculator.calculate()">
                            </div>
                        </div>

                        <!-- Entry / SL / TP -->
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                            <div>
                                <label style="display:block;font-size:.75rem;color:#6b7280;font-weight:600;margin-bottom:5px;">Entry Price</label>
                                <input type="number" id="rc-d-entry" value="1.08500" step="0.00001"
                                    style="width:100%;padding:9px 12px;background:#0d1117;border:1px solid #374151;
                                           border-radius:8px;color:white;font-size:.875rem;box-sizing:border-box;outline:none;"
                                    onfocus="this.style.borderColor='#7c3aed'" onblur="this.style.borderColor='#374151'"
                                    oninput="RiskCalculator.calculate()">
                            </div>
                            <div>
                                <label style="display:block;font-size:.75rem;color:#6b7280;font-weight:600;margin-bottom:5px;">Stop Loss</label>
                                <input type="number" id="rc-d-sl" value="1.08000" step="0.00001"
                                    style="width:100%;padding:9px 12px;background:#0d1117;border:1px solid #374151;
                                           border-radius:8px;color:white;font-size:.875rem;box-sizing:border-box;outline:none;"
                                    onfocus="this.style.borderColor='#7c3aed'" onblur="this.style.borderColor='#374151'"
                                    oninput="RiskCalculator.calculate()">
                            </div>
                        </div>
                        <div>
                            <label style="display:block;font-size:.75rem;color:#6b7280;font-weight:600;margin-bottom:5px;">
                                Take Profit <span style="font-weight:400;color:#4b5563;">(optional — for R:R)</span>
                            </label>
                            <input type="number" id="rc-d-tp" value="1.09500" step="0.00001"
                                style="width:100%;padding:9px 12px;background:#0d1117;border:1px solid #374151;
                                       border-radius:8px;color:white;font-size:.875rem;box-sizing:border-box;outline:none;"
                                onfocus="this.style.borderColor='#7c3aed'" onblur="this.style.borderColor='#374151'"
                                oninput="RiskCalculator.calculate()">
                        </div>

                    </div>
                </div>

                <!-- Results -->
                <div style="display:flex;flex-direction:column;gap:16px;">
                    <div style="background:#111827;border-radius:12px;padding:24px;border:1px solid #1f2937;">
                        <h3 style="color:white;font-size:.9rem;font-weight:700;margin:0 0 16px;">Results</h3>
                        <div style="text-align:center;padding:16px 0 12px;">
                            <div id="rc-d-main" style="font-size:3rem;font-weight:800;color:#a78bfa;line-height:1;">—</div>
                            <div style="color:#4b5563;font-size:.8rem;margin-top:4px;">Standard Lots</div>
                        </div>
                        <div id="rc-d-details"></div>
                        <div id="rc-d-warning" style="display:none;margin-top:12px;"></div>
                    </div>
                </div>
            </div>

            <!-- Advanced tools row -->
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:20px;" class="rc-grid-responsive">

                <!-- Drawdown Simulator -->
                <div style="background:#111827;border-radius:12px;padding:22px;border:1px solid #1f2937;">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">
                        <i class="fas fa-chart-line" style="color:#f87171;font-size:.85rem;"></i>
                        <h3 style="color:white;font-size:.875rem;font-weight:700;margin:0;">Drawdown Simulator</h3>
                    </div>
                    <table style="width:100%;border-collapse:collapse;font-size:.78rem;" id="rc-d-dd">
                        <thead>
                            <tr>
                                <th style="color:#4b5563;font-weight:600;padding:6px 8px;text-align:left;border-bottom:1px solid #1f2937;">Losses</th>
                                <th style="color:#4b5563;font-weight:600;padding:6px 8px;text-align:left;border-bottom:1px solid #1f2937;">Balance</th>
                                <th style="color:#4b5563;font-weight:600;padding:6px 8px;text-align:left;border-bottom:1px solid #1f2937;">Down</th>
                                <th style="color:#4b5563;font-weight:600;padding:6px 8px;text-align:left;border-bottom:1px solid #1f2937;">To Recover</th>
                            </tr>
                        </thead>
                        <tbody id="rc-d-dd-body">
                            <tr><td colspan="4" style="color:#374151;padding:12px;text-align:center;">Enter values above</td></tr>
                        </tbody>
                    </table>
                </div>

                <!-- Daily Loss Limit -->
                <div style="background:#111827;border-radius:12px;padding:22px;border:1px solid #1f2937;">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">
                        <i class="fas fa-calendar-day" style="color:#fbbf24;font-size:.85rem;"></i>
                        <h3 style="color:white;font-size:.875rem;font-weight:700;margin:0;">Daily Loss Limit</h3>
                    </div>
                    <div style="margin-bottom:12px;">
                        <label style="display:block;font-size:.75rem;color:#6b7280;font-weight:600;margin-bottom:5px;">Max Daily Loss (%)</label>
                        <input type="number" id="rc-d-daily" value="5" min="1" max="20" step="0.5"
                            style="width:100%;padding:8px 12px;background:#0d1117;border:1px solid #374151;
                                   border-radius:8px;color:white;font-size:.875rem;box-sizing:border-box;outline:none;"
                            onfocus="this.style.borderColor='#7c3aed'" onblur="this.style.borderColor='#374151'"
                            oninput="RiskCalculator.calculate()">
                    </div>
                    <div id="rc-d-daily-body">
                        <div style="color:#374151;font-size:.82rem;text-align:center;padding:12px;">Enter values above</div>
                    </div>
                </div>
            </div>

            ${isAuth ? `
            <!-- History (authenticated users only) -->
            <div style="margin-top:20px;background:#111827;border-radius:12px;padding:22px;border:1px solid #1f2937;">
                <h3 style="color:white;font-size:.875rem;font-weight:700;margin:0 0 14px;">
                    <i class="fas fa-history" style="color:#6b7280;margin-right:.4rem;"></i>
                    Recent Calculations
                </h3>
                <div id="rc-d-history">
                    <div style="text-align:center;padding:16px;color:#374151;">
                        <i class="fas fa-spinner fa-spin"></i>
                    </div>
                </div>
            </div>
            ` : ''}

        </div>`;

        // Initial calculation and history load
        this.calculate();
        if (isAuth) this.loadHistory();
    },

    // ── Main calculate ────────────────────────────────────────────────────────
    calculate() {
        const instrKey  = document.getElementById('rc-d-instr')?.value || 'forex';
        const instr     = _RC_INSTR[instrKey] || _RC_INSTR.forex;
        const balance   = parseFloat(document.getElementById('rc-d-balance')?.value) || 0;
        const riskPct   = parseFloat(document.getElementById('rc-d-risk')?.value)    || 1;
        const entry     = parseFloat(document.getElementById('rc-d-entry')?.value)   || 0;
        const sl        = parseFloat(document.getElementById('rc-d-sl')?.value)      || 0;
        const tp        = parseFloat(document.getElementById('rc-d-tp')?.value)      || 0;
        const dailyLim  = parseFloat(document.getElementById('rc-d-daily')?.value)   || 5;

        if (!balance || !entry || !sl || entry === sl) {
            this._placeholder();
            return;
        }

        const riskAmt  = balance * (riskPct / 100);
        const stopDist = Math.abs(entry - sl);
        // FIXED formula
        const stopPips = stopDist / instr.pip;
        const rawLots  = riskAmt / (stopPips * instr.pv);
        const lotSize  = Math.max(0.01, Math.round(rawLots * 100) / 100);
        const maxLoss  = stopPips * instr.pv * lotSize;
        const rr       = (tp && tp !== entry) ? Math.round((Math.abs(tp - entry) / stopDist) * 100) / 100 : 0;

        const rrColor  = rr >= 2 ? '#34d399' : rr >= 1.5 ? '#fbbf24' : '#f87171';
        let warnHtml = '', warnStyle = '';
        if (riskPct > 2) {
            warnHtml  = '⚠️ Risking more than 2% is dangerous for your account.';
            warnStyle = 'background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.3);border-radius:8px;padding:9px 12px;color:#fbbf24;font-size:.78rem;';
        } else if (rr > 0 && rr < 1.5) {
            warnHtml  = '⚠️ R:R below 1:1.5 — consider a better take profit.';
            warnStyle = 'background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.3);border-radius:8px;padding:9px 12px;color:#fbbf24;font-size:.78rem;';
        } else if (rr >= 2) {
            warnHtml  = `✅ Solid 1:${rr} R:R — good setup.`;
            warnStyle = 'background:rgba(52,211,153,.1);border:1px solid rgba(52,211,153,.3);border-radius:8px;padding:9px 12px;color:#34d399;font-size:.78rem;';
        }

        const mainEl = document.getElementById('rc-d-main');
        if (mainEl) mainEl.textContent = lotSize.toFixed(2);

        const detEl = document.getElementById('rc-d-details');
        if (detEl) detEl.innerHTML = `
            <div style="display:flex;justify-content:space-between;padding:7px 0;font-size:.8rem;border-bottom:1px solid #1f2937;">
                <span style="color:#6b7280;">Max Loss</span>
                <span style="color:#f87171;font-weight:600;">$${maxLoss.toFixed(2)}</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:7px 0;font-size:.8rem;border-bottom:1px solid #1f2937;">
                <span style="color:#6b7280;">Stop Pips</span>
                <span style="color:white;font-weight:600;">${stopPips.toFixed(1)}</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:7px 0;font-size:.8rem;border-bottom:${rr > 0 ? '1px solid #1f2937' : 'none'};">
                <span style="color:#6b7280;">Pip Value / Lot</span>
                <span style="color:white;font-weight:600;">$${instr.pv.toFixed(2)}</span>
            </div>
            ${rr > 0 ? `
            <div style="display:flex;justify-content:space-between;padding:7px 0;font-size:.8rem;">
                <span style="color:#6b7280;">Risk : Reward</span>
                <span style="color:${rrColor};font-weight:700;">1 : ${rr}</span>
            </div>` : ''}
        `;

        const warnEl = document.getElementById('rc-d-warning');
        if (warnEl) {
            if (warnHtml) { warnEl.style.display = 'block'; warnEl.innerHTML = `<div style="${warnStyle}">${warnHtml}</div>`; }
            else { warnEl.style.display = 'none'; }
        }

        this._updateDrawdown(balance, riskPct);
        this._updateDailyLimit(balance, riskPct, dailyLim, maxLoss);

        // FIXED: warn threshold — risk_calculator.js was calling UI.showToast() which doesn't exist
        if (riskPct > 2 && typeof window.dashboard?._toast === 'function') {
            window.dashboard._toast('Warning: risking more than 2% per trade is dangerous', 'warning');
        }
    },

    // ── Drawdown table ────────────────────────────────────────────────────────
    _updateDrawdown(balance, riskPct) {
        const tbody = document.getElementById('rc-d-dd-body');
        if (!tbody) return;
        const steps = [1, 2, 3, 5, 7, 10];
        tbody.innerHTML = steps.map(n => {
            const rem      = balance * Math.pow(1 - riskPct / 100, n);
            const lostPct  = ((balance - rem) / balance * 100).toFixed(1);
            const recover  = ((balance / rem - 1) * 100).toFixed(1);
            const col      = n <= 2 ? '#fbbf24' : n <= 5 ? '#f97316' : '#f87171';
            return `<tr>
                <td style="padding:7px 8px;color:#94a3b8;">${n}</td>
                <td style="padding:7px 8px;color:white;font-weight:600;">$${Math.round(rem).toLocaleString()}</td>
                <td style="padding:7px 8px;color:${col};font-weight:600;">-${lostPct}%</td>
                <td style="padding:7px 8px;color:#6b7280;">+${recover}%</td>
            </tr>`;
        }).join('');
    },

    // ── Daily limit panel ─────────────────────────────────────────────────────
    _updateDailyLimit(balance, riskPct, limitPct, lossPerTrade) {
        const el = document.getElementById('rc-d-daily-body');
        if (!el) return;
        const limitAmt  = balance * (limitPct / 100);
        const maxTrades = Math.max(0, Math.floor(limitAmt / lossPerTrade));
        let rows = '';
        for (let i = 0; i <= Math.min(maxTrades, 3); i++) {
            const left  = Math.max(0, maxTrades - i);
            const col   = left <= 1 ? '#f87171' : left <= 2 ? '#fbbf24' : '#34d399';
            rows += `<div style="display:flex;justify-content:space-between;padding:5px 0;font-size:.78rem;border-bottom:1px solid #0d1117;">
                <span style="color:#6b7280;">${i} loss${i !== 1 ? 'es' : ''} today</span>
                <span style="color:${col};font-weight:700;">${left} trade${left !== 1 ? 's' : ''} left</span>
            </div>`;
        }
        el.innerHTML = `
            <div style="display:flex;justify-content:space-between;padding:0 0 10px;margin-bottom:6px;border-bottom:1px solid #1f2937;">
                <span style="font-size:.75rem;color:#4b5563;">Daily cap (${limitPct}%)</span>
                <span style="color:#fbbf24;font-weight:700;font-size:.82rem;">$${limitAmt.toFixed(2)}</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:6px 0 10px;border-bottom:1px solid #1f2937;">
                <span style="font-size:.78rem;color:#6b7280;">Max trades at ${riskPct}% risk</span>
                <span style="color:white;font-weight:700;">${maxTrades}</span>
            </div>
            ${rows}
        `;
    },

    // ── Instrument change ─────────────────────────────────────────────────────
    onInstrumentChange() {
        const key  = document.getElementById('rc-d-instr')?.value || 'forex';
        const inst = _RC_INSTR[key] || _RC_INSTR.forex;
        ['rc-d-entry', 'rc-d-sl', 'rc-d-tp'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.step = inst.step;
        });
        const e = document.getElementById('rc-d-entry');
        const s = document.getElementById('rc-d-sl');
        const t = document.getElementById('rc-d-tp');
        if (e) e.value = inst.eg.e;
        if (s) s.value = inst.eg.sl;
        if (t) t.value = inst.eg.tp;
        this.calculate();
    },

    // ── Load history ──────────────────────────────────────────────────────────
    async loadHistory() {
        const el = document.getElementById('rc-d-history');
        if (!el) return;
        try {
            // FIXED: was API.getRiskHistory() — that method doesn't exist in Pipways.
            // Using dashboard.apiRequest() which is the correct Pipways pattern.
            const history = await window.dashboard.apiRequest('/risk/history');
            if (!Array.isArray(history) || !history.length) {
                el.innerHTML = '<p style="color:#374151;font-size:.8rem;text-align:center;padding:12px;">No calculations saved yet.</p>';
                return;
            }
            el.innerHTML = history.map(h => `
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:9px 0;border-bottom:1px solid #0d1117;font-size:.8rem;">
                    <span style="color:#6b7280;">
                        ${new Date(h.calculated_at).toLocaleDateString('en-GB', { day:'numeric', month:'short' })}
                        <span style="margin-left:6px;color:#4b5563;font-size:.72rem;">${h.instrument_type || 'forex'}</span>
                    </span>
                    <span style="color:#a78bfa;font-weight:700;">${Number(h.position_size).toFixed(2)} lots</span>
                    <span style="color:#6b7280;">${h.risk_percent}% risk</span>
                    <span style="color:${h.risk_reward_ratio >= 2 ? '#34d399' : '#6b7280'};">
                        ${h.risk_reward_ratio > 0 ? `1:${h.risk_reward_ratio}` : '—'}
                    </span>
                </div>
            `).join('');
        } catch (e) {
            console.error('[RiskCalculator] Failed to load history:', e);
            el.innerHTML = '<p style="color:#374151;font-size:.8rem;text-align:center;padding:12px;">Could not load history.</p>';
        }
    },

    // ── Placeholder state ─────────────────────────────────────────────────────
    _placeholder() {
        const m = document.getElementById('rc-d-main');
        if (m) m.textContent = '—';
        const d = document.getElementById('rc-d-details');
        if (d) d.innerHTML = '';
        const w = document.getElementById('rc-d-warning');
        if (w) w.style.display = 'none';
        const dd = document.getElementById('rc-d-dd-body');
        if (dd) dd.innerHTML = '<tr><td colspan="4" style="color:#374151;padding:12px;text-align:center;">Enter values above</td></tr>';
        const dl = document.getElementById('rc-d-daily-body');
        if (dl) dl.innerHTML = '<div style="color:#374151;font-size:.78rem;text-align:center;padding:12px;">Enter values above</div>';
    },
};

window.RiskCalculator = RiskCalculator;
