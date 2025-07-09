"""
Shared styling system for InfiniLing application
Provides consistent TTK styles and color constants across all modules
"""
from tkinter import ttk

# Color Palette
class Colors:
    # Primary colors
    PRIMARY = '#0078d4'
    PRIMARY_HOVER = '#106ebe'
    PRIMARY_PRESSED = '#005a9e'
    
    # Secondary colors
    SECONDARY = '#27ae60'
    SECONDARY_HOVER = '#219a52'
    
    # Neutral colors
    WHITE = '#ffffff'
    LIGHT_GRAY = '#f8f9fa'
    MEDIUM_GRAY = '#6c757d'
    DARK_GRAY = '#2c3e50'
    BORDER_GRAY = '#e9ecef'
    TEXT_GRAY = '#495057'
    
    # Status colors
    SUCCESS = '#28a745'
    WARNING = '#ffc107'
    ERROR = '#dc3545'
    INFO = '#17a2b8'
    
    # Tile colors
    TILE_NORMAL = '#f9f9f9'
    TILE_SELECTED = '#fff3cd'
    TILE_SELECTED_TEXT = '#856404'
    
    # Background colors
    CARD_BG = '#ffffff'
    CONTENT_BG = '#f8f9fa'
    HEADER_BG = '#f8f9fa'
    
    # Button colors - Audio Controls
    BUTTON_PLAY = '#27ae60'      # Green
    BUTTON_PAUSE = '#f39c12'     # Orange  
    BUTTON_STOP = '#e74c3c'      # Red
    BUTTON_JUMP = '#3498db'      # Blue
    BUTTON_SPEED = '#9b59b6'     # Purple
    
    # Button colors - General Actions
    BUTTON_PRIMARY = '#007bff'   # Blue
    BUTTON_SECONDARY = '#6c757d' # Grey
    BUTTON_SUCCESS = '#28a745'   # Green
    BUTTON_DANGER = '#dc3545'    # Red
    BUTTON_WARNING = '#ffc107'   # Yellow
    BUTTON_INFO = '#17a2b8'      # Cyan
    
    # Hover states (slightly darker versions)
    BUTTON_PLAY_HOVER = '#229954'
    BUTTON_PAUSE_HOVER = '#e67e22'
    BUTTON_STOP_HOVER = '#c0392b'
    BUTTON_JUMP_HOVER = '#2980b9'
    BUTTON_SPEED_HOVER = '#8e44ad'
    
    # Legacy aliases for backward compatibility
    LIGHT = '#f8f9fa'  # Same as LIGHT_GRAY
    DARK = '#343a40'
    BLACK = '#000000'
    BACKGROUND = '#f8f9fa'  # Same as CONTENT_BG
    SURFACE = '#ffffff'     # Same as CARD_BG
    BORDER = '#dee2e6'      # Same as BORDER_GRAY
    TEXT = '#212529'        # Same as TEXT_GRAY
    TEXT_MUTED = '#6c757d'  # Same as MEDIUM_GRAY
    TEXT_LIGHT = '#ffffff'  # Same as WHITE
    
    # Additional aliases
    ACCENT = '#3498db'      # Same as BUTTON_JUMP
    DANGER = '#e74c3c'      # Same as ERROR
    
    # State colors
    SELECTED = '#007bff'
    HOVER = '#e9ecef'
    ACTIVE = '#007bff'
    DISABLED = '#e9ecef'
    
    # Vocabulary colors
    KNOWN = '#28a745'
    LEARNING = '#ffc107'
    UNKNOWN = '#dc3545'
    
    # Progress colors
    PROGRESS_BG = '#e9ecef'
    PROGRESS_FILL = '#007bff'

# Font Definitions
class Fonts:
    # Font family
    FAMILY = 'Segoe UI'
    
    # Font sizes
    TITLE = ('Segoe UI', 20, 'bold')
    HEADING = ('Segoe UI', 18, 'bold')
    SUBHEADING = ('Segoe UI', 14, 'bold')
    BODY = ('Segoe UI', 11)
    BODY_BOLD = ('Segoe UI', 11, 'bold')
    SMALL = ('Segoe UI', 10)
    SMALL_ITALIC = ('Segoe UI', 9, 'italic')
    
    # Button fonts
    BUTTON_LARGE = ('Segoe UI', 12, 'bold')
    BUTTON_NORMAL = ('Segoe UI', 11)
    
    # Tile fonts
    TILE_WORD = ('Segoe UI', 13, 'bold')
    TILE_TRANSLATION = ('Segoe UI', 11)
    TILE_PRONUNCIATION = ('Segoe UI', 9, 'italic')

