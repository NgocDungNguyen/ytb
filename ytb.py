import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
from PIL import Image, ImageTk
import requests
from io import BytesIO
import pygame
import random
import cv2
import yt_dlp
import customtkinter as ctk
from ttkbootstrap import Style
from ttkbootstrap.constants import *
import ffmpeg
FFMPEG_PATH = r"C:\Users\LucyS\Downloads\Compressed\ffmpeg-2025-03-31-git-35c091f4b7-full_build\ffmpeg-2025-03-31-git-35c091f4b7-full_build\bin"

class EnhancedYouTubeDownloaderPlayer:
    def __init__(self, master):
        self.master = master
        master.title("Enhanced YouTube Downloader & Player")
        master.geometry("1280x720")
        
        self.theme = "darkly"  # Changed from "dark" to "darkly"
        self.style = Style(theme=self.theme)
        
        self.setup_styles()
        self.create_menu()
        self.setup_main_interface()
        
        pygame.mixer.init()

    def setup_styles(self):
        self.style.configure("TLabel", font=("Roboto", 10))
        self.style.configure("TButton", font=("Roboto", 10))
        self.style.configure("TEntry", font=("Roboto", 10))
        self.style.configure("Accent.TButton", font=("Roboto", 10, "bold"))

    def create_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.add_to_playlist)
        file_menu.add_command(label="Exit", command=self.master.quit)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Convert Video to MP3", command=self.convert_video_to_mp3)
        tools_menu.add_command(label="Convert to MP4", command=self.convert_to_mp4)

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Theme", command=self.toggle_theme)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def setup_main_interface(self):
        self.main_frame = ttk.Frame(self.master, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.downloader_frame = ttk.Frame(self.notebook, padding="10")
        self.player_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.downloader_frame, text="Downloader")
        self.notebook.add(self.player_frame, text="Player")

        self.setup_downloader()
        self.setup_player()

    def setup_downloader(self):
        left_frame = ttk.Frame(self.downloader_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        right_frame = ttk.Frame(self.downloader_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        url_frame = ttk.LabelFrame(left_frame, text="YouTube URL", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 10))

        self.url_entry = ttk.Entry(url_frame, width=50)
        self.url_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        ttk.Button(url_frame, text="Get Info", command=self.get_video_info, style="Accent.TButton").pack(side=tk.RIGHT, padx=(10, 0))

        options_frame = ttk.LabelFrame(left_frame, text="Download Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))

        self.format_var = tk.StringVar(value="video")
        ttk.Radiobutton(options_frame, text="Video (MP4)", variable=self.format_var, value="video").pack(anchor=tk.W)
        ttk.Radiobutton(options_frame, text="Audio (MP3)", variable=self.format_var, value="audio").pack(anchor=tk.W)

        ttk.Label(options_frame, text="Quality:").pack(anchor=tk.W, pady=(10, 0))
        self.quality_var = tk.StringVar(value="720p")
        self.quality_menu = ttk.Combobox(options_frame, textvariable=self.quality_var, values=["144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p"])
        self.quality_menu.pack(fill=tk.X)

        self.download_button = ttk.Button(left_frame, text="Download", command=self.start_download_all, style="Accent.TButton")
        self.download_button.pack(fill=tk.X, pady=(0, 10))

        progress_frame = ttk.LabelFrame(left_frame, text="Download Progress", padding="10")
        progress_frame.pack(fill=tk.X)

        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=300, mode="determinate", style="success.Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.status_label = ttk.Label(progress_frame, text="Ready to download")
        self.status_label.pack(anchor=tk.W)

        ttk.Button(left_frame, text="Download History", command=self.show_history).pack(fill=tk.X, pady=(10, 0))

        info_frame = ttk.LabelFrame(right_frame, text="Video Information", padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True)

        self.thumbnail_label = ttk.Label(info_frame)
        self.thumbnail_label.pack(pady=(0, 10))

        self.title_label = ttk.Label(info_frame, text="", wraplength=300)
        self.title_label.pack()

        self.info_label = ttk.Label(info_frame, text="", wraplength=300)
        self.info_label.pack()

        self.download_history = []

    def setup_player(self):
        self.playlist = []
        self.current_track = 0
        self.is_playing = False
        self.repeat_mode = 'no_repeat'
        self.current_file_type = None
        self.video_paused = False

        left_frame = ttk.Frame(self.player_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        right_frame = ttk.Frame(self.player_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        playlist_frame = ttk.LabelFrame(left_frame, text="Playlist", padding="10")
        playlist_frame.pack(fill=tk.BOTH, expand=True)

        self.playlist_box = tk.Listbox(playlist_frame, selectmode=tk.SINGLE, activestyle='none', bg='#2c2c2c', fg='white')
        self.playlist_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(playlist_frame, orient="vertical", command=self.playlist_box.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.playlist_box.config(yscrollcommand=scrollbar.set)

        ttk.Button(left_frame, text="Add to Playlist", command=self.add_to_playlist, style="Accent.TButton").pack(fill=tk.X, pady=(10, 0))

        player_frame = ttk.LabelFrame(right_frame, text="Now Playing", padding="10")
        player_frame.pack(fill=tk.BOTH, expand=True)

        self.video_label = ttk.Label(player_frame)
        self.video_label.pack(pady=(0, 10))

        control_frame = ttk.Frame(player_frame)
        control_frame.pack(fill=tk.X)

        ttk.Button(control_frame, text="⏮", command=self.play_previous, style="Accent.TButton").pack(side=tk.LEFT)
        self.play_pause_button = ttk.Button(control_frame, text="▶", command=self.toggle_play_pause, style="Accent.TButton")
        self.play_pause_button.pack(side=tk.LEFT)
        ttk.Button(control_frame, text="⏭", command=self.play_next, style="Accent.TButton").pack(side=tk.LEFT)
        ttk.Button(control_frame, text="🔀", command=self.toggle_shuffle, style="Accent.TButton").pack(side=tk.LEFT)
        self.repeat_button = ttk.Button(control_frame, text="🔁", command=self.toggle_repeat, style="Accent.TButton")
        self.repeat_button.pack(side=tk.LEFT)

    def get_video_info(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return

        try:
            ydl_opts = {'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info['title']
                duration = info['duration']
                views = info['view_count']
                thumbnail_url = info['thumbnail']

                formats = info['formats']
                available_qualities = set()
                for f in formats:
                    if f.get('height'):
                        available_qualities.add(f"{f['height']}p")
                self.quality_menu['values'] = sorted(list(available_qualities), key=lambda x: int(x[:-1]))

                self.title_label.config(text=f"Title: {title}")
                self.info_label.config(text=f"Duration: {duration} seconds\nViews: {views}")

                response = requests.get(thumbnail_url)
                img = Image.open(BytesIO(response.content))
                img = img.resize((300, 225), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.thumbnail_label.config(image=photo)
                self.thumbnail_label.image = photo

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def start_download_all(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return

        save_path = filedialog.askdirectory()
        if not save_path:
            return

        format_choice = self.format_var.get()
        quality = self.quality_var.get()

        self.download_button.config(state=tk.DISABLED)
        self.progress_bar["value"] = 0
        self.status_label.config(text="Starting download...")

        threading.Thread(target=self.download_thread, args=(url, save_path, format_choice, quality)).start()

    def download_thread(self, url, save_path, format_choice, quality):
        try:
            if format_choice == "video":
                ydl_opts = {
                    'format': f'bestvideo[height<={quality[:-1]}]+bestaudio/best[height<={quality[:-1]}]',
                    'outtmpl': f'{save_path}/%(title)s.%(ext)s',
                    'progress_hooks': [self.progress_hook],
                    'ffmpeg_location': FFMPEG_PATH,  # Add FFmpeg path
                }
            else:  # audio
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': f'{save_path}/%(title)s.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'progress_hooks': [self.progress_hook],
                    'ffmpeg_location': FFMPEG_PATH,  # Add FFmpeg path
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                self.download_history.append(filename)

            self.master.after(0, lambda: self.status_label.config(text="Download completed!"))
            messagebox.showinfo("Success", "Download completed successfully!")
        except Exception as e:
            self.master.after(0, lambda: self.status_label.config(text=f"Error: {str(e)}"))
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.master.after(0, lambda: self.download_button.config(state=tk.NORMAL))

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d['_percent_str']
            speed = d['_speed_str']
            eta = d['_eta_str']
            self.master.after(0, lambda: self.update_progress(percent, speed, eta))
        elif d['status'] == 'finished':
            self.master.after(0, lambda: self.status_label.config(text="Download finished, now processing..."))

    def update_progress(self, percent, speed, eta):
        # Remove ANSI color codes and other non-numeric characters
        clean_percent = ''.join(c for c in percent if c.isdigit() or c == '.')
        if clean_percent:
            try:
                self.progress_bar["value"] = float(clean_percent)
            except ValueError:
                # Fallback if conversion still fails
                self.progress_bar["value"] = 0
        
        # Display the raw values without trying to parse them
        self.status_label.config(text=f"Downloading at {speed}, ETA: {eta}")

    def show_history(self):
        history_window = tk.Toplevel(self.master)
        history_window.title("Download History")
        history_window.geometry("500x300")

        history_listbox = tk.Listbox(history_window, width=70)
        history_listbox.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        for item in self.download_history:
            history_listbox.insert(tk.END, os.path.basename(item))

        def open_file_location():
            selected = history_listbox.curselection()
            if selected:
                file_path = self.download_history[selected[0]]
                os.startfile(os.path.dirname(file_path))

        open_button = ttk.Button(history_window, text="Open File Location", command=open_file_location)
        open_button.pack(pady=10)

    def add_to_playlist(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Media Files", "*.mp3 *.mp4")])
        for file_path in file_paths:
            self.playlist.append(file_path)
            self.playlist_box.insert(tk.END, os.path.basename(file_path))

    def toggle_play_pause(self):
        if not self.playlist:
            messagebox.showinfo("Info", "Playlist is empty. Add some tracks first.")
            return

        if not self.is_playing:
            self.play_track()
        else:
            if self.current_file_type == 'audio':
                pygame.mixer.music.pause()
            else:  # video
                self.video_paused = True
            self.play_pause_button.config(text="▶")
            self.is_playing = False

    def play_track(self):
        file_path = self.playlist[self.current_track]
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == '.mp3':
            self.play_audio(file_path)
        elif file_extension == '.mp4':
            self.play_video(file_path)

    def play_audio(self, file_path):
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        self.play_pause_button.config(text="⏸")
        self.is_playing = True
        self.current_file_type = 'audio'

    def play_video(self, file_path):
        self.video = cv2.VideoCapture(file_path)
        self.video_paused = False
        self.current_file_type = 'video'
        self.play_pause_button.config(text="⏸")
        self.is_playing = True
        self.update_video_frame()

    def update_video_frame(self):
        if self.is_playing and not self.video_paused:
            ret, frame = self.video.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (400, 300))
                photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
                self.video_label.config(image=photo)
                self.video_label.image = photo
                self.master.after(30, self.update_video_frame)
            else:
                self.play_next()

    def play_next(self):
        if not self.playlist:
            return
        self.current_track = (self.current_track + 1) % len(self.playlist)
        self.play_track()

    def play_previous(self):
        if not self.playlist:
            return
        self.current_track = (self.current_track - 1) % len(self.playlist)
        self.play_track()

    def toggle_shuffle(self):
        random.shuffle(self.playlist)
        self.playlist_box.delete(0, tk.END)
        for item in self.playlist:
            self.playlist_box.insert(tk.END, os.path.basename(item))
        messagebox.showinfo("Info", "Playlist shuffled")

    def toggle_repeat(self):
        if self.repeat_mode == 'no_repeat':
            self.repeat_mode = 'repeat_all'
            self.repeat_button.config(text="🔁")
        elif self.repeat_mode == 'repeat_all':
            self.repeat_mode = 'repeat_one'
            self.repeat_button.config(text="🔂")
        else:
            self.repeat_mode = 'no_repeat'
            self.repeat_button.config(text="🔁")
            
            
    def convert_video_to_mp3(self):
        input_file = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv")])
        if not input_file:
            return

        output_file = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3 Files", "*.mp3")])
        if not output_file:
            return

        try:
            # Set the FFmpeg binary location
            ffmpeg.input(input_file).output(
                output_file, 
                acodec='libmp3lame',
                **{'cmd': os.path.join(FFMPEG_PATH, 'ffmpeg')}
            ).run()
            messagebox.showinfo("Success", "Video successfully converted to MP3!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during conversion: {str(e)}")

    def convert_to_mp4(self):
        input_file = filedialog.askopenfilename(filetypes=[("Video Files", "*.avi *.mov *.mkv")])
        if not input_file:
            return

        output_file = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 Files", "*.mp4")])
        if not output_file:
            return

        try:
            # Set the FFmpeg binary location
            ffmpeg.input(input_file).output(
                output_file, 
                vcodec='libx264', 
                acodec='aac',
                **{'cmd': os.path.join(FFMPEG_PATH, 'ffmpeg')}
            ).run()
            messagebox.showinfo("Success", "Video successfully converted to MP4!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during conversion: {str(e)}")

    def toggle_theme(self):
        self.theme = "litera" if self.theme == "darkly" else "darkly"  # Toggle between "darkly" and "litera"
        self.style.theme_use(self.theme)

    def show_about(self):
        messagebox.showinfo("About", "Enhanced YouTube Downloader & Player\nVersion 2.0\n\nCreated by Your Name")

if __name__ == '__main__':
    root = ctk.CTk()
    app = EnhancedYouTubeDownloaderPlayer(root)
    root.mainloop()