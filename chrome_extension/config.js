// ============================================
// YTB Extension Configuration
// ============================================
// The extension will automatically detect which server to use:
// - If localhost:5000 is running → uses local server
// - If localhost is down → uses Render server
// ============================================

const CONFIG = {
    // Local development server
    LOCAL_URL: 'http://localhost:5000',
    
    // Production server (Render)
    PRODUCTION_URL: 'https://ytb-wjja.onrender.com',
    
    // This will be set automatically after detection
    SERVER_URL: null,
    
    // Version for tracking
    VERSION: '1.1',
    
    // Polling interval for download progress (ms)
    POLL_INTERVAL: 1000,
    
    // Message display time after completion (ms)
    SUCCESS_MESSAGE_DURATION: 5000
};

// Auto-detect which server to use
async function detectServer() {
    // Try localhost first (for developers)
    try {
        const response = await fetch(`${CONFIG.LOCAL_URL}/health`, {
            method: 'GET',
            signal: AbortSignal.timeout(2000) // 2 second timeout
        });
        if (response.ok) {
            CONFIG.SERVER_URL = CONFIG.LOCAL_URL;
            console.log('✓ Using LOCAL server:', CONFIG.SERVER_URL);
            return CONFIG.LOCAL_URL;
        }
    } catch (e) {
        // Localhost not available, try production
    }
    
    // Fall back to Render production server
    CONFIG.SERVER_URL = CONFIG.PRODUCTION_URL;
    console.log('✓ Using PRODUCTION server:', CONFIG.SERVER_URL);
    return CONFIG.PRODUCTION_URL;
}
