# How to Fix YouTube 429 Errors (Rate Limiting)

YouTube blocks automated requests. To fix this, you need to export your cookies.

## Quick Steps

### 1. Install Cookie Exporter Extension

Install one of these Chrome extensions:
- **Get cookies.txt LOCALLY** (recommended): https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
- **cookies.txt**: https://chrome.google.com/webstore/detail/cookiestxt/njabckikapfpffapmjgojcnbfjonfjfg

### 2. Export Cookies from YouTube

1. Go to **https://www.youtube.com** in Chrome
2. Make sure you're **logged into your Google account**
3. Click the cookie extension icon in your toolbar
4. Click **"Export"** or **"Download"**
5. Save the file as `cookies.txt`

### 3. Move to YTB Folder

Move the `cookies.txt` file to:
```
c:\Users\LucyS\ytb\cookies.txt
```

### 4. Restart the Server

Stop and restart the server:
```bash
# Stop with Ctrl+C, then:
python server.py
```

You should see:
```
✓ Using cookies.txt for authentication
```

## Important Notes

- **Keep cookies.txt private** - Don't share or upload to GitHub!
- **Cookies expire** - If you get 429 errors again, export fresh cookies
- **Stay logged in** - Make sure you're logged into YouTube when exporting

## Troubleshooting

### Still getting 429 errors?
1. Make sure `cookies.txt` is in the same folder as `server.py`
2. Make sure you exported from YouTube while logged in
3. Try exporting fresh cookies

### Subtitles not downloading?
- Not all videos have subtitles
- Some videos only have auto-generated captions
- Try a popular video that definitely has subtitles
