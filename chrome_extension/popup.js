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

    let isDownloading = false;
    let serverOnline = false;
    let SERVER_URL = null;

    // 1. Auto-detect server (localhost or production)
    statusBadge.textContent = "Detecting...";
    SERVER_URL = await detectServer();
    
    // 2. Check Server Status
    await checkServer();

    // 3. Get Current Tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!serverOnline) {
        showMessage("Server offline. Make sure the server is running.", "error");
    } else if (tab && tab.url && (tab.url.includes('youtube.com/watch') || tab.url.includes('youtu.be/'))) {
        // 4. Check for existing persisted task
        const restored = await tryRestoreState(tab.url);
        
        // If not downloading, load info
        if (!restored) {
            loadVideoInfo(tab.url);
        } else {
             // We are restoring, so just load video info in background/silently to update UI if needed
             // But usually restoration sets the UI.
        }
    } else {
        showMessage("Please open a valid YouTube video page", "error");
    }

    // Event Listeners
    document.getElementById('download-video').addEventListener('click', () => startDownload('video'));
    document.getElementById('download-audio').addEventListener('click', () => startDownload('audio'));
    document.getElementById('download-transcript').addEventListener('click', () => startDownload('transcript'));

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
        
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        const quality = document.getElementById('quality-select').value;
        
        try {
            isDownloading = true;
            controls.classList.add('disabled');
            progressContainer.classList.remove('hidden');
            resetProgress();

            const response = await fetch(`${SERVER_URL}/download`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    url: tab.url,
                    type,
                    quality
                })
            });

            const data = await response.json();
            
            if (data.task_id) {
                // Save state
                await chrome.storage.local.set({
                    currentDownload: {
                        taskId: data.task_id,
                        url: tab.url,
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
            progressStatus.textContent = "Completed!";
            progressFill.style.width = "100%";
            progressPercent.textContent = "100%";
            
            // Trigger browser download of the file
            if (taskId) {
                const downloadUrl = `${SERVER_URL}/download-file/${taskId}`;
                chrome.tabs.create({ url: downloadUrl, active: false });
            }
            
            showMessage("Download starting...", "success");
            setTimeout(() => {
                progressContainer.classList.add('hidden');
                messageArea.textContent = "";
            }, 5000);
        } else {
            showMessage(`Error: ${errorMsg}`, "error");
            progressContainer.classList.add('hidden');
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
