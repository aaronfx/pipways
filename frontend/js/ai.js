/**
 * Pipways AI Engine v2.3
 * Production-Ready Namespaced Module
 */

(function() {
    'use strict';
    
    // Prevent double initialization
    if (window.ai && window.ai.__initialized) {
        console.log('AI module already initialized');
        return;
    }
    
    const API_BASE = "/api/ai";
    
    // File storage
    let currentChartFile = null;
    let currentPerformanceFile = null;
    
    /* ===============================
       PRIVATE HELPERS
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
        msg.style.cssText = "margin-bottom: 12px; display: flex; justify-content: " + (role === "user" ? "flex-end" : "flex-start") + ";";
        
        const bubble = document.createElement("div");
        bubble.style.cssText = role === "user" 
            ? "background: var(--primary); color: white; padding: 12px 16px; border-radius: 12px; max-width: 70%; line-height: 1.5;"
            : "background: var(--bg-hover); padding: 12px 16px; border-radius: 12px; max-width: 70%; line-height: 1.5;";
        
        if (role === "ai") {
            bubble.innerHTML = "<strong>AI Mentor:</strong> " + text.replace(/\n/g, '<br>');
        } else {
            bubble.textContent = text;
        }
        
        msg.appendChild(bubble);
        chatBox.appendChild(msg);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function ensureContainersExist() {
        // Ensure analysis results container exists
        let container = document.getElementById("analysis-results");
        if (!container) {
            container = document.createElement("div");
            container.id = "analysis-results";
            container.className = "hidden";
            
            const performanceSection = document.getElementById("performance-section");
            if (performanceSection) {
                performanceSection.appendChild(container);
            }
        }
        
        // Ensure metric containers exist inside analysis-results
        const requiredIds = [
            "trader-score", 
            "score-circle", 
            "score-interpretation",
            "performance-summary",
            "top-mistakes", 
            "strengths-list", 
            "improvement-plan", 
            "recommended-courses", 
            "mentor-advice"
        ];
        
        requiredIds.forEach(id => {
            if (!document.getElementById(id)) {
                const el = document.createElement("div");
                el.id = id;
                if (container) container.appendChild(el);
            }
        });
    }

    /* ===============================
       PUBLIC API (window.ai)
    ================================ */
    
    window.ai = {
        __initialized: true,
        
        /**
         * Initialize AI Mentor with welcome message
         */
        initMentor: function() {
            const chatBox = document.getElementById("chat-messages");
            if (!chatBox) return;
            
            // Only add welcome message if chat is empty
            if (chatBox.children.length === 0) {
                appendChat("ai", "Hello! I'm your AI trading mentor. Ask me anything about trading strategies, risk management, psychology, or market analysis.");
            }
        },
        
        /**
         * Send chat message to AI Mentor
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
                appendChat("ai", res.response || "I'm here to help with your trading questions.");
            } catch (error) {
                console.error("Mentor error:", error);
                appendChat("ai", "I'm having trouble connecting. Please try again.");
            }
        },

        /**
         * Handle chart upload
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
                reader.readAsDataURL(currentChartFile);
            }
        },

        /**
         * Analyze chart image
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
                resultBox.innerHTML = "<p style='text-align: center; padding: 20px;'><i class='fas fa-spinner fa-spin'></i> Analyzing...</p>";
            }
            if (resultContainer) {
                resultContainer.classList.remove("hidden");
            }

            try {
                const res = await apiRequest("/analyze-chart", "POST", formData);
                if (resultBox) {
                    resultBox.innerHTML = res.analysis ? res.analysis.replace(/\n/g, '<br>') : "No analysis available.";
                }
            } catch (error) {
                console.error("Chart analysis error:", error);
                if (resultBox) {
                    resultBox.innerHTML = "<p style='color: var(--danger);'>Analysis failed. Please try again.</p>";
                }
            }
        },

        /**
         * Handle performance file upload
         */
        handlePerformanceUpload: function(input) {
            if (!input || !input.files || !input.files[0]) return;
            
            const file = input.files[0];
            const validExts = ['.csv', '.xlsx', '.xls', '.png', '.jpg', '.jpeg', '.pdf'];
            const fileName = file.name.toLowerCase();
            
            const isValid = validExts.some(ext => fileName.endsWith(ext));
            if (!isValid) {
                alert("Please upload CSV, Excel, PNG, JPG, or PDF files only.");
                input.value = '';
                return;
            }
            
            currentPerformanceFile = file;
            
            const container = document.getElementById("performance-preview-container");
            if (container) {
                container.classList.remove("hidden");
            }
            
            console.log("File selected:", file.name);
        },

        /**
         * Analyze performance (main function for button)
         */
        analyzePerformance: async function() {
            if (!currentPerformanceFile) {
                alert("Please upload a trading statement first.");
                return;
            }

            // Ensure containers exist before rendering
            ensureContainersExist();

            const formData = new FormData();
            formData.append("file", currentPerformanceFile);

            const container = document.getElementById("analysis-results");
            if (container) {
                container.classList.remove("hidden");
                container.innerHTML = "<p style='text-align: center; padding: 40px;'><i class='fas fa-spinner fa-spin fa-2x'></i><br><br>Analyzing performance...</p>";
            }

            try {
                const result = await apiRequest("/analyze-performance-file", "POST", formData);
                this.renderPerformance(result);
            } catch (error) {
                console.error("Performance analysis error:", error);
                if (container) {
                    container.innerHTML = "<p style='color: var(--danger); text-align: center; padding: 20px;'>Analysis failed. " + error.message + "</p>";
                }
            }
        },

        /**
         * Render performance analysis results
         */
        renderPerformance: function(data) {
            if (!data || !data.metrics) {
                console.error("Invalid data received");
                return;
            }
            
            const metrics = data.metrics;
            const container = document.getElementById("analysis-results");
            
            if (!container) return;
            
            // Build HTML for results
            let html = '<div style="padding: 20px;">';
            
            // Score display
            const score = metrics.overall_score || Math.round((metrics.win_rate || 0) * (metrics.profit_factor || 1) / 10);
            html += `
                <div style="text-align: center; margin-bottom: 30px;">
                    <div style="font-size: 48px; font-weight: bold; color: var(--primary);">${score || 0}</div>
                    <div style="color: var(--text-secondary);">Performance Score</div>
                </div>
            `;
            
            // Metrics grid
            html += `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin-bottom: 30px;">
                    <div style="background: var(--bg-hover); padding: 16px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 24px; font-weight: bold; color: var(--success);">${metrics.trades || 0}</div>
                        <div style="font-size: 12px; color: var(--text-secondary);">Total Trades</div>
                    </div>
                    <div style="background: var(--bg-hover); padding: 16px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 24px; font-weight: bold; color: var(--success);">${metrics.win_rate || 0}%</div>
                        <div style="font-size: 12px; color: var(--text-secondary);">Win Rate</div>
                    </div>
                    <div style="background: var(--bg-hover); padding: 16px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 24px; font-weight: bold; color: var(--primary);">${metrics.profit_factor || 0}</div>
                        <div style="font-size: 12px; color: var(--text-secondary);">Profit Factor</div>
                    </div>
                </div>
            `;
            
            // AI Analysis sections
            if (data.analysis) {
                const analysis = data.analysis;
                
                // Parse sections
                const sections = [
                    { name: "Key Issues", id: "key-issues" },
                    { name: "Strengths", id: "strengths" },
                    { name: "Improvement Plan", id: "improvement" },
                    { name: "Mentor Advice", id: "advice" }
                ];
                
                sections.forEach(section => {
                    const regex = new RegExp(`${section.name}[\\s:]*([\\s\\S]*?)(?=\\n[A-Z][a-zA-Z\\s]+[\\s:]|\\n\\n[A-Z]|$)`, "i");
                    const match = analysis.match(regex);
                    const content = match ? match[1].trim() : "No data available.";
                    
                    html += `
                        <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 16px;">
                            <h3 style="margin-top: 0; color: var(--primary);">${section.name}</h3>
                            <div style="line-height: 1.6;">${content.replace(/\n/g, '<br>')}</div>
                        </div>
                    `;
                });
            }
            
            html += '</div>';
            container.innerHTML = html;
        }
    };
    
    // Auto-initialize mentor when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            window.ai.initMentor();
        });
    } else {
        window.ai.initMentor();
    }
    
    console.log('Pipways AI Engine v2.3 initialized successfully');
})();
