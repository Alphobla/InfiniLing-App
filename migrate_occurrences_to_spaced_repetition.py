#!/usr/bin/env python3
"""
Migration script to transfer old occurrence data to new database structure with spaced repetition data.

This script reads the existing database with old occurrence structure and creates a new database
with spaced repetition data calculated and stored in each occurrence record.
"""

import os
import shutil
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.shared.database_models import DatabaseManager, Vocabulary, VocabularyOccurrence, VocabularyOccurrenceOld, OldBase


class OldDatabaseManager:
    """
    Database manager for old database structure (for migration only).
    """
    
    def __init__(self, database_url: str):
        """Initialize database manager with connection."""
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    @contextmanager
    def session_scope(self):
        """Context manager for database sessions with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_all_words(self):
        """Get all vocabulary words from old database."""
        with self.session_scope() as session:
            words = session.query(Vocabulary).all()
            # Force loading of attributes to avoid detached instance issues
            result = []
            for word in words:
                result.append({
                    'id': word.id,
                    'word': word.word,
                    'translation': word.translation,
                    'pronunciation': word.pronunciation,
                    'language_from': word.language_from,
                    'language_to': word.language_to
                })
            return result
    
    def get_old_word_occurrences(self, vocabulary_id: int):
        """Get all occurrences for a vocabulary word from the old table structure."""
        with self.session_scope() as session:
            occurrences = session.query(VocabularyOccurrenceOld).filter(
                VocabularyOccurrenceOld.vocabulary_id == vocabulary_id
            ).all()
            
            # Extract data while session is active to avoid detached instance issues
            result = []
            for occ in occurrences:
                result.append({
                    'id': occ.id,
                    'vocabulary_id': occ.vocabulary_id,
                    'date': occ.date,
                    'repeat': occ.repeat,
                    'response_time_ms': occ.response_time_ms,
                    'session_id': occ.session_id
                })
            return result


class SpacedRepetitionMigrator:
    """
    Migrates old occurrence data to new spaced repetition structure.
    """
    
    def __init__(self):
        # SM-2 Algorithm parameters
        self.initial_interval = 1  # First review after 1 day
        self.second_interval = 6   # Second review after 6 days
        self.min_easiness = 1.3    # Minimum easiness factor
        self.initial_easiness = 2.5  # Starting easiness factor
    
    def calculate_easiness_factor(self, current_ef: float, performance_score: int) -> float:
        """
        Calculate new easiness factor based on performance (SM-2 algorithm).
        
        Args:
            current_ef: Current easiness factor
            performance_score: 1-5 scale (1=total failure, 5=perfect)
        
        Returns:
            New easiness factor
        """
        # SM-2 formula: EF' = EF + (0.1 - (5-q)*(0.08+(5-q)*0.02))
        new_ef = current_ef + (0.1 - (5 - performance_score) * (0.08 + (5 - performance_score) * 0.02))
        return max(new_ef, self.min_easiness)
    
    def calculate_next_interval(self, repetitions: int, easiness_factor: float, current_interval: int) -> int:
        """
        Calculate next review interval in days (SM-2 algorithm).
        
        Args:
            repetitions: Number of successful repetitions
            easiness_factor: Current easiness factor
            current_interval: Current interval in days
        
        Returns:
            Next review interval in days
        """
        if repetitions == 0:
            return self.initial_interval
        elif repetitions == 1:
            return self.second_interval
        else:
            # For repetitions >= 2: interval = previous_interval * easiness_factor
            return int(current_interval * easiness_factor)
    
    def migrate_word_occurrences(self, old_db: OldDatabaseManager, new_db: DatabaseManager, word_id: int) -> None:
        """
        Migrate all occurrences for a single word, calculating spaced repetition data.
        
        Args:
            old_db: Old database manager
            new_db: New database manager
            word_id: ID of the word to migrate
        """
        # Get old occurrences
        old_occurrences = old_db.get_old_word_occurrences(word_id)
        
        if not old_occurrences:
            return
        
        # Sort by date to process in chronological order
        old_occurrences.sort(key=lambda x: x['date'])
        
        # Initialize spaced repetition state
        current_ef = self.initial_easiness
        current_reps = 0
        current_interval = 0
        
        # Process each occurrence
        for occ in old_occurrences:
            # Convert old repeat boolean to feedback score
            # This is a simplified conversion - in reality, you might have more nuanced data
            if occ['repeat']:
                feedback_score = 2  # Poor performance
                performance_score = 2
            else:
                feedback_score = 4  # Good performance
                performance_score = 4
            
            # Calculate new spaced repetition parameters
            new_ef = self.calculate_easiness_factor(current_ef, performance_score)
            
            # Determine success/failure and update repetitions
            success = feedback_score >= 3  # 3, 4, 5 are considered successful
            if success:
                new_reps = current_reps + 1
            else:
                new_reps = 0  # Reset on failure
            
            # Calculate new interval
            new_interval = self.calculate_next_interval(new_reps, new_ef, current_interval)
            
            # Create new occurrence with spaced repetition data
            with new_db.session_scope() as session:
                new_occurrence = VocabularyOccurrence(
                    vocabulary_id=word_id,
                    date=occ['date'],
                    repeat=occ['repeat'],
                    feedback_score=feedback_score,
                    easiness_factor=new_ef,
                    interval_days=new_interval,
                    repetitions=new_reps,
                )
                session.add(new_occurrence)
            
            # Update state for next iteration
            current_ef = new_ef
            current_reps = new_reps
            current_interval = new_interval
    
    def migrate_database(self, old_db_path: str = None, new_db_path: str = None) -> bool:
        """
        Migrate entire database from old structure to new structure.
        
        Args:
            old_db_path: Path to old database (if None, uses default)
            new_db_path: Path to new database (if None, uses default with '_new' suffix)
        
        Returns:
            True if migration successful, False otherwise
        """
        try:
            # Set up database paths
            if old_db_path is None:
                old_db_path = "src/vocabulary.db"
                old_db_path = os.path.abspath(old_db_path)
            if new_db_path is None:
                new_db_path = "src/vocabulary_new.db"
                new_db_path = os.path.abspath(new_db_path)
            
            # Check if old database exists
            if not os.path.exists(old_db_path):
                print(f"Error: Old database not found at {old_db_path}")
                return False
            
            # Remove new database if it exists
            if os.path.exists(new_db_path):
                os.remove(new_db_path)
                print(f"Removed existing new database: {new_db_path}")
            
            # Initialize database managers
            old_db = OldDatabaseManager(f"sqlite:///{old_db_path}")
            new_db = DatabaseManager(f"sqlite:///{new_db_path}")
            new_db.initialize_database()
            
            print("Starting occurrence migration...")
            
            # Get all words from old database
            old_words = old_db.get_all_words()
            print(f"Found {len(old_words)} words to migrate")
            
            migrated_words = 0
            migrated_occurrences = 0
            
            # Migrate each word
            for word_dict in old_words:
                # First, copy the word itself
                with new_db.session_scope() as session:
                    new_word = Vocabulary(
                        word=word_dict['word'],
                        translation=word_dict['translation'],
                        language_from=word_dict['language_from'],
                        language_to=word_dict['language_to'],
                        pronunciation=word_dict['pronunciation'],
                        # Copy other fields as needed
                    )
                    session.add(new_word)
                    session.flush()  # Get the ID
                    new_word_id = new_word.id
                
                # Get old occurrences count for progress
                old_occurrences = old_db.get_old_word_occurrences(word_dict['id'])
                if old_occurrences:
                    migrated_occurrences += len(old_occurrences)
                
                # Migrate occurrences for this word
                self.migrate_word_occurrences(old_db, new_db, new_word_id)
                
                migrated_words += 1
                
                # Progress indicator
                if migrated_words % 100 == 0:
                    print(f"Migrated {migrated_words} words...")
            
            print(f"\n=== Migration Summary ===")
            print(f"Total words migrated: {migrated_words}")
            print(f"Total occurrences migrated: {migrated_occurrences}")
            print(f"New database created: {new_db_path}")
            
            # Verify migration
            print(f"\n=== Verification ===")
            new_words = new_db.get_all_words()
            print(f"Words in new database: {len(new_words)}")
            
            # Sample verification
            if new_words:
                sample_word = new_words[0]
                sample_occurrences = new_db.get_word_occurrences(sample_word['id'])
                print(f"Sample word: {sample_word['word']} → {sample_word['translation']}")
                print(f"Sample occurrences: {len(sample_occurrences)}")
                
                if sample_occurrences:
                    latest_occ = max(sample_occurrences, key=lambda x: x.date)
                    print(f"Latest occurrence: EF={latest_occ.easiness_factor:.2f}, "
                          f"Reps={latest_occ.repetitions}, Interval={latest_occ.interval_days} days")
            
            return True
            
        except Exception as e:
            print(f"Migration failed: {e}")
            return False


def main():
    print("Spaced Repetition Migration Script")
    print("=" * 50)
    
    migrator = SpacedRepetitionMigrator()
    
    # Run migration
    success = migrator.migrate_database()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Test the new database with the updated spaced repetition selector")
        print("2. If everything works, replace the old database with the new one:")
        print("   - Backup old database: mv vocabulary.db vocabulary_old.db")
        print("   - Use new database: mv vocabulary_new.db vocabulary.db")
        print("3. Delete this migration script (it's no longer needed)")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above and try again.")


if __name__ == "__main__":
    main()