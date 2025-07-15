"""
Vocabulary panel widget for displaying word translations and frequency analysis.
"""

import tkinter as tk
from tkinter import ttk, Frame, Label, Button
import threading
from typing import Optional
from .gpt_translator import GPTTranslator, WordAnalysis
from .styles import Colors


class VocabularyPanel:
    """Panel for displaying word translations and frequency analysis."""
    
    def __init__(self, parent, language_from: str = "fr", language_to: str = "de"):
        """
        Initialize vocabulary panel.
        
        Args:
            parent: Parent widget
            language_from: Source language code
            language_to: Target language code
        """
        self.parent = parent
        self.language_from = language_from
        self.language_to = language_to
        
        # Initialize translator
        try:
            self.translator = GPTTranslator()
        except ValueError as e:
            self.translator = None
            print(f"Translation disabled: {e}")
        
        # Current translation state
        self.current_analysis = None
        self.is_loading = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the vocabulary panel UI."""
        # Main container
        self.container = Frame(self.parent, bg='#ffffff', bd=5, width=270)
        self.container.pack(fill='both', expand=False, padx=5, pady=5)
        
        # Header
        header_frame = Frame(self.container, bg='#ffffff')
        header_frame.pack(fill='x', padx=5, pady=5)
        
        Label(header_frame, text="Vocabulary", 
              font=("Segoe UI", 12, "bold"),
              bg='#ffffff', fg='#2c3e50').pack(side='left')
        
        # Clear button
        self.clear_btn = Button(header_frame, text="✕", 
                               command=self.clear_translation,
                               font=("Segoe UI", 12),
                               bg='#dc3545', fg='white',
                               relief='flat', bd=0, pady=2, padx=10)
        self.clear_btn.pack(side='right', padx=(100, 5))
        
        # Content area
        self.content_frame = Frame(self.container, bg='#ffffff')
        self.content_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Initial empty state
        self.show_empty_state()
    
    def show_empty_state(self):
        """Show empty state message."""
        self.clear_content()
        
        Label(self.content_frame, 
              text="Double-click a word\nto see translation",
              font=("Segoe UI", 10),
              bg='#ffffff', fg='#6c757d',
              justify='center').pack(expand=True)
    
    def show_loading_state(self, word: str):
        """Show loading state during translation."""
        self.clear_content()
        self.is_loading = True
        
        # Loading message
        loading_frame = Frame(self.content_frame, bg='#ffffff')
        loading_frame.pack(expand=True, fill='both')
        
        Label(loading_frame, text=f"Translating '{word}'...",
              font=("Segoe UI", 10, "bold"),
              bg='#ffffff', fg='#2c3e50').pack(pady=10)
        
        # Simple loading animation
        self.loading_label = Label(loading_frame, text="⟳",
                                  font=("Segoe UI", 16),
                                  bg='#ffffff', fg='#007bff')
        self.loading_label.pack()
        
        # Start loading animation
        self.animate_loading()
    
    def animate_loading(self):
        """Animate the loading indicator."""
        if self.is_loading and hasattr(self, 'loading_label'):
            current_text = self.loading_label.cget('text')
            if current_text == '⟳':
                self.loading_label.config(text='⟲')
            else:
                self.loading_label.config(text='⟳')
            
            # Schedule next animation frame
            self.parent.after(500, self.animate_loading)
    
    def show_error_state(self, error_message: str):
        """Show error state."""
        self.clear_content()
        
        error_frame = Frame(self.content_frame, bg='#ffffff')
        error_frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        Label(error_frame, text="⚠️ Translation Error",
              font=("Segoe UI", 10, "bold"),
              bg='#ffffff', fg='#dc3545').pack(pady=5)
        
        Label(error_frame, text=error_message,
              font=("Segoe UI", 9),
              bg='#ffffff', fg='#6c757d',
              wraplength=200, justify='left').pack(pady=5)
    
    def show_translation(self, analysis: WordAnalysis):
        """Display translation analysis."""
        self.clear_content()
        self.current_analysis = analysis
        
        # Create content frame directly
        content_frame = Frame(self.content_frame, bg='#ffffff')
        content_frame.pack(fill='both', expand=True)
        
        # Build content
        self.build_translation_content(content_frame, analysis)
    
    def build_translation_content(self, parent, analysis: WordAnalysis):
        """Build the translation content layout."""
        # Original word section
        # self.add_section_header(parent, "Original Word")
        
        word_frame = Frame(parent, bg='#ffffff')
        word_frame.pack(fill='x', padx=10, pady=5)
        
        if analysis.original_word != analysis.root_word:
            Label(word_frame, text=analysis.original_word,
                  font=("Segoe UI", 14, "bold"),
                  bg='#ffffff', fg='#2c3e50').pack(anchor='w')
            
            Label(word_frame, text=f"{analysis.root_word} ({analysis.grammatical_relation})",
                  font=("Segoe UI", 10),
                  bg='#ffffff', fg='#6c757d').pack(anchor='w')
        else:
            Label(word_frame, text=analysis.original_word,
                  font=("Segoe UI", 14, "bold"),
                  bg='#ffffff', fg='#2c3e50').pack(anchor='w')
        
        # Translation section
        # self.add_section_header(parent, "Translation")
        
        trans_frame = Frame(parent, bg='#ffffff')
        trans_frame.pack(fill='x', padx=10, pady=5)
        
        Label(trans_frame, text=analysis.primary_translation,
              font=("Segoe UI", 12, "bold"),
              bg='#ffffff', fg='#007bff').pack(anchor='w')
        
        if analysis.secondary_translation:
            Label(trans_frame, text=f"alt.: {analysis.secondary_translation}",
                  font=("Segoe UI", 10),
                  bg='#ffffff', fg='#6c757d').pack(anchor='w')
        
        if analysis.context_translation and analysis.context_translation != analysis.primary_translation:
            Label(trans_frame, text=f"Context: {analysis.context_translation}",
                  font=("Segoe UI", 10),
                  bg='#ffffff', fg='#6c757d').pack(anchor='w')
        
        # Frequency section with color coding
        # self.add_section_header(parent, "Frequency Analysis")
        
        freq_frame = Frame(parent, bg='#ffffff')
        freq_frame.pack(fill='x', padx=10, pady=5)
        
        freq_info = analysis.frequency_info
        if freq_info.get("found"):
            # Color-coded frequency level
            freq_color = freq_info.get("color", "#6c757d")
            
            freq_label_frame = Frame(freq_frame, bg=freq_color, relief='solid', bd=1)
            freq_label_frame.pack(fill='x', pady=2)
            
            Label(freq_label_frame, text=f"📊 {freq_info['level']}",
                  font=("Segoe UI", 11, "bold"),
                  bg=freq_color, fg='white', pady=3).pack()
            
            # Rank information
            if freq_info.get("rank"):
                Label(freq_frame, text=f"Rank: #{freq_info['rank']:,}",
                      font=("Segoe UI", 10),
                      bg='#ffffff', fg='#6c757d').pack(anchor='w', pady=2)
        else:
            Label(freq_frame, text="Frequency data not available",
                  font=("Segoe UI", 10),
                  bg='#ffffff', fg='#6c757d').pack(anchor='w')
        
        # Part of speech
        if analysis.part_of_speech != "unknown":
            # self.add_section_header(parent, "Grammar")
            
            grammar_frame = Frame(parent, bg='#ffffff')
            grammar_frame.pack(fill='x', padx=10, pady=5)
            
            Label(grammar_frame, text=f"🏷️ {analysis.part_of_speech}",
                  font=("Segoe UI", 10),
                  bg='#ffffff', fg='#6c757d').pack(anchor='w')
    
    def add_section_header(self, parent, title: str):
        """Add a section header."""
        header_frame = Frame(parent, bg='#e9ecef')
        header_frame.pack(fill='x', padx=5, pady=(10, 0))
        
        Label(header_frame, text=title,
              font=("Segoe UI", 10, "bold"),
              bg='#e9ecef', fg='#495057', pady=3).pack(anchor='w', padx=5)
    
    def clear_content(self):
        """Clear all content from the panel."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.is_loading = False
    
    def clear_translation(self):
        """Clear the current translation and show empty state."""
        self.current_analysis = None
        self.show_empty_state()
    
    def translate_word(self, word: str, context: str = ""):
        """
        Translate a word asynchronously.
        
        Args:
            word: Word to translate
            context: Surrounding context
        """
        if not self.translator:
            self.show_error_state("Translation service not available.\nPlease check your API key.")
            return
        
        if not word or not word.strip():
            return
        
        word = word.strip()
        
        # Show loading state
        self.show_loading_state(word)
        
        # Start translation in background thread
        thread = threading.Thread(target=self._translate_worker, args=(word, context))
        thread.daemon = True
        thread.start()
    
    def _translate_worker(self, word: str, context: str):
        """Background worker for translation."""
        try:
            # Perform translation
            analysis = self.translator.analyze_word_comprehensive(
                word, self.language_from, self.language_to, context
            )
            
            # Update UI on main thread
            self.parent.after(0, lambda: self.show_translation(analysis))
            
        except Exception as e:
            error_msg = f"Failed to translate '{word}': {str(e)}"
            self.parent.after(0, lambda: self.show_error_state(error_msg))
    
    def set_languages(self, language_from: str, language_to: str):
        """Update the languages used for translation."""
        self.language_from = language_from
        self.language_to = language_to
        
        # Clear current translation if languages changed
        if self.current_analysis:
            self.clear_translation()