const ChartAnalysisPage = {
    async render(container) {
        container.innerHTML = `
            <div class="page-header">
                <h1>📊 AI Chart Analysis</h1>
                <p>Upload your charts for instant pattern recognition</p>
            </div>
            
            <div class="chart-analysis-container" style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                <div class="upload-section">
                    <div class="upload-area" id="dropZone" 
                         style="border: 2px dashed #cbd5e1; border-radius: 0.5rem; padding: 3rem; 
                                text-align: center; background: #f8fafc; cursor: pointer;"
                         onclick="document.getElementById('chartInput').click()"
                         ondrop="ChartAnalysisPage.handleDrop(event)" 
                         ondragover="event.preventDefault()">
                        
                        <div style="font-size: 3rem; margin-bottom: 1rem;">📈</div>
                        <h3>Drop chart image here</h3>
                        <p style="color: #64748b;">or click to browse</p>
                        <input type="file" id="chartInput" accept="image/*" style="display: none;" 
                               onchange="ChartAnalysisPage.handleFile(this.files[0])">
                    </div>
                    
                    <div class="form-row" style="margin-top: 1rem;">
                        <div class="form-group">
                            <label>Symbol (optional)</label>
                            <input type="text" id="chartSymbol" placeholder="EURUSD">
                        </div>
                        <div class="form-group">
                            <label>Timeframe (optional)</label>
                            <select id="chartTimeframe">
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
                
                <div class="results-section" id="chartResults">
                    <div class="placeholder" style="text-align: center; color: #94a3b8; padding: 3rem;">
                        <p>Upload a chart to see AI analysis</p>
                        <small>Supports: PNG, JPG, JPEG</small>
                    </div>
                </div>
            </div>
            
            <div class="pattern-library" style="margin-top: 3rem;">
                <h3>Pattern Library</h3>
                <div id="patternGrid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
                    Loading...
                </div>
            </div>
        `;
        
        this.loadPatternLibrary();
    },

    handleDrop(e) {
        e.preventDefault();
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            this.handleFile(file);
        }
    },

    async handleFile(file) {
        if (!file) return;
        
        const results = document.getElementById('chartResults');
        results.innerHTML = '<div class="spinner" style="text-align: center; padding: 3rem;"><div class="loading"></div><p>Analyzing chart...</p></div>';
        
        const symbol = document.getElementById('chartSymbol')?.value;
        const timeframe = document.getElementById('chartTimeframe')?.value;
        
        try {
            const analysis = await API.analyzeChartImage(file, symbol, timeframe);
            this.displayResults(analysis);
        } catch (error) {
            results.innerHTML = `<div class="error" style="color: #dc2626; text-align: center; padding: 2rem;">
                Analysis failed: ${error.message}
            </div>`;
        }
    },

    displayResults(analysis) {
        const container = document.getElementById('chartResults');
        
        container.innerHTML = `
            <div class="analysis-result" style="background: white; padding: 1.5rem; border-radius: 0.5rem;">
                <div class="result-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3>Analysis Results</h3>
                    <span class="badge" style="background: ${analysis.confidence > 0.7 ? '#dcfce7' : '#fef3c7'}; 
                                              color: ${analysis.confidence > 0.7 ? '#166534' : '#92400e'};
                                              padding: 0.25rem 0.75rem; border-radius: 1rem;">
                        ${Math.round(analysis.confidence * 100)}% Confidence
                    </span>
                </div>
                
                <div class="bias-indicator" style="margin-bottom: 1rem;">
                    <strong>Trading Bias:</strong>
                    <span style="font-size: 1.25rem; margin-left: 0.5rem; 
                                 color: ${analysis.trading_bias === 'bullish' ? '#16a34a' : analysis.trading_bias === 'bearish' ? '#dc2626' : '#64748b'};">
                        ${analysis.trading_bias === 'bullish' ? '🟢 Bullish' : analysis.trading_bias === 'bearish' ? '🔴 Bearish' : '⚪ Neutral'}
                    </span>
                </div>
                
                <div class="patterns-detected" style="margin-bottom: 1rem;">
                    <strong>Patterns Detected:</strong>
                    ${analysis.patterns_detected.length === 0 ? '<p>No clear patterns</p>' : 
                      analysis.patterns_detected.map(p => `
                        <div class="pattern-tag" style="background: #e0e7ff; display: inline-block; 
                                                      padding: 0.25rem 0.75rem; margin: 0.25rem; border-radius: 1rem; font-size: 0.875rem;">
                            ${p.name} (${p.reliability})
                        </div>
                      `).join('')}
                </div>
                
                <div class="key-levels" style="margin-bottom: 1rem;">
                    <strong>Key Levels:</strong>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 0.5rem;">
                        <div>Resistance 2: <code>${analysis.resistance_levels[1] || 'N/A'}</code></div>
                        <div>Resistance 1: <code>${analysis.resistance_levels[0] || 'N/A'}</code></div>
                        <div>Support 1: <code>${analysis.support_levels[0] || 'N/A'}</code></div>
                        <div>Support 2: <code>${analysis.support_levels[1] || 'N/A'}</code></div>
                    </div>
                </div>
                
                <div class="insights">
                    <strong>Insights:</strong>
                    <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                        ${analysis.key_insights.map(i => `<li>${i}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    },

    async loadPatternLibrary() {
        try {
            const patterns = await API.getPatternLibrary();
            const container = document.getElementById('patternGrid');
            
            // Flatten patterns object
            const allPatterns = [
                ...(patterns.reversal || []),
                ...(patterns.continuation || []),
                ...(patterns.candlestick || [])
            ];
            
            container.innerHTML = allPatterns.slice(0, 6).map(p => `
                <div class="pattern-card" style="background: white; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0;">
                    <h4>${p.name}</h4>
                    <span class="badge" style="background: ${p.type === 'reversal' ? '#fee2e2' : p.type === 'continuation' ? '#dcfce7' : '#e0e7ff'}; 
                                              font-size: 0.75rem; padding: 0.125rem 0.5rem; border-radius: 0.25rem;">
                        ${p.type}
                    </span>
                    <p style="font-size: 0.875rem; color: #64748b; margin: 0.5rem 0;">${p.description}</p>
                    <small style="color: #059669;">Success rate: ${p.success_rate}</small>
                </div>
            `).join('');
        } catch (e) {
            document.getElementById('patternGrid').innerHTML = 'Failed to load patterns';
        }
    }
};
