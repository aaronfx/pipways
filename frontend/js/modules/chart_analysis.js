const ChartAnalysisPage = {
    async render() {
        const app = document.getElementById('app');
        
        app.innerHTML = `
            <div class="page-header">
                <h1>📊 AI Chart Analysis</h1>
                <p>Upload your charts for instant pattern recognition</p>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                <div>
                    <div class="upload-area" id="dropZone" onclick="document.getElementById('chartInput').click()">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">📈</div>
                        <h3>Drop chart image here</h3>
                        <p style="color: var(--gray-500); margin-top: 0.5rem;">or click to browse</p>
                        <input type="file" id="chartInput" accept="image/*" style="display: none;" onchange="ChartAnalysisPage.handleFile(this.files[0])">
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
    
    async handleFile(file) {
        if (!file) return;
        
        if (file.size > 5 * 1024 * 1024) {
            UI.showToast('File too large (max 5MB)', 'error');
            return;
        }
        
        const results = document.getElementById('chartResults');
        results.innerHTML = '<div class="loading" style="text-align: center; padding: 3rem;"><div class="spinner" style="margin: 0 auto 1rem;"></div><p>Analyzing chart with AI Vision...</p></div>';
        
        const symbol = document.getElementById('chartSymbol')?.value;
        const timeframe = document.getElementById('chartTimeframe')?.value;
        
        try {
            const analysis = await API.analyzeChartImage(file, symbol, timeframe);
            this.displayResults(analysis);
        } catch (error) {
            results.innerHTML = `<div class="alert alert-error">Analysis failed: ${error.message}</div>`;
        }
    },
    
    displayResults(analysis) {
        const container = document.getElementById('chartResults');
        
        const biasColor = analysis.trading_bias === 'bullish' ? 'var(--success)' : 
                         analysis.trading_bias === 'bearish' ? 'var(--danger)' : 'var(--gray-500)';
        
        container.innerHTML = `
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--gray-200);">
                    <h3 style="margin: 0;">Analysis Results</h3>
                    <span class="badge badge-${analysis.confidence > 0.7 ? 'success' : 'warning'}">
                        ${Math.round(analysis.confidence * 100)}% Confidence
                    </span>
                </div>
                
                <div style="margin-bottom: 1.5rem;">
                    <span style="color: var(--gray-600);">Trading Bias:</span>
                    <span style="font-size: 1.25rem; margin-left: 0.5rem; color: ${biasColor}; font-weight: 600; text-transform: uppercase;">
                        ${analysis.trading_bias}
                    </span>
                </div>
                
                <div style="margin-bottom: 1.5rem;">
                    <strong style="display: block; margin-bottom: 0.5rem;">Patterns Detected:</strong>
                    ${analysis.patterns_detected?.length ? analysis.patterns_detected.map(p => 
                        `<span class="badge badge-info" style="margin: 0.25rem;">${p.name} (${p.reliability})</span>`
                    ).join('') : '<span class="text-muted">No clear patterns</span>'}
                </div>
                
                <div style="margin-bottom: 1.5rem;">
                    <strong style="display: block; margin-bottom: 0.5rem;">Key Levels:</strong>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.875rem;">
                        <div class="bg-danger text-danger" style="padding: 0.5rem; border-radius: var(--radius);">
                            Resistance: <strong>${analysis.resistance_levels?.[0] || 'N/A'}</strong>
                        </div>
                        <div class="bg-success text-success" style="padding: 0.5rem; border-radius: var(--radius);">
                            Support: <strong>${analysis.support_levels?.[0] || 'N/A'}</strong>
                        </div>
                    </div>
                </div>
                
                <div>
                    <strong style="display: block; margin-bottom: 0.5rem;">AI Insights:</strong>
                    <ul style="padding-left: 1.5rem; color: var(--gray-600);">
                        ${analysis.key_insights?.map(i => `<li>${i}</li>`).join('') || '<li>No specific insights</li>'}
                    </ul>
                </div>
            </div>
        `;
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
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <h4 style="margin: 0; font-size: 1rem;">${p.name}</h4>
                        <span class="badge badge-${p.type === 'reversal' ? 'danger' : p.type === 'continuation' ? 'success' : 'info'}" style="font-size: 0.75rem;">
                            ${p.type}
                        </span>
                    </div>
                    <p style="font-size: 0.875rem; color: var(--gray-600);">${p.description}</p>
                    <small style="color: var(--success); font-weight: 600;">Success rate: ${p.success_rate}</small>
                </div>
            `).join('');
        } catch (e) {
            document.getElementById('patternGrid').innerHTML = 'Failed to load patterns';
        }
    }
};
