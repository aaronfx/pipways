/**
 * Admin Settings Module
 */

const adminSettings = {
    async load() {
        try {
            const settings = await api.get('/api/admin/settings');
            
            document.getElementById('setting-site-name').value = settings.site_name || '';
            document.getElementById('setting-contact-email').value = settings.contact_email || '';
            document.getElementById('setting-telegram-free').value = settings.telegram_free_link || '';
            document.getElementById('setting-telegram-vip').value = settings.telegram_vip_link || '';
            document.getElementById('setting-vip-price').value = settings.vip_price || '';
            document.getElementById('setting-vip-currency').value = settings.vip_price_currency || 'USD';
            
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    },
    
    async save(e) {
        e.preventDefault();
        
        const data = {
            site_name: document.getElementById('setting-site-name').value,
            contact_email: document.getElementById('setting-contact-email').value,
            telegram_free_link: document.getElementById('setting-telegram-free').value,
            telegram_vip_link: document.getElementById('setting-telegram-vip').value,
            vip_price: parseFloat(document.getElementById('setting-vip-price').value) || null,
            vip_price_currency: document.getElementById('setting-vip-currency').value
        };
        
        try {
            ui.showLoading('Saving settings...');
            await api.put('/api/admin/settings', data);
            ui.showToast('Settings saved successfully', 'success');
        } catch (error) {
            ui.showToast('Error saving settings: ' + error.message, 'error');
        } finally {
            ui.hideLoading();
        }
    }
};
