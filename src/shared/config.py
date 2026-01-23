"""
Simple Configuration Management for InfiniLing
"""

import json
import os
import tempfile

class ConfigManager:
    """Simple configuration manager."""
    
    def __init__(self, config_file='config.json'):
        self.config_root = self._get_config_root()
        self.config_file = self.resolve_path(config_file)
        self.config = self._load_config()
    
    def _get_config_root(self):
        """Get the base directory for resources (handles PyInstaller)."""
        import sys
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        return os.path.abspath(".")

    def resolve_path(self, relative_path):
        """Resolve a path relative to the config root or absolute."""
        if not relative_path:
            return self.config_root
        if os.path.isabs(relative_path):
            return os.path.normpath(relative_path)
        return os.path.normpath(os.path.join(self.config_root, relative_path))
    
    def get_user_data_dir(self):
        """Get path to writable user data directory."""
        home = os.path.expanduser('~')
        data_dir = os.path.join(home, '.infiniling')
        os.makedirs(data_dir, exist_ok=True)
        return data_dir
    
    def _load_config(self):
        """Load config from JSON file."""
        with open(self.config_file, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        return user_config
    
    def get(self, key_path, default=None):
        """Get config value using dot notation like 'ui.window_sizes.reader.width'."""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def get_window_size(self, window_type):
        """Get (width, height) for window type."""
        window_config = self.get(f'ui.window_sizes.{window_type}', {'width': 500, 'height': 600})
        return window_config['width'], window_config['height']
    
    def get_user_settings_path(self):
        """Get path to user settings in home directory."""
        home = os.path.expanduser('~')
        settings_dir = os.path.join(home, '.infiniling')
        os.makedirs(settings_dir, exist_ok=True)
        return os.path.join(settings_dir, 'settings.json')

    def load_user_settings(self):
        """Load user settings from home directory."""
        path = self.get_user_settings_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_api_key(self, api_key):
        """Save API key to user settings."""
        settings = self.load_user_settings()
        settings['openai_api_key'] = api_key
        path = self.get_user_settings_path()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
        # Also update the in-memory config for immediate use
        # We store it where the app expects it (usually env or passed to classes)
        os.environ['OPENAI_API_KEY'] = api_key

    def save_mother_tongue(self, language_code):
        """Save mother tongue to user settings."""
        settings = self.load_user_settings()
        settings['mother_tongue'] = language_code
        path = self.get_user_settings_path()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)

    def get_mother_tongue(self):
        """Get mother tongue from user settings."""
        settings = self.load_user_settings()
        return settings.get('mother_tongue')

    def save_last_language(self, language_code):
        """Save last used source language to user settings."""
        settings = self.load_user_settings()
        settings['last_language_from'] = language_code
        path = self.get_user_settings_path()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)

    def get_last_language(self):
        """Get last used source language from user settings. Returns None if not set."""
        settings = self.load_user_settings()
        return settings.get('last_language_from')

    def get_api_key(self):
        """Get API key from ENV or User Settings."""
        # 1. Check ENV (highest priority, from .env file)
        key = os.getenv('OPENAI_API_KEY')
        if key and key.strip():
            return key
            
        # 2. Check User Settings
        settings = self.load_user_settings()
        return settings.get('openai_api_key')

    def get_temp_path(self, filename):
        """Get full path for temp file."""
        return os.path.join(tempfile.gettempdir(), filename)

def initialize_config(config_file='config.json'):
    """Initialize configuration."""
    return ConfigManager(config_file)