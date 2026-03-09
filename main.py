<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pipways - Professional Trading Platform v3.1</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --telegram: #0088cc;
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --bg-hover: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border: #334155;
            --premium: #fbbf24;
            --success: #10b981;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
            overflow-x: hidden;
        }

        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(15, 23, 42, 0.9);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            flex-direction: column;
            gap: 20px;
        }

        .loading-overlay.show { display: flex; }
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid var(--border);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        .auth-wall {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, var(--bg-dark) 0%, var(--bg-card) 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            padding: 20px;
        }

        .auth-container {
            width: 100%;
            max-width: 420px;
            background: var(--bg-card);
            border-radius: 16px;
            padding: 40px;
            border: 1px solid var(--border);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }

        .auth-logo {
            font-size: 28px;
            font-weight: 700;
            text-align: center;
            margin-bottom: 8px;
            color: var(--primary);
        }

        .form-group { margin-bottom: 20px; }
        .form-label {
            display: block;
            margin-bottom: 8px;
            color: var(--text-secondary);
            font-size: 14px;
            font-weight: 500;
        }

        .form-input, .form-select {
            width: 100%;
            padding: 12px 16px;
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 16px;
            transition: all 0.3s;
        }

        .form-input:focus, .form-select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .btn {
            width: 100%;
            padding: 12px 24px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .btn:hover { background: var(--primary-dark); transform: translateY(-1px); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .btn-secondary { background: transparent; color: var(--text-secondary); border: 1px solid var(--border); margin-top: 12px; }
        .btn-danger { background: var(--danger); }
        .btn-success { background: var(--success); }
        .btn-telegram { background: var(--telegram); }
        .btn-premium { background: var(--premium); color: var(--bg-dark); }
        .btn-sm { padding: 8px 16px; font-size: 14px; width: auto; }

        .sidebar {
            position: fixed;
            left: 0;
            top: 0;
            width: 280px;
            height: 100vh;
            background: var(--bg-card);
            border-right: 1px solid var(--border);
            padding: 20px 0;
            overflow-y: auto;
            z-index: 100;
            transition: transform 0.3s ease;
            display: flex;
            flex-direction: column;
        }

        .sidebar-header {
            padding: 0 20px 20px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 20px;
            flex-shrink: 0;
        }

        .sidebar-logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 24px;
            font-weight: 700;
        }

        .nav-menu {
            list-style: none;
            padding: 0 10px;
            flex: 1;
            overflow-y: auto;
        }

        .nav-item { margin-bottom: 5px; }

        .nav-link {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            color: var(--text-secondary);
            text-decoration: none;
            border-radius: 10px;
            transition: all 0.3s;
            cursor: pointer;
            position: relative;
            background: none;
            border: none;
            width: 100%;
            font-size: 16px;
            text-align: left;
        }

        .nav-link:hover, .nav-link.active {
            background: var(--primary);
            color: white;
        }

        .premium-badge {
            position: absolute;
            right: 10px;
            background: var(--premium);
            color: var(--bg-dark);
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 10px;
            font-weight: 700;
        }

        .sidebar-footer {
            padding: 20px;
            border-top: 1px solid var(--border);
            background: var(--bg-card);
            margin-top: auto;
            flex-shrink: 0;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 15px;
        }

        .user-avatar {
            width: 40px;
            height: 40px;
            background: var(--primary);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
        }

        .admin-badge {
            display: inline-block;
            padding: 2px 8px;
            background: var(--warning);
            color: var(--bg-dark);
            border-radius: 12px;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            margin-top: 4px;
        }

        .main-content {
            margin-left: 280px;
            min-height: 100vh;
            transition: margin-left 0.3s ease;
        }

        .section {
            display: none;
            animation: fadeIn 0.3s ease;
        }

        .section.active { display: block; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .page-header {
            padding: 40px;
            background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-dark) 100%);
            border-bottom: 1px solid var(--border);
        }

        .page-header h2 {
            font-size: 36px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
            padding: 30px;
        }

        .stat-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid var(--border);
            transition: all 0.3s;
        }

        .stat-card:hover { transform: translateY(-2px); border-color: var(--primary); }

        .stat-icon {
            width: 48px;
            height: 48px;
            background: rgba(99, 102, 241, 0.1);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: var(--primary);
            margin-bottom: 16px;
        }

        .stat-value { font-size: 32px; font-weight: 700; margin-bottom: 4px; }
        .stat-label { color: var(--text-secondary); font-size: 14px; }

        .content-grid {
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 24px;
        }

        .content-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid var(--border);
            transition: all 0.3s;
        }

        .content-card:hover {
            transform: translateY(-5px);
            border-color: var(--primary);
        }

        .data-table-container {
            background: var(--bg-card);
            border-radius: 16px;
            border: 1px solid var(--border);
            overflow: hidden;
            margin: 0 30px 30px;
        }

        .data-table-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }

        .search-box {
            position: relative;
            flex: 1;
            max-width: 300px;
        }

        .search-box input {
            width: 100%;
            padding: 10px 16px 10px 40px;
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 14px;
        }

        .search-box i {
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 16px 24px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }

        th {
            background: var(--bg-dark);
            font-weight: 600;
            color: var(--text-secondary);
            font-size: 12px;
            text-transform: uppercase;
        }

        .action-btns { display: flex; gap: 8px; }

        .action-btn {
            width: 32px;
            height: 32px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--bg-hover);
            color: var(--text-secondary);
            transition: all 0.2s;
        }

        .action-btn:hover { background: var(--primary); color: white; }
        .action-btn.delete:hover { background: var(--danger); }

        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            z-index: 2000;
            align-items: center;
            justify-content: center;
            padding: 20px;
            overflow-y: auto;
        }

        .modal.show { display: flex; }

        .modal-content {
            background: var(--bg-card);
            border-radius: 16px;
            width: 100%;
            max-width: 800px;
            max-height: 90vh;
            overflow-y: auto;
            border: 1px solid var(--border);
        }

        .modal-header {
            padding: 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            background: var(--bg-card);
            z-index: 10;
        }

        .modal-close {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 24px;
            cursor: pointer;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 6px;
        }

        .modal-close:hover { background: var(--bg-hover); color: var(--text-primary); }

        .modal-body { padding: 24px; }
        .modal-footer {
            padding: 20px 24px;
            border-top: 1px solid var(--border);
            display: flex;
            gap: 12px;
            justify-content: flex-end;
            position: sticky;
            bottom: 0;
            background: var(--bg-card);
        }

        .editor-toolbar {
            padding: 10px;
            background: var(--bg-hover);
            border: 1px solid var(--border);
            border-bottom: none;
            border-radius: 8px 8px 0 0;
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .editor-btn {
            padding: 8px 12px;
            background: var(--bg-dark);
            border: 1px solid var(--border);
            color: var(--text-secondary);
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .editor-btn:hover, .editor-btn.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }

        .editor-content {
            padding: 16px;
            min-height: 300px;
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 0 0 8px 8px;
            outline: none;
            color: var(--text-primary);
            line-height: 1.6;
        }

        .editor-content img { max-width: 100%; border-radius: 8px; margin: 10px 0; }
        .editor-content iframe { max-width: 100%; border-radius: 8px; margin: 10px 0; }

        .admin-tabs {
            display: flex;
            gap: 10px;
            margin: 0 30px 30px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 20px;
            flex-wrap: wrap;
        }

        .admin-tab {
            padding: 12px 24px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 500;
        }

        .admin-tab:hover { background: var(--bg-hover); color: var(--text-primary); }
        .admin-tab.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }

        .admin-panel { display: none; }
        .admin-panel.active { display: block; }

        .analyzer-container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 30px;
        }

        .score-display {
            text-align: center;
            padding: 40px;
            background: var(--bg-card);
            border-radius: 20px;
            border: 2px solid var(--border);
            margin-bottom: 30px;
        }

        .score-circle {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: conic-gradient(var(--primary) calc(var(--score) * 1%), var(--bg-hover) 0);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            position: relative;
        }

        .score-circle::before {
            content: '';
            position: absolute;
            width: 120px;
            height: 120px;
            background: var(--bg-card);
            border-radius: 50%;
        }

        .score-value {
            position: relative;
            font-size: 48px;
            font-weight: 700;
            color: var(--primary);
        }

        .analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .analysis-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid var(--border);
        }

        .metric-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
        }

        .improvement-list {
            list-style: none;
        }

        .improvement-list li {
            padding: 10px 0;
            padding-left: 28px;
            position: relative;
        }

        .improvement-list li::before {
            content: '→';
            position: absolute;
            left: 0;
            color: var(--primary);
            font-weight: bold;
        }

        .trade-entry-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }

        .trade-list {
            background: var(--bg-card);
            border-radius: 12px;
            border: 1px solid var(--border);
            max-height: 400px;
            overflow-y: auto;
        }

        .trade-item {
            padding: 16px;
            border-bottom: 1px solid var(--border);
            display: grid;
            grid-template-columns: 1fr auto auto auto;
            gap: 12px;
            align-items: center;
        }

        .trade-pnl.positive { color: var(--success); }
        .trade-pnl.negative { color: var(--danger); }

        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-published { background: rgba(16, 185, 129, 0.2); color: var(--success); }
        .status-draft { background: rgba(148, 163, 184, 0.2); color: var(--text-secondary); }
        .status-scheduled { background: rgba(251, 191, 36, 0.2); color: var(--premium); }

        .toast {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 24px;
            background: var(--danger);
            color: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            display: none;
            align-items: center;
            gap: 12px;
            z-index: 10000;
            animation: slideInRight 0.3s ease;
        }

        .toast.show { display: flex; }
        .toast.success { background: var(--success); }

        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
                z-index: 101;
            }

            .sidebar.open { transform: translateX(0); }

            .main-content {
                margin-left: 0;
                padding-top: 60px;
            }

            .mobile-header {
                display: flex !important;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                height: 60px;
                background: var(--bg-card);
                border-bottom: 1px solid var(--border);
                z-index: 1000;
                align-items: center;
                justify-content: space-between;
                padding: 0 20px;
            }

            .stats-grid { grid-template-columns: 1fr; padding: 15px; }
            .data-table-container { margin: 0 15px 15px; }
            .admin-tabs { margin: 0 15px 15px; }
        }

        .hidden { display: none !important; }

        .upload-area {
            border: 2px dashed var(--border);
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }

        .upload-area:hover {
            border-color: var(--primary);
            background: rgba(99, 102, 241, 0.05);
        }
    </style>
