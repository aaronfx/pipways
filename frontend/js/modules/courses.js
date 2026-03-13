const CoursesPage = {
    async render() {
        document.getElementById('app').innerHTML = `
            <div class="page-header">
                <h1>📚 Trading Courses</h1>
                <p>Master the markets with our comprehensive curriculum</p>
            </div>
            <div class="card">
                <div class="card-body">
                    <p class="text-muted">Course content loading...</p>
                    <p>Browse available courses and track your progress.</p>
                    <a href="#/dashboard" class="btn btn-primary">Back to Dashboard</a>
                </div>
            </div>
        `;
    }
};
