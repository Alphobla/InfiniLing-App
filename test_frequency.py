#!/usr/bin/env python3
"""
Test script for frequency analysis module
"""

from src.shared.frequency_analysis import (
    get_word_frequency_category,
    format_frequency_info,
    is_common_word,
    get_supported_languages
)

def test_frequency_analysis():
    # Test words in different languages
    test_cases = [
        ("hello", "en"),
        ("the", "en"),
        ("computer", "en"),
        ("bonjour", "fr"),
        ("le", "fr"),
        ("ordinateur", "fr"),
        ("hallo", "de"),
        ("der", "de"),
        ("computer", "de"),
    ]
    
    print("=== Word Frequency Analysis Test ===\n")
    
    for word, lang in test_cases:
        print(f"Testing: '{word}' in {lang}")
        
        # Get detailed category info
        info = get_word_frequency_category(word, lang)
        print(f"  Category: {info['category']}")
        print(f"  Level: {info['level']}")
        print(f"  Rank: {info['rank']}")
        print(f"  Zipf: {info['zipf_frequency']}")
        print(f"  Common: {is_common_word(word, lang)}")
        print(f"  Formatted: {format_frequency_info(word, lang)}")
        print()
    
    print("Supported languages:", get_supported_languages()[:10], "...")

if __name__ == "__main__":
    test_frequency_analysis()