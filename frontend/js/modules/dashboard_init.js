// Dashboard Initialization
// Instantiate the DashboardController after all prototype methods are loaded.
// This file must be loaded AFTER dashboard_core.js and all dashboard_*.js module files.

const dashboard = new DashboardController();

// Expose on window so external module scripts can access them.
window.dashboard = dashboard;

// API shim: provide a simple API object that delegates to dashboard.apiRequest
const API = {
    request(endpoint, opts = {}) {
        return dashboard.apiRequest(endpoint, opts);
    }
};
