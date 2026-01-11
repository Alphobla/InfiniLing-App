from tkinter import Frame, Button, Label, filedialog, messagebox, ttk, Entry, Checkbutton, Radiobutton, DoubleVar, BooleanVar, IntVar, StringVar
from ..shared.reader_ui import ReaderUI
from ..shared.styles import apply_modern_theme, Colors, Fonts, Spacing
from ..shared.style_utils import StyledWidgets, TileStyles, LayoutHelpers, CommonPatterns
import os
import threading
from ..shared.styles import center_top_window
import json

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
        
        # Group all vocabulary config reads together
        self.vocab_defaults = self.config.get('vocabulary')
        
        # Configuration variables
        self.vocab_source = StringVar(value="databank")  # Radio button group: "databank", "test", "last_text"
        self.import_new_list = BooleanVar(value=False)  # Sub-option for databank
        self.total_words = IntVar(value=self.vocab_defaults['default_total_words'])
        self.new_word_ratio = DoubleVar(value=self.vocab_defaults['default_new_word_ratio'])
        self.text_length = IntVar(value=self.vocab_defaults['default_text_length'])
        self.selected_language = StringVar(value="fr")  # Language selection
        self.selected_difficulty = StringVar(value="A1")  # Difficulty for scratch mode
        self.set_window_size()
        self.setup_ui()
        
    def setup_ui(self):
        
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
                                  command=self.new_list_importer,
                                  font=Fonts.BODY,
                                  bg=Colors.WHITE, fg=Colors.DARK_GRAY,
                                  activebackground=Colors.WHITE)
        import_check.pack(anchor='w')

        test_radio = Radiobutton(vocab_source_frame, 
                                text="✨ Start from scratch (generate new words)", 
                                variable=self.vocab_source,
                                value="scratch",
                                font=Fonts.BODY,
                                bg=Colors.WHITE, fg=Colors.PRIMARY,
                                activebackground=Colors.WHITE)
        test_radio.pack(anchor='w', pady=2)

        # Difficulty selection for scratch mode (hidden by default)
        self.difficulty_frame = Frame(vocab_source_frame, bg=Colors.WHITE)
        Label(self.difficulty_frame, text="Difficulty:", font=Fonts.BODY, bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(side='left', padx=(20, 5))
        difficulty_combo = ttk.Combobox(self.difficulty_frame, 
                                       textvariable=self.selected_difficulty,
                                       values=["A1", "A2", "B1", "B2", "C1", "C2"],
                                       state="readonly",
                                       width=5,
                                       font=Fonts.BODY)
        difficulty_combo.pack(side='left')
        
        # Trace to show/hide difficulty
        def on_source_change(*args):
            if self.vocab_source.get() == "scratch":
                self.difficulty_frame.pack(anchor='w', pady=2, after=test_radio)
            else:
                self.difficulty_frame.pack_forget()
        
        self.vocab_source.trace_add("write", on_source_change)
        on_source_change() # Initial state

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

        # Text length
        text_length_frame = Frame(vocab_source_frame, bg=Colors.WHITE)
        text_length_frame.pack(fill='x', pady=Spacing.XS)
        text_length_entry = Entry(text_length_frame, textvariable=self.text_length, 
                           font=Fonts.BODY, width=5, justify='center')
        text_length_entry.pack(side='left', padx=Spacing.XS)
        Label(text_length_frame, text="Text length (words)", 
              font=Fonts.BODY, 
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(side='left')

        # Language selection
        language_frame = Frame(vocab_source_frame, bg=Colors.WHITE)
        language_frame.pack(fill='x', pady=Spacing.XS)

        # Get language options from config
        languages = self.vocab_defaults['languages']['available_languages']

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

    def generate_wordtext(self):
        """Generate wordtext using the modern backend"""
        try:
            # Check selected vocabulary source
            vocab_source = self.vocab_source.get()
            
            if vocab_source == "scratch":
                # scratch mode logic will be handled in separate thread
                pass
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
                    # Get selected language code
                    selected_lang_name = self.selected_language.get()
                    
                    if vocab_source == "scratch":
                        result = self.vocab_app.run_scratch_session(
                            language=selected_lang_name,
                            difficulty=self.selected_difficulty.get(),
                            total_words=self.total_words.get(),
                            text_length=self.text_length.get(),
                            generate_audio=True,
                            progress_callback=lambda msg: print(f"✨ {msg}"),
                        )
                    else:
                        result = self.vocab_app.run_learning_session(
                            total_words=self.total_words.get(),
                            new_word_ratio=self.new_word_ratio.get(),
                            text_length=self.text_length.get(),
                            language=selected_lang_name,  # Pass the full language name
                            generate_audio=True,
                            progress_callback=lambda msg: print(f"📖 {msg}"),
                        )
                    self.master.after(0, lambda: self.on_generation_complete(result))
                except Exception as e:
                    error_msg = f"❌ Generation failed: {str(e)}"
                    self.master.after(0, lambda: self.on_task_error(error_msg))

            
            threading.Thread(target=generation_task, daemon=True).start()
            
        except Exception as e:
            print(f"❌ Error starting generation: {str(e)}")
            self.generate_button.config(state='normal', text="📖\nGenerate\nText")

    def new_list_importer(self):
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
                                          f"⏭️ Skipped the rest (already exist).\n")
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

    
    def load_last_text_mode(self):
        """Load last generated text mode for offline use"""
        try:
            print("📂 Loading last generated text...")
            
            # Disable generate button during processing
            self.generate_button.config(state='disabled', text="Loading...")
            
            def load_task():
                try:
                    print("Loading last session...")
                    result = self.vocab_app.read_temp_session_data()

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
            words = result.get('words')
            text = result.get('text')
            audio_path = result.get('audio_path')
            self.proceed_to_reader(words, text, audio_path)

        except Exception as e:
            self.on_generation_error(f"Error processing results: {str(e)}")

    def on_load_complete(self, result):
        """Handle successful load completion"""
        try:
            # Reset button state
            self.generate_button.config(state='normal', text="📖\nGenerate\nText")
            text = result.get('text', '')  
            audio_path = result.get('audio_path', '')
            words = result.get('words', [])
            
            if text:
                print("✅ Last text loaded successfully (offline mode)")
                
                # Start reader interface with loaded content
                self.vocab_app.update_current_session_data(result)
                self.proceed_to_reader(words, text, audio_path)
            else:
                print("❌ No saved text found. Generate new content first.")
            
        except Exception as e:
            self.on_task_error(f"Error processing loaded content: {str(e)}")
    
    def on_task_error(self, error_message):
        """Handle task errors"""
        print(f"❌ {error_message}")
        self.generate_button.config(state='normal', text="📖\nGenerate\nText")

    def proceed_to_reader(self, words, generated_text, audio_path):
        """Show the in-app reader interface"""
        try:            
            # Hide the main interface
            for widget in self.master.winfo_children():
                widget.pack_forget()
            
            print(f"service app: {type(self.vocab_app)}")
            # Create review interface
            self.reader_ui = ReaderUI(
                master=self.master,
                title="Reading Practice",
                service_app=self.vocab_app,
                audio_path=audio_path,
                text_content=generated_text,
                back_callback=self.return_to_config,
                forward_callback="proceed_to_review",
                forward_text="Review Words →",
                config=self.config
            )
            
        except Exception as e:
            print(f"Failed to show gentexter reader interface: {str(e)}")

    def return_to_config(self):
        """Return from reader interface to config interface"""
        # Clear session data when returning
        if hasattr(self, 'vocab_service'):
            self.vocab_service.clear_current_session_data()
            
        # Destroy reader interface if it exists
        for widget in self.master.winfo_children():
            widget.destroy()
        
        # Recreate config interface
        self.set_window_size()
        self.setup_ui()

    def set_window_size(self):
        """Set window size for gentexter interface using config"""
        root = self.master.winfo_toplevel()
        window_width, window_height = self.config.get_window_size('gentexter')
        center_top_window(self.master, width=window_width, height=window_height)
