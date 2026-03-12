/**
 * Pipways AI Engine
 * Production-Ready Namespaced Module
 * Prevents duplicate declaration errors via IIFE encapsulation
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
    async function apiRequest(endpoint, method = "POST", body = null) {
        const options = {
            method: method,
            headers: {}
        };

        if (body instanceof FormData) {
            options.body = body;
        } else if (body) {
            options.headers["Content-Type"] = "application/json";
            options.body = JSON.stringify(body);
        }

        const response = await fetch(`${API_BASE}${endpoint}`, options);

        if (!response.ok) {
            const error = await response.text();
            throw new Error(error);
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
        
        if (role === "ai") {
            bubble.innerHTML = `<strong>AI Mentor:</strong> ${text}`;
        } else {
            bubble.textContent = text;
        }
        
        msg.appendChild(bubble);
        chatBox.appendChild(msg);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function formatList(text) {
        if (!text) return "<li>No data available.</li>";
        
        const lines = text
            .split("\n")
            .map(l => l.trim())
            .filter(l => l.length > 0);
            
        let html = "";
        lines.forEach(line => {
            // Remove bullet markers
            const cleanLine = line.replace(/^[-•*]\s*/, '').replace(/^\d+\.\s*/, '');
            if (cleanLine && !cleanLine.match(/^Key Issues|^Strengths|^Improvement|^Recommended|^Mentor/i)) {
                html += `<li>${cleanLine}</li>`;
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
         * Corresponds to: id="chat-input", id="chat-messages"
         */
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

        /**
         * Handle Chart Image Upload
         * Stores file and displays preview
         */
        handleChartUpload: function(input) {
            if (!input?.files?.[0]) return;
            
            currentChartFile = input.files[0];
            
            const preview = document.getElementById("chart-preview");
            const container = document.getElementById("chart-preview-container");
            
            if (preview && container) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    container.classList.remove("hidden");
                };
                reader.readAsDataURL(currentChartFile);
            }
        },

        /**
         * Analyze Chart with AI
         * Uses stored file from handleChartUpload
         */
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
            
            if (resultBox) {
                resultBox.innerHTML = "<p><i class='fas fa-spinner fa-spin'></i> Analyzing chart with AI...</p>";
            }
            if (resultContainer) {
                resultContainer.classList.remove("hidden");
            }

            try {
                const res = await apiRequest("/analyze-chart", "POST", formData);
                if (resultBox) {
                    // Preserve line breaks from AI response
                    resultBox.innerHTML = res.analysis.replace(/\n/g, '<br>');
                }
            } catch (error) {
                console.error("Chart analysis error:", error);
                if (resultBox) {
                    resultBox.innerHTML = "<p style='color: var(--danger);'>Chart analysis failed. Please ensure the image is clear and try again.</p>";
                }
            }
        },

        /**
         * Handle Performance Statement Upload
         */
        handlePerformanceUpload: function(input) {
            if (!input?.files?.[0]) return;
            
            const file = input.files[0];
            const allowed = ["image/jpeg", "image/png", "image/webp", "image/jpg"];
            
            if (!allowed.includes(file.type)) {
                alert("Supported formats: JPG, PNG, WEBP only");
                return;
            }
            
            currentPerformanceFile = file;
            
            const preview = document.getElementById("performance-preview");
            const container = document.getElementById("performance-preview-container");
            
            if (preview && container) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    container.classList.remove("hidden");
                };
                reader.readAsDataURL(currentPerformanceFile);
            }
        },

        /**
         * Analyze Performance with AI Vision
         */
        analyzePerformanceVision: async function() {
            if (!currentPerformanceFile) {
                alert("Please upload a trading statement image first.");
                return;
            }

            const formData = new FormData();
            formData.append("file", currentPerformanceFile);

            const container = document.getElementById("analysis-results");
            if (container) {
                container.classList.remove("hidden");
                // Show loading state while preserving structure
                const scoreEl = document.getElementById("trader-score");
                if (scoreEl) scoreEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            }

            try {
                const result = await apiRequest("/analyze-performance-file", "POST", formData);
                this.renderPerformance(result);
            } catch (error) {
                console.error("Performance analysis error:", error);
                if (container) {
                    container.innerHTML = "<p style='color: var(--danger); text-align: center; padding: 40px;'>Analysis failed. Please try a clearer image.</p>";
                }
            }
        },

        /**
         * Render Performance Metrics to DOM
         */
        renderPerformance: function(data) {
            if (!data?.metrics) return;
            
            const metrics = data.metrics;
            
            // Update Score
            const scoreEl = document.getElementById("trader-score");
            const scoreCircle = document.getElementById("score-circle");
            const scoreInterp = document.getElementById("score-interpretation");
            
            if (scoreEl) {
                const score = Math.round(metrics.overall_score || (metrics.win_rate * metrics.profit_factor) || 0);
                scoreEl.textContent = score;
                if (scoreCircle) scoreCircle.style.setProperty('--score', score);
                
                if (scoreInterp) {
                    if (score >= 80) scoreInterp.textContent = "Excellent trading performance";
                    else if (score >= 60) scoreInterp.textContent = "Good performance with room for improvement";
                    else if (score >= 40) scoreInterp.textContent = "Average - focus on risk management";
                    else scoreInterp.textContent = "Needs significant improvement";
                }
            }

            // Update Summary Metrics
            const summaryEl = document.getElementById("performance-summary");
            if (summaryEl) {
                summaryEl.innerHTML = `
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

                // Extract section using regex (handles multiline)
                const regex = new RegExp(`${sectionName}[\\s:]*([\\s\\S]*?)(?=\\n[A-Z][a-zA-Z\\s]+[\\s:]|\\n\\n[A-Z]|$)`, "i");
                const match = text.match(regex);
                
                if (match?.[1]) {
                    const content = match[1].trim();
                    
                    if (elementId === "recommended-courses") {
                        // Create tag buttons for courses
                        const courses = content.split(/[,\n]/).map(c => c.replace(/^[-•*]\s*/, '').trim()).filter(c => c);
                        el.innerHTML = courses.map(c => `<span class="tag" style="background: var(--primary); color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; margin: 4px; display: inline-block;">${c}</span>`).join('');
                    } else if (elementId === "mentor-advice") {
                        el.innerHTML = content.replace(/\n/g, '<br>');
                    } else {
                        // List items for UL elements
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
    
    console.log('Pipways AI Engine v2.0 initialized successfully');
})();
