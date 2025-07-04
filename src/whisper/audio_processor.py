from pydub import AudioSegment
import os

class AudioProcessor:
    def __init__(self, audio_path):
        self.audio_path = audio_path
        self.audio_segment = None

    def load_audio(self):
        """Load audio file and prepare it for transcription."""
        if not os.path.exists(self.audio_path):
            raise FileNotFoundError(f"Audio file not found: {self.audio_path}")
        
        self.audio_segment = AudioSegment.from_file(self.audio_path)
        print(f"Loaded audio file: {self.audio_path}")

    def get_duration(self):
        """Get the duration of the audio in seconds."""
        if self.audio_segment is None:
            raise ValueError("Audio not loaded. Please load the audio first.")
        
        return len(self.audio_segment) / 1000.0  # Convert milliseconds to seconds

    def export_audio(self, export_path, format='wav'):
        """Export the audio to a specified format."""
        if self.audio_segment is None:
            raise ValueError("Audio not loaded. Please load the audio first.")
        
        self.audio_segment.export(export_path, format=format)
        print(f"Exported audio to: {export_path}")