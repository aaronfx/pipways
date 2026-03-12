/**
 * Admin Dashboard Module
 * Handles statistics, charts, and overview
 */

const adminDashboard = {
    charts: {},
    
    async loadStats() {
        try {
            const stats = await api.get('/api/admin/dashboard/stats');
            
            // Update stat cards
            this.updateStat('stat-total-users', stats.total_users || 0);
            this.updateStat('stat-active-signals', stats.active_signals || 0);
            this.updateStat('stat-total-courses', stats.total_courses || 0);
            this.updateStat('stat-upcoming-webinars', stats.upcoming_webinars || 0);
            this.updateStat('stat-premium-users', stats.vip_users || 0);
            this.updateStat('stat-blog-posts', stats.published_posts || 0);
            this.updateStat('stat-published-count', stats.published_posts || 0);
            this.updateStat('stat-premium-courses', stats.premium_courses || '-');
            
            // Initialize charts
            this.initCharts();
            
            // Load recent activity
            this.loadActivity();
            
        } catch (error) {
            console.error('Failed to load dashboard stats:', error);
            ui.showToast('Failed to load dashboard data', 'error');
        }
    },
    
    updateStat(elementId, value) {
        const element = document.getElementById(elementId);
        if(element) {
            element.textContent = value;
        }
    },
    
    initCharts() {
        // User Growth Chart (Canvas)
        const userCtx = document.getElementById('userGrowthChart');
        if(userCtx) {
            this.drawLineChart(userCtx, [12, 19, 25, 32, 45, 58, 72], 'Users');
        }
        
        // Signal Performance Chart
        const signalCtx = document.getElementById('signalPerformanceChart');
        if(signalCtx) {
            this.drawBarChart(signalCtx, [65, 78, 90, 81, 96, 85, 92], 'Win Rate %');
        }
    },
    
    drawLineChart(canvas, data, label) {
        const ctx = canvas.getContext('2d');
        const width = canvas.parentElement.clientWidth;
        const height = 250;
        canvas.width = width;
        canvas.height = height;
        
        ctx.clearRect(0, 0, width, height);
        
        const padding = 40;
        const chartWidth = width - (padding * 2);
        const chartHeight = height - (padding * 2);
        const maxValue = Math.max(...data) * 1.2;
        
        ctx.beginPath();
        ctx.strokeStyle = '#6366f1';
        ctx.lineWidth = 3;
        
        data.forEach((value, index) => {
            const x = padding + (index / (data.length - 1)) * chartWidth;
            const y = height - padding - (value / maxValue) * chartHeight;
            
            if(index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        
        ctx.stroke();
        
        ctx.lineTo(padding + chartWidth, height - padding);
        ctx.lineTo(padding, height - padding);
        ctx.closePath();
        
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, 'rgba(99, 102, 241, 0.2)');
        gradient.addColorStop(1, 'rgba(99, 102, 241, 0)');
        ctx.fillStyle = gradient;
        ctx.fill();
        
        data.forEach((value, index) => {
            const x = padding + (index / (data.length - 1)) * chartWidth;
            const y = height - padding - (value / maxValue) * chartHeight;
            
            ctx.beginPath();
            ctx.fillStyle = '#6366f1';
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
        });
    },
    
    drawBarChart(canvas, data, label) {
        const ctx = canvas.getContext('2d');
        const width = canvas.parentElement.clientWidth;
        const height = 250;
        canvas.width = width;
        canvas.height = height;
        
        ctx.clearRect(0, 0, width, height);
        
        const padding = 40;
        const chartWidth = width - (padding * 2);
        const chartHeight = height - (padding * 2);
        const maxValue = 100;
        const barWidth = (chartWidth / data.length) * 0.6;
        const spacing = (chartWidth / data.length) * 0.4;
        
        data.forEach((value, index) => {
            const x = padding + (index * (barWidth + spacing)) + (spacing / 2);
            const barHeight = (value / maxValue) * chartHeight;
            const y = height - padding - barHeight;
            
            ctx.fillStyle = '#10b981';
            ctx.fillRect(x, y, barWidth, barHeight);
        });
    },
    
    async loadActivity() {
        const feed = document.getElementById('admin-activity-feed');
        if(!feed) return;
        
        const activities = [
            { type: 'user', message: 'New user registered', time: '2 minutes ago', icon: 'user-plus' },
            { type: 'signal', message: 'EURUSD Buy signal created', time: '15 minutes ago', icon: 'satellite-dish' },
            { type: 'blog', message: 'New blog post published', time: '1 hour ago', icon: 'newspaper' },
            { type: 'course', message: 'Course "Advanced Forex" updated', time: '3 hours ago', icon: 'graduation-cap' }
        ];
        
        feed.innerHTML = activities.map(act => `
            <div class="activity-item">
                <div class="activity-icon ${act.type === 'user' ? 'success' : act.type === 'signal' ? 'primary' : 'warning'}">
                    <i class="fas fa-${act.icon}"></i>
                </div>
                <div class="activity-content">
                    <p>${act.message}</p>
                    <small>${act.time}</small>
                </div>
            </div>
        `).join('');
    },
    
    clearActivity() {
        const feed = document.getElementById('admin-activity-feed');
        if(feed) feed.innerHTML = '';
    },
    
    updateChartPeriod(days) {
        this.initCharts();
    },
    
    refreshAllData() {
        ui.showLoading('Refreshing data...');
        this.loadStats();
        setTimeout(() => ui.hideLoading(), 1000);
    }
};
