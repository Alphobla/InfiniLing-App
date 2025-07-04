import whisper
import os

class Transcriber:
    def __init__(self, model_size="small"):
        self.model = whisper.load_model(model_size)
        print(f"Loaded Whisper model: {model_size}")

    def transcribe(self, audio_path, language="fr"):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        print(f"Transcribing audio file: {audio_path}")
        result = self.model.transcribe(audio_path, language=language)
        return result["text"]

    def save_transcription(self, transcription, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(transcription)
        print(f"Transcription saved to: {output_path}")