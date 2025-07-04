from tkinter import Tk, Frame, Button, Label, filedialog, messagebox, ttk, Entry, Checkbutton, BooleanVar, IntVar, Text, Scrollbar, DoubleVar
from vocabulary.main_orchestrator import VocabularyApp
import os
import threading

# Try to import VLC for audio playback
try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False
    print("Warning: VLC not available. Audio playback will be disabled.")

class VocabularyInterface:
    def __init__(self, master, back_callback=None):
        self.master = master
        self.back_callback = back_callback
        self.master.title("📚 InfiniLing - Wordstory")
        self.master.geometry("500x600")
        self.master.configure(bg='#f8f9fa')

        # Initialize the modern vocabulary app backend
        tracking_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'word_tracking.json')
        self.vocab_app = VocabularyApp(tracking_file_path)
        
        # Configuration variables
        self.use_databank = BooleanVar(value=True)
        self.import_new_list = BooleanVar(value=False)
        self.use_test_mode = BooleanVar(value=False)
        self.use_last_text = BooleanVar(value=False)
        self.random_sample_size = IntVar(value=40)
        self.final_selection_size = IntVar(value=20)
        
        self.setup_ui()

    def setup_ui(self):
        # Main container
        main_frame = Frame(self.master, bg='#f8f9fa')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Header with back button
        header_frame = Frame(main_frame, bg='#f8f9fa')
        header_frame.pack(fill='x', pady=(0, 15))

        if self.back_callback:
            back_button = Button(header_frame, text="← Menu", 
                               command=self.back_callback,
                               font=("Segoe UI", 10, "bold"),
                               bg='#95a5a6', fg='white',
                               activebackground='#7f8c8d',
                               relief='flat', bd=0, pady=5, padx=15)
            back_button.pack(side='left')

        # Title
        title_label = Label(main_frame, text="📚 Wordstory", 
                           font=("Segoe UI", 20, "bold"), 
                           bg='#f8f9fa', fg='#2c3e50')
        title_label.pack(pady=(0, 30))

        # Configuration section
        config_frame = Frame(main_frame, bg='#ffffff', relief='raised', bd=1)
        config_frame.pack(fill='x', pady=(0, 20), padx=10)

        Label(config_frame, text="Configuration", 
              font=("Segoe UI", 14, "bold"), 
              bg='#ffffff', fg='#2c3e50').pack(pady=(15, 15))

        # Vocabulary source options
        vocab_source_frame = Frame(config_frame, bg='#ffffff')
        vocab_source_frame.pack(fill='x', padx=20, pady=(0, 15))

        databank_check = Checkbutton(vocab_source_frame, 
                                    text="Use vocabulary databank", 
                                    variable=self.use_databank,
                                    font=("Segoe UI", 11),
                                    bg='#ffffff', fg='#2c3e50',
                                    activebackground='#ffffff')
        databank_check.pack(anchor='w', pady=2)

        import_check = Checkbutton(vocab_source_frame, 
                                  text="Import new list to databank", 
                                  variable=self.import_new_list,
                                  command=self.on_import_check,
                                  font=("Segoe UI", 11),
                                  bg='#ffffff', fg='#2c3e50',
                                  activebackground='#ffffff')
        import_check.pack(anchor='w', pady=2)

        test_check = Checkbutton(vocab_source_frame, 
                                text="🧪 Test mode (use preset data)", 
                                variable=self.use_test_mode,
                                font=("Segoe UI", 11),
                                bg='#ffffff', fg='#e67e22',
                                activebackground='#ffffff')
        test_check.pack(anchor='w', pady=2)

        last_text_check = Checkbutton(vocab_source_frame, 
                                      text="📄 Use last generated text", 
                                      variable=self.use_last_text,
                                      font=("Segoe UI", 11),
                                      bg='#ffffff', fg='#3498db',
                                      activebackground='#ffffff')
        last_text_check.pack(anchor='w', pady=2)

        # Batch size configuration
        batch_frame = Frame(config_frame, bg='#ffffff')
        batch_frame.pack(fill='x', padx=20, pady=(10, 20))

        # Random word batch size
        random_frame = Frame(batch_frame, bg='#ffffff')
        random_frame.pack(fill='x', pady=5)
        
        Label(random_frame, text="Random word batch size:", 
              font=("Segoe UI", 11), 
              bg='#ffffff', fg='#2c3e50').pack(side='left')
        
        random_entry = Entry(random_frame, textvariable=self.random_sample_size, 
                           font=("Segoe UI", 11), width=10, justify='center')
        random_entry.pack(side='right')

        # Urgent word batch size
        urgent_frame = Frame(batch_frame, bg='#ffffff')
        urgent_frame.pack(fill='x', pady=5)
        
        Label(urgent_frame, text="Urgent word batch size:", 
              font=("Segoe UI", 11), 
              bg='#ffffff', fg='#2c3e50').pack(side='left')
        
        urgent_entry = Entry(urgent_frame, textvariable=self.final_selection_size, 
                           font=("Segoe UI", 11), width=10, justify='center')
        urgent_entry.pack(side='right')

        # Generate button (centered square)
        generate_frame = Frame(main_frame, bg='#f8f9fa')
        generate_frame.pack(pady=30)

        generate_button_frame = Frame(generate_frame, bg='#27ae60', relief='raised', bd=2)
        generate_button_frame.pack()
        generate_button_frame.pack_propagate(False)
        generate_button_frame.configure(width=180, height=180)

        self.generate_button = Button(generate_button_frame, text="📖\nGenerate\nWordtext", 
                                     command=self.generate_wordtext,
                                     font=("Segoe UI", 14, "bold"),
                                     bg='#27ae60', fg='white',
                                     activebackground='#219a52', activeforeground='white',
                                     relief='flat', bd=0)
        self.generate_button.pack(fill='both', expand=True)

        # Status section
        status_frame = Frame(main_frame, bg='#ffffff', relief='raised', bd=1)
        status_frame.pack(fill='x', padx=10, pady=(20, 0))
        status_frame.pack_propagate(False)
        status_frame.configure(height=60)

        self.status_label = Label(status_frame, text="Ready to generate wordtext", 
                                 font=("Segoe UI", 10), 
                                 bg='#ffffff', fg='#7f8c8d')
        self.status_label.pack(expand=True)

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
                    # Use the modern backend to import vocabulary
                    imported_count = self.vocab_app.import_vocabulary_from_file(file_path)
                    
                    if imported_count > 0:
                        self.status_label.config(text=f"Imported {imported_count} new words to databank")
                    else:
                        self.status_label.config(text="No new words to import (all words already in databank)")
                    
                except Exception as e:
                    self.status_label.config(text=f"Import failed: {str(e)}")
                    self.import_new_list.set(False)
            else:
                # User canceled file selection
                self.import_new_list.set(False)

    def generate_wordtext(self):
        """Generate wordtext using the modern backend"""
        try:
            # Pull latest from Git before generating words
            git_status = None
            if hasattr(self.vocab_app, 'git_manager'):
                self.status_label.config(text="🔄 Pulling latest vocabulary from Git...")
                print("🔄 Pulling latest vocabulary from Git...")
                git_status = self.vocab_app.git_manager.pull_latest()
                if git_status:
                    print("✅ Git pull successful. Using latest vocabulary.")
                    self.status_label.config(text="✅ Git pull successful. Using latest vocabulary.")
                else:
                    print("⚠️ Git pull failed. Using local vocabulary.")
                    self.status_label.config(text="⚠️ Git pull failed. Using local vocabulary.")
            # Check if test mode is enabled
            if self.use_test_mode.get():
                self.run_test_mode()
                return
            
            # Check if use last text mode is enabled
            if self.use_last_text.get():
                self.load_last_text_mode()
                return
            
            # Validate configuration
            random_size = self.random_sample_size.get()
            urgent_size = self.final_selection_size.get()
            
            if random_size <= 0 or urgent_size <= 0:
                self.status_label.config(text="❌ Batch sizes must be positive numbers")
                return
            
            if urgent_size > random_size:
                self.status_label.config(text="❌ Urgent batch size cannot be larger than random batch size")
                return
                
            if not self.use_databank.get():
                self.status_label.config(text="❌ Please enable 'Use vocabulary databank' option")
                return
            
            # Disable generate button during processing
            self.generate_button.config(state='disabled', text="Generating...")
            self.status_label.config(text="Generating wordtext...")
            
            # Define the generation task
            def generation_task():
                try:
                    print("Starting generation task...")
                    
                    # Run the complete learning session
                    result = self.vocab_app.run_learning_session(
                        random_sample_size=random_size,
                        final_selection_size=urgent_size,
                        language="French",
                        generate_audio=True,
                        import_from_downloads=False
                    )
                    
                    print(f"Generation task completed with result: {len(result.get('selected_words', []))} words")
                    
                    # Process results on main thread
                    self.master.after(0, lambda res=result: self.on_generation_complete(res))
                    
                except Exception as e:
                    error_msg = f"❌ Generation failed: {str(e)}"
                    self.master.after(0, lambda msg=error_msg: self.on_generation_error(msg))
                    
                finally:
                    # Re-enable generate button
                    self.master.after(0, lambda: self.generate_button.config(
                        state='normal', 
                        text="📖\nGenerate\nWordtext"
                    ))
            
            # Run generation in a separate thread
            generation_thread = threading.Thread(target=generation_task, daemon=True)
            generation_thread.start()
            
        except Exception as e:
            self.status_label.config(text=f"❌ Error starting generation: {str(e)}")
            self.generate_button.config(state='normal', text="📖\nGenerate\nWordtext")

    def load_last_text_mode(self):
        """Load last generated text mode for offline use"""
        try:
            self.status_label.config(text="📂 Loading last generated text...")
            
            # Disable generate button during processing
            self.generate_button.config(state='disabled', text="Loading...")
            
            def load_task():
                try:
                    print("Loading last session...")
                    
                    # Try to pull from Git first (optional, may fail if offline)
                    if hasattr(self.vocab_app, 'git_manager'):
                        print("🔄 Attempting Git pull...")
                        success = self.vocab_app.git_manager.pull_latest()
                        if success:
                            print("✅ Successfully synced with Git repository")
                        else:
                            print("⚠️ Git pull failed (proceeding with local files)")
                    
                    # Load last session data
                    result = self.vocab_app.load_last_session(
                        progress_callback=lambda msg: self.master.after(0, 
                            lambda m=msg: self.status_label.config(text=m))
                    )
                    
                    print(f"Load task completed with story length: {len(result.get('story', ''))}")
                    
                    # Process results on main thread
                    self.master.after(0, lambda res=result: self.on_load_complete(res))
                    
                except Exception as e:
                    error_msg = f"❌ Load failed: {str(e)}"
                    self.master.after(0, lambda msg=error_msg: self.on_load_error(msg))
                    
                finally:
                    # Re-enable generate button (with error handling)
                    def safe_button_reset():
                        try:
                            if hasattr(self, 'generate_button') and self.generate_button.winfo_exists():
                                self.generate_button.config(state='normal', text="📖\nGenerate\nWordtext")
                        except Exception:
                            pass  # Button might be destroyed if UI switched
                    self.master.after(0, safe_button_reset)
            
            # Run loading in a separate thread
            load_thread = threading.Thread(target=load_task, daemon=True)
            load_thread.start()
            
        except Exception as e:
            self.status_label.config(text=f"❌ Error starting load: {str(e)}")
            self.generate_button.config(state='normal', text="📖\nGenerate\nWordtext")

    def on_generation_complete(self, result):
        """Handle successful generation completion"""
        try:
            selected_words = result.get('selected_words', [])
            story = result.get('story', '')
            audio_path = result.get('audio_path', '')
            
            if selected_words:
                if self.use_test_mode.get():
                    self.status_label.config(text=f"🧪 Test mode complete! {len(selected_words)} words loaded")
                else:
                    self.status_label.config(text=f"✅ Generation complete! {len(selected_words)} words selected")
                
                # Start review interface
                self.show_review_interface(selected_words, story, audio_path)
            else:
                self.status_label.config(text="❌ No words were selected for the story")
            
        except Exception as e:
            self.on_generation_error(f"Error processing results: {str(e)}")
    
    def on_generation_error(self, error_message):
        """Handle generation errors"""
        self.status_label.config(text=error_message)
        self.generate_button.config(state='normal', text="📖\nGenerate\nWordtext")

    def on_load_complete(self, result):
        """Handle successful load completion"""
        try:
            story = result.get('story', '')
            audio_path = result.get('audio_path', '')
            
            if story:
                self.status_label.config(text="✅ Last text loaded successfully (offline mode)")
                
                # Create empty word data for offline mode (no specific vocabulary tracking)
                offline_words = [
                    {'word': f'Word{i+1}', 'translation': f'Translation{i+1}', 'pronunciation': ''}
                    for i in range(10)  # Create 10 placeholder words for review
                ]
                
                # Start review interface with loaded content
                self.show_review_interface(offline_words, story, audio_path)
            else:
                self.status_label.config(text="❌ No saved text found. Generate new content first.")
            
        except Exception as e:
            self.on_load_error(f"Error processing loaded content: {str(e)}")
    
    def on_load_error(self, error_message):
        """Handle load errors"""
        self.status_label.config(text=error_message)
        self.generate_button.config(state='normal', text="📖\nGenerate\nWordtext")

    def run_test_mode(self):
        """Run test mode with preset data for development"""
        try:
            self.status_label.config(text="🧪 Running in test mode...")
            
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

            # Create a dummy audio path (you could put a real test audio file here)
            # If you want to test audio controls, put a test.mp3 file in the data folder
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
            test_audio_file = os.path.join(data_dir, 'test.mp3')
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
            self.status_label.config(text=f"❌ Test mode failed: {str(e)}")
            self.generate_button.config(state='normal', text="📖\nGenerate\nWordtext")
    
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
    """Modern vocabulary review interface with professional audio controls"""
    
    def __init__(self, master, review_data, generated_text, audio_path, back_callback=None, vocab_app=None):
        self.master = master
        self.review_data = review_data
        self.generated_text = generated_text
        self.audio_path = audio_path
        self.back_callback = back_callback
        self.vocab_app = vocab_app
        
        # Review state
        self.marked_difficult = set()
        self.reviewed_words = set()
        
        # Audio related variables
        self.vlc_available = VLC_AVAILABLE
        self.audio_speed = 0.9
        self.audio_length = 1
        self._slider_dragging = False
        
        # Sync with Git at the start of review session
        if self.vocab_app and hasattr(self.vocab_app, 'git_manager'):
            print("🔄 Syncing with Git repository...")
            success = self.vocab_app.git_manager.pull_latest()
            if success:
                print("✅ Successfully synced with Git repository")
                # Refresh database after Git pull
                if hasattr(self.vocab_app, 'database_manager'):
                    self.vocab_app.database_manager._refresh_word_stats()
            else:
                print("⚠️ Failed to sync with Git (using local data)")
        
        # Initialize VLC if available
        if self.vlc_available and self.audio_path and os.path.exists(self.audio_path):
            try:
                self.vlc_instance = vlc.Instance()
                self.vlc_player = self.vlc_instance.media_player_new()
                media = self.vlc_instance.media_new(self.audio_path)
                self.vlc_player.set_media(media)
            except Exception as e:
                print(f"VLC initialization failed: {e}")
                self.vlc_available = False
        
        # Setup window for review
        self.master.title("📚 InfiniLing - Vocabulary Review")
        self.master.geometry("1200x800")
        self.master.configure(bg='#ffffff')
        self.master.minsize(1000, 600)
        
        # Setup modern styles
        self.setup_modern_styles()
        
        # Setup layout
        self.setup_layout()
        self.setup_start_view()

    def setup_modern_styles(self):
        """Configure modern styling"""
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
        
        # New tile styles for elegant layout
        style.configure('TileContainer.TFrame',
                       background='#f8f9fa',
                       relief='solid',
                       borderwidth=1)
        
        style.configure('SelectedTileContainer.TFrame',
                       background='#fff3cd',
                       relief='solid',
                       borderwidth=2)
        
        style.configure('TileWord.TLabel',
                       font=('Segoe UI', 13, 'bold'),
                       background='#f8f9fa',
                       foreground='#212529')
        
        style.configure('TileTranslation.TLabel',
                       font=('Segoe UI', 11),
                       background='#f8f9fa',
                       foreground='#0078d4')
        
        style.configure('TilePronunciation.TLabel',
                       font=('Segoe UI', 9, 'italic'),
                       background='#f8f9fa',
                       foreground='#6c757d')
        
        style.configure('TileOverlay.TButton',
                       relief='flat',
                       borderwidth=0,
                       background='#f8f9fa')
        
        style.configure('SelectedTileOverlay.TButton',
                       relief='flat',
                       borderwidth=0,
                       background='#fff3cd')
        
        style.map('TileOverlay.TButton',
                 background=[('active', '#e9ecef')])
        
        style.map('SelectedTileOverlay.TButton',
                 background=[('active', '#ffeaa7')])
        
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

        # Selected tile label styles
        style.configure('SelectedTileWord.TLabel',
                       font=('Segoe UI', 13, 'bold'),
                       background='#fff3cd',
                       foreground='#856404')
        
        style.configure('SelectedTileTranslation.TLabel',
                       font=('Segoe UI', 11),
                       background='#fff3cd',
                       foreground='#0078d4')
        
        style.configure('SelectedTilePronunciation.TLabel',
                       font=('Segoe UI', 9, 'italic'),
                       background='#fff3cd',
                       foreground='#6c757d')
        
        # Warning button style for exit without saving
        style.configure('Warning.TButton', 
                       font=('Segoe UI', 11),
                       padding=(20, 12),
                       relief='flat',
                       borderwidth=0,
                       background='#dc3545',
                       foreground='white')
        
        style.map('Warning.TButton',
                 background=[('active', '#c82333'),
                           ('pressed', '#bd2130')])
        
    def setup_layout(self):
        """Setup the main layout with audio controls at bottom"""
        # Clear existing widgets
        for widget in self.master.winfo_children():
            widget.destroy()
        
        # Audio controls at bottom first (so they don't get pushed out)
        self.audio_controls_frame = ttk.Frame(self.master)
        self.audio_controls_frame.pack(side='bottom', fill='x', padx=10, pady=10)
        
        # Content frame fills the rest
        self.content_frame = ttk.Frame(self.master)
        self.content_frame.pack(side='top', fill='both', expand=True)
        
        # Setup audio controls
        self.setup_audio_controls()

    def setup_start_view(self):
        """Setup the initial reading/text view"""
        self.clear_content_frame()
        
        # Show audio controls in reading view
        self.audio_controls_frame.pack(side='bottom', fill='x', padx=10, pady=10)
    
        # Main container with padding
        main_frame = ttk.Frame(self.content_frame, style='Card.TFrame', padding="40")
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Header row: Title (left), Action button (right)
        header_frame = ttk.Frame(main_frame, style='Card.TFrame')
        header_frame.pack(fill='x', pady=(0, 20))
        
        title = ttk.Label(header_frame, text="📖 Reading Practice", style='Heading.TLabel')
        title.pack(side='left')
        
        btn = ttk.Button(header_frame, text="Pass on to Vocabulary", 
                        command=self.setup_tile_view, style='Accent.TButton')
        btn.pack(side='right', padx=(10, 0))
        
        if self.generated_text:
            # Text section with modern styling
            text_frame = ttk.Frame(main_frame, style='Card.TFrame')
            text_frame.pack(fill='both', expand=True)
            
            # Scrollable text widget
            text_container = ttk.Frame(text_frame)
            text_container.pack(fill='both', expand=True)
            
            text_widget = Text(text_container, 
                              wrap='word', 
                              font=('Segoe UI', 12), 
                              bg='#fafafa', 
                              fg='#212529',
                              relief='flat', 
                              borderwidth=0,
                              selectbackground='#0078d4',
                              selectforeground='white',
                              padx=20, pady=15)
            
            scrollbar = ttk.Scrollbar(text_container, orient='vertical', command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
            
            text_widget.insert('1.0', self.generated_text)
            text_widget.config(state='disabled')
        
        # Action button
        btn = ttk.Button(main_frame, text="Review Vocabulary", 
                        command=self.setup_tile_view, style='Accent.TButton')
        btn.pack(side='bottom', pady=20)

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

    def setup_tile_view(self):
        """Setup the vocabulary selection view"""
        self.clear_content_frame()
        
        # Hide audio controls in tile review
        self.audio_controls_frame.pack_forget()
    
        # Debug: Print what data we have
        print(f"DEBUG: Setting up tiles with {len(self.review_data)} words")
        for i, word_data in enumerate(self.review_data[:5]):  # Show first 5
            print(f"  Word {i+1}: {word_data}")
        
        # Main container
        main_frame = ttk.Frame(self.content_frame, style='Card.TFrame', padding="40")
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Header with title and continue button
        header_frame = ttk.Frame(main_frame, style='Card.TFrame')
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Title section (left side)
        title_frame = ttk.Frame(header_frame, style='Card.TFrame')
        title_frame.pack(side='left', fill='x', expand=True)
        
        title = ttk.Label(title_frame, text="🎯 Select words you want to review again", style='Heading.TLabel')
        title.pack(anchor='w')
        
        subtitle = ttk.Label(title_frame, text="Click on vocabulary items that need more practice", style='Subheading.TLabel')
        subtitle.pack(anchor='w', pady=(5, 0))
        
        # Continue button (right side)
        continue_btn = ttk.Button(header_frame, text="Continue →", 
                                 command=self.finish_review, style='Accent.TButton')
        continue_btn.pack(side='right', padx=(20, 0))
        
        # Create a visible container for the tiles with background color
        tiles_container = ttk.Frame(main_frame)
        tiles_container.pack(expand=True, fill='both', pady=(10, 0))
        tiles_container.configure(style='Card.TFrame')
        
        # Tiles grid (4 columns x 5 rows, max 20 items)
        grid_frame = ttk.Frame(tiles_container)
        grid_frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.tiles = []
        cols = 4
        rows = 5
        max_tiles = cols * rows
        vocab_to_show = self.review_data[:max_tiles]
        
        print(f"DEBUG: Creating {len(vocab_to_show)} tiles in {rows}x{cols} grid")
        
        for i, word_data in enumerate(vocab_to_show):
            word, translation, pronunciation = self.extract_word_data(word_data, i)
            row = i // cols
            col = i % cols
            
            print(f"DEBUG: Creating tile {i+1} at grid ({row},{col}): {word} -> {translation}")
            
            # Create tile with visible border and background
            tile_frame = ttk.Frame(grid_frame)
            tile_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew', ipadx=5, ipady=5)
            tile_frame.configure(relief='solid', borderwidth=2)
            
            # Add minimum size to ensure visibility
            tile_frame.grid_propagate(False)
            tile_frame.configure(width=200, height=100)
            
            # Create inner content frame
            content_frame = Frame(tile_frame, bg='#f9f9f9', relief='flat')
            content_frame.pack(fill='both', expand=True, padx=5, pady=5)
            
            # Word display
            word_label = Label(content_frame, text=word, 
                              font=('Segoe UI', 13, 'bold'),
                              bg='#f9f9f9', fg='#212529')
            word_label.pack(pady=(10, 2))
            
            # Translation
            trans_label = Label(content_frame, text=f"→ {translation}", 
                               font=('Segoe UI', 11),
                               bg='#f9f9f9', fg='#0078d4')
            trans_label.pack(pady=(2, 5))
            
            # Pronunciation if available
            if pronunciation:
                pron_label = Label(content_frame, text=f"[{pronunciation}]", 
                                  font=('Segoe UI', 9, 'italic'),
                                  bg='#f9f9f9', fg='#6c757d')
                pron_label.pack(pady=(0, 10))
            
            # Click handler for the entire tile
            def make_click_handler(w):
                return lambda event: self.toggle_tile(w)
            
            click_handler = make_click_handler(word)
            content_frame.bind('<Button-1>', click_handler)
            word_label.bind('<Button-1>', click_handler)
            trans_label.bind('<Button-1>', click_handler)
            
            self.tiles.append((tile_frame, content_frame, word))
        
        # Configure grid weights to ensure tiles are visible
        for col in range(cols):
            grid_frame.grid_columnconfigure(col, weight=1, minsize=220)
        for row in range(rows):
            grid_frame.grid_rowconfigure(row, weight=1, minsize=140)
    
    def toggle_tile(self, word):
        """Toggle word selection in tile view"""
        print(f"DEBUG: Toggling tile for word: {word}")
    
        if word in self.marked_difficult:
            self.marked_difficult.remove(word)
            # Find and update the tile style to normal
            for tile_frame, content_frame, tile_word in self.tiles:
                if tile_word == word:
                    content_frame.configure(bg='#f9f9f9')
                    for child in content_frame.winfo_children():
                        if isinstance(child, Label):
                            child.configure(bg='#f9f9f9')
                    print(f"DEBUG: Unmarked {word} as difficult")
                    break
        else:
            self.marked_difficult.add(word)
            # Find and update the tile style to selected
            for tile_frame, content_frame, tile_word in self.tiles:
                if tile_word == word:
                    content_frame.configure(bg='#fff3cd')
                    for child in content_frame.winfo_children():
                        if isinstance(child, Label):
                            child.configure(bg='#fff3cd')
                    print(f"DEBUG: Marked {word} as difficult")
                    break
    
        print(f"DEBUG: Currently marked difficult: {list(self.marked_difficult)}")

    def setup_audio_controls(self):
        """Setup professional audio controls"""
        for widget in self.audio_controls_frame.winfo_children():
            widget.destroy()

        # Always show audio controls area
        audio_frame = ttk.LabelFrame(self.audio_controls_frame, text="🎵 Audio Controls", padding="15")
        audio_frame.pack(fill='x', padx=10, pady=5)

        if self.vlc_available and self.audio_path and os.path.exists(self.audio_path):
            # Top row - Main playback controls
            controls_row = ttk.Frame(audio_frame)
            controls_row.pack(fill='x', pady=(0, 10))
            
            # Playback controls (centered)
            playback_frame = ttk.Frame(controls_row)
            playback_frame.pack(expand=True)
            
            self.play_btn = ttk.Button(playback_frame, text="▶ Play", 
                                      command=self.play_audio, style='Accent.TButton')
            self.play_btn.pack(side='left', padx=5)
            
            self.pause_btn = ttk.Button(playback_frame, text="⏸ Pause", 
                                       command=self.pause_audio, style='Modern.TButton')
            self.pause_btn.pack(side='left', padx=5)
            
            self.stop_btn = ttk.Button(playback_frame, text="⏹ Stop", 
                                      command=self.stop_audio, style='Modern.TButton')
            self.stop_btn.pack(side='left', padx=5)
            
            # Separator
            ttk.Separator(playback_frame, orient='vertical').pack(side='left', fill='y', padx=15)
            
            # Jump controls
            self.jump_back_btn = ttk.Button(playback_frame, text="⏪ -4s", 
                                           command=lambda: self.jump_audio(-4), style='Modern.TButton')
            self.jump_back_btn.pack(side='left', padx=5)
            
            self.jump_forward_btn = ttk.Button(playback_frame, text="+4s ⏩", 
                                              command=lambda: self.jump_audio(4), style='Modern.TButton')
            self.jump_forward_btn.pack(side='left', padx=5)
            
            # Separator
            ttk.Separator(playback_frame, orient='vertical').pack(side='left', fill='y', padx=15)
            
            # Speed controls
            self.slower_btn = ttk.Button(playback_frame, text="🐌 -5%", 
                                        command=lambda: self.change_speed(-0.05), style='Modern.TButton')
            self.slower_btn.pack(side='left', padx=2)
            
            self.faster_btn = ttk.Button(playback_frame, text="🐇 +5%", 
                                        command=lambda: self.change_speed(0.05), style='Modern.TButton')
            self.faster_btn.pack(side='left', padx=2)
            
            # Bottom row - Progress bar
            progress_row = ttk.Frame(audio_frame)
            progress_row.pack(fill='x')
            
            self.audio_progress = DoubleVar()
            self.audio_progress_bar = ttk.Scale(progress_row, 
                                              variable=self.audio_progress, 
                                              length=500, 
                                              from_=0, 
                                              to=100, 
                                              orient='horizontal', 
                                              command=self.slider_seek_update)
            self.audio_progress_bar.pack(side='left', fill='x', expand=True, padx=(0, 10))
            self.audio_progress_bar.bind('<ButtonRelease-1>', self.slider_seek_commit)
            
            # Initialize and start progress updates
            self.update_audio_progress()
        else:
            # Show disabled controls if no audio available
            controls_row = ttk.Frame(audio_frame)
            controls_row.pack(fill='x', pady=(0, 10))
            
            playback_frame = ttk.Frame(controls_row)
            playback_frame.pack(expand=True)
            
            # Disabled buttons
            ttk.Button(playback_frame, text="▶ Play", state='disabled', style='Accent.TButton').pack(side='left', padx=5)
            ttk.Button(playback_frame, text="⏸ Pause", state='disabled', style='Modern.TButton').pack(side='left', padx=5)
            ttk.Button(playback_frame, text="⏹ Stop", state='disabled', style='Modern.TButton').pack(side='left', padx=5)
            
            ttk.Separator(playback_frame, orient='vertical').pack(side='left', fill='y', padx=15)
            
            ttk.Button(playback_frame, text="⏪ -4s", state='disabled', style='Modern.TButton').pack(side='left', padx=5)
            ttk.Button(playback_frame, text="+4s ⏩", state='disabled', style='Modern.TButton').pack(side='left', padx=5)
            
            ttk.Separator(playback_frame, orient='vertical').pack(side='left', fill='y', padx=15)
            
            ttk.Button(playback_frame, text="🐌 -5%", state='disabled', style='Modern.TButton').pack(side='left', padx=2)
            ttk.Button(playback_frame, text="🐇 +5%", state='disabled', style='Modern.TButton').pack(side='left', padx=2)
            
            # Message
            if not self.audio_path:
                message = "No audio file available"
            elif not VLC_AVAILABLE:
                message = "VLC not available - install VLC media player for audio support"
            else:
                message = "Audio file not found"
            
            ttk.Label(audio_frame, text=message, style='Body.TLabel').pack(pady=10)

    # Audio control methods
    def play_audio(self):
        if hasattr(self, 'vlc_player'):
            self.vlc_player.play()
            self.vlc_player.set_rate(self.audio_speed)
            self.update_audio_progress()

    def pause_audio(self):
        if hasattr(self, 'vlc_player'):
            self.vlc_player.pause()

    def stop_audio(self):
        if hasattr(self, 'vlc_player'):
            self.vlc_player.stop()
            if hasattr(self, 'audio_progress'):
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
            position = float(self.audio_progress.get()) / 100.0
            self.vlc_player.set_position(position)
        self._slider_dragging = False

    def jump_audio(self, seconds):
        if hasattr(self, 'vlc_player') and self.audio_length > 0:
            current_time = self.vlc_player.get_time()
            new_time = max(0, min(self.audio_length * 1000, current_time + seconds * 1000))
            self.vlc_player.set_time(int(new_time))

    def update_audio_progress(self):
        if hasattr(self, 'vlc_player') and hasattr(self, 'audio_progress') and not self._slider_dragging:
            if self.vlc_player.is_playing():
                length = self.vlc_player.get_length()
                if length > 0:
                    self.audio_length = length / 1000  # Convert to seconds
                    current_time = self.vlc_player.get_time()
                    if current_time >= 0:
                        progress = (current_time / length) * 100
                        self.audio_progress.set(progress)
        
        if hasattr(self, 'master'):
            self.master.after(200, self.update_audio_progress)

    def clear_content_frame(self):
        """Clear all widgets from content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def finish_review(self):
        """Finish the review session and show statistics"""
        try:
            # Only show statistics, do NOT save any progress yet!
            print(f"� Review complete: {len(self.marked_difficult)} difficult, {len(self.review_data) - len(self.marked_difficult)} easy words")
            print("📋 Showing statistics - choose your save option...")
            # Show statistics page (saving will happen when user chooses)
            self.setup_statistics_view()
        except Exception as e:
            print(f"Error finishing review: {e}")
            # Still try to show statistics
            self.setup_statistics_view()

    def save_review_progress(self):
        """Save the review progress to database and Git"""
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
                # Commit changes to Git after saving word progress
                if hasattr(self.vocab_app, 'git_manager'):
                    print("🔄 Committing changes to Git...")
                    commit_message = f"Update vocabulary progress: {len(self.marked_difficult)} difficult, {len(self.review_data) - len(self.marked_difficult)} easy words"
                    success = self.vocab_app.git_manager.push_changes(commit_message)
                    if success:
                        print("✅ Successfully saved progress and committed to Git")
                    else:
                        print("⚠️ Failed to commit to Git (changes saved locally)")
                else:
                    print("⚠️ Git manager not available - changes saved locally only")
            else:
                print("⚠️ Database manager not available")
        except Exception as e:
            print(f"Error saving review progress: {e}")
            raise

    def setup_statistics_view(self):
        """Setup the statistics view showing before/after urgency comparison"""
        self.clear_content_frame()
        
        # Main container
        main_frame = ttk.Frame(self.content_frame, style='Card.TFrame', padding="30")
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Header with navigation buttons
        header_frame = ttk.Frame(main_frame, style='Card.TFrame')
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Navigation buttons (upper left)
        nav_frame = ttk.Frame(header_frame, style='Card.TFrame')
        nav_frame.pack(side='left')
        
        save_exit_btn = ttk.Button(nav_frame, text="💾 Save & Exit", 
                                  command=self.save_and_exit, style='Accent.TButton')
        save_exit_btn.pack(side='left', padx=(0, 8))
        
        save_menu_btn = ttk.Button(nav_frame, text="💾 Save & Menu", 
                                  command=self.save_and_menu, style='Modern.TButton')
        save_menu_btn.pack(side='left', padx=(0, 8))
        
        exit_no_save_btn = ttk.Button(nav_frame, text="🚪 Exit (No Save)", 
                                     command=self.exit_without_saving, style='Warning.TButton')
        exit_no_save_btn.pack(side='left')
        
        # Title (center)
        title_frame = ttk.Frame(header_frame, style='Card.TFrame')
        title_frame.pack(side='right', fill='x', expand=True)
        
        title = ttk.Label(title_frame, text="📊 Review Statistics", style='Heading.TLabel')
        title.pack()
        
        # Statistics summary
        summary_frame = ttk.Frame(main_frame, style='Card.TFrame')
        summary_frame.pack(fill='x', pady=(0, 20))
        
        total_words = len(self.review_data)
        difficult_words = len(self.marked_difficult)
        easy_words = total_words - difficult_words
        
        summary_text = f"📖 Total words reviewed: {total_words}   |   😰 Marked difficult: {difficult_words}   |   😊 Marked easy: {easy_words}"
        summary_label = ttk.Label(summary_frame, text=summary_text, style='Subheading.TLabel')
        summary_label.pack()
        
        # Main visualization area
        viz_frame = ttk.Frame(main_frame, style='Card.TFrame')
        viz_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        # Create the urgency comparison chart
        self.create_urgency_comparison_chart(viz_frame)

    def create_urgency_comparison_chart(self, parent_frame):
        """Create an elegant urgency comparison visualization"""
        try:
            # Import matplotlib for visualization
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
            import numpy as np
            
            # Prepare data for all words from JSON
            word_data = []
            
            if self.vocab_app and hasattr(self.vocab_app, 'database_manager'):
                # Get all words from database
                all_words = self.vocab_app.database_manager.word_stats
                
                # Calculate urgency for each word
                for word_key, stats in all_words.items():
                    if '|' in word_key:
                        word, translation = word_key.split('|', 1)
                        
                        # Calculate before urgency using the vocabulary selector from vocab_app
                        before_urgency = self.vocab_app.vocabulary_selector.calculate_word_priority(word, translation)
                        
                        # Use helper to check if word was reviewed and if marked difficult
                        reviewed = False
                        difficult = False
                        for idx, wd in enumerate(self.review_data):
                            w, t, _ = self.extract_word_data(wd, idx)
                            if w == word:
                                reviewed = True
                                if word in self.marked_difficult:
                                    difficult = True
                                break
                        if difficult:
                            after_urgency = min(100, before_urgency + 15)
                        elif reviewed:
                            after_urgency = max(0, before_urgency - 10)
                        else:
                            after_urgency = before_urgency
                        
                        word_data.append({
                            'word': word,
                            'translation': translation,
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
            
            # Sort by before urgency (highest first)
            word_data.sort(key=lambda x: x['before'], reverse=True)
            
            # Limit to top 50 words for better visualization
            word_data = word_data[:50]
            
            # Create matplotlib figure
            fig = Figure(figsize=(14, 8), dpi=100, facecolor='white')
            ax = fig.add_subplot(111)
            
            # Prepare data for plotting
            x_pos = np.arange(len(word_data))
            before_urgencies = [wd['before'] for wd in word_data]
            after_urgencies = [wd['after'] for wd in word_data]
            
            # Create elegant line chart
            ax.plot(x_pos, before_urgencies, 'o-', color='#dc3545', linewidth=2, 
                   markersize=6, label='Before Review', alpha=0.8)
            ax.plot(x_pos, after_urgencies, 'o-', color='#28a745', linewidth=2, 
                   markersize=6, label='After Review', alpha=0.8)
            
            # Highlight reviewed words
            for i, wd in enumerate(word_data):
                if wd['reviewed']:
                    if wd['difficult']:
                        # Difficult words in red
                        ax.scatter(i, wd['after'], color='#dc3545', s=100, marker='x', 
                                 linewidth=3, label='Marked Difficult' if i == 0 else "")
                    else:
                        # Easy words in green
                        ax.scatter(i, wd['after'], color='#28a745', s=80, marker='o', 
                                 alpha=0.7, label='Marked Easy' if i == 0 else "")
            
            # Styling
            ax.set_xlabel('Words (sorted by initial urgency)', fontsize=12, fontweight='bold')
            ax.set_ylabel('Urgency Score', fontsize=12, fontweight='bold')
            ax.set_title('Word Learning Progress: Before vs After Review', 
                        fontsize=16, fontweight='bold', pad=20)
            
            # Set y-axis limits
            ax.set_ylim(0, 105)
            
            # Add grid for better readability
            ax.grid(True, alpha=0.3, linestyle='--')
            
            # Add legend
            ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
            
            # Remove x-axis labels for cleaner look
            ax.set_xticks([])
            
            # Add some statistics text
            total_reviewed = sum(1 for wd in word_data if wd['reviewed'])
            avg_before = np.mean(before_urgencies) if before_urgencies else 0
            avg_after = np.mean(after_urgencies) if after_urgencies else 0
            
            stats_text = f"Total words: {len(word_data)} | Reviewed: {total_reviewed} | Avg urgency: {avg_before:.1f} -> {avg_after:.1f}"
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, parent_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
            
        except ImportError:
            # Fallback if matplotlib not available
            fallback_label = ttk.Label(parent_frame, 
                                 text="Install matplotlib for advanced visualizations\n\n" +
                                      f"Words reviewed: {len(self.review_data)}\n" +
                                      f"Marked difficult: {len(self.marked_difficult)}\n" +
                                      f"Marked easy: {len(self.review_data) - len(self.marked_difficult)}", 
                                 style='Body.TLabel', justify='center')
            fallback_label.pack(expand=True)
        except Exception as e:
            # Error fallback
            error_label = ttk.Label(parent_frame, 
                                  text=f"Error creating visualization: {str(e)}", 
                                  style='Body.TLabel')
            error_label.pack(expand=True)

    def save_and_exit(self):
        """Save progress and exit the application"""
        try:
            # Actually save the progress now
            self.save_review_progress()
            print("👋 Exiting application...")
            if hasattr(self, 'master'):
                self.master.quit()
                self.master.destroy()
        except Exception as e:
            print(f"Error saving and exiting: {e}")
            # Still try to exit
            if hasattr(self, 'master'):
                self.master.quit()

    def save_and_menu(self):
        """Save progress and return to main menu"""
        try:
            # Actually save the progress now
            self.save_review_progress()
            print("🏠 Returning to main menu...")
            if self.back_callback:
                self.back_callback()
        except Exception as e:
            print(f"Error saving and returning to menu: {e}")
            # Still try to go back
            if self.back_callback:
                self.back_callback()

    def exit_without_saving(self):
        """Exit without saving progress (undo the review changes)"""
        try:
            print("🚪 Exiting without saving progress...")
            
            # Show confirmation dialog
            import tkinter.messagebox as msgbox
            result = msgbox.askyesno(
                "Exit Without Saving", 
                "Are you sure you want to exit without saving your review progress?\n\n"
                "This will undo all the words you marked as difficult or easy in this session.",
                icon='warning'
            )
            
            if result:
                # Undo the database changes by removing the last occurrences
                if self.vocab_app and hasattr(self.vocab_app, 'database_manager'):
                    # We can't easily undo specific occurrences, so we'll just go back without saving
                    # In a real implementation, you might want to track changes and revert them
                    print("⚠️ Review progress discarded")
                
                # Return to main menu without saving
                if self.back_callback:
                    self.back_callback()
            # If user says no, just stay on the statistics page
                
        except Exception as e:
            print(f"Error exiting without saving: {e}")
            # Still try to go back if there's an error
            if self.back_callback:
                self.back_callback()

    def back_to_menu(self):
        """Go back to main menu (deprecated - use save_and_menu instead)"""
        self.save_and_menu()

