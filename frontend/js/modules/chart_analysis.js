/**
 * chart_analysis.js — Chart Analysis Module
 * frontend/js/modules/chart_analysis.js  →  served at /js/modules/chart_analysis.js
 *
 * Depends on: window.dashboard (DashboardController), window.API
 * Both are guaranteed to exist when this script runs because dashboard.html
 * loads this AFTER the inline <script> block that defines them.
 */

// ── CSS custom property shims ────────────────────────────────────────────────
// Mirror the values used in dashboard.html's <style> block so the dynamically
// rendered chart analysis markup styles correctly.
(function setCSSVars() {
    const vars = {
        '--primary':  '#7c3aed', '--info':    '#3b82f6', '--success': '#10b981',
        '--danger':   '#ef4444', '--warning': '#f59e0b',
        '--gray-50':  '#f9fafb', '--gray-100':'#f3f4f6', '--gray-200':'#e5e7eb',
        '--gray-300': '#d1d5db', '--gray-400':'#9ca3af', '--gray-500':'#6b7280',
        '--gray-600': '#4b5563', '--gray-700':'#374151', '--gray-800':'#1f2937',
        '--gray-900': '#111827', '--radius':  '0.75rem',
    };
    Object.entries(vars).forEach(([k, v]) =>
        document.documentElement.style.setProperty(k, v));
})();

