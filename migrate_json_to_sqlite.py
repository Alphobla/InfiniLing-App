#!/usr/bin/env python3
"""
One-time migration script to convert JSON vocabulary data to SQLite database.

This script reads the existing word_tracking.json file and migrates all vocabulary
data to the new SQLite database structure.
"""

import json
import os
from datetime import datetime
from src.shared.database_models import DatabaseManager, Vocabulary, VocabularyOccurrence

def migrate_json_to_sqlite():
    """
    Migrate vocabulary data from JSON file to SQLite database.
    """
    # Paths
    json_file_path = "data/word_tracking.json"
    
    print("Starting migration from JSON to SQLite...")
    
    # Check if JSON file exists
    if not os.path.exists(json_file_path):
        print(f"Error: JSON file not found at {json_file_path}")
        return False
    
    # Load JSON data
    print("Loading JSON data...")
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return False
    
    print(f"Found {len(json_data)} vocabulary entries to migrate")
    
    # Initialize database
    print("Initializing SQLite database...")
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    
    # Migrate data
    print("Migrating vocabulary data...")
    migrated_count = 0
    error_count = 0
    
    for key, word_data in json_data.items():
        try:
            # Extract word and translation from key or data
            word = word_data.get('word', '')
            translation = word_data.get('translation', '')
            pronunciation = word_data.get('pronunciation', '')
            
            # Use a single session for the entire word migration
            with db_manager.session_scope() as session:
                # Add vocabulary word
                vocab = Vocabulary(
                    word=word,
                    translation=translation,
                    pronunciation=pronunciation if pronunciation else None,
                    language_from='fr',  # Default based on your data
                    language_to='de'     # Default based on your data
                )
                session.add(vocab)
                session.flush()  # Get the ID without committing
                
                # Migrate occurrences
                occurrences = word_data.get('occurrences', [])
                for occurrence in occurrences:
                    # Parse date from ISO format
                    date_str = occurrence.get('date', '')
                    try:
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except ValueError:
                        # Fallback to current time if date parsing fails
                        date_obj = datetime.utcnow()
                    
                    repeat = occurrence.get('repeat', False)
                    
                    # Add occurrence to database
                    occ = VocabularyOccurrence(
                        vocabulary_id=vocab.id,
                        date=date_obj,
                        repeat=repeat
                    )
                    session.add(occ)
            
            migrated_count += 1
            
            # Progress indicator
            if migrated_count % 100 == 0:
                print(f"Migrated {migrated_count} words...")
                
        except Exception as e:
            print(f"Error migrating word '{key}': {e}")
            error_count += 1
            continue
    
    # Summary
    print(f"\n=== Migration Summary ===")
    print(f"Total words processed: {len(json_data)}")
    print(f"Successfully migrated: {migrated_count}")
    print(f"Errors: {error_count}")
    print(f"Success rate: {migrated_count/len(json_data)*100:.1f}%")
    
    # Verify migration
    print("\n=== Verification ===")
    all_words = db_manager.get_all_words()
    print(f"Words in database: {len(all_words)}")
    
    # Show sample of migrated data
    if all_words:
        print("\nSample migrated words:")
        for word in all_words[:5]:
            word_id = word['id']
            word_word = word['word']
            word_translation = word['translation']
            occurrences = db_manager.get_word_occurrences(word_id)
            print(f"- {word_word} → {word_translation} ({len(occurrences)} occurrences)")
    
    return True

if __name__ == "__main__":
    print("JSON to SQLite Migration Script")
    print("=" * 40)
    
    success = migrate_json_to_sqlite()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Test the database with some queries")
        print("2. Update selector.py to use the new database")
        print("3. Remove or archive the old JSON file")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above and try again.")