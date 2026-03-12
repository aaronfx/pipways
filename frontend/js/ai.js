/**
 * Pipways AI Module
 * Handles:
 * - AI Mentor Chat
 * - Chart Analysis
 * - Performance Vision Analysis
 */

const ai = {

    chatHistory: [],
    currentChartFile: null,
    currentChartImage: null,
    currentPerformanceImage: null,

    /*
    ================================
    AI MENTOR CHAT
    ================================
    */

    async sendChatMessage() {

        const input = document.getElementById('chat-input');
        const messages = document.getElementById('chat-messages');

        if (!input || !messages) return;

        const message = input.value.trim();
        if (!message) return;

        const userMsg = document.createElement('div');
        userMsg.className = 'chat-message user';
        userMsg.innerHTML =
            `<div class="chat-bubble"><strong>You:</strong> ${message}</div>`;

        messages.appendChild(userMsg);
        messages.scrollTop = messages.scrollHeight;

        input.value = "";

        this.chatHistory.push({
            role: "user",
            content: message
        });

        try {

            const response = await api.post('/api/ai/mentor', {

                message: message,
                history: this.chatHistory

            });

            const text = response.response || "No response";

            this.chatHistory.push({
                role: "assistant",
                content: text
            });

            const aiMsg = document.createElement('div');
            aiMsg.className = 'chat-message';

            aiMsg.innerHTML =
                `<div class="chat-bubble"><strong>AI Mentor:</strong> ${marked.parse(text)}</div>`;

            messages.appendChild(aiMsg);
            messages.scrollTop = messages.scrollHeight;

        }
        catch (error) {

            console.error("AI mentor error:", error);

            ui.showToast("AI mentor unavailable", "error");

        }

    },


    /*
    ================================
    CHART IMAGE UPLOAD
    ================================
    */

    handleChartUpload(input) {

        const file = input.files[0];
        if (!file) return;

        if (file.size > 10 * 1024 * 1024) {

            ui.showToast("Image too large (10MB max)", "error");
            return;

        }

        this.currentChartFile = file;

        const reader = new FileReader();

        reader.onload = (e) => {

            this.currentChartImage = e.target.result;

            const preview = document.getElementById("chart-preview");
            const container = document.getElementById("chart-preview-container");

            if (preview) preview.src = e.target.result;

            if (container)
                container.classList.remove("hidden");

        };

        reader.readAsDataURL(file);

    },


    /*
    ================================
    CHART ANALYSIS
    ================================
    */

    async analyzeChart() {

        if (!this.currentChartFile) {

            ui.showToast("Upload chart first", "error");
            return;

        }

        ui.showLoading("Analyzing chart...");

        try {

            const pair =
                document.getElementById("chart-pair")?.value || "EURUSD";

            const timeframe =
                document.getElementById("chart-timeframe")?.value || "1H";

            const context =
                document.getElementById("chart-context")?.value || "";

            const formData = new FormData();

            formData.append("image", this.currentChartFile);
            formData.append("pair", pair);
            formData.append("timeframe", timeframe);
            formData.append("context", context);

            const response =
                await api.upload("/api/ai/analyze-chart", formData);

            const content =
                document.getElementById("chart-analysis-content");

            const result =
                document.getElementById("chart-analysis-result");

            if (content) {

                const text =
                    response.analysis ||
                    "No analysis returned";

                content.innerHTML = marked.parse(text);

            }

            if (result)
                result.classList.remove("hidden");

        }
        catch (error) {

            console.error("Chart AI error:", error);

            ui.showToast("Chart analysis failed", "error");

        }
        finally {

            ui.hideLoading();

        }

    },


    /*
    ================================
    PERFORMANCE IMAGE UPLOAD
    ================================
    */

    handlePerformanceUpload(input) {

        const file = input.files[0];
        if (!file) return;

        const reader = new FileReader();

        reader.onload = (e) => {

            this.currentPerformanceImage = e.target.result;

            const preview =
                document.getElementById("performance-preview");

            const container =
                document.getElementById("performance-preview-container");

            if (preview) preview.src = e.target.result;

            if (container)
                container.classList.remove("hidden");

        };

        reader.readAsDataURL(file);

    },


    /*
    ================================
    PERFORMANCE ANALYSIS
    ================================
    */

    async analyzePerformanceVision() {

        if (!this.currentPerformanceImage) {

            ui.showToast("Upload statement image first", "error");
            return;

        }

        ui.showLoading("Analyzing performance...");

        try {

            const balance =
                parseFloat(
                    document.getElementById("vision-account-balance")?.value
                ) || 0;

            const period =
                parseInt(
                    document.getElementById("vision-trading-period")?.value
                ) || 30;

            const response =
                await api.post("/api/ai/analyze-vision", {

                    image: this.currentPerformanceImage,
                    account_balance: balance,
                    trading_period_days: period

                });

            this.displayPerformanceResults(response);

        }
        catch (error) {

            console.error("Performance AI error:", error);

            ui.showToast("Performance analysis failed", "error");

        }
        finally {

            ui.hideLoading();

        }

    },


    /*
    ================================
    DISPLAY PERFORMANCE RESULTS
    ================================
    */

    displayPerformanceResults(data) {

        const container =
            document.getElementById("analysis-results");

        if (!container) return;

        container.classList.remove("hidden");

        const score =
            document.getElementById("trader-score");

        if (score)
            score.textContent = data.trader_score || 0;


        const analysis =
            document.getElementById("performance-analysis-text");

        if (analysis && data.analysis)
            analysis.innerHTML =
                marked.parse(data.analysis);


        const strengths =
            document.getElementById("strengths-list");

        if (strengths && data.strengths)
            strengths.innerHTML =
                data.strengths.map(s => `<li>${s}</li>`).join("");


        const mistakes =
            document.getElementById("top-mistakes");

        if (mistakes && data.top_mistakes)
            mistakes.innerHTML =
                data.top_mistakes.map(m => `<li>${m}</li>`).join("");


        const plan =
            document.getElementById("improvement-plan");

        if (plan && data.improvement_plan)
            plan.innerHTML =
                data.improvement_plan.map(p => `<li>${p}</li>`).join("");

    }

};
