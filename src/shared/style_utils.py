"""
Style utilities for common UI patterns and helper functions
"""
from tkinter import Frame, Label, Button, ttk
from .styles import Colors, Fonts, Spacing

class StyledWidgets:
    """Factory class for creating consistently styled widgets"""
    
    @staticmethod
    def create_header_frame(parent, bg=Colors.HEADER_BG):
        """Create a standard header frame"""
        frame = Frame(parent, bg=bg)
        return frame
    
    @staticmethod
    def create_card_frame(parent, padding=Spacing.LG):
        """Create a card-style frame with consistent styling"""
        frame = ttk.Frame(parent, style='Card.TFrame', padding=padding)
        return frame
    
    @staticmethod
    def create_back_button(parent, command, text="← Back"):
        """Create a standard back button"""
        button = Button(parent, text=text, command=command,
                       font=Fonts.BODY_BOLD, bg='#95a5a6', fg=Colors.WHITE,
                       activebackground='#7f8c8d', relief='flat', bd=0, 
                       pady=Spacing.XS, padx=Spacing.MD)
        return button
    
    @staticmethod
    def create_title_label(parent, text, bg=Colors.CARD_BG):
        """Create a title label with consistent styling"""
        label = Label(parent, text=text, font=Fonts.TITLE,
                     bg=bg, fg=Colors.DARK_GRAY)
        return label
    
    @staticmethod
    def create_heading_label(parent, text, bg=Colors.CARD_BG):
        """Create a heading label with consistent styling"""
        label = Label(parent, text=text, font=Fonts.HEADING,
                     bg=bg, fg=Colors.DARK_GRAY)
        return label
    
    @staticmethod
    def create_status_label(parent, text="Ready", bg=Colors.CARD_BG):
        """Create a status label with consistent styling"""
        label = Label(parent, text=text, font=Fonts.BODY,
                     bg=bg, fg=Colors.MEDIUM_GRAY)
        return label
    
    @staticmethod
    def create_config_section(parent, title, bg=Colors.WHITE):
        """Create a configuration section with title and content frame"""
        # Main section frame
        section_frame = Frame(parent, bg=bg, relief='raised', bd=1)
        
        # Title label
        title_label = Label(section_frame, text=title, 
                           font=Fonts.SUBHEADING,
                           bg=bg, fg=Colors.DARK_GRAY)
        title_label.pack(pady=(Spacing.MD, Spacing.MD))
        
        # Content frame for section content
        content_frame = Frame(section_frame, bg=bg)
        content_frame.pack(fill='x', padx=Spacing.LG, pady=(0, Spacing.MD))
        
        return section_frame, content_frame

class TileStyles:
    """Utilities for vocabulary tile styling"""
    
    @staticmethod
    def get_normal_colors():
        """Get colors for normal (unselected) tile"""
        return {
            'bg': Colors.TILE_NORMAL,
            'word_fg': Colors.DARK_GRAY,
            'translation_fg': Colors.PRIMARY,
            'pronunciation_fg': Colors.MEDIUM_GRAY
        }
    
    @staticmethod
    def get_selected_colors():
        """Get colors for selected tile"""
        return {
            'bg': Colors.TILE_SELECTED,
            'word_fg': Colors.TILE_SELECTED_TEXT,
            'translation_fg': Colors.PRIMARY,
            'pronunciation_fg': Colors.MEDIUM_GRAY
        }
    
    @staticmethod
    def apply_tile_style(content_frame, word_label, trans_label, pron_label=None, selected=False):
        """Apply consistent styling to a vocabulary tile"""
        colors = TileStyles.get_selected_colors() if selected else TileStyles.get_normal_colors()
        
        # Apply background
        content_frame.configure(bg=colors['bg'])
        
        # Apply text colors
        word_label.configure(bg=colors['bg'], fg=colors['word_fg'])
        trans_label.configure(bg=colors['bg'], fg=colors['translation_fg'])
        
        if pron_label:
            pron_label.configure(bg=colors['bg'], fg=colors['pronunciation_fg'])

