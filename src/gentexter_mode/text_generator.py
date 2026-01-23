#!/usr/bin/env python3
"""
Text Generator

Handles story generation using OpenAI API.
"""

import os
import json
from typing import List, Tuple
from dotenv import load_dotenv
import openai
from src.shared.languages import get_name as get_language_name

# Load environment variables from .env file
load_dotenv()


class TextGenerator:
    """Handles text generation using OpenAI API."""
    
    def __init__(self, config=None):
        self.config = config
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def generate_story(self, vocab_list: List[dict[str, str,str]],
                      language: str = None,
                      word_count: int = 300) -> str:
        """Generate a story incorporating the vocabulary words."""

        if not vocab_list:
            raise ValueError("No vocabulary words provided for story generation")

        if not language:
            raise ValueError("No language specified for story generation")

        # Convert language code to name if needed (e.g., "en" -> "English")
        language_name = get_language_name(language)

        # Format vocabulary for the prompt
        vocab_strings = []
        for vocab_entry in vocab_list:
            word, translation = vocab_entry['word'], vocab_entry['translation']
            vocab_strings.append(f"{word} ({translation})")
        
        vocab_list_str = ", ".join(vocab_strings)
        
        prompt = f"""Write an engaging short dialogue in {language_name} (about {word_count} words) that naturally incorporates these vocabulary words:

            {vocab_list_str}

            Requirements:
            - Use ALL the vocabulary words naturally in context
            - Make the dialogue interesting and coherent
            - Use conversational, modern {language_name}, dont use rare words
            - The dialogue should help reinforce the meaning of each word through context
            - Make sure the dialogue flows well and is enjoyable to read

            Please write only the dialogue in {language_name}, no other text."""

        try:
            print(f"🎯 Generating dialogue with {len(vocab_list)} vocabulary words...")
            
            story_model = self.config.get('text_generation.model')
            if not story_model:
                raise KeyError("'text_generation.model' not configured in config.json")
            story_temp = self.config.get('text_generation.temperature')
            if story_temp is None:
                raise KeyError("'text_generation.temperature' not configured in config.json")
            max_factor = self.config.get('text_generation.max_tokens_per_word')
            if max_factor is None:
                raise KeyError("'text_generation.max_tokens_per_word' not configured in config.json")
            
            response = self.client.chat.completions.create(
                model=story_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=int(word_count * max_factor),
                temperature=story_temp
            )
            
            content = response.choices[0].message.content
            story = content.strip() if content else ""
            
            if not story:
                raise ValueError("Empty story generated")
            
            print(f"✅ Story generated successfully ({len(story)} characters)")
            return story
            
        except Exception as e:
            print(f"❌ Error generating story: {e}")
            raise

    def generate_initial_words(self, language: str, difficulty: str, count: int = 20) -> List[dict]:
        """Generate a list of vocabulary words for a specific language and difficulty."""

        if not language:
            raise ValueError("No language specified for word generation")

        # Convert language code to name if needed (e.g., "en" -> "English")
        language_name = get_language_name(language)

        prompt = f"""Generate a list of exactly {count} common and useful vocabulary words in {language_name} for a learner at {difficulty} level.
        
        Requirements:
        - Words should be appropriate for the {difficulty} (CEFR) level.
        - Focus on practical, everyday vocabulary.
        - Provide the response as a JSON array of objects.
        - Each object MUST have "word" and "translation" (in German) keys.
        
        Example format:
        [
            {{"word": "bonjour", "translation": "Guten Tag"}},
            ...
        ]
        
        Provide ONLY the JSON array, no other text."""

        try:
            print(f"🎯 Generating {count} words for {language_name} ({difficulty})...")
            
            story_model = self.config.get('text_generation.model', 'gpt-4o-mini')
            
            response = self.client.chat.completions.create(
                model=story_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={"type": "json_object"} if "4o" in story_model else None
            )
            
            content = response.choices[0].message.content
            # GPT might wrap JSON in code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            data = json.loads(content)
            
            # Handle cases where GPT might return a root object instead of a list
            if isinstance(data, dict):
                # Look for a list inside the dict
                for key, value in data.items():
                    if isinstance(value, list):
                        data = value
                        break
            
            if not isinstance(data, list):
                raise ValueError("Generated content is not a list of words")
                
            return data[:count]
            
        except Exception as e:
            print(f"❌ Error generating initial words: {e}")
            raise

