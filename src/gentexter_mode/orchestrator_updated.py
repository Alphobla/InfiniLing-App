#!/usr/bin/env python3
"""
Updated Main Orchestrator - Database Version

Coordinates all the components for a complete vocabulary learning session using 
the new SQLite database and scientific spaced repetition system.
"""

import os
import tempfile
import json
from typing import List, Tuple, Optional
from .text_generator import TextGenerator
from .audio_generator import AudioGenerator
from .spaced_repetition_selector import SpacedRepetitionSelector
from ..shared.database_models import DatabaseManager


class VocabularyApp:
    """Main application coordinator for vocabulary learning sessions with database backend."""
    
    def __init__(self, database_url: str = None, config=None):
        """
        Initialize the vocabulary app with database backend and configuration.
        
        Args:
            database_url: Database connection string (defaults to SQLite in project root)
            config: ConfigManager instance for accessing configuration settings
        """
        self.config = config
        self.database_manager = DatabaseManager(database_url)
        self.spaced_repetition_selector = SpacedRepetitionSelector(self.database_manager)
        self.text_generator = TextGenerator(config=self.config)
        self.audio_generator = AudioGenerator(config=self.config)
        
        # Session data storage for passing data between stages
        self._current_session_data = {}
    
    def run_learning_session(self, 
                           total_words: int = 20,
                           new_word_ratio: float = 0.25,  # 25% new words (5 out of 20)
                           text_length: int = 300,
                           language: str = "French",
                           generate_audio: bool = True,
                           progress_callback=None) -> dict:
        """
        Run a complete vocabulary learning session using spaced repetition.
        
        Args:
            total_words: Total number of words to use (default: 20)
            new_word_ratio: Ratio of new words to include (default: 0.25 = 25%)
            language: Language for text generation
            generate_audio: Whether to generate audio
            progress_callback: Optional callback function for progress updates
        
        Returns:
            dict: Session results with words, text, audio_path, and session_info
        """
        
        # Get database statistics
        stats = self.spaced_repetition_selector.get_review_statistics()
        vocab_count = stats['total_words']
        progress_callback(f"📊 Database: {vocab_count} total words, {stats['due_words']} due, {stats['new_words']} new") if progress_callback else None

        # Check if we have enough vocabulary
        progress_callback(f"❌ Not enough vocabulary words. Need at least {total_words}, have {vocab_count}") if progress_callback and vocab_count < total_words else None
        
        words_objects = self.spaced_repetition_selector.select_words_for_review(
            target_count=total_words,
            new_word_ratio=new_word_ratio
        )
        
        if not words_objects:
            progress_callback("❌ No words selected") if progress_callback else None
            return {"words": [], "text": "", "audio_path": "", "session_info": {}}
        
        # Convert word objects to dicts for text generator compatibility
        words = []
        session_info = {
            'total_words': len(words_objects),
            'word_details': []
        }
        
        for word_obj in words_objects:
            # Convert to dictionary format
            word_dic = {
                'word': word_obj.word,
                'translation': word_obj.translation,
                'pronunciation': word_obj.pronunciation or ""
            }
            words.append(word_dic)
            
            # Add word details for session info
            occurrences = self.database_manager.get_word_occurrences(word_obj.id)
            is_new = len(occurrences) == 0
            
            session_info['word_details'].append({
                'id': word_obj.id,
                'word': word_obj.word,
                'translation': word_obj.translation,
                'is_new': is_new,
                'total_reviews': len(occurrences),
                'pronunciation': word_obj.pronunciation
            })
        
        if progress_callback:
            new_word_count = int(total_words * new_word_ratio)
            progress_callback(f"✅ Selected {len(words)} ({new_word_count} new) words for the session")

        # Generate content
        generated_text = ""
        audio_path = ""
        
        if self.text_generator:
            try:
                generated_text = self.text_generator.generate_story(words, language, word_count=text_length)

                # Save the generated text persistently
                text_filename = self.config.get('paths.temp_text_file', 'infiniling_text.txt')
                text_path = self.config.get_temp_path(text_filename)
                text_path = self.config.resolve_path(text_path)
                
                try:
                    with open(text_path, 'w', encoding='utf-8') as f:
                        f.write(generated_text)
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"⚠️ Could not save text file: {e}")
                
            except Exception as e:
                if progress_callback:
                    progress_callback(f"❌ Error generating text: {e}")
                generated_text = ""
        
        if self.audio_generator and generated_text and generate_audio:
            try:
                progress_callback("🎵 Generating audio...") if progress_callback else None

                audio_filename = self.config.get('paths.temp_audio_file', 'infiniling_audio.mp3')
                audio_path = self.config.get_temp_path(audio_filename)
                audio_path = self.config.resolve_path(audio_path)
                success = self.audio_generator.generate_audio(generated_text, audio_path)

            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️ Error generating audio: {e}")
                audio_path = ""
        self._current_session_data = {
            "words": words,
            "text": generated_text,
            "audio_path": audio_path,
            "session_info": session_info
        }
        self.save_temp_session_data()
        # Return session results
        return self._current_session_data
    
    def run_scratch_session(self, 
                             language: str = "French",
                             difficulty: str = "A1",
                             total_words: int = 20,
                             text_length: int = 300,
                             generate_audio: bool = True,
                             progress_callback=None) -> dict:
        """
        Run a learning session starting from scratch by generating words from GPT.
        
        Args:
            language: Language for word and text generation
            difficulty: Difficulty level (A1-C2)
            total_words: Total number of words to generate
            text_length: Length of the generated story
            generate_audio: Whether to generate audio
            progress_callback: Optional callback for progress updates
            
        Returns:
            dict: Session results
        """
        # 1. Generate words and translations
        progress_callback(f"🎯 Generating {total_words} {difficulty} words in {language}...") if progress_callback else None
        words = self.text_generator.generate_initial_words(language, difficulty, count=total_words)
        
        if not words:
            progress_callback("❌ Failed to generate words") if progress_callback else None
            return {"words": [], "text": "", "audio_path": "", "session_info": {}}
            
        progress_callback(f"✅ Generated {len(words)} words") if progress_callback else None
        
        # 2. Generate content (Story)
        progress_callback(f"📖 Generating story in {language}...") if progress_callback else None
        generated_text = self.text_generator.generate_story(words, language, word_count=text_length)
        
        # Save text file
        text_filename = self.config.get('paths.temp_text_file', 'infiniling_text.txt')
        text_path = self.config.get_temp_path(text_filename)
        text_path = self.config.resolve_path(text_path)
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(generated_text)
            
        # 3. Generate Audio
        audio_path = ""
        if generate_audio and generated_text:
            progress_callback("🎵 Generating audio...") if progress_callback else None
            audio_filename = self.config.get('paths.temp_audio_file', 'infiniling_audio.mp3')
            audio_path = self.config.get_temp_path(audio_filename)
            audio_path = self.config.resolve_path(audio_path)
            self.audio_generator.generate_audio(generated_text, audio_path)
            
        # 4. Prepare session info
        session_info = {
            'total_words': len(words),
            'word_details': [
                {
                    'id': None, 
                    'word': w['word'], 
                    'translation': w['translation'], 
                    'is_new': True, 
                    'total_reviews': 0,
                    'pronunciation': w.get('pronunciation', '')
                } for w in words
            ],
            'mode': 'scratch',
            'difficulty': difficulty
        }
        
        self._current_session_data = {
            "words": words,
            "text": generated_text,
            "audio_path": audio_path,
            "session_info": session_info
        }
        
        self.save_temp_session_data()
        return self._current_session_data

    def get_vocabulary_count(self) -> int:
        """Get the total number of words in the database."""
        return len(self.database_manager.get_all_words())
    
    def add_word_to_database(self, word: str, translation: str, 
                           language_from: str = 'fr', language_to: str = 'de',
                           pronunciation: str = None, 
                           example_sentence_original: str = None,
                           example_sentence_translation: str = None) -> bool:
        """
        Add a new word to the vocabulary database.
        
        Args:
            word: The word to add
            translation: Translation of the word
            language_from: Source language (default: 'fr')
            language_to: Target language (default: 'de')
            pronunciation: Optional pronunciation
            example_sentence_original: Optional example sentence in original language
            example_sentence_translation: Optional example sentence translation
        
        Returns:
            bool: True if word was added successfully, False otherwise
        """
        try:
            self.database_manager.add_word(
                word=word,
                translation=translation,
                language_from=language_from,
                language_to=language_to,
                pronunciation=pronunciation,
                example_sentence_original=example_sentence_original,
                example_sentence_translation=example_sentence_translation
            )
            return True
        except Exception as e:
            print(f"❌ Error adding word to database: {e}")
            return False
    
    def mark_word_reviewed(self, word_id: int, feedback_score: int) -> bool:
        """
        Mark a word as reviewed with feedback score.
        
        Args:
            word_id: ID of the word that was reviewed
            feedback_score: Score from 1-5 (1=total failure, 5=perfect)
        
        Returns:
            bool: True if successfully recorded, False otherwise
        """
        try:
            self.spaced_repetition_selector.mark_word_reviewed(word_id, feedback_score)
            return True
        except Exception as e:
            print(f"❌ Error marking word as reviewed: {e}")
            return False
    
    def load_last_session(self) -> dict:
        """
        Load the last generated session content.
        
        Returns:
            dict: Dictionary with 'text', 'audio_path', and 'words' if available
        """
        result = {
            'text': '',
            'audio_path': '',
            'words': []
        }
        
        try:
            # Load text using config paths
            text_filename = self.config.get('paths.temp_text_file', 'infiniling_text.txt')
            text_path = self.config.get_temp_path(text_filename)
            audio_filename = self.config.get('paths.temp_audio_file', 'infiniling_audio.mp3')
            audio_path = self.config.get_temp_path(audio_filename)
            words_filename = self.config.get('paths.temp_words_file', 'infiniling_words.json')
            words_path = self.config.get_temp_path(words_filename)
            
            # Load text
            with open(text_path, 'r', encoding='utf-8') as f:
                result['text'] = f.read()
            
            # Load audio path
            result['audio_path'] = audio_path
            
            # Load words
            with open(words_path, 'r', encoding='utf-8') as f:
                result['words'] = json.load(f)
        
        except Exception as e:
            print(f"⚠️ Error loading last session: {e}")
        
        return result
    
    def update_current_session_data(self, data: dict):
        """
        Update the current session data with new information.
        
        Args:
            data: Dictionary with session data to update
        """
        if not isinstance(data, dict):
            raise ValueError("Session data must be a dictionary")
        
        self._current_session_data.update(data)

    def get_current_session_data(self) -> dict:
        """
        Get current session data.
        
        Returns:
            dict: Current session data
        """
        return self._current_session_data.copy()
    
    def clear_current_session_data(self):
        """Clear current session data."""
        self._current_session_data = {}

    def save_temp_session_data(self):
        """
        Save session data to a temporary file.
        
        Args:
            session_data: Dictionary with session data to save
        
        Returns:
            str: Path to the temporary file
        """
        try:
            words_filename = self.config.get('paths.temp_words_file')
            words_path = self.config.get_temp_path(words_filename)
            session_data = self.get_current_session_data()
            
            with open(words_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=4)
            return words_path
        except Exception as e:
            print(f"❌ Error saving temporary session data: {e}")
            return ""

    def read_temp_session_data(self):
        """Read temporary session data from file"""
        try:
            words_filename = self.config.get('paths.temp_words_file')
            words_path = self.config.get_temp_path(words_filename)
            
            with open(words_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            return session_data
        except Exception as e:
            print(f"❌ Error reading temporary words: {str(e)}")
            return None

# Example usage and testing
if __name__ == "__main__":
    # Initialize the app
    app = VocabularyApp()
    
    # Get statistics
    stats = app.spaced_repetition_selector.get_review_statistics()
    print(f"📊 Vocabulary Statistics:")
    print(f"  Total words: {stats['total_words']}")
    print(f"  New words: {stats['new_words']}")
    print(f"  Due words: {stats['due_words']}")
    print(f"  Future words: {stats['future_words']}")
    
    # Run a learning session
    if stats['total_words'] >= 20:
        print("\n🚀 Running learning session...")
        
        def progress_callback(message):
            print(f"  {message}")
        
        result = app.run_learning_session(
            total_words=20,
            new_word_ratio=0.25,
            generate_audio=False,  # Skip audio for demo
            progress_callback=progress_callback
        )
        
        print(f"\n📝 Generated text ({len(result['text'])} characters):")
        print(result['text'][:200] + "..." if len(result['text']) > 200 else result['text'])
        
        print(f"\n📊 Session info:")
        print(f"  Words selected: {result['session_info']['total_words']}")
        new_words = sum(1 for word in result['session_info']['word_details'] if word['is_new'])
        print(f"  New words: {new_words}")
        print(f"  Due words: {result['session_info']['total_words'] - new_words}")
    
    else:
        print(f"\n❌ Not enough words in database. Need 20, have {stats['total_words']}")
        print("Please run the migration script first to populate the database.")