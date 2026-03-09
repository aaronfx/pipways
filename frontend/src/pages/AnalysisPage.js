import { Component } from '../components/Component.js';
import { Sidebar } from '../components/Sidebar.js';
import { api } from '../api/client.js';
import { showLoading } from '../utils/helpers.js';

export class AnalysisPage extends Component {
    constructor() {
        super();
        this.selectedFile = null;
    }

    render() {
        const container = document.createElement('div');
        container.className = 'main-app';
        
        const sidebar = new Sidebar();
        container.appendChild(sidebar.render());
        
        const main = document.createElement('main');
        main.className = 'main-content';
        main.innerHTML = `
            <div class="page-header">
                <h2><i class="fas fa-robot" style="color: var(--primary);"></i> AI Chart Analysis</h2>
                <p>Upload chart screenshots for instant technical analysis</p>
            </div>
            
            <div class="analysis-container">
                <div class="analysis-form card">
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Currency Pair</label>
                            <input type="text" id="chart-pair" class="form-input" placeholder="EURUSD" value="EURUSD">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Timeframe</label>
                            <select id="chart-timeframe" class="form-input">
                                <option value="5M">5 Minutes</option>
                                <option value="15M">15 Minutes</option>
                                <option value="1H" selected>1 Hour</option>
                                <option value="4H">4 Hours</option>
                                <option value="D1">Daily</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Additional Context (Optional)</label>
                        <input type="text" id="chart-context" class="form-input" placeholder="e.g., 'Looking for breakout entry' or 'Support at 1.0850'">
                    </div>
                    
                    <div class="upload-area" id="chart-upload-area">
                        <i class="fas fa-cloud-upload-alt"></i>
                        <h3>Drop Chart Image Here</h3>
                        <p class="text-secondary">or click to browse (PNG, JPG, max 10MB)</p>
                        <input type="file" id="chart-file" class="hidden" accept="image/*">
                    </div>
                    
                    <div id="chart-preview" class="hidden">
                        <img id="chart-img-preview" class="preview-image">
                        <button type="button" class="btn btn-sm btn-danger" id="remove-chart">Remove</button>
                    </div>
                    
                    <button class="btn btn-primary btn-block" id="analyze-chart-btn" disabled>
                        <i class="fas fa-brain"></i> Analyze Chart
                    </button>
                </div>
                
                <div id="chart-result" class="analysis-result hidden">
                    <div class="result-card card">
                        <div class="result-header">
                            <i class="fas fa-robot"></i>
                            <h3>AI Analysis Report</h3>
                        </div>
                        <div id="chart-analysis-content" class="result-content"></div>
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(main);
        return container;
    }

    bindEvents() {
        const uploadArea = this.element.querySelector('#chart-upload-area');
        const fileInput = this.element.querySelector('#chart-file');
        const preview = this.element.querySelector('#chart-preview');
        const imgPreview = this.element.querySelector('#chart-img-preview');
        const analyzeBtn = this.element.querySelector('#analyze-chart-btn');
        const removeBtn = this.element.querySelector('#remove-chart');
        
        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length) this.handleFile(files[0], preview, imgPreview, analyzeBtn);
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                this.handleFile(e.target.files[0], preview, imgPreview, analyzeBtn);
            }
        });
        
        removeBtn.addEventListener('click', () => {
            this.selectedFile = null;
            fileInput.value = '';
            preview.classList.add('hidden');
            uploadArea.classList.remove('hidden');
            analyzeBtn.disabled = true;
        });
        
        analyzeBtn.addEventListener('click', () => this.analyzeChart());
    }

    handleFile(file, previewContainer, imgElement, analyzeBtn) {
        if (file.size > 10 * 1024 * 1024) {
            api.showToast('File too large. Max 10MB.', 'error');
            return;
        }
        
        this.selectedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            imgElement.src = e.target.result;
            previewContainer.classList.remove('hidden');
            document.getElementById('chart-upload-area').classList.add('hidden');
            analyzeBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    async analyzeChart() {
        if (!this.selectedFile) return;
        
        const formData = new FormData();
        formData.append('file', this.selectedFile);
        formData.append('pair', document.getElementById('chart-pair').value || 'EURUSD');
        formData.append('timeframe', document.getElementById('chart-timeframe').value);
        formData.append('additional_info', document.getElementById('chart-context').value || '');
        
        showLoading(true, 'AI analyzing chart... This takes 10-20 seconds');
        
        try {
            const result = await api.analyzeChart(formData);
            this.displayResult(result);
        } catch (error) {
            console.error(error);
        } finally {
            showLoading(false);
        }
    }

    displayResult(result) {
        const resultDiv = this.element.querySelector('#chart-result');
        const contentDiv = this.element.querySelector('#chart-analysis-content');
        
        let html = '';
        if (result.formatted) {
            // Fixed: Use string replacement instead of regex
            html = result.formatted.split('\n').join('<br>');
        } else if (result.analysis) {
            html = `<pre>${JSON.stringify(result.analysis, null, 2)}</pre>`;
        } else {
            html = '<p>No analysis available</p>';
        }
        
        contentDiv.innerHTML = html;
        resultDiv.classList.remove('hidden');
        resultDiv.scrollIntoView({ behavior: 'smooth' });
    }
}
