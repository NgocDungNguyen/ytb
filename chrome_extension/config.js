// ============================================
// YTB Extension Configuration
// ============================================
// IMPORTANT: Update SERVER_URL before publishing to Chrome Web Store!
// 
// For LOCAL development (testing on your PC):
//   const SERVER_URL = 'http://localhost:5000';
//
// For PRODUCTION (after deploying to Render):
//   const SERVER_URL = 'https://your-app-name.onrender.com';
// ============================================

const CONFIG = {
    // Change this URL to your Render deployment URL before publishing!
    // Example: 'https://ytb-server.onrender.com'
    SERVER_URL: 'http://localhost:5000',
    
    // Version for tracking
    VERSION: '1.1',
    
    // Polling interval for download progress (ms)
    POLL_INTERVAL: 1000,
    
    // Message display time after completion (ms)
    SUCCESS_MESSAGE_DURATION: 5000
};

// Export for use in popup.js
// (In Chrome extensions, we just make it global)
