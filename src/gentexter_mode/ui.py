from tkinter import Frame, Button, Label, filedialog, messagebox, ttk, Entry, Checkbutton, Radiobutton, BooleanVar, IntVar, StringVar
import tkinter.messagebox as msgbox
from .orchestrator_updated import VocabularyApp
from ..shared.reader_ui import ReaderUI
from ..shared.styles import apply_modern_theme, Colors, Fonts, Spacing
from ..shared.style_utils import StyledWidgets, TileStyles, LayoutHelpers, CommonPatterns
import os
import threading
from ..shared.styles import center_top_window

class VocabularyInterface:
    def __init__(self, master, back_callback=None):
        self.master = master
        self.back_callback = back_callback
        self.master.title("📚 InfiniLing - Gentexter")
        self.master.configure(bg=Colors.LIGHT_GRAY)

        # Initialize the modern vocabulary app backend
        self.vocab_app = VocabularyApp()
        
        # Configuration variables
        self.vocab_source = StringVar(value="databank")  # Radio button group: "databank", "test", "last_text"
        self.import_new_list = BooleanVar(value=False)  # Sub-option for databank
        self.total_words = IntVar(value=20)
        self.new_word_ratio = IntVar(value=.25)

        self.setup_ui()

    def setup_ui(self):
        # Set window size for gentexter interface
        center_top_window(self.master, width=500, height=700)
        
        # Apply modern theme
        apply_modern_theme()
        
        # Main container
        main_frame = Frame(self.master, bg=Colors.LIGHT_GRAY)
        main_frame.pack(expand=True, fill='both', padx=Spacing.LG, pady=Spacing.LG)

        # Header with back button and title
        header_frame = CommonPatterns.create_header_with_back_button(
            main_frame, "📚 Wordstory", self.back_callback
        )

        # Configuration section
        config_frame, config_content = StyledWidgets.create_config_section(main_frame, "Configuration")
        config_frame.pack(fill='x', pady=(0, Spacing.LG), padx=Spacing.SM)

        # Vocabulary source options
        vocab_source_frame = Frame(config_content, bg=Colors.WHITE)
        vocab_source_frame.pack(fill='x', padx=Spacing.LG, pady=(0, Spacing.MD))

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

        # Batch size configuration
        batch_frame = Frame(config_content, bg=Colors.WHITE)
        batch_frame.pack(fill='x', padx=Spacing.LG, pady=(Spacing.SM, Spacing.LG))

        # Total words to learn
        tot_words_frame = Frame(batch_frame, bg=Colors.WHITE)
        tot_words_frame.pack(fill='x', pady=Spacing.XS)

        Label(tot_words_frame, text="Total words to learn:", 
              font=Fonts.BODY, 
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(side='left')

        tot_words_entry = Entry(tot_words_frame, textvariable=self.total_words, 
                           font=Fonts.BODY, width=10, justify='center')
        tot_words_entry.pack(side='right')

        # New word ratio
        new_ratio_frame = Frame(batch_frame, bg=Colors.WHITE)
        new_ratio_frame.pack(fill='x', pady=Spacing.XS)

        Label(new_ratio_frame, text="New words ratio:", 
              font=Fonts.BODY, 
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(side='left')

        new_ratio_entry = Entry(new_ratio_frame, textvariable=self.new_word_ratio, 
                           font=Fonts.BODY, width=10, justify='center')
        new_ratio_entry.pack(side='right')

        # Generate button (using shared utility for large square button)
        self.generate_button = CommonPatterns.create_main_action_button(
            main_frame, "📖\nGenerate\nText", self.generate_wordtext, button_type="large_square"
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
                    
                    # Display results
                    print(f"📋 Import Results:")
                    print(f"  Total rows: {results['total_rows']}")
                    print(f"  ✅ Imported: {results['imported']}")
                    print(f"  ⏭️ Skipped: {results['skipped']}")
                    print(f"  ❌ Errors: {results['errors']}")
                    
                    if results['imported'] > 0:
                        messagebox.showinfo("Import Successful", 
                                          f"Successfully imported {results['imported']} new words!\n\n"
                                          f"Total rows: {results['total_rows']}\n"
                                          f"Skipped (already exist): {results['skipped']}\n"
                                          f"Errors: {results['errors']}")
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
                    result = self.vocab_app.run_learning_session(
                        total_words=self.total_words.get(),
                        new_word_ratio=self.new_word_ratio.get(),
                        language="French",
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
                    print(f"Load task completed with story length: {len(result.get('story', ''))}")
                    self.master.after(0, lambda: self.on_load_complete(result))
                except Exception as e:
                    error_msg = f"❌ Load failed: {str(e)}"
                    self.master.after(0, lambda: self.on_load_error(error_msg))
                finally:
                    def safe_button_reset():
                        try:
                            if hasattr(self, 'generate_button') and self.generate_button.winfo_exists():
                                self.generate_button.config(state='normal', text="📖\nGenerate\nText")
                        except Exception:
                            pass
                    self.master.after(0, safe_button_reset)
            
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
            
            if selected_words:
                if self.vocab_source.get() == "test":
                    print(f"🧪 Test mode complete! {len(selected_words)} words loaded")
                else:
                    print(f"✅ Generation complete! {len(selected_words)} words selected")
                
                # Start review interface
                self.show_review_interface(selected_words, story, audio_path)
            else:
                print("❌ No words were selected for the story")
            
        except Exception as e:
            self.on_generation_error(f"Error processing results: {str(e)}")
    
    def on_generation_error(self, error_message):
        """Handle generation errors"""
        print(error_message)
        self.generate_button.config(state='normal', text="📖\nGenerate\nText")

    def on_load_complete(self, result):
        """Handle successful load completion"""
        try:
            story = result.get('text', '')  # orchestrator returns 'text', not 'story'
            audio_path = result.get('audio_path', '')
            selected_words = result.get('words', [])  # orchestrator returns 'words', not 'selected_words'
            
            if story:
                print("✅ Last text loaded successfully (offline mode)")
                
                # Use saved vocabulary words if available, otherwise create placeholders
                if selected_words:
                    # Convert tuples to dictionaries for compatibility with review interface
                    review_words = [
                        {'word': word, 'translation': translation, 'pronunciation': pronunciation}
                        for word, translation, pronunciation in selected_words
                    ]
                    print(f"📚 Using {len(review_words)} saved vocabulary words for review")
                else:
                    # Fallback to placeholder words if no saved words found
                    review_words = [
                        {'word': f'Word{i+1}', 'translation': f'Translation{i+1}', 'pronunciation': ''}
                        for i in range(10)  # Create 10 placeholder words for review
                    ]
                    print("⚠️ No saved vocabulary words found, using placeholders")
                
                # Start review interface with loaded content
                self.show_review_interface(review_words, story, audio_path)
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
            test_audio_file = os.path.join(audio_dir, 'Le public mène la révolution médiatique - 20 juin 2025.mp3')
            test_audio_path = test_audio_file if os.path.exists(test_audio_file) else ""
            print(f"DEBUG: Test audio path: {test_audio_path}")
            print(f"DEBUG: Audio file exists: {os.path.exists(test_audio_path) if test_audio_path else False}")
            
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
    
    def show_review_interface(self, review_data, generated_text, audio_path):
        """Show the in-app review interface"""
        try:
            # Hide the main interface
            for widget in self.master.winfo_children():
                widget.pack_forget()
            
            # Create review interface
            self.review_interface = ReviewInterface(
                self.master, 
                review_data, 
                generated_text, 
                audio_path,
                back_callback=self.return_from_review,
                vocab_app=self.vocab_app
            )
            
        except Exception as e:
            print(f"Failed to show review interface: {str(e)}")
            
            # Restore main interface if review fails
            self.return_from_review()

    def return_from_review(self):
        """Return from review interface to main interface"""
        try:
            # Destroy review interface if it exists
            if hasattr(self, 'review_interface'):
                for widget in self.master.winfo_children():
                    widget.destroy()
                delattr(self, 'review_interface')
            
            # Recreate main interface
            self.setup_ui()
            
        except Exception as e:
            print(f"Error returning from review: {e}")


class ReviewInterface:
    """3-stage vocabulary review: READ → TILE → STATS"""
    
    def __init__(self, master, review_data, generated_text, audio_path, back_callback=None, vocab_app=None):
        self.master = master
        self.review_data = review_data
        self.generated_text = generated_text
        self.audio_path = audio_path
        self.back_callback = back_callback
        self.vocab_app = vocab_app
        
        # Review session state
        self.current_view = "READ"  # READ → TILE → STATS
        self.marked_difficult = set()
        self.reader_ui = None  # Will hold shared ReaderUI instance
        
        # Setup window and start with READ view
        self._setup_window()
        self.style_manager = apply_modern_theme()  # Use shared styling system
        self.setup_layout()
        self.show_read_view()

    def setup_layout(self):
        """Setup the main layout"""
        # Clear existing widgets
        for widget in self.master.winfo_children():
            widget.destroy()
        
        # Content frame fills the available space
        self.content_frame = ttk.Frame(self.master)
        self.content_frame.pack(fill='both', expand=True)
    
    def _setup_window(self):
        """Setup window configuration"""
        # Get the root window (in case master is a frame)
        root = self.master.winfo_toplevel()
        #check what kind of object root is
        print(f"DEBUG: root is of type {type(root)}")
        root.title("📚 InfiniLing - Vocabulary Review")
        # Note: Don't change geometry/size as this should adapt to existing window
        root.configure(bg=Colors.WHITE)
    
    # VIEW 1: Reading Practice (uses shared ReaderUI)
    def show_read_view(self):
        """Show reading view with text and audio using shared ReaderUI"""
        self.current_view = "READ"
        self.clear_content_frame()
        
        # Use shared ReaderUI for the text display and audio controls
        if hasattr(self, 'reader_ui'):
            del self.reader_ui
        
        # Create wrapper for the reading view
        reading_frame = Frame(self.content_frame, bg=Colors.WHITE)
        reading_frame.pack(fill='both', expand=True)

        
        # Use shared ReaderUI component
        self.reader_ui = ReaderUI(
            master=reading_frame,
            title="Reading Practice",
            audio_path=self.audio_path,
            text_content=self.generated_text,
            back_callback=self.back_callback
        )
        
        # Add navigation to tile view by finding and modifying the header
        self._add_navigation_to_reader_header(reading_frame)
    
    def _add_navigation_to_reader_header(self, reading_frame):
        """Add navigation button to the shared ReaderUI header"""
        for widget in reading_frame.winfo_children():
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    if hasattr(child, 'winfo_children'):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, Frame) and str(grandchild['bg']) == Colors.LIGHT_GRAY:
                                btn = ttk.Button(grandchild, text="Review Vocabulary →", 
                                               command=self.show_tile_view, 
                                               style='Accent.TButton')
                                btn.pack(side='right', padx=(Spacing.SM, 0))
                                return
    
    # VIEW 2: Vocabulary Review (tile selection)
    def show_tile_view(self):
        """Show vocabulary tile selection view"""
        self.current_view = "TILE"
        self.clear_content_frame()
        
        # Main container
        main_frame = ttk.Frame(self.content_frame, style='Card.TFrame', padding="40")
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Header with title and continue button
        self._create_tile_header(main_frame)
        
        # Create vocabulary tiles
        self._create_vocabulary_tiles(main_frame)
    
    def _create_tile_header(self, parent):
        """Create header for tile view"""
        header_frame = ttk.Frame(parent, style='Card.TFrame')
        header_frame.pack(fill='x', pady=(0, Spacing.LG))
        
        # Title section (left side)
        title_frame = ttk.Frame(header_frame, style='Card.TFrame')
        title_frame.pack(side='left', fill='x', expand=True)
        
        title = ttk.Label(title_frame, text="🎯 Select words you want to review again", style='Heading.TLabel')
        title.pack(anchor='w')
        
        subtitle = ttk.Label(title_frame, text="Click on vocabulary items that need more practice", style='Subheading.TLabel')
        subtitle.pack(anchor='w', pady=(Spacing.XS, 0))
        
        # Continue button (right side)
        continue_btn = ttk.Button(header_frame, text="Continue →", 
                                 command=self.show_statistics_view, style='Accent.TButton')
        continue_btn.pack(side='right', padx=(Spacing.LG, 0))
    
    def _create_vocabulary_tiles(self, parent):
        """Create the vocabulary selection tiles"""
        # Create container for tiles
        tiles_container = ttk.Frame(parent)
        tiles_container.pack(expand=True, fill='both', pady=(Spacing.SM, 0))
        tiles_container.configure(style='Card.TFrame')
        
        # Tiles grid (4 columns x 5 rows, max 20 items)
        grid_frame = ttk.Frame(tiles_container)
        grid_frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.tiles = []
        cols = 4
        rows = 5
        max_tiles = cols * rows
        vocab_to_show = self.review_data[:max_tiles]
        
        for i, word_data in enumerate(vocab_to_show):
            word, translation, pronunciation = self.extract_word_data(word_data, i)
            row = i // cols
            col = i % cols
            
            # Create individual tile
            tile_data = self._create_single_tile(grid_frame, word, translation, pronunciation, row, col)
            self.tiles.append((tile_data, word))
        
        # Configure grid weights
        LayoutHelpers.configure_grid_weights(grid_frame, cols, rows, min_col_width=220, min_row_height=140)
    
    def _create_single_tile(self, parent, word, translation, pronunciation, row, col):
        """Create a single vocabulary tile using shared styling system"""
        # Create tile frame
        tile_frame = ttk.Frame(parent)
        tile_frame.grid(row=row, column=col, padx=Spacing.XS, pady=Spacing.XS, 
                       sticky='nsew', ipadx=Spacing.XS, ipady=Spacing.XS)
        tile_frame.configure(relief='solid', borderwidth=2)
        tile_frame.grid_propagate(False)
        tile_frame.configure(width=200, height=100)
        
        # Create inner content using shared tile colors
        tile_colors = TileStyles.get_normal_colors()
        content_frame = Frame(tile_frame, bg=tile_colors['bg'], relief='flat')
        content_frame.pack(fill='both', expand=True, padx=Spacing.XS, pady=Spacing.XS)
        
        # Word display
        word_label = Label(content_frame, text=word, 
                          font=Fonts.TILE_WORD,
                          bg=tile_colors['bg'], fg=tile_colors['word_fg'])
        word_label.pack(pady=(Spacing.SM, 2))
        
        # Translation
        trans_label = Label(content_frame, text=f"→ {translation}", 
                           font=Fonts.TILE_TRANSLATION,
                           bg=tile_colors['bg'], fg=tile_colors['translation_fg'])
        trans_label.pack(pady=(2, Spacing.XS))
        
        # Pronunciation if available
        pron_label = None
        if pronunciation:
            pron_label = Label(content_frame, text=f"[{pronunciation}]", 
                              font=Fonts.TILE_PRONUNCIATION,
                              bg=tile_colors['bg'], fg=tile_colors['pronunciation_fg'])
            pron_label.pack(pady=(0, Spacing.SM))
        
        # Click handler for the entire tile
        click_handler = lambda event: self.toggle_tile(word)
        content_frame.bind('<Button-1>', click_handler)
        word_label.bind('<Button-1>', click_handler)
        trans_label.bind('<Button-1>', click_handler)
        if pron_label:
            pron_label.bind('<Button-1>', click_handler)
        
        return (tile_frame, content_frame, word_label, trans_label, pron_label)
    
    # VIEW 3: Statistics & Save options
    def show_statistics_view(self):
        """Show statistics and save options"""
        self.current_view = "STATS"
        self.clear_content_frame()
        
        # Main container
        main_frame = ttk.Frame(self.content_frame, style='Card.TFrame', padding="30")
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Header with save options
        self._create_statistics_header(main_frame)
        
        # Statistics summary
        self._create_statistics_summary(main_frame)
        
        # Visualization
        self._create_statistics_visualization(main_frame)

    def _create_statistics_header(self, parent):
        """Create header with save options for statistics view"""
        header_frame = ttk.Frame(parent, style='Card.TFrame')
        header_frame.pack(fill='x', pady=(0, Spacing.LG))
        
        # Navigation buttons (left side)
        nav_frame = ttk.Frame(header_frame, style='Card.TFrame')
        nav_frame.pack(side='left')
        
        save_exit_btn = ttk.Button(nav_frame, text="💾 Save & Exit", 
                                  command=self.save_and_exit, style='Accent.TButton')
        save_exit_btn.pack(side='left', padx=(0, Spacing.SM))
        
        save_menu_btn = ttk.Button(nav_frame, text="💾 Save & Menu", 
                                  command=self.save_and_menu, style='Modern.TButton')
        save_menu_btn.pack(side='left', padx=(0, Spacing.SM))
        
        exit_no_save_btn = ttk.Button(nav_frame, text="🚪 Exit (No Save)", 
                                     command=self.exit_without_saving, style='Warning.TButton')
        exit_no_save_btn.pack(side='left')
        
        # Title (right side)
        title_frame = ttk.Frame(header_frame, style='Card.TFrame')
        title_frame.pack(side='right')
        
        title = ttk.Label(title_frame, text="📊 Review Statistics", style='Heading.TLabel')
        title.pack()
    
    def _create_statistics_summary(self, parent):
        """Create statistics summary section"""
        summary_frame = ttk.Frame(parent, style='Card.TFrame')
        summary_frame.pack(fill='x', pady=(0, Spacing.LG))
        
        total_words = len(self.review_data)
        difficult_words = len(self.marked_difficult)
        easy_words = total_words - difficult_words
        
        summary_text = f"📖 Total: {total_words}   |   😰 Difficult: {difficult_words}   |   😊 Easy: {easy_words}"
        summary_label = ttk.Label(summary_frame, text=summary_text, style='Subheading.TLabel')
        summary_label.pack()
    
    def _create_statistics_visualization(self, parent):
        """Create statistics visualization"""
        viz_frame = ttk.Frame(parent, style='Card.TFrame')
        viz_frame.pack(fill='both', expand=True, pady=(Spacing.SM, 0))
        
        try:
            # Try to create advanced visualization
            self.create_urgency_comparison_chart(viz_frame)
        except ImportError:
            # Simple fallback visualization
            fallback_text = f"📊 Review Complete!\n\n" \
                           f"Words reviewed: {len(self.review_data)}\n" \
                           f"Marked for more practice: {len(self.marked_difficult)}\n" \
                           f"Understood well: {len(self.review_data) - len(self.marked_difficult)}"
            
            fallback_label = ttk.Label(viz_frame, text=fallback_text, 
                                     style='Body.TLabel', justify='center')
            fallback_label.pack(expand=True)

    def create_urgency_comparison_chart(self, parent_frame):
        """Create an elegant urgency comparison visualization"""
        try:
            # Import matplotlib for visualization
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
            
            # Prepare data for visualization
            word_data = []
            
            if self.vocab_app and hasattr(self.vocab_app, 'database_manager'):
                # Get word stats from database
                all_words = self.vocab_app.database_manager.word_stats
                
                # Calculate urgency for each word
                for word_key, stats in all_words.items():
                    if '|' in word_key:
                        word, translation = word_key.split('|', 1)
                        
                        # Calculate before urgency
                        before_urgency = self.vocab_app.vocabulary_selector.calculate_word_priority(word, translation)
                        
                        # Check if word was reviewed and marked difficult
                        reviewed = False
                        difficult = False
                        for idx, wd in enumerate(self.review_data):
                            w, t, _ = self.extract_word_data(wd, idx)
                            if w == word:
                                reviewed = True
                                if word in self.marked_difficult:
                                    difficult = True
                                break
                        
                        # Calculate after urgency
                        if difficult:
                            after_urgency = min(100, before_urgency + 15)
                        elif reviewed:
                            after_urgency = max(0, before_urgency - 10)
                        else:
                            after_urgency = before_urgency
                        
                        word_data.append({
                            'word': word,
                            'before': before_urgency,
                            'after': after_urgency,
                            'reviewed': reviewed,
                            'difficult': difficult
                        })
            
            if not word_data:
                # Fallback if no data available
                no_data_label = ttk.Label(parent_frame, 
                                        text="📊 No word tracking data available for visualization", 
                                        style='Body.TLabel')
                no_data_label.pack(expand=True)
                return
            
            # Sort by before urgency and limit to top 50
            word_data.sort(key=lambda x: x['before'], reverse=True)
            word_data = word_data[:50]
            
            # Create matplotlib figure
            fig = Figure(figsize=(14, 8), dpi=100, facecolor='white')
            ax = fig.add_subplot(111)
            
            # Prepare data for plotting
            x_pos = list(range(len(word_data)))
            before_urgencies = [wd['before'] for wd in word_data]
            after_urgencies = [wd['after'] for wd in word_data]
            
            # Create line chart
            ax.plot(x_pos, before_urgencies, 'o-', color='#dc3545', linewidth=2, 
                   markersize=6, label='Before Review', alpha=0.8)
            ax.plot(x_pos, after_urgencies, 'o-', color='#28a745', linewidth=2, 
                   markersize=6, label='After Review', alpha=0.8)
            
            # Styling
            ax.set_xlabel('Words (sorted by initial urgency)', fontsize=12, fontweight='bold')
            ax.set_ylabel('Urgency Score', fontsize=12, fontweight='bold')
            ax.set_title('Word Learning Progress: Before vs After Review', 
                        fontsize=16, fontweight='bold', pad=20)
            ax.set_ylim(0, 105)
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
            ax.set_xticks([])
            
            # Add statistics
            total_reviewed = sum(1 for wd in word_data if wd['reviewed'])
            avg_before = sum(before_urgencies) / len(before_urgencies) if before_urgencies else 0
            avg_after = sum(after_urgencies) / len(after_urgencies) if after_urgencies else 0
            
            stats_text = f"Total: {len(word_data)} | Reviewed: {total_reviewed} | Avg urgency: {avg_before:.1f} -> {avg_after:.1f}"
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, parent_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
            
        except ImportError:
            # Fallback if matplotlib not available
            raise ImportError("matplotlib not available")
        except Exception as e:
            # Error fallback
            error_label = ttk.Label(parent_frame, 
                                  text=f"Error creating visualization: {str(e)}", 
                                  style='Body.TLabel')
            error_label.pack(expand=True)

    # Save and business logic methods
    def save_review_progress(self):
        """Save the review progress to database"""
        try:
            if self.vocab_app and hasattr(self.vocab_app, 'database_manager'):
                print(f"💾 Saving word progress to database...")
                # Update word statistics based on review
                for idx, word_data in enumerate(self.review_data):
                    word, translation, _ = self.extract_word_data(word_data, idx)
                    if word in self.marked_difficult:
                        # Mark as difficult (to be repeated)
                        self.vocab_app.database_manager.add_occurrence(word, translation, repeat=True)
                    else:
                        # Mark as understood (not repeated)
                        self.vocab_app.database_manager.add_occurrence(word, translation, repeat=False)
            else:
                print("⚠️ Database manager not available")
        except Exception as e:
            print(f"Error saving review progress: {e}")
            raise

    def save_and_exit(self):
        """Save progress and exit the application"""
        try:
            self.save_review_progress()
            print("👋 Exiting application...")
            if hasattr(self, 'master'):
                self.master.quit()
                self.master.destroy()
        except Exception as e:
            print(f"Error saving and exiting: {e}")
            if hasattr(self, 'master'):
                self.master.quit()

    def save_and_menu(self):
        """Save progress and return to main menu"""
        try:
            self.save_review_progress()
            print("🏠 Returning to main menu...")
            if self.back_callback:
                self.back_callback()
        except Exception as e:
            print(f"Error saving and returning to menu: {e}")
            if self.back_callback:
                self.back_callback()

    def exit_without_saving(self):
        """Exit without saving progress"""
        try:
            print("🚪 Exiting without saving progress...")
            
            # Show confirmation dialog
            result = msgbox.askyesno(
                "Exit Without Saving", 
                "Are you sure you want to exit without saving your review progress?\n\n"
                "This will undo all the words you marked as difficult or easy in this session.",
                icon='warning'
            )
            
            if result:
                print("⚠️ Review progress discarded")
                if self.back_callback:
                    self.back_callback()
        except Exception as e:
            print(f"Error exiting without saving: {e}")
            if self.back_callback:
                self.back_callback()

    
    # Helper methods
    def extract_word_data(self, word_data, idx=None):
        """Helper to extract word, translation, pronunciation from dict or tuple/list"""
        if isinstance(word_data, dict):
            word = word_data.get('word', f'Word{idx+1}' if idx is not None else 'Word')
            translation = word_data.get('translation', f'Translation{idx+1}' if idx is not None else 'Translation')
            pronunciation = word_data.get('pronunciation', '')
        elif isinstance(word_data, (tuple, list)):
            word = word_data[0] if len(word_data) > 0 else (f'Word{idx+1}' if idx is not None else 'Word')
            translation = word_data[1] if len(word_data) > 1 else (f'Translation{idx+1}' if idx is not None else 'Translation')
            pronunciation = word_data[2] if len(word_data) > 2 else ''
        else:
            word = f'Word{idx+1}' if idx is not None else 'Word'
            translation = f'Translation{idx+1}' if idx is not None else 'Translation'
            pronunciation = ''
        return word, translation, pronunciation

    def clear_content_frame(self):
        """Clear all widgets from content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def toggle_tile(self, word):
        """Toggle word selection in tile view using shared styling system"""
        if word in self.marked_difficult:
            self.marked_difficult.remove(word)
            selected = False
        else:
            self.marked_difficult.add(word)
            selected = True
        
        # Update tile style using shared utility
        for tile_data, tile_word in self.tiles:
            if tile_word == word:
                tile_frame, content_frame, word_label, trans_label, pron_label = tile_data
                TileStyles.apply_tile_style(content_frame, word_label, trans_label, pron_label, selected)
                break

