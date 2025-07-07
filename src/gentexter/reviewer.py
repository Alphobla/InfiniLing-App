#!/usr/bin/env python3
"""
Review Interface

Handles the vocabulary review process with modern UI.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import threading
from typing import List, Tuple, Optional, Set

# Try to import VLC, handle gracefully if not available
try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False
    print("Warning: VLC not available. Audio playback will be disabled.")


class ReviewInterface:
    """Modern vocabulary review interface with audio support."""
    
    def __init__(self, vocab_list: List[Tuple[str, str, str]], 
                 vocabulary_selector,
                 git_manager=None,
                 generated_text: Optional[str] = None, 
                 audio_path: Optional[str] = None,
                 example_sentences: Optional[dict] = None):
        
        # Handle both 2-tuple and 3-tuple formats
        self.vocab_list = []
        for vocab_entry in vocab_list:
            if len(vocab_entry) == 2:
                source, target = vocab_entry
                pronunciation = ""
            else:
                source, target, pronunciation = vocab_entry
            self.vocab_list.append((source, target, pronunciation))
        
        self.vocabulary_selector = vocabulary_selector
        self.git_manager = git_manager
        self.generated_text = generated_text
        self.audio_path = audio_path
        self.example_sentences = example_sentences or {}
        self.difficult_words: Set[Tuple[str, str]] = set()
        self.review_complete = False
        self.tiles = []
        self.save_allowed = False
        
        # Audio related variables
        self.vlc_available = VLC_AVAILABLE
        self.audio_speed = 0.9
        self.audio_length = 0
        self._slider_dragging = False
        
        # Initialize VLC if available
        if self.vlc_available and self.audio_path and os.path.exists(self.audio_path):
            try:
                self.vlc_instance = vlc.Instance()
                if self.vlc_instance is None:
                    raise Exception("VLC instance could not be created")
            except Exception as e:
                print(f"Warning: VLC initialization failed: {e}")
                self.vlc_available = False
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("📚 InfiniLing - Vocabulary Review")
        self.root.geometry("1200x800")
        self.root.configure(bg='#ffffff')
        self.root.minsize(1000, 600)
        
        # Setup UI
        self.setup_modern_styles()
        self.setup_layout()
        self.setup_start_view()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Sync with Git on startup
        if self.git_manager:
            print("🔄 Syncing with Git repository...")
            self.git_manager.sync_async("pull")
    
    def setup_modern_styles(self):
        """Configure modern styling for the application."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure button styles
        style.configure('Accent.TButton', 
                       font=('Segoe UI', 12, 'bold'),
                       padding=(25, 15),
                       relief='flat',
                       borderwidth=0,
                       background='#0078d4',
                       foreground='white')
        
        style.map('Accent.TButton',
                 background=[('active', '#106ebe'),
                           ('pressed', '#005a9e')])
        
        style.configure('Modern.TButton', 
                       font=('Segoe UI', 11),
                       padding=(20, 12),
                       relief='flat',
                       borderwidth=0)
        
        style.configure('Tile.TButton', 
                       font=('Segoe UI', 11),
                       padding=(15, 10),
                       relief='flat',
                       borderwidth=1,
                       background='#f8f9fa',
                       foreground='#212529')
        
        style.map('Tile.TButton',
                 background=[('active', '#e9ecef'),
                           ('pressed', '#dee2e6')])
        
        style.configure('Selected.TButton', 
                       font=('Segoe UI', 11, 'bold'),
                       padding=(15, 10),
                       relief='flat',
                       borderwidth=2,
                       background='#fff3cd',
                       foreground='#856404')
        
        # Configure frame and label styles
        style.configure('Card.TFrame',
                       background='#ffffff',
                       relief='flat',
                       borderwidth=1)
        
        style.configure('Heading.TLabel',
                       font=('Segoe UI', 20, 'bold'),
                       background='#ffffff',
                       foreground='#212529')
        
        style.configure('Subheading.TLabel',
                       font=('Segoe UI', 14),
                       background='#ffffff',
                       foreground='#6c757d')
        
        style.configure('Body.TLabel',
                       font=('Segoe UI', 11),
                       background='#ffffff',
                       foreground='#495057')
    
    def setup_layout(self):
        """Setup the main layout with audio controls at bottom."""
        # Audio controls at bottom
        self.audio_controls_frame = ttk.Frame(self.root)
        self.audio_controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        # Content frame fills the rest
        self.content_frame = ttk.Frame(self.root)
        self.content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Setup audio controls once
        self.setup_audio_controls()
    
    def setup_start_view(self):
        """Setup the initial reading/text view."""
        self.clear_content_frame()
        
        # Main container
        main_frame = ttk.Frame(self.content_frame, style='Card.TFrame', padding="40")
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Header with title and action button
        header_frame = ttk.Frame(main_frame, style='Card.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title = ttk.Label(header_frame, text="📖 Reading Practice", style='Heading.TLabel')
        title.pack(side=tk.LEFT)
        
        skip_btn = ttk.Button(header_frame, text="Skip to Vocabulary Review", 
                             command=self.setup_tile_view, style='Accent.TButton')
        skip_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Display generated text if available
        if self.generated_text:
            text_frame = ttk.Frame(main_frame, style='Card.TFrame')
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            # Scrollable text widget
            text_container = ttk.Frame(text_frame)
            text_container.pack(fill=tk.BOTH, expand=True)
            
            text_widget = tk.Text(text_container, 
                                wrap=tk.WORD, 
                                font=('Segoe UI', 12), 
                                bg='#fafafa', 
                                fg='#212529',
                                relief='flat', 
                                borderwidth=0,
                                selectbackground='#0078d4',
                                selectforeground='white',
                                padx=20, pady=15)
            
            scrollbar = ttk.Scrollbar(text_container, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget.insert('1.0', self.generated_text)
            text_widget.config(state='disabled')
        else:
            # Show vocabulary list if no text
            vocab_frame = ttk.Frame(main_frame, style='Card.TFrame')
            vocab_frame.pack(fill=tk.BOTH, expand=True)
            
            vocab_label = ttk.Label(vocab_frame, text="📚 Today's Vocabulary:", style='Subheading.TLabel')
            vocab_label.pack(pady=(0, 15))
            
            for i, (word, translation, pronunciation) in enumerate(self.vocab_list, 1):
                word_text = f"{i:2}. {word} → {translation}"
                if pronunciation:
                    word_text += f" [{pronunciation}]"
                
                word_label = ttk.Label(vocab_frame, text=word_text, style='Body.TLabel')
                word_label.pack(anchor='w', pady=2)
        
        # Continue button
        continue_btn = ttk.Button(main_frame, text="Continue to Vocabulary Review", 
                                 command=self.setup_tile_view, style='Accent.TButton')
        continue_btn.pack(pady=20)
    
    def setup_tile_view(self):
        """Setup the vocabulary selection view."""
        self.clear_content_frame()
        
        # Main container
        main_frame = ttk.Frame(self.content_frame, style='Card.TFrame', padding="40")
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Title section
        title = ttk.Label(main_frame, text="🎯 Select words you want to review again", style='Heading.TLabel')
        title.pack(pady=(0, 20))
        
        subtitle = ttk.Label(main_frame, text="Click on vocabulary items that need more practice", style='Subheading.TLabel')
        subtitle.pack(pady=(0, 30))
        
        # Tiles grid (4 columns x 5 rows, max 20 items)
        grid_frame = ttk.Frame(main_frame)
        grid_frame.pack(expand=True)
        
        self.tiles = []
        cols = 4
        rows = 5
        max_tiles = cols * rows
        vocab_to_show = self.vocab_list[:max_tiles]
        
        for i, (source, target, pronunciation) in enumerate(vocab_to_show):
            if pronunciation:
                tile_text = f"{source} [{pronunciation}] → {target}"
            else:
                tile_text = f"{source} → {target}"
            
            tile = ttk.Button(grid_frame, text=tile_text, width=30, style='Tile.TButton')
            row = i // cols
            col = i % cols
            tile.grid(row=row, column=col, padx=15, pady=10, sticky="ew")
            tile.config(command=lambda t=tile, w=(source, target): self.toggle_tile(t, w))
            self.tiles.append((tile, (source, target)))
        
        # Configure grid weights
        for col in range(cols):
            grid_frame.columnconfigure(col, weight=1)
        
        # Continue button
        continue_btn = ttk.Button(main_frame, text="Continue", 
                                 command=self.setup_results_view, style='Accent.TButton')
        continue_btn.pack(pady=20)
    
    def toggle_tile(self, tile, word):
        """Toggle word selection in tile view."""
        if word in self.difficult_words:
            self.difficult_words.remove(word)
            tile.config(style='Tile.TButton')
        else:
            self.difficult_words.add(word)
            tile.config(style='Selected.TButton')
    
    def setup_results_view(self):
        """Setup the final results and statistics view."""
        self.save_allowed = True
        self.clear_content_frame()
        
        # Use regular tk.Frame for white background
        main_frame = tk.Frame(self.content_frame, bg='white')
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Header with title and action buttons
        header_frame = tk.Frame(main_frame, bg='white')
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        title = tk.Label(header_frame, text="✅ Review Complete", 
                        font=('Segoe UI', 20, 'bold'), 
                        bg='white', fg='#212529')
        title.pack(side=tk.LEFT)
        
        # Action buttons
        btn_frame = tk.Frame(header_frame, bg='white')
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="Generate New Session", 
                  command=self.generate_new_session, style='Modern.TButton').pack(side=tk.LEFT, padx=(0, 15))
        ttk.Button(btn_frame, text="Finish & Save", 
                  command=self.save_and_exit, style='Accent.TButton').pack(side=tk.LEFT)
        
        # Content area
        content_frame = tk.Frame(main_frame, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Left section: Difficult words
        if self.difficult_words:
            left_section = tk.Frame(content_frame, bg='white')
            left_section.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
            
            difficult_label = tk.Label(left_section, text="🔄 Words that need more practice:", 
                                      font=('Segoe UI', 14), bg='white', fg='#6c757d')
            difficult_label.pack(anchor='w', pady=(0, 10))
            
            # Grid for difficult words
            grid_frame = tk.Frame(left_section, bg='white', width=400)
            grid_frame.pack(fill=tk.Y)
            grid_frame.pack_propagate(False)
            
            for idx, (source, target) in enumerate(self.difficult_words):
                row = idx // 2
                col = idx % 2
                tile = self.create_compact_word_tile(grid_frame, source, target)
                tile.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
            
            grid_frame.columnconfigure(0, weight=1)
            grid_frame.columnconfigure(1, weight=1)
        
        # Right section: Statistics
        right_section = tk.Frame(content_frame, bg='white')
        right_section.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Statistics summary
        stats_label = tk.Label(right_section, text="📊 Session Statistics", 
                              font=('Segoe UI', 14), bg='white', fg='#6c757d')
        stats_label.pack(anchor='w', pady=(60, 10))
        
        # Calculate statistics
        total_words = len(self.vocab_list)
        difficult_count = len(self.difficult_words)
        mastered_count = total_words - difficult_count
        
        stats_text = f"""
📚 Total words reviewed: {total_words}
✅ Words mastered: {mastered_count}
🔄 Words needing practice: {difficult_count}
🎯 Success rate: {(mastered_count/total_words)*100:.1f}%
        """.strip()
        
        stats_content = tk.Label(right_section, text=stats_text, 
                               font=('Segoe UI', 11), bg='white', fg='#495057',
                               justify='left')
        stats_content.pack(anchor='w', pady=10)
        
        # Simple progress bar visualization
        self.create_progress_visualization(right_section, mastered_count, total_words)
    
    def create_compact_word_tile(self, parent, source, target):
        """Create a compact word tile."""
        tile_frame = tk.Frame(parent, bg='white', relief='solid', bd=1)
        
        inner_frame = tk.Frame(tile_frame, bg='white')
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        word_frame = tk.Frame(inner_frame, bg='white')
        word_frame.pack(fill=tk.X, pady=(0, 3))
        
        tk.Label(word_frame, text=source, font=('Segoe UI', 10, 'bold'), 
                fg='#2c3e50', bg='white').pack(side=tk.LEFT)
        tk.Label(word_frame, text=" → ", font=('Segoe UI', 9), 
                fg='#7f8c8d', bg='white').pack(side=tk.LEFT)
        tk.Label(word_frame, text=target, font=('Segoe UI', 10), 
                fg='#e74c3c', bg='white').pack(side=tk.LEFT)
        
        return tile_frame
    
    def create_progress_visualization(self, parent, mastered, total):
        """Create a simple progress visualization."""
        if total == 0:
            return
        
        canvas = tk.Canvas(parent, width=300, height=60, bg='white', highlightthickness=0)
        canvas.pack(pady=20)
        
        # Draw progress bar
        bar_width = 250
        bar_height = 20
        x_start = 25
        y_start = 20
        
        # Background bar
        canvas.create_rectangle(x_start, y_start, x_start + bar_width, y_start + bar_height, 
                               fill='#e9ecef', outline='#dee2e6')
        
        # Progress bar
        progress_width = (mastered / total) * bar_width
        canvas.create_rectangle(x_start, y_start, x_start + progress_width, y_start + bar_height, 
                               fill='#28a745', outline='#28a745')
        
        # Add percentage text
        percentage = (mastered / total) * 100
        canvas.create_text(x_start + bar_width // 2, y_start + bar_height // 2, 
                          text=f"{percentage:.1f}%", 
                          font=('Segoe UI', 10, 'bold'), fill='white')
    
    def clear_content_frame(self):
        """Clear all widgets from content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def setup_audio_controls(self):
        """Setup audio controls."""
        self.clear_audio_controls()
        
        audio_frame = ttk.LabelFrame(self.audio_controls_frame, text="🎵 Audio Controls", padding="15")
        audio_frame.pack(fill=tk.X, padx=10, pady=5)
        
        if self.vlc_available and self.audio_path and os.path.exists(self.audio_path):
            self.setup_working_audio_controls(audio_frame)
        else:
            self.setup_disabled_audio_controls(audio_frame)
    
    def setup_working_audio_controls(self, parent):
        """Setup working audio controls with VLC."""
        try:
            # Initialize VLC player
            self.vlc_player = self.vlc_instance.media_player_new()
            media = self.vlc_instance.media_new(self.audio_path)
            self.vlc_player.set_media(media)
            
            # Control buttons row
            controls_row = ttk.Frame(parent)
            controls_row.pack(fill=tk.X, pady=(0, 10))
            
            playback_frame = ttk.Frame(controls_row)
            playback_frame.pack(expand=True)
            
            # Main controls
            self.play_btn = ttk.Button(playback_frame, text="▶ Play", 
                                      command=self.play_audio, style='Accent.TButton')
            self.play_btn.pack(side=tk.LEFT, padx=5)
            
            ttk.Button(playback_frame, text="⏸ Pause", 
                      command=self.pause_audio, style='Modern.TButton').pack(side=tk.LEFT, padx=5)
            
            ttk.Button(playback_frame, text="⏹ Stop", 
                      command=self.stop_audio, style='Modern.TButton').pack(side=tk.LEFT, padx=5)
            
            # Separator
            ttk.Separator(playback_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=15)
            
            # Jump controls
            ttk.Button(playback_frame, text="⏪ -4s", 
                      command=lambda: self.jump_audio(-4), style='Modern.TButton').pack(side=tk.LEFT, padx=5)
            
            ttk.Button(playback_frame, text="+4s ⏩", 
                      command=lambda: self.jump_audio(4), style='Modern.TButton').pack(side=tk.LEFT, padx=5)
            
            # Speed controls
            ttk.Separator(playback_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=15)
            
            ttk.Button(playback_frame, text="🐌 -5%", 
                      command=lambda: self.change_speed(-0.05), style='Modern.TButton').pack(side=tk.LEFT, padx=2)
            
            ttk.Button(playback_frame, text="🐇 +5%", 
                      command=lambda: self.change_speed(0.05), style='Modern.TButton').pack(side=tk.LEFT, padx=2)
            
            # Progress bar row
            progress_row = ttk.Frame(parent)
            progress_row.pack(fill=tk.X)
            
            self.audio_progress = tk.DoubleVar()
            self.audio_progress_bar = ttk.Scale(progress_row, 
                                              variable=self.audio_progress, 
                                              length=500, 
                                              from_=0, 
                                              to=100, 
                                              orient=tk.HORIZONTAL, 
                                              command=self.slider_seek_update)
            self.audio_progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            self.audio_progress_bar.bind('<ButtonRelease-1>', self.slider_seek_commit)
            
            # Start audio progress updates
            self.update_audio_progress()
            
        except Exception as e:
            print(f"Error setting up audio controls: {e}")
            self.setup_disabled_audio_controls(parent)
    
    def setup_disabled_audio_controls(self, parent):
        """Setup disabled audio controls."""
        controls_row = ttk.Frame(parent)
        controls_row.pack(fill=tk.X, pady=(0, 10))
        
        playback_frame = ttk.Frame(controls_row)
        playback_frame.pack(expand=True)
        
        # Disabled buttons
        ttk.Button(playback_frame, text="▶ Play", state=tk.DISABLED, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(playback_frame, text="⏸ Pause", state=tk.DISABLED, style='Modern.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(playback_frame, text="⏹ Stop", state=tk.DISABLED, style='Modern.TButton').pack(side=tk.LEFT, padx=5)
        
        # Message
        if not self.audio_path:
            message = "No audio file available"
        elif not VLC_AVAILABLE:
            message = "VLC not available - audio playback disabled"
        else:
            message = "Audio file not found"
        
        ttk.Label(parent, text=message, style='Body.TLabel').pack(pady=10)
    
    def clear_audio_controls(self):
        """Clear audio controls frame."""
        for widget in self.audio_controls_frame.winfo_children():
            widget.destroy()
    
    # Audio control methods
    def play_audio(self):
        if hasattr(self, 'vlc_player'):
            self.vlc_player.play()
            self.vlc_player.set_rate(self.audio_speed)
    
    def pause_audio(self):
        if hasattr(self, 'vlc_player'):
            self.vlc_player.pause()
    
    def stop_audio(self):
        if hasattr(self, 'vlc_player'):
            self.vlc_player.stop()
            self.audio_progress.set(0)
    
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
            try:
                rel = self.audio_progress.get() / 100.0
                rel = min(max(rel, 0), 1)
                new_pos = rel * self.audio_length
                self.vlc_player.set_time(int(new_pos * 1000))
            except Exception:
                pass
        self._slider_dragging = False
    
    def update_audio_progress(self):
        if hasattr(self, 'vlc_player') and self.vlc_player.is_playing() and not self._slider_dragging:
            try:
                length = self.vlc_player.get_length() / 1000.0
                if length > 0:
                    self.audio_length = length
                pos = self.vlc_player.get_time() / 1000.0
                progress = min(100, (pos / self.audio_length) * 100)
                self.audio_progress.set(progress)
            except:
                pass
        
        if hasattr(self, 'root'):
            self.root.after(200, self.update_audio_progress)
    
    def jump_audio(self, seconds):
        if hasattr(self, 'vlc_player') and self.audio_length > 0:
            try:
                cur_pos = self.vlc_player.get_time() / 1000.0
                new_pos = min(max(cur_pos + seconds, 0), self.audio_length)
                self.vlc_player.set_time(int(new_pos * 1000))
                self.audio_progress.set((new_pos / self.audio_length) * 100)
            except Exception:
                pass
    
    def save_and_exit(self):
        """Save results and exit."""
        if self.save_allowed:
            # Mark words as used or not understood
            for (source, target, _) in self.vocab_list:
                if (source, target) in self.difficult_words:
                    self.vocabulary_selector.mark_word_not_understood(source, target)
                else:
                    self.vocabulary_selector.mark_word_used(source, target)
            
            # Save to database
            print("💾 Saving vocabulary tracking data...")
            self.vocabulary_selector.database_manager.save_tracking_data()
            
            # Sync with Git
            if self.git_manager:
                print("🔄 Saving changes to Git repository...")
                self.git_manager.sync_async("push")
        
        self.review_complete = True
        self.root.quit()
        self.root.destroy()
    
    def generate_new_session(self):
        """Start a new vocabulary session."""
        self.save_and_exit()
    
    def on_close(self):
        """Handle window close."""
        if messagebox.askokcancel("Quit", "Save progress before closing?"):
            self.save_and_exit()
        else:
            self.review_complete = False
            self.root.quit()
            self.root.destroy()
    
    def run(self) -> bool:
        """Run the review interface and return completion status."""
        self.root.mainloop()
        return self.review_complete


def create_review_session(vocab_list: List[Tuple[str, str, str]], 
                         vocabulary_selector,
                         git_manager=None,
                         generated_text: Optional[str] = None, 
                         audio_path: Optional[str] = None,
                         example_sentences: Optional[dict] = None) -> bool:
    """
    Create and run a vocabulary review session.
    
    Returns:
        bool: True if review was completed successfully, False if cancelled
    """
    
    review_interface = ReviewInterface(
        vocab_list=vocab_list,
        vocabulary_selector=vocabulary_selector,
        git_manager=git_manager,
        generated_text=generated_text,
        audio_path=audio_path,
        example_sentences=example_sentences
    )
    
    return review_interface.run()
