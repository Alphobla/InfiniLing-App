"""
Tests for the Spaced Repetition Selector (SM-2 Algorithm).

These tests verify that the core spaced repetition algorithm works correctly:
- Easiness factor calculations
- Interval calculations
- Word selection logic
"""

import pytest
from datetime import datetime, timedelta
from src.gentexter_mode.spaced_repetition_selector import SpacedRepetitionSelector
from src.shared.database_models import VocabularyOccurrence


class TestEasinessFactorCalculation:
    """Tests for the SM-2 easiness factor formula."""

    def test_perfect_score_increases_easiness(self, in_memory_db):
        """Perfect performance (5) should increase easiness factor."""
        selector = SpacedRepetitionSelector(in_memory_db)
        initial_ef = 2.5
        new_ef = selector.calculate_easiness_factor(initial_ef, performance_score=5)
        assert new_ef > initial_ef

    def test_poor_score_decreases_easiness(self, in_memory_db):
        """Poor performance (1) should decrease easiness factor."""
        selector = SpacedRepetitionSelector(in_memory_db)
        initial_ef = 2.5
        new_ef = selector.calculate_easiness_factor(initial_ef, performance_score=1)
        assert new_ef < initial_ef

    def test_easiness_never_below_minimum(self, in_memory_db):
        """Easiness factor should never go below 1.3 (min_easiness)."""
        selector = SpacedRepetitionSelector(in_memory_db)
        # Start with already low easiness and give worst score
        new_ef = selector.calculate_easiness_factor(1.3, performance_score=0)
        assert new_ef >= selector.min_easiness

    def test_medium_score_maintains_easiness(self, in_memory_db):
        """Score of 3 should roughly maintain easiness factor."""
        selector = SpacedRepetitionSelector(in_memory_db)
        initial_ef = 2.5
        new_ef = selector.calculate_easiness_factor(initial_ef, performance_score=3)
        # SM-2 formula: for score=3, change is small
        assert abs(new_ef - initial_ef) < 0.2


class TestIntervalCalculation:
    """Tests for review interval calculations."""

    def test_first_review_interval(self, in_memory_db):
        """First review should be after 1 day."""
        selector = SpacedRepetitionSelector(in_memory_db)
        interval = selector.calculate_next_interval(repetitions=0, easiness_factor=2.5, current_interval=0)
        assert interval == 1

    def test_second_review_interval(self, in_memory_db):
        """Second review should be after 6 days."""
        selector = SpacedRepetitionSelector(in_memory_db)
        interval = selector.calculate_next_interval(repetitions=1, easiness_factor=2.5, current_interval=1)
        assert interval == 6

    def test_subsequent_intervals_increase(self, in_memory_db):
        """Subsequent intervals should be multiplied by easiness factor."""
        selector = SpacedRepetitionSelector(in_memory_db)
        easiness = 2.5
        current_interval = 6
        new_interval = selector.calculate_next_interval(repetitions=2, easiness_factor=easiness, current_interval=current_interval)
        expected = int(current_interval * easiness)
        assert new_interval == expected

    def test_higher_easiness_longer_intervals(self, in_memory_db):
        """Higher easiness factor should result in longer intervals."""
        selector = SpacedRepetitionSelector(in_memory_db)
        low_ef_interval = selector.calculate_next_interval(repetitions=3, easiness_factor=1.5, current_interval=10)
        high_ef_interval = selector.calculate_next_interval(repetitions=3, easiness_factor=2.5, current_interval=10)
        assert high_ef_interval > low_ef_interval


