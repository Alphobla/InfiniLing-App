"""
SQLAlchemy Database Models for Vocabulary Management

This module defines the database schema for the vocabulary learning system,
designed to be compatible with the existing selector.py spaced repetition algorithm.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional
from contextlib import contextmanager
import csv
import os

Base = declarative_base()


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
    translation = Column(String(255), nullable=False)
    language_from = Column(String(10), nullable=False, default='fr')
    language_to = Column(String(10), nullable=False, default='de')
    
    # Optional metadata from GPT translation
    primary_translation = Column(String(255))
    secondary_translation = Column(String(255))
    context_translation = Column(String(255))
    part_of_speech = Column(String(50))
    pronunciation = Column(String(255))  # Compatible with existing JSON
    
    # Example sentence (one per word)
    example_sentence_original = Column(Text)
    example_sentence_translation = Column(Text)
    example_sentence_source = Column(String(50), default='tatoeba')  # 'tatoeba', 'manual', 'gpt', etc.
    example_sentence_source_id = Column(String(50))  # External ID from source
    
    # Frequency analysis data
    frequency_rank = Column(Integer)
    frequency_level = Column(String(50))  # 'very_common', 'common', 'uncommon', etc.
    
    # Timestamps
    date_added = Column(DateTime, default=datetime.utcnow)
    date_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    that uses an 'occurrences' array with 'date' and 'repeat' fields.
    """
    __tablename__ = 'vocabulary_occurrences'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    vocabulary_id = Column(Integer, ForeignKey('vocabulary.id'), nullable=False)
    
    # Core tracking data (compatible with existing JSON structure)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    repeat = Column(Boolean, default=False, nullable=False)  # True if word was difficult
    
    # Spaced repetition data (scientific algorithm)
    feedback_score = Column(Integer)  # 1-5 performance score
    easiness_factor = Column(Float, default=2.5)  # SM-2 easiness factor
    interval_days = Column(Integer, default=1)  # Current interval in days
    repetitions = Column(Integer, default=0)  # Number of successful repetitions
    next_review_date = Column(DateTime)  # Next review date based on algorithm
    successful_reviews = Column(Integer, default=0)  # Count of successful reviews
    
    # Relationships
    vocabulary = relationship("Vocabulary", back_populates="occurrences")
    
    def __repr__(self):
        return f"<VocabularyOccurrence(vocab_id={self.vocabulary_id}, date={self.date}, repeat={self.repeat})>"


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
        # Default to SQLite database in the project directory
        import os
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vocabulary.db')
        database_url = f'sqlite:///{db_path}'
    
    engine = create_engine(database_url, echo=False)
    return engine


class DatabaseManager:
    """
    Simple database manager for vocabulary operations.
    
    Handles database connection, session management, and basic operations.
    """
    
    def __init__(self, database_url: str = None):
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
    def add_word(self, word: str, translation: str, language_from: str = 'fr', language_to: str = 'de', **kwargs):
        """Add a new vocabulary word to the database."""
        with self.session_scope() as session:
            vocab = Vocabulary(
                word=word,
                translation=translation,
                language_from=language_from,
                language_to=language_to,
                **kwargs
            )
            session.add(vocab)
            return vocab
    
    def get_word(self, word_id: int):
        """Get a vocabulary word by ID."""
        with self.session_scope() as session:
            return session.query(Vocabulary).filter(Vocabulary.id == word_id).first()
    
    def get_all_words(self):
        """Get all vocabulary words."""
        with self.session_scope() as session:
            words = session.query(Vocabulary).all()
            session.expunge_all()  # Detach all objects from session
            return words
    
    def add_occurrence(self, vocabulary_id: int, repeat: bool = False):
        """Add an occurrence record for a vocabulary word."""
        with self.session_scope() as session:
            occurrence = VocabularyOccurrence(
                vocabulary_id=vocabulary_id,
                repeat=repeat
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
            
    def get_old_word_occurrences(self, vocabulary_id: int):
        """Get all occurrences for a vocabulary word from the old table structure."""
        with self.session_scope() as session:
            return session.query(VocabularyOccurrenceOld).filter(
                VocabularyOccurrenceOld.vocabulary_id == vocabulary_id
            ).all()
    
    def import_vocabulary_from_csv(self, csv_file_path: str, language_from: str = 'fr', language_to: str = 'de'):
        """
        Import vocabulary from a CSV file.
        
        Args:
            csv_file_path: Path to the CSV file
            language_from: Source language (default: 'fr')
            language_to: Target language (default: 'de')
        
        Returns:
            dict: Import results with counts
        """
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        results = {
            'total_rows': 0,
            'imported': 0,
            'skipped': 0,
            'errors': 0,
            'error_details': []
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
                        results['skipped'] += 1
                        continue
                    
                    # Check if word already exists
                    with self.session_scope() as session:
                        existing_word = session.query(Vocabulary).filter(
                            Vocabulary.word == word,
                            Vocabulary.translation == translation,
                            Vocabulary.language_from == language_from,
                            Vocabulary.language_to == language_to
                        ).first()
                        
                        if existing_word:
                            results['skipped'] += 1
                            continue
                        
                        # Add new word
                        vocab = Vocabulary(
                            word=word,
                            translation=translation,
                            language_from=language_from,
                            language_to=language_to
                        )
                        session.add(vocab)
                        results['imported'] += 1
                        
                except Exception as e:
                    results['errors'] += 1
                    results['error_details'].append(f"Row {results['total_rows']}: {str(e)}")
        
        return results


if __name__ == "__main__":
    # Test database creation
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    print("Database schema created successfully!")