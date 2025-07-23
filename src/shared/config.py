"""
Simple Configuration Management for InfiniLing
"""

import json
import os
import tempfile

class ConfigManager:
    """Simple configuration manager."""
    
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self._load_config()
    
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
    
    def get_temp_path(self, filename):
        """Get full path for temp file."""
        return os.path.join(tempfile.gettempdir(), filename)

def initialize_config(config_file='config.json'):
    """Initialize configuration."""
    return ConfigManager(config_file)