# Spacing Constants
class Spacing:
    XS = 5
    SM = 10
    MD = 15
    LG = 20
    XL = 30
    XXL = 40

class StyleManager:
    """Central style manager for consistent TTK styling"""
    
    def __init__(self):
        self.style = ttk.Style()
        self.setup_theme()
    
    def setup_theme(self):
        """Setup the complete modern theme"""
        self.style.theme_use('clam')
        
        # Setup all style components
        self._setup_button_styles()
        self._setup_frame_styles()
        self._setup_label_styles()
        self._setup_tile_styles()
    
    def _setup_button_styles(self):
        """Configure all button styles"""
        # Primary accent button
        self.style.configure('Accent.TButton', 
                           font=Fonts.BUTTON_LARGE,
                           padding=(25, 15),
                           relief='flat',
                           borderwidth=0,
                           background=Colors.PRIMARY,
                           foreground=Colors.WHITE)
        
        self.style.map('Accent.TButton',
                      background=[('active', Colors.PRIMARY_HOVER),
                                ('pressed', Colors.PRIMARY_PRESSED)])
        
        # Modern button (secondary)
        self.style.configure('Modern.TButton', 
                           font=Fonts.BUTTON_NORMAL,
                           padding=(20, 12),
                           relief='flat',
                           borderwidth=0,
                           background=Colors.LIGHT_GRAY,
                           foreground=Colors.DARK_GRAY)
        
        self.style.map('Modern.TButton',
                      background=[('active', Colors.BORDER_GRAY),
                                ('pressed', '#dee2e6')])
        
        # Warning button (for destructive actions)
        self.style.configure('Warning.TButton', 
                           font=Fonts.BUTTON_NORMAL,
                           padding=(20, 12),
                           relief='flat',
                           borderwidth=0,
                           background=Colors.ERROR,
                           foreground=Colors.WHITE)
        
        self.style.map('Warning.TButton',
                      background=[('active', '#c82333'),
                                ('pressed', '#bd2130')])
        
        # Success button
        self.style.configure('Success.TButton', 
                           font=Fonts.BUTTON_NORMAL,
                           padding=(20, 12),
                           relief='flat',
                           borderwidth=0,
                           background=Colors.SUCCESS,
                           foreground=Colors.WHITE)
        
        self.style.map('Success.TButton',
                      background=[('active', '#218838'),
                                ('pressed', '#1e7e34')])
    
    def _setup_frame_styles(self):
        """Configure frame styles"""
        # Card frame (elevated content)
        self.style.configure('Card.TFrame',
                           background=Colors.CARD_BG,
                           relief='flat',
                           borderwidth=1)
        
        # Content frame (main content areas)
        self.style.configure('Content.TFrame',
                           background=Colors.CONTENT_BG,
                           relief='flat')
        
        # Header frame
        self.style.configure('Header.TFrame',
                           background=Colors.HEADER_BG,
                           relief='flat')
    
    def _setup_label_styles(self):
        """Configure label styles"""
        # Title labels
        self.style.configure('Title.TLabel',
                           font=Fonts.TITLE,
                           background=Colors.CARD_BG,
                           foreground=Colors.DARK_GRAY)
        
        # Heading labels
        self.style.configure('Heading.TLabel',
                           font=Fonts.HEADING,
                           background=Colors.CARD_BG,
                           foreground=Colors.DARK_GRAY)
        
        # Subheading labels
        self.style.configure('Subheading.TLabel',
                           font=Fonts.SUBHEADING,
                           background=Colors.CARD_BG,
                           foreground=Colors.MEDIUM_GRAY)
        
        # Body text labels
        self.style.configure('Body.TLabel',
                           font=Fonts.BODY,
                           background=Colors.CARD_BG,
                           foreground=Colors.TEXT_GRAY)
        
        # Status labels
        self.style.configure('Success.TLabel',
                           font=Fonts.BODY,
                           background=Colors.CARD_BG,
                           foreground=Colors.SUCCESS)
        
        self.style.configure('Warning.TLabel',
                           font=Fonts.BODY,
                           background=Colors.CARD_BG,
                           foreground=Colors.WARNING)
        
        self.style.configure('Error.TLabel',
                           font=Fonts.BODY,
                           background=Colors.CARD_BG,
                           foreground=Colors.ERROR)
    
    def _setup_tile_styles(self):
        """Configure vocabulary tile styles"""
        # Normal tile container
        self.style.configure('TileContainer.TFrame',
                           background=Colors.TILE_NORMAL,
                           relief='solid',
                           borderwidth=1)
        
        # Selected tile container
        self.style.configure('SelectedTileContainer.TFrame',
                           background=Colors.TILE_SELECTED,
                           relief='solid',
                           borderwidth=2)
        
        # Tile word labels (normal)
        self.style.configure('TileWord.TLabel',
                           font=Fonts.TILE_WORD,
                           background=Colors.TILE_NORMAL,
                           foreground=Colors.DARK_GRAY)
        
        self.style.configure('TileTranslation.TLabel',
                           font=Fonts.TILE_TRANSLATION,
                           background=Colors.TILE_NORMAL,
                           foreground=Colors.PRIMARY)
        
        self.style.configure('TilePronunciation.TLabel',
                           font=Fonts.TILE_PRONUNCIATION,
                           background=Colors.TILE_NORMAL,
                           foreground=Colors.MEDIUM_GRAY)
        
        # Tile word labels (selected)
        self.style.configure('SelectedTileWord.TLabel',
                           font=Fonts.TILE_WORD,
                           background=Colors.TILE_SELECTED,
                           foreground=Colors.TILE_SELECTED_TEXT)
        
        self.style.configure('SelectedTileTranslation.TLabel',
                           font=Fonts.TILE_TRANSLATION,
                           background=Colors.TILE_SELECTED,
                           foreground=Colors.PRIMARY)
        
        self.style.configure('SelectedTilePronunciation.TLabel',
                           font=Fonts.TILE_PRONUNCIATION,
                           background=Colors.TILE_SELECTED,
                           foreground=Colors.MEDIUM_GRAY)
        
        # Tile overlay buttons (for click handling)
        self.style.configure('TileOverlay.TButton',
                           relief='flat',
                           borderwidth=0,
                           background=Colors.TILE_NORMAL)
        
        self.style.configure('SelectedTileOverlay.TButton',
                           relief='flat',
                           borderwidth=0,
                           background=Colors.TILE_SELECTED)
        
        self.style.map('TileOverlay.TButton',
                      background=[('active', Colors.BORDER_GRAY)])
        
        self.style.map('SelectedTileOverlay.TButton',
                      background=[('active', '#ffeaa7')])

