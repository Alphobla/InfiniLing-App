#!/usr/bin/env python3
"""
Audio Generator

Handles text-to-speech audio generation using OpenAI API.
"""

import os
from typing import Optional
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()


class AudioGenerator:
    """Handles audio generation using OpenAI TTS API."""
    
    def __init__(self, config=None):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Available voices: alloy, echo, fable, onyx, nova, shimmer
        self.available_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        self.default_voice = "onyx"
    
    def generate_audio(self, text: str, output_path: str, 
                      voice: str = None, 
                      model: str = "tts-1", 
                      speed: float = 1.0) -> bool:
        """
        Generate TTS audio for the given text.
        
        Args:
            text: Text to convert to speech
            output_path: Path where to save the audio file
            voice: Voice to use (default: onyx)
            model: TTS model to use (tts-1 or tts-1-hd)
            speed: Speech speed (0.25 to 4.0)
        
        Returns:
            bool: True if successful, False otherwise
        """
        
        if not text or not text.strip():
            raise ValueError("No text provided for audio generation")
        
        if voice is None:
            voice = self.default_voice
        
        if voice not in self.available_voices:
            print(f"⚠️ Voice '{voice}' not available. Using default '{self.default_voice}'")
            voice = self.default_voice
        
        # Validate speed
        speed = max(0.25, min(4.0, speed))
        
        try:
            print(f"🎵 Generating audio with voice '{voice}'...")
            
            audio_model = model # Fallback to param if config fails
            audio_voice = voice
            
            if hasattr(self, 'config') and self.config:
                audio_model = self.config.get('audio.model', model)
                audio_voice = self.config.get('audio.voice', voice)
            
            audio_response = self.client.audio.speech.create(
                model=audio_model,
                voice=audio_voice,
                input=text,
                response_format="mp3",
                speed=speed
            )
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save audio file
            with open(output_path, "wb") as audio_file:
                audio_file.write(audio_response.content)
            
            print(f"✅ Audio generated successfully: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error generating audio: {e}")
            return False

