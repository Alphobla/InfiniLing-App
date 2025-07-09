import os
import sys
import whisper
import re
import io


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
            # Get audio duration first for progress calculation
            if progress_callback:
                # Load audio to get duration
                audio = whisper.load_audio(audio_path)
                duration = len(audio) / whisper.audio.SAMPLE_RATE
                
                old_stdout = sys.stdout
                captured = io.StringIO()
                
                class ProgressCapture:
                    def __init__(self, duration, callback):
                        self.duration = duration
                        self.callback = callback
                    
                    def write(self, text):
                        captured.write(text)
                        old_stdout.write(text)  # Still show in terminal
                        
                        # Parse segment timestamps from verbose output
                        # Look for lines like "[00:20.000 --> 00:25.000]"
                        match = re.search(r'\[(\d{2}):(\d{2}\.\d{3}) --> (\d{2}):(\d{2}\.\d{3})\]', text)
                        if match:
                            # Extract end time
                            end_min = int(match.group(3))
                            end_sec = float(match.group(4))
                            current_time = end_min * 60 + end_sec
                            
                            # Calculate progress as percentage
                            if self.duration > 0:
                                percent = min(100, int((current_time / self.duration) * 100))
                                self.callback(f"Transcribing... {percent}%", percent)
                    
                    def flush(self):
                        captured.flush()
                        old_stdout.flush()
                
                sys.stdout = ProgressCapture(duration, progress_callback)
                result = self.model.transcribe(audio_path, language=language, verbose=True)
                sys.stdout = old_stdout
            else:
                result = self.model.transcribe(audio_path, language=language, verbose=True)
            
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

