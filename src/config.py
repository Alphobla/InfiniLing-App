"""
InfiniLing Configuration File
Centralized configuration for the unified language learning application.
"""

import os

# Application Information
APP_NAME = "InfiniLing"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Unified Language Learning Application"

# Paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
TRANSCRIPTIONS_DIR = os.path.join(DATA_DIR, 'transcriptions_and_audio')
WORD_TRACKING_FILE = os.path.join(DATA_DIR, 'word_tracking.json')

# Transcriber Configuration
TRANSCRIBER_MODELS = {
    'tiny': {'size': 'tiny', 'description': 'Fastest, least accurate', 'time_factor': 0.3},
    'base': {'size': 'base', 'description': 'Good balance of speed and accuracy', 'time_factor': 0.5},
    'small': {'size': 'small', 'description': 'Better accuracy, slower', 'time_factor': 0.8},
    'medium': {'size': 'medium', 'description': 'High accuracy, slow', 'time_factor': 1.2},
    'large': {'size': 'large', 'description': 'Highest accuracy, very slow', 'time_factor': 2.0}
}

DEFAULT_TRANSCRIBER_MODEL = 'base'
DEFAULT_TRANSCRIBER_LANGUAGE = 'fr'

# Gentexter Configuration
DEFAULT_RANDOM_SAMPLE_SIZE = 40
DEFAULT_FINAL_SELECTION_SIZE = 20
DEFAULT_USE_DATABANK = True
DEFAULT_USE_TEST_MODE = False

# UI Configuration
MAIN_WINDOW_SIZE = "600x450"
TRANSCRIBER_WINDOW_SIZE = "700x600"
GENTEXTER_WINDOW_SIZE = "500x600"
REVIEW_WINDOW_SIZE = "900x700"

# Colors
COLORS = {
    'primary': '#3498db',
    'secondary': '#e74c3c',
    'success': '#27ae60',
    'warning': '#f39c12',
    'danger': '#dc3545',
    'background': '#f0f0f0',
    'text': '#2c3e50',
    'light': '#f8f9fa',
    'dark': '#212529'
}

# Audio Configuration
SUPPORTED_AUDIO_FORMATS = [
    ("All Audio Files", "*.mp3;*.wav;*.m4a;*.flac;*.aac;*.ogg"),
    ("MP3 Files", "*.mp3"),
    ("WAV Files", "*.wav"),
    ("M4A Files", "*.m4a"),
    ("FLAC Files", "*.flac"),
    ("All Files", "*.*")
]

# Ensure data directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)