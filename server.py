import os
import shutil
import tempfile
import threading
import uuid

import yt_dlp
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

app = Flask(__name__)
# Allow all origins for Chrome extension - update with your specific extension ID in production
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuration - Environment variables for production (Render)
PORT = int(os.environ.get("PORT", 5000))
IS_PRODUCTION = os.environ.get("RENDER", False) or os.environ.get("PRODUCTION", False)

# FFmpeg path - On Render/Linux, ffmpeg is installed system-wide
if IS_PRODUCTION:
    FFMPEG_PATH = "/usr/bin"  # Linux default
else:
    # Local Windows development path
    FFMPEG_PATH = r"C:\Users\LucyS\Downloads\Compressed\ffmpeg-2025-03-31-git-35c091f4b7-full_build\ffmpeg-2025-03-31-git-35c091f4b7-full_build\bin"

# Download directory - Use temp directory for cloud deployment
if IS_PRODUCTION:
    DOWNLOAD_DIR = tempfile.mkdtemp(prefix="ytb_downloads_")
else:
    DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "YTB_Downloads")

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

tasks = {}

# Track if we've shown the cookie warning (only show once)
_cookie_warning_shown = False


def get_base_ydl_opts(cookies_from_extension=None):
    """Get base yt-dlp options with automatic cookie handling"""
    global _cookie_warning_shown

    opts = {
        "quiet": True,
        "no_warnings": True,
        "ffmpeg_location": FFMPEG_PATH,
        # Anti-bot measures
        "sleep_interval": 1,
        "sleep_interval_requests": 1,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
    }

    # Priority 1: Use cookies sent from Chrome extension (best - auto from browser!)
    if cookies_from_extension:
        temp_cookie_file = os.path.join(
            DOWNLOAD_DIR, f"temp_cookies_{uuid.uuid4().hex[:8]}.txt"
        )
        try:
            with open(temp_cookie_file, "w") as f:
                f.write("# Netscape HTTP Cookie File\n")
                f.write(cookies_from_extension)
            opts["cookiefile"] = temp_cookie_file
            opts["_temp_cookie_file"] = temp_cookie_file  # Track for cleanup
            if not _cookie_warning_shown:
                print("✓ Using cookies from Chrome extension (auto-authenticated!)")
                _cookie_warning_shown = True
            return opts
        except Exception as e:
            print(f"⚠ Could not write extension cookies: {e}")

    # Priority 2: Use cookies.txt if it exists
    local_cookies = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "cookies.txt"
    )
    if os.path.exists(local_cookies):
        opts["cookiefile"] = local_cookies
        if not _cookie_warning_shown:
            print("✓ Using cookies.txt for authentication")
            _cookie_warning_shown = True
    else:
        # No cookies available
        if not _cookie_warning_shown:
            print(
                "ℹ No cookies available. If you get 429 errors, the extension will auto-send browser cookies."
            )
            _cookie_warning_shown = True

    return opts


def progress_hook(d, task_id):
    if d["status"] == "downloading":
        p_str = d.get("_percent_str", "0%").replace("%", "")
        try:
            percent = float(p_str)
        except:
            percent = 0

        tasks[task_id].update(
            {
                "status": "downloading",
                "progress": percent,
                "speed": d.get("_speed_str", "N/A"),
                "eta": d.get("_eta_str", "N/A"),
            }
        )
    elif d["status"] == "finished":
        tasks[task_id].update({"status": "processing", "progress": 100})