# Utility functions for consistent styling
def apply_modern_theme():
    """Apply the modern theme to the current application"""
    return StyleManager()

def get_button_style(button_type='modern'):
    """Get appropriate button style name"""
    styles = {
        'accent': 'Accent.TButton',
        'primary': 'Accent.TButton',
        'modern': 'Modern.TButton',
        'secondary': 'Modern.TButton',
        'warning': 'Warning.TButton',
        'danger': 'Warning.TButton',
        'success': 'Success.TButton'
    }
    return styles.get(button_type, 'Modern.TButton')

def get_label_style(label_type='body'):
    """Get appropriate label style name"""
    styles = {
        'title': 'Title.TLabel',
        'heading': 'Heading.TLabel',
        'subheading': 'Subheading.TLabel',
        'body': 'Body.TLabel',
        'success': 'Success.TLabel',
        'warning': 'Warning.TLabel',
        'error': 'Error.TLabel'
    }
    return styles.get(label_type, 'Body.TLabel')

def get_frame_style(frame_type='content'):
    """Get appropriate frame style name"""
    styles = {
        'card': 'Card.TFrame',
        'content': 'Content.TFrame',
        'header': 'Header.TFrame'
    }
    return styles.get(frame_type, 'Content.TFrame')

def center_top_window(root, width=600, height=450):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 6)
    root.geometry(f"{width}x{height}+{x}+{y}")
