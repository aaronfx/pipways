
export function showLoading(show, message = 'Loading...') {
    let spinner = document.getElementById('global-loading');

    if (show) {
        if (!spinner) {
            spinner = document.createElement('div');
            spinner.id = 'global-loading';
            spinner.innerHTML = `
                <div class="spinner-overlay">
                    <div class="spinner"></div>
                    <p class="spinner-text">${message}</p>
                </div>
            `;
            document.body.appendChild(spinner);
        } else {
            spinner.querySelector('.spinner-text').textContent = message;
            spinner.style.display = 'flex';
        }
    } else if (spinner) {
        spinner.style.display = 'none';
    }
}
