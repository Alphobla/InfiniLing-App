from tkinter import Frame, Button, Label, messagebox, ttk, Entry, Radiobutton, DoubleVar, IntVar, StringVar
from ..shared.reader_ui import ReaderUI
from ..shared.styles import Colors, Fonts, Spacing
from ..shared.style_utils import StyledWidgets, CommonPatterns
from ..shared.languages import get_all_languages, get_code, get_name
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
        
        # Group all vocabulary config reads together
        self.vocab_defaults = self.config.get('vocabulary')

        # Determine initial source: Use scratch if databank is empty
        initial_source = "databank"
        try:
            if vocab_service and vocab_service.get_vocabulary_count() == 0:
                initial_source = "scratch"
        except Exception:
            pass

        self.vocab_source = StringVar(value=initial_source)  # Radio button group: "scratch", "last_text", "databank"
        self.total_words = IntVar(value=self.vocab_defaults['default_total_words'])
        self.new_word_ratio = DoubleVar(value=self.vocab_defaults['default_new_word_ratio'])
        self.text_length = IntVar(value=self.vocab_defaults['default_text_length'])
        # Use last used language from settings (None if not set)
        last_lang_code = self.config.get_last_language()
        self.selected_language = StringVar(value=last_lang_code or "")
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

        # Option 1: Start from scratch
        scratch_radio = Radiobutton(vocab_source_frame,
                                   text="Start from scratch (generate new words)",
                                   variable=self.vocab_source,
                                   value="scratch",
                                   font=Fonts.BODY,
                                   bg=Colors.WHITE, fg=Colors.PRIMARY,
                                   activebackground=Colors.WHITE)
        scratch_radio.pack(anchor='w', pady=2)

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

        # Option 2: Use last generated text
        last_text_radio = Radiobutton(vocab_source_frame,
                                      text="Use last generated text",
                                      variable=self.vocab_source,
                                      value="last_text",
                                      font=Fonts.BODY,
                                      bg=Colors.WHITE, fg=Colors.INFO,
                                      activebackground=Colors.WHITE)
        last_text_radio.pack(anchor='w', pady=2)

        # Option 3: Use vocabulary database
        databank_radio = Radiobutton(vocab_source_frame,
                                    text="Use vocabulary database",
                                    variable=self.vocab_source,
                                    value="databank",
                                    font=Fonts.BODY,
                                    bg=Colors.WHITE, fg=Colors.DARK_GRAY,
                                    activebackground=Colors.WHITE)
        databank_radio.pack(anchor='w', pady=2)

        # Databank-specific options (hidden by default)
        self.databank_options_frame = Frame(vocab_source_frame, bg=Colors.WHITE)

        # Total words to learn
        tot_words_frame = Frame(self.databank_options_frame, bg=Colors.WHITE)
        tot_words_frame.pack(fill='x', pady=Spacing.XS, padx=(20, 0))
        tot_words_entry = Entry(tot_words_frame, textvariable=self.total_words,
                           font=Fonts.BODY, width=5, justify='center')
        tot_words_entry.pack(side='left', padx=Spacing.XS)
        Label(tot_words_frame, text="Total words to learn",
              font=Fonts.BODY,
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(side='left')

        # New word ratio
        new_ratio_frame = Frame(self.databank_options_frame, bg=Colors.WHITE)
        new_ratio_frame.pack(fill='x', pady=Spacing.XS, padx=(20, 0))
        new_ratio_entry = Entry(new_ratio_frame, textvariable=self.new_word_ratio,
                           font=Fonts.BODY, width=5, justify='center')
        new_ratio_entry.pack(side='left', padx=Spacing.XS)
        Label(new_ratio_frame, text="New words ratio (0-1)",
              font=Fonts.BODY,
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(side='left')

        # Common options (always visible)
        common_frame = Frame(vocab_source_frame, bg=Colors.WHITE)
        common_frame.pack(fill='x', pady=(Spacing.SM, 0))

        # Text length
        text_length_frame = Frame(common_frame, bg=Colors.WHITE)
        text_length_frame.pack(fill='x', pady=Spacing.XS)
        text_length_entry = Entry(text_length_frame, textvariable=self.text_length,
                           font=Fonts.BODY, width=5, justify='center')
        text_length_entry.pack(side='left', padx=Spacing.XS)
        Label(text_length_frame, text="Text length (words)",
              font=Fonts.BODY,
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(side='left')

        # Language selection
        language_frame = Frame(common_frame, bg=Colors.WHITE)
        language_frame.pack(fill='x', pady=Spacing.XS)

        # Get languages from central module
        all_languages = get_all_languages()  # [(name, code), ...]
        language_names = [name for name, code in all_languages]

        language_combobox = ttk.Combobox(language_frame,
                                        textvariable=self.selected_language,
                                        values=language_names,
                                        state="readonly",
                                        width=10,
                                        font=Fonts.BODY)
        language_combobox.pack(side='left', padx=Spacing.XS)
        # Set to last used language name (if any)
        last_lang = self.config.get_last_language()
        if last_lang:
            language_combobox.set(get_name(last_lang))

        Label(language_frame, text="Generated language",
              font=Fonts.BODY,
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(side='left', padx=(0, Spacing.XS))

        # Trace to show/hide conditional options
        def on_source_change(*args):
            source = self.vocab_source.get()
            # Show difficulty only for scratch mode
            if source == "scratch":
                self.difficulty_frame.pack(anchor='w', pady=2, after=scratch_radio)
            else:
                self.difficulty_frame.pack_forget()
            # Show databank options only for databank mode
            if source == "databank":
                self.databank_options_frame.pack(fill='x', after=databank_radio)
            else:
                self.databank_options_frame.pack_forget()

        self.vocab_source.trace_add("write", on_source_change)
        on_source_change()  # Initial state
        

        # Generate button (using shared utility for large square button)
        self.generate_button = CommonPatterns.create_main_action_button(
            main_frame, "📖\nGenerate\nText", self.generate_wordtext, button_type="large_square", center=True
        )

    def generate_wordtext(self):
        """Generate wordtext using the modern backend"""
        try:
            # Validate language selection
            if not self.selected_language.get():
                messagebox.showerror("Error", "Please select a language first.")
                return

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
            print(f"🚀 Generating Text... Source: {vocab_source}, Total Words: {self.total_words.get()}, Lang: {self.selected_language.get()}")
            
            # Run generation in a separate thread
            def generation_task():
                try:
                    # Get selected language code (convert display name to code)
                    lang_code = self.get_selected_language_code()
                    # Save as last used language
                    self.config.save_last_language(lang_code)

                    if vocab_source == "scratch":
                        # For scratch mode, word count is derived from text length
                        scratch_word_count = max(5, self.text_length.get() // 20)
                        result = self.vocab_app.run_scratch_session(
                            language=lang_code,
                            difficulty=self.selected_difficulty.get(),
                            total_words=scratch_word_count,
                            text_length=self.text_length.get(),
                            generate_audio=True,
                            progress_callback=lambda msg: print(f"✨ {msg}"),
                        )
                    else:
                        result = self.vocab_app.run_learning_session(
                            total_words=self.total_words.get(),
                            new_word_ratio=self.new_word_ratio.get(),
                            text_length=self.text_length.get(),
                            language=lang_code,
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
            
            if not words and not text:
                msg = "No content was generated."
                if self.vocab_source.get() == "databank":
                    msg += "\n\nTip: Your databank might be empty. Try 'Start from scratch' to generate new words!"
                else:
                    msg += " Please check your API key and connection."
                self.on_task_error(msg)
                return
                
            self.proceed_to_reader(words, text, audio_path)

        except Exception as e:
            self.on_task_error(f"Error processing results: {str(e)}")

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
        """Handle task errors with user notification"""
        print(f"❌ {error_message}")
        # Reset button state
        self.generate_button.config(state='normal', text="📖\nGenerate\nText")
        # Show error to user
        messagebox.showerror("Generation Error", error_message)

    def proceed_to_reader(self, words, generated_text, audio_path):
        """Show the in-app reader interface"""
        try:            
            # Hide the main interface
            for widget in self.master.winfo_children():
                widget.pack_forget()
            
            print(f"service app: {type(self.vocab_app)}")
            # Get target language from config
            language_to = self.config.get('vocabulary.languages.to', 'de')

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
                language_from=self.get_selected_language_code(),
                language_to=language_to,
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

    def get_selected_language_code(self) -> str:
        """Convert selected language display name to code for API calls."""
        display_name = self.selected_language.get()
        code = get_code(display_name)
        return code if code else display_name.lower()[:2]
