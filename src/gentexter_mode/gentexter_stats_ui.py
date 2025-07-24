from tkinter import Frame, Label, Canvas, messagebox
from ..shared.styles import Colors, Fonts, Spacing, center_top_window
from ..shared.style_utils import CommonPatterns
from datetime import datetime, timedelta
import math


class GentexterStats:
    def __init__(self, master, review_data, word_scores, vocab_app=None, config=None):
        """
        Initialize GentexterStats with dependency injection.
        
        Args:
            master: Tkinter root window
            review_data: List of reviewed words data
            word_scores: Dict mapping word -> score (0-5)
            vocab_app: VocabularyApp service instance
            config: ConfigManager instance
        """
        self.master = master
        self.config = config
        self.review_data = review_data
        self.word_scores = word_scores  # word -> score (0-5)
        self.vocab_app = vocab_app
        
        self.set_window_size()
        self.setup_ui()

    def set_window_size(self):
        """Set window size for gentexter interface using config"""
        window_width, window_height = self.config.get_window_size('gentexter')
        center_top_window(self.master, width=window_width, height=window_height)

    def setup_ui(self):
        """Setup the complete stats UI layout"""
        # Clear existing widgets
        for widget in self.master.winfo_children():
            widget.destroy()
            
        # Main container
        main_frame = Frame(self.master, bg=Colors.LIGHT_GRAY)
        main_frame.pack(expand=True, fill='both', padx=Spacing.LG, pady=Spacing.LG)

        # Header with navigation
        header_frame = CommonPatterns.create_header_with_navigation(
            main_frame, 
            "📊 Test Results", 
            back_command=self.return_to_menu,
            forward_command=self.save_test,
            forward_text="Save Test",
            backward_text="Discard Test"
        )
        
        # Create performance graph
        self.create_performance_graph(main_frame)

    def create_performance_graph(self, parent):
        """Create the performance visualization graph"""
        # Graph container
        graph_frame = Frame(parent, bg=Colors.WHITE, relief='raised', bd=1)
        graph_frame.pack(expand=True, fill='both', padx=Spacing.SM, pady=Spacing.SM)
        
        # Title
        title_label = Label(graph_frame, text="📈 Vocabulary Performance Overview", 
                           font=(Fonts.BODY[0], 14, "bold"), 
                           bg=Colors.WHITE, fg=Colors.DARK_GRAY)
        title_label.pack(pady=(Spacing.LG, Spacing.SM))
        
        # Subtitle
        subtitle_label = Label(graph_frame, 
                              text="The higher the score, the better!", 
                              font=Fonts.BODY, bg=Colors.WHITE, fg=Colors.MEDIUM_GRAY)
        subtitle_label.pack(pady=(0, Spacing.MD))
        
        # Canvas for graph
        self.canvas = Canvas(graph_frame, bg=Colors.WHITE, height=350, 
                           borderwidth=0, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, padx=Spacing.LG, pady=Spacing.MD)
        
        # Draw the graph
        self.draw_performance_graph()

    def get_word_performance_data(self):
        """Get performance data for all words in database"""
        try:
            # Get all vocabulary words from database
            all_words = self.vocab_app.database_manager.get_all_words()
            
            performance_data = []
            for word in all_words:
                # Use the existing get_due_days method for consistent calculation
                days_until_review = self.vocab_app.database_manager.get_due_days(word.id) if not None else 100
                
                # Check if this word was in the current review session
                is_reviewed = any(word.word == reviewed_word.get('word') for reviewed_word in self.review_data)

                performance_data.append({'days_until_review': days_until_review,'is_reviewed': is_reviewed})

            print(f" sample performance data: {performance_data[:5]}")  # Debug output
            # Sort by performance (worse performance = more days = left side of graph)
            performance_data.sort(key=lambda x: x['days_until_review'], reverse=True)
            return performance_data
            
        except Exception as e:
            print(f"Error getting performance data: {e}")
            return []

    def draw_performance_graph(self):
        """Draw the performance graph on canvas"""
        try:
            data = self.get_word_performance_data()
            if not data:
                return self._show_message("No vocabulary data available")
            if len(data) <= 3:
                return self._show_message("Not enough words for performance graph")

            # Setup canvas dimensions
            self.master.update_idletasks()
            canvas_width = self.canvas.winfo_width() or 460  # Fallback width
            canvas_height = self.canvas.winfo_height() or 350  # Fallback height
            
            # Graph layout
            margins = {'left': 60, 'right': 30, 'top': 30, 'bottom': 50}
            graph_width = canvas_width - margins['left'] - margins['right']
            graph_height = canvas_height - margins['top'] - margins['bottom']
            max_days = max(item['days_until_review'] for item in data)
            x_step = graph_width / max(len(data) - 1, 1)
            
            # Draw graph components
            self._draw_axis_labels(margins, graph_width, graph_height, max_days, canvas_height)
            points = self._plot_data_points(data, margins, graph_width, graph_height, max_days, x_step)
            self.canvas.create_line(points, fill=Colors.INFO, width=2, smooth=True)
            self._draw_legend(margins, graph_width)
                
        except Exception as e:
            print(f"Error drawing graph: {e}")
            self._show_message("Error loading performance data", Colors.ERROR)

    def _show_message(self, message, color=Colors.MEDIUM_GRAY):
        """Show centered message on canvas"""
        self.canvas.create_text(250, 175, text=message, font=Fonts.BODY, fill=color)

    def _draw_x_marker(self, x, y, size=4):
        """Draw an 'X' marker at given coordinates"""
        self.canvas.create_line(x-size, y-size, x+size, y+size, fill=Colors.PRIMARY, width=2)
        self.canvas.create_line(x-size, y+size, x+size, y-size, fill=Colors.PRIMARY, width=2)

    def _draw_axis_labels(self, margins, graph_width, graph_height, max_days, canvas_height):
        """Draw axis labels and titles"""
        # Y-axis labels
        y_labels = [0, max_days//4, max_days//2, 3*max_days//4, max_days]
        for i, label in enumerate(y_labels):
            y = margins['top'] + graph_height - (i * graph_height / 4)
            self.canvas.create_text(margins['left'] - 10, y, text=str(label), 
                                  anchor='e', font=('Arial', 8), fill=Colors.DARK_GRAY)
        
        # Axis titles
        self.canvas.create_text(20, margins['top'] + graph_height//2, text="Days until next review", 
                              anchor='center', font=('Arial', 9, 'bold'), fill=Colors.DARK_GRAY, angle=90)
        self.canvas.create_text(margins['left'] + graph_width//2, canvas_height - 10, text="Words in Database", 
                              anchor='center', font=('Arial', 9, 'bold'), fill=Colors.DARK_GRAY)

    def _plot_data_points(self, data, margins, graph_width, graph_height, max_days, x_step):
        """Plot data points and return coordinates for connecting line"""
        points = []
        for i, item in enumerate(data):
            x = margins['left'] + (i * x_step)
            y = margins['top'] + graph_height - (item['days_until_review'] / max_days * graph_height)
            points.extend([x, y])
            
            if item['is_reviewed']:
                self._draw_x_marker(x, y)
        return points

    def _draw_legend(self, margins, graph_width):
        """Draw graph legend"""
        legend_x = margins['left'] + graph_width - 100
        legend_y = margins['top'] + 10
        
        # 'X' symbol for reviewed words
        self._draw_x_marker(legend_x, legend_y + 2, size=5)
        self.canvas.create_text(legend_x + 10, legend_y + 2, text="Reviewed words", 
                              anchor='w', font=('Arial', 8), fill=Colors.DARK_GRAY)

    def save_test(self):
        """Save test results to database and return to config"""
        try:
            # Save each reviewed word's performance
            for word_data in self.review_data:
                word_text = word_data.get('word')
                if word_text in self.word_scores:
                    score = self.word_scores[word_text]
                    
                    # Find the vocabulary ID for this word
                    vocab_word = self.vocab_app.database_manager.get_id_by_string(word_text)
                    
                    if vocab_word:
                        # Add occurrence record
                        self.vocab_app.database_manager.add_occurrence(
                            vocabulary_id=vocab_word.id,
                            feedback_score=score
                        )
                    else:
                        messagebox.showwarning(
                            "Word Not Found",
                            f"The word '{word_text}' is not in the vocabulary database and was not saved. All upcoming words will be skipped."
                        )
                        break
            
            print(f"✅ Saved test results for {len(self.word_scores)} words")
            
        except Exception as e:
            print(f"❌ Error saving test results: {e}")
        
        # Return to menu
        messagebox.showinfo("Test Saved", "Your test results have been saved successfully.")
        self.return_to_menu()

    def return_to_menu(self):
        """Return from stats interface to config interface"""
        # Clear session data when returning
        if hasattr(self.vocab_app, 'clear_current_session_data'):
            self.vocab_app.clear_current_session_data()
            
        # Destroy stats interface
        for widget in self.master.winfo_children():
            widget.destroy()
        
        # Import and recreate config interface
        from ..shared.menu import MainMenu
        MainMenu(
            master=self.master,
            config=self.config,
            vocab_service=self.vocab_app
        )
