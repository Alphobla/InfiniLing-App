"""
Tatoeba API client for getting sentence examples.
Uses the (unstable) Tatoeba API to find and translate example sentences.
"""

import requests
import time
from typing import Optional, Tuple

def get_sentence_example(word: str, source_lang: str, target_lang: str) -> Optional[Tuple[str, str]]:
    """Get a random sentence example with translation from Tatoeba."""
    
    # Map 2-letter codes to Tatoeba's 3-letter codes
    langs = {'fr': 'fra', 'de': 'deu', 'en': 'eng', 'es': 'spa', 'it': 'ita', 'pt': 'por', 'ru': 'rus'}
    src, tgt = langs.get(source_lang, source_lang), langs.get(target_lang, target_lang)
    
    time.sleep(1) # Respect rate limits
    
    try:
        # 1. Search for sentences containing the word
        search_url = "https://api.tatoeba.org/unstable/sentences"
        params = {'lang': src, 'trans:lang': tgt, 'sort': 'random', 'word_count': '4-10', 'q': word, 'limit': 10}
        
        search_resp = requests.get(search_url, params=params, timeout=10)
        search_resp.raise_for_status()
        results = search_resp.json().get('data', [])

        # 2. Fetch details for each result to find the translation
        for entry in results:
            if not entry.get('id'): continue
            
            detail_url = f"https://api.tatoeba.org/unstable/sentences/{entry['id']}"
            detail_resp = requests.get(detail_url, timeout=10)
            if not detail_resp.ok: continue
            
            # The detail response might have the sentence directly or in 'data'
            data = detail_resp.json()
            sentence = data.get('data', data) if isinstance(data, dict) else {}
            
            original_text = sentence.get('text', '')
            translations = sentence.get('translations', [])
            
            # Find the first translation in the target language
            for item in translations:
                # Could be a list of translations or a single translation dict
                group = item if isinstance(item, list) else [item]
                for trans in group:
                    if isinstance(trans, dict) and trans.get('lang') == tgt:
                        return original_text, trans.get('text', '')
                        
    except Exception as e:
        print(f"Tatoeba error: {e}")
        
    return None

if __name__ == "__main__":
    for word, sl, tl in [("parler", "fr", "de"), ("chat", "fr", "en")]:
        print(f"Searching for '{word}' ({sl}->{tl})...")
        res = get_sentence_example(word, sl, tl)
        if res:
            print(f"  {sl.upper()}: {res[0]}\n  {tl.upper()}: {res[1]}\n")
        else:
            print(f"  No example found.\n")