// ── ChartAnalysisPage ─────────────────────────────────────────────────────────
const ChartAnalysisPage = {
    currentAnalysis: null,
    uploadedImage:   null,
    chartAnnotations: null,

    async render(containerId = 'app') {
        const app = document.getElementById(containerId);
        if (!app) return;

        app.innerHTML = `
            <div style="margin-bottom:1.25rem;">
                <h1 style="font-size:1.1rem;font-weight:700;color:white;margin:0 0 .2rem;">📊 AI Chart Analysis</h1>
                <p style="font-size:.8rem;color:var(--gray-500);margin:0;">Smart Money Concepts (SMC) Institutional Analysis</p>
            </div>

            <!-- Step 1: Upload + Analyze -->
            <div class="card" style="margin-bottom:1.25rem;background:linear-gradient(135deg,var(--gray-800) 0%,var(--gray-900) 100%);">
                <div class="card-body" style="padding:1.25rem;">
                    <div style="font-size:.75rem;font-weight:700;color:var(--primary);text-transform:uppercase;
                                letter-spacing:.05em;margin-bottom:.75rem;">
                        Step 1 — Upload Chart
                    </div>
                    <div class="upload-area" id="dropZone"
                         onclick="document.getElementById('chartInput').click()"
                         style="padding:1.5rem;">
                        <div style="font-size:2.5rem;margin-bottom:.5rem;">📈</div>
                        <h3 style="margin:0 0 .25rem;font-size:.95rem;">Drop chart image here</h3>
                        <p style="color:var(--gray-500);margin:0;font-size:.8rem;">or click to browse · PNG, JPG, WEBP (max 10MB)</p>
                        <input type="file" id="chartInput" accept="image/*" style="display:none;"
                               onchange="ChartAnalysisPage.handleFile(this.files[0])">
                    </div>

                    <div id="imagePreview" style="display:none;margin-top:1rem;">
                        <div style="position:relative;border-radius:var(--radius);overflow:hidden;
                                    border:1px solid var(--gray-300);">
                            <img id="previewImg" style="width:100%;height:auto;display:block;" />
                            <button onclick="ChartAnalysisPage.clearImage()"
                                    style="position:absolute;top:0.5rem;right:0.5rem;
                                           background:rgba(0,0,0,0.7);color:white;border:none;
                                           border-radius:50%;width:32px;height:32px;cursor:pointer;
                                           display:flex;align-items:center;justify-content:center;">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>

                    <!-- Symbol + Timeframe -->
                    <div class="grid grid-cols-2 gap-3 mt-3">
                        <div class="form-group mb-0">
                            <label style="font-size:.75rem;color:var(--gray-500);">Symbol (optional)</label>
                            <input type="text" id="chartSymbol" placeholder="Auto-detected" class="form-control">
                        </div>
                        <div class="form-group mb-0">
                            <label style="font-size:.75rem;color:var(--gray-500);">Timeframe (optional)</label>
                            <select id="chartTimeframe" class="form-control">
                                <option value="">Auto-detect</option>
                                <option value="5M">5M</option>
                                <option value="15M">15M</option>
                                <option value="1H">1H</option>
                                <option value="4H">4H</option>
                                <option value="1D">1D</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Step 2: Analysis Results -->
            <div style="font-size:.75rem;font-weight:700;color:var(--primary);text-transform:uppercase;
                        letter-spacing:.05em;margin-bottom:.75rem;">
                Step 2 — AI Analysis
            </div>
            <div id="chartResults" style="margin-bottom:1.25rem;">
                <div class="card" style="text-align:center;padding:3rem;">
                    <p class="text-muted">Upload a chart above to see AI analysis</p>
                    <small>The AI will identify structure, OBs, FVGs and generate a trade setup</small>
                </div>
            </div>

            <!-- Step 3: Trade Validator -->
            <div class="card" style="background:linear-gradient(135deg,var(--gray-800) 0%,var(--gray-900) 100%);">
                <div class="card-header" style="border-bottom:1px solid var(--gray-700);">
                    <h3 class="card-title" style="display:flex;align-items:center;gap:0.5rem;">
                        <i class="fas fa-shield-alt text-primary"></i> Step 3 — Validate Your Setup
                    </h3>
                    <p style="margin:.25rem 0 0;font-size:.75rem;color:var(--gray-500);">
                        Modify the AI levels or enter your own — then validate against the analysis.
                    </p>
                </div>
                <div class="card-body">
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                        <div class="form-group mb-0">
                            <label style="font-size:0.75rem;color:var(--gray-500);">Entry Price</label>
                            <input type="number" id="validatorEntry" step="0.00001"
                                   class="form-control" placeholder="e.g. 4465">
                        </div>
                        <div class="form-group mb-0">
                            <label style="font-size:0.75rem;color:var(--gray-500);">Direction</label>
                            <select id="validatorDirection" class="form-control">
                                <option value="BUY">BUY</option>
                                <option value="SELL">SELL</option>
                            </select>
                        </div>
                        <div class="form-group mb-0">
                            <label style="font-size:0.75rem;color:var(--gray-500);">Stop Loss</label>
                            <input type="number" id="validatorSL" step="0.00001"
                                   class="form-control" placeholder="e.g. 4400">
                        </div>
                        <div class="form-group mb-0">
                            <label style="font-size:0.75rem;color:var(--gray-500);">Take Profit</label>
                            <input type="number" id="validatorTP" step="0.00001"
                                   class="form-control" placeholder="e.g. 4580">
                        </div>
                    </div>
                    <button onclick="ChartAnalysisPage.validateTrade()"
                            class="btn btn-primary btn-block"
                            style="background:linear-gradient(90deg,var(--primary) 0%,var(--info) 100%);">
                        <i class="fas fa-check-circle"></i> Validate Setup
                    </button>
                    <div id="validatorResults" style="display:none;margin-top:1rem;"></div>
                </div>
            </div>

            <div style="margin-top:2.5rem;">
                <h3 style="font-size:1rem;font-weight:600;color:white;margin-bottom:.75rem;">Pattern Library</h3>
                <div id="patternGrid"
                     style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(250px,100%),1fr));
                            gap:1rem;">
                    Loading patterns...
                </div>
            </div>`;

        const dropZone = document.getElementById('dropZone');
        if (dropZone) {
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.style.borderColor = 'var(--primary)';
                dropZone.style.background  = '#1e1b4b';
            });
            dropZone.addEventListener('dragleave', () => {
                dropZone.style.borderColor = '#4b5563';
                dropZone.style.background  = '#111827';
            });
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                const file = e.dataTransfer.files[0];
                if (file && file.type.startsWith('image/')) this.handleFile(file);
            });
        }

        this.loadPatterns();
    },

    handleFile(file) {
        if (!file) return;
        if (file.size > 10 * 1024 * 1024) { this._toast('File too large (max 10MB)', 'error'); return; }
        this.uploadedImage = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            const previewDiv = document.getElementById('imagePreview');
            const previewImg = document.getElementById('previewImg');
            if (previewImg) previewImg.src = e.target.result;
            if (previewDiv) previewDiv.style.display = 'block';
        };
        reader.readAsDataURL(file);
        // Rec 7: Show analyze button instead of auto-triggering
        // User can set symbol/timeframe before clicking
        const resultsDiv = document.getElementById('chartResults');
        if (resultsDiv) resultsDiv.innerHTML = `
            <div style="text-align:center;padding:3rem;background:#111827;border-radius:12px;border:1px solid #374151;">
                <div style="font-size:2.5rem;margin-bottom:1rem;">📊</div>
                <p style="color:white;font-weight:600;margin-bottom:.5rem;">Chart ready for analysis</p>
                <p style="color:#9ca3af;font-size:.875rem;margin-bottom:1.5rem;">
                    Optionally set the symbol and timeframe above, then click Analyze.
                </p>
                <button onclick="ChartAnalysisPage.analyzeChart(ChartAnalysisPage.uploadedImage)"
                        style="padding:12px 32px;background:linear-gradient(90deg,#7c3aed,#3b82f6);
                               color:white;border:none;border-radius:8px;font-weight:700;
                               font-size:1rem;cursor:pointer;letter-spacing:.03em;">
                    <i class="fas fa-robot" style="margin-right:8px;"></i>Analyze Chart
                </button>
            </div>`;
    },

    clearImage() {
        if (this._retryTimeout) { clearTimeout(this._retryTimeout); this._retryTimeout = null; }
        this.uploadedImage    = null;
        this.currentAnalysis  = null;
        this.chartAnnotations = null;
        const previewDiv  = document.getElementById('imagePreview');
        const chartInput  = document.getElementById('chartInput');
        const results     = document.getElementById('chartResults');
        const valResults  = document.getElementById('validatorResults');
        if (previewDiv)  previewDiv.style.display = 'none';
        if (chartInput)  chartInput.value = '';
        if (valResults) { valResults.style.display = 'none'; valResults.innerHTML = ''; }
        // Fix 3: also reset results panel so stale analysis doesn't show
        if (results) results.innerHTML = `
            <div class="card" style="text-align:center;padding:3rem;">
                <p class="text-muted">Upload a chart to see AI analysis</p>
                <small>Supports: PNG, JPG, JPEG, WEBP (max 10MB)</small>
            </div>`;
        // Fix 2: clear validator inputs when image is cleared
        ['validatorEntry','validatorSL','validatorTP'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
        const dirEl = document.getElementById('validatorDirection');
        if (dirEl) dirEl.value = 'BUY';
    },

    async analyzeChart(file, _retryCount = 0) {
        const results = document.getElementById('chartResults');
        if (!results) return;

        // ── Client-side usage gate ────────────────────────────────────────────
        if (window.PipwaysUsage?.isLoaded) {
            const check = window.PipwaysUsage.checkUsage('chart_analysis');
            if (!check.allowed) {
                results.innerHTML = `
                    <div style="text-align:center;padding:3rem;background:#111827;border-radius:12px;border:1px solid #374151;">
                        <div style="font-size:2.5rem;margin-bottom:1rem;">🔒</div>
                        <p style="color:white;font-weight:700;font-size:1.1rem;margin-bottom:.5rem;">Free limit reached</p>
                        <p style="color:#9ca3af;font-size:.875rem;margin-bottom:1.5rem;">
                            You've used all ${check.limit} free chart analyses today.<br>Upgrade to Pro for 50/day.
                        </p>
                        <div style="display:flex;gap:.75rem;justify-content:center;flex-wrap:wrap;">
                            <button onclick="window.PaymentsPage ? PaymentsPage.startPayment('pro_monthly') : window.location.href='/pricing.html'"
                                style="padding:10px 24px;background:#7c3aed;color:white;border:none;
                                       border-radius:8px;font-weight:700;font-size:.9rem;cursor:pointer;">
                                Upgrade to Pro →
                            </button>
                        </div>
                    </div>`;
                window.PipwaysUsage.showUpgradeModal('chart_analysis');
                return;
            }
        }

        results.innerHTML = `<div class="loading" style="text-align:center;padding:3rem;">
            <div class="spinner" style="margin:0 auto 1rem;"></div>
            <p>Analyzing chart with AI Vision…</p>
            <small>This may take 10–20 seconds</small>
        </div>`;

        const symbol    = document.getElementById('chartSymbol')?.value    || null;
        const timeframe = document.getElementById('chartTimeframe')?.value || null;

        try {
            const analysis = await API.analyzeChartImage(file, symbol, timeframe);
            this.currentAnalysis = analysis;
            if (analysis.chart_annotations) this.chartAnnotations = analysis.chart_annotations;
            this.displayResults(analysis);
            // Refresh usage badge so remaining count updates immediately
            if (window.PipwaysUsage) window.PipwaysUsage.loadUserLimits();

        } catch (error) {
            // ── 402 limit reached — show upgrade modal instead of raw error ──
            if (error.message && (error.message.includes('limit_reached') || error.message.includes('402'))) {
                // Show upgrade UI
                if (results) results.innerHTML = `
                    <div style="text-align:center;padding:3rem;background:#111827;border-radius:12px;border:1px solid #374151;">
                        <div style="font-size:2.5rem;margin-bottom:1rem;">🔒</div>
                        <p style="color:white;font-weight:700;font-size:1.1rem;margin-bottom:.5rem;">Free limit reached</p>
                        <p style="color:#9ca3af;font-size:.875rem;margin-bottom:1.5rem;">
                            You've used all your free chart analyses.<br>Upgrade to Pro for unlimited access.
                        </p>
                        <div style="display:flex;gap:.75rem;justify-content:center;flex-wrap:wrap;">
                            <button onclick="window.PaymentsPage ? PaymentsPage.startPayment('pro_monthly') : window.location.href='/pricing.html'"
                                style="padding:10px 24px;background:#7c3aed;color:white;border:none;
                                       border-radius:8px;font-weight:700;font-size:.9rem;cursor:pointer;">
                                Upgrade to Pro →
                            </button>
                            <a href="/pricing.html"
                                style="padding:10px 24px;background:#1f2937;color:#9ca3af;border:1px solid #374151;
                                       border-radius:8px;font-weight:600;font-size:.9rem;text-decoration:none;
                                       display:inline-flex;align-items:center;">
                                See Plans
                            </a>
                        </div>
                    </div>`;

                // Also trigger the upgrade modal if available
                setTimeout(() => {
                    if (window.PipwaysUsage && PipwaysUsage.showUpgradeModal) {
                        PipwaysUsage.showUpgradeModal('chart_analysis',
                            PipwaysUsage.used('chart_analysis'),
                            PipwaysUsage.limit('chart_analysis'));
                    } else if (window.PaymentsPage) {
                        PaymentsPage.showUpgradeModal('Chart Analysis');
                    }
                }, 300);
                return;
            }

            const MAX_RETRIES = 3;
            if (error.isColdStart && _retryCount < MAX_RETRIES) {
                const next = _retryCount + 1;
                let secs   = 10;
                const tick = () => {
                    // Bug 4 fix: check if user cleared the image during countdown
                    if (!this.uploadedImage || !document.getElementById('chartResults')) return;
                    results.innerHTML = `
                        <div style="text-align:center;padding:3rem;">
                            <div style="font-size:2.5rem;margin-bottom:1rem;">🌙</div>
                            <p style="color:#f59e0b;font-weight:600;margin-bottom:0.5rem;">Server is waking up…</p>
                            <p style="color:#9ca3af;font-size:0.875rem;margin-bottom:1.5rem;">
                                Retrying in <strong style="color:white;">${secs}s</strong>
                                (attempt ${next}/${MAX_RETRIES})
                            </p>
                            <div style="width:200px;height:4px;background:#374151;border-radius:2px;margin:0 auto;">
                                <div style="width:${Math.round(((10-secs)/10)*100)}%;height:100%;
                                            background:#f59e0b;border-radius:2px;transition:width 0.9s linear;"></div>
                            </div>
                            <button onclick="ChartAnalysisPage.analyzeChart(ChartAnalysisPage.uploadedImage)"
                                    style="margin-top:1.5rem;padding:0.5rem 1.5rem;background:#7c3aed;color:white;
                                           border:none;border-radius:0.5rem;cursor:pointer;font-size:0.875rem;">
                                Retry now
                            </button>
                        </div>`;
                    if (secs <= 0) { this.analyzeChart(file, next); return; }
                    secs--;
                    this._retryTimeout = setTimeout(tick, 1000);
                };
                tick();
                return;
            }

            this.uploadedImage   = null;
            this.currentAnalysis = null;
            const exhausted = error.isColdStart && _retryCount >= MAX_RETRIES;
            let userMsg;
            if (exhausted) {
                userMsg = 'The server is taking too long to wake up. Please wait 30 seconds and try again.';
            } else {
                try {
                    const parsed = JSON.parse(error.message);
                    userMsg = parsed.detail || parsed.error || error.message;
                } catch (_) {
                    userMsg = error.message;
                }
            }
            results.innerHTML = `
                <div class="alert alert-error" style="padding:1.25rem;">
                    <div style="font-weight:600;margin-bottom:0.5rem;">
                        ${exhausted ? '⏳ Server not ready' : '❌ Analysis failed'}
                    </div>
                    <div style="font-size:0.875rem;">${userMsg}</div>
                    ${exhausted ? `<button onclick="ChartAnalysisPage.clearImage()"
                        style="margin-top:1rem;padding:0.4rem 1rem;background:rgba(239,68,68,.2);
                               color:#f87171;border:1px solid rgba(239,68,68,.4);border-radius:.5rem;
                               cursor:pointer;font-size:.8rem;">Clear &amp; try again</button>` : ''}
                </div>`;
        }
    },

    // Bug 3 fix: HTML escape all AI-generated text before innerHTML insertion
    _esc(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    },

    // Rec 8: toast notification — uses existing dashboard toast if available
    _toast(msg, type = 'success') {
        if (window.dashboard && dashboard.showToast) {
            dashboard.showToast(msg, type);
        } else if (window.showToast) {
            showToast(msg, type);
        } else {
            console.log(`[${type}] ${msg}`);
        }
    },

    displayResults(analysis) {
        const container = document.getElementById('chartResults');
        if (!container) return;

        const biasColor = analysis.trading_bias === 'bullish' ? 'var(--success)' :
                          analysis.trading_bias === 'bearish' ? 'var(--danger)'  : 'var(--gray-500)';
        const biasBg    = analysis.trading_bias === 'bullish' ? 'rgba(16,185,129,.1)' :
                          analysis.trading_bias === 'bearish' ? 'rgba(239,68,68,.1)'  : 'rgba(107,114,128,.1)';

        let marketStructureHTML = '';
        if (analysis.market_structure) {
            const msColor = analysis.market_structure === 'bullish' ? 'var(--success)' :
                            analysis.market_structure === 'bearish' ? 'var(--danger)'  : 'var(--gray-500)';
            marketStructureHTML = `
                <div style="background:rgba(0,0,0,.2);border-radius:var(--radius);padding:1rem;
                            margin-bottom:1.5rem;border-left:4px solid ${msColor};">
                    <div style="font-size:.75rem;color:var(--gray-500);text-transform:uppercase;
                                margin-bottom:.5rem;">Market Structure</div>
                    <div style="font-size:1.25rem;font-weight:700;color:${msColor};
                                text-transform:uppercase;">${analysis.market_structure}</div>
                </div>`;
        }

        let smcSignalsHTML = '';
        if (analysis.smc_signals?.length) {
            smcSignalsHTML = `
                <div style="margin-bottom:1.5rem;">
                    <strong style="display:block;margin-bottom:.75rem;color:var(--gray-300);">
                        <i class="fas fa-university mr-2" style="color:var(--primary);"></i>SMC Signals:
                    </strong>
                    <ul style="padding-left:0;margin:0;list-style:none;">
                        ${analysis.smc_signals.map(s => `
                        <li style="margin-bottom:.5rem;color:var(--gray-400);display:flex;align-items:flex-start;">
                            <i class="fas fa-check-circle mr-2 mt-1"
                               style="font-size:.75rem;color:var(--success);"></i>
                            <span>${this._esc(s)}</span>
                        </li>`).join('')}
                    </ul>
                </div>`;
        }

        let tradeSetupHTML = '';
        if (analysis.trade_setup) {
            const setup = analysis.trade_setup;

            // Infer direction from price geometry if AI returned NEUTRAL
            let dir = (setup.direction || 'NEUTRAL').toUpperCase();
            if (dir === 'NEUTRAL') {
                const e = parseFloat(String(setup.entry).replace(',', ''));
                const t = parseFloat(String(setup.take_profit).replace(',', ''));
                if (!isNaN(e) && !isNaN(t)) dir = t > e ? 'BUY' : 'SELL';
            }
            const dirColor = dir === 'BUY' ? 'var(--success)' : 'var(--danger)';

            // Auto-fill symbol input with AI-detected value
            const symInput = document.getElementById('chartSymbol');
            if (symInput && analysis.symbol && analysis.symbol !== 'Unknown') {
                symInput.value = analysis.symbol;
            }

            // Fix 2: Detect LIMIT ORDER vs MARKET ORDER
            // BUY LIMIT:  entry is below current price — waiting for pullback down to entry
            // SELL LIMIT: entry is above current price — waiting for pullback up to entry
            // We detect this by comparing entry against the dealing range high/low
            let orderTypeLabel = '';
            const entryNum = parseFloat(String(setup.entry).replace(',', ''));
            const approxRange = analysis.chart_annotations?.premium_discount?.range || [];
            const rangeHigh = parseFloat(approxRange[1]);
            const rangeLow  = parseFloat(approxRange[0]);
            const rangeMid  = (!isNaN(rangeHigh) && !isNaN(rangeLow)) ? (rangeHigh + rangeLow) / 2 : null;

            let isPendingOrder = false;
            let orderTypeText  = '';

            if (!isNaN(entryNum) && rangeMid !== null) {
                const isPendingBuy  = dir === 'BUY'  && entryNum < rangeMid * 0.999;
                const isPendingSell = dir === 'SELL' && entryNum > rangeMid * 1.001;
                if (isPendingBuy)  { isPendingOrder = true; orderTypeText = `BUY LIMIT — wait for price to pull BACK DOWN to ${this._esc(String(setup.entry))}`; }
                if (isPendingSell) { isPendingOrder = true; orderTypeText = `SELL LIMIT — wait for price to pull BACK UP to ${this._esc(String(setup.entry))}`; }
            }

            if (isPendingOrder) {
                orderTypeLabel = `
                <div style="background:rgba(245,158,11,.12);border:1px solid rgba(245,158,11,.4);
                            border-radius:.5rem;padding:.6rem .75rem;margin-bottom:1rem;
                            display:flex;align-items:center;gap:.5rem;font-size:.8rem;">
                    <span style="font-size:1rem;">⏳</span>
                    <div>
                        <span style="color:#f59e0b;font-weight:700;">PENDING LIMIT ORDER</span>
                        <span style="color:#9ca3af;margin-left:.35rem;">${orderTypeText}</span>
                    </div>
                </div>`;
            } else {
                orderTypeLabel = `
                <div style="background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.3);
                            border-radius:.5rem;padding:.6rem .75rem;margin-bottom:1rem;
                            display:flex;align-items:center;gap:.5rem;font-size:.8rem;">
                    <span style="font-size:1rem;">⚡</span>
                    <div>
                        <span style="color:#10b981;font-weight:700;">MARKET ORDER</span>
                        <span style="color:#9ca3af;margin-left:.35rem;">Entry is at or near current price — can enter now</span>
                    </div>
                </div>`;
            }

            tradeSetupHTML = `
                <div style="background:linear-gradient(135deg,rgba(124,58,237,.1) 0%,rgba(59,130,246,.1) 100%);
                            border:1px solid var(--primary);border-radius:var(--radius);
                            padding:1.25rem;margin:1.5rem 0;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
                        <h4 style="margin:0;color:var(--primary);display:flex;align-items:center;gap:.5rem;">
                            <i class="fas fa-robot"></i> AI Signal Engine
                        </h4>
                        <span style="background:var(--primary);color:white;padding:.25rem .75rem;
                                     border-radius:9999px;font-size:.75rem;font-weight:600;">
                            ${Math.round((setup.probability || .7) * 100)}% Confidence
                        </span>
                    </div>
                    ${orderTypeLabel}
                    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:1rem;">
                        <div style="text-align:center;padding:.75rem;background:rgba(0,0,0,.2);border-radius:var(--radius);">
                            <div style="font-size:.75rem;color:var(--gray-500);margin-bottom:.25rem;">Entry</div>
                            <div style="font-size:1.25rem;font-weight:700;color:var(--gray-100);">${setup.entry||'--'}</div>
                        </div>
                        <div style="text-align:center;padding:.75rem;background:rgba(239,68,68,.2);border-radius:var(--radius);">
                            <div style="font-size:.75rem;color:var(--gray-500);margin-bottom:.25rem;">Stop Loss</div>
                            <div style="font-size:1.25rem;font-weight:700;color:var(--danger);">${setup.stop_loss||'--'}</div>
                        </div>
                        <div style="text-align:center;padding:.75rem;background:rgba(16,185,129,.2);border-radius:var(--radius);">
                            <div style="font-size:.75rem;color:var(--gray-500);margin-bottom:.25rem;">Take Profit</div>
                            <div style="font-size:1.25rem;font-weight:700;color:var(--success);">${setup.take_profit||'--'}</div>
                        </div>
                    </div>
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;
                                padding:.75rem;background:rgba(0,0,0,.2);border-radius:var(--radius);">
                        <div>
                            <span style="color:var(--gray-500);font-size:.875rem;">Risk:Reward</span>
                            <span style="color:var(--primary);font-weight:700;margin-left:.5rem;">${setup.risk_reward||'N/A'}</span>
                        </div>
                        <div>
                            <span style="color:var(--gray-500);font-size:.875rem;">Direction</span>
                            <span style="color:${dirColor};font-weight:700;margin-left:.5rem;">${dir}</span>
                        </div>
                    </div>
                    <button onclick="ChartAnalysisPage.saveSignal()"
                            class="btn btn-success btn-block"
                            style="background:linear-gradient(90deg,var(--success) 0%,#059669 100%);">
                        <i class="fas fa-save"></i> Save Signal to Dashboard
                    </button>
                    ${!this._isAdmin() ? `
                    <p style="margin-top:8px;font-size:11px;color:#6b7280;text-align:center;">
                        <i class="fas fa-lock" style="margin-right:4px;"></i>
                        Signal publishing is admin-only to maintain signal quality.
                    </p>` : ''}
                </div>`;

            // Auto-fill validator with AI trade setup levels
            const eEl = document.getElementById('validatorEntry');
            const sEl = document.getElementById('validatorSL');
            const tEl = document.getElementById('validatorTP');
            const dEl = document.getElementById('validatorDirection');
            if (eEl) eEl.value = setup.entry || '';
            if (sEl) sEl.value = setup.stop_loss || '';
            if (tEl) tEl.value = setup.take_profit || '';
            if (dEl) dEl.value = dir === 'BUY' ? 'BUY' : 'SELL';
        } else {
            // Fix 2: No trade setup — clear validator so stale values don't mislead
            ['validatorEntry','validatorSL','validatorTP'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.value = '';
            });
        }

        const patternsHTML = (analysis.patterns_detected?.length)
            ? analysis.patterns_detected.map(p =>
                `<span class="badge badge-info" style="margin:.25rem;padding:.5rem 1rem;">
                    ${p.name||'Pattern'} <small style="opacity:.7;">(${p.reliability||'medium'})</small>
                </span>`).join('')
            : '<span class="text-muted">No patterns detected</span>';

        let annotationsHTML = '';
        if (analysis.chart_annotations?.order_blocks?.length ||
            analysis.chart_annotations?.fair_value_gaps?.length) {
            annotationsHTML = `
                <div style="margin-bottom:1.5rem;padding:1rem;
                            background:rgba(124,58,237,.05);border:1px solid rgba(124,58,237,.2);
                            border-radius:var(--radius);">
                    <strong style="display:block;margin-bottom:.5rem;color:var(--primary);font-size:.875rem;">
                        <i class="fas fa-layer-group mr-2"></i>Chart Annotations Ready
                    </strong>
                    <div style="font-size:.75rem;color:var(--gray-500);">
                        ${analysis.chart_annotations.order_blocks?.length||0} Order Blocks,
                        ${analysis.chart_annotations.fair_value_gaps?.length||0} FVGs,
                        ${analysis.chart_annotations.liquidity_zones?.length||0} Liquidity Zones
                    </div>
                </div>`;
        }

        container.innerHTML = `
            <div class="card">
                <div style="display:flex;justify-content:space-between;align-items:center;
                            margin-bottom:1.5rem;padding-bottom:1rem;border-bottom:1px solid var(--gray-700);">
                    <h3 style="margin:0;">${this._esc(analysis.symbol||'Unknown Symbol')}</h3>
                    <div style="display:flex;gap:.5rem;">
                        <span class="badge badge-${(analysis.confidence||0)>.7?'success':'warning'}">
                            ${Math.round((analysis.confidence||0)*100)}% Confidence
                        </span>
                        ${analysis.mode==='ai'?'<span class="badge badge-info">SMC AI</span>':''}
                    </div>
                </div>
                <div style="background:${biasBg};border:1px solid ${biasColor};
                            border-radius:var(--radius);padding:1rem;margin-bottom:1.5rem;text-align:center;">
                    <div style="font-size:.875rem;color:var(--gray-500);margin-bottom:.5rem;">Trading Bias</div>
                    <div style="font-size:1.5rem;font-weight:700;color:${biasColor};
                                text-transform:uppercase;letter-spacing:.05em;">
                        ${analysis.trading_bias||'Neutral'}
                    </div>
                </div>
                ${marketStructureHTML}
                ${analysis.chart_image?`
                    <div style="margin-bottom:1.5rem;">
                        <div style="font-size:.875rem;color:var(--gray-500);margin-bottom:.5rem;">Analyzed Chart</div>
                        <img src="${analysis.chart_image}"
                             style="width:100%;border-radius:var(--radius);border:1px solid var(--gray-700);" />
                    </div>`:''}
                ${annotationsHTML}
                ${tradeSetupHTML}
                ${smcSignalsHTML}
                <div style="margin-bottom:1.5rem;">
                    <strong style="display:block;margin-bottom:.75rem;color:var(--gray-300);">Patterns Detected:</strong>
                    ${patternsHTML}
                </div>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(200px,100%),1fr));gap:1rem;margin-bottom:1.5rem;">
                    <div style="background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);
                                border-radius:var(--radius);padding:1rem;">
                        <div style="font-size:.75rem;color:var(--gray-500);text-transform:uppercase;
                                    margin-bottom:.5rem;">Resistance Levels</div>
                        ${analysis.resistance_levels?.length
                            ? analysis.resistance_levels.map(l=>
                                `<div style="font-family:monospace;color:var(--danger);
                                             font-weight:600;margin-bottom:.25rem;">${l}</div>`).join('')
                            : '<span class="text-muted">None detected</span>'}
                    </div>
                    <div style="background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.3);
                                border-radius:var(--radius);padding:1rem;">
                        <div style="font-size:.75rem;color:var(--gray-500);text-transform:uppercase;
                                    margin-bottom:.5rem;">Support Levels</div>
                        ${analysis.support_levels?.length
                            ? analysis.support_levels.map(l=>
                                `<div style="font-family:monospace;color:var(--success);
                                             font-weight:600;margin-bottom:.25rem;">${l}</div>`).join('')
                            : '<span class="text-muted">None detected</span>'}
                    </div>
                </div>
                <div>
                    <strong style="display:block;margin-bottom:.75rem;color:var(--gray-300);">
                        <i class="fas fa-lightbulb mr-2" style="color:var(--warning);"></i>Institutional Insights:
                    </strong>
                    <ul style="padding-left:1.5rem;margin:0;">
                        ${analysis.key_insights?.length
                            ? analysis.key_insights.map(i=>
                                `<li style="margin-bottom:.5rem;color:var(--gray-400);">${this._esc(i)}</li>`).join('')
                            : '<li class="text-muted">No specific insights</li>'}
                    </ul>
                </div>
            </div>`;
    },

    async validateTrade() {
        const eEl = document.getElementById('validatorEntry');
        const sEl = document.getElementById('validatorSL');
        const tEl = document.getElementById('validatorTP');
        const dEl = document.getElementById('validatorDirection');
        if (!eEl || !sEl || !tEl || !dEl) return;

        const entry     = parseFloat(eEl.value);
        const sl        = parseFloat(sEl.value);
        const tp        = parseFloat(tEl.value);
        const direction = dEl.value;
        const symbol    = (document.getElementById('chartSymbol')?.value || '').toUpperCase() || 'Unknown';

        if (!entry || !sl || !tp) {
            this._toast('Please fill in Entry, Stop Loss and Take Profit', 'error');
            return;
        }

        const rd = document.getElementById('validatorResults');
        if (!rd) return;
        rd.style.display = 'block';

        const result = this._validateSignal(entry, sl, tp, direction, symbol);

        const sc = result.score >= 80 ? '#00d084'
                 : result.score >= 60 ? '#f59e0b'
                 : '#ef4444';

        const verdict = result.score >= 80 ? '✅ High Quality Signal — Tradeable'
                      : result.score >= 60 ? '⚠️ Average Signal — Trade with caution'
                      : '❌ Poor Signal — Do Not Trade';

        rd.innerHTML = `
            <div style="background:var(--gray-900);border-radius:var(--radius);padding:1rem;
                        border:1px solid var(--gray-700);">

                <!-- Score header -->
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem;">
                    <span style="color:var(--gray-400);font-size:.8rem;font-weight:600;text-transform:uppercase;letter-spacing:.04em;">Signal Quality</span>
                    <span style="font-size:2rem;font-weight:800;color:${sc};">${result.score}<span style="font-size:1rem;color:var(--gray-500);">/100</span></span>
                </div>
                <div style="width:100%;height:8px;background:var(--gray-700);border-radius:4px;margin-bottom:.75rem;overflow:hidden;">
                    <div style="width:${result.score}%;height:100%;background:${sc};border-radius:4px;transition:width .6s ease;"></div>
                </div>
                <div style="padding:.6rem .75rem;border-radius:.5rem;margin-bottom:1rem;
                            background:rgba(0,0,0,.3);border-left:3px solid ${sc};
                            font-weight:700;font-size:.85rem;color:${sc};">${verdict}</div>

                <!-- Key metrics -->
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.5rem;margin-bottom:1rem;">
                    <div style="text-align:center;padding:.6rem;background:var(--gray-800);border-radius:.5rem;">
                        <div style="font-size:.65rem;color:var(--gray-500);text-transform:uppercase;margin-bottom:2px;">R:R</div>
                        <div style="font-size:1rem;font-weight:800;color:white;">${result.rr_text}</div>
                    </div>
                    <div style="text-align:center;padding:.6rem;background:var(--gray-800);border-radius:.5rem;">
                        <div style="font-size:.65rem;color:var(--gray-500);text-transform:uppercase;margin-bottom:2px;">TP Hit %</div>
                        <div style="font-size:1rem;font-weight:800;color:#00d084;">${result.tp_prob}%</div>
                    </div>
                    <div style="text-align:center;padding:.6rem;background:var(--gray-800);border-radius:.5rem;">
                        <div style="font-size:.65rem;color:var(--gray-500);text-transform:uppercase;margin-bottom:2px;">SL Risk</div>
                        <div style="font-size:1rem;font-weight:800;color:#ef4444;">${100 - result.tp_prob}%</div>
                    </div>
                </div>

                <!-- Score breakdown -->
                <div style="margin-bottom:.75rem;border:1px solid var(--gray-700);border-radius:.5rem;overflow:hidden;">
                    <div style="font-size:.7rem;color:var(--gray-500);text-transform:uppercase;
                                letter-spacing:.05em;padding:.4rem .75rem;background:var(--gray-800);
                                border-bottom:1px solid var(--gray-700);">Score Breakdown</div>
                    ${result.breakdown.map((b, i) => `
                        <div style="display:flex;justify-content:space-between;align-items:center;
                                    padding:.45rem .75rem;font-size:.8rem;
                                    ${i < result.breakdown.length-1 ? 'border-bottom:1px solid rgba(255,255,255,.04);' : ''}">
                            <span style="color:var(--gray-400);">${this._esc(b.label)}</span>
                            <div style="display:flex;align-items:center;gap:.5rem;">
                                <div style="width:60px;height:4px;background:var(--gray-700);border-radius:2px;">
                                    <div style="width:${Math.round((b.score/b.max)*100)}%;height:100%;
                                                background:${b.score/b.max >= .7 ? '#00d084' : b.score/b.max >= .4 ? '#f59e0b' : '#ef4444'};
                                                border-radius:2px;"></div>
                                </div>
                                <span style="font-weight:700;min-width:32px;text-align:right;
                                             color:${b.score/b.max >= .7 ? '#00d084' : b.score/b.max >= .4 ? '#f59e0b' : '#ef4444'};">
                                    ${b.score}/${b.max}
                                </span>
                            </div>
                        </div>`).join('')}
                </div>

                ${result.warnings.length ? `
                <div style="padding:.75rem;background:rgba(239,68,68,.08);border-radius:.5rem;
                            border-left:3px solid #ef4444;margin-bottom:.5rem;">
                    <div style="font-size:.7rem;color:#ef4444;font-weight:700;margin-bottom:.35rem;">⚠ Issues</div>
                    ${result.warnings.map(w=>`<div style="font-size:.8rem;color:var(--gray-300);margin-bottom:.2rem;">• ${this._esc(w)}</div>`).join('')}
                </div>` : ''}

                ${result.positives.length ? `
                <div style="padding:.75rem;background:rgba(0,208,132,.06);border-radius:.5rem;
                            border-left:3px solid #00d084;">
                    <div style="font-size:.7rem;color:#00d084;font-weight:700;margin-bottom:.35rem;">✓ Strengths</div>
                    ${result.positives.map(p=>`<div style="font-size:.8rem;color:var(--gray-300);margin-bottom:.2rem;">• ${this._esc(p)}</div>`).join('')}
                </div>` : ''}
            </div>`;
    },

    // ── Independent signal validator ──────────────────────────────────────────
    // Works completely independently of the chart analysis.
    // Evaluates any signal purely on its own merits — R:R, stop size,
    // target realism, and probability estimation.
    // Max score: 100 pts across 5 criteria.
    _validateSignal(entry, sl, tp, direction, symbol) {
        const warnings  = [];
        const positives = [];
        const breakdown = [];
        const isBuy     = direction === 'BUY';

        // ── Instrument detection — used across all scoring sections ──────────────
        const isGold    = symbol.includes('XAU') || symbol.includes('GOLD');
        const isIndex   = ['US30','US500','NAS100','UK100','DE30'].some(s => symbol.includes(s));
        const isJPY     = symbol.includes('JPY');
        const isCrypto  = ['BTC','ETH','XRP','LTC'].some(s => symbol.includes(s));

        // ── Basic geometry ────────────────────────────────────────────────────
        const risk      = Math.abs(entry - sl);
        const reward    = Math.abs(tp - entry);
        const rr        = risk > 0 ? reward / risk : 0;
        const rr_text   = rr > 0 ? `1:${rr.toFixed(2)}` : 'N/A';

        const slWrong = (isBuy && sl >= entry) || (!isBuy && sl <= entry);
        const tpWrong = (isBuy && tp <= entry) || (!isBuy && tp >= entry);
        if (slWrong) warnings.push(`Stop loss must be ${isBuy ? 'BELOW' : 'ABOVE'} entry for a ${direction}.`);
        if (tpWrong) warnings.push(`Take profit must be ${isBuy ? 'ABOVE' : 'BELOW'} entry for a ${direction}.`);

        // ── 1. Risk:Reward (30 pts) — instrument-aware thresholds ───────────────
        let rrScore = 0;
        const isHighVolatility = isGold || isIndex || isCrypto;
        const rrFullMarks  = isHighVolatility ? 2.5 : 3.0;
        const rrGoodMarks  = isHighVolatility ? 1.8 : 2.0;
        const rrAcceptable = isHighVolatility ? 1.4 : 1.5;

        if      (rr >= rrFullMarks)  { rrScore = 30; positives.push(`Excellent R:R of ${rr_text} for this instrument.`); }
        else if (rr >= rrGoodMarks)  { rrScore = 24; positives.push(`Strong R:R of ${rr_text}.`); }
        else if (rr >= rrAcceptable) { rrScore = 16; }
        else if (rr >= 1.0)          { rrScore =  8; warnings.push(`R:R of ${rr_text} is below the ${rrAcceptable} minimum for ${symbol || 'this instrument'}.`); }
        else if (rr >= 0.5)          { rrScore =  2; warnings.push(`R:R of ${rr_text} — risk outweighs reward. Avoid this setup.`); }
        else                         { rrScore =  0; warnings.push(`R:R of ${rr_text} — do not trade this signal.`); }
        breakdown.push({ label: `Risk:Reward Ratio (${rr_text})`, score: rrScore, max: 30 });

        // ── 2. Stop Loss Sizing (25 pts) ──────────────────────────────────────
        let slScore = 0;
        const stopPct = (risk / entry) * 100;

        // Instrument-based stop expectations
        let minPct, maxPct, idealLabel;
        if      (isGold)   { minPct = 0.3;  maxPct = 2.0; idealLabel = '0.3–2% (30–200 pts on gold)'; }
        else if (isIndex)  { minPct = 0.15; maxPct = 1.5; idealLabel = '0.15–1.5% of index price'; }
        else if (isCrypto) { minPct = 1.0;  maxPct = 5.0; idealLabel = '1–5% for crypto'; }
        else if (isJPY)    { minPct = 0.1;  maxPct = 0.8; idealLabel = '10–80 pips for JPY pairs'; }
        else               { minPct = 0.1;  maxPct = 0.8; idealLabel = '10–80 pips for forex'; }

        if (slWrong) {
            slScore = 0;
        } else if (stopPct >= minPct && stopPct <= maxPct) {
            slScore = 25;
            positives.push(`Stop size of ${stopPct.toFixed(2)}% is appropriate for ${symbol || 'this instrument'}.`);
        } else if (stopPct < minPct) {
            slScore = 8;
            warnings.push(`Stop of ${stopPct.toFixed(2)}% is very tight for ${symbol}. Typical: ${idealLabel}. Risk of early stop out on normal volatility.`);
        } else if (stopPct <= maxPct * 1.5) {
            slScore = 15;
            warnings.push(`Stop of ${stopPct.toFixed(2)}% is slightly wide — reducing position size is advised.`);
        } else {
            slScore = 3;
            warnings.push(`Stop of ${stopPct.toFixed(2)}% is excessively wide. This will require very small position size to manage risk.`);
        }
        breakdown.push({ label: 'Stop Loss Sizing', score: slScore, max: 25 });

        // ── 3. Target Realism (20 pts) ────────────────────────────────────────
        // Is the TP a realistic distance? Not too far, not too close.
        let tpScore = 0;
        const tpPct = (reward / entry) * 100;

        let maxRealistic;
        if      (isGold)   maxRealistic = 4.0;
        else if (isIndex)  maxRealistic = 3.0;
        else if (isCrypto) maxRealistic = 10.0;
        else               maxRealistic = 1.5;  // forex

        if (tpWrong) {
            tpScore = 0;
        } else if (tpPct <= maxRealistic && rr >= 1.5) {
            tpScore = 20;
            positives.push(`Target of ${tpPct.toFixed(2)}% is realistic and achievable for this instrument.`);
        } else if (tpPct <= maxRealistic * 1.5 && rr >= 1.2) {
            tpScore = 14;
        } else if (tpPct > maxRealistic * 2) {
            tpScore = 5;
            warnings.push(`Target of ${tpPct.toFixed(2)}% from entry may be over-extended. Consider a closer partial target first.`);
        } else {
            tpScore = 10;
        }
        breakdown.push({ label: 'Target Realism', score: tpScore, max: 20 });

        // ── 4. Probability Authenticity (15 pts) ──────────────────────────────
        // Signal authenticity — does the math make sense as a real trade?
        let authScore = 0;
        const hasValidGeometry  = !slWrong && !tpWrong;
        const hasReasonableStop = stopPct >= minPct * 0.5 && stopPct <= maxPct * 2;
        const hasPositiveRR     = rr >= 1.0;

        if (hasValidGeometry && hasReasonableStop && hasPositiveRR) {
            authScore = 15;
            positives.push('Signal geometry is valid — entry, stop and target are logically consistent.');
        } else if (hasValidGeometry && hasPositiveRR) {
            authScore = 10;
        } else if (hasValidGeometry) {
            authScore = 5;
        } else {
            authScore = 0;
            warnings.push('Signal geometry has errors — check that SL and TP are on the correct sides of entry.');
        }
        breakdown.push({ label: 'Signal Authenticity', score: authScore, max: 15 });

        // ── 5. Projected Win Rate / Edge (10 pts) ─────────────────────────────
        // Based purely on R:R — higher R:R means you can be wrong more often and still profit.
        // At 1:2 R:R you only need to win 34% of trades to break even.
        // At 1:3 R:R you only need to win 25%.
        let edgeScore = 0;
        const breakevenWinRate = rr > 0 ? (1 / (1 + rr)) * 100 : 100;

        if (breakevenWinRate <= 30) {
            edgeScore = 10;
            positives.push(`At ${rr_text} you only need a ${breakevenWinRate.toFixed(0)}% win rate to be profitable — strong statistical edge.`);
        } else if (breakevenWinRate <= 40) {
            edgeScore = 8;
            positives.push(`Breakeven win rate is ${breakevenWinRate.toFixed(0)}% — achievable with a solid strategy.`);
        } else if (breakevenWinRate <= 50) {
            edgeScore = 5;
        } else {
            edgeScore = 0;
            warnings.push(`You need to win more than ${breakevenWinRate.toFixed(0)}% of trades to profit at this R:R — very hard to sustain.`);
        }
        breakdown.push({ label: 'Statistical Edge', score: edgeScore, max: 10 });

        // ── Final score ───────────────────────────────────────────────────────
        const totalMax = breakdown.reduce((s, b) => s + b.max, 0);
        const raw      = breakdown.reduce((s, b) => s + b.score, 0);
        const score    = Math.round((raw / totalMax) * 100);

        // TP probability — derived from R:R and score
        // At 1:2 R:R with a good score, probability of TP hit ~55-65%
        const baseProbability = Math.round(50 + (rr - 1) * 8);
        const scoreBonus      = Math.round((score - 50) * 0.15);
        const tp_prob         = Math.min(82, Math.max(25, baseProbability + scoreBonus));

        return { score, rr_text, tp_prob, warnings, positives, breakdown };
    },


    // ── Admin check — mirrors dashboard._isAdminUser() ───────────────────────
    _isAdmin() {
        try {
            const user = JSON.parse(localStorage.getItem('pipways_user') || '{}');
            if (!user) return false;
            if (user.is_admin === true)     return true;
            if (user.role === 'admin')      return true;
            if (user.is_superuser === true) return true;
            const email = (user.email || '').toLowerCase();
            if (email === 'admin@pipways.com' ||
                email === 'contact@gopipways.com' ||
                email.startsWith('admin+')) return true;
            return false;
        } catch (_) { return false; }
    },

    async saveSignal() {
        // Admin only — public signals grid must stay clean and professional
        if (!this._isAdmin()) {
            this._toast('Only admins can publish signals to the dashboard.', 'error');
            return;
        }
        if (!this.currentAnalysis?.trade_setup) {
            this._toast('No trade setup to save', 'error');
            return;
        }
        const setup    = this.currentAnalysis.trade_setup;
        const analysis = this.currentAnalysis;
        let dir = (setup.direction || 'NEUTRAL').toUpperCase();
        if (dir === 'NEUTRAL') {
            const e = parseFloat(String(setup.entry).replace(',', ''));
            const t = parseFloat(String(setup.take_profit).replace(',', ''));
            if (!isNaN(e) && !isNaN(t)) dir = t > e ? 'BUY' : 'SELL';
        }

        try {
            const token = localStorage.getItem('pipways_token');
            const rationale = (analysis.key_insights || []).join('\n\n') ||
                `${analysis.trading_bias} bias on ${analysis.symbol}. ` +
                `${analysis.confluence_reason || ''}`;

            const payload = {
                symbol:          analysis.symbol || 'Unknown',
                direction:       dir,
                entry_price:     parseFloat(setup.entry),
                stop_loss:       parseFloat(setup.stop_loss),
                take_profit:     parseFloat(setup.take_profit),
                confidence:      Math.round((setup.probability || 0.7) * 100),
                rationale:       rationale,
                pattern_name:    (analysis.patterns_detected?.[0]?.name) || 'SMC Breakout',
                structure:       analysis.market_structure || 'breakout',
                bias_d1:         analysis.trading_bias === 'bullish' ? 'BULL' :
                                 analysis.trading_bias === 'bearish' ? 'BEAR' : 'NEUTRAL',
                bias_h4:         analysis.trading_bias === 'bullish' ? 'BULL' :
                                 analysis.trading_bias === 'bearish' ? 'BEAR' : 'NEUTRAL',
                bos_m5:          analysis.bos_confirmed ? (dir === 'BUY' ? 'UP' : 'DOWN') : 'NEUTRAL',
                timeframe:       'H1',
                source:          'chart_analysis',
                is_pattern_idea: true,
            };

            const res = await fetch('/api/signals', {
                method: 'POST',
                headers: {
                    'Content-Type':  'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify(payload),
            });

            if (res.ok) {
                this._toast(`✅ ${analysis.symbol} ${dir} signal published to Enhanced Signals!`, 'success');
            } else {
                const body = await res.json().catch(() => ({}));
                throw new Error(body.detail || `HTTP ${res.status}`);
            }
        } catch (error) {
            this._toast('Error saving signal: ' + error.message, 'error');
        }
    },

    async loadPatterns() {
        try {
            const patterns  = await API.getPatternLibrary();
            const container = document.getElementById('patternGrid');
            if (!container) return;
            const all = [
                ...(patterns.reversal||[]), ...(patterns.continuation||[]),
                ...(patterns.candlestick||[]), ...(patterns.smc||[]),
            ];
            container.innerHTML = all.map(p => `
                <div class="card" style="transition:transform .2s;"
                     onmouseover="this.style.transform='translateY(-4px)'"
                     onmouseout="this.style.transform='translateY(0)'">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem;">
                        <h4 style="margin:0;font-size:1rem;color:var(--gray-200);">${this._esc(p.name)}</h4>
                        <span class="badge badge-${p.type==='reversal'?'danger':p.type==='continuation'?'success':p.type==='smc'?'primary':'info'}"
                              style="font-size:.75rem;">${this._esc(p.type)}</span>
                    </div>
                    <p style="font-size:.875rem;color:var(--gray-500);margin-bottom:.75rem;">${this._esc(p.description)}</p>
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <small style="color:var(--success);font-weight:600;">${this._esc(p.success_rate)} success rate</small>
                        <span class="badge badge-${p.reliability==='high'?'success':p.reliability==='medium'?'warning':'secondary'}"
                              style="font-size:.7rem;">${this._esc(p.reliability)}</span>
                    </div>
                </div>`).join('');
        } catch (_) {
            const c = document.getElementById('patternGrid');
            if (c) c.innerHTML = '<span class="text-muted">Failed to load patterns</span>';
        }
    },
};

// ── Extend window.API with Chart Analysis methods ─────────────────────────────
// window.API and window.dashboard are set in dashboard.html's inline script block.

API.analyzeChartImage = async function(file, symbol, timeframe) {
    const token = localStorage.getItem('pipways_token');
    if (!token) { _handleAuthError(); throw new Error('Not authenticated'); }

    const formData = new FormData();
    formData.append('file', file);
    if (symbol)    formData.append('symbol', symbol);
    if (timeframe) formData.append('timeframe', timeframe);

    const response = await fetch(`${window.location.origin}/ai/chart/analyze`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
    });

    if (!response.ok) {
        if (response.status === 401) { _handleAuthError(); throw new Error('Session expired.'); }
        if (response.status === 413) throw new Error('Image too large (max 10MB).');
        if (response.status === 504) throw new Error('Analysis timed out. Try a smaller image.');
        if (response.status === 503) {
            let detail = '';
            try { const b = await response.clone().json(); detail = b.detail||''; } catch(_){}
            if (detail.toLowerCase().includes('auth') || detail.toLowerCase().includes('key'))
                throw new Error('AI service authentication failed. Check OPENROUTER_API_KEY.');
            if (detail.toLowerCase().includes('rate'))
                throw new Error('AI rate limit reached. Please wait.');
            const err = new Error(detail || 'COLD_START');
            err.isColdStart = !detail || detail.toLowerCase().includes('unavailable');
            throw err;
        }
        const detail = await _parseApiError(response);
        throw new Error(detail || 'Analysis failed');
    }
    return response.json();
};

API.validateTrade = function(params) {
    return dashboard.apiRequest('/ai/trade/validate', {
        method: 'POST', body: JSON.stringify(params),
    });
};

API.saveSignal = function(params) {
    return dashboard.apiRequest('/ai/signal/save', {
        method: 'POST', body: JSON.stringify(params),
    });
};

API.getPatternLibrary = function() {
    return dashboard.apiRequest('/ai/chart/pattern-library');
};
