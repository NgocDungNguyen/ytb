document.addEventListener('DOMContentLoaded', async () => {
    const statusBadge = document.getElementById('server-status');
    const controls = document.getElementById('controls');
    const messageArea = document.getElementById('message-area');
    const progressContainer = document.getElementById('progress-container');
    const progressFill = document.getElementById('progress-fill');
    const progressPercent = document.getElementById('progress-percent');
    const progressStatus = document.getElementById('progress-status');
    const progressSpeed = document.getElementById('progress-speed');
    const progressEta = document.getElementById('progress-eta');
    const urlInput = document.getElementById('url-input');
    const loadUrlBtn = document.getElementById('load-url-btn');

    let isDownloading = false;
    let serverOnline = false;
    let SERVER_URL = null;
    let currentVideoUrl = null;  // Track the current video URL
    let youtubeCookies = null;   // Store YouTube cookies for authentication

    // 1. Auto-detect server (localhost or production)
    statusBadge.textContent = "Detecting...";
    SERVER_URL = await detectServer();
    
    // 2. Extract YouTube cookies (for anti-429 protection)
    youtubeCookies = await getYouTubeCookies();
    
    // 3. Check Server Status
    await checkServer();

    // 3. Get Current Tab and check if it's a YouTube page
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!serverOnline) {
        showMessage("Server offline. Make sure the server is running.", "error");
    } else if (tab && tab.url && isValidYouTubeUrl(tab.url)) {
        // Auto-fill URL from current tab
        urlInput.value = tab.url;
        currentVideoUrl = tab.url;
        
        // Check for existing persisted task
        const restored = await tryRestoreState(tab.url);
        
        // If not downloading, load info
        if (!restored) {
            loadVideoInfo(tab.url);
        }
    } else {
        // Not on YouTube - show input field message
        showMessage("Paste a YouTube URL above, or open a YouTube video", "normal");
        controls.classList.remove('disabled');  // Enable controls for manual URL
    }

    // Event Listeners
    document.getElementById('download-video').addEventListener('click', () => startDownload('video'));
    document.getElementById('download-audio').addEventListener('click', () => startDownload('audio'));
    document.getElementById('download-transcript').addEventListener('click', () => startDownload('transcript'));
    
    // Manual URL Load button
    loadUrlBtn.addEventListener('click', () => loadManualUrl());
    
    // Also load on Enter key in input
    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') loadManualUrl();
    });

    // Function to validate YouTube URLs (including Shorts!)
    function isValidYouTubeUrl(url) {
        if (!url) return false;
        return (
            url.includes('youtube.com/watch') ||
            url.includes('youtube.com/shorts/') ||  // YouTube Shorts
            url.includes('youtu.be/') ||
            url.includes('youtube.com/v/') ||
            url.includes('youtube.com/embed/')
        );
    }

    // Load video from manual URL input
    async function loadManualUrl() {
        const url = urlInput.value.trim();
        
        if (!url) {
            showMessage("Please enter a YouTube URL", "error");
            return;
        }
        
        if (!isValidYouTubeUrl(url)) {
            showMessage("Invalid YouTube URL. Supported: videos, shorts, youtu.be links", "error");
            return;
        }
        
        if (!serverOnline) {
            showMessage("Server is offline", "error");
            return;
        }
        
        currentVideoUrl = url;
        loadVideoInfo(url);
    }

    // Extract YouTube cookies from browser - auto-authentication!
    async function getYouTubeCookies() {
        try {
            // Try multiple domains to get all YouTube cookies
            const domains = [".youtube.com", "youtube.com", ".google.com"];
            let allCookies = [];
            
            for (const domain of domains) {
                try {
                    const cookies = await chrome.cookies.getAll({ domain });
                    if (cookies && cookies.length > 0) {
                        allCookies = allCookies.concat(cookies);
                    }
                } catch (e) {
                    console.log(`No cookies for ${domain}`);
                }
            }
            
            // Remove duplicates by name
            const uniqueCookies = [...new Map(allCookies.map(c => [c.name, c])).values()];
            
            if (uniqueCookies.length > 0) {
                // Convert to Netscape cookie format for yt-dlp
                const cookieLines = uniqueCookies.map(c => {
                    const secure = c.secure ? "TRUE" : "FALSE";
                    const expiry = c.expirationDate ? Math.floor(c.expirationDate) : 0;
                    return `${c.domain}\tTRUE\t${c.path}\t${secure}\t${expiry}\t${c.name}\t${c.value}`;
                });
                console.log(`✓ Extracted ${uniqueCookies.length} YouTube cookies`);
                return cookieLines.join('\n');
            } else {
                console.warn("No YouTube cookies found - make sure you're logged into YouTube");
            }
        } catch (e) {
            console.error("Could not get YouTube cookies:", e);
        }
        return null;
    }

    async function checkServer() {
        try {
            const response = await fetch(`${SERVER_URL}/health`, { 
                method: 'GET',
                signal: AbortSignal.timeout(5000) // 5 second timeout
            });
            
            if (response.ok) {
                serverOnline = true;
                statusBadge.textContent = "Online";
                statusBadge.classList.add('online');
                statusBadge.classList.remove('offline');
            } else {
                throw new Error('Server error');
            }
        } catch (e) {
            serverOnline = false;
            statusBadge.textContent = "Offline";
            statusBadge.classList.add('offline');
            statusBadge.classList.remove('online');
            console.error('Server check failed:', e);
        }
    }

    async function tryRestoreState(currentUrl) {
        try {
            const data = await chrome.storage.local.get(['currentDownload']);
            if (data.currentDownload && data.currentDownload.url === currentUrl) {
                const { taskId, type } = data.currentDownload;
                console.log("Restoring task:", taskId);
                
                // Check if task is still valid on server
                const response = await fetch(`${SERVER_URL}/progress/${taskId}`);
                if (response.ok) {
                    const taskData = await response.json();
                    if (taskData.error) {
                         // Task invalid/expired
                         await chrome.storage.local.remove('currentDownload');
                         return false;
                    }
                    
                    // It's valid, restore UI
                    isDownloading = true;
                    controls.classList.add('disabled');
                    progressContainer.classList.remove('hidden');
                    
                    // Manually populate video info if we can (optional, or just wait for loadVideoInfo)
                     // But loadVideoInfo might be slow.
                     
                    pollProgress(taskId);
                    return true;
                }
            }
        } catch (e) {
            console.error("Error restoring state:", e);
        }
        return false;
    }

    async function loadVideoInfo(url) {
        try {
            const response = await fetch(`${SERVER_URL}/info`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });
            
            if (!response.ok) throw new Error('Server returned error');

            const data = await response.json();
            
            document.getElementById('thumbnail').src = data.thumbnail || '';
            document.getElementById('video-title').textContent = data.title || 'Unknown Title';
            document.getElementById('video-duration').textContent = formatDuration(data.duration);
            document.getElementById('video-views').textContent = `${formatViews(data.views)} views`;
            
            document.getElementById('video-info').classList.remove('hidden');
            if(!isDownloading) controls.classList.remove('disabled');
        } catch (error) {
            console.error(error);
            showMessage("Could not connect to server. Is 'Start_Extension_Server.bat' running?", "error");
            statusBadge.textContent = "Offline";
            statusBadge.classList.add('offline');
        }
    }

    async function startDownload(type) {
        if (isDownloading) return;
        
        // Use manual URL if entered, otherwise use detected URL
        const urlToDownload = urlInput.value.trim() || currentVideoUrl;
        
        if (!urlToDownload) {
            showMessage("Please enter or load a YouTube URL first", "error");
            return;
        }
        
        if (!isValidYouTubeUrl(urlToDownload)) {
            showMessage("Invalid YouTube URL", "error");
            return;
        }
        
        const quality = document.getElementById('quality-select').value;
        const audioQuality = document.getElementById('audio-quality-select').value;
        
        try {
            isDownloading = true;
            controls.classList.add('disabled');
            progressContainer.classList.remove('hidden');
            resetProgress();

            const response = await fetch(`${SERVER_URL}/download`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    url: urlToDownload,
                    type,
                    quality,
                    audioQuality,
                    cookies: youtubeCookies  // Send cookies for anti-429 protection
                })
            });

            const data = await response.json();
            
            if (data.task_id) {
                // Save state
                await chrome.storage.local.set({
                    currentDownload: {
                        taskId: data.task_id,
                        url: urlToDownload,
                        type: type
                    }
                });
                
                pollProgress(data.task_id);
            } else {
                throw new Error(data.error || 'Failed to start');
            }

        } catch (error) {
            showMessage(error.message, "error");
            isDownloading = false;
            controls.classList.remove('disabled');
            progressContainer.classList.add('hidden');
        }
    }

    async function pollProgress(taskId) {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`${SERVER_URL}/progress/${taskId}`);
                const data = await response.json();

                if (data.error) {
                    clearInterval(interval);
                    completeDownload(false, data.error, null);
                    return;
                }

                updateProgressUI(data);

                if (data.status === 'finished' || data.status === 'error') {
                    clearInterval(interval);
                    completeDownload(data.status === 'finished', data.error, taskId);
                }

            } catch (e) {
                console.error("Polling error", e);
            }
        }, 1000);
    }

    function updateProgressUI(data) {
        if (data.status === 'downloading') {
            progressStatus.textContent = "Downloading...";
            progressFill.style.width = `${data.progress}%`;
            progressPercent.textContent = `${Math.round(data.progress)}%`;
            progressSpeed.textContent = data.speed;
            progressEta.textContent = `ETA: ${data.eta}`;
        } else if (data.status === 'processing') {
            progressStatus.textContent = "Processing/Converting...";
            progressFill.style.width = "100%";
        }
    }

    async function completeDownload(success, errorMsg, taskId) {
        isDownloading = false;
        controls.classList.remove('disabled');
        
        // Clear storage
        await chrome.storage.local.remove('currentDownload');

        if (success) {
            progressStatus.textContent = "Preparing file...";
            progressFill.style.width = "100%";
            progressPercent.textContent = "100%";
            
            // Download file as blob to bypass IDM interception
            if (taskId) {
                try {
                    progressStatus.textContent = "Fetching file...";
                    
                    const downloadUrl = `${SERVER_URL}/download-file/${taskId}`;
                    const response = await fetch(downloadUrl);
                    
                    if (!response.ok) throw new Error('Failed to fetch file');
                    
                    // Get filename from Content-Disposition header or generate one
                    const contentDisposition = response.headers.get('Content-Disposition');
                    let filename = 'download';
                    if (contentDisposition) {
                        const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                        if (match && match[1]) {
                            filename = match[1].replace(/['"]/g, '');
                        }
                    }
                    
                    // Convert to blob
                    const blob = await response.blob();
                    
                    // Create blob URL and trigger download
                    const blobUrl = URL.createObjectURL(blob);
                    
                    // Use Chrome downloads API with blob URL - IDM can't intercept this!
                    chrome.downloads.download({
                        url: blobUrl,
                        filename: filename,
                        saveAs: true
                    }, (downloadId) => {
                        if (downloadId) {
                            console.log('Download started with ID:', downloadId);
                            // Clean up blob URL after a delay
                            setTimeout(() => URL.revokeObjectURL(blobUrl), 60000);
                        } else {
                            // Fallback: open blob in new tab
                            const a = document.createElement('a');
                            a.href = blobUrl;
                            a.download = filename;
                            a.click();
                        }
                    });
                    
                    progressStatus.textContent = "Completed!";
                    showNotification("Download Complete! 🎉", "Your file is ready!");
                    showMessage("Save dialog should appear now!", "success");
                    
                } catch (fetchError) {
                    console.error('Blob download failed:', fetchError);
                    showMessage("Download prepared. Check your downloads folder.", "success");
                }
            }
            
            setTimeout(() => {
                progressContainer.classList.add('hidden');
                messageArea.textContent = "";
            }, 5000);
        } else {
            showNotification("Download Failed ❌", errorMsg);
            showMessage(`Error: ${errorMsg}`, "error");
            progressContainer.classList.add('hidden');
        }
    }

    function showNotification(title, message) {
        // Request notification permission and show
        if (Notification.permission === "granted") {
            new Notification(title, {
                body: message,
                icon: "icon.jpg"
            });
        } else if (Notification.permission !== "denied") {
            Notification.requestPermission().then(permission => {
                if (permission === "granted") {
                    new Notification(title, {
                        body: message,
                        icon: "icon.jpg"
                    });
                }
            });
        }
    }

    function resetProgress() {
        progressFill.style.width = "0%";
        progressPercent.textContent = "0%";
        progressSpeed.textContent = "";
        progressEta.textContent = "";
        progressStatus.textContent = "Starting...";
    }

    function showMessage(text, type = 'normal') {
        messageArea.textContent = text;
        messageArea.className = 'message-area ' + type;
    }

    function formatDuration(seconds) {
        if (!seconds) return '--:--';
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m}:${s.toString().padStart(2, '0')}`;
    }

    function formatViews(views) {
        if (!views) return '0';
        if (views >= 1000000) return (views / 1000000).toFixed(1) + 'M';
        if (views >= 1000) return (views / 1000).toFixed(1) + 'K';
        return views;
    }
});
