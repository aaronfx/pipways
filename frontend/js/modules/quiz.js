const QuizModule = {
    async render(courseId, quizId) {
        try {
            const quiz = await API.request(`/courses/${courseId}/quizzes/${quizId}`);

            const app = document.getElementById('app');
            app.innerHTML = `
                <div class="quiz-container">
                    <h2>${quiz.title}</h2>
                    <form id="quizForm" onsubmit="QuizModule.submit(event, ${courseId}, ${quizId})">
                        ${quiz.questions.map((q, idx) => `
                            <div class="question-card">
                                <h4>Question ${idx + 1}</h4>
                                <p>${q.question}</p>
                                <div class="options">
                                    ${q.options.map((opt, optIdx) => `
                                        <label class="option">
                                            <input type="radio" name="q${idx}" value="${opt}" required>
                                            <span>${opt}</span>
                                        </label>
                                    `).join('')}
                                </div>
                            </div>
                        `).join('')}
                        <button type="submit" class="btn btn-primary btn-lg">Submit Quiz</button>
                    </form>
                </div>
            `;
        } catch (e) {
            UI.showToast('Failed to load quiz', 'error');
        }
    },

    async submit(e, courseId, quizId) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const answers = {};

        formData.forEach((value, key) => {
            answers[key.replace('q', '')] = value;
        });

        try {
            const result = await API.submitQuiz(courseId, quizId, answers);
            this.showResults(result);
        } catch (error) {
            UI.showToast(error.message, 'error');
        }
    },

    showResults(result) {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="quiz-results ${result.passed ? 'passed' : 'failed'}">
                <h2>${result.passed ? '🎉 Congratulations!' : '❌ Quiz Failed'}</h2>
                <div class="score-circle">
                    <span class="score">${result.score}%</span>
                    <small>Passing: ${result.passing_score}%</small>
                </div>

                <div class="results-breakdown">
                    ${result.results.map((r, idx) => `
                        <div class="result-item ${r.is_correct ? 'correct' : 'incorrect'}">
                            <h4>Q${idx + 1}: ${r.is_correct ? '✅' : '❌'}</h4>
                            <p>${r.question}</p>
                            ${!r.is_correct ? `<p class="correct-answer">Correct: ${r.correct_answer}</p>` : ''}
                        </div>
                    `).join('')}
                </div>

                <button onclick="Router.go('#/courses')" class="btn btn-primary">Back to Courses</button>
            </div>
        `;
    }
};