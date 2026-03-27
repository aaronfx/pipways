# Add to subscriptions.py FEATURE_CONFIG

FEATURE_CONFIG = {
    # ... existing features ...
    
    "signals_visible": {
        "free": 3,      # Free users see 3 signals
        "pro": None     # Pro users see all signals
    },
    "signals_detailed_analysis": {
        "free": 1,      # Free users get 1 detailed analysis per day
        "pro": None     # Pro users get unlimited
    },
    "signals_chart_access": {
        "free": False,  # Free users can't access full charts
        "pro": True     # Pro users get full chart access
    }
}

# Add to usage.js
window.PipwaysUsage = {
    // ... existing code ...
    
    checkSignalsAccess: async function() {
        const user = Store.getUser();
        if (!user) return false;
        
        if (user.subscription_tier === 'free') {
            const usage = await this.checkUsage('signals_visible', 1);
            if (!usage.allowed) {
                this.showUpgradeModal('signals');
                return false;
            }
        }
        return true;
    },
    
    checkChartAccess: async function() {
        const user = Store.getUser();
        if (!user) return false;
        
        if (user.subscription_tier === 'free') {
            const hasAccess = await this.getFeatureLimit('signals_chart_access');
            if (!hasAccess) {
                this.showUpgradeModal('chart_analysis', {
                    title: 'Full Chart Analysis',
                    message: 'Upgrade to Pro to access detailed chart analysis and TradingView integration.'
                });
                return false;
            }
        }
        return true;
    }
};
