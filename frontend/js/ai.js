/**
 * Pipways AI Engine
 * Production-Ready Namespaced Module
 * Supports: CSV, Excel, PDF, and Images
 */

(function() {
    'use strict';
    
    if (window.ai && window.ai.__initialized) return;
    
    const API_BASE = "/api/ai";
    
    let currentChartFile = null;
    let currentPerformanceFile = null;
    
    async function apiRequest(endpoint, method = "POST", body = null) {
        const options = { method: method, headers: {} };
        if (body instanceof FormData) {
            options.body = body;
        } else if (body) {
            options.headers["Content-Type"] = "application/json";
            options.body = JSON.stringify(body);
        }

        const response = await fetch(`${API_BASE}${endpoint}`, options);
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || `HTTP ${response.status}`);
        }
        return response.json();
    }

    function appendChat(role, text) {
        const chatBox = document.getElementById("chat-messages");
        if (!chatBox) return;
        const msg = document.createElement("div");
        msg.className = "chat-message";
        const bubble = document.createElement("div");
        bubble.className = role === "user" ? "chat-bubble user" : "chat-bubble ai";
        bubble.innerHTML = role === "ai" ? `<strong>AI Mentor:</strong> ${text}` : text;
        msg.appendChild(bubble);
        chatBox.appendChild(msg);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function formatList(text) {
        if (!text) return "<li>No data available.</li>";
        const lines = text.split("\n").map(l => l.trim()).filter(l => l.length > 0);
        let html = "";
        lines.forEach(line => {
            const cleanLine = line.replace(/^[-•*]\s*/, '').replace(/^\d+\.\s*/, '');
            if (cleanLine && !cleanLine.match(/^Key Issues|^Strengths|^Improvement|^Recommended|^Mentor|^Performance|^Risk|^Discipline|^Overall/i)) {
                html += `<li>${cleanLine}</li>`;
            }
        });
        return html || "<li>No specific items listed.</li>";
    }

    function getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        if (['csv', 'xls', 'xlsx'].includes(ext)) return 'fa-file-csv';
        if (['pdf'].includes(ext)) return 'fa-file-pdf';
        if (['jpg', 'jpeg', 'png', 'webp', 'gif'].includes(ext)) return 'fa-file-image';
        return 'fa-file';
    }

    function getFileColor(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        if (['csv', 'xls', 'xlsx'].includes(ext)) return 'var(--success)';
        if (['pdf'].includes(ext)) return 'var(--danger)';
        if (['jpg', 'jpeg', 'png', 'webp'].includes(ext)) return 'var(--primary)';
        return 'var(--text-secondary)';
    }

    window.ai = {
        __initialized: true,
        
        sendChatMessage: async function() {
            const input = document.getElementById("chat-input");
            if (!input) return;
            const message = input.value.trim();
            if (!message) return;

            appendChat("user", message);
            input.value = "";

            try {
                const res = await apiRequest("/mentor", "POST", { message: message });
                appendChat("ai", res.response);
            } catch (error) {
                console.error("Mentor error:", error);
                appendChat("ai", "I'm having trouble connecting right now. Please try again.");
            }
        },

        handleChartUpload: function(input) {
            if (!input?.files?.[0]) return;
            currentChartFile = input.files[0];
            const preview = document.getElementById("chart-preview");
            const container = document.getElementById("chart-preview-container");
            if (preview && container) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                    container.classList.remove("hidden");
                };
                reader.readAsDataURL(currentChartFile);
            }
        },

        analyzeChart: async function() {
            if (!currentChartFile) {
                alert("Please upload a chart image first.");
                return;
            }

            const pair = document.getElementById("chart-pair")?.value || "EURUSD";
            const timeframe = document.getElementById("chart-timeframe")?.value || "1H";
            const context = document.getElementById("chart-context")?.value || "";

            const formData = new FormData();
            formData.append("image", currentChartFile);
            formData.append("pair", pair);
            formData.append("timeframe", timeframe);
            formData.append("context", context);

            const resultBox = document.getElementById("chart-analysis-content");
            const resultContainer = document.getElementById("chart-analysis-result");
            
            if (resultBox) resultBox.innerHTML = "<p><i class='fas fa-spinner fa-spin'></i> Analyzing chart with AI...</p>";
            if (resultContainer) resultContainer.classList.remove("hidden");

            try {
                const res = await apiRequest("/analyze-chart", "POST", formData);
                if (resultBox) resultBox.innerHTML = res.analysis.replace(/\n/g, '<br>');
            } catch (error) {
                console.error("Chart analysis error:", error);
                if (resultBox) resultBox.innerHTML = "<p style='color: var(--danger);'>Chart analysis failed. Please try again.</p>";
            }
        },

        /**
         * Handle Performance File Upload (CSV/Excel/PDF/Image)
         */
        handlePerformanceUpload: function(input) {
            if (!input?.files?.[0]) return;
            
            const file = input.files[0];
            const allowedTypes = [
                // Spreadsheets
                "text/csv",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/csv",
                // PDF
                "application/pdf",
                // Images
                "image/jpeg",
                "image/png",
                "image/webp",
                "image/jpg",
                "image/gif"
            ];
            
            const allowedExts = ['.csv', '.xls', '.xlsx', '.pdf', '.jpg', '.jpeg', '.png', '.webp', '.gif'];
            const hasValidExt = allowedExts.some(ext => file.name.toLowerCase().endsWith(ext));
            const hasValidType = allowedTypes.includes(file.type);
            
            if (!hasValidType && !hasValidExt) {
                alert("Supported formats: CSV, Excel, PDF, or Images (JPG, PNG, WEBP)");
                input.value = '';
                return;
            }
            
            currentPerformanceFile = file;
            
            const container = document.getElementById("performance-preview-container");
            const preview = document.getElementById("performance-preview");
            
            if (container) {
                container.classList.remove("hidden");
                
                // Remove old file info if exists
                const oldInfo = document.getElementById("performance-file-info");
                if (oldInfo) oldInfo.remove();
                
                const fileIcon = getFileIcon(file.name);
                const fileColor = getFileColor(file.name);
                
                // Create file info display
                const fileInfo = document.createElement("div");
                fileInfo.id = "performance-file-info";
                fileInfo.style.cssText = "text-align: center; padding: 30px; background: var(--bg-hover); border-radius: 12px; margin-bottom: 16px; border: 2px dashed var(--border);";
                fileInfo.innerHTML = `
                    <i class="fas ${fileIcon}" style="font-size: 64px; color: ${fileColor}; margin-bottom: 16px;"></i>
                    <div style="font-weight: 600; font-size: 16px; margin-bottom: 8px;">${file.name}</div>
                    <div style="color: var(--text-secondary); font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">
                        ${(file.size/1024).toFixed(1)} KB • ${file.type || 'Document'}
                    </div>
                `;
                
                if (preview && preview.parentNode) {
                    preview.parentNode.insertBefore(fileInfo, preview);
                }
                
                // Handle image preview if it's an image
                if (file.type.startsWith('image/')) {
                    if (preview) {
                        preview.style.display = 'block';
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            preview.src = e.target.result;
                        };
                        reader.readAsDataURL(file);
                    }
                } else {
                    if (preview) preview.style.display = 'none';
                }
            }
        },

        /**
         * Analyze Performance (Multi-Format)
         */
        analyzePerformanceVision: async function() {
            if (!currentPerformanceFile) {
                alert("Please upload a trading statement (CSV, Excel, PDF, or Image).");
                return;
            }

            const formData = new FormData();
            formData.append("file", currentPerformanceFile);

            const container = document.getElementById("analysis-results");
            if (container) {
                container.classList.remove("hidden");
                const scoreEl = document.getElementById("trader-score");
                if (scoreEl) scoreEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            }

            try {
                const result = await apiRequest("/analyze-performance-file", "POST", formData);
                this.renderPerformance(result);
            } catch (error) {
                console.error("Performance analysis error:", error);
                const container = document.getElementById("analysis-results");
                if (container) {
                    container.innerHTML = `<div style='color: var(--danger); text-align: center; padding: 40px; background: var(--bg-card); border-radius: 12px; margin: 20px;'>
                        <i class="fas fa-exclamation-circle" style="font-size: 48px; margin-bottom: 16px; display: block;"></i>
                        <strong>Analysis Failed</strong><br>
                        ${error.message || 'Unable to process file. Ensure it is a valid trading statement.'}
                    </div>`;
                }
            }
        },

        renderPerformance: function(data) {
            if (!data) return;
            
            const metrics = data.metrics || {};
            const isVision = data.source === 'vision_ocr';
            
            // Update Score Display
            const scoreEl = document.getElementById("trader-score");
            const scoreCircle = document.getElementById("score-circle");
            const scoreInterp = document.getElementById("score-interpretation");
            
            if (scoreEl) {
                // Use overall_score for vision, calculated for structured
                let score = metrics.overall_score || Math.round((metrics.win_rate * metrics.profit_factor) / 10) || 0;
                if (score > 100) score = 100;
                if (score < 0) score = 0;
                
                scoreEl.textContent = isNaN(score) ? 0 : score;
                if (scoreCircle) scoreCircle.style.setProperty('--score', score);
                
                if (scoreInterp) {
                    if (score >= 80) scoreInterp.textContent = "Excellent trading performance";
                    else if (score >= 60) scoreInterp.textContent = "Good performance with room for improvement";
                    else if (score >= 40) scoreInterp.textContent = "Average - focus on risk management";
                    else scoreInterp.textContent = "Needs significant improvement";
                }
            }

            // Source badge
            const summaryEl = document.getElementById("performance-summary");
            if (summaryEl) {
                const sourceBadge = isVision ? 
                    `<span style="background: var(--warning); color: var(--bg-dark); padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; margin-bottom: 12px; display: inline-block;"><i class="fas fa-eye"></i> AI Vision Analysis</span>` :
                    `<span style="background: var(--success); color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; margin-bottom: 12px; display: inline-block;"><i class="fas fa-table"></i> Structured Data</span>`;
                
                summaryEl.innerHTML = sourceBadge + `
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px;">
                        <div class="metric-box" style="background: var(--bg-hover); padding: 12px; border-radius: 8px;">
                            <div style="font-size: 12px; color: var(--text-secondary);">Total Trades</div>
                            <div style="font-size: 20px; font-weight: 600;">${metrics.trades || 0}</div>
                        </div>
                        <div class="metric-box" style="background: var(--bg-hover); padding: 12px; border-radius: 8px;">
                            <div style="font-size: 12px; color: var(--text-secondary);">Win Rate</div>
                            <div style="font-size: 20px; font-weight: 600; color: var(--success);">${metrics.win_rate || 0}%</div>
                        </div>
                        <div class="metric-box" style="background: var(--bg-hover); padding: 12px; border-radius: 8px;">
                            <div style="font-size: 12px; color: var(--text-secondary);">Profit Factor</div>
                            <div style="font-size: 20px; font-weight: 600; color: var(--primary);">${metrics.profit_factor || 0}</div>
                        </div>
                        <div class="metric-box" style="background: var(--bg-hover); padding: 12px; border-radius: 8px;">
                            <div style="font-size: 12px; color: var(--text-secondary);">Expectancy</div>
                            <div style="font-size: 20px; font-weight: 600;">${metrics.expectancy || 0}</div>
                        </div>
                    </div>
                `;
            }

            if (data.analysis) {
                this.splitAnalysis(data.analysis);
            }
        },

        splitAnalysis: function(text) {
            if (!text) return;
            
            const sectionMap = {
                "Key Issues": "top-mistakes",
                "Strengths": "strengths-list",
                "Improvement Plan": "improvement-plan",
                "Recommended Courses": "recommended-courses",
                "Mentor Advice": "mentor-advice"
            };

            for (const [sectionName, elementId] of Object.entries(sectionMap)) {
                const el = document.getElementById(elementId);
                if (!el) continue;

                const regex = new RegExp(`${sectionName}[\\s:]*([\\s\\S]*?)(?=\\n[A-Z][a-zA-Z\\s]+[\\s:]|\\n\\n[A-Z]|$)`, "i");
                const match = text.match(regex);
                
                if (match?.[1]) {
                    const content = match[1].trim();
                    if (elementId === "recommended-courses") {
                        const courses = content.split(/[,\n]/).map(c => c.replace(/^[-•*]\s*/, '').trim()).filter(c => c && c.length > 2);
                        el.innerHTML = courses.map(c => `<span class="tag" style="background: var(--primary); color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; margin: 4px; display: inline-block;">${c}</span>`).join('');
                    } else if (elementId === "mentor-advice") {
                        el.innerHTML = content.replace(/\n/g, '<br>');
                    } else {
                        el.innerHTML = formatList(content);
                    }
                } else {
                    if (el.tagName === "UL") {
                        el.innerHTML = "<li>Analysis data not available for this section.</li>";
                    } else {
                        el.textContent = "No data available.";
                    }
                }
            }
        }
    };
    
    console.log('Pipways AI Engine v2.1 (Multi-Format) initialized successfully');
})();
