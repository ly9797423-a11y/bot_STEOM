<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#007AFF">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>منصة الاستثمار</title>
    
    <!-- Firebase SDKs -->
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-auth-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-database-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-analytics-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-storage-compat.js"></script>
    
    <!-- Google Fonts - Amiri -->
    <link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap" rel="stylesheet">
    
    <style>
        /* ============================================================
           CSS Variables & Root Configuration
           ============================================================ */
        :root {
            /* Primary Colors */
            --primary: #007AFF;
            --primary-dark: #0056B3;
            --primary-darker: #003D7A;
            --primary-light: #E3F2FD;
            --primary-lighter: #F0F7FF;
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --primary-gradient-hover: linear-gradient(135deg, #5a6fd8 0%, #6a3e8e 100%);
            
            /* Success Colors */
            --success: #34C759;
            --success-dark: #28A745;
            --success-darker: #1E7E34;
            --success-light: #E8F5E9;
            --success-gradient: linear-gradient(135deg, #34C759 0%, #30B350 100%);
            
            /* Danger Colors */
            --danger: #FF3B30;
            --danger-dark: #C62828;
            --danger-darker: #8E1D1D;
            --danger-light: #FFEBEE;
            --danger-gradient: linear-gradient(135deg, #FF3B30 0%, #C62828 100%);
            
            /* Warning Colors */
            --warning: #FF9500;
            --warning-dark: #F57C00;
            --warning-light: #FFF3E0;
            --warning-gradient: linear-gradient(135deg, #FF9500 0%, #FF6B6B 100%);
            
            /* Info Colors */
            --info: #5AC8FA;
            --info-dark: #0288D1;
            --info-light: #E1F5FE;
            
            /* Background Colors */
            --background: #F2F2F7;
            --background-dark: #1a1a2e;
            --background-darker: #16213e;
            --background-darkest: #0f0f1a;
            
            /* Card Colors */
            --card: #FFFFFF;
            --card-dark: #16213e;
            --card-hover: #F8F8FA;
            
            /* Text Colors */
            --text: #1C1C1E;
            --text-secondary: #6E6E73;
            --text-tertiary: #AEAEB2;
            --text-light: #FFFFFF;
            --text-light-secondary: rgba(255,255,255,0.7);
            
            /* Border Colors */
            --border: #D1D1D6;
            --border-light: #E5E5EA;
            --border-lighter: #F0F0F5;
            
            /* Shadow System */
            --shadow-xs: 0 1px 2px rgba(0,0,0,0.05);
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
            --shadow: 0 2px 10px rgba(0,0,0,0.1);
            --shadow-md: 0 4px 20px rgba(0,0,0,0.12);
            --shadow-lg: 0 10px 30px rgba(0,0,0,0.15);
            --shadow-xl: 0 20px 40px rgba(0,0,0,0.2);
            --shadow-2xl: 0 30px 60px rgba(0,0,0,0.25);
            
            /* Border Radius */
            --radius-xs: 4px;
            --radius-sm: 8px;
            --radius: 12px;
            --radius-md: 14px;
            --radius-lg: 16px;
            --radius-xl: 20px;
            --radius-2xl: 30px;
            --radius-full: 50%;
            --radius-pill: 999px;
            
            /* Layout */
            --nav-height: 85px;
            --status-bar: 44px;
            --safe-bottom: env(safe-area-inset-bottom, 0px);
            --safe-top: env(safe-area-inset-top, 0px);
            --safe-left: env(safe-area-inset-left, 0px);
            --safe-right: env(safe-area-inset-right, 0px);
            
            /* Transitions */
            --transition-fast: 0.15s ease;
            --transition: 0.3s ease;
            --transition-slow: 0.5s ease;
            --transition-spring: cubic-bezier(0.25, 0.46, 0.45, 0.94);
            
            /* Fonts */
            --font-primary: 'Amiri', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
            --font-secondary: 'Cairo', 'Amiri', -apple-system, sans-serif;
        }

        /* ============================================================
           CSS Reset & Base Styles
           ============================================================ */
        *,
        *::before,
        *::after {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        html {
            font-size: 16px;
            scroll-behavior: smooth;
            -webkit-text-size-adjust: 100%;
            -moz-text-size-adjust: 100%;
            text-size-adjust: 100%;
            height: 100%;
        }

        body {
            font-family: var(--font-primary);
            background: var(--background);
            color: var(--text);
            min-height: 100vh;
            min-height: 100dvh;
            overflow-x: hidden;
            user-select: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            -webkit-touch-callout: none;
            line-height: 1.6;
            letter-spacing: 0.3px;
            position: relative;
            height: 100%;
        }

        /* ============================================================
           Animations Keyframes
           ============================================================ */
        @keyframes slideUp {
            from { transform: translateY(50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        @keyframes slideDown {
            from { transform: translateY(-50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        @keyframes slideLeft {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes slideRight {
            from { transform: translateX(-100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }

        @keyframes scaleIn {
            from { transform: scale(0.8); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }

        @keyframes scaleOut {
            from { transform: scale(1); opacity: 1; }
            to { transform: scale(0.8); opacity: 0; }
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        @keyframes shimmer {
            0% { background-position: -1000px 0; }
            100% { background-position: 1000px 0; }
        }

        @keyframes countdown-pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.02); }
        }

        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-10px); }
            60% { transform: translateY(-5px); }
        }

        @keyframes ripple {
            to { transform: scale(4); opacity: 0; }
        }

        @keyframes glow {
            0%, 100% { box-shadow: 0 0 5px rgba(0,122,255,0.3); }
            50% { box-shadow: 0 0 20px rgba(0,122,255,0.6); }
        }

        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }

        @keyframes gradient-shift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        @keyframes progress-fill {
            from { width: 0; }
            to { width: var(--progress-width); }
        }

        @keyframes notification-slide {
            0% { transform: translateX(100%); opacity: 0; }
            10% { transform: translateX(0); opacity: 1; }
            90% { transform: translateX(0); opacity: 1; }
            100% { transform: translateX(100%); opacity: 0; }
        }

        @keyframes heartbeat {
            0%, 100% { transform: scale(1); }
            25% { transform: scale(1.1); }
            50% { transform: scale(1); }
            75% { transform: scale(1.05); }
        }

        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        @keyframes typewriter {
            from { width: 0; }
            to { width: 100%; }
        }

        .page-enter {
            animation: slideUp 0.4s var(--transition-spring);
        }

        .fade-enter {
            animation: fadeIn 0.3s ease-out;
        }

        .scale-enter {
            animation: scaleIn 0.3s var(--transition-spring);
        }

        .slide-left-enter {
            animation: slideLeft 0.3s ease-out;
        }

        .slide-right-enter {
            animation: slideRight 0.3s ease-out;
        }

        /* ============================================================
           Typography
           ============================================================ */
        h1, h2, h3, h4, h5, h6 {
            font-weight: 700;
            line-height: 1.3;
            margin-bottom: 10px;
            font-family: var(--font-secondary);
        }

        h1 { font-size: 28px; }
        h2 { font-size: 24px; }
        h3 { font-size: 20px; }
        h4 { font-size: 18px; }
        h5 { font-size: 16px; }
        h6 { font-size: 14px; }

        p {
            margin-bottom: 10px;
            line-height: 1.6;
        }

        a {
            color: var(--primary);
            text-decoration: none;
            transition: color var(--transition-fast);
        }

        a:hover {
            color: var(--primary-dark);
        }

        code {
            font-family: 'Courier New', monospace;
            background: #F0F0F5;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 14px;
            word-break: break-all;
        }

        /* ============================================================
           iOS Components - Buttons
           ============================================================ */
        .ios-button {
            background: var(--primary);
            color: white;
            border: none;
            border-radius: var(--radius);
            padding: 15px 20px;
            font-size: 17px;
            font-weight: 600;
            cursor: pointer;
            transition: all var(--transition-fast);
            font-family: var(--font-secondary);
            width: 100%;
            position: relative;
            overflow: hidden;
            letter-spacing: 0.5px;
            -webkit-tap-highlight-color: transparent;
            appearance: none;
            -webkit-appearance: none;
            outline: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .ios-button:hover {
            opacity: 0.9;
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }

        .ios-button:active {
            opacity: 0.7;
            transform: scale(0.98);
            box-shadow: var(--shadow-sm);
        }

        .ios-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            pointer-events: none;
            box-shadow: none;
        }

        .ios-button:focus {
            outline: 2px solid var(--primary);
            outline-offset: 2px;
        }

        .ios-button-secondary {
            background: var(--card);
            color: var(--primary);
            border: 1.5px solid var(--primary);
        }

        .ios-button-secondary:hover {
            background: var(--primary-light);
        }

        .ios-button-danger {
            background: var(--danger);
        }

        .ios-button-danger:hover {
            background: var(--danger-dark);
        }

        .ios-button-success {
            background: var(--success);
        }

        .ios-button-success:hover {
            background: var(--success-dark);
        }

        .ios-button-warning {
            background: var(--warning);
        }

        .ios-button-outline {
            background: transparent;
            color: var(--primary);
            border: 1.5px solid var(--primary);
        }

        .ios-button-ghost {
            background: transparent;
            color: var(--text-secondary);
            border: none;
        }

        .ios-button-ghost:hover {
            color: var(--text);
            background: rgba(0,0,0,0.05);
        }

        /* ============================================================
           iOS Components - Inputs
           ============================================================ */
        .ios-input {
            width: 100%;
            padding: 15px;
            border: 1.5px solid var(--border);
            border-radius: var(--radius);
            font-size: 16px;
            background: var(--card);
            transition: all var(--transition);
            font-family: var(--font-secondary);
            color: var(--text);
            appearance: none;
            -webkit-appearance: none;
            outline: none;
        }

        .ios-input:hover {
            border-color: var(--text-tertiary);
        }

        .ios-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 4px rgba(0,122,255,0.1);
        }

        .ios-input::placeholder {
            color: #AEAEB2;
        }

        .ios-input:disabled {
            background: #F2F2F7;
            color: #AEAEB2;
            cursor: not-allowed;
        }

        .ios-input-error {
            border-color: var(--danger) !important;
        }

        .ios-textarea {
            width: 100%;
            padding: 15px;
            border: 1.5px solid var(--border);
            border-radius: var(--radius);
            font-size: 16px;
            background: var(--card);
            transition: all var(--transition);
            font-family: var(--font-secondary);
            resize: vertical;
            min-height: 100px;
            outline: none;
        }

        .ios-textarea:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 4px rgba(0,122,255,0.1);
        }

        .ios-select {
            width: 100%;
            padding: 15px;
            border: 1.5px solid var(--border);
            border-radius: var(--radius);
            font-size: 16px;
            background: var(--card);
            font-family: var(--font-secondary);
            color: var(--text);
            appearance: none;
            -webkit-appearance: none;
            cursor: pointer;
            outline: none;
        }

        .ios-select:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 4px rgba(0,122,255,0.1);
        }

        /* ============================================================
           iOS Components - Cards
           ============================================================ */
        .ios-card {
            background: var(--card);
            border-radius: var(--radius);
            padding: 20px;
            margin: 10px;
            box-shadow: var(--shadow);
            transition: all var(--transition);
            position: relative;
            overflow: hidden;
        }

        .ios-card:hover {
            box-shadow: var(--shadow-md);
        }

        .ios-card:active {
            transform: scale(0.98);
            box-shadow: var(--shadow-lg);
        }

        .ios-card-flat {
            background: var(--card);
            border-radius: var(--radius);
            padding: 20px;
            margin: 10px;
            border: 1px solid var(--border-light);
        }

        .ios-card-gradient {
            background: var(--primary-gradient);
            border-radius: var(--radius);
            padding: 20px;
            margin: 10px;
            color: white;
            box-shadow: var(--shadow-lg);
        }

        /* ============================================================
           Navigation Bar
           ============================================================ */
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-top: 0.5px solid var(--border);
            display: flex;
            justify-content: space-around;
            align-items: center;
            height: var(--nav-height);
            padding-bottom: var(--safe-bottom);
            padding-left: var(--safe-left);
            padding-right: var(--safe-right);
            z-index: 100;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
        }

        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: none;
            border: none;
            cursor: pointer;
            padding: 8px 12px;
            transition: all var(--transition);
            position: relative;
            min-width: 60px;
            border-radius: 10px;
            -webkit-tap-highlight-color: transparent;
            outline: none;
        }

        .nav-item:hover {
            background: rgba(0,122,255,0.05);
        }

        .nav-item:active {
            background: rgba(0,122,255,0.1);
            transform: scale(0.95);
        }

        .nav-item svg {
            width: 24px;
            height: 24px;
            margin-bottom: 3px;
            transition: all var(--transition);
            fill: #8E8E93;
        }

        .nav-item span {
            font-size: 10px;
            font-weight: 600;
            color: #8E8E93;
            transition: all var(--transition);
            letter-spacing: 0.3px;
        }

        .nav-item.active svg {
            fill: var(--primary);
            transform: translateY(-2px);
        }

        .nav-item.active span {
            color: var(--primary);
            font-weight: 700;
        }

        .nav-badge {
            position: absolute;
            top: 2px;
            right: 5px;
            background: var(--danger);
            color: white;
            border-radius: var(--radius-full);
            width: 18px;
            height: 18px;
            font-size: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            animation: bounce 0.5s ease;
            box-shadow: 0 2px 5px rgba(255,59,48,0.3);
        }

        /* ============================================================
           Notification Icon
           ============================================================ */
        .notification-icon {
            position: fixed;
            top: calc(20px + var(--safe-top));
            left: calc(20px + var(--safe-left));
            z-index: 50;
            background: var(--card);
            border-radius: var(--radius-full);
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: var(--shadow);
            cursor: pointer;
            transition: all var(--transition);
            border: 1px solid var(--border);
            -webkit-tap-highlight-color: transparent;
        }

        .notification-icon:hover {
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }

        .notification-icon:active {
            transform: scale(0.9);
            box-shadow: var(--shadow-lg);
        }

        .notification-icon svg {
            width: 24px;
            height: 24px;
            fill: var(--primary);
        }

        /* ============================================================
           Auth Pages
           ============================================================ */
        .auth-container {
            min-height: 100vh;
            min-height: 100dvh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 20px;
            background: var(--primary-gradient);
            background-size: 400% 400%;
            animation: gradient-shift 15s ease infinite;
            position: relative;
            overflow: hidden;
        }

        .auth-container::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 3s infinite;
        }

        .auth-container::after {
            content: '';
            position: absolute;
            bottom: -20%;
            right: -20%;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%);
            border-radius: var(--radius-full);
        }

        .auth-card {
            background: var(--card);
            border-radius: var(--radius-xl);
            padding: 30px;
            box-shadow: var(--shadow-xl);
            max-width: 420px;
            width: 100%;
            margin: 0 auto;
            animation: scaleIn 0.5s var(--transition-spring);
            position: relative;
            z-index: 1;
        }

        .auth-title {
            text-align: center;
            margin-bottom: 25px;
            font-size: 24px;
            font-weight: 700;
            color: var(--text);
        }

        .auth-subtitle {
            text-align: center;
            margin-bottom: 20px;
            font-size: 14px;
            color: var(--text-secondary);
        }

        .auth-divider {
            display: flex;
            align-items: center;
            margin: 20px 0;
            color: var(--text-secondary);
            font-size: 14px;
        }

        .auth-divider::before,
        .auth-divider::after {
            content: '';
            flex: 1;
            height: 1px;
            background: var(--border);
        }

        .auth-divider span {
            padding: 0 10px;
            white-space: nowrap;
        }

        /* ============================================================
           Home Page Styles
           ============================================================ */
        .home-dashboard {
            padding: 20px 10px;
            max-width: 600px;
            margin: 0 auto;
        }

        .daily-profit-container {
            background: var(--primary-gradient);
            border-radius: var(--radius-xl);
            padding: 25px;
            color: white;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            position: relative;
            overflow: hidden;
        }

        .daily-profit-container::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            border-radius: var(--radius-full);
        }

        .daily-profit-container::after {
            content: '';
            position: absolute;
            bottom: -30%;
            left: -30%;
            width: 150px;
            height: 150px;
            background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
            border-radius: var(--radius-full);
        }

        .daily-profit-amount {
            font-size: 48px;
            font-weight: 700;
            margin: 15px 0;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
            position: relative;
            z-index: 1;
        }

        .daily-profit-label {
            font-size: 14px;
            opacity: 0.9;
            position: relative;
            z-index: 1;
        }

        .countdown-timer {
            background: rgba(255,255,255,0.2);
            border-radius: var(--radius);
            padding: 15px;
            font-size: 32px;
            font-weight: 700;
            letter-spacing: 2px;
            animation: countdown-pulse 2s infinite;
            position: relative;
            z-index: 1;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }

        .claim-button {
            background: var(--success);
            color: white;
            border: none;
            border-radius: var(--radius);
            padding: 15px;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            width: 100%;
            margin-top: 15px;
            font-family: var(--font-secondary);
            transition: all var(--transition);
            position: relative;
            z-index: 1;
            box-shadow: 0 5px 15px rgba(52, 199, 89, 0.3);
            -webkit-tap-highlight-color: transparent;
        }

        .claim-button:hover {
            box-shadow: 0 8px 20px rgba(52, 199, 89, 0.4);
        }

        .claim-button:active {
            transform: scale(0.95);
            box-shadow: 0 2px 5px rgba(52, 199, 89, 0.3);
        }

        .claim-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            box-shadow: none;
        }

        .plans-toggle-button {
            background: var(--warning-gradient);
            color: white;
            border: none;
            border-radius: var(--radius);
            padding: 15px;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            width: 100%;
            margin: 10px 0;
            font-family: var(--font-secondary);
            box-shadow: 0 5px 15px rgba(255, 107, 107, 0.3);
            transition: all var(--transition);
            -webkit-tap-highlight-color: transparent;
        }

        .plans-toggle-button:hover {
            box-shadow: 0 8px 20px rgba(255, 107, 107, 0.4);
        }

        .plans-toggle-button:active {
            transform: scale(0.95);
        }

        .my-subscriptions-button {
            background: var(--success-gradient);
            color: white;
            border: none;
            border-radius: var(--radius);
            padding: 15px;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            width: 100%;
            margin: 10px 0;
            font-family: var(--font-secondary);
            box-shadow: 0 5px 15px rgba(52, 199, 89, 0.3);
            transition: all var(--transition);
            -webkit-tap-highlight-color: transparent;
        }

        .my-subscriptions-button:hover {
            box-shadow: 0 8px 20px rgba(52, 199, 89, 0.4);
        }

        .my-subscriptions-button:active {
            transform: scale(0.95);
        }

        /* ============================================================
           Investment Plans
           ============================================================ */
        .plan-card {
            background: var(--card);
            border-radius: var(--radius);
            padding: 20px;
            margin: 10px 0;
            box-shadow: var(--shadow);
            border-left: 4px solid var(--primary);
            transition: all var(--transition);
            position: relative;
            overflow: hidden;
        }

        .plan-card:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }

        .plan-card:active {
            transform: scale(0.98);
        }

        .plan-card.recommended {
            border-left-color: var(--warning);
            background: linear-gradient(135deg, #FFF9E6 0%, #FFFFFF 100%);
        }

        .plan-card.recommended::before {
            content: 'مميز';
            position: absolute;
            top: 10px;
            left: 10px;
            background: var(--warning);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 5px rgba(255,149,0,0.3);
        }

        .plan-name {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 10px;
        }

        .plan-details {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            font-size: 14px;
            color: var(--text-secondary);
        }

        .plan-price {
            font-size: 24px;
            font-weight: 700;
            color: var(--primary);
        }

        .plan-profit {
            font-size: 18px;
            font-weight: 700;
            color: var(--success);
        }

        /* ============================================================
           Wallet Styles
           ============================================================ */
        .wallet-container {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            border-radius: var(--radius-xl);
            padding: 30px;
            margin: 20px 10px;
            color: white;
            position: relative;
            overflow: hidden;
            box-shadow: var(--shadow-xl);
        }

        .wallet-container::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
            animation: pulse 3s infinite;
        }

        .wallet-container::after {
            content: '';
            position: absolute;
            bottom: -30%;
            right: -30%;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%);
            border-radius: var(--radius-full);
        }

        .wallet-balance {
            font-size: 48px;
            font-weight: 700;
            text-align: center;
            margin: 20px 0;
            position: relative;
            z-index: 1;
            letter-spacing: 1px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }

        .wallet-label {
            font-size: 14px;
            opacity: 0.8;
            text-align: center;
            position: relative;
            z-index: 1;
        }

        .wallet-stats {
            display: flex;
            justify-content: space-around;
            margin-top: 20px;
            position: relative;
            z-index: 1;
        }

        .wallet-stat {
            text-align: center;
        }

        .wallet-stat-value {
            font-size: 20px;
            font-weight: 700;
        }

        .wallet-stat-label {
            font-size: 12px;
            opacity: 0.7;
        }

        /* ============================================================
           Chat Styles
           ============================================================ */
        .chat-container {
            display: flex;
            flex-direction: column;
            height: 60vh;
            background: var(--card);
            border-radius: var(--radius);
            overflow: hidden;
            margin: 10px;
            box-shadow: var(--shadow);
        }

        .chat-header {
            background: var(--card);
            padding: 15px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #F8F8F8;
            scroll-behavior: smooth;
        }

        .chat-message {
            max-width: 75%;
            margin: 10px 0;
            padding: 12px 16px;
            border-radius: 20px;
            word-wrap: break-word;
            position: relative;
            animation: slideUp 0.3s ease;
        }

        .chat-message.sent {
            background: var(--primary);
            color: white;
            margin-left: auto;
            border-bottom-left-radius: 5px;
        }

        .chat-message.received {
            background: #E9E9EB;
            margin-right: auto;
            border-bottom-right-radius: 5px;
        }

        .chat-message-time {
            font-size: 11px;
            opacity: 0.7;
            display: block;
            margin-top: 5px;
        }

        .chat-input-container {
            display: flex;
            gap: 10px;
            padding: 10px;
            border-top: 1px solid var(--border);
            background: var(--card);
        }

        /* ============================================================
           Admin Panel Styles
           ============================================================ */
        .admin-container {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
            padding-bottom: 100px;
        }

        .admin-sidebar {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: var(--radius);
            padding: 20px;
            color: white;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .admin-title {
            text-align: center;
            margin-bottom: 20px;
            font-size: 20px;
            font-weight: 700;
            color: white;
        }

        .admin-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }

        .admin-button {
            background: rgba(255,255,255,0.1);
            color: white;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: var(--radius);
            padding: 12px;
            font-size: 14px;
            cursor: pointer;
            transition: all var(--transition);
            font-family: var(--font-secondary);
            text-align: center;
            -webkit-tap-highlight-color: transparent;
        }

        .admin-button:hover {
            background: rgba(255,255,255,0.2);
        }

        .admin-button:active {
            transform: scale(0.95);
        }

        .admin-button.active {
            background: var(--primary);
            border-color: var(--primary);
            box-shadow: 0 5px 15px rgba(0,122,255,0.3);
        }

        /* ============================================================
           Admin Stats
           ============================================================ */
        .admin-stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }

        .admin-stat-card {
            background: white;
            border-radius: var(--radius);
            padding: 20px;
            text-align: center;
            box-shadow: var(--shadow);
            transition: all var(--transition);
        }

        .admin-stat-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }

        .admin-stat-icon {
            font-size: 40px;
            margin-bottom: 10px;
        }

        .admin-stat-value {
            font-size: 28px;
            font-weight: 700;
            color: var(--primary);
        }

        .admin-stat-label {
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 5px;
        }

        /* ============================================================
           Circular Progress
           ============================================================ */
        .circular-progress {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: conic-gradient(var(--primary) 0%, #E5E5EA 0%);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 20px auto;
            position: relative;
            transition: all 0.5s ease;
        }

        .circular-progress::before {
            content: '';
            position: absolute;
            width: 90px;
            height: 90px;
            border-radius: 50%;
            background: white;
        }

        .circular-progress-value {
            position: relative;
            z-index: 1;
            font-size: 24px;
            font-weight: 700;
            color: var(--primary);
        }

        /* ============================================================
           Blocked Screen
           ============================================================ */
        .blocked-screen {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
            background: var(--danger-gradient);
            color: white;
            text-align: center;
        }

        .blocked-icon {
            font-size: 80px;
            margin-bottom: 20px;
            animation: bounce 2s infinite;
        }

        .blocked-title {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 10px;
        }

        .blocked-reason {
            font-size: 16px;
            opacity: 0.9;
            margin-bottom: 20px;
            text-align: center;
            max-width: 400px;
        }

        .appeal-button {
            background: white;
            color: var(--danger);
            border: none;
            border-radius: var(--radius);
            padding: 15px 30px;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            font-family: var(--font-secondary);
            margin: 5px 0;
            max-width: 300px;
            width: 100%;
            transition: all var(--transition);
            -webkit-tap-highlight-color: transparent;
        }

        .appeal-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }

        /* ============================================================
           Action Buttons
           ============================================================ */
        .action-buttons {
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
            margin-top: 10px;
        }

        .action-btn {
            padding: 8px 12px;
            font-size: 11px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-family: var(--font-secondary);
            font-weight: 600;
            transition: all 0.2s;
            width: auto;
            -webkit-tap-highlight-color: transparent;
        }

        .action-btn:active {
            transform: scale(0.95);
        }

        .action-btn-block {
            background: var(--danger);
            color: white;
        }

        .action-btn-unblock {
            background: var(--success);
            color: white;
        }

        .action-btn-view {
            background: #E3F2FD;
            color: var(--primary);
        }

        .action-btn-edit {
            background: #FFF3E0;
            color: var(--warning);
        }

        .action-btn-send {
            background: #E8F5E9;
            color: var(--success);
        }

        .action-btn-delete {
            background: #FFEBEE;
            color: var(--danger);
        }

        .action-btn-copy {
            background: #F3E5F5;
            color: #9C27B0;
        }

        /* ============================================================
           Toast & Modal
           ============================================================ */
        .toast {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.85);
            color: white;
            padding: 14px 24px;
            border-radius: 25px;
            font-size: 14px;
            z-index: 1000;
            pointer-events: none;
            animation: slideDown 0.3s ease;
            max-width: 90%;
            text-align: center;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            box-shadow: var(--shadow-lg);
        }

        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 200;
            animation: fadeIn 0.3s ease;
            backdrop-filter: blur(5px);
            -webkit-backdrop-filter: blur(5px);
        }

        .modal-content {
            background: var(--card);
            border-radius: var(--radius-xl);
            padding: 20px;
            max-width: 90%;
            width: 400px;
            max-height: 80vh;
            overflow-y: auto;
            animation: scaleIn 0.3s var(--transition-spring);
            box-shadow: var(--shadow-xl);
        }

        .modal-title {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 15px;
            text-align: center;
        }

        /* ============================================================
           Loading Spinner
           ============================================================ */
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #F3F3F3;
            border-top: 4px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }

        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255,255,255,0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 300;
            backdrop-filter: blur(5px);
            -webkit-backdrop-filter: blur(5px);
        }

        /* ============================================================
           Utility Classes
           ============================================================ */
        .hidden { display: none !important; }
        .text-center { text-align: center; }
        .text-right { text-align: right; }
        .text-left { text-align: left; }
        .mt-5 { margin-top: 5px; }
        .mt-10 { margin-top: 10px; }
        .mt-15 { margin-top: 15px; }
        .mt-20 { margin-top: 20px; }
        .mt-30 { margin-top: 30px; }
        .mb-5 { margin-bottom: 5px; }
        .mb-10 { margin-bottom: 10px; }
        .mb-15 { margin-bottom: 15px; }
        .mb-20 { margin-bottom: 20px; }
        .p-10 { padding: 10px; }
        .p-15 { padding: 15px; }
        .p-20 { padding: 20px; }
        .p-30 { padding: 30px; }
        .flex { display: flex; }
        .flex-between { display: flex; justify-content: space-between; align-items: center; }
        .flex-center { display: flex; align-items: center; justify-content: center; }
        .flex-column { display: flex; flex-direction: column; }
        .gap-5 { gap: 5px; }
        .gap-10 { gap: 10px; }
        .gap-15 { gap: 15px; }
        .gap-20 { gap: 20px; }
        .w-full { width: 100%; }
        .w-auto { width: auto; }
        .font-bold { font-weight: 700; }
        .text-primary { color: var(--primary); }
        .text-success { color: var(--success); }
        .text-danger { color: var(--danger); }
        .text-warning { color: var(--warning); }
        .text-secondary { color: var(--text-secondary); }
        .bg-primary { background: var(--primary); }
        .bg-success { background: var(--success); }
        .bg-danger { background: var(--danger); }
        .bg-warning { background: var(--warning); }

        /* ============================================================
           Scrollbar
           ============================================================ */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }

        ::-webkit-scrollbar-track {
            background: transparent;
        }

        ::-webkit-scrollbar-thumb {
            background: #C1C1C1;
            border-radius: 3px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #A8A8A8;
        }

        /* ============================================================
           Responsive Design
           ============================================================ */
        @media (max-width: 768px) {
            .auth-card {
                padding: 20px;
            }
            
            .wallet-balance {
                font-size: 36px;
            }
            
            .plan-name {
                font-size: 18px;
            }
            
            .plan-price {
                font-size: 20px;
            }
            
            .daily-profit-amount {
                font-size: 36px;
            }
            
            .admin-stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        @media (max-width: 480px) {
            .ios-button {
                padding: 12px 16px;
                font-size: 15px;
            }
            
            .ios-input {
                padding: 12px;
                font-size: 14px;
            }
            
            .wallet-balance {
                font-size: 32px;
            }
            
            .nav-item span {
                font-size: 9px;
            }
            
            .daily-profit-amount {
                font-size: 32px;
            }
            
            .admin-stats-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (min-width: 1024px) {
            .auth-card {
                max-width: 500px;
            }
            
            .ios-card {
                margin: 15px auto;
                max-width: 600px;
            }
            
            .home-dashboard {
                max-width: 700px;
            }
        }
    </style>
</head>
<body>
    <div id="app"></div>
    <div id="toast" class="toast hidden"></div>
    <div id="modal"></div>
    <div id="loading"></div>

    <script>
        // ============================================================
        // Firebase Configuration
        // ============================================================
        const firebaseConfig = {
            apiKey: "AIzaSyADVytdWRsJoROwJb-GRPIyqLoLeqzk1pk",
            authDomain: "httpsexploitation.firebaseapp.com",
            databaseURL: "https://httpsexploitation-default-rtdb.firebaseio.com",
            projectId: "httpsexploitation",
            storageBucket: "httpsexploitation.firebasestorage.app",
            messagingSenderId: "331907569752",
            appId: "1:331907569752:web:b1268107b40062bcedd22d",
            measurementId: "G-JJJSWSZN2N"
        };

        // Initialize Firebase
        firebase.initializeApp(firebaseConfig);
        const auth = firebase.auth();
        const database = firebase.database();
        const analytics = firebase.analytics();

        // ============================================================
        // Constants
        // ============================================================
        const ADMIN_EMAIL = "ugd729710@gmail.com";
        const MIN_WITHDRAWAL = 5;
        const WITHDRAWAL_COOLDOWN = 24 * 60 * 60 * 1000;
        const PROFIT_INTERVAL = 24 * 60 * 60 * 1000;
        const REFERRAL_PERCENTAGE = 0.05;
        const TIME_MANIPULATION_THRESHOLD = 5 * 60 * 1000;
        const SESSION_CHECK_INTERVAL = 5 * 60 * 1000;
        const ACTIVITY_LOG_RETENTION = 24 * 60 * 60 * 1000;
        const MAX_DEVICE_WARNINGS = 2;

        // ============================================================
        // State Management
        // ============================================================
        let currentUser = null;
        let currentPage = 'home';
        let userData = null;
        let notifications = [];
        let investmentPlans = [];
        let userInvestments = [];
        let supportMessages = [];
        let adminPage = 'dashboard';
        let depositAddress = '';
        let selectedChatUser = null;
        let maintenanceMode = false;
        let blockedIPs = [];
        let admins = [];
        let privacyPolicy = '';
        let showPlans = false;
        let showMySubscriptions = false;
        let dailyProfitTotal = 0;
        let lastProfitClaim = null;
        let deviceWarnings = 0;
        let referredUsers = [];
        let withdrawalFilter = 'pending';
        let chatFilter = 'pending';
        let isClaiming = false;
        let registrationEnabled = true;
        let loginEnabled = true;
        let lastClaimTimestamp = null;

        // ============================================================
        // Utility Functions
        // ============================================================
        function showToast(message, duration = 3000) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.classList.remove('hidden');
            clearTimeout(window.toastTimeout);
            window.toastTimeout = setTimeout(() => {
                toast.classList.add('hidden');
            }, duration);
        }

        function showModal(content) {
            const modal = document.getElementById('modal');
            modal.innerHTML = `
                <div class="modal-overlay" onclick="if(event.target===this)closeModal()">
                    <div class="modal-content">
                        ${content}
                    </div>
                </div>
            `;
        }

        function closeModal() {
            document.getElementById('modal').innerHTML = '';
        }

        function showLoading() {
            const loading = document.getElementById('loading');
            loading.innerHTML = '<div class="loading-overlay"><div class="spinner"></div></div>';
        }

        function hideLoading() {
            document.getElementById('loading').innerHTML = '';
        }

        function formatDate(timestamp) {
            if (!timestamp) return '';
            return new Date(timestamp).toLocaleDateString('ar-IQ', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }

        function formatNumber(num) {
            return (num || 0).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }

        function generateUniqueId() {
            return Date.now().toString(36) + Math.random().toString(36).substr(2, 9) + Math.random().toString(36).substr(2, 5);
        }

        function generateReferralCode() {
            let code = '';
            for (let i = 0; i < 8; i++) {
                code += Math.floor(Math.random() * 10);
            }
            return code;
        }

        function validateEmail(email) {
            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return re.test(email);
        }

        function validatePhone(phone) {
            const re = /^\d{10,18}$/;
            return re.test(phone);
        }

        function validateTronAddress(address) {
            return address.startsWith('T') && address.length === 34;
        }

        function generateDeviceId() {
            let deviceId = localStorage.getItem('deviceId');
            if (!deviceId) {
                deviceId = generateUniqueId();
                localStorage.setItem('deviceId', deviceId);
            }
            return deviceId;
        }

        function getClientIP() {
            return new Promise((resolve) => {
                fetch('https://api.ipify.org?format=json')
                    .then(response => response.json())
                    .then(data => resolve(data.ip))
                    .catch(() => resolve('unknown'));
            });
        }

        function logActivity(userId, type, description, amount = 0) {
            database.ref('activities').push({
                userId: userId,
                type: type,
                description: description,
                amount: amount,
                timestamp: Date.now()
            });
        }

        function cleanupOldActivities() {
            const cutoffTime = Date.now() - ACTIVITY_LOG_RETENTION;
            database.ref('activities').orderByChild('timestamp').endAt(cutoffTime).once('value').then(snapshot => {
                const activities = snapshot.val();
                if (activities) {
                    Object.keys(activities).forEach(key => {
                        database.ref('activities/' + key).remove();
                    });
                }
            });
        }

        // ============================================================
        // Security Functions
        // ============================================================
        function protectAgainstTimeManipulation() {
            const lastTime = localStorage.getItem('lastServerTime');
            const currentTime = Date.now();
            
            if (lastTime) {
                const timeDiff = currentTime - parseInt(lastTime);
                
                if (timeDiff < -TIME_MANIPULATION_THRESHOLD) {
                    console.error('Time manipulation detected');
                    if (currentUser) {
                        database.ref('users/' + currentUser.uid).update({
                            balance: 0,
                            isBlocked: true,
                            blockReason: 'محاولة التلاعب بالوقت - حظر دائم',
                            blockTimestamp: Date.now()
                        });
                        
                        database.ref('activities').push({
                            userId: currentUser.uid,
                            type: 'security',
                            description: 'محاولة التلاعب بالوقت - تم الحظر',
                            timestamp: Date.now()
                        });
                        
                        auth.signOut();
                        showToast('تم حظر حسابك نهائياً بسبب محاولة التلاعب بالنظام');
                    }
                    return false;
                }
            }
            
            localStorage.setItem('lastServerTime', currentTime.toString());
            return true;
        }

        function validateSession() {
            if (!currentUser) return false;
            
            const deviceId = generateDeviceId();
            const storedDeviceId = localStorage.getItem('userDeviceId');
            const warnings = parseInt(localStorage.getItem('deviceWarnings') || '0');
            
            if (storedDeviceId && storedDeviceId !== deviceId) {
                const newWarnings = warnings + 1;
                localStorage.setItem('deviceWarnings', newWarnings.toString());
                
                if (newWarnings >= MAX_DEVICE_WARNINGS) {
                    if (currentUser) {
                        database.ref('users/' + currentUser.uid).update({
                            isBlocked: true,
                            blockReason: 'محاولة التحايل على النظام - استخدام أجهزة متعددة',
                            blockTimestamp: Date.now()
                        });
                        
                        database.ref('activities').push({
                            userId: currentUser.uid,
                            type: 'security',
                            description: 'استخدام أجهزة متعددة - حظر دائم',
                            timestamp: Date.now()
                        });
                        
                        auth.signOut();
                        showToast('تم حظر الحساب بسبب استخدام أجهزة متعددة');
                    }
                    return false;
                } else {
                    showToast(`تحذير ${newWarnings}: تم اكتشاف جهاز جديد. عند تكرار هذا سيتم حظر الحساب`);
                    return true;
                }
            }
            
            localStorage.setItem('userDeviceId', deviceId);
            return true;
        }

        function checkMaintenanceMode() {
            return maintenanceMode;
        }

        function calculateDailyProfit() {
            let total = 0;
            const now = Date.now();
            
            userInvestments.forEach(inv => {
                if (now < inv.endTime) {
                    total += inv.dailyProfit;
                }
            });
            
            return total;
        }

        function loadReferredUsers() {
            if (!currentUser) return;
            
            database.ref('referrals').orderByChild('referrerId').equalTo(currentUser.uid).once('value').then(snapshot => {
                const referrals = snapshot.val() || {};
                const referralKeys = Object.keys(referrals);
                
                if (referralKeys.length === 0) {
                    referredUsers = [];
                    if (currentPage === 'referral') renderApp();
                    return;
                }
                
                const userPromises = referralKeys.map(userId => {
                    return database.ref('users/' + userId).once('value').then(userSnapshot => {
                        const userData = userSnapshot.val();
                        return {
                            userId: userId,
                            userName: userData?.name || 'مستخدم محذوف',
                            email: userData?.email || '',
                            phone: userData?.phone || '',
                            ...referrals[userId]
                        };
                    });
                });
                
                Promise.all(userPromises).then(users => {
                    referredUsers = users;
                    if (currentPage === 'referral') renderApp();
                });
            });
        }

        // ============================================================
        // Authentication Functions
        // ============================================================
        async function signUpWithEmail(email, password, phone, name, inviteCode) {
            try {
                if (!registrationEnabled && email !== ADMIN_EMAIL) {
                    showToast('التسجيل متوقف حالياً');
                    return;
                }
                
                const userCredential = await auth.createUserWithEmailAndPassword(email, password);
                const user = userCredential.user;
                const referralCode = generateReferralCode();
                const deviceId = generateDeviceId();
                
                await database.ref('users/' + user.uid).set({
                    email: email,
                    phone: phone,
                    name: name,
                    balance: 0,
                    totalInvested: 0,
                    totalEarned: 0,
                    referralCode: referralCode,
                    createdAt: Date.now(),
                    isAdmin: email === ADMIN_EMAIL,
                    isBlocked: false,
                    deviceId: deviceId,
                    lastLogin: Date.now(),
                    referralEarnings: 0,
                    accountStatus: 'active',
                    deviceWarnings: 0,
                    lastProfitClaim: null
                });

                if (inviteCode) {
                    await processReferral(inviteCode, user.uid);
                }
                
                logActivity(user.uid, 'auth', 'إنشاء حساب جديد');
                
                showToast('تم إنشاء الحساب بنجاح');
                return user;
            } catch (error) {
                console.error('Sign up error:', error);
                let errorMessage = 'فشل إنشاء الحساب';
                
                switch (error.code) {
                    case 'auth/email-already-in-use':
                        errorMessage = 'البريد الإلكتروني مستخدم بالفعل';
                        break;
                    case 'auth/invalid-email':
                        errorMessage = 'البريد الإلكتروني غير صالح';
                        break;
                    case 'auth/weak-password':
                        errorMessage = 'كلمة السر ضعيفة جداً';
                        break;
                    case 'auth/operation-not-allowed':
                        errorMessage = 'التسجيل غير متاح حالياً';
                        break;
                }
                
                showToast(errorMessage);
                throw error;
            }
        }

        async function signInWithEmail(email, password) {
            try {
                if (!loginEnabled && email !== ADMIN_EMAIL) {
                    showToast('تسجيل الدخول متوقف حالياً');
                    return;
                }
                
                if (checkMaintenanceMode() && email !== ADMIN_EMAIL) {
                    showToast('المنصة قيد الصيانة حالياً');
                    throw new Error('Maintenance mode');
                }
                
                const userCredential = await auth.signInWithEmailAndPassword(email, password);
                const user = userCredential.user;
                
                const userSnapshot = await database.ref('users/' + user.uid).once('value');
                const userData = userSnapshot.val();
                
                if (userData && userData.isBlocked) {
                    await auth.signOut();
                    showToast('حسابك محظور: ' + (userData.blockReason || 'سبب غير محدد'));
                    throw new Error('Blocked account');
                }
                
                await database.ref('users/' + user.uid).update({
                    lastLogin: Date.now(),
                    deviceId: generateDeviceId()
                });
                
                logActivity(user.uid, 'auth', 'تسجيل دخول');
                
                showToast('تم تسجيل الدخول بنجاح');
                return user;
            } catch (error) {
                console.error('Sign in error:', error);
                let errorMessage = 'فشل تسجيل الدخول';
                
                switch (error.code) {
                    case 'auth/wrong-password':
                        errorMessage = 'كلمة السر غير صحيحة';
                        break;
                    case 'auth/user-not-found':
                        errorMessage = 'المستخدم غير موجود';
                        break;
                    case 'auth/invalid-email':
                        errorMessage = 'البريد الإلكتروني غير صالح';
                        break;
                    case 'auth/too-many-requests':
                        errorMessage = 'محاولات كثيرة، حاول لاحقاً';
                        break;
                }
                
                showToast(errorMessage);
                throw error;
            }
        }

        async function signInWithPhone(phone, password) {
            try {
                const snapshot = await database.ref('users').orderByChild('phone').equalTo(phone).once('value');
                const users = snapshot.val();
                
                if (users) {
                    const userId = Object.keys(users)[0];
                    return await signInWithEmail(users[userId].email, password);
                } else {
                    showToast('رقم الهاتف غير مسجل');
                    throw new Error('Phone not registered');
                }
            } catch (error) {
                throw error;
            }
        }

        async function processReferral(inviteCode, newUserId) {
            try {
                const snapshot = await database.ref('users').orderByChild('referralCode').equalTo(inviteCode).once('value');
                const users = snapshot.val();
                
                if (users) {
                    const referrerId = Object.keys(users)[0];
                    
                    await database.ref('referrals/' + newUserId).set({
                        referrerId: referrerId,
                        timestamp: Date.now(),
                        status: 'active'
                    });
                    
                    await database.ref('users/' + newUserId).update({
                        referrerId: referrerId
                    });
                    
                    logActivity(newUserId, 'referral', 'تطبيق رمز دعوة');
                    
                    showToast('تم تطبيق رمز الدعوة بنجاح');
                } else {
                    showToast('رمز الدعوة غير صالح');
                }
            } catch (error) {
                console.error('Referral error:', error);
            }
        }

        // ============================================================
        // Render Functions
        // ============================================================
        function renderApp() {
            const app = document.getElementById('app');
            
            if (!currentUser) {
                renderAuthPage(app);
            } else if (userData && userData.isBlocked) {
                renderBlockedPage(app);
            } else if (userData && userData.isAdmin && adminPage) {
                renderAdminPanel(app);
            } else {
                renderUserDashboard(app);
            }
        }

        function renderAuthPage(app) {
            if (checkMaintenanceMode()) {
                app.innerHTML = `
                    <div class="auth-container">
                        <div class="auth-card">
                            <h2 class="auth-title">صيانة</h2>
                            <p class="auth-subtitle">المنصة قيد الصيانة حالياً، يرجى المحاولة لاحقاً</p>
                        </div>
                    </div>
                `;
                return;
            }
            
            app.innerHTML = `
                <div class="auth-container">
                    <div class="auth-card">
                        <h2 class="auth-title">تسجيل الدخول</h2>
                        <p class="auth-subtitle">مرحباً بعودتك</p>
                        <form id="loginForm" autocomplete="off">
                            <div class="mb-15">
                                <input type="text" id="loginIdentifier" class="ios-input" placeholder="البريد الإلكتروني أو رقم الهاتف" required>
                            </div>
                            <div class="mb-20">
                                <input type="password" id="loginPassword" class="ios-input" placeholder="كلمة السر" required>
                            </div>
                            <button type="submit" class="ios-button">تسجيل الدخول</button>
                        </form>
                        <div class="auth-divider">
                            <span>أو</span>
                        </div>
                        <button class="ios-button ios-button-secondary" onclick="showSignUpForm()">إنشاء حساب جديد</button>
                        <button class="ios-button ios-button-ghost mt-10" onclick="showPrivacyPolicy()">سياسة الخصوصية</button>
                    </div>
                </div>
            `;
            
            document.getElementById('loginForm').addEventListener('submit', handleLogin);
        }

        function handleLogin(e) {
            e.preventDefault();
            const identifier = document.getElementById('loginIdentifier').value.trim();
            const password = document.getElementById('loginPassword').value;
            
            if (!identifier || !password) {
                showToast('يرجى ملء جميع الحقول');
                return;
            }
            
            if (validateEmail(identifier)) {
                signInWithEmail(identifier, password);
            } else if (validatePhone(identifier)) {
                signInWithPhone(identifier, password);
            } else {
                showToast('يرجى إدخال بريد إلكتروني أو رقم هاتف صحيح');
            }
        }

        function showSignUpForm() {
            const app = document.getElementById('app');
            app.innerHTML = `
                <div class="auth-container">
                    <div class="auth-card">
                        <h2 class="auth-title">إنشاء حساب</h2>
                        <p class="auth-subtitle">جميع الحقول إجبارية</p>
                        <form id="signUpForm" autocomplete="off">
                            <div class="mb-15">
                                <input type="text" id="signUpName" class="ios-input" placeholder="الاسم الكامل" required>
                            </div>
                            <div class="mb-15">
                                <input type="tel" id="signUpPhone" class="ios-input" placeholder="رقم الهاتف (10-18 رقم)" required>
                            </div>
                            <div class="mb-15">
                                <input type="email" id="signUpEmail" class="ios-input" placeholder="البريد الإلكتروني" required>
                            </div>
                            <div class="mb-15">
                                <input type="password" id="signUpPassword" class="ios-input" placeholder="كلمة السر (6 أحرف على الأقل)" required>
                            </div>
                            <div class="mb-20">
                                <input type="text" id="signUpInviteCode" class="ios-input" placeholder="رمز الدعوة">
                            </div>
                            <button type="submit" class="ios-button">إنشاء الحساب</button>
                        </form>
                        <button class="ios-button ios-button-secondary mt-10" onclick="renderApp()">العودة لتسجيل الدخول</button>
                    </div>
                </div>
            `;
            
            document.getElementById('signUpForm').addEventListener('submit', handleSignUp);
        }

        function handleSignUp(e) {
            e.preventDefault();
            const name = document.getElementById('signUpName').value.trim();
            const phone = document.getElementById('signUpPhone').value.trim();
            const email = document.getElementById('signUpEmail').value.trim();
            const password = document.getElementById('signUpPassword').value;
            const inviteCode = document.getElementById('signUpInviteCode').value.trim();
            
            if (!name || !phone || !email || !password) {
                showToast('جميع الحقول إجبارية');
                return;
            }
            
            if (!validatePhone(phone)) {
                showToast('رقم الهاتف يجب أن يكون من 10 إلى 18 رقم');
                return;
            }
            
            if (!validateEmail(email)) {
                showToast('البريد الإلكتروني غير صحيح');
                return;
            }
            
            if (password.length < 6) {
                showToast('كلمة السر يجب أن تكون 6 أحرف على الأقل');
                return;
            }
            
            signUpWithEmail(email, password, phone, name, inviteCode);
        }

        function showPrivacyPolicy() {
            const app = document.getElementById('app');
            app.innerHTML = `
                <div class="auth-container">
                    <div class="auth-card">
                        <h2 class="auth-title">سياسة الخصوصية</h2>
                        <div style="max-height:500px; overflow-y:auto; line-height:1.8; text-align:justify; font-size:14px;">
                            ${privacyPolicy || getDefaultPrivacyPolicy()}
                        </div>
                        <button class="ios-button mt-20" onclick="renderApp()">العودة</button>
                    </div>
                </div>
            `;
        }

        function getDefaultPrivacyPolicy() {
            return `
                <h3>سياسة الخصوصية لمنصة الاستثمار</h3>
                <p>آخر تحديث: ${new Date().toLocaleDateString('ar-IQ')}</p>
                
                <h4>1. مقدمة</h4>
                <p>نحن في منصة الاستثمار نلتزم بحماية خصوصية مستخدمينا. توضح سياسة الخصوصية هذه كيفية جمع واستخدام وحماية المعلومات الشخصية التي تقدمها عند استخدام منصتنا.</p>
                
                <h4>2. المعلومات التي نجمعها</h4>
                <p>نقوم بجمع المعلومات التالية:</p>
                <ul style="padding-right:20px;">
                    <li>الاسم الكامل</li>
                    <li>البريد الإلكتروني</li>
                    <li>رقم الهاتف</li>
                    <li>معلومات المعاملات المالية</li>
                    <li>بيانات الجهاز والمتصفح</li>
                </ul>
                
                <h4>3. استخدام المعلومات</h4>
                <p>نستخدم المعلومات المجمعة للأغراض التالية:</p>
                <ul style="padding-right:20px;">
                    <li>إنشاء وإدارة الحسابات</li>
                    <li>معالجة المعاملات المالية</li>
                    <li>تحسين خدماتنا</li>
                    <li>التواصل مع المستخدمين</li>
                    <li>منع الاحتيال وحماية الأمن</li>
                </ul>
                
                <h4>4. حماية البيانات</h4>
                <p>نستخدم تقنيات تشفير متقدمة لحماية بيانات المستخدمين. جميع المعاملات تتم عبر اتصالات آمنة ومشفرة.</p>
                
                <h4>5. مشاركة المعلومات</h4>
                <p>لا نشارك المعلومات الشخصية مع أطراف ثالثة إلا في الحالات التالية:</p>
                <ul style="padding-right:20px;">
                    <li>بموافقة صريحة من المستخدم</li>
                    <li>للامتثال للمتطلبات القانونية</li>
                    <li>لحماية حقوق المنصة والمستخدمين</li>
                </ul>
                
                <h4>6. حقوق المستخدم</h4>
                <p>يحق للمستخدمين:</p>
                <ul style="padding-right:20px;">
                    <li>الوصول إلى بياناتهم</li>
                    <li>تصحيح المعلومات غير الدقيقة</li>
                    <li>حذف حسابهم</li>
                    <li>سحب الموافقة على معالجة البيانات</li>
                </ul>
                
                <h4>7. ملفات تعريف الارتباط</h4>
                <p>نستخدم ملفات تعريف الارتباط لتحسين تجربة المستخدم وتخصيص المحتوى.</p>
                
                <h4>8. التغييرات على السياسة</h4>
                <p>نحتفظ بالحق في تعديل سياسة الخصوصية. سيتم إشعار المستخدمين بأي تغييرات جوهرية.</p>
                
                <h4>9. الاتصال</h4>
                <p>للاستفسارات حول سياسة الخصوصية، يرجى التواصل مع فريق الدعم.</p>
            `;
        }

        function renderBlockedPage(app) {
            app.innerHTML = `
                <div class="blocked-screen">
                    <div class="blocked-icon">🚫</div>
                    <h2 class="blocked-title">تم حظر حسابك</h2>
                    <p class="blocked-reason">السبب: ${userData.blockReason || 'غير محدد'}</p>
                    <p class="blocked-reason">تاريخ الحظر: ${formatDate(userData.blockTimestamp)}</p>
                    <button class="appeal-button" onclick="appealBlock()">الطعن في القرار</button>
                    <button class="appeal-button" style="margin-top:10px; background:transparent; color:white; border:2px solid white;" onclick="logout()">تسجيل الخروج</button>
                </div>
            `;
        }

        function appealBlock() {
            showModal(`
                <h3 class="modal-title">الطعن في قرار الحظر</h3>
                <p class="text-center mb-10">اشرح سبب طعنك في القرار</p>
                <textarea id="appealReason" class="ios-textarea" placeholder="سبب الطعن..."></textarea>
                <button class="ios-button mt-10" onclick="submitAppeal()">إرسال الطعن</button>
            `);
        }

        function submitAppeal() {
            const reason = document.getElementById('appealReason').value.trim();
            if (!reason) {
                showToast('يرجى كتابة سبب الطعن');
                return;
            }
            
            database.ref('appeals').push({
                userId: currentUser.uid,
                userName: userData.name,
                reason: reason,
                status: 'pending',
                timestamp: Date.now()
            }).then(() => {
                showToast('تم إرسال طعنك للمراجعة');
                closeModal();
            });
        }

        function renderUserDashboard(app) {
            const notificationCount = notifications.filter(n => !n.read).length;
            const isAdmin = userData && userData.isAdmin;
            
            app.innerHTML = `
                <div class="notification-icon" onclick="showNotifications()">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                        <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                    </svg>
                    ${notificationCount > 0 ? `<div class="nav-badge">${notificationCount}</div>` : ''}
                </div>
                
                <div id="pageContent" style="padding-bottom:100px;">
                    ${renderCurrentPage()}
                </div>
                
                <nav class="bottom-nav">
                    <button class="nav-item ${currentPage === 'home' ? 'active' : ''}" onclick="switchPage('home')">
                        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L2 12h3v8h6v-6h2v6h6v-8h3L12 2z"/></svg>
                        <span>الرئيسية</span>
                    </button>
                    <button class="nav-item ${currentPage === 'wallet' ? 'active' : ''}" onclick="switchPage('wallet')">
                        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M21 18v1c0 1.1-.9 2-2 2H5c-1.11 0-2-.9-2-2V5c0-1.1.89-2 2-2h14c1.1 0 2 .9 2 2v1h-9c-1.11 0-2 .9-2 2v8c0 1.1.89 2 2 2h9z"/></svg>
                        <span>المحفظة</span>
                    </button>
                    <button class="nav-item ${currentPage === 'support' ? 'active' : ''}" onclick="switchPage('support')">
                        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>
                        <span>الدعم</span>
                    </button>
                    <button class="nav-item ${currentPage === 'referral' ? 'active' : ''}" onclick="switchPage('referral')">
                        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3z"/></svg>
                        <span>الدعوة</span>
                    </button>
                    <button class="nav-item ${currentPage === 'profile' ? 'active' : ''}" onclick="switchPage('profile')">
                        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
                        <span>حسابي</span>
                    </button>
                    ${isAdmin ? `
                    <button class="nav-item" onclick="showAdminPanel()">
                        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/></svg>
                        <span>التحكم</span>
                    </button>
                    ` : ''}
                </nav>
            `;
        }

        function renderCurrentPage() {
            switch (currentPage) {
                case 'home': return renderHomePage();
                case 'wallet': return renderWalletPage();
                case 'support': return renderSupportPage();
                case 'referral': return renderReferralPage();
                case 'profile': return renderProfilePage();
                case 'notifications': return renderNotificationsPage();
                default: return renderHomePage();
            }
        }

        function renderHomePage() {
            const dailyProfit = calculateDailyProfit();
            const canClaim = userData.lastProfitClaim ? (Date.now() - userData.lastProfitClaim >= PROFIT_INTERVAL) : true;
            
            return `
                <div class="home-dashboard page-enter">
                    <div class="daily-profit-container">
                        <h3 class="daily-profit-label">أرباحك اليومية</h3>
                        <div class="daily-profit-amount">${formatNumber(dailyProfit)} USDT</div>
                        <div class="countdown-timer" id="profitCountdown">
                            ${canClaim ? 'جاهز للاستلام' : formatCountdown(userData.lastProfitClaim + PROFIT_INTERVAL)}
                        </div>
                        <button class="claim-button" id="claimButton" ${canClaim && dailyProfit > 0 ? '' : 'disabled'} onclick="claimDailyProfit()">
                            ${canClaim && dailyProfit > 0 ? 'استلام أرباحك اليومية' : 'الرجاء الانتظار'}
                        </button>
                    </div>
                    
                    <button class="plans-toggle-button" onclick="togglePlans()">الخطط المتاحة</button>
                    <div id="availablePlans" style="${showPlans ? '' : 'display:none;'}">${renderAvailablePlans()}</div>
                    
                    <button class="my-subscriptions-button" onclick="toggleMySubscriptions()">اشتراكاتي</button>
                    <div id="mySubscriptions" style="${showMySubscriptions ? '' : 'display:none;'}">${renderMySubscriptions()}</div>
                </div>
            `;
        }

        function renderAvailablePlans() {
            if (investmentPlans.length === 0) return '<p class="text-center p-20">لا توجد خطط متاحة</p>';
            
            return investmentPlans.map(plan => {
                const purchased = userInvestments.some(inv => inv.planId === plan.id);
                const totalProfit = plan.dailyProfit * plan.duration;
                
                return `
                    <div class="plan-card ${plan.recommended ? 'recommended' : ''}">
                        <div class="plan-name">${plan.name}</div>
                        <div class="plan-details">
                            <span>السعر: <strong class="plan-price">${plan.price} USDT</strong></span>
                            <span>الربح اليومي: <strong class="plan-profit">${plan.dailyProfit} USDT</strong></span>
                        </div>
                        <div class="plan-details">
                            <span>المدة: ${plan.duration} يوم</span>
                            <span>الإجمالي: ${totalProfit} USDT</span>
                        </div>
                        ${purchased ? 
                            '<button class="ios-button" disabled style="background:var(--success); opacity:0.7;">تم الشراء</button>' : 
                            `<button class="ios-button" onclick="purchasePlan('${plan.id}')">شراء الخطة</button>`
                        }
                    </div>
                `;
            }).join('');
        }

        function renderMySubscriptions() {
            if (userInvestments.length === 0) return '<p class="text-center p-20">لا توجد اشتراكات نشطة</p>';
            
            return userInvestments.map(inv => {
                const daysLeft = Math.ceil((inv.endTime - Date.now()) / (24 * 60 * 60 * 1000));
                return `
                    <div class="ios-card">
                        <h3>${inv.planName}</h3>
                        <div style="font-size:24px;font-weight:bold;color:var(--primary);text-align:center;padding:15px;background:#F0F0F5;border-radius:8px;margin:10px 0;" id="timer-${inv.id}">
                            ${formatTimeRemaining(inv.endTime)}
                        </div>
                        <div class="flex-between">
                            <span>الربح اليومي: ${inv.dailyProfit} USDT</span>
                            <span>المتبقي: ${daysLeft} يوم</span>
                        </div>
                        <div class="flex-between mt-10">
                            <span>الأرباح المجمعة: ${formatNumber(inv.accumulatedProfit)} USDT</span>
                            <span>السعر: ${inv.price} USDT</span>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function togglePlans() {
            showPlans = !showPlans;
            renderApp();
        }

        function toggleMySubscriptions() {
            showMySubscriptions = !showMySubscriptions;
            renderApp();
        }

        function formatCountdown(endTime) {
            const remaining = endTime - Date.now();
            if (remaining <= 0) return '00:00:00';
            
            const hours = Math.floor(remaining / (60 * 60 * 1000));
            const minutes = Math.floor((remaining % (60 * 60 * 1000)) / (60 * 1000));
            const seconds = Math.floor((remaining % (60 * 1000)) / 1000);
            
            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }

        function claimDailyProfit() {
            if (isClaiming) {
                showToast('جاري المعالجة...');
                return;
            }
            
            const total = calculateDailyProfit();
            if (total <= 0) {
                showToast('لا توجد أرباح للاستلام');
                return;
            }
            
            const canClaim = userData.lastProfitClaim ? (Date.now() - userData.lastProfitClaim >= PROFIT_INTERVAL) : true;
            if (!canClaim) {
                showToast('لم يحن وقت الاستلام بعد');
                return;
            }
            
            isClaiming = true;
            showLoading();
            
            database.ref('users/' + currentUser.uid).update({
                balance: (userData.balance || 0) + total,
                totalEarned: (userData.totalEarned || 0) + total,
                lastProfitClaim: Date.now()
            }).then(() => {
                if (userData.referrerId) {
                    const referralEarning = total * REFERRAL_PERCENTAGE;
                    database.ref('users/' + userData.referrerId).update({
                        balance: firebase.database.ServerValue.increment(referralEarning),
                        referralEarnings: firebase.database.ServerValue.increment(referralEarning)
                    });
                }
                
                userInvestments.forEach(inv => {
                    if (Date.now() < inv.endTime) {
                        database.ref('investments/' + inv.id).update({
                            accumulatedProfit: (inv.accumulatedProfit || 0) + inv.dailyProfit,
                            lastProfitTime: Date.now()
                        });
                    }
                });
                
                database.ref('users/' + currentUser.uid + '/notifications').push({
                    title: 'ربح يومي',
                    body: `تم إضافة ${total} USDT إلى رصيدك`,
                    timestamp: Date.now(),
                    read: false
                });
                
                logActivity(currentUser.uid, 'profit', 'استلام أرباح يومية', total);
                
                hideLoading();
                isClaiming = false;
                showToast(`تم استلام ${formatNumber(total)} USDT`);
                renderApp();
            }).catch(error => {
                hideLoading();
                isClaiming = false;
                showToast('فشل استلام الأرباح');
                console.error('Claim error:', error);
            });
        }

        function formatTimeRemaining(endTime) {
            const remaining = endTime - Date.now();
            if (remaining <= 0) return 'منتهية';
            
            const days = Math.floor(remaining / (24 * 60 * 60 * 1000));
            const hours = Math.floor((remaining % (24 * 60 * 60 * 1000)) / (60 * 60 * 1000));
            const minutes = Math.floor((remaining % (60 * 60 * 1000)) / (60 * 1000));
            
            return `${days} يوم ${hours}:${minutes.toString().padStart(2, '0')}`;
        }

        function renderWalletPage() {
            return `
                <div class="page-enter">
                    <div class="wallet-container">
                        <div class="wallet-label text-center">رصيدك الحالي</div>
                        <div class="wallet-balance">${formatNumber(userData?.balance || 0)} USDT</div>
                        <div class="wallet-stats">
                            <div class="wallet-stat">
                                <div class="wallet-stat-value">${formatNumber(userData?.totalInvested || 0)}</div>
                                <div class="wallet-stat-label">إجمالي الاستثمار</div>
                            </div>
                            <div class="wallet-stat">
                                <div class="wallet-stat-value">${formatNumber(userData?.totalEarned || 0)}</div>
                                <div class="wallet-stat-label">إجمالي الأرباح</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="p-10">
                        <h4>الشحن عبر USDT (TRC20)</h4>
                        <div class="ios-card">
                            <p class="font-bold mb-10">عنوان المحفظة:</p>
                            <code style="word-break:break-all; background:#F0F0F0; padding:15px; border-radius:8px; display:block; font-size:14px;">${depositAddress || 'TRON_ADDRESS_PLACEHOLDER'}</code>
                            <button class="ios-button ios-button-secondary mt-10" onclick="copyDepositAddress()">نسخ العنوان</button>
                            <p class="mt-15" style="font-size:13px; color:var(--text-secondary);">
                                بعد إتمام التحويل، أرسل وصل التحويل والبريد الإلكتروني إلى بوت التليجرام: @Receipt_transferOKX_bot
                            </p>
                        </div>
                    </div>
                    
                    <div class="p-10">
                        <h4>السحب</h4>
                        <div class="ios-card">
                            <form id="withdrawalForm">
                                <input type="number" id="withdrawalAmount" class="ios-input" placeholder="المبلغ (الحد الأدنى 5 USDT)" min="5" step="0.01" required style="margin-bottom:15px;">
                                <input type="text" id="withdrawalAddress" class="ios-input" placeholder="عنوان TRON (TRC20)" required style="margin-bottom:15px;">
                                <button type="submit" class="ios-button">طلب سحب</button>
                            </form>
                            <p class="mt-15" style="font-size:12px; color:var(--text-secondary);">
                                يمكنك السحب مرة واحدة كل 24 ساعة<br>
                                مدة استلام التحويل من دقيقة إلى 48 ساعة
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }

        function renderSupportPage() {
            const myMessages = supportMessages.filter(msg => 
                msg.senderId === currentUser.uid || msg.receiverId === currentUser.uid
            );
            
            return `
                <div class="page-enter">
                    <div class="p-20 text-center">
                        <h2>الدعم الفني</h2>
                        <p style="color:var(--text-secondary); font-size:14px;">تواصل مع فريق الدعم</p>
                    </div>
                    <div class="chat-container">
                        <div class="chat-header">
                            <span class="font-bold">محادثة مباشرة</span>
                            <span style="font-size:12px; color:var(--success);">متصل</span>
                        </div>
                        <div class="chat-messages" id="supportMessages">
                            ${myMessages.length > 0 ? myMessages.map(msg => `
                                <div class="chat-message ${msg.senderId === currentUser.uid ? 'sent' : 'received'}">
                                    ${msg.text}
                                    <span class="chat-message-time">${formatDate(msg.timestamp)}</span>
                                </div>
                            `).join('') : '<p class="text-center mt-20" style="color:var(--text-secondary);">ابدأ المحادثة مع الدعم الفني</p>'}
                        </div>
                        <form id="supportForm" class="chat-input-container">
                            <input type="text" id="supportInput" class="ios-input" placeholder="اكتب رسالتك..." style="flex:1;">
                            <button type="submit" class="ios-button" style="width:auto; padding:12px 20px;">إرسال</button>
                        </form>
                    </div>
                </div>
            `;
        }

        function renderReferralPage() {
            const referralLink = `https://exploitation.kesug.com/${userData?.referralCode || ''}`;
            
            return `
                <div class="page-enter">
                    <div class="p-20">
                        <h2 class="text-center">دعوة الأصدقاء</h2>
                        <p class="text-center" style="color:var(--text-secondary);">احصل على مكافآت عند دعوة أصدقائك</p>
                        
                        <div class="ios-card mt-20">
                            <h4>رابط الدعوة الخاص بك:</h4>
                            <code style="word-break:break-all; background:#F0F0F0; padding:15px; border-radius:8px; display:block; margin:15px 0; font-size:14px;">${referralLink}</code>
                            <button class="ios-button" onclick="copyReferralLink()">نسخ الرابط</button>
                        </div>
                        
                        <div class="referral-stats">
                            <div class="referral-stat-card">
                                <div class="referral-stat-value">${referredUsers.length}</div>
                                <div class="referral-stat-label">عدد المدعوين</div>
                            </div>
                            <div class="referral-stat-card">
                                <div class="referral-stat-value">${formatNumber(userData?.referralEarnings || 0)}</div>
                                <div class="referral-stat-label">إجمالي الأرباح</div>
                            </div>
                        </div>
                        
                        <div class="ios-card">
                            <h4>المدعوين:</h4>
                            <div id="referredUsersList">
                                ${referredUsers.length > 0 ? referredUsers.map(ref => `
                                    <div class="flex-between mt-10" style="background:#F0F0F5; padding:15px; border-radius:8px;">
                                        <div>
                                            <strong style="font-size:16px;">${ref.userName || 'مستخدم'}</strong>
                                            <br>
                                            <small style="color:var(--text-secondary);">${ref.email || ''}</small>
                                        </div>
                                        <div style="text-align:left;">
                                            <small style="color:var(--text-secondary); display:block;">${formatDate(ref.timestamp)}</small>
                                            <small style="color:var(--success); display:block;">نشط</small>
                                        </div>
                                    </div>
                                `).join('') : '<p class="text-center mt-10">لم تقم بدعوة أي شخص بعد</p>'}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        function renderProfilePage() {
            return `
                <div class="page-enter">
                    <div class="profile-header">
                        <div class="profile-avatar">${userData?.name?.charAt(0) || 'م'}</div>
                        <h2>${userData?.name || 'مستخدم'}</h2>
                        <p style="opacity:0.8;">${userData?.email || ''}</p>
                    </div>
                    
                    <div class="p-20">
                        <div class="ios-card">
                            <h4>معلومات الحساب</h4>
                            <div class="flex-between mt-10">
                                <span style="color:var(--text-secondary);">رقم الهاتف:</span>
                                <span>${userData?.phone || ''}</span>
                            </div>
                            <div class="flex-between mt-10">
                                <span style="color:var(--text-secondary);">رمز الدعوة:</span>
                                <span>${userData?.referralCode || ''}</span>
                            </div>
                            <div class="flex-between mt-10">
                                <span style="color:var(--text-secondary);">تاريخ التسجيل:</span>
                                <span>${formatDate(userData?.createdAt)}</span>
                            </div>
                        </div>
                        
                        <div class="ios-card">
                            <h4>الإحصائيات</h4>
                            <div class="flex-between mt-10">
                                <span style="color:var(--text-secondary);">الرصيد:</span>
                                <strong>${formatNumber(userData?.balance || 0)} USDT</strong>
                            </div>
                            <div class="flex-between mt-10">
                                <span style="color:var(--text-secondary);">إجمالي الاستثمار:</span>
                                <strong>${formatNumber(userData?.totalInvested || 0)} USDT</strong>
                            </div>
                            <div class="flex-between mt-10">
                                <span style="color:var(--text-secondary);">إجمالي الأرباح:</span>
                                <strong>${formatNumber(userData?.totalEarned || 0)} USDT</strong>
                            </div>
                        </div>
                        
                        <button class="ios-button ios-button-danger mt-20" onclick="logout()">تسجيل الخروج</button>
                    </div>
                </div>
            `;
        }

        function renderNotificationsPage() {
            return `
                <div class="page-enter">
                    <div class="p-20 text-center">
                        <h2>الإشعارات</h2>
                    </div>
                    ${notifications.length > 0 ? notifications.map(notif => `
                        <div class="ios-card" style="${notif.read ? 'opacity:0.7;' : ''}">
                            <h4>${notif.title}</h4>
                            <p class="mt-5">${notif.body}</p>
                            <small style="color:var(--text-secondary); display:block; margin-top:10px;">${formatDate(notif.timestamp)}</small>
                        </div>
                    `).join('') : '<p class="text-center mt-20">لا توجد إشعارات</p>'}
                </div>
            `;
        }

        function switchPage(page) {
            currentPage = page;
            renderApp();
        }

        function showNotifications() {
            currentPage = 'notifications';
            renderApp();
            
            if (currentUser) {
                const notificationsRef = database.ref('users/' + currentUser.uid + '/notifications');
                notificationsRef.once('value').then(snapshot => {
                    const notifs = snapshot.val();
                    if (notifs) {
                        Object.keys(notifs).forEach(key => {
                            if (!notifs[key].read) {
                                database.ref('users/' + currentUser.uid + '/notifications/' + key).update({read: true});
                            }
                        });
                    }
                });
            }
        }

        function copyReferralLink() {
            const link = `https://exploitation.kesug.com/${userData?.referralCode || ''}`;
            navigator.clipboard.writeText(link).then(() => {
                showToast('تم نسخ الرابط');
            }).catch(() => {
                const textArea = document.createElement('textarea');
                textArea.value = link;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                showToast('تم نسخ الرابط');
            });
        }

        function copyDepositAddress() {
            navigator.clipboard.writeText(depositAddress).then(() => {
                showToast('تم نسخ العنوان');
            });
        }

        function purchasePlan(planId) {
            const plan = investmentPlans.find(p => p.id === planId);
            if (!plan) return;
            
            if (userInvestments.some(inv => inv.planId === planId)) {
                showToast('لا يمكنك شراء نفس الخطة مرتين');
                return;
            }
            
            if ((userData?.balance || 0) < plan.price) {
                showToast('رصيدك غير كافي لشراء هذه الخطة');
                return;
            }
            
            showModal(`
                <h3 class="modal-title">تأكيد الشراء</h3>
                <div class="text-center mt-20">
                    <p style="font-size:18px; font-weight:700;">${plan.name}</p>
                    <p style="color:var(--text-secondary);">السعر: ${plan.price} USDT</p>
                    <p style="color:var(--success);">الربح اليومي: ${plan.dailyProfit} USDT</p>
                    <p style="color:var(--text-secondary);">المدة: ${plan.duration} يوم</p>
                </div>
                <div class="flex gap-10 mt-20">
                    <button class="ios-button" onclick="confirmPurchase('${plan.id}')">تأكيد الشراء</button>
                    <button class="ios-button ios-button-secondary" onclick="closeModal()">إلغاء</button>
                </div>
            `);
        }

        function confirmPurchase(planId) {
            const plan = investmentPlans.find(p => p.id === planId);
            if (!plan) return;
            
            if (userInvestments.some(inv => inv.planId === planId)) {
                showToast('لا يمكنك شراء نفس الخطة مرتين');
                closeModal();
                return;
            }
            
            if ((userData?.balance || 0) < plan.price) {
                showToast('رصيدك غير كافي');
                closeModal();
                return;
            }
            
            const newBalance = (userData.balance || 0) - plan.price;
            const investment = {
                id: generateUniqueId(),
                userId: currentUser.uid,
                planId: plan.id,
                planName: plan.name,
                price: plan.price,
                dailyProfit: plan.dailyProfit,
                duration: plan.duration,
                startTime: Date.now(),
                endTime: Date.now() + (plan.duration * PROFIT_INTERVAL),
                accumulatedProfit: 0,
                lastProfitTime: Date.now()
            };
            
            showLoading();
            
            database.ref('users/' + currentUser.uid).update({
                balance: newBalance,
                totalInvested: (userData.totalInvested || 0) + plan.price
            }).then(() => {
                return database.ref('investments/' + investment.id).set(investment);
            }).then(() => {
                logActivity(currentUser.uid, 'purchase', `شراء خطة ${plan.name}`, plan.price);
                
                hideLoading();
                closeModal();
                showToast('تم شراء الخطة بنجاح');
                renderApp();
            }).catch(error => {
                hideLoading();
                closeModal();
                showToast('فشل شراء الخطة');
                console.error('Purchase error:', error);
            });
        }

        function logout() {
            auth.signOut().then(() => {
                currentUser = null;
                userData = null;
                adminPage = null;
                localStorage.removeItem('userDeviceId');
                localStorage.removeItem('deviceWarnings');
                renderApp();
            });
        }

        // ============================================================
        // Admin Panel Functions
        // ============================================================
        function showAdminPanel() {
            adminPage = 'dashboard';
            renderApp();
        }

        function setAdminPage(page) {
            adminPage = page;
            renderApp();
        }

        function renderAdminPanel(app) {
            app.innerHTML = `
                <div class="admin-container">
                    <div class="admin-sidebar">
                        <h2 class="admin-title">لوحة التحكم</h2>
                        <div class="admin-grid">
                            <button class="admin-button ${adminPage === 'dashboard' ? 'active' : ''}" onclick="setAdminPage('dashboard')">الإحصائيات</button>
                            <button class="admin-button ${adminPage === 'users' ? 'active' : ''}" onclick="setAdminPage('users')">المستخدمين</button>
                            <button class="admin-button ${adminPage === 'topUsers' ? 'active' : ''}" onclick="setAdminPage('topUsers')">الأعلى رصيداً</button>
                            <button class="admin-button ${adminPage === 'plans' ? 'active' : ''}" onclick="setAdminPage('plans')">الخطط</button>
                            <button class="admin-button ${adminPage === 'notifications' ? 'active' : ''}" onclick="setAdminPage('notifications')">الإشعارات</button>
                            <button class="admin-button ${adminPage === 'blocked' ? 'active' : ''}" onclick="setAdminPage('blocked')">المحظورون</button>
                            <button class="admin-button ${adminPage === 'logs' ? 'active' : ''}" onclick="setAdminPage('logs')">السجلات</button>
                            <button class="admin-button ${adminPage === 'chats' ? 'active' : ''}" onclick="setAdminPage('chats')">المحادثات</button>
                            <button class="admin-button ${adminPage === 'withdrawals' ? 'active' : ''}" onclick="setAdminPage('withdrawals')">السحوبات</button>
                            <button class="admin-button ${adminPage === 'settings' ? 'active' : ''}" onclick="setAdminPage('settings')">الإعدادات</button>
                            <button class="admin-button ${adminPage === 'appeals' ? 'active' : ''}" onclick="setAdminPage('appeals')">الطعون</button>
                        </div>
                        <button class="ios-button ios-button-secondary mt-20" onclick="logout()">تسجيل الخروج</button>
                    </div>
                    <div id="adminContent" style="margin-top:20px; color:white;">
                        <div class="spinner"></div>
                    </div>
                </div>
            `;
            
            setTimeout(() => loadAdminContent(), 100);
        }

        function loadAdminContent() {
            const content = document.getElementById('adminContent');
            if (!content) return;
            
            switch (adminPage) {
                case 'dashboard': loadAdminDashboard(content); break;
                case 'users': loadAdminUsers(content); break;
                case 'topUsers': loadTopUsers(content); break;
                case 'plans': loadAdminPlans(content); break;
                case 'notifications': loadAdminNotifications(content); break;
                case 'blocked': loadAdminBlocked(content); break;
                case 'logs': loadAdminLogs(content); break;
                case 'chats': loadAdminChats(content); break;
                case 'withdrawals': loadAdminWithdrawals(content); break;
                case 'settings': loadAdminSettings(content); break;
                case 'appeals': loadAdminAppeals(content); break;
            }
        }

        function loadAdminDashboard(content) {
            Promise.all([
                database.ref('users').once('value'),
                database.ref('investments').once('value'),
                database.ref('withdrawals').once('value'),
                database.ref('activities').once('value'),
                database.ref('appeals').once('value')
            ]).then(([usersSnap, invSnap, withSnap, actSnap, appSnap]) => {
                const users = usersSnap.val() || {};
                const investments = invSnap.val() || {};
                const withdrawals = withSnap.val() || {};
                const activities = actSnap.val() || {};
                const appeals = appSnap.val() || {};
                
                const totalUsers = Object.keys(users).length;
                const activeUsers = Object.values(users).filter(u => !u.isBlocked).length;
                const blockedUsers = totalUsers - activeUsers;
                const totalInvested = Object.values(investments).reduce((sum, inv) => sum + (inv.price || 0), 0);
                const pendingWithdrawals = Object.values(withdrawals).filter(w => w.status === 'pending').length;
                const totalActivities = Object.keys(activities).length;
                const pendingAppeals = Object.values(appeals).filter(a => a.status === 'pending').length;
                const activePercentage = totalUsers > 0 ? (activeUsers / totalUsers * 100) : 0;
                
                content.innerHTML = `
                    <div class="ios-card" style="color:var(--text);">
                        <h3 class="text-center mb-20">إحصائيات المنصة</h3>
                        
                        <div class="circular-progress" style="background: conic-gradient(var(--primary) ${activePercentage}%, #E5E5EA 0%);">
                            <div class="circular-progress-value">${activePercentage.toFixed(1)}%</div>
                        </div>
                        <p class="text-center mb-20">نسبة المستخدمين النشطين</p>
                        
                        <div class="admin-stats-grid">
                            <div class="admin-stat-card">
                                <div class="admin-stat-icon">👥</div>
                                <div class="admin-stat-value">${totalUsers}</div>
                                <div class="admin-stat-label">إجمالي المستخدمين</div>
                            </div>
                            <div class="admin-stat-card">
                                <div class="admin-stat-icon">✅</div>
                                <div class="admin-stat-value" style="color:var(--success);">${activeUsers}</div>
                                <div class="admin-stat-label">نشطين</div>
                            </div>
                            <div class="admin-stat-card">
                                <div class="admin-stat-icon">🚫</div>
                                <div class="admin-stat-value" style="color:var(--danger);">${blockedUsers}</div>
                                <div class="admin-stat-label">محظورين</div>
                            </div>
                            <div class="admin-stat-card">
                                <div class="admin-stat-icon">💰</div>
                                <div class="admin-stat-value">${formatNumber(totalInvested)}</div>
                                <div class="admin-stat-label">الاستثمارات</div>
                            </div>
                            <div class="admin-stat-card">
                                <div class="admin-stat-icon">💳</div>
                                <div class="admin-stat-value" style="color:var(--warning);">${pendingWithdrawals}</div>
                                <div class="admin-stat-label">سحوبات معلقة</div>
                            </div>
                            <div class="admin-stat-card">
                                <div class="admin-stat-icon">📊</div>
                                <div class="admin-stat-value">${totalActivities}</div>
                                <div class="admin-stat-label">الحركات</div>
                            </div>
                            <div class="admin-stat-card">
                                <div class="admin-stat-icon">📝</div>
                                <div class="admin-stat-value" style="color:var(--warning);">${pendingAppeals}</div>
                                <div class="admin-stat-label">طعون</div>
                            </div>
                        </div>
                    </div>
                `;
            });
        }

        function loadAdminUsers(content) {
            database.ref('users').once('value').then(snapshot => {
                const users = snapshot.val() || {};
                const usersList = Object.keys(users).map(userId => {
                    return renderUserCard(userId, users[userId]);
                }).join('');
                
                content.innerHTML = `
                    <div class="ios-card" style="color:var(--text);">
                        <div class="flex-between mb-10">
                            <h3>المستخدمين (${Object.keys(users).length})</h3>
                            <input type="text" class="ios-input" placeholder="بحث..." style="width:200px;" oninput="searchUsersInAdmin(this.value)">
                        </div>
                        <div id="usersList">${usersList}</div>
                    </div>
                `;
            });
        }

        function renderUserCard(userId, user) {
            return `
                <div class="ios-card" style="color:var(--text);">
                    <div class="flex-between">
                        <h4>${user.name} ${user.isBlocked ? '<span style="color:var(--danger); font-size:12px;">(محظور)</span>' : ''}</h4>
                        <span style="font-size:12px; color:var(--text-secondary);">${formatDate(user.createdAt)}</span>
                    </div>
                    <p class="mt-5">${user.email} | ${user.phone}</p>
                    <p class="mt-5">الرصيد: <strong>${formatNumber(user.balance || 0)} USDT</strong></p>
                    <div class="action-buttons">
                        ${user.isBlocked ? 
                            `<button class="action-btn action-btn-unblock" onclick="toggleUserBlock('${userId}', false)">فك الحظر</button>` :
                            `<button class="action-btn action-btn-block" onclick="toggleUserBlock('${userId}', true)">حظر</button>`
                        }
                        <button class="action-btn action-btn-view" onclick="viewUserActivity('${userId}')">سجل الحركات</button>
                        <button class="action-btn action-btn-edit" onclick="editUserBalance('${userId}', ${user.balance || 0})">تعديل الرصيد</button>
                        <button class="action-btn action-btn-send" onclick="sendUserNotification('${userId}')">إرسال رسالة</button>
                        <button class="action-btn action-btn-delete" onclick="deleteUser('${userId}')">حذف نهائي</button>
                    </div>
                </div>
            `;
        }

        function searchUsersInAdmin(query) {
            if (!query) {
                loadAdminContent();
                return;
            }
            
            database.ref('users').once('value').then(snapshot => {
                const users = snapshot.val() || {};
                const filtered = Object.keys(users).filter(userId => {
                    const user = users[userId];
                    return user.name.includes(query) || user.email.includes(query) || user.phone.includes(query);
                });
                
                const usersList = filtered.map(userId => renderUserCard(userId, users[userId])).join('');
                document.getElementById('usersList').innerHTML = usersList || '<p>لا توجد نتائج</p>';
            });
        }

        function loadTopUsers(content) {
            database.ref('users').orderByChild('balance').limitToLast(25).once('value').then(snapshot => {
                const users = snapshot.val() || {};
                const sortedUsers = Object.keys(users).reverse();
                
                const usersList = sortedUsers.map((userId, index) => {
                    const user = users[userId];
                    return `
                        <div class="ios-card" style="color:var(--text);">
                            <div class="flex-between">
                                <h4>#${index + 1} - ${user.name}</h4>
                                <strong style="color:var(--primary);">${formatNumber(user.balance || 0)} USDT</strong>
                            </div>
                            <p>${user.email} | ${user.phone}</p>
                            <div class="action-buttons">
                                ${user.isBlocked ? 
                                    `<button class="action-btn action-btn-unblock" onclick="toggleUserBlock('${userId}', false)">فك الحظر</button>` :
                                    `<button class="action-btn action-btn-block" onclick="toggleUserBlock('${userId}', true)">حظر</button>`
                                }
                                <button class="action-btn action-btn-view" onclick="viewUserActivity('${userId}')">سجل</button>
                                <button class="action-btn action-btn-edit" onclick="editUserBalance('${userId}', ${user.balance || 0})">رصيد</button>
                                <button class="action-btn action-btn-send" onclick="sendUserNotification('${userId}')">رسالة</button>
                                <button class="action-btn action-btn-delete" onclick="deleteUser('${userId}')">حذف</button>
                            </div>
                        </div>
                    `;
                }).join('');
                
                content.innerHTML = `
                    <div class="ios-card" style="color:var(--text);">
                        <h3>أعلى 25 مستخدم رصيداً</h3>
                        <div class="mt-10">${usersList}</div>
                    </div>
                `;
            });
        }

        function loadAdminPlans(content) {
            database.ref('plans').once('value').then(snapshot => {
                const plans = snapshot.val() || {};
                const plansList = Object.keys(plans).map(planId => {
                    const plan = plans[planId];
                    return `
                        <div class="ios-card" style="color:var(--text);">
                            <h4>${plan.name}</h4>
                            <p>السعر: ${plan.price} | الربح: ${plan.dailyProfit} | المدة: ${plan.duration}</p>
                            <button class="ios-button ios-button-danger mt-10" style="width:auto;" onclick="deletePlan('${planId}')">حذف</button>
                        </div>
                    `;
                }).join('');
                
                content.innerHTML = `
                    <div class="ios-card" style="color:var(--text);">
                        <h3>إضافة خطة</h3>
                        <form id="addPlanForm">
                            <input type="text" id="planName" class="ios-input" placeholder="اسم الخطة" required style="margin:10px 0;">
                            <input type="number" id="planPrice" class="ios-input" placeholder="السعر" required style="margin:10px 0;">
                            <input type="number" id="planDailyProfit" class="ios-input" placeholder="الربح اليومي" required style="margin:10px 0;">
                            <input type="number" id="planDuration" class="ios-input" placeholder="المدة" required style="margin:10px 0;">
                            <button type="submit" class="ios-button">إضافة</button>
                        </form>
                    </div>
                    <div class="mt-20">${plansList}</div>
                `;
                
                document.getElementById('addPlanForm').addEventListener('submit', (e) => {
                    e.preventDefault();
                    const plan = {
                        id: generateUniqueId(),
                        name: document.getElementById('planName').value,
                        price: parseFloat(document.getElementById('planPrice').value),
                        dailyProfit: parseFloat(document.getElementById('planDailyProfit').value),
                        duration: parseInt(document.getElementById('planDuration').value),
                        totalProfit: parseFloat(document.getElementById('planDailyProfit').value) * parseInt(document.getElementById('planDuration').value)
                    };
                    
                    database.ref('plans/' + plan.id).set(plan).then(() => {
                        showToast('تمت الإضافة');
                        loadAdminPlans(content);
                    });
                });
            });
        }

        function deletePlan(planId) {
            database.ref('plans/' + planId).remove().then(() => {
                showToast('تم الحذف');
                loadAdminContent();
            });
        }

        function loadAdminNotifications(content) {
            content.innerHTML = `
                <div class="ios-card" style="color:var(--text);">
                    <h3>إرسال إشعار</h3>
                    <form id="sendNotificationForm">
                        <input type="text" id="notificationTitle" class="ios-input" placeholder="العنوان" required style="margin:10px 0;">
                        <textarea id="notificationBody" class="ios-textarea" placeholder="النص" required style="margin:10px 0;"></textarea>
                        <button type="submit" class="ios-button">إرسال للجميع</button>
                    </form>
                </div>
            `;
            
            document.getElementById('sendNotificationForm').addEventListener('submit', (e) => {
                e.preventDefault();
                const title = document.getElementById('notificationTitle').value;
                const body = document.getElementById('notificationBody').value;
                
                database.ref('users').once('value').then(snapshot => {
                    const users = snapshot.val() || {};
                    Object.keys(users).forEach(userId => {
                        database.ref('users/' + userId + '/notifications').push({
                            title, body, timestamp: Date.now(), read: false
                        });
                    });
                    showToast('تم الإرسال');
                });
            });
        }

        function loadAdminBlocked(content) {
            database.ref('users').orderByChild('isBlocked').equalTo(true).once('value').then(snapshot => {
                const users = snapshot.val() || {};
                const blockedList = Object.keys(users).map(userId => {
                    const user = users[userId];
                    return `
                        <div class="ios-card" style="color:var(--text);">
                            <h4>${user.name}</h4>
                            <p>${user.email}</p>
                            <p style="color:var(--danger);">${user.blockReason || 'غير محدد'}</p>
                            <div class="action-buttons">
                                <button class="action-btn action-btn-unblock" onclick="toggleUserBlock('${userId}', false)">فك الحظر</button>
                                <button class="action-btn action-btn-view" onclick="viewUserActivity('${userId}')">سجل</button>
                            </div>
                        </div>
                    `;
                }).join('');
                
                content.innerHTML = `
                    <div class="ios-card" style="color:var(--text);">
                        <h3>المحظورون</h3>
                        <input type="text" class="ios-input mt-10" placeholder="بحث..." oninput="searchBlockedUsers(this.value)">
                        <div id="blockedUsersList">${blockedList || '<p class="text-center">لا يوجد</p>'}</div>
                    </div>
                `;
            });
        }

        function searchBlockedUsers(query) {
            if (!query) {
                loadAdminContent();
                return;
            }
            
            database.ref('users').orderByChild('isBlocked').equalTo(true).once('value').then(snapshot => {
                const users = snapshot.val() || {};
                const filtered = Object.keys(users).filter(userId => {
                    const user = users[userId];
                    return user.name.includes(query) || user.email.includes(query);
                });
                
                const blockedList = filtered.map(userId => {
                    const user = users[userId];
                    return `
                        <div class="ios-card" style="color:var(--text);">
                            <h4>${user.name}</h4>
                            <p>${user.email}</p>
                            <p style="color:var(--danger);">${user.blockReason || 'غير محدد'}</p>
                            <div class="action-buttons">
                                <button class="action-btn action-btn-unblock" onclick="toggleUserBlock('${userId}', false)">فك الحظر</button>
                                <button class="action-btn action-btn-view" onclick="viewUserActivity('${userId}')">سجل</button>
                            </div>
                        </div>
                    `;
                }).join('');
                
                document.getElementById('blockedUsersList').innerHTML = blockedList || '<p>لا توجد نتائج</p>';
            });
        }

        function loadAdminLogs(content) {
            database.ref('activities').limitToLast(100).once('value').then(snapshot => {
                const activities = snapshot.val() || {};
                const logs = Object.values(activities).reverse().map(activity => `
                    <div class="ios-card" style="color:var(--text);">
                        <p class="font-bold">${activity.description}</p>
                        <small>${formatDate(activity.timestamp)}</small>
                    </div>
                `).join('');
                
                content.innerHTML = `
                    <div class="ios-card" style="color:var(--text);">
                        <div class="flex-between">
                            <h3>السجلات</h3>
                            <button class="ios-button ios-button-danger" style="width:auto; font-size:12px;" onclick="clearAllLogs()">مسح السجلات</button>
                        </div>
                        <div class="mt-10">${logs || '<p class="text-center">لا توجد سجلات</p>'}</div>
                    </div>
                `;
            });
        }

        function clearAllLogs() {
            if (confirm('هل أنت متأكد من مسح جميع السجلات؟')) {
                database.ref('activities').remove().then(() => {
                    showToast('تم مسح السجلات');
                    loadAdminContent();
                });
            }
        }

        function loadAdminChats(content) {
            database.ref('supportMessages').once('value').then(snapshot => {
                const messages = snapshot.val() || {};
                const userChats = {};
                
                Object.values(messages).forEach(msg => {
                    const otherId = msg.senderId === currentUser.uid ? msg.receiverId : msg.senderId;
                    if (!userChats[otherId]) {
                        userChats[otherId] = {
                            messages: [],
                            hasAdminReply: false
                        };
                    }
                    userChats[otherId].messages.push(msg);
                    if (msg.senderId === currentUser.uid) {
                        userChats[otherId].hasAdminReply = true;
                    }
                });
                
                const filteredChats = Object.keys(userChats).filter(userId => {
                    if (chatFilter === 'pending') {
                        return !userChats[userId].hasAdminReply;
                    } else {
                        return userChats[userId].hasAdminReply;
                    }
                });
                
                const chatList = filteredChats.map(userId => {
                    const userChat = userChats[userId];
                    const lastMessage = userChat.messages[userChat.messages.length - 1];
                    
                    return `
                        <div class="ios-card" style="color:var(--text); cursor:pointer;" onclick="openChatWithUser('${userId}')">
                            <h4>${lastMessage.senderName || 'مستخدم'}</h4>
                            <p>${lastMessage.text}</p>
                            <small>${formatDate(lastMessage.timestamp)}</small>
                            <button class="ios-button mt-10">فتح المحادثة</button>
                        </div>
                    `;
                }).join('');
                
                content.innerHTML = `
                    <div class="ios-card" style="color:var(--text);">
                        <h3>المحادثات</h3>
                        <div class="flex gap-10 mb-10">
                            <button class="ios-button ${chatFilter === 'pending' ? 'ios-button-warning' : 'ios-button-secondary'}" style="width:auto;" onclick="setChatFilter('pending')">المعلقة</button>
                            <button class="ios-button ${chatFilter === 'replied' ? 'ios-button-success' : 'ios-button-secondary'}" style="width:auto;" onclick="setChatFilter('replied')">تم الرد</button>
                        </div>
                        ${chatList || '<p class="text-center">لا توجد محادثات</p>'}
                    </div>
                `;
            });
        }

        function setChatFilter(filter) {
            chatFilter = filter;
            loadAdminContent();
        }

        function openChatWithUser(userId) {
            database.ref('users/' + userId).once('value').then(userSnapshot => {
                const user = userSnapshot.val();
                
                database.ref('supportMessages').once('value').then(snapshot => {
                    const messages = snapshot.val() || {};
                    const userMessages = Object.values(messages).filter(msg => 
                        msg.senderId === userId || msg.receiverId === userId
                    );
                    
                    const chatContent = userMessages.map(msg => `
                        <div class="chat-message ${msg.senderId === userId ? 'received' : 'sent'}">
                            ${msg.text}
                            <br><small>${formatDate(msg.timestamp)}</small>
                        </div>
                    `).join('');
                    
                    showModal(`
                        <h3 class="modal-title">${user?.name || 'مستخدم'}</h3>
                        
                        <div class="action-buttons mb-10">
                            ${user?.isBlocked ? 
                                `<button class="action-btn action-btn-unblock" onclick="toggleUserBlock('${userId}', false)">فك الحظر</button>` :
                                `<button class="action-btn action-btn-block" onclick="toggleUserBlock('${userId}', true)">حظر</button>`
                            }
                            <button class="action-btn action-btn-view" onclick="viewUserActivity('${userId}')">سجل الحركات</button>
                            <button class="action-btn action-btn-edit" onclick="editUserBalance('${userId}', ${user?.balance || 0})">تعديل الرصيد</button>
                            <button class="action-btn action-btn-send" onclick="sendUserNotification('${userId}')">إرسال رسالة</button>
                            <button class="action-btn action-btn-delete" onclick="deleteUser('${userId}')">حذف المستخدم</button>
                            <button class="action-btn action-btn-copy" onclick="copyUserEmail('${userId}')">نسخ الإيميل</button>
                        </div>
                        
                        <div style="max-height:300px; overflow-y:auto; margin:10px 0; background:#F8F8F8; padding:15px; border-radius:10px;">
                            ${chatContent || '<p class="text-center">لا توجد رسائل</p>'}
                        </div>
                        
                        <form id="adminReplyForm">
                            <input type="text" id="adminReplyInput" class="ios-input" placeholder="اكتب ردك..." required>
                            <div class="flex gap-10 mt-10">
                                <button type="submit" class="ios-button">إرسال الرد</button>
                                <button type="button" class="ios-button ios-button-danger" style="width:auto;" onclick="deleteChat('${userId}')">حذف المحادثة</button>
                            </div>
                        </form>
                    `);
                    
                    document.getElementById('adminReplyForm').addEventListener('submit', (e) => {
                        e.preventDefault();
                        const replyText = document.getElementById('adminReplyInput').value.trim();
                        
                        if (replyText) {
                            database.ref('supportMessages').push({
                                senderId: currentUser.uid,
                                senderName: 'الدعم الفني',
                                receiverId: userId,
                                text: replyText,
                                timestamp: Date.now()
                            }).then(() => {
                                showToast('تم الإرسال');
                                closeModal();
                                loadAdminContent();
                            });
                        }
                    });
                });
            });
        }

        function deleteChat(userId) {
            if (confirm('هل تريد حذف جميع رسائل هذه المحادثة؟')) {
                database.ref('supportMessages').once('value').then(snapshot => {
                    const messages = snapshot.val() || {};
                    Object.keys(messages).forEach(key => {
                        if (messages[key].senderId === userId || messages[key].receiverId === userId) {
                            database.ref('supportMessages/' + key).remove();
                        }
                    });
                    
                    showToast('تم حذف المحادثة');
                    closeModal();
                    loadAdminContent();
                });
            }
        }

        function loadAdminWithdrawals(content) {
            database.ref('withdrawals').once('value').then(snapshot => {
                const withdrawals = snapshot.val() || {};
                const filtered = Object.keys(withdrawals).filter(id => {
                    if (withdrawalFilter === 'pending') {
                        return withdrawals[id].status === 'pending';
                    } else {
                        return withdrawals[id].status === 'approved';
                    }
                });
                
                const withdrawalList = filtered.map(withdrawalId => {
                    const w = withdrawals[withdrawalId];
                    
                    return `
                        <div class="ios-card" style="color:var(--text);">
                            <h4>${w.userName}</h4>
                            <p>المبلغ: ${formatNumber(w.amount)} USDT</p>
                            <p>العنوان: ${w.address}</p>
                            <div class="action-buttons">
                                <button class="action-btn action-btn-copy" onclick="copyWithdrawalAddress('${w.address}')">نسخ العنوان</button>
                                <button class="action-btn action-btn-copy" onclick="copyUserEmail('${w.userId}')">نسخ الإيميل</button>
                                ${w.status === 'pending' ? `
                                <button class="action-btn action-btn-unblock" onclick="processWithdrawal('${withdrawalId}', 'approved')">موافقة</button>
                                <button class="action-btn action-btn-block" onclick="processWithdrawal('${withdrawalId}', 'rejected')">رفض</button>
                                ` : ''}
                            </div>
                        </div>
                    `;
                }).join('');
                
                content.innerHTML = `
                    <div class="ios-card" style="color:var(--text);">
                        <h3>طلبات السحب</h3>
                        <div class="flex gap-10 mb-10">
                            <button class="ios-button ${withdrawalFilter === 'pending' ? 'ios-button-warning' : 'ios-button-secondary'}" style="width:auto;" onclick="setWithdrawalFilter('pending')">المعلقة</button>
                            <button class="ios-button ${withdrawalFilter === 'approved' ? 'ios-button-success' : 'ios-button-secondary'}" style="width:auto;" onclick="setWithdrawalFilter('approved')">الموافق عليها</button>
                        </div>
                        <input type="text" class="ios-input mb-10" placeholder="بحث..." oninput="searchWithdrawals(this.value)">
                        <div id="withdrawalsList">${withdrawalList || '<p class="text-center">لا توجد طلبات</p>'}</div>
                    </div>
                `;
            });
        }

        function setWithdrawalFilter(filter) {
            withdrawalFilter = filter;
            loadAdminContent();
        }

        function copyWithdrawalAddress(address) {
            navigator.clipboard.writeText(address).then(() => showToast('تم النسخ'));
        }

        function copyUserEmail(userId) {
            database.ref('users/' + userId).once('value').then(snapshot => {
                const user = snapshot.val();
                if (user && user.email) {
                    navigator.clipboard.writeText(user.email).then(() => showToast('تم نسخ الإيميل'));
                }
            });
        }

        function searchWithdrawals(query) {
            if (!query) return;
            database.ref('withdrawals').once('value').then(snapshot => {
                const withdrawals = snapshot.val() || {};
                const filtered = Object.keys(withdrawals).filter(id => {
                    const w = withdrawals[id];
                    return w.userName.includes(query) || w.address.includes(query);
                });
                
                const list = filtered.map(id => {
                    const w = withdrawals[id];
                    return `
                        <div class="ios-card" style="color:var(--text);">
                            <h4>${w.userName}</h4>
                            <p>${w.amount} USDT</p>
                            <p>${w.address}</p>
                        </div>
                    `;
                }).join('');
                
                document.getElementById('withdrawalsList').innerHTML = list || '<p>لا توجد نتائج</p>';
            });
        }

        function processWithdrawal(withdrawalId, status) {
            database.ref('withdrawals/' + withdrawalId).update({status}).then(() => {
                showToast('تمت المعالجة');
                loadAdminContent();
            });
        }

        function loadAdminSettings(content) {
            content.innerHTML = `
                <div class="ios-card" style="color:var(--text);">
                    <h3>الإعدادات</h3>
                    
                    <div class="mt-20">
                        <h4>عنوان TRON (TRC20):</h4>
                        <input type="text" id="depositAddressInput" class="ios-input" value="${depositAddress}" style="margin:10px 0;">
                        <button class="ios-button" onclick="updateDepositAddress()">تحديث العنوان</button>
                    </div>
                    
                    <div class="mt-20">
                        <h4>وضع الصيانة:</h4>
                        <label style="display:flex; align-items:center; gap:10px; cursor:pointer;">
                            <input type="checkbox" id="maintenanceModeCheckbox" ${maintenanceMode ? 'checked' : ''} onchange="toggleMaintenanceMode(this.checked)">
                            تفعيل وضع الصيانة
                        </label>
                    </div>
                    
                    <div class="mt-20">
                        <h4>إيقاف تسجيل الدخول:</h4>
                        <label style="display:flex; align-items:center; gap:10px; cursor:pointer;">
                            <input type="checkbox" id="loginEnabledCheckbox" ${!loginEnabled ? 'checked' : ''} onchange="toggleLoginEnabled(!this.checked)">
                            إيقاف تسجيل الدخول
                        </label>
                    </div>
                    
                    <div class="mt-20">
                        <h4>إيقاف إنشاء الحساب:</h4>
                        <label style="display:flex; align-items:center; gap:10px; cursor:pointer;">
                            <input type="checkbox" id="registrationEnabledCheckbox" ${!registrationEnabled ? 'checked' : ''} onchange="toggleRegistrationEnabled(!this.checked)">
                            إيقاف إنشاء الحساب
                        </label>
                    </div>
                    
                    <div class="mt-20">
                        <h4>حظر IP:</h4>
                        <input type="text" id="blockedIPInput" class="ios-input" placeholder="عنوان IP" style="margin:10px 0;">
                        <button class="ios-button ios-button-danger" onclick="blockIP()">حظر العنوان</button>
                        <div class="mt-10">
                            ${blockedIPs.length > 0 ? blockedIPs.map(ip => `
                                <div class="flex-between" style="background:#F0F0F5; padding:10px; border-radius:8px; margin:5px 0;">
                                    <span>${ip}</span>
                                    <button class="ios-button ios-button-danger" style="width:auto; font-size:11px;" onclick="unblockIP('${ip}')">إلغاء</button>
                                </div>
                            `).join('') : '<p>لا توجد عناوين محظورة</p>'}
                        </div>
                    </div>
                    
                    <div class="mt-20">
                        <h4>إضافة مشرف:</h4>
                        <input type="email" id="adminEmailInput" class="ios-input" placeholder="البريد الإلكتروني" style="margin:10px 0;">
                        <button class="ios-button" onclick="addAdmin()">إضافة مشرف</button>
                        <div class="mt-10">
                            ${admins.length > 0 ? admins.map(admin => `
                                <div class="flex-between" style="background:#F0F0F5; padding:10px; border-radius:8px; margin:5px 0;">
                                    <span>${admin}</span>
                                    ${admin !== ADMIN_EMAIL ? `<button class="ios-button ios-button-danger" style="width:auto; font-size:11px;" onclick="removeAdmin('${admin}')">حذف</button>` : '<span style="color:var(--primary); font-size:12px;">المشرف الرئيسي</span>'}
                                </div>
                            `).join('') : '<p>لا يوجد مشرفين إضافيين</p>'}
                        </div>
                    </div>
                </div>
            `;
        }

        function updateDepositAddress() {
            const address = document.getElementById('depositAddressInput').value.trim();
            if (address) {
                database.ref('settings').update({depositAddress: address}).then(() => {
                    depositAddress = address;
                    showToast('تم التحديث');
                });
            }
        }

        function toggleMaintenanceMode(enabled) {
            database.ref('settings').update({maintenanceMode: enabled}).then(() => {
                maintenanceMode = enabled;
                showToast(enabled ? 'تم التفعيل' : 'تم التعطيل');
            });
        }

        function toggleLoginEnabled(enabled) {
            database.ref('settings').update({loginEnabled: enabled}).then(() => {
                loginEnabled = enabled;
                showToast(enabled ? 'تم تفعيل تسجيل الدخول' : 'تم إيقاف تسجيل الدخول');
            });
        }

        function toggleRegistrationEnabled(enabled) {
            database.ref('settings').update({registrationEnabled: enabled}).then(() => {
                registrationEnabled = enabled;
                showToast(enabled ? 'تم تفعيل إنشاء الحساب' : 'تم إيقاف إنشاء الحساب');
            });
        }

        function blockIP() {
            const ip = document.getElementById('blockedIPInput').value.trim();
            if (ip) {
                database.ref('settings/blockedIPs').push(ip).then(() => {
                    blockedIPs.push(ip);
                    showToast('تم الحظر');
                    loadAdminContent();
                });
            }
        }

        function unblockIP(ip) {
            database.ref('settings/blockedIPs').once('value').then(snapshot => {
                const ips = snapshot.val() || {};
                Object.keys(ips).forEach(key => {
                    if (ips[key] === ip) {
                        database.ref('settings/blockedIPs/' + key).remove();
                    }
                });
                blockedIPs = blockedIPs.filter(bip => bip !== ip);
                showToast('تم إلغاء الحظر');
                loadAdminContent();
            });
        }

        function addAdmin() {
            const email = document.getElementById('adminEmailInput').value.trim();
            if (!validateEmail(email)) {
                showToast('بريد غير صالح');
                return;
            }
            
            database.ref('admins').push(email).then(() => {
                admins.push(email);
                
                database.ref('users').orderByChild('email').equalTo(email).once('value').then(snapshot => {
                    const users = snapshot.val();
                    if (users) {
                        const userId = Object.keys(users)[0];
                        database.ref('users/' + userId).update({isAdmin: true});
                    }
                });
                
                showToast('تم إضافة المشرف');
                loadAdminContent();
            });
        }

        function removeAdmin(email) {
            database.ref('admins').once('value').then(snapshot => {
                const adminsList = snapshot.val() || {};
                Object.keys(adminsList).forEach(key => {
                    if (adminsList[key] === email) {
                        database.ref('admins/' + key).remove();
                    }
                });
                admins = admins.filter(a => a !== email);
                
                database.ref('users').orderByChild('email').equalTo(email).once('value').then(snapshot => {
                    const users = snapshot.val();
                    if (users) {
                        const userId = Object.keys(users)[0];
                        if (email !== ADMIN_EMAIL) {
                            database.ref('users/' + userId).update({isAdmin: false});
                        }
                    }
                });
                
                showToast('تم حذف المشرف');
                loadAdminContent();
            });
        }

        function loadAdminAppeals(content) {
            database.ref('appeals').once('value').then(snapshot => {
                const appeals = snapshot.val() || {};
                const appealsList = Object.keys(appeals).map(appealId => {
                    const appeal = appeals[appealId];
                    return `
                        <div class="ios-card" style="color:var(--text);">
                            <h4>${appeal.userName}</h4>
                            <p>${appeal.reason}</p>
                            <small>${formatDate(appeal.timestamp)}</small>
                            <div class="action-buttons">
                                <button class="action-btn action-btn-unblock" onclick="processAppeal('${appealId}', 'approved')">قبول</button>
                                <button class="action-btn action-btn-block" onclick="processAppeal('${appealId}', 'rejected')">رفض</button>
                            </div>
                        </div>
                    `;
                }).join('');
                
                content.innerHTML = `
                    <div class="ios-card" style="color:var(--text);">
                        <h3>الطعون</h3>
                        ${appealsList || '<p class="text-center">لا توجد طعون</p>'}
                    </div>
                `;
            });
        }

        function processAppeal(appealId, status) {
            database.ref('appeals/' + appealId).update({status}).then(() => {
                showToast('تمت المعالجة');
                loadAdminContent();
            });
        }

        function toggleUserBlock(userId, shouldBlock) {
            database.ref('users/' + userId).update({
                isBlocked: shouldBlock,
                blockReason: shouldBlock ? 'حظر من المشرف' : null,
                blockTimestamp: shouldBlock ? Date.now() : null
            }).then(() => {
                showToast(shouldBlock ? 'تم الحظر' : 'تم فك الحظر');
                loadAdminContent();
            });
        }

        function viewUserActivity(userId) {
            database.ref('activities').orderByChild('userId').equalTo(userId).limitToLast(50).once('value').then(snapshot => {
                const activities = snapshot.val();
                let html = '<h3 class="modal-title">سجل حركات المستخدم</h3>';
                
                if (activities) {
                    html += Object.values(activities).reverse().map(activity => `
                        <div style="margin:10px 0; padding:10px; background:#F0F0F5; border-radius:8px;">
                            <p class="font-bold">${activity.description}</p>
                            <div class="flex-between">
                                <small style="color:var(--text-secondary);">${formatDate(activity.timestamp)}</small>
                                ${activity.amount ? `<small style="color:var(--primary); font-weight:600;">${activity.amount} USDT</small>` : ''}
                            </div>
                        </div>
                    `).join('');
                } else {
                    html += '<p class="text-center">لا توجد حركات</p>';
                }
                
                showModal(html);
            });
        }

        function editUserBalance(userId, currentBalance) {
            showModal(`
                <h3 class="modal-title">تعديل رصيد المستخدم</h3>
                <p>الرصيد الحالي: <strong>${formatNumber(currentBalance)} USDT</strong></p>
                <input type="number" id="newBalance" class="ios-input" value="${currentBalance}" step="0.01" style="margin:15px 0;">
                <div class="flex gap-10">
                    <button class="ios-button" onclick="updateUserBalance('${userId}')">تحديث الرصيد</button>
                    <button class="ios-button ios-button-secondary" onclick="closeModal()">إلغاء</button>
                </div>
            `);
        }

        function updateUserBalance(userId) {
            const newBalance = parseFloat(document.getElementById('newBalance').value);
            if (isNaN(newBalance) || newBalance < 0) {
                showToast('رصيد غير صالح');
                return;
            }
            
            database.ref('users/' + userId).update({
                balance: newBalance
            }).then(() => {
                database.ref('users/' + userId + '/notifications').push({
                    title: 'تحديث الرصيد',
                    body: `تم تحديث رصيدك إلى ${formatNumber(newBalance)} USDT`,
                    timestamp: Date.now(),
                    read: false
                });
                
                logActivity(userId, 'admin', `تعديل الرصيد إلى ${newBalance} USDT`, newBalance);
                showToast('تم تحديث الرصيد');
                closeModal();
                loadAdminContent();
            });
        }

        function sendUserNotification(userId) {
            showModal(`
                <h3 class="modal-title">إرسال رسالة للمستخدم</h3>
                <input type="text" id="userNotifTitle" class="ios-input" placeholder="عنوان الرسالة" style="margin:10px 0;">
                <textarea id="userNotifBody" class="ios-textarea" placeholder="نص الرسالة" style="margin:10px 0;"></textarea>
                <div class="flex gap-10">
                    <button class="ios-button" onclick="sendNotifToUser('${userId}')">إرسال</button>
                    <button class="ios-button ios-button-secondary" onclick="closeModal()">إلغاء</button>
                </div>
            `);
        }

        function sendNotifToUser(userId) {
            const title = document.getElementById('userNotifTitle').value.trim();
            const body = document.getElementById('userNotifBody').value.trim();
            
            if (!title || !body) {
                showToast('يرجى ملء جميع الحقول');
                return;
            }
            
            database.ref('users/' + userId + '/notifications').push({
                title, body, timestamp: Date.now(), read: false
            }).then(() => {
                logActivity(userId, 'admin', 'إرسال إشعار للمستخدم');
                showToast('تم إرسال الرسالة');
                closeModal();
            });
        }

        function deleteUser(userId) {
            showModal(`
                <h3 class="modal-title">تأكيد الحذف النهائي</h3>
                <p class="text-center">هل أنت متأكد من حذف هذا المستخدم نهائياً؟</p>
                <p class="text-center" style="color:var(--danger); font-weight:700;">لا يمكن التراجع عن هذا الإجراء</p>
                <div class="flex gap-10 mt-20">
                    <button class="ios-button ios-button-danger" onclick="confirmDeleteUser('${userId}')">حذف نهائي</button>
                    <button class="ios-button ios-button-secondary" onclick="closeModal()">إلغاء</button>
                </div>
            `);
        }

        function confirmDeleteUser(userId) {
            database.ref('users/' + userId).remove().then(() => {
                database.ref('investments').orderByChild('userId').equalTo(userId).once('value').then(snapshot => {
                    const investments = snapshot.val();
                    if (investments) {
                        Object.keys(investments).forEach(key => {
                            database.ref('investments/' + key).remove();
                        });
                    }
                });
                
                database.ref('referrals/' + userId).remove();
                database.ref('activities').orderByChild('userId').equalTo(userId).once('value').then(snapshot => {
                    const activities = snapshot.val();
                    if (activities) {
                        Object.keys(activities).forEach(key => {
                            database.ref('activities/' + key).remove();
                        });
                    }
                });
                
                logActivity(userId, 'admin', 'حذف المستخدم نهائياً');
                showToast('تم حذف المستخدم');
                closeModal();
                loadAdminContent();
            });
        }

        // ============================================================
        // Event Delegation
        // ============================================================
        document.addEventListener('submit', function(e) {
            if (e.target.id === 'supportForm') {
                e.preventDefault();
                const input = document.getElementById('supportInput');
                const message = input.value.trim();
                
                if (message && currentUser) {
                    database.ref('supportMessages').push({
                        senderId: currentUser.uid,
                        senderName: userData.name,
                        receiverId: 'admin',
                        text: message,
                        timestamp: Date.now()
                    }).then(() => {
                        input.value = '';
                        database.ref('supportMessages').once('value').then(snapshot => {
                            supportMessages = snapshot.val() ? Object.values(snapshot.val()) : [];
                            renderApp();
                        });
                    });
                }
            }
            
            if (e.target.id === 'withdrawalForm') {
                e.preventDefault();
                const amount = parseFloat(document.getElementById('withdrawalAmount').value);
                const address = document.getElementById('withdrawalAddress').value.trim();
                
                if (amount < MIN_WITHDRAWAL) {
                    showToast(`الحد الأدنى ${MIN_WITHDRAWAL} USDT`);
                    return;
                }
                
                if (!validateTronAddress(address)) {
                    showToast('عنوان TRON غير صالح');
                    return;
                }
                
                if (amount > (userData.balance || 0)) {
                    showToast('رصيد غير كافي');
                    return;
                }
                
                const lastWithdrawal = userData.lastWithdrawal || 0;
                if (Date.now() - lastWithdrawal < WITHDRAWAL_COOLDOWN) {
                    showToast('يمكنك السحب مرة واحدة كل 24 ساعة');
                    return;
                }
                
                database.ref('withdrawals').push({
                    userId: currentUser.uid,
                    userName: userData.name,
                    amount,
                    address,
                    status: 'pending',
                    timestamp: Date.now()
                }).then(() => {
                    database.ref('users/' + currentUser.uid).update({
                        balance: (userData.balance || 0) - amount,
                        lastWithdrawal: Date.now()
                    });
                    
                    logActivity(currentUser.uid, 'withdrawal', `طلب سحب ${amount} USDT`, amount);
                    showToast('تم تقديم الطلب');
                    renderApp();
                });
            }
        });

        // ============================================================
        // Initialize Listeners
        // ============================================================
        function initializeListeners() {
            database.ref('plans').on('value', (snapshot) => {
                investmentPlans = snapshot.val() ? Object.values(snapshot.val()) : [];
                if (currentUser && !userData?.isAdmin) renderApp();
            });

            database.ref('investments').on('value', (snapshot) => {
                if (currentUser) {
                    const investments = snapshot.val();
                    userInvestments = investments ? Object.values(investments).filter(inv => inv.userId === currentUser.uid) : [];
                    
                    userInvestments.forEach(inv => {
                        if (Date.now() > inv.endTime) {
                            database.ref('investments/' + inv.id).remove();
                        }
                    });
                    
                    if (!userData?.isAdmin) renderApp();
                }
            });

            database.ref('supportMessages').on('value', (snapshot) => {
                supportMessages = snapshot.val() ? Object.values(snapshot.val()) : [];
                if (currentUser && (currentPage === 'support' || adminPage === 'chats')) renderApp();
            });

            database.ref('settings').on('value', (snapshot) => {
                const settings = snapshot.val();
                if (settings) {
                    depositAddress = settings.depositAddress || '';
                    maintenanceMode = settings.maintenanceMode || false;
                    blockedIPs = settings.blockedIPs ? Object.values(settings.blockedIPs) : [];
                    privacyPolicy = settings.privacyPolicy || '';
                    loginEnabled = settings.loginEnabled !== undefined ? settings.loginEnabled : true;
                    registrationEnabled = settings.registrationEnabled !== undefined ? settings.registrationEnabled : true;
                }
            });

            database.ref('admins').on('value', (snapshot) => {
                const adminsList = snapshot.val();
                admins = adminsList ? Object.values(adminsList) : [];
            });
        }

        initializeListeners();
        protectAgainstTimeManipulation();
        setInterval(protectAgainstTimeManipulation, 60000);
        setInterval(validateSession, SESSION_CHECK_INTERVAL);
        setInterval(cleanupOldActivities, 60 * 60 * 1000);

        // ============================================================
        // Auth State Observer
        // ============================================================
        auth.onAuthStateChanged(async (user) => {
            if (user) {
                currentUser = user;
                
                if (!validateSession()) return;
                
                const userSnapshot = await database.ref('users/' + user.uid).once('value');
                userData = userSnapshot.val();
                
                if (userData && userData.isBlocked) {
                    renderApp();
                    return;
                }
                
                if (userData) {
                    await database.ref('users/' + user.uid).update({
                        lastLogin: Date.now()
                    });
                    
                    if (userData.isAdmin || admins.includes(userData.email)) {
                        userData.isAdmin = true;
                    }
                }
                
                const notificationsSnapshot = await database.ref('users/' + user.uid + '/notifications').once('value');
                notifications = notificationsSnapshot.val() ? Object.values(notificationsSnapshot.val()) : [];
                
                loadReferredUsers();
                renderApp();
            } else {
                currentUser = null;
                userData = null;
                adminPage = null;
                renderApp();
            }
        });

        // ============================================================
        // Countdown Timer Update
        // ============================================================
        setInterval(() => {
            if (currentUser && !userData?.isAdmin && currentPage === 'home') {
                const countdownElement = document.getElementById('profitCountdown');
                if (countdownElement && userData?.lastProfitClaim) {
                    const remaining = (userData.lastProfitClaim + PROFIT_INTERVAL) - Date.now();
                    if (remaining <= 0) {
                        countdownElement.textContent = 'جاهز للاستلام';
                        const claimButton = document.getElementById('claimButton');
                        if (claimButton) {
                            claimButton.disabled = false;
                            claimButton.textContent = 'استلام أرباحك اليومية';
                        }
                    } else {
                        countdownElement.textContent = formatCountdown(userData.lastProfitClaim + PROFIT_INTERVAL);
                    }
                }
            }
        }, 1000);

        // ============================================================
        // Initial Render
        // ============================================================
        renderApp();
    </script>
</body>
</html>
