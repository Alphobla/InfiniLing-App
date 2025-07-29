#!/usr/bin/env python3
"""
Text Generator

Handles story generation using OpenAI API.
"""

import os
from typing import List, Tuple
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()


class TextGenerator:
    """Handles text generation using OpenAI API."""
    
    def __init__(self, config=None):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def generate_story(self, vocab_list: List[dict[str, str,str]], 
                      language: str = "French", 
                      word_count: int = 300) -> str:
        """Generate a story incorporating the vocabulary words."""
        
        if not vocab_list:
            raise ValueError("No vocabulary words provided for story generation")
        
        # Format vocabulary for the prompt
        vocab_strings = []
        for vocab_entry in vocab_list:
            word, translation = vocab_entry['word'], vocab_entry['translation']
            vocab_strings.append(f"{word} ({translation})")
        
        vocab_list_str = ", ".join(vocab_strings)
        
        prompt = f"""Write an engaging short dialogue in {language} (about {word_count} words) that naturally incorporates these vocabulary words:

            {vocab_list_str}

            Requirements:
            - Use ALL the vocabulary words naturally in context
            - Make the dialogue interesting and coherent  
            - Use conversational, modern {language}, dont use rare words
            - The dialogue should help reinforce the meaning of each word through context
            - Make sure the dialogue flows well and is enjoyable to read

            Please write only the dialogue in {language}, no other text."""

        try:
            print(f"🎯 Generating dialogue with {len(vocab_list)} vocabulary words...")
            
            import json
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            response = self.client.chat.completions.create(
                model=config['text_generation']['model'],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=int(word_count * config['text_generation']['max_tokens_per_word']),
                temperature=config['text_generation']['temperature']
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

