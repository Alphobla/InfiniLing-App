"""
GPT-based word translation and analysis module.
Provides lemmatization, translation, and linguistic analysis using OpenAI API.
"""

from openai import OpenAI
import json
import os
from typing import Dict, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from .frequency_analysis import get_word_frequency_category

# Load environment variables
load_dotenv()


@dataclass
class WordAnalysis:
    """Data class for comprehensive word analysis results."""
    original_word: str
    root_word: str
    grammatical_relation: str
    primary_translation: str
    secondary_translation: Optional[str]
    part_of_speech: str
    frequency_info: Dict
    context_translation: Optional[str]
    language_from: str
    language_to: str


class GPTTranslator:
    """GPT-based translator with lemmatization and frequency analysis."""
    
    def __init__(self, api_key: str = None):
        """Initialize with OpenAI API key."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env file or pass as parameter.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.cache = {}  # Simple translation cache
        
    def _call_gpt(self, prompt: str, model: str = "gpt-3.5-turbo") -> str:
        """Make API call to GPT."""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"GPT API error: {e}")
            return None
    
    def lemmatize_word(self, word: str, language: str, context: str = "") -> Dict:
        """
        Find root word and grammatical relation using GPT.
        
        Args:
            word: Word to analyze
            language: Source language code (e.g., 'fr', 'de')
            context: Surrounding sentence for better accuracy
            
        Returns:
            Dictionary with root word and grammatical relation
        """
        cache_key = f"lemma_{word}_{language}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        prompt = f"""
        Analyze this {language} word: "{word}"
        {f'Context: "{context}"' if context else ''}
        
        Provide a JSON response with:
        1. "root_word": the base/dictionary form (infinitive for verbs, singular for nouns)
        2. "grammatical_relation": describe the transformation (e.g., "past tense", "plural", "3rd person singular", "comparative", "unchanged")
        3. "part_of_speech": noun, verb, adjective, adverb, etc.
        
        Example: "books" -> {{"root_word": "book", "grammatical_relation": "plural noun", "part_of_speech": "noun"}}
        
        Response format: JSON only, no explanation.
        """
        
        response = self._call_gpt(prompt)
        if not response:
            return {"root_word": word, "grammatical_relation": "unchanged", "part_of_speech": "unknown"}
        
        try:
            result = json.loads(response)
            self.cache[cache_key] = result
            return result
        except json.JSONDecodeError:
            return {"root_word": word, "grammatical_relation": "unchanged", "part_of_speech": "unknown"}
    
    def translate_word(self, word: str, language_from: str, language_to: str, context: str = "") -> Dict:
        """
        Translate word with primary and secondary translations.
        
        Args:
            word: Word to translate
            language_from: Source language code
            language_to: Target language code
            context: Surrounding text for context-aware translation
            
        Returns:
            Dictionary with translation information
        """
        cache_key = f"trans_{word}_{language_from}_{language_to}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        lang_names = {
            'en': 'English', 'fr': 'French', 'de': 'German', 'es': 'Spanish',
            'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
            'ko': 'Korean', 'zh': 'Chinese', 'ar': 'Arabic', 'hi': 'Hindi'
        }
        
        from_lang = lang_names.get(language_from, language_from)
        to_lang = lang_names.get(language_to, language_to)
        
        prompt = f"""
        Translate this {from_lang} word to {to_lang}: "{word}"
        {f'Context: "{context}"' if context else ''}
        
        Provide a JSON response with:
        1. "primary_translation": most common/best translation
        2. "secondary_translation": alternative translation if relevant (null if not applicable)
        3. "context_translation": translation considering the context (null if no context or same as primary)
        
        Response format: JSON only, no explanation.
        """
        
        response = self._call_gpt(prompt)
        if not response:
            return {"primary_translation": "Translation unavailable", "secondary_translation": None, "context_translation": None}
        
        try:
            result = json.loads(response)
            self.cache[cache_key] = result
            return result
        except json.JSONDecodeError:
            return {"primary_translation": "Translation error", "secondary_translation": None, "context_translation": None}
    
    def analyze_word_comprehensive(self, word: str, language_from: str, language_to: str = "en", context: str = "") -> WordAnalysis:
        """
        Comprehensive word analysis combining lemmatization, translation, and frequency.
        
        Args:
            word: Word to analyze
            language_from: Source language code
            language_to: Target language code (default: English)
            context: Surrounding text for context
            
        Returns:
            WordAnalysis object with all information
        """
        # Step 1: Lemmatize the word
        lemma_info = self.lemmatize_word(word, language_from, context)
        root_word = lemma_info.get("root_word", word)
        
        # Step 2: Translate the root word
        translation_info = self.translate_word(root_word, language_from, language_to, context)
        
        # Step 3: Get frequency analysis for root word
        frequency_info = get_word_frequency_category(root_word, language_from)
        
        # Step 4: Combine all information
        return WordAnalysis(
            original_word=word,
            root_word=root_word,
            grammatical_relation=lemma_info.get("grammatical_relation", "unchanged"),
            primary_translation=translation_info.get("primary_translation", ""),
            secondary_translation=translation_info.get("secondary_translation"),
            part_of_speech=lemma_info.get("part_of_speech", "unknown"),
            frequency_info=frequency_info,
            context_translation=translation_info.get("context_translation"),
            language_from=language_from,
            language_to=language_to
        )
    
    def format_analysis_for_display(self, analysis: WordAnalysis) -> str:
        """
        Format analysis results for display in UI.
        
        Args:
            analysis: WordAnalysis object
            
        Returns:
            Formatted string for display
        """
        lines = []
        
        # Word and root
        if analysis.original_word != analysis.root_word:
            lines.append(f"📝 {analysis.original_word} → {analysis.root_word} ({analysis.grammatical_relation})")
        else:
            lines.append(f"📝 {analysis.original_word}")
        
        # Translation
        lines.append(f"🔤 {analysis.primary_translation}")
        if analysis.secondary_translation:
            lines.append(f"   Alt: {analysis.secondary_translation}")
        
        # Context translation if different
        if analysis.context_translation and analysis.context_translation != analysis.primary_translation:
            lines.append(f"   Context: {analysis.context_translation}")
        
        # Frequency
        freq = analysis.frequency_info
        if freq.get("found"):
            lines.append(f"📊 {freq['level']} (#{freq['rank']})")
        
        # Part of speech
        if analysis.part_of_speech != "unknown":
            lines.append(f"🏷️ {analysis.part_of_speech}")
        
        return "\n".join(lines)
    
    def get_quick_translation(self, word: str, language_from: str, language_to: str = "en") -> str:
        """
        Quick translation for simple cases.
        
        Args:
            word: Word to translate
            language_from: Source language
            language_to: Target language
            
        Returns:
            Simple translation string
        """
        translation_info = self.translate_word(word, language_from, language_to)
        return translation_info.get("primary_translation", "Translation unavailable")


# Utility functions for easy integration
def create_translator(api_key: str) -> GPTTranslator:
    """Create a GPT translator instance."""
    return GPTTranslator(api_key)


def quick_translate(word: str, language_from: str, language_to: str = "en", api_key: str = None) -> str:
    """Quick translation function."""
    if not api_key:
        return "API key required"
    
    translator = GPTTranslator(api_key)
    return translator.get_quick_translation(word, language_from, language_to)