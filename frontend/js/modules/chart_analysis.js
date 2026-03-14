const ChartAnalysisPage = {
    currentAnalysis: null,
    uploadedImage: null,

    async render() {
        const app = document.getElementById('app');

        app.innerHTML = `
            <div class="page-header">
                <h1>📊 AI Chart Analysis</h1>
                <p>Upload your charts for instant pattern recognition and trade setup generation</p>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                <div>
                    <div class="upload-area" id="dropZone" onclick="document.getElementById('chartInput').click()">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">📈</div>
                        <h3>Drop chart image here</h3>
                        <p style="color: var(--gray-500); margin-top: 0.5rem;">or click to browse</p>
                        <input type="file" id="chartInput" accept="image/*" style="display: none;" onchange="ChartAnalysisPage.handleFile(this.files[0])">
                    </div>

                    <!-- Image Preview Section -->
                    <div id="imagePreview" style="display: none; margin-top: 1rem;">
                        <div style="position: relative; border-radius: var(--radius); overflow: hidden; border: 1px solid var(--gray-300);">
                            <img id="previewImg" style="width: 100%; height: auto; display: block;" />
                            <button onclick="ChartAnalysisPage.clearImage()" style="position: absolute; top: 0.5rem; right: 0.5rem; background: rgba(0,0,0,0.7); color: white; border: none; border-radius: 50%; width: 32px; height: 32px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
                        <div class="form-group mb-0">
                            <label>Symbol (optional)</label>
                            <input type="text" id="chartSymbol" placeholder="EURUSD" class="form-control">
                        </div>
                        <div class="form-group mb-0">
                            <label>Timeframe (optional)</label>
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

                    <!-- Trade Validator Card -->
                    <div class="card" style="margin-top: 1.5rem; background: linear-gradient(135deg, var(--gray-800) 0%, var(--gray-900) 100%);">
                        <div class="card-header" style="border-bottom: 1px solid var(--gray-700);">
                            <h3 class="card-title" style="display: flex; align-items: center; gap: 0.5rem;">
                                <i class="fas fa-shield-alt text-primary"></i>
                                Trade Validator
                            </h3>
                        </div>
                        <div class="card-body">
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 1rem;">
                                <div class="form-group mb-0">
                                    <label style="font-size: 0.75rem; color: var(--gray-500);">Entry Price</label>
                                    <input type="number" id="validatorEntry" step="0.00001" class="form-control" placeholder="1.0850">
                                </div>
                                <div class="form-group mb-0">
                                    <label style="font-size: 0.75rem; color: var(--gray-500);">Direction</label>
                                    <select id="validatorDirection" class="form-control">
                                        <option value="BUY">BUY</option>
                                        <option value="SELL">SELL</option>
                                    </select>
                                </div>
                                <div class="form-group mb-0">
                                    <label style="font-size: 0.75rem; color: var(--gray-500);">Stop Loss</label>
                                    <input type="number" id="validatorSL" step="0.00001" class="form-control" placeholder="1.0800">
                                </div>
                                <div class="form-group mb-0">
                                    <label style="font-size: 0.75rem; color: var(--gray-500);">Take Profit</label>
                                    <input type="number" id="validatorTP" step="0.00001" class="form-control" placeholder="1.0900">
                                </div>
                            </div>
                            <button onclick="ChartAnalysisPage.validateTrade()" class="btn btn-primary btn-block" style="background: linear-gradient(90deg, var(--primary) 0%, var(--info) 100%);">
                                <i class="fas fa-check-circle"></i> Validate Setup
                            </button>
                            <div id="validatorResults" style="display: none; margin-top: 1rem;"></div>
                        </div>
                    </div>
                </div>

                <div id="chartResults">
                    <div class="card" style="text-align: center; padding: 3rem;">
                        <p class="text-muted">Upload a chart to see AI analysis</p>
                        <small>Supports: PNG, JPG, JPEG (max 5MB)</small>
                    </div>
                </div>
            </div>

            <div style="margin-top: 3rem;">
                <h3>Pattern Library</h3>
                <div id="patternGrid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin-top: 1rem;">
                    Loading patterns...
                </div>
            </div>
        `;

        // Setup drag and drop
        const dropZone = document.getElementById('dropZone');
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = 'var(--primary)';
            dropZone.style.background = '#eff6ff';
        });
        dropZone.addEventListener('dragleave', () => {
            dropZone.style.borderColor = 'var(--gray-300)';
            dropZone.style.background = 'var(--gray-50)';
        });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                this.handleFile(file);
            }
        });

        this.loadPatterns();
    },

    handleFile(file) {
        if (!file) return;

        if (file.size > 5 * 1024 * 1024) {
            UI.showToast('File too large (max 5MB)', 'error');
            return;
        }

        // Store file for later
        this.uploadedImage = file;

        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            const previewDiv = document.getElementById('imagePreview');
            const previewImg = document.getElementById('previewImg');
            previewImg.src = e.target.result;
            previewDiv.style.display = 'block';
        };
        reader.readAsDataURL(file);

        // Auto-analyze
        this.analyzeChart(file);
    },

    clearImage() {
        this.uploadedImage = null;
        document.getElementById('imagePreview').style.display = 'none';
        document.getElementById('chartInput').value = '';
        document.getElementById('chartResults').innerHTML = `
            <div class="card" style="text-align: center; padding: 3rem;">
                <p class="text-muted">Upload a chart to see AI analysis</p>
                <small>Supports: PNG, JPG, JPEG (max 5MB)</small>
            </div>
        `;
    },

    async analyzeChart(file) {
        const results = document.getElementById('chartResults');
        results.innerHTML = '<div class="loading" style="text-align: center; padding: 3rem;"><div class="spinner" style="margin: 0 auto 1rem;"></div><p>Analyzing chart with AI Vision...</p><small>This may take 10-20 seconds</small></div>';

        const symbol = document.getElementById('chartSymbol')?.value;
        const timeframe = document.getElementById('chartTimeframe')?.value;

        try {
            const analysis = await API.analyzeChartImage(file, symbol, timeframe);
            this.currentAnalysis = analysis;
            this.displayResults(analysis);
        } catch (error) {
            results.innerHTML = `<div class="alert alert-error">Analysis failed: ${error.message}</div>`;
        }
    },

    displayResults(analysis) {
        const container = document.getElementById('chartResults');

        const biasColor = analysis.trading_bias === 'bullish' ? 'var(--success)' : 
                         analysis.trading_bias === 'bearish' ? 'var(--danger)' : 'var(--gray-500)';

        const biasBg = analysis.trading_bias === 'bullish' ? 'rgba(16, 185, 129, 0.1)' : 
                      analysis.trading_bias === 'bearish' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(107, 114, 128, 0.1)';

        // Build trade setup HTML if available
        let tradeSetupHTML = '';
        if (analysis.trade_setup) {
            const setup = analysis.trade_setup;
            tradeSetupHTML = `
                <div style="background: linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%); border: 1px solid var(--primary); border-radius: var(--radius); padding: 1.25rem; margin: 1.5rem 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h4 style="margin: 0; color: var(--primary); display: flex; align-items: center; gap: 0.5rem;">
                            <i class="fas fa-robot"></i>
                            AI Trade Setup
                        </h4>
                        <span style="background: var(--primary); color: white; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">
                            ${Math.round((setup.probability || 0.7) * 100)}% Confidence
                        </span>
                    </div>

                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1rem;">
                        <div style="text-align: center; padding: 0.75rem; background: rgba(0,0,0,0.2); border-radius: var(--radius);">
                            <div style="font-size: 0.75rem; color: var(--gray-500); margin-bottom: 0.25rem;">Entry</div>
                            <div style="font-size: 1.25rem; font-weight: 700; color: var(--gray-100);">${setup.entry}</div>
                        </div>
                        <div style="text-align: center; padding: 0.75rem; background: rgba(239, 68, 68, 0.2); border-radius: var(--radius);">
                            <div style="font-size: 0.75rem; color: var(--gray-500); margin-bottom: 0.25rem;">Stop Loss</div>
                            <div style="font-size: 1.25rem; font-weight: 700; color: var(--danger);">${setup.stop_loss}</div>
                        </div>
                        <div style="text-align: center; padding: 0.75rem; background: rgba(16, 185, 129, 0.2); border-radius: var(--radius);">
                            <div style="font-size: 0.75rem; color: var(--gray-500); margin-bottom: 0.25rem;">Take Profit</div>
                            <div style="font-size: 1.25rem; font-weight: 700; color: var(--success);">${setup.take_profit}</div>
                        </div>
                    </div>

                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; padding: 0.75rem; background: rgba(0,0,0,0.2); border-radius: var(--radius);">
                        <div>
                            <span style="color: var(--gray-500); font-size: 0.875rem;">Risk:Reward Ratio</span>
                            <span style="color: var(--primary); font-weight: 700; margin-left: 0.5rem;">${setup.risk_reward || 'N/A'}</span>
                        </div>
                        <div>
                            <span style="color: var(--gray-500); font-size: 0.875rem;">Direction</span>
                            <span style="color: ${setup.direction === 'BUY' || setup.direction === 'BULLISH' ? 'var(--success)' : 'var(--danger)'}; font-weight: 700; margin-left: 0.5rem;">${setup.direction}</span>
                        </div>
                    </div>

                    <button onclick="ChartAnalysisPage.saveSignal()" class="btn btn-success btn-block" style="background: linear-gradient(90deg, var(--success) 0%, #059669 100%);">
                        <i class="fas fa-save"></i> Save as Signal
                    </button>
                </div>
            `;

            // Auto-fill validator
            document.getElementById('validatorEntry').value = setup.entry;
            document.getElementById('validatorSL').value = setup.stop_loss;
            document.getElementById('validatorTP').value = setup.take_profit;
            document.getElementById('validatorDirection').value = setup.direction === 'BULLISH' ? 'BUY' : (setup.direction === 'BEARISH' ? 'SELL' : 'BUY');
        }

        container.innerHTML = `
            <div class="card" style="max-height: 80vh; overflow-y: auto;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--gray-700);">
                    <h3 style="margin: 0;">${analysis.symbol || 'Unknown Symbol'}</h3>
                    <div style="display: flex; gap: 0.5rem;">
                        <span class="badge badge-${analysis.confidence > 0.7 ? 'success' : 'warning'}">
                            ${Math.round(analysis.confidence * 100)}% Confidence
                        </span>
                        ${analysis.mode === 'ai' ? '<span class="badge badge-info">AI Powered</span>' : ''}
                    </div>
                </div>

                <div style="background: ${biasBg}; border: 1px solid ${biasColor}; border-radius: var(--radius); padding: 1rem; margin-bottom: 1.5rem; text-align: center;">
                    <div style="font-size: 0.875rem; color: var(--gray-500); margin-bottom: 0.5rem;">Trading Bias</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: ${biasColor}; text-transform: uppercase; letter-spacing: 0.05em;">
                        ${analysis.trading_bias}
                    </div>
                </div>

                ${analysis.chart_image ? `
                    <div style="margin-bottom: 1.5rem;">
                        <div style="font-size: 0.875rem; color: var(--gray-500); margin-bottom: 0.5rem;">Analyzed Chart</div>
                        <img src="${analysis.chart_image}" style="width: 100%; border-radius: var(--radius); border: 1px solid var(--gray-700);" />
                    </div>
                ` : ''}

                ${tradeSetupHTML}

                <div style="margin-bottom: 1.5rem;">
                    <strong style="display: block; margin-bottom: 0.75rem; color: var(--gray-300);">Patterns Detected:</strong>
                    ${analysis.patterns_detected?.length ? analysis.patterns_detected.map(p => 
                        `<span class="badge badge-info" style="margin: 0.25rem; padding: 0.5rem 1rem;">${p.name} <small style="opacity: 0.7;">(${p.reliability})</small></span>`
                    ).join('') : '<span class="text-muted">No clear patterns</span>'}
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem;">
                    <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: var(--radius); padding: 1rem;">
                        <div style="font-size: 0.75rem; color: var(--gray-500); text-transform: uppercase; margin-bottom: 0.5rem;">Resistance Levels</div>
                        ${analysis.resistance_levels?.length ? analysis.resistance_levels.map(l => 
                            `<div style="font-family: monospace; color: var(--danger); font-weight: 600; margin-bottom: 0.25rem;">${l}</div>`
                        ).join('') : '<span class="text-muted">None detected</span>'}
                    </div>
                    <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: var(--radius); padding: 1rem;">
                        <div style="font-size: 0.75rem; color: var(--gray-500); text-transform: uppercase; margin-bottom: 0.5rem;">Support Levels</div>
                        ${analysis.support_levels?.length ? analysis.support_levels.map(l => 
                            `<div style="font-family: monospace; color: var(--success); font-weight: 600; margin-bottom: 0.25rem;">${l}</div>`
                        ).join('') : '<span class="text-muted">None detected</span>'}
                    </div>
                </div>

                <div>
                    <strong style="display: block; margin-bottom: 0.75rem; color: var(--gray-300);">AI Insights:</strong>
                    <ul style="padding-left: 1.5rem; margin: 0;">
                        ${analysis.key_insights?.map(i => `<li style="margin-bottom: 0.5rem; color: var(--gray-400);">${i}</li>`).join('') || '<li class="text-muted">No specific insights</li>'}
                    </ul>
                </div>
            </div>
        `;
    },

    async validateTrade() {
        const entry = parseFloat(document.getElementById('validatorEntry').value);
        const sl = parseFloat(document.getElementById('validatorSL').value);
        const tp = parseFloat(document.getElementById('validatorTP').value);
        const direction = document.getElementById('validatorDirection').value;
        const symbol = this.currentAnalysis?.symbol || 'Unknown';

        if (!entry || !sl || !tp) {
            UI.showToast('Please fill in all price levels', 'warning');
            return;
        }

        const resultsDiv = document.getElementById('validatorResults');
        resultsDiv.style.display = 'block';
        resultsDiv.innerHTML = '<div class="loading"><div class="spinner" style="width: 24px; height: 24px;"></div><small>Validating...</small></div>';

        try {
            const result = await API.validateTrade({
                entry_price: entry,
                stop_loss: sl,
                take_profit: tp,
                direction: direction,
                symbol: symbol
            });

            const scoreColor = result.quality_score >= 80 ? 'var(--success)' : 
                              result.quality_score >= 60 ? 'var(--warning)' : 'var(--danger)';

            resultsDiv.innerHTML = `
                <div style="background: var(--gray-900); border-radius: var(--radius); padding: 1rem; border: 1px solid var(--gray-700);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <span style="color: var(--gray-500);">Quality Score</span>
                        <span style="font-size: 1.5rem; font-weight: 700; color: ${scoreColor};">${result.quality_score}/100</span>
                    </div>
                    <div style="width: 100%; height: 6px; background: var(--gray-700); border-radius: 3px; margin-bottom: 1rem; overflow: hidden;">
                        <div style="width: ${result.quality_score}%; height: 100%; background: ${scoreColor}; border-radius: 3px; transition: width 0.5s ease;"></div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; font-size: 0.875rem;">
                        <div>
                            <span style="color: var(--gray-500);">R:R Ratio:</span>
                            <span style="color: var(--gray-200); font-weight: 600; margin-left: 0.5rem;">${result.risk_reward_text}</span>
                        </div>
                        <div>
                            <span style="color: var(--gray-500);">Probability:</span>
                            <span style="color: var(--gray-200); font-weight: 600; margin-left: 0.5rem;">${Math.round(result.probability_estimate * 100)}%</span>
                        </div>
                        <div>
                            <span style="color: var(--gray-500);">Structure:</span>
                            <span style="color: ${result.structure_valid ? 'var(--success)' : 'var(--danger)'}; font-weight: 600; margin-left: 0.5rem;">
                                ${result.structure_quality}
                            </span>
                        </div>
                    </div>
                    ${result.warnings?.length ? `
                        <div style="margin-top: 1rem; padding: 0.75rem; background: rgba(239, 68, 68, 0.1); border-radius: var(--radius); border-left: 3px solid var(--danger);">
                            <div style="font-size: 0.75rem; color: var(--danger); margin-bottom: 0.25rem;">Warnings:</div>
                            ${result.warnings.map(w => `<div style="font-size: 0.875rem; color: var(--gray-300);">• ${w}</div>`).join('')}
                        </div>
                    ` : ''}
                    ${result.recommendations?.length ? `
                        <div style="margin-top: 0.75rem; padding: 0.75rem; background: rgba(16, 185, 129, 0.1); border-radius: var(--radius); border-left: 3px solid var(--success);">
                            <div style="font-size: 0.75rem; color: var(--success); margin-bottom: 0.25rem;">Recommendations:</div>
                            ${result.recommendations.map(r => `<div style="font-size: 0.875rem; color: var(--gray-300);">• ${r}</div>`).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
        } catch (error) {
            resultsDiv.innerHTML = `<div class="alert alert-error">${error.message}</div>`;
        }
    },

    async saveSignal() {
        if (!this.currentAnalysis || !this.currentAnalysis.trade_setup) {
            UI.showToast('No trade setup to save', 'warning');
            return;
        }

        const setup = this.currentAnalysis.trade_setup;

        try {
            const result = await API.saveSignal({
                symbol: this.currentAnalysis.symbol || 'Unknown',
                direction: setup.direction,
                entry_price: parseFloat(setup.entry),
                stop_loss: parseFloat(setup.stop_loss),
                take_profit: parseFloat(setup.take_profit),
                confidence: setup.probability || 0.7,
                analysis: this.currentAnalysis.key_insights?.join('\n') || ''
            });

            if (result.success) {
                UI.showToast('Signal saved successfully!', 'success');
            } else {
                throw new Error('Failed to save signal');
            }
        } catch (error) {
            UI.showToast('Error saving signal: ' + error.message, 'error');
        }
    },

    async loadPatterns() {
        try {
            const patterns = await API.getPatternLibrary();
            const container = document.getElementById('patternGrid');

            const allPatterns = [
                ...(patterns.reversal || []),
                ...(patterns.continuation || []),
                ...(patterns.candlestick || [])
            ];

            container.innerHTML = allPatterns.slice(0, 6).map(p => `
                <div class="card" style="transition: transform 0.2s;" onmouseover="this.style.transform='translateY(-4px)'" onmouseout="this.style.transform='translateY(0)'">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <h4 style="margin: 0; font-size: 1rem; color: var(--gray-200);">${p.name}</h4>
                        <span class="badge badge-${p.type === 'reversal' ? 'danger' : p.type === 'continuation' ? 'success' : 'info'}" style="font-size: 0.75rem;">
                            ${p.type}
                        </span>
                    </div>
                    <p style="font-size: 0.875rem; color: var(--gray-500); margin-bottom: 0.75rem;">${p.description}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <small style="color: var(--success); font-weight: 600;">${p.success_rate} success rate</small>
                        <span class="badge badge-${p.reliability === 'high' ? 'success' : p.reliability === 'medium' ? 'warning' : 'secondary'}" style="font-size: 0.7rem;">
                            ${p.reliability}
                        </span>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            document.getElementById('patternGrid').innerHTML = '<span class="text-muted">Failed to load patterns</span>';
        }
    }
};

// API Helper functions that need to be added to the global API object
if (typeof API !== 'undefined') {
    API.analyzeChartImage = async function(file, symbol, timeframe) {
        const formData = new FormData();
        formData.append('file', file);
        if (symbol) formData.append('symbol', symbol);
        if (timeframe) formData.append('timeframe', timeframe);

        const response = await fetch(`${API_BASE}/ai/chart/analyze`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('pipways_token')}`
            },
            body: formData
        });

        if (!response.ok) {
            const error = await response.text();
            throw new Error(error || 'Analysis failed');
        }

        return response.json();
    };

    API.validateTrade = async function(params) {
        return this.request('/ai/trade/validate', {
            method: 'POST',
            body: JSON.stringify(params)
        });
    };

    API.saveSignal = async function(params) {
        return this.request('/ai/signal/save', {
            method: 'POST',
            body: JSON.stringify(params)
        });
    };

    API.getPatternLibrary = async function() {
        return this.request('/ai/chart/pattern-library');
    };
}
