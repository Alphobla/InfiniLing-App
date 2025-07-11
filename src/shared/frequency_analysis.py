"""
Word frequency analysis module using wordfreq library.
Provides functions to analyze word frequency rankings across different languages.
"""

from wordfreq import word_frequency, zipf_frequency
from typing import Optional, Dict, Tuple


def get_word_frequency_rank(word: str, language: str) -> Optional[int]:
    """
    Get the approximate frequency rank of a word in a given language.
    
    Args:
        word: The word to analyze
        language: Language code (e.g., 'en', 'fr', 'de', 'es')
    
    Returns:
        Approximate rank (1-based) or None if word not found
    """
    try:
        # Get Zipf frequency (logarithmic scale where 6+ = very common)
        zipf_freq = zipf_frequency(word.lower(), language)
        
        # Convert Zipf frequency to approximate rank
        # Zipf 7+ ≈ top 100, 6+ ≈ top 1000, 5+ ≈ top 10000, etc.
        if zipf_freq >= 7.0:
            return int(10 ** (8 - zipf_freq))
        elif zipf_freq >= 3.0:
            return int(10 ** (8 - zipf_freq))
        else:
            return None
            
    except Exception:
        return None


def get_word_frequency_category(word: str, language: str) -> Dict[str, any]:
    """
    Categorize a word's frequency level with detailed information.
    
    Args:
        word: The word to analyze
        language: Language code (e.g., 'en', 'fr', 'de', 'es')
    
    Returns:
        Dictionary with frequency information including category, rank, and level
    """
    try:
        zipf_freq = zipf_frequency(word.lower(), language)
        raw_freq = word_frequency(word.lower(), language)
        
        # Calculate approximate rank first
        rank = get_word_frequency_rank(word, language)
        
        # Determine category based on actual rank
        if rank and rank <= 100:
            category = "top_100"
            level = "Top 100"
            color = "#1B5E20"  # Dark green
        elif rank and rank <= 1000:
            category = "top_1000"
            level = "Top 1,000"
            color = "#2E7D32"  # Green
        elif rank and rank <= 5000:
            category = "top_5000"
            level = "Top 5,000"
            color = "#388E3C"  # Light green
        elif rank and rank <= 10000:
            category = "top_10000"
            level = "Top 10,000"
            color = "#689F38"  # Light green
        elif rank and rank <= 20000:
            category = "top_20000"
            level = "Top 20,000"
            color = "#FBC02D"  # Yellow
        elif rank and rank <= 50000:
            category = "top_50000"
            level = "Top 50,000"
            color = "#FF8F00"  # Orange
        elif rank and rank <= 100000:
            category = "top_100000"
            level = "Top 100,000"
            color = "#F57C00"  # Dark orange
        else:
            category = "rare"
            level = "Rare"
            color = "#D32F2F"  # Red
        
        return {
            "word": word,
            "language": language,
            "category": category,
            "level": level,
            "rank": rank,
            "zipf_frequency": round(zipf_freq, 2),
            "raw_frequency": raw_freq,
            "color": color,
            "found": True
        }
        
    except Exception as e:
        return {
            "word": word,
            "language": language,
            "category": "unknown",
            "level": "Unknown",
            "rank": None,
            "zipf_frequency": 0,
            "raw_frequency": 0,
            "color": "#757575",  # Gray
            "found": False,
            "error": str(e)
        }


def is_common_word(word: str, language: str, threshold: float = 4.8) -> bool:
    """
    Check if a word is considered common (above threshold).
    
    Args:
        word: The word to check
        language: Language code
        threshold: Zipf frequency threshold (default 4.8 = top 5,000)
    
    Returns:
        True if word is common, False otherwise
    """
    try:
        zipf_freq = zipf_frequency(word.lower(), language)
        return zipf_freq >= threshold
    except Exception:
        return False


def get_supported_languages() -> list:
    """
    Get list of supported language codes.
    
    Returns:
        List of supported language codes
    """
    # Common languages supported by wordfreq
    return [
        'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh',
        'ar', 'hi', 'nl', 'pl', 'tr', 'sv', 'da', 'no', 'fi', 'cs',
        'hu', 'el', 'he', 'th', 'vi', 'id', 'ms', 'tl', 'sw', 'ro',
        'bg', 'hr', 'sk', 'sl', 'et', 'lv', 'lt', 'mt', 'cy', 'ga'
    ]


def format_frequency_info(word: str, language: str) -> str:
    """
    Format frequency information as a readable string.
    
    Args:
        word: The word to analyze
        language: Language code
    
    Returns:
        Formatted string with frequency information
    """
    info = get_word_frequency_category(word, language)
    
    if not info["found"]:
        return f"'{word}' - frequency data not available"
    
    rank_text = f"#{info['rank']}" if info["rank"] else "unranked"
    return f"'{word}' - {info['level']} ({rank_text})"