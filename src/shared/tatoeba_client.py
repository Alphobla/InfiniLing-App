"""
Simple Tatoeba API client for getting sentence examples.
"""

import requests
import time
from typing import Optional, Tuple


def get_sentence_example(word: str, source_lang: str, target_lang: str) -> Optional[Tuple[str, str]]:
    """
    Get one example sentence from Tatoeba using the new unstable API.
    
    Args:
        word: Word to find example for
        source_lang: Source language code (e.g., 'fr')
        target_lang: Target language code (e.g., 'de')
        
    Returns:
        Tuple of (original_sentence, translation) or None if not found
    """
    # Convert 2-letter codes to 3-letter codes used by Tatoeba
    lang_mapping = {
        'fr': 'fra', 'de': 'deu', 'en': 'eng', 'es': 'spa', 
        'it': 'ita', 'pt': 'por', 'ru': 'rus'
    }
    
    source_code = lang_mapping.get(source_lang, source_lang)
    target_code = lang_mapping.get(target_lang, target_lang)
    
    # Rate limiting - wait 1 second between requests
    time.sleep(1)
    
    try:
        # Use new unstable API endpoint with proper search
        url = "https://api.tatoeba.org/unstable/sentences"
        params = {
            'lang': source_code,  # Search in source language only
            'trans:lang': target_code,  # Get translation in target language
            'sort': 'random',  # Sort by word count (longest first)
            'word_count': '4-10',  # Filter for sentences with 5 or more words
            'q': word,  # Actually search for the word
            'limit': 10  # Get more results to find one containing the word
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Look through sentences to find one with target language translation
        if 'data' in data:
            for sentence in data['data']:
                original_text = sentence.get('text', '')
                translations = sentence.get('translations', [])
                
                # Look through translation groups
                for translation_group in translations:
                    for translation in translation_group:
                        if translation.get('lang') == target_code:
                            return (original_text, translation.get('text', ''))
        
        return None
        
    except Exception as e:
        print(f"Tatoeba API error: {e}")
        return None


if __name__ == "__main__":
    # Test the function with a simple example
    print("Testing Tatoeba client...")
    
    # Test French to German
    result = get_sentence_example("parler", "fr", "de")
    if result:
        print(f"French: {result[0]}")
        print(f"German: {result[1]}")
    else:
        print("No example found for 'parler' (French -> German)")
    
    print("\n" + "="*50 + "\n")
    
    # Test French to English
    result = get_sentence_example("chat", "fr", "en")
    if result:
        print(f"French: {result[0]}")
        print(f"English: {result[1]}")
    else:
        print("No example found for 'chat' (French -> English)")