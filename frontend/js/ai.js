async analyzePerformanceVision() {

    if (!this.currentPerformanceImage) {
        ui.showToast('Please upload a trading statement image', 'error');
        return;
    }

    ui.showLoading('Analyzing trading performance...');

    try {

        const balance =
            parseFloat(document.getElementById('vision-account-balance')?.value) || 0;

        const period =
            parseInt(document.getElementById('vision-trading-period')?.value) || 30;

        const response = await api.post('/api/ai/analyze-vision', {

            image: this.currentPerformanceImage,
            account_balance: balance,
            trading_period_days: period

        });

        this.displayPerformanceResults(response);

    } catch (error) {

        console.error('Performance analysis error:', error);

        const errorMsg =
            error?.message ||
            (typeof error === 'string' ? error : 'Server error');

        ui.showToast('Analysis failed: ' + errorMsg, 'error');

    } finally {

        ui.hideLoading();

    }
}