</head>
<body>
    <!-- Loading Overlay -->
    <div class="loading-overlay" id="loading-overlay">
        <div class="spinner"></div>
        <p>Processing...</p>
    </div>

    <!-- Toast Notification -->
    <div class="toast" id="toast">
        <i class="fas fa-exclamation-circle"></i>
        <span id="toast-message">Error message</span>
    </div>

    <!-- Auth Wall -->
    <div class="auth-wall" id="auth-wall">
        <div class="auth-container">
            <div class="auth-logo">
                <i class="fas fa-chart-line"></i> Pipways v3.1
            </div>
            <p style="text-align: center; color: var(--text-secondary); margin-bottom: 32px;">Professional Trading Platform</p>

            <form id="login-form" onsubmit="handleLogin(event)">
                <div class="form-group">
                    <label class="form-label">Email</label>
                    <input type="email" name="email" class="form-input" required placeholder="admin@pipways.com">
                </div>
                <div class="form-group">
                    <label class="form-label">Password</label>
                    <input type="password" name="password" class="form-input" required placeholder="••••••••">
                </div>
                <div id="login-error" style="color: var(--danger); margin-bottom: 16px; display: none;"></div>
                <button type="submit" class="btn" id="login-btn">
                    <span>Login</span>
                </button>
                <button type="button" class="btn btn-secondary" onclick="showRegister()">
                    Create Account
                </button>
            </form>

            <form id="register-form" class="hidden" onsubmit="handleRegister(event)">
                <div class="form-group">
                    <label class="form-label">Full Name</label>
                    <input type="text" name="full_name" class="form-input" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Email</label>
                    <input type="email" name="email" class="form-input" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Password</label>
                    <input type="password" name="password" class="form-input" required minlength="8">
                    <small style="color: var(--text-secondary); display: block; margin-top: 5px;">
                        Min 8 chars, uppercase, lowercase, number, special char
                    </small>
                </div>
                <div id="register-error" style="color: var(--danger); margin-bottom: 16px; display: none;"></div>
                <button type="submit" class="btn" id="register-btn">
                    <span>Create Account</span>
                </button>
                <button type="button" class="btn btn-secondary" onclick="showLogin()">
                    Back to Login
                </button>
            </form>
        </div>
    </div>

    <!-- Main App -->
    <div class="main-app hidden" id="main-app">
        <!-- Mobile Header -->
        <div class="mobile-header" style="display: none;">
            <div style="display: flex; align-items: center; gap: 10px; font-size: 20px; font-weight: 700;">
                <i class="fas fa-chart-line" style="color: var(--primary);"></i>
                <span>Pipways</span>
            </div>
            <button onclick="toggleSidebar()" style="width: 40px; height: 40px; background: var(--bg-hover); border: none; border-radius: 10px; color: var(--text-primary); font-size: 20px; cursor: pointer;">
                <i class="fas fa-bars"></i>
            </button>
        </div>

        <!-- Sidebar Overlay -->
        <div class="sidebar-overlay" onclick="toggleSidebar()" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.5); z-index: 99;"></div>

        <!-- Sidebar -->
        <aside class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <div class="sidebar-logo">
                    <i class="fas fa-chart-line"></i>
                    <span>Pipways</span>
                </div>
            </div>

            <ul class="nav-menu">
                <li class="nav-item">
                    <button class="nav-link active" onclick="showSection('home', this)">
                        <i class="fas fa-home"></i>
                        <span>Overview</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showSection('telegram', this)">
                        <i class="fab fa-telegram"></i>
                        <span>Telegram Signals</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showSection('signals', this)">
                        <i class="fas fa-satellite-dish"></i>
                        <span>Trading Signals</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showSection('analysis', this)">
                        <i class="fas fa-robot"></i>
                        <span>AI Analysis</span>
                        <span class="premium-badge">PRO</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showSection('performance', this)">
                        <i class="fas fa-chart-pie"></i>
                        <span>Performance AI</span>
                        <span class="premium-badge">NEW</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showSection('mentor', this)">
                        <i class="fas fa-comments"></i>
                        <span>AI Mentor</span>
                        <span class="premium-badge">PRO</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showSection('courses', this)">
                        <i class="fas fa-graduation-cap"></i>
                        <span>Courses</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showSection('webinars', this)">
                        <i class="fas fa-video"></i>
                        <span>Webinars</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showSection('blog', this)">
                        <i class="fas fa-newspaper"></i>
                        <span>Blog</span>
                    </button>
                </li>
                <li class="nav-item hidden" id="admin-nav-item">
                    <button class="nav-link" onclick="showSection('admin', this)" style="color: var(--warning);">
                        <i class="fas fa-cog"></i>
                        <span>Admin Dashboard</span>
                    </button>
                </li>
            </ul>

            <div class="sidebar-footer">
                <div class="user-info">
                    <div class="user-avatar" id="user-avatar">A</div>
                    <div>
                        <div style="font-weight: 600;" id="user-name">Admin User</div>
                        <div style="font-size: 12px; color: var(--text-secondary);" id="user-email">admin@pipways.com</div>
                        <span class="admin-badge hidden" id="admin-badge">ADMIN</span>
                    </div>
                </div>
                <button class="btn btn-danger" onclick="logout()" style="width: 100%;">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </button>
            </div>
        </aside>

        <!-- Main Content -->
        <main class="main-content">
            <!-- Home Section -->
            <div class="section active" id="home-section">
                <div class="page-header">
                    <h2><i class="fas fa-home"></i> Dashboard Overview</h2>
                    <p>Welcome back to your professional trading environment</p>
                </div>
                <div class="content-grid">
                    <div class="content-card">
                        <h3><i class="fas fa-signal" style="color: var(--primary);"></i> Latest Signals</h3>
                        <p>View the most recent trading signals generated by our AI and expert analysts.</p>
                        <button class="btn btn-sm" onclick="showSection('signals', document.querySelectorAll('.nav-link')[2])" style="margin-top: 12px;">View Signals</button>
                    </div>
                    <div class="content-card">
                        <h3><i class="fas fa-chart-pie" style="color: var(--secondary);"></i> Performance Analysis</h3>
                        <p>Upload your trading history for comprehensive AI-powered performance evaluation.</p>
                        <button class="btn btn-sm btn-success" onclick="showSection('performance', document.querySelectorAll('.nav-link')[4])" style="margin-top: 12px;">Analyze Now</button>
                    </div>
                    <div class="content-card">
                        <h3><i class="fas fa-robot" style="color: var(--warning);"></i> AI Chart Analysis</h3>
                        <p>Get instant technical analysis on your chart screenshots.</p>
                        <button class="btn btn-sm" onclick="showSection('analysis', document.querySelectorAll('.nav-link')[3])" style="margin-top: 12px; background: var(--warning); color: var(--bg-dark);">Analyze Chart</button>
                    </div>
                </div>
            </div>

            <!-- Performance Analyzer Section -->
            <div class="section" id="performance-section">
                <div class="page-header">
                    <h2><i class="fas fa-chart-pie" style="color: var(--secondary);"></i> AI Performance Analyzer</h2>
                    <p>Get professional trading performance evaluation and improvement strategies</p>
                </div>
                
                <div class="analyzer-container">
                    <div class="content-card" style="margin-bottom: 30px;">
                        <h3 style="margin-bottom: 20px;">Select Input Method</h3>
                        <div style="display: flex; gap: 12px; margin-bottom: 20px;">
                            <button class="btn btn-sm" onclick="showTradeInput('manual')" id="btn-manual" style="background: var(--primary);">Manual Entry</button>
                            <button class="btn btn-sm btn-secondary" onclick="showTradeInput('csv')" id="btn-csv">Upload CSV</button>
                        </div>

                        <div id="manual-input">
                            <div class="trade-entry-grid">
                                <div class="form-group">
                                    <label class="form-label">Pair (e.g., EURUSD)</label>
                                    <input type="text" id="trade-pair" class="form-input" placeholder="EURUSD">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Direction</label>
                                    <select id="trade-direction" class="form-input">
                                        <option value="buy">BUY</option>
                                        <option value="sell">SELL</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Entry Price</label>
                                    <input type="number" id="trade-entry" class="form-input" step="0.00001" placeholder="1.0850">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Exit Price</label>
                                    <input type="number" id="trade-exit" class="form-input" step="0.00001" placeholder="1.0900">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Lot Size</label>
                                    <input type="number" id="trade-lots" class="form-input" step="0.01" placeholder="0.1">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Pips (+/-)</label>
                                    <input type="number" id="trade-pips" class="form-input" step="0.1" placeholder="+50">
                                </div>
                                <div class="form-group" style="grid-column: 1 / -1;">
                                    <label class="form-label">Notes (Optional)</label>
                                    <input type="text" id="trade-notes" class="form-input" placeholder="Breakout trade, FOMC news...">
                                </div>
                            </div>
                            <button class="btn" onclick="addTrade()" style="width: auto;">
                                <i class="fas fa-plus"></i> Add Trade
                            </button>
                        </div>

                        <div id="csv-input" class="hidden">
                            <div class="upload-area" onclick="document.getElementById('csv-file').click()">
                                <i class="fas fa-file-csv" style="font-size: 48px; color: var(--primary); margin-bottom: 16px;"></i>
                                <h3>Upload Trading History CSV</h3>
                                <p style="color: var(--text-secondary); margin-top: 8px;">Format: Date, Pair, Direction, Entry, Exit, Lots, Pips, Notes</p>
                                <input type="file" id="csv-file" class="hidden" accept=".csv" onchange="handleCSVUpload(this)">
                            </div>
                        </div>
                    </div>

                    <div class="content-card hidden" id="trades-list-card" style="margin-bottom: 30px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                            <h3>Trades (<span id="trade-count">0</span>)</h3>
                            <button class="btn btn-sm btn-danger" onclick="clearTrades()">Clear All</button>
                        </div>
                        <div class="trade-list" id="trades-container"></div>
                        <div style="margin-top: 20px; display: flex; gap: 12px; align-items: center;">
                            <div class="form-group" style="flex: 1; margin: 0;">
                                <label class="form-label">Account Balance (Optional)</label>
                                <input type="number" id="account-balance" class="form-input" placeholder="10000">
                            </div>
                            <button class="btn btn-success" onclick="analyzePerformance()" style="margin-top: 20px;">
                                <i class="fas fa-brain"></i> Analyze Performance
                            </button>
                        </div>
                    </div>

                    <div id="analysis-results" class="hidden">
                        <div class="score-display">
                            <div class="score-circle" id="score-circle" style="--score: 0;">
                                <div class="score-value" id="trader-score">0</div>
                            </div>
                            <h2>Trading Performance Score</h2>
                            <p style="color: var(--text-secondary); margin-top: 8px;" id="score-interpretation">Analysis complete</p>
                        </div>

                        <div class="analysis-grid">
                            <div class="analysis-card">
                                <h3><i class="fas fa-chart-bar" style="color: var(--primary);"></i> Performance Summary</h3>
                                <div id="performance-summary"></div>
                            </div>

                            <div class="analysis-card">
                                <h3><i class="fas fa-exclamation-triangle" style="color: var(--danger);"></i> Key Issues</h3>
                                <ul class="improvement-list" id="top-mistakes"></ul>
                            </div>

                            <div class="analysis-card">
                                <h3><i class="fas fa-check-circle" style="color: var(--success);"></i> Strengths</h3>
                                <ul class="improvement-list" id="strengths-list"></ul>
                            </div>

                            <div class="analysis-card">
                                <h3><i class="fas fa-arrow-up" style="color: var(--warning);"></i> Improvement Plan</h3>
                                <ul class="improvement-list" id="improvement-plan"></ul>
                            </div>
                        </div>

                        <div class="analysis-card" style="margin-top: 20px;">
                            <h3><i class="fas fa-graduation-cap" style="color: var(--premium);"></i> Recommended Courses</h3>
                            <div id="recommended-courses" style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px;"></div>
                        </div>

                        <div class="analysis-card" style="margin-top: 20px; background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%);">
                            <h3><i class="fas fa-user-tie" style="color: var(--primary);"></i> Mentor Advice</h3>
                            <p id="mentor-advice" style="margin-top: 12px; line-height: 1.8; font-style: italic;"></p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Admin Section -->
            <div class="section" id="admin-section">
                <div class="page-header">
                    <h2><i class="fas fa-cog" style="color: var(--warning);"></i> Admin Dashboard</h2>
                    <p>Manage content, users, and platform settings</p>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-icon"><i class="fas fa-users"></i></div>
                        <div class="stat-value" id="stat-total-users">-</div>
                        <div class="stat-label">Total Users</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon" style="background: rgba(16, 185, 129, 0.1); color: var(--success);"><i class="fas fa-signal"></i></div>
                        <div class="stat-value" id="stat-active-signals">-</div>
                        <div class="stat-label">Active Signals</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon" style="background: rgba(251, 191, 36, 0.1); color: var(--premium);"><i class="fas fa-crown"></i></div>
                        <div class="stat-value" id="stat-premium-users">-</div>
                        <div class="stat-label">Premium Users</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon" style="background: rgba(99, 102, 241, 0.1); color: var(--primary);"><i class="fas fa-newspaper"></i></div>
                        <div class="stat-value" id="stat-blog-posts">-</div>
                        <div class="stat-label">Blog Posts</div>
                    </div>
                </div>

                <div class="admin-tabs">
                    <button class="admin-tab active" onclick="showAdminTab('content', this)" id="tab-content">Content</button>
                    <button class="admin-tab" onclick="showAdminTab('users', this)" id="tab-users">Users</button>
                    <button class="admin-tab" onclick="showAdminTab('lms', this)" id="tab-lms">LMS</button>
                    <button class="admin-tab" onclick="showAdminTab('signals', this)" id="tab-signals">Signals</button>
                </div>

                <!-- Content Panel -->
                <div class="admin-panel active" id="panel-content">
                    <div class="data-table-container">
                        <div class="data-table-header">
                            <h3>Blog Posts</h3>
                            <button class="btn btn-sm btn-success" onclick="openBlogModal()">
                                <i class="fas fa-plus"></i> New Post
                            </button>
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th>Title</th>
                                    <th>Status</th>
                                    <th>Category</th>
                                    <th>Date</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="blog-table-body">
                                <tr><td colspan="5" style="text-align: center; padding: 40px;">Loading...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Users Panel -->
                <div class="admin-panel" id="panel-users">
                    <div class="data-table-container">
                        <div class="data-table-header">
                            <h3>User Management</h3>
                            <div class="search-box">
                                <i class="fas fa-search"></i>
                                <input type="text" id="user-search" placeholder="Search users..." oninput="searchUsers()">
                            </div>
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th>User</th>
                                    <th>Role</th>
                                    <th>Subscription</th>
                                    <th>Joined</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="users-table-body">
                                <tr><td colspan="5" style="text-align: center; padding: 40px;">Loading...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- LMS Panel -->
                <div class="admin-panel" id="panel-lms">
                    <div class="content-grid" style="padding: 0 30px;">
                        <div class="content-card">
                            <h3><i class="fas fa-graduation-cap" style="color: var(--warning);"></i> Create Course</h3>
                            <form id="course-form" onsubmit="createCourse(event)">
                                <div class="form-group">
                                    <input type="text" name="title" class="form-input" placeholder="Course Title" required>
                                </div>
                                <div class="form-group">
                                    <textarea name="description" class="form-input" placeholder="Description" rows="3" required></textarea>
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                                    <div class="form-group">
                                        <select name="level" class="form-input">
                                            <option value="beginner">Beginner</option>
                                            <option value="intermediate">Intermediate</option>
                                            <option value="advanced">Advanced</option>
                                        </select>
                                    </div>
                                    <div class="form-group">
                                        <input type="number" name="duration_hours" class="form-input" placeholder="Duration (hours)" step="0.5">
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">
                                        <input type="checkbox" name="is_premium" style="margin-right: 8px;">
                                        Premium Course
                                    </label>
                                </div>
                                <button type="submit" class="btn btn-sm" style="background: var(--warning); color: var(--bg-dark);">Create Course</button>
                            </form>
                        </div>

                        <div class="content-card">
                            <h3><i class="fas fa-video" style="color: var(--secondary);"></i> Create Webinar</h3>
                            <form id="webinar-form" onsubmit="createWebinar(event)">
                                <div class="form-group">
                                    <input type="text" name="title" class="form-input" placeholder="Webinar Title" required>
                                </div>
                                <div class="form-group">
                                    <textarea name="description" class="form-input" placeholder="Description" rows="3" required></textarea>
                                </div>
                                <div class="form-group">
                                    <input type="datetime-local" name="scheduled_at" class="form-input" required>
                                </div>
                                <div class="form-group">
                                    <input type="text" name="meeting_link" class="form-input" placeholder="Zoom/Meet Link">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">
                                        <input type="checkbox" name="is_premium" style="margin-right: 8px;">
                                        Premium Webinar
                                    </label>
                                </div>
                                <button type="submit" class="btn btn-sm btn-success">Create Webinar</button>
                            </form>
                        </div>
                    </div>
                </div>

                <!-- Signals Panel -->
                <div class="admin-panel" id="panel-signals">
                    <div style="max-width: 800px; margin: 0 auto; background: var(--bg-card); padding: 30px; border-radius: 16px; border: 1px solid var(--border);">
                        <h3 style="margin-bottom: 24px;"><i class="fas fa-plus-circle"></i> Create New Signal</h3>
                        <form onsubmit="createSignal(event)">
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                                <div class="form-group">
                                    <label class="form-label">Currency Pair</label>
                                    <input type="text" name="pair" class="form-input" placeholder="EURUSD" required style="text-transform: uppercase;">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Direction</label>
                                    <select name="direction" class="form-input">
                                        <option value="buy">BUY</option>
                                        <option value="sell">SELL</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Entry Price</label>
                                    <input type="number" name="entry_price" class="form-input" step="0.00001" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Stop Loss</label>
                                    <input type="number" name="stop_loss" class="form-input" step="0.00001">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Take Profit</label>
                                    <input type="number" name="take_profit" class="form-input" step="0.00001">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Timeframe</label>
                                    <select name="timeframe" class="form-input">
                                        <option value="1H">1 Hour</option>
                                        <option value="4H">4 Hours</option>
                                        <option value="D1">Daily</option>
                                    </select>
                                </div>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Analysis</label>
                                <textarea name="analysis" class="form-input" rows="4" placeholder="Technical analysis..."></textarea>
                            </div>
                            <button type="submit" class="btn"><i class="fas fa-paper-plane"></i> Publish Signal</button>
                        </form>
                    </div>
                </div>
            </div>

            <!-- Blog Modal with Enhanced Editor -->
            <div class="modal" id="blog-modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Create Blog Post</h3>
                        <button class="modal-close" onclick="closeModal('blog-modal')">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="blog-form">
                            <div class="form-group">
                                <label class="form-label">Title</label>
                                <input type="text" name="title" class="form-input" required>
                            </div>
                            
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                                <div class="form-group">
                                    <label class="form-label">Category</label>
                                    <select name="category" class="form-input">
                                        <option value="Trading">Trading</option>
                                        <option value="Analysis">Analysis</option>
                                        <option value="Psychology">Psychology</option>
                                        <option value="Strategy">Strategy</option>
                                        <option value="News">News</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Status</label>
                                    <select name="status" class="form-input" onchange="toggleSchedule(this.value)">
                                        <option value="draft">Draft</option>
                                        <option value="published">Published</option>
                                        <option value="scheduled">Scheduled</option>
                                    </select>
                                </div>
                            </div>

                            <div class="form-group hidden" id="schedule-field">
                                <label class="form-label">Schedule Date</label>
                                <input type="datetime-local" name="scheduled_at" class="form-input">
                            </div>

                            <div class="form-group">
                                <label class="form-label">Featured Image URL</label>
                                <input type="text" name="featured_image" class="form-input" placeholder="https://...">
                            </div>

                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                                <div class="form-group">
                                    <label class="form-label">Meta Title (SEO)</label>
                                    <input type="text" name="meta_title" class="form-input">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Meta Description (SEO)</label>
                                    <input type="text" name="meta_description" class="form-input">
                                </div>
                            </div>

                            <div class="form-group">
                                <label class="form-label">Tags (comma separated)</label>
                                <input type="text" name="tags" class="form-input" placeholder="forex, trading, gold">
                            </div>

                            <div class="form-group">
                                <label class="form-label">Content</label>
                                <div class="editor-toolbar">
                                    <button type="button" class="editor-btn" onclick="editorFormat('bold')" title="Bold"><i class="fas fa-bold"></i></button>
                                    <button type="button" class="editor-btn" onclick="editorFormat('italic')" title="Italic"><i class="fas fa-italic"></i></button>
                                    <button type="button" class="editor-btn" onclick="editorFormat('h2')" title="Heading 2">H2</button>
                                    <button type="button" class="editor-btn" onclick="editorFormat('h3')" title="Heading 3">H3</button>
                                    <button type="button" class="editor-btn" onclick="editorFormat('ul')" title="Bullet List"><i class="fas fa-list-ul"></i></button>
                                    <button type="button" class="editor-btn" onclick="editorFormat('ol')" title="Numbered List"><i class="fas fa-list-ol"></i></button>
                                    <button type="button" class="editor-btn" onclick="editorFormat('link')" title="Insert Link"><i class="fas fa-link"></i></button>
                                    <button type="button" class="editor-btn" onclick="insertImage()" title="Insert Image"><i class="fas fa-image"></i></button>
                                    <button type="button" class="editor-btn" onclick="insertVideo()" title="Embed Video"><i class="fas fa-video"></i></button>
                                </div>
                                <div class="editor-content" id="editor-content" contenteditable="true" oninput="updateEditorContent()"></div>
                                <input type="hidden" name="content" id="blog-content-hidden">
                            </div>

                            <div class="form-group">
                                <label class="form-label">
                                    <input type="checkbox" name="is_premium" style="margin-right: 8px;">
                                    Premium Content
                                </label>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="closeModal('blog-modal')" style="width: auto;">Cancel</button>
                        <button class="btn" onclick="submitBlogPost()" style="width: auto;">Publish</button>
                    </div>
                </div>
            </div>

            <!-- Telegram Section -->
            <div class="section" id="telegram-section">
                <div class="page-header">
                    <h2><i class="fab fa-telegram" style="color: var(--telegram);"></i> Telegram Signals</h2>
                </div>
                <div class="content-grid">
                    <div class="content-card">
                        <div style="width: 80px; height: 80px; background: var(--telegram); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; font-size: 40px; color: white;">
                            <i class="fab fa-telegram"></i>
                        </div>
                        <h3 style="text-align: center;">Free Channel</h3>
                        <div style="text-align: center; font-size: 48px; font-weight: 700; margin: 20px 0;">FREE</div>
                        <button class="btn btn-telegram" onclick="window.open('https://t.me/pipways_free', '_blank')">
                            <i class="fab fa-telegram"></i> Join Free Channel
                        </button>
                    </div>
                    <div class="content-card">
                        <div style="width: 80px; height: 80px; background: var(--premium); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; font-size: 40px; color: var(--bg-dark);">
                            <i class="fas fa-crown"></i>
                        </div>
                        <h3 style="text-align: center;">VIP Channel</h3>
                        <div style="text-align: center; font-size: 48px; font-weight: 700; margin: 20px 0; color: var(--premium);">$99/mo</div>
                        <button class="btn btn-premium" onclick="showToast('Contact admin for upgrade', 'success')">
                            <i class="fas fa-crown"></i> Upgrade to VIP
                        </button>
                    </div>
                </div>
            </div>

            <!-- Signals Section -->
            <div class="section" id="signals-section">
                <div class="page-header">
                    <h2><i class="fas fa-satellite-dish" style="color: var(--primary);"></i> Trading Signals</h2>
                    <p>Live trading signals from our expert analysts</p>
                </div>
                <div class="content-grid" id="signals-container">
                    <div class="content-card">
                        <p style="text-align: center; color: var(--text-secondary);">Loading signals...</p>
                    </div>
                </div>
            </div>

            <!-- AI Analysis Section -->
            <div class="section" id="analysis-section">
                <div class="page-header">
                    <h2><i class="fas fa-robot" style="color: var(--warning);"></i> AI Chart Analysis</h2>
                    <p>Upload your chart screenshots for instant AI-powered technical analysis</p>
                </div>
                <div style="max-width: 800px; margin: 30px auto; padding: 0 30px;">
                    <div class="content-card">
                        <div class="upload-area" onclick="document.getElementById('chart-file').click()">
                            <i class="fas fa-cloud-upload-alt" style="font-size: 64px; color: var(--primary); margin-bottom: 20px;"></i>
                            <h3>Upload Chart Image</h3>
                            <p style="color: var(--text-secondary); margin-top: 8px;">Click to select or drag and drop</p>
                            <input type="file" id="chart-file" class="hidden" accept="image/*" onchange="analyzeChart(this)">
                        </div>
                        <div style="margin-top: 20px;">
                            <div class="form-group">
                                <label class="form-label">Currency Pair</label>
                                <input type="text" id="chart-pair" class="form-input" placeholder="EURUSD" value="EURUSD">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Timeframe</label>
                                <select id="chart-timeframe" class="form-input">
                                    <option value="1H">1 Hour</option>
                                    <option value="4H">4 Hours</option>
                                    <option value="D1">Daily</option>
                                    <option value="W1">Weekly</option>
                                </select>
                            </div>
                        </div>
                        <div id="chart-analysis-result" style="margin-top: 30px; display: none;">
                            <h3 style="margin-bottom: 16px;">Analysis Result</h3>
                            <div id="chart-result-content" style="background: var(--bg-dark); padding: 20px; border-radius: 8px; white-space: pre-wrap; font-family: monospace;"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Courses Section -->
            <div class="section" id="courses-section">
                <div class="page-header">
                    <h2><i class="fas fa-graduation-cap" style="color: var(--warning);"></i> Trading Courses</h2>
                    <p>Professional trading education for all levels</p>
                </div>
                <div class="content-grid" id="courses-container">
                    <div class="content-card">
                        <p style="text-align: center; color: var(--text-secondary);">Loading courses...</p>
                    </div>
                </div>
            </div>

            <!-- Webinars Section -->
            <div class="section" id="webinars-section">
                <div class="page-header">
                    <h2><i class="fas fa-video" style="color: var(--secondary);"></i> Upcoming Webinars</h2>
                    <p>Live training sessions with expert traders</p>
                </div>
                <div class="content-grid" id="webinars-container">
                    <div class="content-card">
                        <p style="text-align: center; color: var(--text-secondary);">Loading webinars...</p>
                    </div>
                </div>
            </div>

            <!-- Blog Section -->
            <div class="section" id="blog-section">
                <div class="page-header">
                    <h2><i class="fas fa-newspaper" style="color: var(--primary);"></i> Trading Blog</h2>
                    <p>Latest news, analysis, and educational content</p>
                </div>
                <div class="content-grid" id="blog-container">
                    <div class="content-card">
                        <p style="text-align: center; color: var(--text-secondary);">Loading posts...</p>
                    </div>
                </div>
            </div>

            <!-- AI Mentor Section -->
            <div class="section" id="mentor-section">
                <div class="page-header">
                    <h2><i class="fas fa-comments" style="color: var(--premium);"></i> AI Trading Mentor</h2>
                    <p>Get personalized trading advice and answers to your questions</p>
                </div>
                <div style="max-width: 900px; margin: 30px auto; padding: 0 30px;">
                    <div class="content-card" style="height: 600px; display: flex; flex-direction: column;">
                        <div id="chat-messages" style="flex: 1; overflow-y: auto; margin-bottom: 20px; padding: 20px; background: var(--bg-dark); border-radius: 8px;">
                            <div style="background: var(--bg-hover); padding: 16px; border-radius: 12px; margin-bottom: 12px; max-width: 80%;">
                                <strong style="color: var(--premium);">AI Mentor:</strong><br>
                                Hello! I'm your AI Trading Mentor. Ask me anything about trading strategies, risk management, psychology, or market analysis.
                            </div>
                        </div>
                        <div style="display: flex; gap: 12px;">
                            <input type="text" id="chat-input" class="form-input" placeholder="Type your question..." style="flex: 1;" onkeypress="if(event.key==='Enter') sendChatMessage()">
                            <button class="btn btn-sm" onclick="sendChatMessage()" style="width: auto;"><i class="fas fa-paper-plane"></i></button>
                        </div>
                    </div>
                </div>
            </div>

        </main>
    </div>

    <script>
        // ==========================================
        // CONFIGURATION
        // ==========================================
        const API_URL = 'https://pipways-api-nhem.onrender.com';
        let authToken = localStorage.getItem('access_token');
        let refreshToken = localStorage.getItem('refresh_token');
        let currentUser = null;
        let trades = [];
        let currentPage = 1;

        // ==========================================
        // INITIALIZATION
        // ==========================================
        document.addEventListener('DOMContentLoaded', function() {
            if (authToken) {
                validateToken();
            } else {
                showAuthWall();
            }
        });

        function showLoading(show = true, text = 'Processing...') {
            const overlay = document.getElementById('loading-overlay');
            overlay.querySelector('p').textContent = text;
            overlay.classList.toggle('show', show);
        }

        function showToast(message, type = 'error') {
            const toast = document.getElementById('toast');
            toast.className = `toast ${type}`;
            document.getElementById('toast-message').textContent = message;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 5000);
        }

        // ==========================================
        // TOKEN MANAGEMENT
        // ==========================================
        async function validateToken() {
            try {
                const payload = JSON.parse(atob(authToken.split('.')[1]));
                
                if (payload.exp * 1000 < Date.now()) {
                    console.log('Token expired, attempting refresh...');
                    await refreshAccessToken();
                } else {
                    currentUser = payload;
                    showMainApp();
                }
            } catch (error) {
                console.error('Token validation error:', error);
                showAuthWall();
            }
        }

        async function refreshAccessToken() {
            try {
                if (!refreshToken) {
                    throw new Error('No refresh token');
                }

                const response = await fetch(`${API_URL}/auth/refresh`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${refreshToken}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    authToken = data.access_token;
                    localStorage.setItem('access_token', authToken);
                    currentUser = JSON.parse(atob(authToken.split('.')[1]));
                    showMainApp();
                } else {
                    throw new Error('Refresh failed');
                }
            } catch (error) {
                console.error('Refresh error:', error);
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                showAuthWall();
            }
        }

        // ==========================================
        // AUTH FUNCTIONS
        // ==========================================
        function showAuthWall() {
            document.getElementById('auth-wall').classList.remove('hidden');
            document.getElementById('main-app').classList.add('hidden');
        }

        function showMainApp() {
            document.getElementById('auth-wall').classList.add('hidden');
            document.getElementById('main-app').classList.remove('hidden');
            
            if (currentUser) {
                console.log("User:", currentUser.email, "Role:", currentUser.role);
                
                const isAdmin = currentUser.role === 'admin' || currentUser.role === 'moderator';
                
                if (isAdmin) {
                    const adminNav = document.getElementById('admin-nav-item');
                    const adminBadge = document.getElementById('admin-badge');
                    
                    if (adminNav) adminNav.classList.remove('hidden');
                    if (adminBadge) adminBadge.classList.remove('hidden');
                }
                
                document.getElementById('user-name').textContent = currentUser.full_name || currentUser.email;
                document.getElementById('user-email').textContent = currentUser.email;
                document.getElementById('user-avatar').textContent = (currentUser.full_name || currentUser.email).charAt(0).toUpperCase();
            }
        }

        function showRegister() {
            document.getElementById('login-form').classList.add('hidden');
            document.getElementById('register-form').classList.remove('hidden');
        }

        function showLogin() {
            document.getElementById('register-form').classList.add('hidden');
            document.getElementById('login-form').classList.remove('hidden');
        }

        async function handleLogin(e) {
            e.preventDefault();
            const btn = document.getElementById('login-btn');
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';

            try {
                const response = await fetch(`${API_URL}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        email: e.target.email.value,
                        password: e.target.password.value
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    authToken = data.access_token;
                    refreshToken = data.refresh_token;
                    localStorage.setItem('access_token', authToken);
                    localStorage.setItem('refresh_token', refreshToken);
                    currentUser = data.user;
                    showMainApp();
                    showToast('Welcome back!', 'success');
                } else {
                    document.getElementById('login-error').textContent = data.detail || 'Login failed';
                    document.getElementById('login-error').style.display = 'block';
                }
            } catch (error) {
                showToast('Network error. Please try again.', 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<span>Login</span>';
            }
        }

        async function handleRegister(e) {
            e.preventDefault();
            const btn = document.getElementById('register-btn');
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';

            try {
                const response = await fetch(`${API_URL}/auth/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        email: e.target.email.value,
                        password: e.target.password.value,
                        full_name: e.target.full_name.value
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    authToken = data.access_token;
                    refreshToken = data.refresh_token;
                    localStorage.setItem('access_token', authToken);
                    localStorage.setItem('refresh_token', refreshToken);
                    currentUser = data.user;
                    showMainApp();
                    showToast('Account created successfully!', 'success');
                } else {
                    document.getElementById('register-error').textContent = data.detail || 'Registration failed';
                    document.getElementById('register-error').style.display = 'block';
                }
            } catch (error) {
                showToast('Network error. Please try again.', 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<span>Create Account</span>';
            }
        }

        function logout() {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            authToken = null;
            refreshToken = null;
            currentUser = null;
            showAuthWall();
            showToast('Logged out successfully', 'success');
        }

        // ==========================================
        // NAVIGATION
        // ==========================================
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.querySelector('.sidebar-overlay');
            sidebar.classList.toggle('open');
            overlay.style.display = sidebar.classList.contains('open') ? 'block' : 'none';
        }

        function showSection(sectionName, element) {
            document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
            if (element) element.classList.add('active');

            document.querySelectorAll('.section').forEach(section => section.classList.remove('active'));
            document.getElementById(`${sectionName}-section`).classList.add('active');

            if (sectionName === 'admin') {
                loadAdminStats();
                loadBlogPosts();
            } else if (sectionName === 'signals') {
                loadSignals();
            } else if (sectionName === 'courses') {
                loadCourses();
            } else if (sectionName === 'webinars') {
                loadWebinars();
            } else if (sectionName === 'blog') {
                loadBlogPostsPublic();
            }

            if (window.innerWidth <= 768) {
                toggleSidebar();
            }
        }

        function showAdminTab(tabName, element) {
            document.querySelectorAll('.admin-tab').forEach(tab => {
                tab.classList.remove('active');
                tab.style.background = '';
                tab.style.color = '';
            });
            
            element.classList.add('active');
            element.style.background = 'var(--primary)';
            element.style.color = 'white';
            
            document.querySelectorAll('.admin-panel').forEach(panel => panel.classList.remove('active'));
            document.getElementById(`panel-${tabName}`).classList.add('active');
            
            if (tabName === 'users') {
                loadAdminUsers();
            } else if (tabName === 'content') {
                loadBlogPosts();
            }
        }

        // ==========================================
        // PERFORMANCE ANALYZER
        // ==========================================
        function showTradeInput(method) {
            document.getElementById('manual-input').classList.toggle('hidden', method !== 'manual');
            document.getElementById('csv-input').classList.toggle('hidden', method !== 'csv');
            
            document.getElementById('btn-manual').style.background = method === 'manual' ? 'var(--primary)' : 'transparent';
            document.getElementById('btn-csv').style.background = method === 'csv' ? 'var(--primary)' : 'transparent';
        }

        function addTrade() {
            const trade = {
                pair: document.getElementById('trade-pair').value.toUpperCase(),
                direction: document.getElementById('trade-direction').value,
                entry: parseFloat(document.getElementById('trade-entry').value),
                exit: parseFloat(document.getElementById('trade-exit').value),
                lots: parseFloat(document.getElementById('trade-lots').value),
                pips: parseFloat(document.getElementById('trade-pips').value),
                notes: document.getElementById('trade-notes').value
            };

            if (!trade.pair || !trade.entry || !trade.exit) {
                showToast('Please fill in required fields (Pair, Entry, Exit)', 'error');
                return;
            }

            trades.push(trade);
            renderTrades();
            clearTradeInputs();
        }

        function clearTradeInputs() {
            document.getElementById('trade-pair').value = '';
            document.getElementById('trade-entry').value = '';
            document.getElementById('trade-exit').value = '';
            document.getElementById('trade-pips').value = '';
            document.getElementById('trade-notes').value = '';
        }

        function renderTrades() {
            const container = document.getElementById('trades-container');
            const count = document.getElementById('trade-count');
            
            count.textContent = trades.length;
            document.getElementById('trades-list-card').classList.remove('hidden');
            
            container.innerHTML = trades.map((trade, index) => `
                <div class="trade-item">
                    <div>
                        <strong>${trade.pair}</strong> ${trade.direction.toUpperCase()}
                        <div style="font-size: 12px; color: var(--text-secondary);">${trade.notes || ''}</div>
                    </div>
                    <div style="text-align: right;">
                        <div>${trade.entry} → ${trade.exit}</div>
                        <div style="font-size: 12px;">${trade.lots || 0.1} lots</div>
                    </div>
                    <div class="trade-pnl ${trade.pips >= 0 ? 'positive' : 'negative'}" style="font-weight: bold;">
                        ${trade.pips >= 0 ? '+' : ''}${trade.pips} pips
                    </div>
                    <button class="action-btn delete" onclick="removeTrade(${index})" title="Remove">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `).join('');
        }

        function removeTrade(index) {
            trades.splice(index, 1);
            renderTrades();
            if (trades.length === 0) {
                document.getElementById('trades-list-card').classList.add('hidden');
            }
        }

        function clearTrades() {
            trades = [];
            renderTrades();
            document.getElementById('trades-list-card').classList.add('hidden');
        }

        async function analyzePerformance() {
            if (trades.length === 0) {
                showToast('Please add at least one trade', 'error');
                return;
            }

            showLoading(true, 'Analyzing with AI...');
            
            try {
                const response = await fetch(`${API_URL}/analyze/performance`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${authToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        trades: trades,
                        account_balance: parseFloat(document.getElementById('account-balance').value) || null,
                        trading_period_days: 30
                    })
                });

                if (!response.ok) {
                    throw new Error('Analysis failed');
                }

                const data = await response.json();
                displayAnalysis(data.analysis);
                
            } catch (error) {
                console.error('Analysis error:', error);
                showToast('Failed to analyze performance. Please try again.', 'error');
            } finally {
                showLoading(false);
            }
        }

        function displayAnalysis(analysis) {
            document.getElementById('analysis-results').classList.remove('hidden');
            
            const score = analysis.trader_score || 0;
            document.getElementById('trader-score').textContent = score;
            document.getElementById('score-circle').style.setProperty('--score', score);
            
            let interpretation = 'Needs significant improvement';
            if (score >= 80) interpretation = 'Excellent trading performance';
            else if (score >= 60) interpretation = 'Good performance with room for improvement';
            else if (score >= 40) interpretation = 'Average performance, focus on discipline';
            document.getElementById('score-interpretation').textContent = interpretation;

            const summary = analysis.performance_summary || {};
            document.getElementById('performance-summary').innerHTML = `
                <div class="metric-row">
                    <span>Total Trades</span>
                    <strong>${summary.total_trades || 0}</strong>
                </div>
                <div class="metric-row">
                    <span>Win Rate</span>
                    <strong style="color: ${parseInt(summary.win_rate) >= 50 ? 'var(--success)' : 'var(--danger)'}">${summary.win_rate || '0%'}</strong>
                </div>
                <div class="metric-row">
                    <span>Net Pips</span>
                    <strong style="color: ${String(summary.net_pips).startsWith('+') ? 'var(--success)' : 'var(--danger)'}">${summary.net_pips || 0}</strong>
                </div>
                <div class="metric-row">
                    <span>Risk/Reward</span>
                    <strong>${summary.risk_reward_ratio || 'N/A'}</strong>
                </div>
                <div class="metric-row">
                    <span>Profit Factor</span>
                    <strong>${summary.profit_factor || 'N/A'}</strong>
                </div>
            `;

            const createList = (items, containerId) => {
                const container = document.getElementById(containerId);
                if (items && items.length > 0) {
                    container.innerHTML = items.map(item => `<li>${item}</li>`).join('');
                } else {
                    container.innerHTML = '<li style="opacity: 0.6;">None identified</li>';
                }
            };

            createList(analysis.top_mistakes, 'top-mistakes');
            createList(analysis.strengths, 'strengths-list');
            
            const plan = analysis.improvement_plan || {};
            const allImprovements = [
                ...(plan.immediate_actions || []),
                ...(plan.strategy_improvements || []),
                ...(plan.risk_management_fixes || [])
            ];
            createList(allImprovements, 'improvement-plan');

            const coursesContainer = document.getElementById('recommended-courses');
            if (analysis.recommended_courses && analysis.recommended_courses.length > 0) {
                coursesContainer.innerHTML = analysis.recommended_courses.map(course => 
                    `<span style="background: var(--primary); color: white; padding: 6px 12px; border-radius: 20px; font-size: 14px;">${
