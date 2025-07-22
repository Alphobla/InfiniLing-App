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
    
    def __init__(self, database_url: str = None):
        """
        Initialize the vocabulary app with database backend.
        
        Args:
            database_url: Database connection string (defaults to SQLite in project root)
        """
        # Initialize database components
        self.database_manager = DatabaseManager(database_url)
        self.spaced_repetition_selector = SpacedRepetitionSelector(self.database_manager)
        
        # Initialize AI components (may fail if API key not available)
        try:
            self.text_generator = TextGenerator()
            print("✅ Text generator initialized")
        except ValueError as e:
            print(f"⚠️ Text generator not available: {e}")
            self.text_generator = None
        
        try:
            self.audio_generator = AudioGenerator()
            print("✅ Audio generator initialized")
        except ValueError as e:
            print(f"⚠️ Audio generator not available: {e}")
            self.audio_generator = None
    
    def get_vocabulary_count(self) -> int:
        """Get the total number of words in the database."""
        return len(self.database_manager.get_all_words())
    
    def get_review_statistics(self) -> dict:
        """Get current review statistics."""
        return self.spaced_repetition_selector.get_review_statistics()
    
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
    
    def run_learning_session(self, 
                           total_words: int = 20,
                           new_word_ratio: float = 0.25,  # 25% new words (5 out of 20)
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
            dict: Session results with selected_words, story, audio_path, and session_info
        """
        
        if progress_callback:
            progress_callback("🚀 Starting vocabulary learning session...")
        
        # Get database statistics
        stats = self.get_review_statistics()
        vocab_count = stats['total_words']
        
        if progress_callback:
            progress_callback(f"📊 Database: {vocab_count} total words, {stats['due_words']} due, {stats['new_words']} new")
        
        # Check if we have enough vocabulary
        if vocab_count < total_words:
            if progress_callback:
                progress_callback(f"❌ Not enough vocabulary words. Need at least {total_words}, have {vocab_count}")
            return {"selected_words": [], "story": "", "audio_path": "", "session_info": {}}
        
        # Select words using scientific spaced repetition
        if progress_callback:
            new_word_count = int(total_words * new_word_ratio)
            due_word_count = total_words - new_word_count
            progress_callback(f"🎯 Selecting {total_words} words ({due_word_count} due + {new_word_count} new)...")
        
        selected_words_objects = self.spaced_repetition_selector.select_words_for_review(
            target_count=total_words,
            new_word_ratio=new_word_ratio
        )
        
        if not selected_words_objects:
            if progress_callback:
                progress_callback("❌ No words selected")
            return {"selected_words": [], "story": "", "audio_path": "", "session_info": {}}
        
        # Convert word objects to tuples for text generator compatibility
        selected_words = []
        session_info = {
            'total_words': len(selected_words_objects),
            'word_details': []
        }
        
        for word_obj in selected_words_objects:
            # Convert to tuple format: (word, translation, pronunciation)
            word_tuple = (
                word_obj.word,
                word_obj.translation,
                word_obj.pronunciation or ""
            )
            selected_words.append(word_tuple)
            
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
            progress_callback(f"✅ Selected {len(selected_words)} words for the session")
        
        # Generate content
        generated_text = ""
        audio_path = ""
        
        if self.text_generator:
            try:
                if progress_callback:
                    progress_callback(f"📝 Generating story in {language}...")
                generated_text = self.text_generator.generate_story(selected_words, language)
                if progress_callback:
                    progress_callback("✅ Story generated successfully")
                
                # Save the generated text persistently
                if generated_text:
                    text_path = os.path.join(tempfile.gettempdir(), "infiniling_text.txt")
                    try:
                        with open(text_path, 'w', encoding='utf-8') as f:
                            f.write(generated_text)
                    except Exception as e:
                        if progress_callback:
                            progress_callback(f"⚠️ Could not save text file: {e}")
                
                # Save the selected vocabulary words for vocabulary review
                self._save_selected_words(selected_words, progress_callback)
                
            except Exception as e:
                if progress_callback:
                    progress_callback(f"❌ Error generating story: {e}")
                generated_text = ""
        
        if self.audio_generator and generated_text and generate_audio:
            try:
                if progress_callback:
                    progress_callback("🎵 Generating audio...")
                audio_path = os.path.join(tempfile.gettempdir(), "infiniling_audio.mp3")
                success = self.audio_generator.generate_audio(generated_text, audio_path)
                if success and progress_callback:
                    progress_callback("✅ Audio generated successfully")
                elif not success:
                    audio_path = ""
            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️ Error generating audio: {e}")
                audio_path = ""
        
        # Return session results
        return {
            "selected_words": selected_words,
            "story": generated_text,
            "audio_path": audio_path,
            "session_info": session_info
        }
    
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
    
    def _save_selected_words(self, selected_words: List[Tuple[str, str, str]], progress_callback=None):
        """
        Save selected words to temp file for vocabulary review.
        
        Args:
            selected_words: List of (word, translation, pronunciation) tuples
            progress_callback: Optional callback for progress updates
        """
        try:
            words_path = os.path.join(tempfile.gettempdir(), "infiniling_words.json")
            words_data = [
                {
                    "word": word,
                    "translation": translation,
                    "pronunciation": pronunciation
                }
                for word, translation, pronunciation in selected_words
            ]
            
            with open(words_path, 'w', encoding='utf-8') as f:
                json.dump(words_data, f, ensure_ascii=False, indent=2)
            
            if progress_callback:
                progress_callback(f"💾 Temporary vocabulary list saved to {words_path}")
                
        except Exception as e:
            if progress_callback:
                progress_callback(f"⚠️ Could not save vocabulary list: {e}")
    
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
            # Load text
            text_path = os.path.join(tempfile.gettempdir(), "infiniling_text.txt")
            if os.path.exists(text_path):
                with open(text_path, 'r', encoding='utf-8') as f:
                    result['text'] = f.read()
            
            # Load audio path
            audio_path = os.path.join(tempfile.gettempdir(), "infiniling_audio.mp3")
            if os.path.exists(audio_path):
                result['audio_path'] = audio_path
            
            # Load words
            words_path = os.path.join(tempfile.gettempdir(), "infiniling_words.json")
            if os.path.exists(words_path):
                with open(words_path, 'r', encoding='utf-8') as f:
                    result['words'] = json.load(f)
        
        except Exception as e:
            print(f"⚠️ Error loading last session: {e}")
        
        return result
    
    def get_session_configuration(self) -> dict:
        """
        Get current session configuration settings.
        
        Returns:
            dict: Configuration settings
        """
        return {
            'total_words': 20,
            'new_word_ratio': 0.25,
            'due_words': 15,
            'new_words': 5,
            'language': 'French',
            'generate_audio': True
        }
    
    def update_session_configuration(self, **kwargs) -> dict:
        """
        Update session configuration settings.
        
        Args:
            **kwargs: Configuration parameters to update
        
        Returns:
            dict: Updated configuration
        """
        # For now, this is a placeholder since we're using parameters in run_learning_session
        # In a full implementation, this could persist settings to a config file
        current_config = self.get_session_configuration()
        current_config.update(kwargs)
        return current_config


# Example usage and testing
if __name__ == "__main__":
    # Initialize the app
    app = VocabularyApp()
    
    # Get statistics
    stats = app.get_review_statistics()
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
        
        print(f"\n📝 Generated story ({len(result['story'])} characters):")
        print(result['story'][:200] + "..." if len(result['story']) > 200 else result['story'])
        
        print(f"\n📊 Session info:")
        print(f"  Words selected: {result['session_info']['total_words']}")
        new_words = sum(1 for word in result['session_info']['word_details'] if word['is_new'])
        print(f"  New words: {new_words}")
        print(f"  Due words: {result['session_info']['total_words'] - new_words}")
    
    else:
        print(f"\n❌ Not enough words in database. Need 20, have {stats['total_words']}")
        print("Please run the migration script first to populate the database.")