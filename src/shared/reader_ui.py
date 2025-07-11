"""
Shared reader UI component for both transcriber and gentexter modules
"""
from tkinter import Frame, Label, Button
from .audio_controls import AudioControls
from .text_display import TranscriptionTextDisplay
from .vocabulary_panel import VocabularyPanel
from .styles import center_top_window

class ReaderUI:
    """Shared reader UI with text display and audio controls"""
    
    def __init__(self, master, title, audio_path=None, text_content=None, srt_path=None, back_callback=None, 
                 language_from="fr", language_to="de"):
        self.master = master
        self.title = title
        self.audio_path = audio_path
        self.text_content = text_content
        self.srt_path = srt_path
        self.back_callback = back_callback
        self.language_from = language_from
        self.language_to = language_to
        
        # For custom highlighting functionality
        self.highlight_callback = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the complete reader UI layout"""
        # Clear existing widgets
        for widget in self.master.winfo_children():
            widget.destroy()
            
        # Configure window
        self.master.title(f"🎤 InfiniLing - {self.title}")
        self.master.configure(bg='#ffffff')
        center_top_window(self.master, width=1000, height=700)

        # Configure master grid to have a content row and a fixed controls row
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=0)
        self.master.grid_columnconfigure(0, weight=1)

        # Main Content Frame (everything except audio controls)
        content_container = Frame(self.master, bg='#ffffff')
        content_container.grid(row=0, column=0, sticky='nsew')
        content_container.grid_columnconfigure(0, weight=2)  # Text area gets 2/3 width
        content_container.grid_columnconfigure(1, weight=1)  # Vocabulary panel gets 1/3 width
        content_container.grid_rowconfigure(1, weight=1)

        # Header
        self.setup_header(content_container)
        
        # Main text area
        self.setup_text_area(content_container)
        
        # Vocabulary panel
        self.setup_vocabulary_panel(content_container)

        # Audio controls at bottom
        self.setup_audio_controls()

    def setup_header(self, parent):
        """Setup the header with back button and title"""
        header = Frame(parent, bg='#f8f9fa')
        header.grid(row=0, column=0, columnspan=2, sticky='ew')
        
        if self.back_callback:
            Button(header, text="← Back", command=self.back_callback,
                   font=("Segoe UI", 11, "bold"), bg='#95a5a6', fg='white',
                   activebackground='#7f8c8d', relief='flat', bd=0, pady=5, padx=15).pack(side='left')
        
        Label(header, text=self.title, font=("Segoe UI", 18, "bold"),
              bg='#f9f9fa', fg='#2c3e50').pack(side='left', padx=20)

    def setup_text_area(self, parent):
        """Setup the main text display area"""
        main_frame = Frame(parent, bg='#ffffff')
        main_frame.grid(row=1, column=0, sticky='nsew', padx=30, pady=(10, 10))
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # Text area label
        text_label = "Generated Text" if self.text_content else "Transcription Text"
        Label(main_frame, text=text_label, font=("Segoe UI", 13, "bold"),
              bg='#ffffff', fg='#2c3e50').grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        # Text display frame
        text_frame = Frame(main_frame, bg='#ffffff')
        text_frame.grid(row=1, column=0, sticky='nsew')
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)

        # Use shared text display component
        if self.srt_path:
            # For transcription with SRT highlighting
            self.text_display = TranscriptionTextDisplay(text_frame, self.srt_path, self.on_segment_highlight)
        else:
            # For plain text content
            self.text_display = TranscriptionTextDisplay(text_frame, None, self.on_segment_highlight)
            if self.text_content:
                self.text_display.set_text(self.text_content)
        
        # Add double-click binding for word translation
        self.setup_word_translation_binding()

    def setup_vocabulary_panel(self, parent):
        """Setup the vocabulary panel on the right side"""
        vocab_frame = Frame(parent, bg='#ffffff')
        vocab_frame.grid(row=1, column=1, sticky='nsew', padx=(5, 30), pady=(10, 10))
        vocab_frame.grid_columnconfigure(0, weight=1)
        vocab_frame.grid_rowconfigure(0, weight=1)
        
        # Create vocabulary panel
        self.vocabulary_panel = VocabularyPanel(vocab_frame, self.language_from, self.language_to)

    def setup_audio_controls(self):
        """Setup the audio controls at the bottom"""
        # Audio controls frame
        self.audio_controls_frame = Frame(self.master, bg='#f9f9fa')
        self.audio_controls_frame.grid(row=1, column=0, sticky='ew', padx=30, pady=10)
        
        # Use shared audio controls component
        self.audio_controls = AudioControls(self.audio_controls_frame, self.audio_path)
        
        # Setup keyboard bindings
        self.audio_controls.setup_keyboard_bindings(self.master)
        
        # Connect highlighting functionality
        self.connect_highlighting()

    def connect_highlighting(self):
        """Connect the audio controls to text highlighting"""
        # Store original update method
        original_update = self.audio_controls.update_audio_progress
        
        def enhanced_update():
            # Call original update
            original_update()
            
            # Add highlighting if we have VLC player and segments
            if (hasattr(self.audio_controls, 'vlc_player') and 
                hasattr(self.audio_controls, 'audio_progress') and 
                not self.audio_controls._slider_dragging and
                hasattr(self.text_display, 'srt_segments') and
                self.text_display.srt_segments):
                
                if self.audio_controls.vlc_player.is_playing():
                    current_time = self.audio_controls.vlc_player.get_time() / 1000.0
                    if current_time >= 0:
                        self.highlight_current_segment(current_time)
        
        # Replace the update method
        self.audio_controls.update_audio_progress = enhanced_update
        
        # Also enhance the jump_audio method for immediate highlighting
        original_jump = self.audio_controls.jump_audio
        
        def enhanced_jump(seconds):
            original_jump(seconds)
            # Force immediate highlight update after jumping
            if hasattr(self.audio_controls, 'vlc_player') and self.audio_controls.audio_length > 0:
                new_time = self.audio_controls.vlc_player.get_time() / 1000.0
                self.master.after(50, lambda: self.highlight_current_segment(new_time))
        
        self.audio_controls.jump_audio = enhanced_jump

    def on_segment_highlight(self, segment_idx, segment):
        """Callback when a segment is highlighted in the text display"""
        # Can be overridden by subclasses for additional functionality
        if self.highlight_callback:
            self.highlight_callback(segment_idx, segment)

    def highlight_current_segment(self, current_time):
        """Highlight the current segment in the text display"""
        if hasattr(self, 'text_display'):
            self.text_display.highlight_current_segment(current_time)

    def set_highlight_callback(self, callback):
        """Set a custom callback for segment highlighting"""
        self.highlight_callback = callback

    def get_text_display(self):
        """Get the text display component"""
        return getattr(self, 'text_display', None)

    def get_audio_controls(self):
        """Get the audio controls component"""
        return getattr(self, 'audio_controls', None)

    def setup_word_translation_binding(self):
        """Setup double-click binding for word translation"""
        if hasattr(self, 'text_display') and hasattr(self.text_display, 'text_widget'):
            # Bind double-click to word selection and translation
            self.text_display.text_widget.bind('<Double-Button-1>', self.on_word_double_click)

    def on_word_double_click(self, event):
        """Handle double-click on a word for translation"""
        try:
            # Get the clicked word
            widget = event.widget
            
            # Get the position of the click
            x, y = event.x, event.y
            index = widget.index(f"@{x},{y}")
            
            # Select the word at the clicked position
            word_start = widget.index(f"{index} wordstart")
            word_end = widget.index(f"{index} wordend")
            
            # Get the selected word
            word = widget.get(word_start, word_end).strip()
            
            # Clean the word (remove punctuation)
            import re
            word = re.sub(r'[^\w\s]', '', word)
            
            if word and hasattr(self, 'vocabulary_panel'):
                # Get surrounding context (current line)
                line_start = widget.index(f"{index} linestart")
                line_end = widget.index(f"{index} lineend")
                context = widget.get(line_start, line_end)
                
                # Translate the word
                self.vocabulary_panel.translate_word(word, context)
                
        except Exception as e:
            print(f"Error in word translation: {e}")

    def set_translation_languages(self, language_from: str, language_to: str):
        """Update the languages used for translation"""
        self.language_from = language_from
        self.language_to = language_to
        
        if hasattr(self, 'vocabulary_panel'):
            self.vocabulary_panel.set_languages(language_from, language_to)
