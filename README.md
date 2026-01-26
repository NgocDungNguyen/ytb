# YTB - YouTube Downloader Extension

A Chrome extension to download YouTube videos, audio (MP3), and transcripts.

## 🏗️ Project Structure

```
ytb/
├── server.py                 # Flask backend server
├── requirements.txt          # Python dependencies  
├── Procfile                  # For Render deployment
├── render.yaml               # Render configuration
├── cookies.txt               # (Optional) YouTube cookies for anti-429
├── chrome_extension/         # Chrome extension files
│   ├── manifest.json
│   ├── config.js            # ⚠️ UPDATE SERVER_URL HERE
│   ├── popup.html
│   ├── popup.js
│   ├── popup.css
│   └── icon.jpg
└── ytb.py                    # Desktop app (optional)
```

## 🚀 Deployment Guide

### Step 1: Deploy Server to Render

1. **Create a GitHub repo** and push this folder
2. **Go to [Render.com](https://render.com)** and sign up/login
3. **Create New Web Service** → Connect your GitHub repo
4. **Configure:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn server:app --bind 0.0.0.0:$PORT --workers 2 --threads 4`
   - **Environment:** Python 3
   - Add Environment Variable: `RENDER` = `true`
5. **Deploy** and note your URL (e.g., `https://ytb-server.onrender.com`)

### Step 2: Update Extension Config

1. Open `chrome_extension/config.js`
2. Change `SERVER_URL` to your Render URL:
   ```javascript
   SERVER_URL: 'https://YOUR-APP-NAME.onrender.com',
   ```

### Step 3: Upload to Chrome Web Store

1. **Zip the `chrome_extension` folder** (not the whole project!)
2. Go to [Chrome Developer Dashboard](https://chrome.google.com/webstore/devconsole)
3. Pay one-time $5 registration fee (if new developer)
4. Click **New Item** → Upload your ZIP
5. Fill in details, screenshots, etc.
6. Submit for review

## 🧪 Local Testing

### Run Server Locally
```bash
# Windows
Start_Extension_Server.bat

# Or manually
python server.py
```

### Load Extension in Chrome (Developer Mode)
1. Go to `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select the `chrome_extension` folder

## ⚠️ Important Notes

### For Chrome Web Store Submission
- Remove any references to "ytb.py backend" in description
- Don't mention "localhost" anywhere user-visible
- Make sure icons are present (icon.jpg)

### For Render Deployment
- Free tier sleeps after 15 min of inactivity (first request may be slow)
- FFmpeg is installed automatically on Render's Linux servers
- Files are temporarily stored (download immediately)

### Cookies for 429 Errors
If YouTube blocks downloads, see [HOW_TO_FIX_429.md](HOW_TO_FIX_429.md)

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (returns `{status: 'ok'}`) |
| `/info` | POST | Get video info (title, thumbnail, etc.) |
| `/download` | POST | Start download task |
| `/progress/<task_id>` | GET | Check download progress |
| `/download-file/<task_id>` | GET | Download completed file |

## 🔧 Troubleshooting

**Extension says "Server Offline":**
- Make sure server is running (`python server.py`)
- Check `config.js` has correct `SERVER_URL`

**429 Too Many Requests:**
- Add `cookies.txt` file (see HOW_TO_FIX_429.md)

**Download doesn't start:**
- Check browser console for errors (F12 → Console)
- Verify you're on a YouTube video page

## 📄 License

MIT License - Feel free to modify and distribute.
