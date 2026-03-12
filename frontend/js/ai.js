/**
 * AI Tools Module
 * Stable version
 */

const ai = {

    chatHistory: [],
    currentChartFile: null,
    currentPerformanceImage: null,

    // =========================
    // AI MENTOR CHAT
    // =========================
    async sendChatMessage() {

        const input = document.getElementById('chat-input');
        const messagesContainer = document.getElementById('chat-messages');

        const message = input.value.trim();
        if (!message) return;

        const userDiv = document.createElement("div");
        userDiv.className = "chat-message user";
        userDiv.innerHTML = `<div class="chat-bubble"><strong>You:</strong> ${message}</div>`;
        messagesContainer.appendChild(userDiv);

        input.value = "";

        try {

            const response = await api.post('/api/ai/mentor', {
                message: message,
                history: this.chatHistory
            });

            const aiText = response.response || "No response";

            const aiDiv = document.createElement("div");
            aiDiv.className = "chat-message";

            aiDiv.innerHTML =
                `<div class="chat-bubble"><strong>AI Mentor:</strong> ${marked.parse(aiText)}</div>`;

            messagesContainer.appendChild(aiDiv);

        } catch (error) {

            console.error(error);
            ui.showToast("AI error", "error");

        }

    },


    // =========================
    // CHART IMAGE UPLOAD
    // =========================
    handleChartUpload(input) {

        const file = input.files[0];
        if (!file) return;

        this.currentChartFile = file;

        const reader = new FileReader();

        reader.onload = (e) => {

            const preview = document.getElementById("chart-preview");
            const container = document.getElementById("chart-preview-container");

            preview.src = e.target.result;
            container.classList.remove("hidden");

        };

        reader.readAsDataURL(file);

    },


    // =========================
    // CHART AI ANALYSIS
    // =========================
    async analyzeChart() {

        if (!this.currentChartFile) {

            ui.showToast("Upload chart first", "error");
            return;

        }

        ui.showLoading("Analyzing chart...");

        try {

            const formData = new FormData();

            formData.append("image", this.currentChartFile);
            formData.append("pair", document.getElementById("chart-pair").value);
            formData.append("timeframe", document.getElementById("chart-timeframe").value);
            formData.append("context", document.getElementById("chart-context").value);

            const response = await api.upload('/api/ai/analyze-chart', formData);

            const result = document.getElementById("chart-analysis-result");
            const content = document.getElementById("chart-analysis-content");

            content.innerHTML = marked.parse(response.analysis);

            result.classList.remove("hidden");

        } catch (error) {

            console.error(error);
            ui.showToast("Analysis failed", "error");

        } finally {

            ui.hideLoading();

        }

    },


    // =========================
    // PERFORMANCE IMAGE
    // =========================
    handlePerformanceUpload(input) {

        const file = input.files[0];
        if (!file) return;

        const reader = new FileReader();

        reader.onload = (e) => {

            this.currentPerformanceImage = e.target.result;

            const preview = document.getElementById("performance-preview");
            const container = document.getElementById("performance-preview-container");

            preview.src = e.target.result;
            container.classList.remove("hidden");

        };

        reader.readAsDataURL(file);

    },


    // =========================
    // PERFORMANCE AI
    // =========================
    async analyzePerformanceVision() {

        if (!this.currentPerformanceImage) {

            ui.showToast("Upload statement image first", "error");
            return;

        }

        ui.showLoading("Analyzing performance...");

        try {

            const balance =
                parseFloat(document.getElementById("vision-account-balance").value) || 0;

            const period =
                parseInt(document.getElementById("vision-trading-period").value) || 30;

            const response = await api.post('/api/ai/analyze-vision', {

                image: this.currentPerformanceImage,
                account_balance: balance,
                trading_period_days: period

            });

            this.displayPerformanceResults(response);

        } catch (error) {

            console.error(error);

            ui.showToast("Performance analysis failed", "error");

        } finally {

            ui.hideLoading();

        }

    },


    // =========================
    // DISPLAY RESULTS
    // =========================
    displayPerformanceResults(data) {

        const container = document.getElementById("analysis-results");

        container.classList.remove("hidden");

        document.getElementById("trader-score").textContent = data.trader_score;

        const analysis = document.getElementById("performance-analysis-text");

        analysis.innerHTML = marked.parse(data.analysis);

    }

};