def run_download(
    task_id, url, format_choice, quality, audio_quality="192", cookies=None
):
    temp_cookie_file = None
    try:
        tasks[task_id]["status"] = "starting"

        ydl_opts = get_base_ydl_opts(cookies)
        temp_cookie_file = ydl_opts.pop(
            "_temp_cookie_file", None
        )  # Extract for cleanup
        ydl_opts["outtmpl"] = f"{DOWNLOAD_DIR}/%(title)s.%(ext)s"
        ydl_opts["progress_hooks"] = [lambda d: progress_hook(d, task_id)]

        if format_choice == "video":
            # Don't specify format - let yt-dlp pick the best automatically
            # This is the most reliable approach
            pass  # Use default (best available)

        elif format_choice == "audio":
            # Don't specify format - download best and extract audio
            ydl_opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": audio_quality,  # User-selected quality
                }
            ]

        elif format_choice == "transcript":
            ydl_opts["writesubtitles"] = True
            ydl_opts["writeautomaticsub"] = True
            ydl_opts["skip_download"] = True
            ydl_opts["subtitleslangs"] = ["en", "en-orig"]
            ydl_opts["outtmpl"] = f"{DOWNLOAD_DIR}/%(title)s.%(ext)s"
            # Ignore subtitle download errors and continue
            ydl_opts["ignoreerrors"] = True
            ydl_opts["no_warnings"] = True

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # Get the actual downloaded filename
            downloaded_file = ydl.prepare_filename(info)

            filename = info.get("title", "Unknown")
            if format_choice == "audio":
                filename = os.path.splitext(filename)[0] + ".mp3"
                # Audio files get converted, update path
                downloaded_file = os.path.splitext(downloaded_file)[0] + ".mp3"
            elif format_choice == "transcript":
                filename = f"{filename} [Subtitles]"
                # Find the actual subtitle file
                base_path = os.path.splitext(downloaded_file)[0]
                subtitle_found = False
                for ext in [".en.vtt", ".en.srt", ".en-orig.vtt", ".vtt", ".srt"]:
                    potential_file = base_path + ext
                    if os.path.exists(potential_file):
                        downloaded_file = potential_file
                        subtitle_found = True
                        break

                # If no subtitle file found, raise a clear error
                if not subtitle_found:
                    raise Exception(
                        "No subtitles available for this video, or YouTube blocked the request (429 error). Try adding cookies.txt."
                    )

            tasks[task_id].update(
                {
                    "status": "finished",
                    "progress": 100,
                    "filename": filename,
                    "filepath": downloaded_file,  # Store full path for download endpoint
                }
            )

    except Exception as e:
        print(f"Error in task {task_id}: {str(e)}")
        err_msg = str(e)
        if "429" in err_msg or "Too Many Requests" in err_msg:
            err_msg = "YouTube is rate-limiting. Please try again in a few minutes."

        tasks[task_id].update({"status": "error", "error": err_msg})

    finally:
        # Clean up temporary cookie file
        if temp_cookie_file and os.path.exists(temp_cookie_file):
            try:
                os.remove(temp_cookie_file)
            except:
                pass


@app.route("/info", methods=["POST"])
def get_info():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL"}), 400

    try:
        ydl_opts = get_base_ydl_opts()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify(
                {
                    "title": info.get("title"),
                    "thumbnail": info.get("thumbnail"),
                    "duration": info.get("duration"),
                    "views": info.get("view_count"),
                }
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download", methods=["POST"])
def start_download():
    data = request.json
    url = data.get("url")
    format_choice = data.get("type", "video")
    quality = data.get("quality", "720p")
    audio_quality = data.get("audioQuality", "192")  # Default 192 kbps
    cookies = data.get("cookies")  # Cookies from Chrome extension

    if not url:
        return jsonify({"error": "No URL"}), 400

    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "queued", "progress": 0, "speed": "0", "eta": "--:--"}

    thread = threading.Thread(
        target=run_download,
        args=(task_id, url, format_choice, quality, audio_quality, cookies),
    )
    thread.start()

    return jsonify({"task_id": task_id, "status": "started"})


@app.route("/progress/<task_id>", methods=["GET"])
def get_progress(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring and extension status check"""
    return jsonify({"status": "ok", "version": "1.1"})


@app.route("/download-file/<task_id>", methods=["GET"])
def download_file(task_id):
    """Allow browser to download the completed file"""
    task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    if task.get("status") != "finished":
        return jsonify({"error": "Download not complete"}), 400

    filepath = task.get("filepath")
    if filepath and os.path.exists(filepath):
        # Get the filename and determine MIME type
        filename = os.path.basename(filepath)

        # Set correct MIME type based on file extension
        ext = os.path.splitext(filepath)[1].lower()
        mime_types = {
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".mkv": "video/x-matroska",
            ".mp3": "audio/mpeg",
            ".m4a": "audio/mp4",
            ".wav": "audio/wav",
            ".vtt": "text/vtt",
            ".srt": "text/plain",
        }
        mimetype = mime_types.get(ext, "application/octet-stream")

        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,  # Force correct filename
            mimetype=mimetype,  # Force correct MIME type
        )
    return jsonify({"error": "File not found"}), 404


if __name__ == "__main__":
    print("=========================================")
    print(f"YTB Server Running on Port {PORT}")
    print(f"Mode: {'PRODUCTION' if IS_PRODUCTION else 'DEVELOPMENT'}")
    print(f"Save Path: {DOWNLOAD_DIR}")
    print("=========================================")
    # Bind to 0.0.0.0 to accept external connections (required for Render)
    app.run(host="0.0.0.0", port=PORT, threaded=True)
