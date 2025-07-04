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
    
    def __init__(self):
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
            
            audio_response = self.client.audio.speech.create(
                model=model,
                voice=voice,
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
    
    def generate_audio_with_pauses(self, text: str, output_path: str, 
                                  pause_duration: float = 1.0,
                                  voice: str = None) -> bool:
        """
        Generate audio with automatic pauses at sentence breaks.
        
        Args:
            text: Text to convert to speech
            output_path: Path where to save the audio file
            pause_duration: Duration of pauses in seconds
            voice: Voice to use
        
        Returns:
            bool: True if successful, False otherwise
        """
        
        # Add pauses at sentence endings
        import re
        
        # Split text into sentences and add pauses
        sentences = re.split(r'([.!?]+)', text)
        text_with_pauses = ""
        
        for i, part in enumerate(sentences):
            text_with_pauses += part
            # Add pause after sentence endings (but not at the very end)
            if part.strip() and any(punct in part for punct in '.!?') and i < len(sentences) - 1:
                # Add silence using SSML-like pause (OpenAI TTS doesn't support SSML, so we use periods)
                text_with_pauses += "... "
        
        return self.generate_audio(text_with_pauses, output_path, voice=voice)
    
    def generate_vocabulary_audio(self, vocab_list: list, output_dir: str, 
                                 voice: str = None) -> list:
        """
        Generate individual audio files for each vocabulary word.
        
        Args:
            vocab_list: List of (word, translation, pronunciation) tuples
            output_dir: Directory to save audio files
            voice: Voice to use
        
        Returns:
            list: List of generated file paths
        """
        
        if not vocab_list:
            return []
        
        os.makedirs(output_dir, exist_ok=True)
        generated_files = []
        
        for i, (word, translation, pronunciation) in enumerate(vocab_list, 1):
            # Create text for pronunciation
            if pronunciation:
                text = f"{word}. {pronunciation}. {translation}."
            else:
                text = f"{word}. {translation}."
            
            # Generate filename
            safe_word = "".join(c for c in word if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{i:02d}_{safe_word}.mp3"
            file_path = os.path.join(output_dir, filename)
            
            try:
                if self.generate_audio(text, file_path, voice=voice):
                    generated_files.append(file_path)
                    print(f"  ✓ Generated: {filename}")
                else:
                    print(f"  ✗ Failed: {filename}")
            except Exception as e:
                print(f"  ✗ Error generating {filename}: {e}")
        
        print(f"🎵 Generated {len(generated_files)} vocabulary audio files")
        return generated_files
    
    def get_audio_info(self, file_path: str) -> Optional[dict]:
        """
        Get basic information about an audio file.
        
        Args:
            file_path: Path to the audio file
        
        Returns:
            dict: Audio file information or None if file doesn't exist
        """
        
        if not os.path.exists(file_path):
            return None
        
        try:
            file_size = os.path.getsize(file_path)
            return {
                'file_path': file_path,
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'exists': True
            }
        except Exception as e:
            print(f"Error getting audio info: {e}")
            return None
    
    def set_default_voice(self, voice: str):
        """Set the default voice for audio generation."""
        if voice in self.available_voices:
            self.default_voice = voice
            print(f"✅ Default voice set to: {voice}")
        else:
            print(f"❌ Voice '{voice}' not available. Available voices: {', '.join(self.available_voices)}")
    
    def list_available_voices(self) -> list:
        """Get list of available voices."""
        return self.available_voices.copy()
