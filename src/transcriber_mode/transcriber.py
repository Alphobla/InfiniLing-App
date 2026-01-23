import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class Transcriber:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env file or pass as parameter.")

        self.client = OpenAI(api_key=self.api_key)
        print("Initialized OpenAI Whisper API transcriber")

    def transcribe_and_write_srt(self, audio_path, srt_path, language=None, progress_callback=None):
        """Transcribe audio using OpenAI API and write SRT file with proper timestamps"""
        try:
            if progress_callback:
                progress_callback("Uploading audio to OpenAI...", 10)

            with open(audio_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )

            if progress_callback:
                progress_callback("Processing transcription...", 80)

            segments = transcription.segments
            total = len(segments)

            print(f"Writing SRT ({total} segments):")
            with open(srt_path, "w", encoding="utf-8") as f:
                for i, seg in enumerate(segments):
                    start = seg.start
                    end = seg.end
                    text = seg.text.strip()
                    f.write(f"{i+1}\n")
                    f.write(f"{self.format_srt_time(start)} --> {self.format_srt_time(end)}\n")
                    f.write(f"{text}\n\n")

                # Add transcription date at the end
                f.write(f"# TRANSCRIBED: {datetime.now().isoformat()}\n")

            if progress_callback:
                progress_callback("Complete!", 100)

            print(f"\nSRT file saved: {srt_path}")
            return True
        except Exception as e:
            print(f"Transcription error: {e}")
            return False

    def format_srt_time(self, seconds):
        """Format seconds to SRT time format (HH:MM:SS,mmm)"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    def save_transcription(self, transcription, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(transcription)
        print(f"Transcription saved to: {output_path}")
