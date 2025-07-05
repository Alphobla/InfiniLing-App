#!/usr/bin/env python3
"""
Main Orchestrator

Coordinates all the components for a complete vocabulary learning session.
"""

import os
import tempfile
import json
from typing import List, Tuple, Optional
from .git_database_manager import GitManager, DatabaseManager, VocabularyImporter
from .vocabulary_selector import VocabularySelector
from .text_generator_clean import TextGenerator
from .audio_generator import AudioGenerator
from .review_interface import create_review_session


class VocabularyApp:
    """Main application coordinator for vocabulary learning sessions."""
    
    def __init__(self, tracking_file_path: str = None):
        # Initialize tracking file path
        if tracking_file_path is None:
            tracking_file_path = os.path.join(os.getcwd(), "data", "word_tracking.json")
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(tracking_file_path), exist_ok=True)
        
        # Initialize components
        self.git_manager = GitManager()
        self.database_manager = DatabaseManager(tracking_file_path)
        self.vocabulary_selector = VocabularySelector(self.database_manager)
        self.vocabulary_importer = VocabularyImporter(self.database_manager)
        
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
    
    def import_vocabulary_from_file(self, file_path: str) -> int:
        """
        Import vocabulary from a file to the database.
        
        Args:
            file_path: Path to the vocabulary file (CSV/XLSX)
        
        Returns:
            int: Number of new words imported
        """
        try:
            return self.vocabulary_importer.import_from_file(file_path)
        except Exception as e:
            print(f"❌ Error importing vocabulary: {e}")
            return 0
    
    def import_vocabulary_from_downloads(self) -> int:
        """
        Import vocabulary from the latest Favorites file in Downloads.
        
        Returns:
            int: Number of new words imported
        """
        try:
            return self.vocabulary_importer.import_from_downloads()
        except Exception as e:
            print(f"❌ Error importing from downloads: {e}")
            print("\n📋 To import vocabulary:")
            print("1. Export your Reverso favorites as CSV")
            print("2. Save it in your Downloads folder")
            print("3. Run import again")
            return 0
    
    def get_vocabulary_count(self) -> int:
        """Get the total number of words in the database."""
        return len(self.database_manager.get_all_words())
    
    def run_learning_session(self, 
                           random_sample_size: int = 40,
                           final_selection_size: int = 20,
                           language: str = "French",
                           generate_audio: bool = True,
                           import_from_downloads: bool = False,
                           progress_callback=None) -> dict:
        """
        Run a complete vocabulary learning session.
        
        Args:
            random_sample_size: Size of random sample for priority calculation
            final_selection_size: Final number of words to select
            language: Language for text generation
            generate_audio: Whether to generate audio
            import_from_downloads: Whether to import new vocabulary first
            progress_callback: Optional callback function for progress updates
        
        Returns:
            dict: Session results with selected_words, story, audio_path, and session_word_updates
        """
        
        if progress_callback:
            progress_callback("🚀 Starting vocabulary learning session...")
        
        # Import new vocabulary if requested
        if import_from_downloads:
            if progress_callback:
                progress_callback("📥 Importing new vocabulary...")
            imported_count = self.import_vocabulary_from_downloads()
            if imported_count > 0 and progress_callback:
                progress_callback(f"✅ Imported {imported_count} new words")
        
        # Check if we have enough vocabulary
        vocab_count = self.get_vocabulary_count()
        if progress_callback:
            progress_callback(f"📊 Database contains {vocab_count} words")
        
        if vocab_count < final_selection_size:
            if progress_callback:
                progress_callback(f"❌ Not enough vocabulary words. Need at least {final_selection_size}, have {vocab_count}")
            return {"selected_words": [], "story": "", "audio_path": "", "session_word_updates": []}
        
        # Select words using priority system
        if progress_callback:
            progress_callback(f"🎯 Selecting {final_selection_size} words from {random_sample_size} random candidates...")
        
        selected_words = self.vocabulary_selector.select_words_for_session(
            random_sample_size, final_selection_size
        )
        
        if not selected_words:
            if progress_callback:
                progress_callback("❌ No words selected")
            return {"selected_words": [], "story": "", "audio_path": "", "session_word_updates": []}
        
        if progress_callback:
            progress_callback(f"✅ Selected {len(selected_words)} words for the session")
        
        # Instead of marking words as used (which persists), collect intended updates in memory
        session_word_updates = []
        for word, translation, _ in selected_words:
            session_word_updates.append({
                "word": word,
                "translation": translation,
                "repeat": False,  # Not repeated, just used in session
            })
        
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
        
        return {
            "selected_words": selected_words,
            "story": generated_text,
            "audio_path": audio_path,
            "session_word_updates": session_word_updates
        }
    
    def _save_selected_words(self, selected_words: List[Tuple[str, str, str]], progress_callback=None):
        """Save the selected vocabulary words to a JSON file for later use."""
        try:
            words_path = os.path.join(tempfile.gettempdir(), "infiniling_words.json")
            
            # Convert tuples to dictionaries for JSON serialization
            words_data = []
            for word, translation, pronunciation in selected_words:
                words_data.append({
                    "word": word,
                    "translation": translation,
                    "pronunciation": pronunciation or ""
                })
            
            # Save to JSON file
            with open(words_path, 'w', encoding='utf-8') as f:
                json.dump(words_data, f, indent=2, ensure_ascii=False)
            
            if progress_callback:
                progress_callback(f"💾 Saved {len(selected_words)} vocabulary words")
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"⚠️ Could not save vocabulary words: {e}")
            print(f"Error saving vocabulary words: {e}")

    def _load_saved_words(self, progress_callback=None) -> List[Tuple[str, str, str]]:
        """Load the saved vocabulary words from JSON file."""
        try:
            words_path = os.path.join(tempfile.gettempdir(), "infiniling_words.json")
            
            if not os.path.exists(words_path):
                if progress_callback:
                    progress_callback("⚠️ No saved vocabulary words found")
                return []
            
            with open(words_path, 'r', encoding='utf-8') as f:
                words_data = json.load(f)
            
            # Convert dictionaries back to tuples
            selected_words = []
            for word_info in words_data:
                word = word_info.get("word", "")
                translation = word_info.get("translation", "")
                pronunciation = word_info.get("pronunciation", "")
                selected_words.append((word, translation, pronunciation))
            
            if progress_callback:
                progress_callback(f"📚 Loaded {len(selected_words)} vocabulary words")
            
            return selected_words
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"⚠️ Error loading vocabulary words: {e}")
            print(f"Error loading vocabulary words: {e}")
            return []

    def load_last_session(self, progress_callback=None) -> dict:
        """
        Load the last generated text and audio files.
        
        Args:
            progress_callback: Optional callback function for progress updates
        
        Returns:
            dict: Session results with story and audio_path, or empty if not found
        """
        if progress_callback:
            progress_callback("📂 Loading last session...")
        
        # Check for saved text file
        text_path = os.path.join(tempfile.gettempdir(), "infiniling_text.txt")
        generated_text = ""
        
        if os.path.exists(text_path):
            try:
                with open(text_path, 'r', encoding='utf-8') as f:
                    generated_text = f.read()
                if progress_callback:
                    progress_callback("✅ Last text loaded successfully")
            except Exception as e:
                if progress_callback:
                    progress_callback(f"❌ Error loading text file: {e}")
                generated_text = ""
        else:
            if progress_callback:
                progress_callback("❌ No saved text found")
        
        # Check for saved audio file
        audio_path = os.path.join(tempfile.gettempdir(), "infiniling_audio.mp3")
        if not os.path.exists(audio_path):
            audio_path = ""
            if progress_callback:
                progress_callback("⚠️ No saved audio found")
        else:
            if progress_callback:
                progress_callback("✅ Last audio found")
        
        # Load saved vocabulary words
        saved_words = self._load_saved_words(progress_callback)
        
        return {
            "selected_words": saved_words,  # Load saved vocabulary words for review
            "story": generated_text,
            "audio_path": audio_path
        }
    
    def get_database_statistics(self) -> dict:
        """Get statistics about the vocabulary database."""
        word_stats = self.database_manager.word_stats
        
        if not word_stats:
            return {
                'total_words': 0,
                'words_with_occurrences': 0,
                'words_never_reviewed': 0,
                'words_marked_difficult': 0
            }
        
        words_with_occurrences = 0
        words_never_reviewed = 0
        words_marked_difficult = 0
        
        for word_key, stats in word_stats.items():
            occurrences = stats.get('occurrences', [])
            if occurrences:
                words_with_occurrences += 1
                # Check if any occurrence was marked as difficult
                if any(occ.get('repeat', False) for occ in occurrences if isinstance(occ, dict)):
                    words_marked_difficult += 1
            else:
                words_never_reviewed += 1
        
        return {
            'total_words': len(word_stats),
            'words_with_occurrences': words_with_occurrences,
            'words_never_reviewed': words_never_reviewed,
            'words_marked_difficult': words_marked_difficult
        }
    
    def print_database_statistics(self):
        """Print database statistics to console."""
        stats = self.get_database_statistics()
        
        print("\n📊 Vocabulary Database Statistics:")
        print(f"   Total words: {stats['total_words']}")
        print(f"   Words reviewed: {stats['words_with_occurrences']}")
        print(f"   Words never reviewed: {stats['words_never_reviewed']}")
        print(f"   Words marked difficult: {stats['words_marked_difficult']}")
        
        if stats['total_words'] > 0:
            review_percentage = (stats['words_with_occurrences'] / stats['total_words']) * 100
            print(f"   Review coverage: {review_percentage:.1f}%")


def main():
    """Main entry point for the application."""
    app = VocabularyApp()
    
    # Print current database statistics
    app.print_database_statistics()
    
    # Run a learning session
    success = app.run_learning_session(
        random_sample_size=40,
        final_selection_size=20,
        language="French",
        generate_audio=True,
        import_from_downloads=True
    )
    
    if success:
        print("\n🎉 Session completed successfully!")
    else:
        print("\n❌ Session failed or was cancelled")


if __name__ == "__main__":
    main()
