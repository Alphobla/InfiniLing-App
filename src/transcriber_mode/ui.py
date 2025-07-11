from tkinter import Tk, Frame, Label, Button, filedialog, messagebox, ttk, Text, Scrollbar, Canvas, Radiobutton, StringVar
import os
import threading
from .transcriber import Transcriber
import re
import shutil
from src.shared.reader_ui import ReaderUI
from src.shared.styles import center_top_window, Colors

class WhisperInterface:
    def __init__(self, master, back_callback=None):
        self.master = master
        self.back_callback = back_callback
        self.master.title("🎤 InfiniLing - Transcription Mode")
        center_top_window(self.master, width=500, height=550)
        self.master.configure(bg=Colors.BACKGROUND)

        # State management
        self.audio_file_path = None
        self.transcriber = None
        self.ui_state = "INITIAL"  # INITIAL, FILE_SELECTED, TRANSCRIBING, COMPLETED
        self.selected_model = StringVar(value="base")
        self.selected_language = StringVar(value="fr")  # Add language selection, default French
        
        # UI components references
        self.browse_button = None
        self.transcribe_button = None
        self.saved_frame = None
        self.model_frame = None
        self.progress_frame = None
        
        self.setup_styles()
        self.setup_ui()
        self.setup_styles()

    def setup_ui(self):
        # Clear existing content
        for widget in self.master.winfo_children():
            widget.destroy()
            
        # Main container
        main_frame = Frame(self.master, bg=Colors.BACKGROUND)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Header with back button
        header_frame = Frame(main_frame, bg=Colors.BACKGROUND)
        header_frame.pack(fill='x', pady=(0, 15))
        header_frame.grid_columnconfigure(0, weight=0)  # Back-Button
        header_frame.grid_columnconfigure(1, weight=1)  # Titel (zentriert)
        header_frame.grid_columnconfigure(2, weight=0)  # Platzhalter

        if self.back_callback:
            back_button = Button(
                header_frame, text="← Menu",
                command=self.back_callback,
                font=("Segoe UI", 10, "bold"),
                bg=Colors.BUTTON_SECONDARY, fg=Colors.TEXT_LIGHT,
                activebackground=Colors.BUTTON_SECONDARY,
                relief='flat', bd=0, pady=5, padx=15,
            )
            back_button.grid(row=0, column=0, sticky='w')

        title_label = Label(
            header_frame, text="🎤 Transcribr",
            font=("Segoe UI", 20, "bold"),
            bg=Colors.BACKGROUND, fg=Colors.DARK_GRAY
        )
        title_label.grid(row=0, column=1, sticky='n')
        # Unsichtbarer Platzhalter rechts
        right_spacer = Label(header_frame,  text="", bg=Colors.BACKGROUND)
        right_spacer.grid(row=0, column=2, sticky='e', padx=(50, 10))

        # Dynamic content area
        self.content_frame = Frame(main_frame, bg=Colors.BACKGROUND)
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
            # Ensure we have a valid audio file path
            if not self.audio_file_path or not os.path.exists(self.audio_file_path):
                self.master.after(0, lambda: self.transcription_error("No valid audio file selected"))
                return
                
            # Update status on main thread
            self.master.after(0, lambda: self.update_progress_status("Initializing transcriber..."))
            
            # Initialize transcriber with selected model
            model_size = self.selected_model.get()
            language_code = self.selected_language.get()  # Get selected language
            self.master.after(0, lambda: self.update_progress_status(f"Loading {model_size} model ..."))
            
            # Create new transcriber instance for this transcription
            print(f"Creating transcriber with model: {model_size}")  # Debug log
            
            # Show more detailed status during model loading
            self.master.after(0, lambda: self.update_progress_status(f"Loading {model_size} model ..."))
            
            transcriber = Transcriber(model_size=model_size)
            self.current_transcriber = transcriber  # Store for SRT creation
            print("Transcriber created successfully")  # Debug log
            
            self.master.after(0, lambda: self.update_progress_status(f"Model loaded! Starting transcription..."))
            self.master.after(0, lambda: self.update_progress_bar(1))
            # Prepare output paths in data directory
            data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                'data', 'transcriptions_and_audio'
            )
            os.makedirs(data_dir, exist_ok=True)
            
            # Use original filename
            original_name = os.path.splitext(os.path.basename(self.audio_file_path))[0]
            audio_dest = os.path.join(data_dir, f"{original_name}.mp3")
            srt_dest = os.path.join(data_dir, f"{original_name}.srt")
            
            # Perform transcription
            print(f"Starting transcription of: {self.audio_file_path}")  # Debug log
            
            # Callback for progress updates
            def progress_callback(msg, percent=None):
                self.master.after(0, lambda: self.update_progress_status(msg))
                if percent is not None:
                    self.master.after(0, lambda p=percent: self.update_progress_bar(p))

            # Perform transcription with progress callback, writing SRT to final destination
            transcription_success = transcriber.transcribe_and_write_srt(
                self.audio_file_path,
                srt_dest,  # Write SRT directly to data directory
                language=language_code,  # Use selected language
                progress_callback=progress_callback
            )
            print(f"Transcription completed.")  # Debug log
            
            if transcription_success:
                # Save audio file to data directory
                self.master.after(0, lambda: self.update_progress_status("Saving files..."))
                shutil.copy2(self.audio_file_path, audio_dest)
                print(f"Files saved: {audio_dest}, {srt_dest}")
                
                # Call completion handler on main thread
                self.master.after(0, self.transcription_complete)
            else:
                self.master.after(0, lambda: self.transcription_error("Transcription failed"))
            
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
            self.progress_bar['value'] = 0
        
        # Reset to initial state
        self.ui_state = "INITIAL"
        self.update_ui_state()
        
        # Show cancellation message
        messagebox.showinfo("Cancelled", "Transcription cancelled by user.")
    
    def update_progress_status(self, message):
        """Update progress status message"""
        if hasattr(self, 'progress_status'):
            self.progress_status.config(text=message)

    def update_progress_bar(self, percent):
        """Update progress bar percentage"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar['value'] = percent
            # Force update display
            self.progress_bar.update_idletasks()
            self.master.update_idletasks()  # Also update the master window


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
        
        # Reset to initial state
        self.ui_state = "INITIAL"
        self.audio_file_path = None
        self.update_ui_state()

        # Refresh the saved transcriptions list to show the new file
        if hasattr(self, 'saved_tiles_frame') and self.saved_tiles_frame.winfo_exists():
            self.populate_saved_transcriptions()

    def transcription_error(self, error_message):
        """Handle transcription error"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar['value'] = 0
        
        # Reset to initial state
        self.ui_state = "INITIAL"
        self.update_ui_state()
        
        # Show error message
        messagebox.showerror("Error", f"Transcription failed:\n{error_message}")

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
                    title_list = audio.get('title', [])
                    title = title_list[0] if title_list else None
                    if not title:
                        title = os.path.basename(base)
                except Exception:
                    title = os.path.basename(base)
                # Create tile/button
                btn = Button(
                    self.saved_tiles_frame, text=title, font=("Segoe UI", 11),
                    bg=Colors.SURFACE, fg=Colors.DARK_GRAY, relief='flat', bd=1, padx=5, pady=4,
                    anchor='w', justify='left',  # Align text to the left
                    activebackground=Colors.LIGHT_GRAY,
                    command=lambda m=mp3_path, s=srt_path: self.load_saved_transcription(m, s)
                )
                btn.pack(side='top', padx=8, pady=2, fill='x', expand=False)

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
        buttons_frame = Frame(self.content_frame, bg=Colors.BACKGROUND)
        buttons_frame.pack( pady=(0, 20), anchor='center')
        buttons_frame.grid_rowconfigure(0, minsize=150)  # Force row height
        buttons_frame.grid_columnconfigure(0, minsize=150)
        buttons_frame.grid_columnconfigure(1, minsize=150)

        self.browse_button = Button(
            buttons_frame,
            text="Browse \nAudio File",
            command=self.select_audio_file,
            font=("Segoe UI", 12, "bold"),
            bg=Colors.BUTTON_PAUSE, 
            fg=Colors.SURFACE,
            activebackground=Colors.BUTTON_PAUSE_HOVER,
            highlightthickness=1,
            highlightbackground=Colors.BUTTON_PAUSE_HOVER,
            relief='raised', bd=2,
        )
        self.browse_button.grid(row=0, column=0, sticky='nsew', padx=(0, 8))

        self.transcribe_button = Button(
            buttons_frame,
            text="Start \nTranscription",
            command=self.start_transcription,
            font=("Segoe UI", 12, "bold"),
            bg=Colors.BUTTON_PAUSE_HOVER,
            fg=Colors.MEDIUM_GRAY,  # Beautiful green background, grey text to show disabled
            activebackground=Colors.BUTTON_PAUSE_HOVER,
            relief='raised', bd=2,
            highlightthickness=1,
            highlightbackground=Colors.BUTTON_PAUSE_HOVER,
            state='disabled',
        )
        # Force button size to 150x150 pixels
        self.transcribe_button.grid(row=0, column=1, sticky='nsew', padx=(8, 0))

        # Saved transcriptions area
        self.build_saved_transcriptions()
    
    def build_file_selected_ui(self):
        """Build UI for file selected state"""
        # Buttons row
        buttons_frame = Frame(self.content_frame, bg=Colors.BACKGROUND)
        buttons_frame.pack( pady=(0, 20), anchor='center')
        buttons_frame.grid_rowconfigure(0, minsize=150) # Force row height
        buttons_frame.grid_columnconfigure(0, minsize=150)
        buttons_frame.grid_columnconfigure(1, minsize=150)

        # Browse button shows selected file
        if self.audio_file_path:
            filename = os.path.basename(self.audio_file_path)
            display_name = filename[:30] + "..." if len(filename) > 30 else filename
        else:
            display_name = "No file \nselected"
        
        self.browse_button = Button(
            buttons_frame,
            text=f"Selected: \n{display_name}",
            command=self.select_audio_file,
            font=("Segoe UI", 12, "bold"),
            bg=Colors.BUTTON_PAUSE, 
            fg=Colors.SURFACE,
            activebackground=Colors.BUTTON_PAUSE_HOVER,
            highlightthickness=1,
            highlightbackground=Colors.BUTTON_PAUSE_HOVER,
            relief='raised', bd=2,
        )
        self.browse_button.grid(row=0, column=0, sticky='nsew', padx=(0, 8))

        # Transcribe button is now enabled
        self.transcribe_button = Button(
            buttons_frame,
            text="Start Transcription",
            command=self.start_transcription,
            font=("Segoe UI", 12, "bold"),
            bg=Colors.BUTTON_PAUSE,
            fg=Colors.SURFACE,  # Beautiful green background, grey text to show disabled
            activebackground=Colors.BUTTON_SPEED_HOVER,
            highlightthickness=1,
            highlightbackground=Colors.BUTTON_PAUSE_HOVER,
            relief='raised', bd=2,
        )
        self.transcribe_button.grid(row=0, column=1, sticky='nsew', padx=(8, 0))

        # Model selection frame instead of saved transcriptions
        self.build_model_selection()
    
    def build_transcribing_ui(self):
        """Build UI for transcribing state (progress bar)"""
        # Progress frame
        self.progress_frame = Frame(self.content_frame, bg=Colors.SURFACE, relief='raised', bd=1)
        self.progress_frame.pack(fill='x', pady=(0, 20), padx=10)
        
        Label(
            self.progress_frame, text="🎯 Transcribing Audio...",
            font=("Segoe UI", 16, "bold"),
            bg=Colors.SURFACE, fg=Colors.DARK_GRAY
        ).pack(pady=(20, 10))

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, 
            mode='determinate',
            length=400,
            maximum=100,
            style='Modern.Horizontal.TProgressbar'
        )
        self.progress_bar.pack(pady=(0, 10))
        self.progress_bar['value'] = 0  # Start at 0%
        
        # Status label
        self.progress_status = Label(
            self.progress_frame,
            text="Initializing transcriber...",
            font=("Segoe UI", 11),
            bg=Colors.SURFACE, fg=Colors.MEDIUM_GRAY
        )
        self.progress_status.pack(pady=(0, 10))
        
        # Cancel button
        cancel_button = Button(
            self.progress_frame,
            text="Cancel Transcription",
            command=self.cancel_transcription,
            font=("Segoe UI", 11),
            bg=Colors.DANGER, fg=Colors.TEXT_LIGHT,
            activebackground=Colors.BUTTON_STOP_HOVER,
            relief='flat', bd=0, pady=5, padx=15
        )
        cancel_button.pack(pady=(0, 20))

        # Saved transcriptions still available for study
        self.build_saved_transcriptions()
    
    def build_model_selection(self):
        """Build model selection frame"""
        # Get audio file duration for time estimates
        audio_duration = self.get_audio_duration()
        
        # Model options: (description, time_factor, model_name)
        models = [
            ("Blitz guess", 0.3, "tiny"),
            ("Hurried estimate", 0.5, "base"),
            ("Measured notion", 0.8, "small"),
            ("Careful take", 1.2, "medium"),
            ("Deliberate precision", 2.0, "large")
        ]
        self.model_frame = Frame(self.content_frame, bg=Colors.SURFACE, relief='raised', bd=1)
        self.model_frame.pack(fill='both', expand=True, pady=(0, 10), padx=10)
        # Use a grid layout for better alignment
        selection_container = Frame(self.model_frame, bg=Colors.SURFACE)
        selection_container.pack(fill='both', expand=True, padx=10, pady=(0, 20))

        # Model selection column
        model_col = Frame(selection_container, bg=Colors.SURFACE)
        model_col.grid(row=0, column=0, sticky='n', padx=(0, 40))
        Label(model_col, text="Transcription Model", font=("Segoe UI", 12, "bold"), bg=Colors.SURFACE, fg=Colors.DARK_GRAY).pack(pady=(20, 15))
        for description, time_factor, model_name in models:
            estimated_time = self.format_estimated_time(audio_duration * time_factor)
            radio = Radiobutton(
                model_col,
                text=f"{description} (≈{estimated_time})",
                variable=self.selected_model,
                value=model_name,
                font=("Segoe UI", 11),
                bg=Colors.SURFACE,
                fg=Colors.DARK_GRAY,
                activebackground=Colors.SURFACE,
                selectcolor=Colors.SURFACE
            )
            radio.pack(anchor='w', pady=2)

        # Language selection column
        lang_col = Frame(selection_container, bg=Colors.SURFACE)
        lang_col.grid(row=0, column=1, sticky='n')
        Label(lang_col, text="Language", font=("Segoe UI", 12, "bold"), bg=Colors.SURFACE, fg=Colors.DARK_GRAY).pack(pady=(20, 15))
        languages = [
            ("French", "fr"),
            ("Russian", "ru"),
            ("Arabic", "ar"),
            ("English", "en")
        ]
        for lang_desc, lang_code in languages:
            lang_radio = Radiobutton(
                lang_col,
                text=lang_desc,
                variable=self.selected_language,
                value=lang_code,
                font=("Segoe UI", 11),
                bg=Colors.SURFACE,
                fg=Colors.DARK_GRAY,
                activebackground=Colors.SURFACE,
                selectcolor=Colors.SURFACE
            )
            lang_radio.pack(anchor='w', pady=2)

    def build_saved_transcriptions(self):
        """Build saved transcriptions area"""
        self.saved_frame = Frame(self.content_frame, bg=Colors.SURFACE, relief='raised', bd=1)
        self.saved_frame.pack(fill='both', expand=True, pady=(0, 10), padx=10)
        
        Label(
            self.saved_frame, text="Or choose saved transcriptions:",
            font=("Segoe UI", 12, "bold"),
            bg=Colors.SURFACE, fg=Colors.DARK_GRAY
        ).pack(pady=(15, 5), anchor='w', padx=16)

        # Scrollable area for tiles
        canvas = Canvas(self.saved_frame, bg=Colors.SURFACE, highlightthickness=0)
        scrollbar = Scrollbar(self.saved_frame, orient='vertical', command=canvas.yview)
        self.saved_tiles_frame = Frame(canvas, bg=Colors.SURFACE)
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

    def setup_styles(self):
        """Configure modern styling for progress bar and other elements"""
        style = ttk.Style()
        
        # Configure progress bar style with visible colors
        style.configure('Modern.Horizontal.TProgressbar',
                       background='#27ae60',  # Green progress color
                       troughcolor='#ecf0f1',  # Light grey background
                       borderwidth=1,
                       relief='flat',
                       thickness=20,  # Make it thicker
                       lightcolor='#27ae60',
                       darkcolor='#27ae60')
        
        # Map states for better visibility
        style.map('Modern.Horizontal.TProgressbar',
                 background=[('active', '#219a52')])
        
        # Alternative blue style for variety
        style.configure('Blue.Horizontal.TProgressbar',
                       background='#3498db',  # Blue progress color
                       troughcolor='#ecf0f1',  # Light grey background
                       borderwidth=1,
                       relief='flat',
                       thickness=20,
                       lightcolor='#3498db',
                       darkcolor='#3498db')

class SavedTranscriptionReview:
    """Modern review UI for saved transcriptions using shared components."""
    def __init__(self, master, srt_path, mp3_path, back_callback=None):
        self.master = master
        self.srt_path = srt_path
        self.mp3_path = mp3_path
        self.back_callback = back_callback
        
        # Process filename for display
        filename = os.path.basename(self.srt_path or self.mp3_path)
        display_name = os.path.splitext(filename)[0]
        if len(display_name) > 40:
            display_name = display_name[:37] + '...'
        
        # Use shared ReaderUI component
        self.review_ui = ReaderUI(
            master=self.master,
            title=f"{display_name}",
            audio_path=self.mp3_path,
            srt_path=self.srt_path,
            back_callback=self.back_callback
        )

def run_whisper_interface():
    root = Tk()
    app = WhisperInterface(root)
    root.mainloop()