class LayoutHelpers:
    """Helper functions for common layout patterns"""
    
    @staticmethod
    def create_button_row(parent, buttons_config, style='Modern.TButton'):
        """
        Create a row of buttons with consistent spacing
        buttons_config: list of {'text': str, 'command': callable, 'style': str (optional)}
        """
        button_frame = ttk.Frame(parent, style='Card.TFrame')
        
        for i, config in enumerate(buttons_config):
            btn_style = config.get('style', style)
            btn = ttk.Button(button_frame, 
                           text=config['text'], 
                           command=config['command'],
                           style=btn_style)
            btn.pack(side='left', padx=(0, Spacing.SM) if i < len(buttons_config) - 1 else 0)
        
        return button_frame
    
    @staticmethod
    def create_two_column_layout(parent, left_weight=1, right_weight=0):
        """Create a two-column layout with specified weights"""
        # Main container
        container = ttk.Frame(parent, style='Card.TFrame')
        
        # Left column
        left_frame = ttk.Frame(container, style='Card.TFrame')
        left_frame.pack(side='left', fill='both', expand=bool(left_weight))
        
        # Right column
        right_frame = ttk.Frame(container, style='Card.TFrame')
        right_frame.pack(side='right', fill='y' if not right_weight else 'both', 
                        expand=bool(right_weight))
        
        return container, left_frame, right_frame
    
    @staticmethod
    def create_grid_container(parent, cols=4, rows=5, min_col_width=220, min_row_height=140):
        """Create a grid container with proper weight configuration"""
        grid_frame = ttk.Frame(parent)
        
        # Configure column weights
        for col in range(cols):
            grid_frame.grid_columnconfigure(col, weight=1, minsize=min_col_width)
        
        # Configure row weights
        for row in range(rows):
            grid_frame.grid_rowconfigure(row, weight=1, minsize=min_row_height)
        
        return grid_frame

class CommonPatterns:
    """Common UI patterns used across the application"""
    
    @staticmethod
    def create_header_with_back_button(parent, title, back_command=None):
        """Create a standard header with optional back button and title"""
        header_frame = StyledWidgets.create_header_frame(parent)
        header_frame.pack(fill='x', pady=(0, Spacing.MD))
        
        if back_command:
            back_btn = StyledWidgets.create_back_button(header_frame, back_command)
            back_btn.pack(side='left')
        
        title_label = StyledWidgets.create_title_label(header_frame, title, bg=Colors.HEADER_BG)
        title_label.pack(side='left', padx=(Spacing.LG, 0))
        
        return header_frame
    
    @staticmethod
    def create_main_action_button(parent, text, command, button_type='accent'):
        """Create a prominent main action button"""
        # Button container for centering
        button_container = Frame(parent, bg=Colors.CONTENT_BG)
        button_container.pack(pady=Spacing.XL)
        
        # For special large buttons (like generate button)
        if button_type == 'large_square':
            button_frame = Frame(button_container, bg=Colors.SECONDARY, relief='raised', bd=2)
            button_frame.pack()
            button_frame.pack_propagate(False)
            button_frame.configure(width=180, height=180)
            
            button = Button(button_frame, text=text, command=command,
                          font=Fonts.SUBHEADING, bg=Colors.SECONDARY, fg=Colors.WHITE,
                          activebackground=Colors.SECONDARY_HOVER, activeforeground=Colors.WHITE,
                          relief='flat', bd=0)
            button.pack(fill='both', expand=True)
        else:
            # Standard TTK button
            style_map = {
                'accent': 'Accent.TButton',
                'success': 'Success.TButton',
                'warning': 'Warning.TButton'
            }
            button = ttk.Button(button_container, text=text, command=command,
                              style=style_map.get(button_type, 'Accent.TButton'))
            button.pack()
        
        return button
    
    @staticmethod
    def create_status_section(parent, initial_text="Ready"):
        """Create a status section at the bottom of a form"""
        status_frame = Frame(parent, bg=Colors.WHITE, relief='raised', bd=1)
        status_frame.pack(fill='x', padx=Spacing.SM, pady=(Spacing.LG, 0))
        status_frame.pack_propagate(False)
        status_frame.configure(height=60)
        
        status_label = StyledWidgets.create_status_label(status_frame, initial_text, bg=Colors.WHITE)
        status_label.pack(expand=True)
        
        return status_frame, status_label