class TestWordCurrentState:
    """Tests for getting current word state from database."""

    def test_new_word_returns_defaults(self, populated_db):
        """New word with no occurrences should return default values."""
        selector = SpacedRepetitionSelector(populated_db)
        words = populated_db.get_all_words()
        word = words[0]

        ef, reps, interval, last_review = selector.get_word_current_state(word.id)

        assert ef == selector.initial_easiness
        assert reps == 0
        assert interval == 0
        assert last_review is None

    def test_reviewed_word_returns_latest_state(self, populated_db):
        """Word with occurrences should return state from latest occurrence."""
        selector = SpacedRepetitionSelector(populated_db)
        words = populated_db.get_all_words()
        word = words[0]

        # Add an occurrence
        with populated_db.session_scope() as session:
            occ = VocabularyOccurrence(
                vocabulary_id=word.id,
                date=datetime.now(),
                feedback_score=4,
                easiness_factor=2.8,
                interval_days=6,
                repetitions=2
            )
            session.add(occ)

        ef, reps, interval, last_review = selector.get_word_current_state(word.id)

        assert ef == 2.8
        assert reps == 2
        assert interval == 6
        assert last_review is not None


class TestMarkWordReviewed:
    """Tests for marking words as reviewed."""

    def test_valid_feedback_score(self, populated_db):
        """Valid feedback scores (0-5) should be accepted."""
        selector = SpacedRepetitionSelector(populated_db)
        words = populated_db.get_all_words()
        word = words[0]

        # Should not raise
        selector.mark_word_reviewed(word.id, feedback_score=3)

    def test_invalid_feedback_score_raises(self, populated_db):
        """Invalid feedback scores should raise ValueError."""
        selector = SpacedRepetitionSelector(populated_db)
        words = populated_db.get_all_words()
        word = words[0]

        with pytest.raises(ValueError):
            selector.mark_word_reviewed(word.id, feedback_score=6)

        with pytest.raises(ValueError):
            selector.mark_word_reviewed(word.id, feedback_score=-1)

    def test_successful_review_increments_reps(self, populated_db):
        """Successful review (score >= 3) should increment repetitions."""
        selector = SpacedRepetitionSelector(populated_db)
        words = populated_db.get_all_words()
        word = words[0]

        # First successful review
        selector.mark_word_reviewed(word.id, feedback_score=4)
        _, reps, _, _ = selector.get_word_current_state(word.id)
        assert reps == 1

        # Second successful review
        selector.mark_word_reviewed(word.id, feedback_score=5)
        _, reps, _, _ = selector.get_word_current_state(word.id)
        assert reps == 2

    def test_failed_review_resets_reps(self, populated_db):
        """Failed review (score < 3) should reset repetitions to 0."""
        selector = SpacedRepetitionSelector(populated_db)
        words = populated_db.get_all_words()
        word = words[0]

        # Build up some repetitions
        selector.mark_word_reviewed(word.id, feedback_score=5)
        selector.mark_word_reviewed(word.id, feedback_score=4)
        _, reps_before, _, _ = selector.get_word_current_state(word.id)
        assert reps_before == 2

        # Fail
        selector.mark_word_reviewed(word.id, feedback_score=2)
        _, reps_after, _, _ = selector.get_word_current_state(word.id)
        assert reps_after == 0


class TestDueWords:
    """Tests for word selection logic."""

    def test_new_words_are_due_immediately(self, populated_db):
        """New words (no occurrences) should be returned by get_due_words."""
        selector = SpacedRepetitionSelector(populated_db)
        due = selector.get_due_words()
        # All 3 words in populated_db have no occurrences, so all should be due
        assert len(due) == 3

    def test_get_new_words(self, populated_db):
        """Should return only words without any occurrences."""
        selector = SpacedRepetitionSelector(populated_db)

        # Initially all are new
        new_words = selector.get_new_words()
        assert len(new_words) == 3

        # Review one word
        words = populated_db.get_all_words()
        selector.mark_word_reviewed(words[0].id, feedback_score=4)

        # Now only 2 should be new
        new_words = selector.get_new_words()
        assert len(new_words) == 2


class TestReviewStatistics:
    """Tests for review statistics."""

    def test_statistics_counts(self, populated_db):
        """Statistics should correctly count words in different states."""
        selector = SpacedRepetitionSelector(populated_db)

        stats = selector.get_review_statistics()

        assert stats['total_words'] == 3
        assert stats['new_words'] == 3
        assert stats['due_words'] == 0
        assert stats['future_words'] == 0
