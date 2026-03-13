const ChartAnalysisPage = {
    async render(container) {
        container.innerHTML = `
            <div class="page-header" style="margin-bottom: 2rem;">
                <h1>📊 AI Chart Analysis</h1>
                <p style="color: #64748b;">Upload your charts for instant pattern recognition</p>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                <div>
                    <div id="dropZone" 
                         style="border: 2px dashed #cbd5e1; border-radius: 0.5rem; padding: 3rem; text-align: center; background: #f8fafc; cursor: pointer; transition: all 0.2s;"
                         onclick="document.getElementById('chartInput').click()"
                         ondrop="ChartAnalysisPage.handleDrop(event)" 
                         ondragover="event.preventDefault(); this.style.borderColor='#3b82f6'; this.style.background='#eff6ff';"
                         ondragleave="this.style.borderColor='#cbd5e1'; this.style.background='#f8fafc';">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">📈</div>
                        <h3>Drop chart image here</h3>
                        <p style="color: #64748b; margin-top: 0.5rem;">or click to browse</p>
                        <input type="file" id="chartInput" accept="image/*" style="display: none;" onchange="ChartAnalysisPage.handleFile(this.files[0])">
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
                        <div>
                            <label style="display: block; margin-bottom: 0.25rem; font-size: 0.875rem; color: #374151;">Symbol (optional)</label>
                            <input type="text" id="chartSymbol" placeholder="EURUSD" style="width: 100%; padding: 0.75rem; border: 1px solid #e5e7eb; border-radius: 0.375rem;">
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 0.25rem; font-size: 0.875rem; color: #374151;">Timeframe (optional)</label>
                            <select id="chartTimeframe" style="width: 100%; padding: 0.75rem; border: 1px solid #e5e7eb; border-radius: 0.375rem;">
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
                    <div style="text-align: center; color: #94a3b8; padding: 3rem; background: #f8fafc; border-radius: 0.5rem;">
                        <p>Upload a chart to see AI analysis</p>
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
        
        this.loadPatternLibrary();
    },

    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.style.borderColor = '#cbd5e1';
        e.currentTarget.style.background = '#f8fafc';
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            this.handleFile(file);
        }
    },

    async handleFile(file) {
        if (!file) return;
        
        if (file.size > 5 * 1024 * 1024) {
            alert('File too large (max 5MB)');
            return;
        }
        
        const results = document.getElementById('chartResults');
        results.innerHTML = '<div style="text-align: center; padding: 3rem;"><div style="width: 40px; height: 40px; border: 4px solid #f3f4f6; border-top-color: #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 1rem;"></div><p>Analyzing chart with AI Vision...</p></div>';
        
        const symbol = document.getElementById('chartSymbol')?.value;
        const timeframe = document.getElementById('chartTimeframe')?.value;
        
        try {
            const analysis = await API.analyzeChartImage(file, symbol, timeframe);
            this.displayResults(analysis);
        } catch (error) {
            results.innerHTML = `<div style="color: #dc2626; text-align: center; padding: 2rem; background: #fee2e2; border-radius: 0.5rem;">Analysis failed: ${error.message}</div>`;
        }
    },

    displayResults(analysis) {
        const container = document.getElementById('chartResults');
        
        const biasColor = analysis.trading_bias === 'bullish' ? '#16a34a' : analysis.trading_bias === 'bearish' ? '#dc2626' : '#64748b';
        const biasBg = analysis.trading_bias === 'bullish' ? '#dcfce7' : analysis.trading_bias === 'bearish' ? '#fee2e2' : '#f3f4f6';
        
        container.innerHTML = `
            <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid #e5e7eb;">
                    <h3 style="margin: 0;">Analysis Results</h3>
                    <span style="background: ${analysis.confidence > 0.7 ? '#dcfce7' : '#fef3c7'}; color: ${analysis.confidence > 0.7 ? '#166534' : '#92400e'}; padding: 0.5rem 1rem; border-radius: 1rem; font-size: 0.875rem; font-weight: 600;">
                        ${Math.round(analysis.confidence * 100)}% Confidence
                    </span>
                </div>
                
                <div style="margin-bottom: 1.5rem;">
                    <strong style="color: #374151;">Trading Bias:</strong>
                    <span style="font-size: 1.25rem; margin-left: 0.5rem; color: ${biasColor}; font-weight: 600; text-transform: uppercase;">
                        ${analysis.trading_bias}
                    </span>
                </div>
                
                <div style="margin-bottom: 1.5rem;">
                    <strong style="color: #374151; display: block; margin-bottom: 0.5rem;">Patterns Detected:</strong>
                    ${analysis.patterns_detected.length === 0 ? '<p style="color: #64748b;">No clear patterns detected</p>' : 
                      analysis.patterns_detected.map(p => `
                        <span style="display: inline-block; background: #e0e7ff; color: #3730a3; padding: 0.5rem 1rem; margin: 0.25rem; border-radius: 1rem; font-size: 0.875rem;">
                            ${p.name} (${p.reliability})
                        </span>
                      `).join('')}
                </div>
                
                <div style="margin-bottom: 1.5rem;">
                    <strong style="color: #374151; display: block; margin-bottom: 0.5rem;">Key Levels:</strong>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.875rem;">
                        <div style="background: #fee2e2; padding: 0.5rem; border-radius: 0.25rem; color: #991b1b;">
                            Resistance 2: <strong>${analysis.resistance_levels[1] || 'N/A'}</strong>
                        </div>
                        <div style="background: #fecaca; padding: 0.5rem; border-radius: 0.25rem; color: #7f1d1d;">
                            Resistance 1: <strong>${analysis.resistance_levels[0] || 'N/A'}</strong>
                        </div>
                        <div style="background: #bbf7d0; padding: 0.5rem; border-radius: 0.25rem; color: #166534;">
                            Support 1: <strong>${analysis.support_levels[0] || 'N/A'}</strong>
                        </div>
                        <div style="background: #86efac; padding: 0.5rem; border-radius: 0.25rem; color: #14532d;">
                            Support 2: <strong>${analysis.support_levels[1] || 'N/A'}</strong>
                        </div>
                    </div>
                </div>
                
                <div>
                    <strong style="color: #374151; display: block; margin-bottom: 0.5rem;">AI Insights:</strong>
                    <ul style="padding-left: 1.5rem; color: #4b5563; font-size: 0.875rem;">
                        ${analysis.key_insights.map(i => `<li style="margin-bottom: 0.25rem;">${i}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    },

    async loadPatternLibrary() {
        try {
            const patterns = await API.getPatternLibrary();
            const container = document.getElementById('patternGrid');
            
            const allPatterns = [
                ...(patterns.reversal || []),
                ...(patterns.continuation || []),
                ...(patterns.candlestick || [])
            ];
            
            container.innerHTML = allPatterns.slice(0, 6).map(p => `
                <div style="background: white; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <h4 style="margin: 0; font-size: 1rem;">${p.name}</h4>
                        <span style="background: ${p.type === 'reversal' ? '#fee2e2' : p.type === 'continuation' ? '#dcfce7' : '#e0e7ff'}; 
                                     color: ${p.type === 'reversal' ? '#991b1b' : p.type === 'continuation' ? '#166534' : '#3730a3'};
                                     font-size: 0.75rem; padding: 0.25rem 0.5rem; border-radius: 0.25rem; text-transform: uppercase;">
                            ${p.type}
                        </span>
                    </div>
                    <p style="font-size: 0.875rem; color: #64748b; margin: 0.5rem 0;">${p.description}</p>
                    <small style="color: #059669; font-weight: 600;">Success rate: ${p.success_rate}</small>
                </div>
            `).join('');
        } catch (e) {
            document.getElementById('patternGrid').innerHTML = 'Failed to load patterns';
        }
    }
};
