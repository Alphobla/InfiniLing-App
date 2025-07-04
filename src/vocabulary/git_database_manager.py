#!/usr/bin/env python3
"""
Git and Database Manager

Handles Git operations, vocabulary database management, and importing new vocabulary.
"""

import os
import json
import subprocess
import pandas as pd
from typing import List, Tuple, Optional, Dict, Any


class GitManager:
    """Handles Git operations for the vocabulary repository."""
    
    def __init__(self, repo_path: str = None):
        self.repo_path = repo_path or os.getcwd()
        
    
    def pull_latest(self) -> bool:
        """Pull latest changes from Git repository."""
        try:
            result = subprocess.run(['git', 'pull'], 
                                  cwd=self.repo_path, 
                                  capture_output=True, 
                                  text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def push_changes(self, commit_message: str = "Update vocabulary data") -> bool:
        """Push changes to Git repository."""
        try:
            # Add all changes
            subprocess.run(['git', 'add', '.'], cwd=self.repo_path)
            
            # Commit changes
            subprocess.run(['git', 'commit', '-m', commit_message], cwd=self.repo_path)
            
            # Push changes
            result = subprocess.run(['git', 'push'], 
                                  cwd=self.repo_path, 
                                  capture_output=True, 
                                  text=True)
            return result.returncode == 0
        except Exception:
            return False


class DatabaseManager:
    """Manages the vocabulary database (JSON file)."""
    
    def __init__(self, tracking_file_path: str):
        self.tracking_file_path = tracking_file_path
        self.ensure_database_exists()
        # Load word stats after ensuring database exists
        self._refresh_word_stats()
    
    def ensure_database_exists(self):
        """Create the database file if it doesn't exist."""
        if not os.path.exists(self.tracking_file_path):
            os.makedirs(os.path.dirname(self.tracking_file_path), exist_ok=True)
            self.save_data({})
    
    def load_data(self) -> Dict[str, Any]:
        """Load vocabulary data from JSON file."""
        try:
            with open(self.tracking_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_data(self, data: Dict[str, Any]):
        """Save vocabulary data to JSON file."""
        with open(self.tracking_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # Refresh word stats after saving
        self._refresh_word_stats()
    
    def _refresh_word_stats(self):
        """Refresh the word_stats property from the database."""
        self.word_stats = self.load_data()
    
    def get_all_words(self) -> List[Tuple[str, str]]:
        """Get all words from the database as (word, translation) tuples."""
        data = self.load_data()
        words = []
        for key, value in data.items():
            if isinstance(value, dict) and 'word' in value and 'translation' in value:
                words.append((value['word'], value['translation']))
        return words
    
    def get_vocabulary_list(self) -> List[Tuple[str, str, str]]:
        """Get all vocabulary as list of (word, translation, pronunciation) tuples."""
        data = self.load_data()
        vocab_list = []
        
        for word_key, stats in data.items():
            if isinstance(stats, dict) and 'word' in stats and 'translation' in stats:
                word = stats['word']
                translation = stats['translation']
                # Extract pronunciation if available, otherwise empty string
                pronunciation = stats.get('pronunciation', '')
                vocab_list.append((word, translation, pronunciation))
        
        return vocab_list
    
    def add_occurrence(self, word: str, translation: str, repeat: bool = False):
        """Add an occurrence record for a word (compatibility method)."""
        self.update_word_tracking(word, translation, repeat)
    
    def add_words(self, words: List[Tuple[str, str]]) -> int:
        """Add new words to the database. Returns count of newly added words."""
        data = self.load_data()
        added_count = 0
        
        for word, translation in words:
            key = f"{word}|{translation}"
            if key not in data:
                data[key] = {
                    "word": word,
                    "translation": translation,
                    "occurrences": []
                }
                added_count += 1
        
        if added_count > 0:
            self.save_data(data)
            # Refresh word stats after adding new words
            self._refresh_word_stats()
        
        return added_count
    
    def update_word_tracking(self, word: str, translation: str, was_difficult: bool):
        """Update tracking information for a word."""
        import datetime
        
        data = self.load_data()
        key = f"{word}|{translation}"
        
        if key in data:
            data[key]["occurrences"].append({
                "date": datetime.datetime.now().isoformat(),
                "repeat": was_difficult
            })
            self.save_data(data)
            # Note: save_data() automatically calls _refresh_word_stats()
    
    def save_tracking_data(self):
        """Save tracking data (compatibility method)."""
        # Data is automatically saved when updated, so this is a no-op
        # But we refresh to ensure consistency
        self._refresh_word_stats()


class VocabularyImporter:
    """Handles importing vocabulary from various file formats."""
    
    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager
    
    def import_from_file(self, file_path: str) -> int:
        """Import vocabulary from a file. Returns count of newly imported words."""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.csv':
            return self._import_from_csv(file_path)
        elif file_extension == '.xlsx':
            return self._import_from_excel(file_path)
        elif file_extension == '.txt':
            return self._import_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def _import_from_csv(self, file_path: str) -> int:
        """Import from CSV file with multiple encoding support."""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                return self._process_dataframe(df)
            except UnicodeDecodeError:
                continue
        
        raise ValueError("Could not decode CSV file with any supported encoding")
    
    def _import_from_excel(self, file_path: str) -> int:
        """Import from Excel file."""
        df = pd.read_excel(file_path)
        return self._process_dataframe(df)
    
    def _import_from_txt(self, file_path: str) -> int:
        """Import from text file (tab or pipe separated)."""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                # Try tab separation first, then pipe
                for separator in ['\t', '|']:
                    try:
                        df = pd.read_csv(file_path, sep=separator, encoding=encoding)
                        if len(df.columns) >= 2:
                            return self._process_dataframe(df)
                    except:
                        continue
            except UnicodeDecodeError:
                continue
        
        raise ValueError("Could not parse text file")
    
    def _process_dataframe(self, df: pd.DataFrame) -> int:
        """Process pandas DataFrame to extract word pairs."""
        if len(df.columns) < 2:
            raise ValueError("File must have at least 2 columns")
        
        # Try to identify word and translation columns
        word_col = df.columns[0]
        translation_col = df.columns[1]
        
        # Look for common column names
        for col in df.columns:
            col_lower = col.lower()
            if any(name in col_lower for name in ['source', 'word', 'term', 'english']):
                word_col = col
            elif any(name in col_lower for name in ['target', 'translation', 'meaning', 'french', 'german']):
                translation_col = col
        
        # Extract word pairs
        words = []
        for _, row in df.iterrows():
            word = str(row[word_col]).strip()
            translation = str(row[translation_col]).strip()
            
            if word and translation and word != 'nan' and translation != 'nan':
                words.append((word, translation))
        
        if not words:
            raise ValueError("No valid word pairs found in file")
        
        return self.database_manager.add_words(words)
    
    def import_from_downloads(self) -> int:
        """Import vocabulary files from Downloads folder."""
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        supported_extensions = ['.csv', '.xlsx', '.txt']
        
        total_imported = 0
        
        for filename in os.listdir(downloads_path):
            if any(filename.lower().endswith(ext) for ext in supported_extensions):
                file_path = os.path.join(downloads_path, filename)
                try:
                    imported_count = self.import_from_file(file_path)
                    total_imported += imported_count
                except Exception:
                    continue  # Skip files that can't be imported
        
        return total_imported
