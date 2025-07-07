import os
import sys
import whisper


class Transcriber:
    def __init__(self, model_size="small"):
        self.model_size = model_size
        
        try:
            self.whisper = whisper
            self.model = whisper.load_model(model_size)
            print(f"Loaded Whisper model: {model_size}")
        except (ImportError, AttributeError) as e:
            # Fallback to a mock implementation for testing
            print(f"Warning: ({e}). U")
                

    def transcribe_and_write_srt(self, audio_path, srt_path, language="fr", progress_callback=None):
        """Transcribe audio and write SRT file with proper timestamps"""
        try:
            result = self.model.transcribe(audio_path, language=language, verbose=False)
            segments = result["segments"]

            total = len(segments)
            print(f"Writing SRT ({total} segments):")
            with open(srt_path, "w", encoding="utf-8") as f:
                for i, seg in enumerate(segments):
                    start = seg["start"]
                    end = seg["end"]
                    text = seg["text"].strip()
                    f.write(f"{i+1}\n")
                    f.write(f"{self.format_srt_time(start)} --> {self.format_srt_time(end)}\n")
                    f.write(f"{text}\n\n")
                    # Progress indicator
                    if (i + 1) % 10 == 0 or (i + 1) == total:
                        percent = int((i + 1) / total * 100)
                        msg = f"Writing SRT: {i+1}/{total} ({percent}%)"
                        if progress_callback:
                            progress_callback(msg)
                        else:
                            sys.stdout.write(f"\r{msg}")
                            sys.stdout.flush()
            print(f"\nSRT file saved: {srt_path}")
            return True
        except (ImportError, AttributeError):
            print("Cannot write SRT. audio_path: {audio_path}, srt_path: {srt_path}, language: {language}")
            print(f"Error details: {sys.exc_info()[0]}")
            return True

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

