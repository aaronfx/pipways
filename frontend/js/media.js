/**
 * Media Upload Module
 */
const media = {
    async loadMedia(container) {
        if (!auth.requireAdmin()) return;

        container.innerHTML = '<div class="loading">Loading media...</div>';

        try {
            const files = await api.get('/media');

            const html = `
                <div class="page-header">
                    <h1>Media Library</h1>
                    <div>
                        <input type="file" id="media-upload" onchange="media.handleUpload(this)" style="display:none;">
                        <button class="primary" onclick="document.getElementById('media-upload').click()">Upload File</button>
                    </div>
                </div>
                <div class="media-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem;">
                    ${files.length === 0 ? '<p>No media files.</p>' : 
                      files.map(f => this.renderMediaCard(f)).join('')}
                </div>
            `;

            container.innerHTML = html;
        } catch (error) {
            container.innerHTML = `<div class="error">Failed to load media: ${error.message}</div>`;
        }
    },

    renderMediaCard(file) {
        const isImage = file.file_type && file.file_type.startsWith('image/');

        return `
            <div class="card" style="text-align: center;">
                ${isImage ? 
                    `<img src="${file.url}" style="width: 100%; height: 150px; object-fit: cover; border-radius: 0.375rem; margin-bottom: 0.5rem;">` :
                    `<div style="width: 100%; height: 150px; background: var(--bg); display: flex; align-items: center; justify-content: center; border-radius: 0.375rem; margin-bottom: 0.5rem;">📄</div>`
                }
                <div style="font-size: 0.875rem; word-break: break-all;">${file.filename}</div>
                <small style="color: var(--text-light);">${(file.size_bytes / 1024).toFixed(1)} KB</small>
                <div style="margin-top: 0.5rem;">
                    <button class="secondary" onclick="media.deleteFile(${file.id})">Delete</button>
                </div>
            </div>
        `;
    },

    async handleUpload(input) {
        const file = input.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/media/upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: formData
            });

            if (!response.ok) throw new Error('Upload failed');

            ui.showToast('File uploaded successfully', 'success');
            this.loadMedia(document.getElementById('main-content'));
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    },

    async deleteFile(fileId) {
        if (!confirm('Delete this file?')) return;
        try {
            await api.delete(`/media/${fileId}`);
            ui.showToast('File deleted', 'success');
            this.loadMedia(document.getElementById('main-content'));
        } catch (error) {
            ui.showToast(error.message, 'error');
        }
    }
};
