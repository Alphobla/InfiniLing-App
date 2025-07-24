from tkinter import Frame, Button, Label, filedialog, messagebox, ttk, Entry, Checkbutton, Radiobutton, BooleanVar, IntVar, StringVar
import tkinter.messagebox as msgbox
from ..shared.reader_ui import ReaderUI
from ..shared.styles import apply_modern_theme, Colors, Fonts, Spacing
from ..shared.style_utils import StyledWidgets, TileStyles, LayoutHelpers, CommonPatterns
import os
import threading
from ..shared.styles import center_top_window

class GentexterReview:
    def __init__(self, master, review_words, back_callback=None, vocab_app=None, config=None):
        self.master = master
        self.config = config
        self.review_words = review_words
        self.back_callback = back_callback
        self.vocab_app = vocab_app
        
        # Review state
        self.current_word_index = 0
        self.word_scores = {}  # Store scores for each word
        self.translation_visible = False
        
        self.setup_ui()

    def setup_ui(self):
        # Clear any existing widgets to avoid pack/grid conflicts
        for widget in self.master.winfo_children():
            widget.destroy()
            
        window_width, window_height = self.config.get_window_size('gentexter')
        center_top_window(self.master, width=window_width, height=window_height)
        
        # Main container
        main_frame = Frame(self.master, bg=Colors.LIGHT_GRAY)
        main_frame.pack(expand=True, fill='both', padx=Spacing.LG, pady=Spacing.LG)

        # Header with back button and title
        header_frame = CommonPatterns.create_header_with_navigation(
            main_frame, "Review", self.back_callback, self.proceed_to_stats, "See Stats"
        )
        
        # Create word review interface
        self.create_word_review_interface(main_frame)
    
    def create_header(self, parent):
        """Create header for tile view"""
        header_frame = Frame(parent, bg=Colors.WHITE)
        header_frame.pack(fill='x', pady=(0, Spacing.LG))
        
        # Title section (left side)
        title_frame = Frame(header_frame, bg=Colors.WHITE)
        title_frame.pack(side='left', fill='x', expand=True)
        
        title = Label(title_frame, text="🎯 Select words you want to review again", 
                     font=("Segoe UI", 14, "bold"), bg=Colors.WHITE, fg=Colors.DARK_GRAY)
        title.pack(anchor='w')

        subtitle = Label(title_frame, text="Click on vocabulary item to see translation, then mark difficulty from 0-5", 
                        font=("Segoe UI", 11), bg=Colors.WHITE, fg=Colors.MEDIUM_GRAY)
        subtitle.pack(anchor='w', pady=(Spacing.XS, 0))
    
    def create_word_review_interface(self, parent):
        """Create the word-by-word review interface"""
        # Content container
        content_frame = Frame(parent, bg=Colors.WHITE, relief='raised', bd=1)
        content_frame.pack(expand=True, fill='both', padx=Spacing.SM, pady=Spacing.SM)
        
        # Progress indicator
        progress_text = f"Word {self.current_word_index + 1} of {len(self.review_words)}"
        self.progress_label = Label(content_frame, text=progress_text, 
                                   font=Fonts.BODY, bg=Colors.WHITE, fg=Colors.MEDIUM_GRAY)
        self.progress_label.pack(pady=(Spacing.LG, Spacing.SM))
        
        # Current word display
        current_word = self.review_words[self.current_word_index]['word']  # Dictionary access
        self.word_label = Label(content_frame, text=current_word, 
                               font=("Segoe UI", 24, "bold"), bg=Colors.WHITE, fg=Colors.DARK_GRAY)
        self.word_label.pack(pady=(Spacing.LG, Spacing.MD))
        
        # Translation button
        self.translation_button = Button(content_frame, text="See Translation", 
                                        command=self.show_translation,
                                        font=Fonts.BODY, bg=Colors.PRIMARY, fg=Colors.WHITE,
                                        activebackground=Colors.PRIMARY, relief='flat', bd=0,
                                        pady=Spacing.SM, padx=Spacing.LG)
        self.translation_button.pack(pady=Spacing.MD)
        
        # Translation display (initially hidden)
        self.translation_label = Label(content_frame, text="", 
                                      font=("Segoe UI", 16), bg=Colors.WHITE, fg=Colors.INFO)
        self.translation_label.pack(pady=(0, Spacing.LG))
        
        # Difficulty rating buttons (0-5)
        rating_frame = Frame(content_frame, bg=Colors.WHITE)
        rating_frame.pack(pady=Spacing.LG)
        
        Label(rating_frame, text="How easy was this word?", 
              font=Fonts.BODY, bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(pady=(0, Spacing.SM))
        
        buttons_frame = Frame(rating_frame, bg=Colors.WHITE)
        buttons_frame.pack()
        
        # Color gradient from green to red
        colors = ['#c0392b', '#e74c3c', '#e67e22', '#f39c12', '#2ecc71', '#27ae60']
        for i in range(6):
            Button(buttons_frame, text=str(i), command=lambda score=i: self.rate_word(score),
              font=("Segoe UI", 14, "bold"), bg=colors[i], fg=Colors.WHITE,
              activebackground=colors[i], relief='flat', bd=0,
              width=2, height=2).pack(side='left', padx=Spacing.XS)

    def show_translation(self):
        """Show the translation for current word"""
        translation = self.review_words[self.current_word_index]['translation']  # Dictionary access
        self.translation_label.config(text=translation)
        self.translation_visible = True
    
    def rate_word(self, score):
        """Rate current word and move to next"""
        current_word = self.review_words[self.current_word_index]['word']  # Dictionary access
        self.word_scores[current_word] = score
        
        # Move to next word
        self.current_word_index += 1
        
        if self.current_word_index >= len(self.review_words):
            # All words reviewed, go to stats
            self.proceed_to_stats()
        else:
            # Update interface for next word
            self.update_word_display()
    
    def update_word_display(self):
        """Update display for current word"""
        # Update progress
        progress_text = f"Word {self.current_word_index + 1} of {len(self.review_words)}"
        self.progress_label.config(text=progress_text)
        
        # Update word
        current_word = self.review_words[self.current_word_index]['word']  # Dictionary access
        self.word_label.config(text=current_word)
        
        # Reset translation
        self.translation_label.config(text="")
        self.translation_visible = False
        
    def proceed_to_stats(self):
        """Proceed from review to stats stage"""
        try:
            from .gentexter_stats_ui import GentexterStats
            GentexterStats(
                master=self.master,
                review_data=self.review_words,
                word_scores=self.word_scores,
                vocab_app=self.vocab_app,
                config=self.config
            )

        except Exception as e:
            messagebox.showerror("Error", f"Error proceeding to stats: {str(e)}")

