/**
 * Pipways AI Engine v2.2
 * Production-Ready Namespaced Module
 * Supports: CSV, Excel, PDF, and Images
 */

(function() {
    'use strict';
    
    // Prevent double initialization
    if (window.ai && window.ai.__initialized) {
        console.log('AI module already initialized');
        return;
    }
    
    // Local constants - no global scope pollution
    const API_BASE = "/api/ai";
    
    // Temporary storage for uploaded files
    let currentChartFile = null;
    let currentPerformanceFile = null;
    
    /* ===============================
       PRIVATE API HELPERS
    ================================ */
    
    async function apiRequest(endpoint, method, body) {
        const options = {
            method: method || "POST",
            headers: {}
        };

        if (body instanceof FormData) {
            options.body = body;
        } else if (body) {
            options.headers["Content-Type"] = "application/json";
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(`${API_BASE}${endpoint}`, options);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || `HTTP ${response.status}`);
            }

            return response.json();
        } catch (error) {
            console.error(`API Request failed: ${endpoint}`, error);
            throw error;
        }
    }

    function appendChat(role, text) {
        const chatBox = document.getElementById("chat-messages");
        if (!chatBox) {
            console.error("chat-messages element not found");
            return;
        }

        const msg = document.createElement("div");
        msg.className = "chat-message";
        msg.style.cssText = "display: flex; justify-content: " + (role === "user" ? "flex-end" : "flex-start") + "; margin-bottom: 12px;";
        
        const bubble = document.createElement("div");
        bubble.className = "chat-bubble";
        bubble.style.cssText = role === "user" 
            ? "background: var(--primary); color: white; padding: 12px 16px; border-radius: 12px; max-width: 80%; line-height: 1.5; word-wrap: break-word;"
            : "background: var(--bg-hover); padding: 12px 16px; border-radius: 12px; max-width: 80%; line-height: 1.5; word-wrap: break-word;";
        
        if (role === "ai") {
            bubble.innerHTML = "<strong>AI Mentor:</strong> " + text.replace(/\n/g, '<br>');
        } else {
            bubble.textContent = text;
        }
        
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
            if (cleanLine && !cleanLine.match(/^(Key Issues|Strengths|Improvement|Recommended Courses|Mentor Advice|Performance|Risk|Discipline|Overall)/i)) {
                html += `<li style="margin-bottom: 8px; line-height: 1.5;">${cleanLine}</li>`;
            }
        });
        
        return html || "<li>No specific items listed.</li>";
    }

    /* ===============================
       PUBLIC API (window.ai namespace)
    ================================ */
    
    window.ai = {
        __initialized: true,
        
        /**
         * AI Mentor Chat - Send message
         */
        sendChatMessage: async function() {
            const input = document.getElementById("chat-input");
            if (!input) {
                console.error("chat-input element not found");
                return;
            }

            const message = input.value.trim();
            if (!message) return;

            // Add user message to chat
            appendChat("user", message);
            input.value = "";

            // Show typing indicator
            const chatBox = document.getElementById("chat-messages");
            const typingId = "typing-" + Date.now();
            const typingMsg = document.createElement("div");
            typingMsg.id = typingId;
            typingMsg.className = "chat-message";
            typingMsg.style.cssText = "display: flex; justify-content: flex-start; margin-bottom: 12px;";
            typingMsg.innerHTML = '<div style="background: var(--bg-hover); padding: 12px 16px; border-radius: 12px;"><i class="fas fa-spinner fa-spin"></i> AI is typing...</div>';
            chatBox.appendChild(typingMsg);
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const res = await apiRequest("/mentor", "POST", { message: message });
                
                // Remove typing indicator
                const typingEl = document.getElementById(typingId);
                if (typingEl) typingEl.remove();
                
                appendChat("ai", res.response || "I'm sorry, I couldn't process that request.");
            } catch (error) {
                // Remove typing indicator
                const typingEl = document.getElementById(typingId);
                if (typingEl) typingEl.remove();
                
                console.error("Mentor error:", error);
                appendChat("ai", "I'm having trouble connecting right now. Please try again in a moment.");
            }
        },

        /**
         * Handle Chart Image Upload
         */
        handleChartUpload: function(input) {
            if (!input || !input.files || !input.files[0]) return;
            
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
                reader.onerror = function() {
                    alert("Error reading file. Please try again.");
                };
                reader.readAsDataURL(currentChartFile);
            } else {
                console.error("Chart preview elements not found");
            }
        },

        /**
         * Analyze Chart with AI
         */
        analyzeChart: async function() {
            if (!currentChartFile) {
                alert("Please upload a chart image first.");
                return;
            }

            const pairEl = document.getElementById("chart-pair");
            const timeframeEl = document.getElementById("chart-timeframe");
            const contextEl = document.getElementById("chart-context");
            
            const pair = pairEl ? pairEl.value : "EURUSD";
            const timeframe = timeframeEl ? timeframeEl.value : "1H";
            const context = contextEl ? contextEl.value : "";

            const formData = new FormData();
            formData.append("image", currentChartFile);
            formData.append("pair", pair);
            formData.append("timeframe", timeframe);
            formData.append("context", context);

            const resultBox = document.getElementById("chart-analysis-content");
            const resultContainer = document.getElementById("chart-analysis-result");
            
            if (resultBox) {
                resultBox.innerHTML = "<p style='text-align: center; padding: 40px;'><i class='fas fa-spinner fa-spin fa-2x' style='color: var(--primary);'></i><br><br>Analyzing chart with AI...</p>";
            }
            if (resultContainer) {
                resultContainer.classList.remove("hidden");
            }

            try {
                const res = await apiRequest("/analyze-chart", "POST", formData);
                if (resultBox) {
                    resultBox.innerHTML = res.analysis ? res.analysis.replace(/\n/g, '<br>') : "No analysis received.";
                }
            } catch (error) {
                console.error("Chart analysis error:", error);
                if (resultBox) {
                    resultBox.innerHTML = "<p style='color: var(--danger); text-align: center; padding: 20px;'><i class='fas fa-exclamation-circle'></i><br>Chart analysis failed. Please ensure the image is clear and try again.</p>";
                }
            }
        },

        /**
         * Handle Performance File Upload (CSV/Excel/PDF/Image)
         */
        handlePerformanceUpload: function(input) {
            if (!input || !input.files || !input.files[0]) {
                console.error("No file selected");
                return;
            }
            
            const file = input.files[0];
            
            // Validate file extension
            const validExtensions = ['.csv', '.xls', '.xlsx', '.pdf', '.jpg', '.jpeg', '.png', '.webp', '.gif'];
            const fileName = file.name.toLowerCase();
            const hasValidExt = validExtensions.some(ext => fileName.endsWith(ext));
            
            if (!hasValidExt) {
                alert("Please upload a valid file: CSV, Excel, PDF, or Image (JPG, PNG, WEBP)");
                input.value = '';
                return;
            }
            
            // Check file size (10MB max)
            if (file.size > 10 * 1024 * 1024) {
                alert("File is too large. Maximum size is 10MB.");
                input.value = '';
                return;
            }
            
            currentPerformanceFile = file;
            
            const container = document.getElementById("performance-preview-container");
            const preview = document.getElementById("performance-preview");
            
            if (!container) {
                console.error("performance-preview-container not found");
                return;
            }
            
            container.classList.remove("hidden");
            
            // Remove old file info if exists
            const oldInfo = document.getElementById("performance-file-info");
            if (oldInfo) oldInfo.remove();
            
            // Determine icon and color based on file type
            let fileIcon = 'fa-file';
            let fileColor = 'var(--text-secondary)';
            
            if (fileName.endsWith('.pdf')) {
                fileIcon = 'fa-file-pdf';
                fileColor = 'var(--danger)';
            } else if (fileName.match(/\.(jpg|jpeg|png|webp|gif)$/)) {
                fileIcon = 'fa-file-image';
                fileColor = 'var(--primary)';
            } else if (fileName.match(/\.(csv|xls|xlsx)$/)) {
                fileIcon = 'fa-file-csv';
                fileColor = 'var(--success)';
            }
            
            // Create file info display
            const fileInfo = document.createElement("div");
            fileInfo.id = "performance-file-info";
            fileInfo.style.cssText = "text-align: center; padding: 30px; background: var(--bg-hover); border-radius: 12px; margin-bottom: 16px; border: 2px dashed var(--border);";
            fileInfo.innerHTML = `
                <i class="fas ${fileIcon}" style="font-size: 64px; color: ${fileColor}; margin-bottom: 16px; display: block;"></i>
                <div style="font-weight: 600; font-size: 16px; margin-bottom: 8px; word-break: break-word;">${file.name}</div>
                <div style="color: var(--text-secondary); font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">
                    ${(file.size/1024).toFixed(1)} KB
                </div>
            `;
            
            // Insert at beginning of container
            container.insertBefore(fileInfo, container.firstChild);
            
            // Handle image preview if it's an image
            if (preview) {
                if (file.type && file.type.startsWith('image/')) {
                    preview.style.display = 'block';
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        preview.src = e.target.result;
                    };
                    reader.readAsDataURL(file);
                } else {
                    preview.style.display = 'none';
                }
            }
            
            console.log("Performance file selected:", file.name);
        },

        /**
         * Analyze Performance (Multi-Format)
         */
        analyzePerformanceVision: async function() {
            if (!currentPerformanceFile) {
                alert("Please upload a trading statement first.");
                return;
            }

            const formData = new FormData();
            formData.append("file", currentPerformanceFile);

            const container = document.getElementById("analysis-results");
            
            if (container) {
                container.classList.remove("hidden");
                // Scroll to results
                setTimeout(() => {
                    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 100);
            }
            
            // Show loading state in score
            const scoreEl = document.getElementById("trader-score");
            if (scoreEl) {
                scoreEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            }
            
            const summaryEl = document.getElementById("performance-summary");
            if (summaryEl) {
                summaryEl.innerHTML = '<p style="text-align: center; padding: 40px;"><i class="fas fa-spinner fa-spin fa-2x"></i><br><br>AI is analyzing your trading data...</p>';
            }

            try {
                const result = await apiRequest("/analyze-performance-file", "POST", formData);
                this.renderPerformance(result);
            } catch (error) {
                console.error("Performance analysis error:", error);
                
                const errorMsg = error.message || "Analysis failed. Please try again.";
                
                if (container) {
                    container.innerHTML = `
                        <div style="color: var(--danger); text-align: center; padding: 40px; background: var(--bg-card); border-radius: 12px; margin: 20px;">
                            <i class="fas fa-exclamation-circle" style="font-size: 48px; margin-bottom: 16px; display: block;"></i>
                            <strong style="font-size: 18px; display: block; margin-bottom: 8px;">Analysis Failed</strong>
                            <span style="opacity: 0.8;">${errorMsg}</span>
                        </div>
                    `;
                } else {
                    alert("Analysis failed: " + errorMsg);
                }
            }
        },

        /**
         * Render Performance Metrics to DOM
         */
        renderPerformance: function(data) {
            if (!data) {
                console.error("No data received from analysis");
                return;
            }
            
            const metrics = data.metrics || {};
            const isVision = data.source === 'vision_ocr';
            
            // Calculate score
            let score = 0;
            if (metrics.overall_score) {
                score = Math.round(metrics.overall_score);
            } else if (metrics.win_rate && metrics.profit_factor) {
                score = Math.round((metrics.win_rate * metrics.profit_factor) / 10);
            }
            // Clamp score between 0-100
            score = Math.max(0, Math.min(100, score));
            if (isNaN(score)) score = 0;
            
            // Update Score Display
            const scoreEl = document.getElementById("trader-score");
            const scoreCircle = document.getElementById("score-circle");
            const scoreInterp = document.getElementById("score-interpretation");
            
            if (scoreEl) {
                scoreEl.textContent = score;
            }
            if (scoreCircle) {
                scoreCircle.style.setProperty('--score', score);
            }
            if (scoreInterp) {
                if (score >= 80) scoreInterp.textContent = "Excellent trading performance";
                else if (score >= 60) scoreInterp.textContent = "Good performance with room for improvement";
                else if (score >= 40) scoreInterp.textContent = "Average - focus on risk management";
                else scoreInterp.textContent = "Needs significant improvement - consider coaching";
            }

            // Update Summary with source badge
            const summaryEl = document.getElementById("performance-summary");
            if (summaryEl) {
                const sourceBadge = isVision 
                    ? `<span style="background: var(--warning); color: var(--bg-dark); padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; display: inline-block; margin-bottom: 12px;"><i class="fas fa-eye"></i> AI Vision Analysis</span>`
                    : `<span style="background: var(--success); color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; display: inline-block; margin-bottom: 12px;"><i class="fas fa-table"></i> Structured Data</span>`;
                
                summaryEl.innerHTML = sourceBadge + `
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-top: 12px;">
                        <div style="background: var(--bg-hover); padding: 16px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">Total Trades</div>
                            <div style="font-size: 24px; font-weight: 700; color: var(--text-primary);">${metrics.trades || 0}</div>
                        </div>
                        <div style="background: var(--bg-hover); padding: 16px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">Win Rate</div>
                            <div style="font-size: 24px; font-weight: 700; color: var(--success);">${metrics.win_rate || 0}%</div>
                        </div>
                        <div style="background: var(--bg-hover); padding: 16px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">Profit Factor</div>
                            <div style="font-size: 24px; font-weight: 700; color: var(--primary);">${metrics.profit_factor || 0}</div>
                        </div>
                        <div style="background: var(--bg-hover); padding: 16px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">Expectancy</div>
                            <div style="font-size: 24px; font-weight: 700; color: var(--text-primary);">${metrics.expectancy !== undefined ? metrics.expectancy : 0}</div>
                        </div>
                    </div>
                `;
            }

            // Process AI Analysis Sections
            if (data.analysis) {
                this.splitAnalysis(data.analysis);
            }
        },

        /**
         * Split AI Analysis text into sections
         */
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

                // Create regex to find section content
                const regex = new RegExp(`${sectionName}[\\s:]*([\\s\\S]*?)(?=\\n[A-Z][a-zA-Z\\s]+[\\s:]|\\n\\n[A-Z]|$)`, "i");
                const match = text.match(regex);
                
                if (match && match[1]) {
                    const content = match[1].trim();
                    
                    if (elementId === "recommended-courses") {
                        // Create tag buttons for courses
                        const courses = content.split(/[,\n]/).map(c => c.replace(/^[-•*]\s*/, '').trim()).filter(c => c.length > 2);
                        if (courses.length > 0) {
                            el.innerHTML = courses.map(c => `<span style="background: var(--primary); color: white; padding: 6px 14px; border-radius: 16px; font-size: 12px; margin: 4px; display: inline-block; font-weight: 500;">${c}</span>`).join('');
                        } else {
                            el.innerHTML = "<li>No specific courses recommended.</li>";
                        }
                    } else if (elementId === "mentor-advice") {
                        el.innerHTML = content.replace(/\n/g, '<br>');
                    } else {
                        // List items for UL elements
                        if (el.tagName === "UL") {
                            el.innerHTML = formatList(content);
                        } else {
                            el.innerHTML = content.replace(/\n/g, '<br>');
                        }
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
    
    console.log('Pipways AI Engine v2.2 initialized successfully');
})();
