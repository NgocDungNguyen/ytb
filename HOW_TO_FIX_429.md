# How to Fix "429 Too Many Requests" Error

YouTube sometimes blocks downloads with a "429" error. This happens because you're downloading without authentication.

## Solution: Export Your Cookies

### Step 1: Install a Cookie Exporter Extension
1. Open Chrome Web Store
2. Search for **"Get cookies.txt LOCALLY"** by Rahul Shaw (or any similar extension)
3. Add to Chrome

### Step 2: Export Your Cookies
1. Go to **youtube.com** and make sure you're logged in
2. Click the cookie extension icon
3. Click **"Export"** or **"Download"**
4. Save the file as `cookies.txt`

### Step 3: Move the File
1. Move the downloaded `cookies.txt` to: `c:\Users\LucyS\ytb\`
2. The server will automatically detect and use it

### Step 4: Restart the Server
1. Close the server terminal
2. Run `Start_Extension_Server.bat` again
3. You should see: `✓ Using cookies.txt for authentication`

## That's it!
The 429 errors should be completely gone now.
