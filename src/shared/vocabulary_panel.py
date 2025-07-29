"""
Vocabulary panel widget for displaying word translations and frequency analysis.
"""

import tkinter as tk
from tkinter import ttk, Frame, Label, Button
import threading
from typing import Optional
from .gpt_translator import GPTTranslator, WordAnalysis
from .styles import Colors
from .database_models import DatabaseManager


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
        
        # Initialize translator and database manager
        try:
            self.translator = GPTTranslator()
            from .database_models import DatabaseManager
            self.db_manager = DatabaseManager()
        except ValueError as e:
            self.translator = None
            print(f"Translation disabled: {e}")
        
        # Initialize database manager
        try:
            self.db_manager = DatabaseManager()
        except Exception as e:
            self.db_manager = None
            print(f"Database not available: {e}")
        
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
        
        Label(word_frame, text=analysis.root_word,
                font=("Segoe UI", 14, "bold"),
                bg='#ffffff', fg='#2c3e50').pack(anchor='w')
        
        # Translation section
        
        trans_frame = Frame(parent, bg='#ffffff')
        trans_frame.pack(fill='x', padx=10, pady=5)
        
        Label(trans_frame, text=analysis.primary_translation,
              font=("Segoe UI", 12, "bold"),
              bg='#ffffff', fg='#007bff').pack(anchor='w')
        
        if analysis.secondary_translation:
            Label(trans_frame, text=f"alt.: {analysis.secondary_translation}",
                  font=("Segoe UI", 10),
                  bg='#ffffff', fg='#6c757d').pack(anchor='w')
        
        # Frequency section with color coding
        
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
        
        # Example sentences section
        if analysis.example_original:
            example_frame = Frame(parent, bg='#ffffff')
            example_frame.pack(fill='x', padx=10, pady=(10, 5))
            
            Label(example_frame, text="Example:",
                  font=("Segoe UI", 10, "bold"),
                  bg='#ffffff', fg='#2c3e50').pack(anchor='w')
            
            # Original sentence
            Label(example_frame, text=analysis.example_original,
                  font=("Segoe UI", 10, "italic"),
                  bg='#ffffff', fg='#495057',
                  wraplength=240, justify='left').pack(anchor='w', pady=(2, 0))
            
            # Translation
            if analysis.example_translation:
                Label(example_frame, text=analysis.example_translation,
                      font=("Segoe UI", 9),
                      bg='#ffffff', fg='#6c757d',
                      wraplength=240, justify='left').pack(anchor='w', pady=(2, 0))
        
        # Add to vocabulary button
        self.add_vocabulary_button(parent, analysis)
    
    def add_vocabulary_button(self, parent, analysis: WordAnalysis):
        """Add 'Add to Vocabulary' button."""
        if not self.db_manager:
            return  # Skip if database not available
        
        # Button frame
        button_frame = Frame(parent, bg='#ffffff')
        button_frame.pack(fill='x', padx=10, pady=10)
        
        # Add to vocabulary button
        self.add_vocab_btn = Button(
            button_frame,
            text="📚 Add to Vocabulary",
            font=("Segoe UI", 10, "bold"),
            bg='#28a745',
            fg='white',
            relief='flat',
            bd=0,
            pady=8,
            padx=20,
            command=lambda: self.add_to_vocabulary(analysis)
        )
        self.add_vocab_btn.pack(fill='x')
        
        # Add hover effects
        self.add_vocab_btn.bind('<Enter>', lambda e: self.add_vocab_btn.config(bg='#218838'))
        self.add_vocab_btn.bind('<Leave>', lambda e: self.add_vocab_btn.config(bg='#28a745'))
    
    def add_to_vocabulary(self, analysis: WordAnalysis):
        """Add the current word to the vocabulary database."""
        if not self.db_manager or not analysis:
            return
        
        try:
            # Add word to database
            success = self.db_manager.add_word(
                word=analysis.root_word,
                translation=analysis.primary_translation,
                secondary_translation=analysis.secondary_translation,
                language_from=self.language_from,
                language_to=self.language_to,
                frequency_rank=analysis.frequency_info.get('rank') if analysis.frequency_info.get('found') else None,
                frequency_level=analysis.frequency_info.get('level') if analysis.frequency_info.get('found') else None
            )
            
            if success:
                # Update button to show success
                self.add_vocab_btn.config(
                    text="✅ Added to Vocabulary",
                    bg='#6c757d',
                    state='disabled'
                )
                
                # Schedule button reset after 2 seconds
                self.parent.after(2000, self.reset_add_button)
                
                print(f"✅ Added '{analysis.root_word}' to vocabulary database")
            else:
                self.show_add_error("Failed to add word to database")
                
        except Exception as e:
            error_msg = f"Error adding to vocabulary: {str(e)}"
            print(f"❌ {error_msg}")
            self.show_add_error(error_msg)
    
    def reset_add_button(self):
        """Reset the add to vocabulary button to its original state."""
        if hasattr(self, 'add_vocab_btn'):
            self.add_vocab_btn.config(
                text="📚 Add to Vocabulary",
                bg='#28a745',
                state='normal'
            )
    
    def show_add_error(self, error_msg: str):
        """Show error state for add to vocabulary button."""
        if hasattr(self, 'add_vocab_btn'):
            self.add_vocab_btn.config(
                text="❌ Error",
                bg='#dc3545'
            )
            
            # Schedule button reset after 2 seconds
            self.parent.after(2000, self.reset_add_button)
    
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
            # Perform translation using GPT translator
            result = self.translator.analyze_word_string(word, self.language_from, self.language_to)
            
            if "error" in result:
                raise Exception(result["error"])
            
            # Convert dict result to WordAnalysis object
            from .gpt_translator import WordAnalysis
            analysis = WordAnalysis(
                original_word=result["original_word"],
                root_word=result["normalized_word"],
                primary_translation=result["primary_translation"],
                secondary_translation=result["secondary_translation"],
                frequency_info={
                    "level": result["frequency_level"],
                    "rank": result["frequency_rank"],
                    "found": result["frequency_level"] is not None
                },
                language_from=result["language_from"],
                language_to=result["language_to"]
            )
            
            # Add example sentences
            analysis.example_original = result.get("example_original")
            analysis.example_translation = result.get("example_translation")
            
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