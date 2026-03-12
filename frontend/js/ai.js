/*
Pipways AI Engine
Stable Production Version
*/

const API_BASE = "/api/ai";


/* ===============================
   API REQUEST
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



/* ===============================
   AI MENTOR
================================ */

async function sendMentorMessage() {

    const input = document.getElementById("mentorInput");
    const chatBox = document.getElementById("mentorChat");

    if (!input || !chatBox) return;

    const message = input.value.trim();
    if (!message) return;

    appendChat("user", message);
    input.value = "";

    try {

        const res = await apiRequest("/mentor", "POST", {
            message: message
        });

        appendChat("ai", res.response);

    } catch (error) {

        appendChat("ai", "AI mentor unavailable.");
    }
}


function appendChat(role, text) {

    const chatBox = document.getElementById("mentorChat");
    if (!chatBox) return;

    const msg = document.createElement("div");

    msg.className = role === "user"
        ? "chat-user"
        : "chat-ai";

    msg.innerText = text;

    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}



/* ===============================
   AI CHART ANALYZER
================================ */

async function analyzeChart() {

    const fileInput = document.getElementById("chartImage");

    if (!fileInput || !fileInput.files.length) {

        alert("Please upload chart image.");
        return;
    }

    const pair = document.getElementById("pair")?.value || "EURUSD";
    const timeframe = document.getElementById("timeframe")?.value || "1H";
    const context = document.getElementById("context")?.value || "";

    const formData = new FormData();

    formData.append("image", fileInput.files[0]);
    formData.append("pair", pair);
    formData.append("timeframe", timeframe);
    formData.append("context", context);

    const resultBox = document.getElementById("chartResult");

    if (resultBox) resultBox.innerHTML = "Analyzing chart...";

    try {

        const res = await apiRequest("/analyze-chart", "POST", formData);

        if (resultBox) resultBox.innerText = res.analysis;

    } catch (error) {

        console.error(error);

        if (resultBox)
            resultBox.innerText = "Chart analysis failed.";
    }
}



/* ===============================
   PERFORMANCE ANALYZER
================================ */

async function analyzePerformance() {

    const fileInput = document.getElementById("performanceFile");

    if (!fileInput || !fileInput.files.length) {

        alert("Upload trading statement");
        return;
    }

    const file = fileInput.files[0];

    const allowed = [
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ];

    if (!allowed.includes(file.type)) {

        alert("Supported formats: CSV or Excel");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const summary = document.getElementById("performanceSummary");

    if (summary) summary.innerHTML = "Analyzing trading performance...";

    try {

        const result = await apiRequest(
            "/analyze-performance-file",
            "POST",
            formData
        );

        renderPerformance(result);

    } catch (error) {

        console.error(error);

        if (summary)
            summary.innerHTML = "Performance analysis failed.";
    }
}



/* ===============================
   RENDER PERFORMANCE DATA
================================ */

function renderPerformance(data) {

    const metrics = data.metrics;

    const summary = document.getElementById("performanceSummary");

    if (summary) {

        summary.innerHTML = `
            <div>Trades: ${metrics.trades}</div>
            <div>Win Rate: ${metrics.win_rate}%</div>
            <div>Profit Factor: ${metrics.profit_factor}</div>
            <div>Risk Reward: ${metrics.risk_reward}</div>
            <div>Expectancy: ${metrics.expectancy}</div>
        `;
    }

    splitAnalysis(data.analysis);
}



/* ===============================
   SPLIT AI RESPONSE
================================ */

function splitAnalysis(text) {

    const sections = {
        "Key Issues": "keyIssues",
        "Strengths": "strengths",
        "Improvement Plan": "improvementPlan",
        "Recommended Courses": "recommendedCourses",
        "Mentor Advice": "mentorAdvice"
    };

    for (const title in sections) {

        const id = sections[title];
        const box = document.getElementById(id);

        if (!box) continue;

        const regex = new RegExp(`${title}([\\s\\S]*?)(?=\\n[A-Z]|$)`, "i");

        const match = text.match(regex);

        if (match) {

            box.innerHTML = formatList(match[1]);

        } else {

            box.innerHTML = "No data available.";
        }
    }
}



/* ===============================
   FORMAT BULLET LIST
================================ */

function formatList(text) {

    const lines = text
        .split("\n")
        .filter(l => l.trim() !== "");

    let html = "<ul>";

    lines.forEach(line => {

        html += `<li>${line.replace("-", "").trim()}</li>`;
    });

    html += "</ul>";

    return html;
}



/* ===============================
   DRAG DROP SUPPORT
================================ */

function setupDragDrop() {

    const drop = document.getElementById("performanceDrop");

    if (!drop) return;

    drop.addEventListener("dragover", e => {

        e.preventDefault();
    });

    drop.addEventListener("drop", e => {

        e.preventDefault();

        const files = e.dataTransfer.files;

        const input = document.getElementById("performanceFile");

        if (input) input.files = files;
    });
}



/* ===============================
   INIT
================================ */

document.addEventListener("DOMContentLoaded", () => {

    setupDragDrop();
});
