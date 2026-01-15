"""
Scientific Spaced Repetition Selector

This module implements a modern spaced repetition algorithm (based on SM-2)
that works seamlessly with our SQLite database structure with spaced repetition
data stored directly in the VocabularyOccurrence table.

Key features:
- SM-2 algorithm for optimal review intervals
- Database integration for word selection and tracking
- Proper difficulty adjustment based on performance
- Review scheduling based on forgetting curves
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from src.shared.database_models import DatabaseManager, Vocabulary, VocabularyOccurrence


class SpacedRepetitionSelector:
    """
    Scientific spaced repetition selector using SM-2 algorithm.
    
    The SM-2 algorithm adjusts review intervals based on:
    - Performance on previous reviews
    - Easiness factor (difficulty adjustment)
    - Forgetting curve optimization
    """
    
    def __init__(self, database_manager: DatabaseManager):
        """Initialize the selector with database manager."""
        self.db_manager = database_manager
        
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
    
    def get_word_current_state(self, word_id: int) -> Tuple[float, int, int, Optional[datetime]]:
        """
        Get current spaced repetition state for a word from the latest occurrence.
        
        Args:
            word_id: ID of the word
        
        Returns:
            Tuple of (easiness_factor, repetitions, interval_days, last_review_date)
        """
        occurrences = self.db_manager.get_word_occurrences(word_id)
        
        if not occurrences:
            # New word - no reviews yet
            return (self.initial_easiness, 0, 0, None)
        
        # Get the most recent occurrence
        latest_occ = max(occurrences, key=lambda x: x.date)
        
        return (
            latest_occ.easiness_factor or self.initial_easiness,
            latest_occ.repetitions or 0,
            latest_occ.interval_days or 1,
            latest_occ.date
        )
    
    def get_next_review_date(self, word_id: int) -> datetime:
        """
        Calculate when a word should be reviewed next.

        Args:
            word_id: ID of the word

        Returns:
            Next review date
        """
        easiness_factor, repetitions, interval_days, last_review = self.get_word_current_state(word_id)

        if last_review is None:
            # New word - due immediately (use min datetime to ensure it's always in the past)
            return datetime.min

        return last_review + timedelta(days=interval_days)
    
    def get_due_words(self, limit: int = 20) -> List[Dict]:
        """
        Get words that are due for review.
        
        Args:
            limit: Maximum number of words to return
        
        Returns:
            List of word dictionaries sorted by urgency
        """
        all_words = self.db_manager.get_all_words()
        due_words = []
        now = datetime.now()
        
        for word in all_words:
            next_review = self.get_next_review_date(word.id)
            if next_review <= now:
                word.next_review = next_review  # Add as attribute
                due_words.append(word)
        
        # Sort by urgency (most overdue first)
        due_words.sort(key=lambda w: w.next_review)
        
        return due_words[:limit]
    
    def get_new_words(self, limit: int = 5) -> List[Dict]:
        """
        Get new words that haven't been reviewed yet.
        
        Args:
            limit: Maximum number of new words to return
        
        Returns:
            List of word dictionaries for new words
        """
        all_words = self.db_manager.get_all_words()
        new_words = []
        
        for word in all_words:
            occurrences = self.db_manager.get_word_occurrences(word.id)
            if not occurrences:
                new_words.append(word)
        
        # Randomize new words to avoid always getting the same ones
        random.shuffle(new_words)
        return new_words[:limit]
    
    def select_words_for_review(self, target_count: int = 20, new_word_ratio: float = 0.2) -> List[Dict]:
        """
        Select words for review session combining due words and new words.
        
        Args:
            target_count: Target number of words for review
            new_word_ratio: Ratio of new words to include (0.0 to 1.0)
        
        Returns:
            List of word dictionaries for review session
        """
        new_word_count = int(target_count * new_word_ratio)
        due_word_count = target_count - new_word_count
        
        # Get due words and new words
        due_words = self.get_due_words(due_word_count)
        new_words = self.get_new_words(new_word_count)
        
        # Combine and shuffle
        review_words = due_words + new_words
        random.shuffle(review_words)
        
        return review_words[:target_count]
    
    def mark_word_reviewed(self, word_id: int, feedback_score: int) -> None:
        """
        Mark a word as reviewed and update spaced repetition parameters.
        
        Args:
            word_id: ID of the reviewed word
            feedback_score: Performance score 0-5 (0=total failure, 5=perfect)
        """
        if not (0 <= feedback_score <= 5):
            raise ValueError("feedback_score must be between 0 and 5")
        
        # Get current state
        current_ef, current_reps, current_interval, last_review = self.get_word_current_state(word_id)
        
        # Calculate new parameters
        new_ef = self.calculate_easiness_factor(current_ef, feedback_score)
        
        # Determine success/failure and update repetitions
        success = feedback_score >= 3  # 3, 4, 5 are considered successful
        if success:
            new_reps = current_reps + 1
        else:
            new_reps = 0  # Reset on failure
        
        # Calculate new interval
        new_interval = self.calculate_next_interval(new_reps, new_ef, current_interval)
        
        # Create new occurrence with all spaced repetition data
        with self.db_manager.session_scope() as session:
            occurrence = VocabularyOccurrence(
                vocabulary_id=word_id,
                date=datetime.now(),
                feedback_score=feedback_score,
                easiness_factor=new_ef,
                interval_days=new_interval,
                repetitions=new_reps
            )
            session.add(occurrence)
    
    def get_review_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the current review state.
        
        Returns:
            Dictionary with review statistics
        """
        all_words = self.db_manager.get_all_words()
        
        total_words = len(all_words)
        new_words = 0
        due_words = 0
        future_words = 0
        
        now = datetime.now()
        
        for word in all_words:
            occurrences = self.db_manager.get_word_occurrences(word.id)
            
            if not occurrences:
                new_words += 1
            else:
                next_review = self.get_next_review_date(word.id)
                if next_review <= now:
                    due_words += 1
                else:
                    future_words += 1
        
        return {
            'total_words': total_words,
            'new_words': new_words,
            'due_words': due_words,
            'future_words': future_words
        }
    
