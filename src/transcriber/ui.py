from tkinter import Tk, Frame, Label, Button, filedialog, messagebox, ttk, Text, Scrollbar, Canvas, Radiobutton, StringVar
import os
import threading
from .transcriber import Transcriber
import re
import shutil

class WhisperInterface:
    def __init__(self, master, back_callback=None):
        self.master = master
        self.back_callback = back_callback
        self.master.title("🎤 InfiniLing - Whisper Mode")
        self.master.geometry("700x600")
        self.master.configure(bg='#f8f9fa')

        # State management
        self.audio_file_path = None
        self.transcriber = None
        self.ui_state = "INITIAL"  # INITIAL, FILE_SELECTED, TRANSCRIBING, COMPLETED
        self.selected_model = StringVar(value="base")
        
        # UI components references
        self.browse_button = None
        self.transcribe_button = None
        self.saved_frame = None
        self.model_frame = None
        self.progress_frame = None
        
        self.setup_ui()

    def setup_ui(self):
        # Clear existing content
        for widget in self.master.winfo_children():
            widget.destroy()
            
        # Main container
        main_frame = Frame(self.master, bg='#f9f9fa')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Header with back button
        header_frame = Frame(main_frame, bg='#f9f9fa')
        header_frame.pack(fill='x', pady=(0, 15))

        if self.back_callback:
            back_button = Button(header_frame, text="← Menu", 
                               command=self.back_callback,
                               font=("Segoe UI", 10, "bold"),
                               bg='#95a5a6', fg='white',
                               activebackground='#7f8c8d',
                               relief='flat', bd=0, pady=5, padx=15)
            back_button.pack(side='left')

        # Title
        title_label = Label(main_frame, text="🎤 Audio Transcription", 
                           font=("Segoe UI", 20, "bold"), 
                           bg='#f9f9fa', fg='#2c3e50')
        title_label.pack(pady=(0, 20))

        # Dynamic content area
        self.content_frame = Frame(main_frame, bg='#f9f9fa')
        self.content_frame.pack(fill='both', expand=True)
        
        # Build UI based on current state
        self.update_ui_state()


    def select_audio_file(self):
        """Select an audio file for transcription"""
        filetypes = [
            ("All Audio Files", "*.mp3;*.wav;*.m4a;*.flac;*.aac;*.ogg"),
            ("MP3 Files", "*.mp3"),
            ("WAV Files", "*.wav"),
            ("M4A Files", "*.m4a"),
            ("FLAC Files", "*.flac"),
            ("All Files", "*.*")
        ]
        
        selected_path = filedialog.askopenfilename(
            title="Select Audio File for Transcription",
            filetypes=filetypes
        )
        
        if selected_path:
            self.audio_file_path = selected_path
            self.ui_state = "FILE_SELECTED"
            self.update_ui_state()

    def start_transcription(self):
        """Start the transcription process"""
        if not self.audio_file_path:
            messagebox.showwarning("Warning", "Please select an audio file first.")
            return
        
        # Switch to transcribing state
        self.ui_state = "TRANSCRIBING"
        self.update_ui_state()
        
        # Start transcription in background
        threading.Thread(
            target=self.transcribe_audio_background,
            daemon=True
        ).start()

    def transcribe_audio_background(self):
        """Transcribe audio in background thread"""
        try:
            # Update status on main thread
            self.master.after(0, lambda: self.update_progress_status("Initializing transcriber..."))
            
            # Initialize transcriber with selected model
            model_size = self.selected_model.get()
            self.master.after(0, lambda: self.update_progress_status(f"Loading {model_size} model (this may take a few minutes)..."))
            
            # Create new transcriber instance for this transcription
            print(f"Creating transcriber with model: {model_size}")  # Debug log
            
            # Show more detailed status during model loading
            self.master.after(0, lambda: self.update_progress_status(f"Downloading/Loading {model_size} model - please wait..."))
            
            transcriber = Transcriber(model_size=model_size)
            self.current_transcriber = transcriber  # Store for SRT creation
            print("Transcriber created successfully")  # Debug log
            
            self.master.after(0, lambda: self.update_progress_status(f"Model loaded! Starting transcription..."))
            
            # Get audio info for better progress estimates
            audio_duration = self.get_audio_duration()
            filename = os.path.basename(self.audio_file_path)
            
            
            
            # Perform transcription
            print(f"Starting transcription of: {self.audio_file_path}")  # Debug log
            
            # Callback for progress updates
            def progress_callback(msg):
                self.master.after(0, lambda: self.update_progress_status(msg))

            # Perform transcription with progress callback
            transcription = transcriber.transcribe_and_write_srt(
                self.audio_file_path,
                self.audio_file_path,
                language="fr",
                progress_callback=progress_callback
            )
            print(f"Transcription completed.")  # Debug log
            
            
        except Exception as e:
            # Handle errors on main thread
            error_message = str(e)
            print(f"Transcription error: {error_message}")  # Debug log
            import traceback
            traceback.print_exc()  # Print full traceback
            self.master.after(0, lambda msg=error_message: self.transcription_error(msg))

    def cancel_transcription(self):
        """Cancel the current transcription"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.stop()
        
        # Reset to initial state
        self.ui_state = "INITIAL"
        self.update_ui_state()
        
        # Show cancellation message
        messagebox.showinfo("Cancelled", "Transcription cancelled by user.")
    
    def update_progress_status(self, message):
        """Update progress status message"""
        if hasattr(self, 'progress_status'):
            self.progress_status.config(text=message)

    def save_transcription_files(self, transcription):
        """Save audio and transcription files to data directory"""
        try:
            # Get data directory
            data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                'data', 'transcriptions_and_audio'
            )
            os.makedirs(data_dir, exist_ok=True)
            
            # Use original filename
            original_name = os.path.splitext(os.path.basename(self.audio_file_path))[0]
            
            # Copy audio file
            audio_dest = os.path.join(data_dir, f"{original_name}.mp3")
            shutil.copy2(self.audio_file_path, audio_dest)
            # SRT is already written by the transcriber with progress, so skip writing it again.
        except Exception as e:
            raise Exception(f"Failed to save files: {e}")

    def save_as_srt(self, transcription, filepath):
        """Save transcription as SRT file with timestamps"""
        try:
            # For now, create a simple SRT with the full transcription
            # In future, you might want to split into segments
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("1\n")
                f.write("00:00:00,000 --> 00:10:00,000\n")
                f.write(transcription.strip())
                f.write("\n\n")
        except Exception as e:
            raise Exception(f"Failed to save SRT: {e}")

    def transcription_complete(self):
        """Handle transcription completion"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.stop()
        
        # Reset to initial state
        self.ui_state = "INITIAL"
        self.audio_file_path = None
        self.update_ui_state()
        
        # Show success message
        messagebox.showinfo("Success", "Transcription completed and saved!")

    def transcription_error(self, error_message):
        """Handle transcription error"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.stop()
        
        # Reset to initial state
        self.ui_state = "INITIAL"
        self.update_ui_state()
        
        # Show error message
        messagebox.showerror("Error", f"Transcription failed:\n{error_message}")

    # Keep the old transcribe_audio method for backward compatibility
    def transcribe_audio(self):
        """Legacy method - redirects to new workflow"""
        self.start_transcription()

    # Legacy save method - not used in new workflow
    def save_transcription(self):
        """Legacy save method - transcriptions are now auto-saved"""
        messagebox.showinfo("Info", "Transcriptions are automatically saved to the data folder.")

    def populate_saved_transcriptions(self):
        """Scan the transcriptions_and_audio folder and create a tile for each MP3/SRT pair."""
        import glob
        from mutagen.easyid3 import EasyID3
        from mutagen.mp3 import MP3
        folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'transcriptions_and_audio')
        mp3_files = glob.glob(os.path.join(folder, '*.mp3'))
        srt_files = set(os.path.splitext(f)[0] for f in glob.glob(os.path.join(folder, '*.srt')))
        for widget in self.saved_tiles_frame.winfo_children():
            widget.destroy()
        for mp3_path in mp3_files:
            base = os.path.splitext(mp3_path)[0]
            srt_path = base + '.srt'
            if base in srt_files and os.path.exists(srt_path):
                # Try to get title from MP3 metadata
                try:
                    audio = MP3(mp3_path, ID3=EasyID3)
                    title = audio.get('title', [None])[0]
                    if not title:
                        title = os.path.basename(base)
                except Exception:
                    title = os.path.basename(base)
                # Create tile/button
                btn = Button(self.saved_tiles_frame, text=title, font=("Segoe UI", 11, "bold"),
                             bg='#f9f9f9', fg='#2c3e50', relief='raised', bd=2, padx=10, pady=10,
                             anchor='w', justify='left',  # Align text to the left
                             command=lambda m=mp3_path, s=srt_path: self.load_saved_transcription(m, s))
                btn.pack(side='top', padx=8, pady=8, fill='x', expand=False)

    def load_saved_transcription(self, mp3_path, srt_path):
        """Show the modern review UI for the selected saved transcription and audio."""
        def return_to_main():
            # Restore the main Whisper interface
            for widget in self.master.winfo_children():
                widget.destroy()
            self.setup_ui()
        SavedTranscriptionReview(self.master, srt_path, mp3_path, back_callback=return_to_main)

    def update_ui_state(self):
        """Update UI based on current state"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        if self.ui_state == "INITIAL":
            self.build_initial_ui()
        elif self.ui_state == "FILE_SELECTED":
            self.build_file_selected_ui()
        elif self.ui_state == "TRANSCRIBING":
            self.build_transcribing_ui()
    
    def build_initial_ui(self):
        """Build UI for initial state (no file selected)"""
        # Buttons row
        buttons_frame = Frame(self.content_frame, bg='#f9f9fa')
        buttons_frame.pack(fill='x', pady=(0, 20))
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

        self.browse_button = Button(
            buttons_frame,
            text="Browse New Audio File",
            command=self.select_audio_file,
            font=("Segoe UI", 13, "bold"),
            bg='#3498db', fg='white',
            activebackground='#2980b9',
            relief='flat', bd=0,
            height=4
        )
        self.browse_button.grid(row=0, column=0, sticky='nsew', padx=(0, 8))

        self.transcribe_button = Button(
            buttons_frame,
            text="Start Transcription",
            command=self.start_transcription,
            font=("Segoe UI", 13, "bold"),
            bg='#6c757d', fg='#adb5bd',  # Grey/disabled appearance
            relief='flat', bd=0,
            height=4,
            state='disabled'
        )
        self.transcribe_button.grid(row=0, column=1, sticky='nsew', padx=(8, 0))

        # Saved transcriptions area
        self.build_saved_transcriptions()
    
    def build_file_selected_ui(self):
        """Build UI for file selected state"""
        # Buttons row
        buttons_frame = Frame(self.content_frame, bg='#f9f9fa')
        buttons_frame.pack(fill='x', pady=(0, 20))
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

        # Browse button shows selected file
        filename = os.path.basename(self.audio_file_path)
        display_name = filename[:30] + "..." if len(filename) > 30 else filename
        
        self.browse_button = Button(
            buttons_frame,
            text=f"Selected: {display_name}",
            command=self.select_audio_file,
            font=("Segoe UI", 11, "bold"),
            bg='#28a745', fg='white',
            activebackground='#218838',
            relief='flat', bd=0,
            height=4
        )
        self.browse_button.grid(row=0, column=0, sticky='nsew', padx=(0, 8))

        # Transcribe button is now enabled
        self.transcribe_button = Button(
            buttons_frame,
            text="Start Transcription",
            command=self.start_transcription,
            font=("Segoe UI", 13, "bold"),
            bg='#27ae60', fg='white',
            activebackground='#219a52',
            relief='flat', bd=0,
            height=4,
            state='normal'
        )
        self.transcribe_button.grid(row=0, column=1, sticky='nsew', padx=(8, 0))

        # Model selection frame instead of saved transcriptions
        self.build_model_selection()
    
    def build_transcribing_ui(self):
        """Build UI for transcribing state (progress bar)"""
        # Progress frame
        self.progress_frame = Frame(self.content_frame, bg='#ffffff', relief='raised', bd=1)
        self.progress_frame.pack(fill='x', pady=(0, 20), padx=10)
        
        Label(self.progress_frame, text="🎯 Transcribing Audio...", 
              font=("Segoe UI", 16, "bold"), 
              bg='#ffffff', fg='#2c3e50').pack(pady=(20, 10))

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, 
            mode='indeterminate',
            length=400
        )
        self.progress_bar.pack(pady=(0, 10))
        self.progress_bar.start()
        
        # Status label
        self.progress_status = Label(
            self.progress_frame,
            text="Initializing transcriber...",
            font=("Segoe UI", 11),
            bg='#ffffff', fg='#6c757d'
        )
        self.progress_status.pack(pady=(0, 10))
        
        # Cancel button
        cancel_button = Button(
            self.progress_frame,
            text="Cancel Transcription",
            command=self.cancel_transcription,
            font=("Segoe UI", 11),
            bg='#dc3545', fg='white',
            activebackground='#c82333',
            relief='flat', bd=0, pady=5, padx=15
        )
        cancel_button.pack(pady=(0, 20))

        # Saved transcriptions still available for study
        self.build_saved_transcriptions()
    
    def build_model_selection(self):
        """Build model selection frame"""
        self.model_frame = Frame(self.content_frame, bg='#ffffff', relief='raised', bd=1)
        self.model_frame.pack(fill='both', expand=True, pady=(0, 10), padx=10)
        
        Label(self.model_frame, text="Choose Transcription Model", 
              font=("Segoe UI", 14, "bold"), 
              bg='#ffffff', fg='#2c3e50').pack(pady=(20, 15))

        # Get audio file duration for time estimates
        audio_duration = self.get_audio_duration()
        
        # Model options with estimated processing times
        models = [
            ("tiny", "Fastest, least accurate", 0.3),      # ~30% of audio length
            ("base", "Good balance of speed and accuracy", 0.5),  # ~50% of audio length  
            ("small", "Better accuracy, slower", 0.8),     # ~80% of audio length
            ("medium", "High accuracy, slow", 1.2),        # ~120% of audio length
            ("large", "Highest accuracy, very slow", 2.0)  # ~200% of audio length
        ]
        
        model_container = Frame(self.model_frame, bg='#ffffff')
        model_container.pack(expand=True, fill='both', padx=30, pady=(0, 20))
        
        for model, description, time_factor in models:
            model_row = Frame(model_container, bg='#ffffff')
            model_row.pack(fill='x', pady=8)
            
            # Calculate estimated time
            estimated_time = self.format_estimated_time(audio_duration * time_factor)
            
            radio = Radiobutton(
                model_row,
                text=f"{model.title()}: {description} (≈{estimated_time})",
                variable=self.selected_model,
                value=model,
                font=("Segoe UI", 11),
                bg='#ffffff',
                fg='#2c3e50',
                activebackground='#ffffff',
                selectcolor='#ffffff'
            )
            radio.pack(anchor='w')
    
    def build_saved_transcriptions(self):
        """Build saved transcriptions area"""
        self.saved_frame = Frame(self.content_frame, bg='#ffffff', relief='raised', bd=1)
        self.saved_frame.pack(fill='both', expand=True, pady=(0, 10), padx=10)
        
        Label(self.saved_frame, text="Or choose saved transcriptions", 
              font=("Segoe UI", 12, "bold"), 
              bg='#ffffff', fg='#2c3e50').pack(pady=(15, 5), anchor='w', padx=10)

        # Scrollable area for tiles
        canvas = Canvas(self.saved_frame, bg='#ffffff', highlightthickness=0)
        scrollbar = Scrollbar(self.saved_frame, orient='vertical', command=canvas.yview)
        self.saved_tiles_frame = Frame(canvas, bg='#ffffff')
        self.saved_tiles_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.saved_tiles_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        self.populate_saved_transcriptions()
        
        # Set initial state to no file selected
        self.ui_state = "INITIAL"

    def get_audio_duration(self):
        """Get duration of the selected audio file in seconds"""
        if not self.audio_file_path or not os.path.exists(self.audio_file_path):
            return 300  # Default to 5 minutes if file not accessible
        
        try:
            # Try using mutagen to get duration
            from mutagen.mp3 import MP3
            from mutagen.wave import WAVE
            from mutagen.mp4 import MP4
            
            file_ext = os.path.splitext(self.audio_file_path)[1].lower()
            
            if file_ext == '.mp3':
                audio = MP3(self.audio_file_path)
                return audio.info.length
            elif file_ext == '.wav':
                audio = WAVE(self.audio_file_path)
                return audio.info.length
            elif file_ext in ['.m4a', '.mp4']:
                audio = MP4(self.audio_file_path)
                return audio.info.length
            else:
                # For other formats, estimate based on file size (rough approximation)
                file_size = os.path.getsize(self.audio_file_path)
                # Assume ~1MB per minute for compressed audio
                return (file_size / (1024 * 1024)) * 60
                
        except Exception:
            # If duration detection fails, estimate based on file size
            try:
                file_size = os.path.getsize(self.audio_file_path)
                return (file_size / (1024 * 1024)) * 60  # Rough estimate
            except:
                return 300  # Default fallback
    
    def format_estimated_time(self, seconds):
        """Format estimated processing time in a human-readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m"
        else:
            hours = int(seconds / 3600)
            remaining_minutes = int((seconds % 3600) / 60)
            if remaining_minutes > 0:
                return f"{hours}h {remaining_minutes}m"
            else:
                return f"{hours}h"
    
    def format_duration(self, seconds):
        """Format audio duration in a human-readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            remaining_seconds = int(seconds % 60)
            if remaining_seconds > 0:
                return f"{minutes}m {remaining_seconds}s"
            else:
                return f"{minutes}m"
        else:
            hours = int(seconds / 3600)
            remaining_minutes = int((seconds % 3600) / 60)
            if remaining_minutes > 0:
                return f"{hours}h {remaining_minutes}m"
            else:
                return f"{hours}h"

