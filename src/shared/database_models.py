"""
SQLAlchemy Database Models for Vocabulary Management

This module defines the database schema for the vocabulary learning system,
designed to be compatible with the existing selector.py spaced repetition algorithm.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text, Index
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from src.shared.frequency_analysis import get_word_frequency_category, get_word_frequency_rank
from datetime import datetime, timezone
from typing import Optional
from contextlib import contextmanager
import csv
import os

Base = declarative_base()


def utc_now():
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class Vocabulary(Base):
    """
    Core vocabulary table storing word pairs and metadata.
    
    This table maintains compatibility with the existing JSON structure:
    - word: The source word
    - translation: The target translation
    - language_from/language_to: Language pair
    - The unique constraint ensures no duplicate word-translation pairs
    """
    __tablename__ = 'vocabulary'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(255), nullable=False, index=True)
    original_word = Column(String(255), nullable=False, index=True)  # Original word in source language
    translation = Column(String(255), nullable=False)
    language_from = Column(String(10), nullable=False)
    language_to = Column(String(10), nullable=False)  # No default - must be explicitly set
    
    # Optional metadata from GPT translation
    primary_translation = Column(String(255))
    secondary_translation = Column(String(255))
    pronunciation = Column(String(255))  # Compatible with existing JSON
    
    # Example sentence (one per word)
    example_sentence_original = Column(Text)
    example_sentence_translation = Column(Text)
    
    # Frequency analysis data
    frequency_rank = Column(Integer)
    frequency_level = Column(String(50))  # 'very_common', 'common', 'uncommon', etc.
    
    # Timestamps
    date_added = Column(DateTime, default=utc_now)
    date_modified = Column(DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationships
    occurrences = relationship("VocabularyOccurrence", back_populates="vocabulary", cascade="all, delete-orphan")
    
    # Unique constraint to prevent duplicate word-translation pairs
    __table_args__ = (
        Index('idx_word_translation_lang', 'word', 'translation', 'language_from', 'language_to', unique=True),
    )
    
    def __repr__(self):
        return f"<Vocabulary(word='{self.word}', translation='{self.translation}')>"


class VocabularyOccurrence(Base):
    """
    Tracks individual interactions with vocabulary words.
    
    This table is designed to be compatible with the existing selector.py algorithm
    that uses an 'occurrences' array with 'date'  fields.
    """
    __tablename__ = 'vocabulary_occurrences'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    vocabulary_id = Column(Integer, ForeignKey('vocabulary.id'), nullable=False)
    
    # Core tracking data (compatible with existing JSON structure)
    date = Column(DateTime, default=utc_now, nullable=False)
    
    # Spaced repetition data (scientific algorithm)
    feedback_score = Column(Integer)  # 0-5 performance score
    easiness_factor = Column(Float, default=2.5)  # SM-2 easiness factor
    interval_days = Column(Integer, default=1)  # Current interval in days
    repetitions = Column(Integer, default=0)  # Number of successful repetitions
    next_review_date = Column(DateTime)  # Next review date based on algorithm
    successful_reviews = Column(Integer, default=0)  # Count of successful reviews
    
    # Relationships
    vocabulary = relationship("Vocabulary", back_populates="occurrences")
    
    def __repr__(self):
        return f"<VocabularyOccurrence(vocab_id={self.vocabulary_id}, date={self.date}, feedback_score={self.feedback_score})>"


def create_database_engine(database_url: str = None):
    """
    Create a SQLAlchemy engine for the vocabulary database.
    
    Args:
        database_url: Database connection URL. If None, creates a SQLite database
                     in the default location.
    
    Returns:
        SQLAlchemy engine instance
    """
    if database_url is None:
        # Default to SQLite database in the user's home directory
        # This ensures it's writable even when the app is packaged
        home = os.path.expanduser('~')
        db_dir = os.path.join(home, '.infiniling')
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, 'vocabulary.db')
        database_url = f'sqlite:///{db_path}'
    
    engine = create_engine(database_url, echo=False)
    return engine


class DatabaseManager:
    """
    Simple database manager for vocabulary operations.
    
    Handles database connection, session management, and basic operations.
    """
    
    def __init__(self, database_url: str = "sqlite:///./src/vocabulary.db"):
        """Initialize database manager with connection."""
        print(f"Initializing database manager with URL: {database_url}")
        self.engine = create_database_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def initialize_database(self):
        """Create all database tables."""
        Base.metadata.create_all(self.engine)
        
    def get_session(self):
        """Get a new database session."""
        return self.SessionLocal()
        
    @contextmanager
    def session_scope(self):
        """Context manager for database sessions with automatic cleanup."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    # CRUD Operations
    def add_word(self, word: str, translation: str, language_from: str = None, language_to: str = None, **kwargs):
        """Add a new vocabulary word to the database."""
        with self.session_scope() as session:
            vocab = Vocabulary(
                word=word,
                original_word=word,  # Store original word
                translation=translation,
                language_from=language_from,
                language_to=language_to,
                **kwargs
            )
            session.add(vocab)
            session.flush()  # Get the ID
            session.expunge(vocab)  # Detach from session so it's usable after
            return vocab
    
    def get_word(self, word_id: int):
        """Get a vocabulary word by ID."""
        with self.session_scope() as session:
            word = session.query(Vocabulary).filter(Vocabulary.id == word_id).first()
            if word:
                session.expunge(word)  # Detach from session so it's usable after
            return word
    
    def get_id_by_string(self, word_text: str):
        """Get a vocabulary word by its text."""
        with self.session_scope() as session:
            word = session.query(Vocabulary).filter(Vocabulary.word == word_text).first()
            if word:
                session.expunge(word)  # Detach from session
            return word
    
    def get_all_words(self):
        """Get all vocabulary words."""
        with self.session_scope() as session:
            words = session.query(Vocabulary).all()
            session.expunge_all()  # Detach all objects from session
            return words

    def get_language_counts(self):
        """Get count of words per source language."""
        with self.session_scope() as session:
            from sqlalchemy import func
            results = session.query(
                Vocabulary.language_from,
                func.count(Vocabulary.id)
            ).group_by(Vocabulary.language_from).all()
            return {lang: count for lang, count in results if lang}

    def get_words_by_language(self, language_from):
        """Get all words for a specific source language."""
        with self.session_scope() as session:
            words = session.query(Vocabulary).filter(
                Vocabulary.language_from == language_from
            ).all()
            # Detach from session
            for word in words:
                session.expunge(word)
            return words

    def delete_word(self, word_id: int) -> bool:
        """Delete a vocabulary word by ID.

        Args:
            word_id: ID of the word to delete

        Returns:
            True if deleted, False if not found
        """
        with self.session_scope() as session:
            word = session.query(Vocabulary).filter(Vocabulary.id == word_id).first()
            if not word:
                return False
            session.delete(word)
            return True

    def update_word(self, word_id: int, **kwargs) -> bool:
        """Update a vocabulary word's fields.

        Args:
            word_id: ID of the word to update
            **kwargs: Fields to update (word, translation, etc.)

        Returns:
            True if updated, False if not found
        """
        with self.session_scope() as session:
            word = session.query(Vocabulary).filter(Vocabulary.id == word_id).first()
            if not word:
                return False

            for key, value in kwargs.items():
                if hasattr(word, key):
                    setattr(word, key, value)

            word.date_modified = utc_now()
            return True

    def add_occurrence(self, vocabulary_id: int, feedback_score: int):
        """Add an occurrence record for a vocabulary word."""
        with self.session_scope() as session:
            occurrence = VocabularyOccurrence(
                vocabulary_id=vocabulary_id,
                feedback_score=feedback_score
            )
            session.add(occurrence)
            return occurrence
    
    def get_word_occurrences(self, vocabulary_id: int):
        """Get all occurrences for a vocabulary word."""
        with self.session_scope() as session:
            occurences=session.query(VocabularyOccurrence).filter(
                VocabularyOccurrence.vocabulary_id == vocabulary_id
            ).all()
            session.expunge_all()
            return  occurences
            
    def import_vocabulary_from_csv(self, csv_file_path: str, language_from: str = None, language_to: str = None):
        """
        Import vocabulary from a CSV file.

        Args:
            csv_file_path: Path to the CSV file
            language_from: Source language (required)
            language_to: Target language (required)
        
        Returns:
            dict: Import results with counts
        """
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        results = {
            'total_rows': 0,
            'imported': 0,
        }
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                results['total_rows'] += 1
                
                try:
                    # Extract word and translation from CSV
                    word = row.get('source', '').strip()
                    translation = row.get('target', '').strip()
                    
                    # Skip empty rows
                    if not word or not translation:
                        continue
                    
                    # Check if word already exists (as word OR original_word)
                    with self.session_scope() as session:
                        existing_word = session.query(Vocabulary).filter(
                            (
                                (Vocabulary.word == word) | 
                                (Vocabulary.original_word == word)
                            ),
                            Vocabulary.language_from == language_from,
                            Vocabulary.language_to == language_to
                        ).first()
                        
                        if existing_word:
                            continue
                        
                        # Create vocabulary entry with original word as placeholder
                        vocab = Vocabulary(
                            word=word,  # Temporary placeholder, will be replaced during enhancement
                            original_word="empty",  # Store original word as entered
                            translation=translation,
                            language_from=language_from,
                            language_to=language_to
                        )
                        
                        # Enhance the word (normalization, frequency, examples)
                        vocab = self.enhance_word(word=vocab)
                        
                        session.add(vocab)
                        results['imported'] += 1
                        
                except Exception as e:
                    print(f"Row {results['total_rows']}: {str(e)}")
        
        return results

    def update_words(self, start_id: int = None, end_id: int = None) -> dict:
        """
        Re-enhance existing words from their original_word.
        
        Args:
            word_ids: Single ID or list of IDs
            start_id, end_id: ID range (inclusive)
        """
        # Determine target IDs
        target_ids = list(range(start_id, end_id + 1))
        
        results = {'updated': 0, 'errors': 0, 'not_found': 0}
        
        for word_id in target_ids:
            try:
                with self.session_scope() as session:
                    vocab = session.query(Vocabulary).filter(Vocabulary.id == word_id).first()
                    if not vocab:
                        results['not_found'] += 1
                        continue
                    
                    # Re-enhance and update
                    enhanced = self.enhance_word(vocab)
                    for attr in ['word', 'primary_translation', 'secondary_translation', 
                               'frequency_level', 'frequency_rank', 'example_sentence_original', 
                               'example_sentence_translation']:
                        setattr(vocab, attr, getattr(enhanced, attr))
                    vocab.date_modified = utc_now()  # Update modified date
                    
                    results['updated'] += 1
                    
            except Exception as e:
                results['errors'] += 1
                print(f"Error updating ID {word_id}: {e}")
        
        return results

    def get_due_days(self, vocabulary_id: int, new_word_due_days: int = 1) -> int:
        """
        Get the number of days until the next review for a vocabulary word.
        
        Args:
            vocabulary_id: ID of the vocabulary word
            new_word_due_days: Default days for new words with no occurrences
        
        Returns:
            int: Number of days until next review (always returns a number, never None)
        """
        with self.session_scope() as session:
            occurrences = session.query(VocabularyOccurrence).filter(
                VocabularyOccurrence.vocabulary_id == vocabulary_id
            ).order_by(VocabularyOccurrence.date.desc()).all()
            
            if not occurrences:
                return new_word_due_days
            
            last_occurrence = occurrences[0]
            now = datetime.utcnow()  # Use naive datetime to match SQLite storage
            
            # Try to use next_review_date first
            if last_occurrence.next_review_date:
                days = (last_occurrence.next_review_date - now).days
                return max(0, days)  # Don't return negative days (overdue = 0)
            
            # Fallback to interval_days if available
            if last_occurrence.interval_days:
                # Calculate days since last review + interval
                days_since = (now - last_occurrence.date).days
                remaining = last_occurrence.interval_days - days_since
                return max(0, remaining)
            
            # Final fallback
            return new_word_due_days

    def enhance_word(self, word: Vocabulary, api_key: str = None) -> Vocabulary:
        """
        Enhance a vocabulary word with normalized form, translations, examples, and frequency.
        
        Args:
            word: Vocabulary object to enhance
            api_key: OpenAI API key (if None, uses environment variable)
            
        Returns:
            Enhanced Vocabulary object or original if error
        """
        try:
            # Import here to avoid circular imports
            from .gpt_translator import GPTTranslator
            
            # Initialize translator
            if not api_key:
                import os
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.getenv('OPENAI_API_KEY')
            
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found. Set it in environment or pass as parameter.")
            
            translator = GPTTranslator(api_key)
            
            # Get GPT analysis using original word
            analysis = translator.normalize_and_translate(
                word.original_word,
                word.language_from,
                word.language_to,
                word.translation
            )
            
            if not analysis or not isinstance(analysis, dict):
                return word
                
            # Update word with normalized data
            root_word = analysis.get('root_word', word.original_word)
            word.word = root_word
            word.primary_translation = analysis.get("primary_translation", "")
            word.secondary_translation = analysis.get("secondary_translation")

            # Helper to strip articles and gender markers for lookups
            def strip_to_core_word(word_form):
                """Strip articles, gender markers, and extra formatting from word."""
                import re
                core = re.sub(r'\s*\([mf]\.\)$', '', word_form)
                return core.strip()

            # Add frequency data (use stripped word - wordfreq won't find "chien (m.)")
            core_word = strip_to_core_word(root_word)
            frequency = get_word_frequency_category(core_word, word.language_from)
            word.frequency_level = frequency.get('level')
            word.frequency_rank = frequency.get('rank')
            
            return word
            
        except Exception as e:
            raise RuntimeError(f"Error enhancing word '{word.original_word}': {e}") from e

if __name__ == "__main__":
    # Test database creation
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    print("Database schema created successfully!")