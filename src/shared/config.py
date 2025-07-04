# Configuration settings for the unified language application

class Config:
    """Configuration settings for the application."""
    
    # API keys and model parameters
    WHISPER_MODEL_SIZE = "small"  # Options: tiny, base, small, medium, large, turbo
    DEFAULT_LANGUAGE = "fr"  # Default language for transcription
    DOWNLOADS_FOLDER = "~/Downloads"  # Default folder for audio files
    VOCABULARY_FILE_PATH = "data/word_tracking.json"  # Path to the vocabulary tracking file
    APP_SETTINGS_PATH = "data/app_settings.json"  # Path to application settings file

    @staticmethod
    def get_downloads_folder():
        """Return the path to the downloads folder."""
        return os.path.expanduser(Config.DOWNLOADS_FOLDER)

    @staticmethod
    def get_vocabulary_file_path():
        """Return the path to the vocabulary tracking file."""
        return Config.VOCABULARY_FILE_PATH

    @staticmethod
    def get_app_settings_path():
        """Return the path to the application settings file."""
        return Config.APP_SETTINGS_PATH