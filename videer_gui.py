"""
Videer - Video Generation GUI Application
Fetches open source videos from Pexels.com based on text prompts
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import threading
from pexels_client import PexelsClient


class VideerApp:
    """Main GUI application for video generation"""
    
    def __init__(self, root):
        """Initialize the application"""
        self.root = root
        self.root.title("Videer - Video Generator from Pexels")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Initialize Pexels client
        self.pexels_client = None
        self.search_results = []
        
        # Create GUI
        self.create_widgets()
        
        # Load API key if available
        self.load_api_key()
    
    def load_api_key(self):
        """Load API key from .env file if it exists"""
        try:
            if os.path.exists(".env"):
                with open(".env", "r") as f:
                    for line in f:
                        if line.startswith("PEXELS_API_KEY="):
                            api_key = line.split("=", 1)[1].strip()
                            if api_key and api_key != "your_api_key_here":
                                self.api_key_entry.delete(0, tk.END)
                                self.api_key_entry.insert(0, api_key)
                                self.initialize_client()
        except Exception as e:
            print(f"Error loading API key: {e}")
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Videer - Video Generator",
            font=('Arial', 16, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # API Key Section
        api_frame = ttk.LabelFrame(main_frame, text="API Configuration", padding="10")
        api_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        api_frame.columnconfigure(1, weight=1)
        
        ttk.Label(api_frame, text="Pexels API Key:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.api_key_entry = ttk.Entry(api_frame, width=50, show="*")
        self.api_key_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        self.connect_btn = ttk.Button(api_frame, text="Connect", command=self.initialize_client)
        self.connect_btn.grid(row=0, column=2)
        
        ttk.Label(
            api_frame, 
            text="Get your free API key from https://www.pexels.com/api/",
            font=('Arial', 8),
            foreground='gray'
        ).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # Search Parameters Section
        params_frame = ttk.LabelFrame(main_frame, text="Video Search Parameters", padding="10")
        params_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        params_frame.columnconfigure(1, weight=1)
        
        # Text Prompt
        ttk.Label(params_frame, text="Search Prompt:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.prompt_entry = ttk.Entry(params_frame, width=50)
        self.prompt_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.prompt_entry.insert(0, "nature landscape")
        
        # Number of Videos
        ttk.Label(params_frame, text="Number of Videos:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.num_videos_var = tk.IntVar(value=5)
        num_videos_spinbox = ttk.Spinbox(
            params_frame, 
            from_=1, 
            to=80, 
            textvariable=self.num_videos_var,
            width=10
        )
        num_videos_spinbox.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Orientation
        ttk.Label(params_frame, text="Orientation:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.orientation_var = tk.StringVar(value="landscape")
        orientation_combo = ttk.Combobox(
            params_frame,
            textvariable=self.orientation_var,
            values=["landscape", "portrait", "square"],
            state="readonly",
            width=15
        )
        orientation_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Quality
        ttk.Label(params_frame, text="Video Quality:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.quality_var = tk.StringVar(value="hd")
        quality_combo = ttk.Combobox(
            params_frame,
            textvariable=self.quality_var,
            values=["hd", "sd"],
            state="readonly",
            width=15
        )
        quality_combo.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Size
        ttk.Label(params_frame, text="Minimum Size:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.size_var = tk.StringVar(value="medium")
        size_combo = ttk.Combobox(
            params_frame,
            textvariable=self.size_var,
            values=["large", "medium", "small"],
            state="readonly",
            width=15
        )
        size_combo.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Action Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))
        
        self.search_btn = ttk.Button(
            button_frame,
            text="Search Videos",
            command=self.search_videos,
            state=tk.DISABLED
        )
        self.search_btn.pack(side=tk.LEFT, padx=5)
        
        self.download_btn = ttk.Button(
            button_frame,
            text="Download Selected",
            command=self.download_videos,
            state=tk.DISABLED
        )
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        # Results Section
        results_frame = ttk.LabelFrame(main_frame, text="Search Results", padding="10")
        results_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Results text area with scrollbar
        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            width=80,
            height=15,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar
        self.status_label = ttk.Label(
            main_frame,
            text="Ready. Please enter your Pexels API key to get started.",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E))
    
    def initialize_client(self):
        """Initialize Pexels client with API key"""
        api_key = self.api_key_entry.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "Please enter a Pexels API key")
            return
        
        try:
            self.pexels_client = PexelsClient(api_key)
            self.search_btn.config(state=tk.NORMAL)
            self.update_status("Connected to Pexels API successfully!")
            
            # Save API key to .env file
            with open(".env", "w") as f:
                f.write(f"PEXELS_API_KEY={api_key}\n")
            
            messagebox.showinfo("Success", "Connected to Pexels API successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize client: {e}")
            self.update_status("Failed to connect to Pexels API")
    
    def search_videos(self):
        """Search for videos based on the prompt"""
        if not self.pexels_client:
            messagebox.showerror("Error", "Please connect to Pexels API first")
            return
        
        prompt = self.prompt_entry.get().strip()
        if not prompt:
            messagebox.showerror("Error", "Please enter a search prompt")
            return
        
        # Disable button during search
        self.search_btn.config(state=tk.DISABLED)
        self.update_status("Searching for videos...")
        
        # Run search in separate thread to avoid blocking UI
        thread = threading.Thread(target=self._search_videos_thread, args=(prompt,))
        thread.daemon = True
        thread.start()
    
    def _search_videos_thread(self, prompt):
        """Search videos in a separate thread"""
        try:
            results = self.pexels_client.search_videos(
                query=prompt,
                per_page=self.num_videos_var.get(),
                orientation=self.orientation_var.get(),
                size=self.size_var.get()
            )
            
            if results and "videos" in results:
                self.search_results = results["videos"]
                self.root.after(0, self._display_results, results)
            else:
                self.root.after(0, self._show_no_results)
        except Exception as e:
            self.root.after(0, self._show_error, str(e))
        finally:
            self.root.after(0, lambda: self.search_btn.config(state=tk.NORMAL))
    
    def _display_results(self, results):
        """Display search results"""
        videos = results.get("videos", [])
        total = results.get("total_results", 0)
        
        # Enable results text for editing
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        
        self.results_text.insert(tk.END, f"Found {total} total results. Showing {len(videos)} videos:\n\n")
        
        for idx, video in enumerate(videos, 1):
            self.results_text.insert(tk.END, f"Video {idx}:\n")
            self.results_text.insert(tk.END, f"  ID: {video.get('id')}\n")
            self.results_text.insert(tk.END, f"  Duration: {video.get('duration')} seconds\n")
            self.results_text.insert(tk.END, f"  Width: {video.get('width')}px, Height: {video.get('height')}px\n")
            self.results_text.insert(tk.END, f"  User: {video.get('user', {}).get('name', 'Unknown')}\n")
            self.results_text.insert(tk.END, f"  URL: {video.get('url')}\n")
            
            # Show available video files
            video_files = video.get("video_files", [])
            if video_files:
                self.results_text.insert(tk.END, f"  Available qualities: ")
                qualities = [vf.get('quality', 'unknown') for vf in video_files[:3]]
                self.results_text.insert(tk.END, f"{', '.join(qualities)}\n")
            
            self.results_text.insert(tk.END, "\n")
        
        # Disable editing
        self.results_text.config(state=tk.DISABLED)
        
        # Enable download button
        self.download_btn.config(state=tk.NORMAL)
        self.update_status(f"Found {len(videos)} videos")
    
    def _show_no_results(self):
        """Show message when no results found"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "No videos found for this search. Try a different prompt.")
        self.results_text.config(state=tk.DISABLED)
        self.update_status("No videos found")
        messagebox.showinfo("No Results", "No videos found for this search. Try a different prompt.")
    
    def _show_error(self, error_msg):
        """Show error message"""
        self.update_status(f"Error: {error_msg}")
        messagebox.showerror("Search Error", f"An error occurred while searching: {error_msg}")
    
    def download_videos(self):
        """Download the found videos"""
        if not self.search_results:
            messagebox.showerror("Error", "No videos to download. Search for videos first.")
            return
        
        # Ask user for download directory
        download_dir = filedialog.askdirectory(title="Select Download Directory")
        if not download_dir:
            return
        
        # Create downloads subdirectory
        downloads_path = os.path.join(download_dir, "downloads")
        os.makedirs(downloads_path, exist_ok=True)
        
        # Disable buttons during download
        self.download_btn.config(state=tk.DISABLED)
        self.search_btn.config(state=tk.DISABLED)
        
        # Run download in separate thread
        thread = threading.Thread(
            target=self._download_videos_thread,
            args=(downloads_path,)
        )
        thread.daemon = True
        thread.start()
    
    def _download_videos_thread(self, download_dir):
        """Download videos in a separate thread"""
        quality = self.quality_var.get()
        total = len(self.search_results)
        
        self.root.after(0, self.update_status, f"Downloading {total} videos...")
        
        downloaded = 0
        for idx, video in enumerate(self.search_results, 1):
            video_url = PexelsClient.get_video_file(video, quality=quality)
            
            if video_url:
                filename = f"video_{video.get('id')}_{idx}.mp4"
                filepath = os.path.join(download_dir, filename)
                
                self.root.after(0, self.update_status, f"Downloading video {idx}/{total}: {filename}")
                
                if self.pexels_client.download_video(video_url, filepath):
                    downloaded += 1
                    print(f"Downloaded: {filename}")
                else:
                    print(f"Failed to download video {idx}")
        
        # Re-enable buttons and show completion message
        self.root.after(0, lambda: self.download_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.search_btn.config(state=tk.NORMAL))
        self.root.after(
            0,
            self.update_status,
            f"Download complete! Downloaded {downloaded}/{total} videos to {download_dir}"
        )
        self.root.after(
            0,
            messagebox.showinfo,
            "Download Complete",
            f"Successfully downloaded {downloaded}/{total} videos to:\n{download_dir}"
        )
    
    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)


def main():
    """Main entry point"""
    root = tk.Tk()
    app = VideerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
