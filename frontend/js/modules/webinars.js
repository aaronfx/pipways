const WebinarsPage = {
    async render(container) {
        container.innerHTML = '<div class="page-header"><h1>Upcoming Webinars</h1></div>';

        try {
            const webinars = await API.getWebinars(true);

            if (webinars.length === 0) {
                container.innerHTML += '<p>No upcoming webinars scheduled.</p>';
                return;
            }

            let html = '<div class="webinars-list">';
            webinars.forEach(w => {
                const date = new Date(w.scheduled_at);
                html += `
                    <div class="webinar-card" style="display: flex; gap: 1.5rem; background: white; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                        <div class="webinar-date" style="text-align: center; min-width: 80px; background: #f9fafb; padding: 1rem; border-radius: 0.375rem;">
                            <span class="day" style="display: block; font-size: 2rem; font-weight: 700; color: #3b82f6;">${date.getDate()}</span>
                            <span class="month" style="text-transform: uppercase; font-size: 0.875rem; color: #6b7280;">${date.toLocaleString('default', {month: 'short'})}</span>
                        </div>
                        <div class="webinar-info" style="flex: 1;">
                            <h3>${UI.escapeHtml(w.title)}</h3>
                            <p>${UI.escapeHtml(w.description)}</p>
                            <div class="webinar-meta" style="margin-top: 0.5rem; font-size: 0.875rem; color: #6b7280;">
                                <span style="margin-right: 1rem;">👤 ${w.presenter}</span>
                                <span>⏱ ${w.duration_minutes} mins</span>
                            </div>
                            ${w.meeting_link ? `<a href="${w.meeting_link}" target="_blank" class="btn btn-primary" style="margin-top: 1rem; display: inline-block;">Join Meeting</a>` : ''}
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            container.innerHTML += html;
        } catch (error) {
            container.innerHTML += '<p>Failed to load webinars</p>';
        }
    }
};