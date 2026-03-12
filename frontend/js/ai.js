/*
Pipways AI Services
Complete Stable Version
*/

const API_BASE = "/api/ai";


/* --------------------------------
API REQUEST HELPER
-------------------------------- */

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

        const text = await response.text();
        throw new Error(text);
    }

    return response.json();
}



/* --------------------------------
AI MENTOR
-------------------------------- */

async function sendMentorMessage() {

    const input = document.getElementById("mentorInput");

    if (!input) return;

    const message = input.value.trim();

    if (!message) return;

    appendChat("user", message);

    input.value = "";

    try {

        const result = await apiRequest("/mentor", "POST", {
            message: message
        });

        appendChat("ai", result.response);

    } catch (err) {

        appendChat("ai", "AI mentor temporarily unavailable.");
    }
}


function appendChat(role, text) {

    const container = document.getElementById("mentorChat");

    if (!container) return;

    const div = document.createElement("div");

    div.className = role === "user"
        ? "chat-user"
        : "chat-ai";

    div.innerText = text;

    container.appendChild(div);

    container.scrollTop = container.scrollHeight;
}



/* --------------------------------
AI CHART ANALYZER
-------------------------------- */

async function analyzeChart() {

    const fileInput = document.getElementById("chartImage");

    if (!fileInput || !fileInput.files.length) {

        alert("Upload chart image");
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

        const data = await apiRequest("/analyze-chart", "POST", formData);

        if (resultBox) {

            resultBox.innerText = data.analysis;
        }

    } catch (err) {

        if (resultBox) {

            resultBox.innerText = "Chart analysis failed.";
        }
    }
}



/* --------------------------------
AI PERFORMANCE ANALYZER
-------------------------------- */

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

    const summaryBox = document.getElementById("performanceSummary");
    const issuesBox = document.getElementById("keyIssues");
    const strengthBox = document.getElementById("strengths");
    const planBox = document.getElementById("improvementPlan");
    const adviceBox = document.getElementById("mentorAdvice");

    if (summaryBox) summaryBox.innerHTML = "Analyzing trading performance...";

    try {

        const result = await apiRequest(
            "/analyze-performance-file",
            "POST",
            formData
        );

        renderPerformance(result);

    } catch (err) {

        console.error(err);

        if (summaryBox) {

            summaryBox.innerHTML =
                "Performance analysis failed.";
        }
    }
}



/* --------------------------------
RENDER PERFORMANCE RESULTS
-------------------------------- */

function renderPerformance(data) {

    const metrics = data.metrics;
    const analysis = data.analysis || "";

    const summaryBox = document.getElementById("performanceSummary");

    if (summaryBox) {

        summaryBox.innerHTML = `
        <div class="metric">
            Trades: ${metrics.trades}
        </div>
        <div class="metric">
            Win Rate: ${metrics.win_rate}%
        </div>
        <div class="metric">
            Profit Factor: ${metrics.profit_factor}
        </div>
        <div class="metric">
            Risk Reward: ${metrics.risk_reward}
        </div>
        <div class="metric">
            Expectancy: ${metrics.expectancy}
        </div>
        `;
    }

    splitAnalysis(analysis);
}



/* --------------------------------
SPLIT AI RESPONSE INTO SECTIONS
-------------------------------- */

function splitAnalysis(text) {

    const sections = {
        "Key Issues": "keyIssues",
        "Strengths": "strengths",
        "Improvement Plan": "improvementPlan",
        "Recommended Courses": "recommendedCourses",
        "Mentor Advice": "mentorAdvice"
    };

    for (let title in sections) {

        const id = sections[title];

        const box = document.getElementById(id);

        if (!box) continue;

        const regex = new RegExp(`${title}([\\s\\S]*?)(?=\\n[A-Z]|$)`, "i");

        const match = text.match(regex);

        if (match) {

            const content = match[1].trim();

            box.innerHTML = formatList(content);

        } else {

            box.innerHTML = "No data available.";
        }
    }
}



/* --------------------------------
FORMAT BULLET LIST
-------------------------------- */

function formatList(text) {

    const lines = text
        .split("\n")
        .filter(l => l.trim().length > 0);

    let html = "<ul>";

    lines.forEach(line => {

        html += `<li>${line.replace("-", "").trim()}</li>`;
    });

    html += "</ul>";

    return html;
}



/* --------------------------------
FILE DRAG & DROP SUPPORT
-------------------------------- */

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

        if (input) {

            input.files = files;
        }
    });
}



/* --------------------------------
INIT
-------------------------------- */

document.addEventListener("DOMContentLoaded", () => {

    setupDragDrop();

});
