from tkinter import Frame, Button, Label, filedialog, messagebox, ttk, Entry, Checkbutton, Radiobutton, BooleanVar, IntVar, StringVar
import tkinter.messagebox as msgbox
from ..shared.reader_ui import ReaderUI
from ..shared.styles import apply_modern_theme, Colors, Fonts, Spacing
from ..shared.style_utils import StyledWidgets, TileStyles, LayoutHelpers, CommonPatterns
import os
import threading
from ..shared.styles import center_top_window

class GentexterConfig:
    def __init__(self, master, config=None, vocab_service=None, back_callback=None):
        """
        Initialize VocabularyInterface with dependency injection.
        
        Args:
            master: Tkinter root window
            config: ConfigManager instance
            vocab_service: VocabularyApp service instance
            back_callback: Callback function to return to main menu
        """
        self.master = master
        self.config = config
        self.vocab_service = vocab_service
        self.back_callback = back_callback
        
        app_name = self.config.get('app.name', 'InfiniLing')
        bg_color = self.config.get('ui.colors.background')

        self.master.title(f"📚 {app_name} - Gentexter")
        self.master.configure(bg=bg_color)

        # Use injected vocabulary service or create fallback
        self.vocab_app = vocab_service
        
        # Initialize configuration variables from config
        default_words = self.config.get('vocabulary.default_total_words')
        default_ratio = self.config.get('vocabulary.default_new_word_ratio')

        # Configuration variables
        self.vocab_source = StringVar(value="databank")  # Radio button group: "databank", "test", "last_text"
        self.import_new_list = BooleanVar(value=False)  # Sub-option for databank
        self.total_words = IntVar(value=default_words)
        self.new_word_ratio = IntVar(value=default_ratio)
        self.selected_language = StringVar(value="fr")  # Language selection

        self.setup_ui()

    def setup_ui(self):
        # Set window size for gentexter interface using config
        window_width, window_height = self.config.get_window_size('gentexter')
        center_top_window(self.master, width=window_width, height=window_height)
        
        # Apply modern theme
        # apply_modern_theme()
        
        # Main container
        main_frame = Frame(self.master, bg=Colors.LIGHT_GRAY)
        main_frame.pack(expand=True, fill='both', padx=Spacing.LG, pady=Spacing.LG)

        # Header with back button and title
        header_frame = CommonPatterns.create_header_with_navigation(
            main_frame, "📚 Wordstory", self.back_callback
        )

        # Configuration section
        config_frame, config_content = StyledWidgets.create_config_section(main_frame, "Configuration")
        config_frame.pack(fill='x', pady=(0, Spacing.XS), padx=Spacing.SM)

        # Vocabulary source options
        vocab_source_frame = Frame(config_content, bg=Colors.WHITE)
        vocab_source_frame.pack(fill='x', padx=Spacing.LG, pady=(0, 2))

        # Main radio button options
        databank_radio = Radiobutton(vocab_source_frame, 
                                    text="Use vocabulary databank", 
                                    variable=self.vocab_source,
                                    value="databank",
                                    font=Fonts.BODY,
                                    bg=Colors.WHITE, fg=Colors.DARK_GRAY,
                                    activebackground=Colors.WHITE)
        databank_radio.pack(anchor='w', pady=2)

        # Sub-option for databank (indented)
        import_frame = Frame(vocab_source_frame, bg=Colors.WHITE)
        import_frame.pack(fill='x', padx=(20, 0), pady=(0, 2))
        
        import_check = Checkbutton(import_frame, 
                                  text="📥 Import new list to databank", 
                                  variable=self.import_new_list,
                                  command=self.on_import_check,
                                  font=Fonts.BODY,
                                  bg=Colors.WHITE, fg=Colors.DARK_GRAY,
                                  activebackground=Colors.WHITE)
        import_check.pack(anchor='w')

        test_radio = Radiobutton(vocab_source_frame, 
                                text="🧪 Test mode (use preset data)", 
                                variable=self.vocab_source,
                                value="test",
                                font=Fonts.BODY,
                                bg=Colors.WHITE, fg=Colors.WARNING,
                                activebackground=Colors.WHITE)
        test_radio.pack(anchor='w', pady=2)

        last_text_radio = Radiobutton(vocab_source_frame, 
                                      text="📄 Use last generated text", 
                                      variable=self.vocab_source,
                                      value="last_text",
                                      font=Fonts.BODY,
                                      bg=Colors.WHITE, fg=Colors.INFO,
                                      activebackground=Colors.WHITE)
        last_text_radio.pack(anchor='w', pady=2)

        # Total words to learn
        tot_words_frame = Frame(vocab_source_frame, bg=Colors.WHITE)
        tot_words_frame.pack(fill='x', pady=Spacing.XS)

        tot_words_entry = Entry(tot_words_frame, textvariable=self.total_words, 
                           font=Fonts.BODY, width=5, justify='center')
        tot_words_entry.pack(side='left', padx=Spacing.XS)
        Label(tot_words_frame, text="Total words to learn", 
              font=Fonts.BODY, 
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(side='left')


        # New word ratio
        new_ratio_frame = Frame(vocab_source_frame, bg=Colors.WHITE)
        new_ratio_frame.pack(fill='x', pady=Spacing.XS)

        new_ratio_entry = Entry(new_ratio_frame, textvariable=self.new_word_ratio, 
                           font=Fonts.BODY, width=5, justify='center')
        new_ratio_entry.pack(side='left', padx=Spacing.XS)
        Label(new_ratio_frame, text="New words ratio (0-1)", 
              font=Fonts.BODY, 
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(side='left')

        # Language selection
        language_frame = Frame(vocab_source_frame, bg=Colors.WHITE)
        language_frame.pack(fill='x', pady=Spacing.XS)

        # Get language options from config
        languages = self.config.get('vocabulary.languages.available_languages')

        language_combobox = ttk.Combobox(language_frame, 
                                        textvariable=self.selected_language,
                                        values=[lang[0] for lang in languages],
                                        state="readonly",
                                        width=10,
                                        font=Fonts.BODY)
        language_combobox.pack(side='left', padx=Spacing.XS)
        language_combobox.set("French")

        Label(language_frame, text="Generated language", 
              font=Fonts.BODY, 
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(side='left', padx=(0, Spacing.XS))
        

        # Generate button (using shared utility for large square button)
        self.generate_button = CommonPatterns.create_main_action_button(
            main_frame, "📖\nGenerate\nText", self.generate_wordtext, button_type="large_square", center=True
        )

    def on_import_check(self):
        """Handle import new list checkbox"""
        if self.import_new_list.get():
            # Open file browser
            filetypes = [
                ("CSV Files", "*.csv"),
                ("Excel Files", "*.xlsx"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
            
            file_path = filedialog.askopenfilename(
                title="Select Vocabulary File to Import",
                filetypes=filetypes
            )
            
            if file_path:
                try:
                    # Use the database manager to import vocabulary
                    results = self.vocab_app.database_manager.import_vocabulary_from_csv(file_path)
                    
                    if results['imported'] > 0:
                        messagebox.showinfo("Import Successful", 
                                          f"Total rows: {results['total_rows']}\n"
                                          f"✅ Imported: {results['imported']} new words!\n\n"
                                          f"⏭️ Skipped (already exist): {results['skipped']}\n"
                                          f"❌ Errors: {results['errors']}")
                    else:
                        messagebox.showinfo("Import Complete", 
                                          f"No new words to import.\n\n"
                                          f"Total rows: {results['total_rows']}\n"
                                          f"All words already exist in database.")
                    
                except Exception as e:
                    error_msg = f"Import failed: {str(e)}"
                    print(f"❌ {error_msg}")
                    messagebox.showerror("Import Error", error_msg)
                    self.import_new_list.set(False)
            else:
                # User canceled file selection
                self.import_new_list.set(False)

    def generate_wordtext(self):
        """Generate wordtext using the modern backend"""
        try:
            # Check selected vocabulary source
            vocab_source = self.vocab_source.get()
            
            if vocab_source == "test":
                self.run_test_mode()
                return
            elif vocab_source == "last_text":
                self.load_last_text_mode()
                return
            elif vocab_source != "databank":
                print("❌ Please select a vocabulary source")
                return
            

            # Disable generate button during processing
            self.generate_button.config(state='disabled', text="Generating...")
            print("🚀 Generating Text...")
            
            # Run generation in a separate thread
            def generation_task():
                try:
                    print("Starting generation task...")
                    # Get selected language code
                    selected_lang_name = self.selected_language.get()
                    
                    result = self.vocab_app.run_learning_session(
                        total_words=self.total_words.get(),
                        new_word_ratio=self.new_word_ratio.get(),
                        language=selected_lang_name,  # Pass the full language name
                        generate_audio=True,
                        progress_callback=lambda msg: print(f"📖 {msg}"),
                    )
                    print(f"Generation task completed with result: {len(result.get('selected_words', []))} words")
                    self.master.after(0, lambda: self.on_generation_complete(result))
                except Exception as e:
                    error_msg = f"❌ Generation failed: {str(e)}"
                    self.master.after(0, lambda: self.on_generation_error(error_msg))

            
            threading.Thread(target=generation_task, daemon=True).start()
            
        except Exception as e:
            print(f"❌ Error starting generation: {str(e)}")
            self.generate_button.config(state='normal', text="📖\nGenerate\nText")

    def load_last_text_mode(self):
        """Load last generated text mode for offline use"""
        try:
            print("📂 Loading last generated text...")
            
            # Disable generate button during processing
            self.generate_button.config(state='disabled', text="Loading...")
            
            def load_task():
                try:
                    print("Loading last session...")
                    result = self.vocab_app.load_last_session()
                    self.master.after(0, lambda: self.on_load_complete(result))
                except Exception as e:
                    error_msg = f"❌ Load failed: {str(e)}"
                    self.master.after(0, lambda: self.on_load_error(error_msg))
            
            threading.Thread(target=load_task, daemon=True).start()
            
        except Exception as e:
            print(f"❌ Error starting load: {str(e)}")
            self.generate_button.config(state='normal', text="📖\nGenerate\nText")

    def on_generation_complete(self, result):
        """Handle successful generation completion"""
        try:
            selected_words = result.get('selected_words', [])
            story = result.get('story', '')
            audio_path = result.get('audio_path', '')
            
            self.show_reader_interface(selected_words, story, audio_path)

        except Exception as e:
            self.on_generation_error(f"Error processing results: {str(e)}")
    
    def on_generation_error(self, error_message):
        """Handle generation errors"""
        print(error_message)
        self.generate_button.config(state='normal', text="📖\nGenerate\nText")

    def on_load_complete(self, result):
        """Handle successful load completion"""
        try:
            # Reset button state
            self.generate_button.config(state='normal', text="📖\nGenerate\nText")
            story = result.get('text', '')  # orchestrator returns 'text', not 'story'
            audio_path = result.get('audio_path', '')
            selected_words = result.get('words', [])  # orchestrator returns 'words', not 'selected_words'
            
            if story:
                print("✅ Last text loaded successfully (offline mode)")
                
                # Convert tuples to dictionaries for compatibility with review interface
                review_words = [
                    {'word': word, 'translation': translation, 'pronunciation': pronunciation}
                    for word, translation, pronunciation in selected_words
                ]
                print(f"📚 Using {len(review_words)} saved vocabulary words for review")

                # Start reader interface with loaded content
                self.show_reader_interface(review_words, story, audio_path)
            else:
                print("❌ No saved text found. Generate new content first.")
            
        except Exception as e:
            self.on_load_error(f"Error processing loaded content: {str(e)}")
    
    def on_load_error(self, error_message):
        """Handle load errors"""
        print(error_message)
        self.generate_button.config(state='normal', text="📖\nGenerate\nText")

    def run_test_mode(self):
        """Run test mode with preset data for development"""
        try:
            print("🧪 Running in test mode...")
            
            # Create test data
            test_selected_words = [
                {'word': 'bonjour', 'translation': 'hello', 'pronunciation': 'bon-ZHOOR'},
                {'word': 'merci', 'translation': 'thank you', 'pronunciation': 'mer-SEE'},
                {'word': 'au revoir', 'translation': 'goodbye', 'pronunciation': 'oh ruh-VWAHR'},
                {'word': 'oui', 'translation': 'yes', 'pronunciation': 'WEE'},
                {'word': 'non', 'translation': 'no', 'pronunciation': 'NOH'},
                {'word': 'excusez-moi', 'translation': 'excuse me', 'pronunciation': 'eh-skoo-zay MWAH'},
                {'word': 'pardon', 'translation': 'sorry', 'pronunciation': 'par-DOH'},
                {'word': 'comment', 'translation': 'how', 'pronunciation': 'koh-MAHN'},
                {'word': 'pourquoi', 'translation': 'why', 'pronunciation': 'poor-KWAH'},
                {'word': 'où', 'translation': 'where', 'pronunciation': 'OO'},
                {'word': 'quand', 'translation': 'when', 'pronunciation': 'KAHN'},
                {'word': 'combien', 'translation': 'how much', 'pronunciation': 'kohn-bee-AHN'},
                {'word': 'maintenant', 'translation': 'now', 'pronunciation': 'mahn-tuh-NAHN'},
                {'word': 'aujourd\'hui', 'translation': 'today', 'pronunciation': 'oh-zhoor-DWEE'},
                {'word': 'demain', 'translation': 'tomorrow', 'pronunciation': 'duh-MAHN'},
                {'word': 'hier', 'translation': 'yesterday', 'pronunciation': 'ee-YEHR'},
                {'word': 'bien', 'translation': 'well', 'pronunciation': 'bee-AHN'},
                {'word': 'mal', 'translation': 'bad', 'pronunciation': 'MAHL'},
                {'word': 'beaucoup', 'translation': 'a lot', 'pronunciation': 'boh-KOO'},
                {'word': 'peu', 'translation': 'little', 'pronunciation': 'PUH'}
            ]
            
            test_story = """Bonjour! Aujourd'hui, je vais vous raconter une petite histoire. 

            Marie se réveille et dit "Bonjour!" à sa famille. Elle demande "Comment allez-vous?" à sa mère. 
            Sa mère répond "Bien, merci beaucoup!"

            Marie va au marché. Elle demande "Combien coûte cette pomme?" Le vendeur répond "Deux euros, s'il vous plaît."
            Marie dit "Merci!" et achète la pomme.

            Le soir, Marie dit "Au revoir!" à ses amis. Elle rentre chez elle et dit "Bonne nuit!" 
            Demain, elle dira encore "Bonjour!" au monde.

            Cette histoire simple montre pourquoi il est important de bien parler français. 
            Quand nous disons "Excusez-moi" ou "Pardon", nous montrons du respect.
            Où que nous allions, ces mots nous aident. Maintenant, vous savez comment utiliser ces expressions!"""

            # Use one of the existing audio files for testing
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
            audio_dir = os.path.join(data_dir, 'transcriptions_and_audio')
            test_audio_file = os.path.join(audio_dir, '56.Ét 6  Pourquoi on aime Ben Healy.mp3')
            test_audio_path = test_audio_file if os.path.exists(test_audio_file) else ""
            
            # Simulate processing delay for realism
            self.generate_button.config(state='disabled', text="🧪 Testing...")
            
            def complete_test():
                result = {
                    'selected_words': test_selected_words,
                    'story': test_story,
                    'audio_path': test_audio_path
                }
                self.on_generation_complete(result)
            
            # Complete test after a short delay
            self.master.after(1000, complete_test)
            
        except Exception as e:
            print(f"❌ Test mode failed: {str(e)}")
            self.generate_button.config(state='normal', text="📖\nGenerate\nText")
    
    def show_reader_interface(self, review_data, generated_text, audio_path):
        """Show the in-app reader interface"""
        try:
            # Store session data in vocabulary service for next stage
            self.vocab_service.set_current_session_data({
                'words': review_data,
                'text': generated_text,
                'audio_path': audio_path
            })
            
            # Hide the main interface
            for widget in self.master.winfo_children():
                widget.pack_forget()
            

            # Create review interface
            self.reader_ui = ReaderUI(
                master=self.master,
                title="Reading Practice",
                audio_path=audio_path,
                text_content=generated_text,
                back_callback=self.return_from_reader,
                forward_callback=self.proceed_to_review,
                forward_text="Review Words →",
                config=self.config
            )
            
        except Exception as e:
            print(f"Failed to show gentexter reader interface: {str(e)}")

            # Restore main interface if review fails
            self.return_from_reader()

    def proceed_to_review(self):
        """Proceed from reader to review stage"""
        try:
            # Get session data from vocabulary service
            session_data = self.vocab_service.get_current_session_data()
            
            GentexterReview(
                master=self.master,
                review_words=session_data.get('words', []),
                generated_text=session_data.get('text', ''),
                audio_path=session_data.get('audio_path', ''),
                back_callback=self.return_from_reader,
                vocab_app=self.vocab_app,
                config=self.config
            )
            
        except Exception as e:
            print(f"Error proceeding to review: {str(e)}")
            self.return_from_reader()
    
    def return_from_reader(self):
        """Return from reader interface to config interface"""
        # Clear session data when returning
        if hasattr(self, 'vocab_service'):
            self.vocab_service.clear_current_session_data()
            
        # Destroy reader interface if it exists
        for widget in self.master.winfo_children():
            widget.destroy()
        
        # Recreate config interface
        self.setup_ui()

class GentexterReview:
    def __init__(self, master, review_words, generated_text, audio_path, back_callback=None, vocab_app=None, config=None):
        self.master = master
        self.config = config
        self.review_words = review_words
        self.audio_path = audio_path
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
        current_word = self.review_words[self.current_word_index][0]  # First element is word
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
        
        Label(rating_frame, text="How difficult was this word?", 
              font=Fonts.BODY, bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(pady=(0, Spacing.SM))
        
        buttons_frame = Frame(rating_frame, bg=Colors.WHITE)
        buttons_frame.pack()
        
        # Color gradient from green to red
        colors = ['#27ae60', '#2ecc71', '#f39c12', '#e67e22', '#e74c3c', '#c0392b']
        for i in range(6):
            Button(buttons_frame, text=str(i), command=lambda score=i: self.rate_word(score),
                  font=("Segoe UI", 14, "bold"), bg=colors[i], fg=Colors.WHITE,
                  activebackground=colors[i], relief='flat', bd=0,
                  width=2, height=2).pack(side='left', padx=Spacing.XS)

    def show_translation(self):
        """Show the translation for current word"""
        translation = self.review_words[self.current_word_index][1]  # Second element is translation
        self.translation_label.config(text=translation)
        self.translation_visible = True
    
    def rate_word(self, score):
        """Rate current word and move to next"""
        current_word = self.review_words[self.current_word_index][0]  # First element is word
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
        current_word = self.review_words[self.current_word_index][0]  # First element is word
        self.word_label.config(text=current_word)
        
        # Reset translation
        self.translation_label.config(text="")
        self.translation_visible = False
        
    def proceed_to_stats(self):
        """Proceed from review to stats stage"""
        try:
            GentexterStats(
                master=self.master,
                review_data=self.review_words,
                word_scores=self.word_scores,
                vocab_app=self.vocab_app,
                config=self.config
            )

        except Exception as e:
            print(f"Error proceeding to stats: {str(e)}")
            self.return_from_reader()
    
        

class GentexterStats:
    def __init__(self, master, review_data, word_scores, vocab_app=None, config=None):
        self.master = master
        self.config = config
        self.review_data = review_data
        self.word_scores = word_scores
        self.vocab_app = vocab_app
        
