/**
 * dashboard.js — PATCHED METHODS
 *
 * Drop-in replacements for the three broken methods in DashboardController.
 * Apply by replacing the corresponding methods in dashboard.js.
 *
 * Changes:
 *   loadAdminData()   — now delegates to AdminPage.render() instead of rendering
 *                       its own basic 3-card grid. Falls back gracefully if
 *                       AdminPage is not loaded yet.
 *
 *   renderAdminMenu() — added is_superuser check (was missing, inconsistent with
 *                       the constructor check).
 *
 *   api (local client) — removed the duplicate lowercase `api` const at the
 *                        bottom of dashboard.js. Use the global `API` (from
 *                        api.js) everywhere. All internal calls updated below.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * STEP 1: In DashboardController, replace renderAdminMenu() with:
 */

// renderAdminMenu() ─────────────────────────────────────────────────────────
// FIX: added is_superuser to match admin.py guard and constructor logic.
renderAdminMenu_PATCHED() {
    const isAdmin = this.user && (
        this.user.is_admin     === true   // was already here
        || this.user.role      === 'admin'  // was already here
        || this.user.is_superuser === true  // ← WAS MISSING
    );

    const adminMenu = document.getElementById('admin-menu-container');
    if (adminMenu) {
        adminMenu.style.display = isAdmin ? 'block' : 'none';
    }
}

/*
 * STEP 2: Replace loadAdminData() with:
 */

// loadAdminData() ────────────────────────────────────────────────────────────
// FIX: delegates to AdminPage module instead of rendering a basic 3-card grid.
async loadAdminData_PATCHED() {
    const container = document.getElementById('admin-container');
    if (!container) return;

    // Guard: verify admin on the client side before hitting the server
    const isAdmin = this.user && (
        this.user.is_admin === true
        || this.user.role === 'admin'
        || this.user.is_superuser === true
    );

    if (!isAdmin) {
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center py-20 text-center">
                <div class="w-16 h-16 rounded-full bg-red-900/30 flex items-center justify-center mb-4">
                    <i class="fas fa-lock text-red-400 text-2xl"></i>
                </div>
                <h3 class="text-xl font-bold text-white mb-2">Access Denied</h3>
                <p class="text-gray-400 text-sm">Administrator privileges required.</p>
            </div>`;
        return;
    }

    // Delegate to the AdminPage module (admin.js must be loaded in the HTML)
    if (typeof AdminPage !== 'undefined') {
        await AdminPage.render(container);
        return;
    }

    // Fallback: AdminPage not loaded — show a basic error with the raw stats
    console.warn('[Dashboard] AdminPage module not loaded. Showing basic admin view.');
    container.innerHTML = `
        <div class="bg-yellow-900/20 border border-yellow-700/50 rounded-lg p-4 mb-4 text-sm text-yellow-400">
            <i class="fas fa-exclamation-triangle mr-2"></i>
            Admin module (admin.js) is not loaded. Add it to your HTML before dashboard.js.
        </div>`;

    try {
        const stats = await API.getAdminStats();
        container.innerHTML += `
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                    <div class="text-3xl font-bold text-white mb-1">${stats.total_users ?? 0}</div>
                    <div class="text-sm text-gray-400">Total Users</div>
                </div>
                <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                    <div class="text-3xl font-bold text-white mb-1">${stats.active_signals ?? 0}</div>
                    <div class="text-sm text-gray-400">Active Signals</div>
                </div>
                <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                    <div class="text-3xl font-bold text-white mb-1">${stats.new_today ?? 0}</div>
                    <div class="text-sm text-gray-400">New Today</div>
                </div>
            </div>`;
    } catch (err) {
        container.innerHTML += `
            <div class="text-red-400 p-4 bg-red-900/20 rounded-lg border border-red-800 text-sm">
                Failed to load admin data: ${err.message}
            </div>`;
    }
}

/*
 * STEP 3: In DashboardController.loadDashboardStats(), change all `api.X()`
 *         calls to `API.X()` (uppercase). The duplicate `const api = {...}`
 *         block at the bottom of dashboard.js should be deleted entirely.
 *         api.js sets both  window.API  and  window.api  so existing code
 *         won't break during migration.
 *
 * STEP 4: Ensure the HTML loads scripts in this order:
 *
 *   <script src="/js/api.js"></script>      ← defines window.API
 *   <script src="/js/admin.js"></script>    ← defines AdminPage
 *   <script src="/js/dashboard.js"></script> ← DashboardController uses both
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * ROUTER FIX (router.js)
 *
 * Current:   AdminPage.render();           ← no container arg
 * Fixed:     const c = document.getElementById('app');
 *            if (c) AdminPage.render(c);
 * ─────────────────────────────────────────────────────────────────────────────
 */