class SavedTranscriptionReview:
    """Modern review UI for saved transcriptions with audio bar, similar to Wordstory, with SRT highlighting."""
    def __init__(self, master, srt_path, mp3_path, back_callback=None):
        self.master = master
        self.srt_path = srt_path
        self.mp3_path = mp3_path
        self.back_callback = back_callback
        self.vlc_available = False
        try:
            import vlc
            self.vlc = vlc
            self.vlc_available = True
        except ImportError:
            self.vlc = None
        self.audio_speed = 1.0
        self.audio_length = 1
        self._slider_dragging = False
        self.srt_segments = []
        self.current_segment_idx = -1
        self.setup_ui()

    def setup_ui(self):
        for widget in self.master.winfo_children():
            widget.destroy()
        self.master.title("🎤 InfiniLing - Transcription Review")
        self.master.configure(bg='#ffffff')
        self.master.geometry("900x700")
        self.master.minsize(700, 500)

        # Configure master grid to have a content row and a fixed controls row
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=0)
        self.master.grid_columnconfigure(0, weight=1)

        # --- Main Content Frame (everything except audio controls) ---
        content_container = Frame(self.master, bg='#ffffff')
        content_container.grid(row=0, column=0, sticky='nsew')
        content_container.grid_columnconfigure(0, weight=1)
        content_container.grid_rowconfigure(1, weight=1) # Allow text area to expand

        # Header
        header = Frame(content_container, bg='#f8f9fa')
        header.grid(row=0, column=0, sticky='ew')
        if self.back_callback:
            Button(header, text="← Back", command=self.back_callback,
                   font=("Segoe UI", 11, "bold"), bg='#95a5a6', fg='white',
                   activebackground='#7f8c8d', relief='flat', bd=0, pady=5, padx=15).pack(side='left')
        Label(header, text="Transcription Review", font=("Segoe UI", 18, "bold"),
              bg='#f9f9fa', fg='#2c3e50').pack(side='left', padx=20)

        # Main text area
        main_frame = Frame(content_container, bg='#ffffff')
        main_frame.grid(row=1, column=0, sticky='nsew', padx=30, pady=(10, 10))
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        Label(main_frame, text="Transcription Text", font=("Segoe UI", 13, "bold"),
              bg='#ffffff', fg='#2c3e50').grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        text_frame = Frame(main_frame, bg='#ffffff')
        text_frame.grid(row=1, column=0, sticky='nsew')
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)

        self.text_widget = Text(text_frame, font=("Segoe UI", 12), wrap='word',
                               bg='#fafafa', fg='#212529', relief='flat', bd=0,
                               selectbackground='#0078d4', selectforeground='white', padx=20, pady=15)
        scrollbar = Scrollbar(text_frame, orient='vertical', command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        
        self.text_widget.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.parse_and_display_srt()

        # Audio controls at bottom, in the master's second row
        self.audio_controls_frame = Frame(self.master, bg='#f9f9fa')
        self.audio_controls_frame.grid(row=1, column=0, sticky='ew', padx=30, pady=10)
        self.setup_audio_controls()

    def parse_and_display_srt(self):
        self.srt_segments = []
        self.text_widget.config(state='normal')
        self.text_widget.delete('1.0', 'end')
        try:
            with open(self.srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            # Parse SRT
            pattern = re.compile(r"(\d+)\s+([\d:,]+) --> ([\d:,]+)\s+([\s\S]*?)(?=\n\d+\n|\Z)")
            for match in pattern.finditer(srt_content):
                idx = int(match.group(1))
                start = self.srt_time_to_seconds(match.group(2))
                end = self.srt_time_to_seconds(match.group(3))
                text = match.group(4).strip().replace('\n', ' ')
                self.srt_segments.append({'idx': idx, 'start': start, 'end': end, 'text': text})
            # Insert lines and tag them
            for i, seg in enumerate(self.srt_segments):
                tag = f'seg_{i}'
                self.text_widget.insert('end', seg['text'] + '\n', tag)
            self.text_widget.config(state='disabled')
        except Exception as e:
            self.text_widget.insert('1.0', f"Failed to load transcription: {e}")
            self.text_widget.config(state='disabled')

    def srt_time_to_seconds(self, s):
        h, m, rest = s.split(':')
        s, ms = rest.split(',')
        return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000

    def setup_audio_controls(self):
        for widget in self.audio_controls_frame.winfo_children():
            widget.destroy()

        # Configure grid for the main audio controls frame
        self.audio_controls_frame.grid_columnconfigure(0, weight=1)

        if self.vlc_available and self.mp3_path and os.path.exists(self.mp3_path):
            try:
                self.vlc_instance = self.vlc.Instance()
                self.vlc_player = self.vlc_instance.media_player_new()
                media = self.vlc_instance.media_new(self.mp3_path)
                self.vlc_player.set_media(media)
            except Exception:
                self.vlc_available = False
        
        if self.vlc_available and self.mp3_path and os.path.exists(self.mp3_path):
            # --- Playback controls row ---
            playback_frame = Frame(self.audio_controls_frame, bg='#f9f9fa')
            playback_frame.grid(row=0, column=0, sticky='ew', pady=(0, 5))
            
            self.play_btn = Button(playback_frame, text="▶ Play", command=self.play_audio,
                                   font=("Segoe UI", 11, "bold"), bg='#27ae60', fg='white', relief='flat', bd=0)
            self.play_btn.pack(side='left', padx=5)
            self.pause_btn = Button(playback_frame, text="⏸ Pause", command=self.pause_audio,
                                    font=("Segoe UI", 11), bg='#f9f9fa', fg='#2c3e50', relief='flat', bd=0)
            self.pause_btn.pack(side='left', padx=5)
            self.stop_btn = Button(playback_frame, text="⏹ Stop", command=self.stop_audio,
                                   font=("Segoe UI", 11), bg='#f9f9fa', fg='#2c3e50', relief='flat', bd=0)
            self.stop_btn.pack(side='left', padx=5)
            Button(playback_frame, text="⏪ -4s", command=lambda: self.jump_audio(-4), font=("Segoe UI", 11), bg='#f9f9fa', fg='#2c3e50', relief='flat', bd=0).pack(side='left', padx=5)
            Button(playback_frame, text="+4s ⏩", command=lambda: self.jump_audio(4), font=("Segoe UI", 11), bg='#f9f9fa', fg='#2c3e50', relief='flat', bd=0).pack(side='left', padx=5)
            Button(playback_frame, text="🐌 -5%", command=lambda: self.change_speed(-0.05), font=("Segoe UI", 11), bg='#f9f9fa', fg='#2c3e50', relief='flat', bd=0).pack(side='left', padx=2)
            Button(playback_frame, text="🐇 +5%", command=lambda: self.change_speed(0.05), font=("Segoe UI", 11), bg='#f9f9fa', fg='#2c3e50', relief='flat', bd=0).pack(side='left', padx=2)
            
            # --- Progress bar row (directly below controls) ---
            from tkinter import DoubleVar
            self.audio_progress = DoubleVar()

            # Add a custom style for a thicker progress bar
            style = ttk.Style(self.audio_controls_frame)
            # The 'sliderthickness' option makes the slider itself thicker.
            style.configure("Thick.Horizontal.TScale", sliderthickness=25)

            self.audio_progress_bar = ttk.Scale(
                self.audio_controls_frame,
                variable=self.audio_progress,
                from_=0,
                to=100,
                orient='horizontal',
                command=self.slider_seek_update,
                style="Thick.Horizontal.TScale" # Apply the custom style
            )
            self.audio_progress_bar.grid(row=1, column=0, sticky='ew', padx=5, pady=(5, 5))
            self.audio_progress_bar.bind('<ButtonRelease-1>', self.slider_seek_commit)
            self.audio_progress_bar.focus_set()

            # Add mouse wheel scrolling support
            def on_scroll(event):
                if hasattr(self, 'audio_progress'):
                    current = self.audio_progress.get()
                    # Increase sensitivity for better user experience
                    delta = 2 if event.delta > 0 else -2
                    new_value = max(0, min(100, current + delta))
                    self.audio_progress.set(new_value)
                    self.slider_seek_commit() # Commit immediately on scroll
            self.audio_progress_bar.bind('<MouseWheel>', on_scroll)
            # For Linux
            self.audio_progress_bar.bind('<Button-4>', lambda e: on_scroll(type('', (), {'delta': 120})))
            self.audio_progress_bar.bind('<Button-5>', lambda e: on_scroll(type('', (), {'delta': -120})))

            self.update_audio_progress()
        else:
            Label(self.audio_controls_frame, text="No audio file available or VLC not installed.",
                  font=("Segoe UI", 11), bg='#f9f9fa', fg='#dc3545').pack(pady=10)

    def play_audio(self):
        if hasattr(self, 'vlc_player'):
            self.vlc_player.play()
            self.vlc_player.set_rate(self.audio_speed)
            self.update_audio_progress()
    def pause_audio(self):
        if hasattr(self, 'vlc_player'):
            self.vlc_player.pause()
    def stop_audio(self):
        if hasattr(self, 'vlc_player'):
            self.vlc_player.stop()
            if hasattr(self, 'audio_progress'):
                self.audio_progress.set(0)
    def jump_audio(self, seconds):
        if hasattr(self, 'vlc_player') and self.audio_length > 0:
            current_time = self.vlc_player.get_time()
            new_time = max(0, min(self.audio_length * 1000, current_time + seconds * 1000))
            self.vlc_player.set_time(int(new_time))
    def change_speed(self, delta):
        self.audio_speed = max(0.5, min(2.0, self.audio_speed + delta))
        if hasattr(self, 'vlc_player'):
            self.vlc_player.set_rate(self.audio_speed)
        if hasattr(self, 'play_btn'):
            self.play_btn.config(text=f"▶ Play ({int(self.audio_speed*100)}%)")
    def slider_seek_update(self, value):
        self._slider_dragging = True
    def slider_seek_commit(self, event=None):
        if hasattr(self, 'vlc_player') and self.audio_length > 0:
            position = float(self.audio_progress.get()) / 100.0
            self.vlc_player.set_position(position)
        self._slider_dragging = False
    def update_audio_progress(self):
        # Highlight SRT line in sync with audio
        if hasattr(self, 'vlc_player') and hasattr(self, 'audio_progress') and not self._slider_dragging:
            if self.vlc_player.is_playing():
                length = self.vlc_player.get_length()
                if length > 0:
                    self.audio_length = length / 1000
                    current_time = self.vlc_player.get_time() / 1000.0
                    if current_time >= 0:
                        progress = (current_time / self.audio_length) * 100
                        self.audio_progress.set(progress)
                        self.highlight_current_segment(current_time)
        if hasattr(self, 'master'):
            self.master.after(200, self.update_audio_progress)
    def highlight_current_segment(self, current_time):
        # Remove previous highlight
        for i in range(len(self.srt_segments)):
            tag = f'seg_{i}'
            self.text_widget.tag_configure(tag, background='#fafafa')
        # Find and highlight the current segment
        for i, seg in enumerate(self.srt_segments):
            if seg['start'] <= current_time <= seg['end']:
                tag = f'seg_{i}'
                self.text_widget.tag_configure(tag, background='#fff3cd')
                break

def run_whisper_interface():
    root = Tk()
    app = WhisperInterface(root)
    root.mainloop()