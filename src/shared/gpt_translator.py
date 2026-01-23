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
from .languages import get_name as get_language_name

# Load environment variables
load_dotenv()


@dataclass
class WordAnalysis:
    """Data class for comprehensive word analysis results."""
    original_word: str
    root_word: str
    primary_translation: str
    secondary_translation: Optional[str]
    frequency_info: Dict
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
        
    def _call_gpt(self, prompt: str, model: str = None) -> str:
        """Make API call to GPT."""
        try:
            import json
            # Default values if config fails
            model_to_use = "gpt-4o-mini"
            max_tokens = 500
            temperature = 0.3

            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                enh_config = config.get('word_enhancement', {})
                model_to_use = enh_config.get('model', model_to_use)
                max_tokens = enh_config.get('max_tokens', max_tokens)
                temperature = enh_config.get('temperature', temperature)
            except Exception as e:
                print(f"Warning: Could not load config.json for GPTTranslator: {e}")
            
            # Allow override via parameter
            if model:
                model_to_use = model

            response = self.client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"GPT API error ({model_to_use if 'model_to_use' in locals() else 'unknown'}): {e}")
            return None
    
    def lemmatize_word(self, word: str, language: str) -> Dict:
        """
        Find root word and grammatical relation using GPT.
        
        Args:
            word: Word to analyze
            language: Source language code (e.g., 'fr', 'de')
            
        Returns:
            Dictionary with root word and grammatical relation
        """
        cache_key = f"lemma_{word}_{language}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        prompt = f"""
        Analyze the following word in {language}: "{word}"

        For vocabulary database storage, normalize as follows (IMPORTANT)
        - Verbs: convert to infinitive (parlais -> parler)
        - EVERY Noun needs an article (poussière -> la poussière). If the translation is a noun, add the article to the root word.
        - EVERY Adjective stays an adjective: use the base form (gâtée -> gâté)
        - EVERY reflexive verb should stay reflexive (s'empare -> s'emparer, se déroule -> se dérouler)
        - NEVER delete whole words or short version of words ( "s'en va" never to "en aller", "s'effondre" never to "effondrer")
        - Preserve compound words (à peu près -> à peu près)
        - Preserve combined structures (porter plainte -> porter plainte)

        Respond in JSON only, output is the root word.

        Example: "porte plainte" → {{"root_word": "porter plainte"}}
        Output JSON only. No explanation or extra text.
        """
        
        response = self._call_gpt(prompt)
        if not response:
            return {"root_word": word}
        
        try:
            result = json.loads(response)
            self.cache[cache_key] = result
            return result
        except json.JSONDecodeError:
            return {"root_word": word}

    def translate_word(self, word: str, language_from: str, language_to: str, assist_translation: str = None) -> Dict:
        """
        Translate word with primary and secondary translations.
        
        Args:
            word: Word to translate
            language_from: Source language code
            language_to: Target language code
            
        Returns:
            Dictionary with translation information
        """
        cache_key = f"trans_{word}_{language_from}_{language_to}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        from_lang = get_language_name(language_from)
        to_lang = get_language_name(language_to)
        
        prompt = f"""
        Translate this {from_lang} word to {to_lang}: "{word}"
        {f'Assistant translation guidance: "{assist_translation}" - use this as a reference.' if assist_translation else ''}
        
        Provide a JSON response with:
        1. "primary_translation": most common/best translation
        2. "secondary_translation": alternative translation if occurring often (else null)

        Response format: JSON only, no explanation.
        """
        
        response = self._call_gpt(prompt)
        if not response:
            return {"primary_translation": "Translation unavailable", "secondary_translation": None}
        
        try:
            result = json.loads(response)
            self.cache[cache_key] = result
            return result
        except json.JSONDecodeError:
            return {"primary_translation": "Translation error", "secondary_translation": None}
    
    def normalize_and_translate(self, word: str, language_from: str, language_to: str, assist_translation: str = None) -> Dict:
        """
        Combined normalization and translation in one GPT call for consistency.
        
        Args:
            word: Word to normalize and translate
            language_from: Source language code
            language_to: Target language code
            assist_translation: Existing translation as guidance
            
        Returns:
            Dictionary with normalized word and translations
        """
        cache_key = f"norm_trans_{word}_{language_from}_{language_to}_{assist_translation}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        from_lang = get_language_name(language_from)
        to_lang = get_language_name(language_to)
        
        prompt = f"""
        You are a vocabulary database cleaner for a language learning app.

        CONTEXT:
        Users input vocabulary words in messy formats — conjugated verbs, declined adjectives, plural or article-less nouns, etc.  
        Your job is to normalize these into proper **dictionary forms**, then translate them.

        INPUT: Raw {from_lang} word "{word}" (possibly messy/conjugated/declined)  
        {f'HINT: Existing translation is "{assist_translation}" — use as context.' if assist_translation else ''}

        CRITICAL: The word "{word}" IS A REAL {from_lang} WORD. Do NOT translate it to English or another language. Normalize it, then translate.

        ---

        YOUR TASK — STEP BY STEP:

        **STEP 1 — DETERMINE WORD TYPE (based on the word and optional assist_translation):**
        - Is it a **noun**? → go to Step 2
        - Is it a **verb** or reflexive verb? → go to Step 3
        - Is it an **adjective**? → go to Step 4
        - Is it a **compound expression** (e.g. "à peu près", "porter plainte")? → go to Step 5
        - Is it an **abbreviation** or proper name? → go to Step 6

        ---

        **STEP 2 — NOUNS → Normalize and translate**
        - Convert to dictionary form with definite article:
            - "racine" → "la racine "
            - "nid" → "le nid "
        - Add **gender** in brackets if the article abbreviated (l') or in plural (les):
            - "flics" → "les flics (m.)"
            - "arnaque" → "l'arnaque (f.)"
        - Use `assist_translation` to guide sense (e.g. "raccourci" → "le raccourci", not the verb)

        ---

        **STEP 3 — VERBS → Normalize and translate**
        - Convert to **infinitive** form
        - If it's reflexive, keep the **reflexive pronoun**:
            - "parlais" → "parler"
            - "se lève" → "se lever"
            - "s'empêche" → "s'empêcher"

        ---

        **STEP 4 — ADJECTIVES → Normalize and translate**
        - Convert to **masculine singular** form:
            - "belle" → "beau"
            - "gâtée" → "gâté"
            - "verte" → "vert"

        ---

        **STEP 5 — EXPRESSIONS → Keep as-is**
        - Leave intact if it’s a valid phrase or idiom:
            - "porter plainte" → "porter plainte"
            - "à peu près" → "à peu près"

        ---

        **STEP 6 — ABBREVIATIONS / PROPER NAMES**
        - Keep unchanged (e.g. "udc" → "udc")

        ---

        🚫 DO NOT:
        - Guess or change the word’s meaning
        - Omit gender/article for nouns
        - Translate the word into English or a third language
        - Invent new root words (e.g. “belle” → “beller” ✗)

        ---

        ⚠️ IF `assist_translation` IS PRESENT:
        - Use it to **disambiguate the meaning** — e.g. "supplier" + "anflehen" → "supplier", not "liefern"

        ---

        ✅ OUTPUT FORMAT — JSON ONLY (no markdown, no explanation):
        {{
        "root_word": "<cleaned dictionary form in {from_lang}>",
        "primary_translation": "<best translation in {to_lang}, no article needed for nouns>",
        "secondary_translation": "<alternative translation or null>"
        }}

        """
        
        response = self._call_gpt(prompt)
        if not response:
            return {"root_word": word, "primary_translation": "Translation unavailable", "secondary_translation": None}
        
        try:
            # Clean response from potential markdown code blocks
            clean_response = response.strip()
            if clean_response.startswith("```"):
                # Handle ```json ... ``` or just ``` ... ```
                lines = clean_response.splitlines()
                if len(lines) >= 3:
                    # Remove the first and last lines (the backticks)
                    clean_response = "\n".join(lines[1:-1]).strip()
            
            result = json.loads(clean_response)
            
            # Validate root_word - if it's "None", "null", empty, or suspicious, use original
            root_word = result.get("root_word", word)
            if not root_word or root_word.lower() in ["none", "null", "aucun", "nul"]:
                root_word = word
                print(f"Warning: GPT returned invalid root_word '{result.get('root_word')}' for '{word}', using original")
            
            result["root_word"] = root_word
            self.cache[cache_key] = result
            return result
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"JSON parsing error for '{word}': {e}")
            print(f"Response was: {response}")
            return {"root_word": word, "primary_translation": "Translation error", "secondary_translation": None}

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
            lines.append(f"📝 {analysis.original_word} → {analysis.root_word}")
        else:
            lines.append(f"📝 {analysis.original_word}")
        
        # Translation
        lines.append(f"🔤 {analysis.primary_translation}")
        if analysis.secondary_translation:
            lines.append(f"   Alt: {analysis.secondary_translation}")
        
        # Frequency
        freq = analysis.frequency_info
        if freq.get("found"):
            lines.append(f"📊 {freq['level']} (#{freq['rank']})")
        
        
        return "\n".join(lines)

    def analyze_word_string(self, word_text: str, language_from: str = 'fr', language_to: str = 'de', assist_translation: str = None) -> dict:
        """
        Analyze a single word and return all enhancement data as dictionary.
        
        Args:
            word_text: The word to analyze
            language_from: Source language (default: 'fr')
            language_to: Target language (default: 'de')
            assist_translation: Optional existing translation as guidance
            
        Returns:
            dict: Complete word analysis with all data
        """
        try:
            from .tatoeba_client import get_sentence_example
            
            # Get GPT analysis using existing method
            analysis = self.normalize_and_translate(
                word_text,
                language_from,
                language_to,
                assist_translation
            )
            
            if not analysis or not isinstance(analysis, dict):
                return {"error": "Failed to get GPT analysis"}
            
            # Get frequency data
            root_word = analysis.get('root_word', word_text)

            # Helper to strip articles and gender markers for lookups
            def strip_to_core_word(word_form):
                """Strip articles and gender markers."""
                import re
                core = re.sub(r'\s*\([mf]\.\)$', '', word_form)
                return core.strip()

            # Use stripped word for frequency lookup (wordfreq won't find "chien (m.)")
            core_word = strip_to_core_word(root_word)
            frequency = get_word_frequency_category(core_word, language_from)

            # Get example sentence with core word
            example_original = None
            example_translation = None
            try:
                example = get_sentence_example(core_word, language_from, language_to)
                if example:
                    example_original = example[0]
                    example_translation = example[1]
            except:
                pass
            
            # Return complete analysis
            return {
                "original_word": word_text,
                "normalized_word": root_word,
                "primary_translation": analysis.get("primary_translation", ""),
                "secondary_translation": analysis.get("secondary_translation"),
                "frequency_level": frequency.get('level'),
                "frequency_rank": frequency.get('rank'),
                "example_original": example_original,
                "example_translation": example_translation,
                "language_from": language_from,
                "language_to": language_to
            }
            
        except Exception as e:
            return {"error": f"Error analyzing word '{word_text}': {e}"}
# Utility functions for easy integration
def create_translator(api_key: str) -> GPTTranslator:
    """Create a GPT translator instance."""
    return GPTTranslator(api_key)
