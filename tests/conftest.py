"""
Pytest fixtures for InfiniLing tests.
"""

import pytest
import tempfile
import os
import json
from datetime import datetime, timedelta

from src.shared.database_models import DatabaseManager, Base, Vocabulary, VocabularyOccurrence


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    db = DatabaseManager(database_url="sqlite:///:memory:")
    db.initialize_database()
    return db


@pytest.fixture
def populated_db(in_memory_db):
    """Database with sample vocabulary words."""
    db = in_memory_db

    # Add some test words directly using session
    with db.session_scope() as session:
        words = [
            Vocabulary(word="bonjour", original_word="bonjour", translation="Guten Tag",
                      language_from="fr", language_to="de"),
            Vocabulary(word="merci", original_word="merci", translation="Danke",
                      language_from="fr", language_to="de"),
            Vocabulary(word="maison", original_word="maison", translation="Haus",
                      language_from="fr", language_to="de"),
        ]
        for w in words:
            session.add(w)

    return db


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    config_data = {
        "vocabulary": {
            "languages": {
                "source": "fr",
                "target": "de"
            }
        },
        "ui": {
            "window_sizes": {
                "reader": {"width": 800, "height": 600},
                "main": {"width": 500, "height": 400}
            }
        },
        "audio": {
            "voice": "nova",
            "speed": 1.0
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)
