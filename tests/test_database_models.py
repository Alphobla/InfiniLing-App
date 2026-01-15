"""
Tests for Database Models and DatabaseManager.

These tests verify:
- CRUD operations (Create, Read, Update, Delete)
- Data integrity and constraints
- Session management
"""

import pytest
from datetime import datetime, timezone
from src.shared.database_models import DatabaseManager, Vocabulary, VocabularyOccurrence


def utc_now():
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class TestDatabaseManagerInit:
    """Tests for database initialization."""

    def test_creates_tables(self, in_memory_db):
        """Database should create all tables on initialization."""
        # The fixture already initializes, so just verify tables exist
        with in_memory_db.session_scope() as session:
            # This would fail if tables don't exist
            session.query(Vocabulary).all()
            session.query(VocabularyOccurrence).all()

    def test_multiple_init_is_safe(self, in_memory_db):
        """Calling initialize_database multiple times should be safe."""
        # Should not raise - tables already exist
        in_memory_db.initialize_database()
        in_memory_db.initialize_database()


class TestAddWord:
    """Tests for adding vocabulary words."""

    def test_add_word_basic(self, in_memory_db):
        """Should add a word with required fields."""
        word = in_memory_db.add_word(
            word="chat",
            translation="Katze",
            language_from="fr",
            language_to="de"
        )

        # Verify it was added
        all_words = in_memory_db.get_all_words()
        assert len(all_words) == 1
        assert all_words[0].word == "chat"
        assert all_words[0].translation == "Katze"

    def test_add_word_with_optional_fields(self, in_memory_db):
        """Should store optional metadata fields."""
        word = in_memory_db.add_word(
            word="chien",
            translation="Hund",
            language_from="fr",
            language_to="de",
            pronunciation="shee-en",
            primary_translation="Hund",
            secondary_translation="Köter"
        )

        all_words = in_memory_db.get_all_words()
        assert all_words[0].pronunciation == "shee-en"
        assert all_words[0].primary_translation == "Hund"
        assert all_words[0].secondary_translation == "Köter"

    def test_add_word_stores_original(self, in_memory_db):
        """Should store the original word form."""
        word = in_memory_db.add_word(
            word="mangé",  # conjugated form
            translation="gegessen"
        )

        all_words = in_memory_db.get_all_words()
        # original_word should be set to the word parameter
        assert all_words[0].original_word == "mangé"

    def test_add_word_sets_timestamps(self, in_memory_db):
        """Should set date_added timestamp."""
        # Strip timezone for comparison since SQLite stores naive datetimes
        before = utc_now().replace(tzinfo=None)
        word = in_memory_db.add_word(word="test", translation="Test")
        after = utc_now().replace(tzinfo=None)

        all_words = in_memory_db.get_all_words()
        assert all_words[0].date_added is not None
        # Compare naive datetimes (SQLite doesn't preserve timezone)
        assert before <= all_words[0].date_added <= after


class TestGetWord:
    """Tests for retrieving words."""

    def test_get_word_by_id(self, populated_db):
        """Should retrieve word by ID with all attributes accessible."""
        all_words = populated_db.get_all_words()
        word_id = all_words[0].id

        retrieved = populated_db.get_word(word_id)
        assert retrieved is not None
        assert retrieved.id == word_id
        assert retrieved.word == all_words[0].word

    def test_get_word_nonexistent(self, in_memory_db):
        """Should return None for nonexistent ID."""
        result = in_memory_db.get_word(99999)
        assert result is None

    def test_get_id_by_string(self, populated_db):
        """Should find word by text."""
        result = populated_db.get_id_by_string("bonjour")
        assert result is not None
        assert result.word == "bonjour"

    def test_get_id_by_string_not_found(self, populated_db):
        """Should return None for unknown word."""
        result = populated_db.get_id_by_string("nonexistent")
        assert result is None

    def test_get_all_words(self, populated_db):
        """Should return all words."""
        words = populated_db.get_all_words()
        assert len(words) == 3


class TestOccurrences:
    """Tests for vocabulary occurrences (review history)."""

    def test_add_occurrence(self, populated_db):
        """Should add occurrence record."""
        words = populated_db.get_all_words()
        word_id = words[0].id

        populated_db.add_occurrence(word_id, feedback_score=4)

        occurrences = populated_db.get_word_occurrences(word_id)
        assert len(occurrences) == 1
        assert occurrences[0].feedback_score == 4

    def test_multiple_occurrences(self, populated_db):
        """Should track multiple review occurrences."""
        words = populated_db.get_all_words()
        word_id = words[0].id

        populated_db.add_occurrence(word_id, feedback_score=3)
        populated_db.add_occurrence(word_id, feedback_score=4)
        populated_db.add_occurrence(word_id, feedback_score=5)

        occurrences = populated_db.get_word_occurrences(word_id)
        assert len(occurrences) == 3

    def test_occurrence_sets_date(self, populated_db):
        """Occurrence should have a date timestamp."""
        words = populated_db.get_all_words()
        word_id = words[0].id

        before = utc_now()
        populated_db.add_occurrence(word_id, feedback_score=4)
        after = utc_now()

        occurrences = populated_db.get_word_occurrences(word_id)
        assert occurrences[0].date is not None


class TestGetDueDays:
    """Tests for due days calculation."""

    def test_new_word_due_days(self, populated_db):
        """New word should return default due days."""
        words = populated_db.get_all_words()
        word_id = words[0].id

        due_days = populated_db.get_due_days(word_id)
        assert due_days == 1  # Default for new words


class TestSessionScope:
    """Tests for session management."""

    def test_session_commits_on_success(self, in_memory_db):
        """Session should commit changes on successful exit."""
        with in_memory_db.session_scope() as session:
            vocab = Vocabulary(
                word="test",
                original_word="test",
                translation="Test"
            )
            session.add(vocab)

        # Should persist after context exit
        words = in_memory_db.get_all_words()
        assert len(words) == 1

    def test_session_rollbacks_on_error(self, in_memory_db):
        """Session should rollback on exception."""
        try:
            with in_memory_db.session_scope() as session:
                vocab = Vocabulary(
                    word="test",
                    original_word="test",
                    translation="Test"
                )
                session.add(vocab)
                raise Exception("Simulated error")
        except Exception:
            pass

        # Should NOT persist due to rollback
        words = in_memory_db.get_all_words()
        assert len(words) == 0
