import whisper
import os
import glob
import sys
import shutil
import subprocess
import webbrowser
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

def transcribe_and_write_srt(mp3_path, srt_path, language="fr", model_size="tiny"):
    model = whisper.load_model(model_size)
    print(f"Transcribing {mp3_path} with Whisper model '{model_size}'...")
    result = model.transcribe(mp3_path, language=language, verbose=False)
    segments = result["segments"]

    total = len(segments)
    print(f"Writing SRT ({total} segments):")
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments):
            start = seg["start"] # type: ignore
            end = seg["end"] # type: ignore
            text = seg["text"].strip() # type: ignore
            f.write(f"{i+1}\n")
            f.write(f"{format_srt_time(start)} --> {format_srt_time(end)}\n")
            f.write(f"{text}\n\n")
            # Progress indicator
            if (i + 1) % 10 == 0 or (i + 1) == total:
                percent = int((i + 1) / total * 100)
                sys.stdout.write(f"\rProgress: {i+1}/{total} ({percent}%)")
                sys.stdout.flush()
    print("\nSRT file saved:", srt_path)

def format_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def get_base_filename(path):
    return os.path.splitext(os.path.basename(path))[0]

def get_title_from_mp3(mp3_path):
    try:
        audio = MP3(mp3_path, ID3=EasyID3)
        title = audio.get('title', [None])[0]
        if title:
            # Clean up title for filename usage
            title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).rstrip()
            return title
    except Exception:
        pass
    # fallback: use base filename without extension
    return os.path.splitext(os.path.basename(mp3_path))[0]

if __name__ == "__main__":
    # Model selection (multilingual only)
    print("Select a Whisper multilingual model:")
    print("1. tiny (~1GB VRAM, ~10x speed)")
    print("2. base (~1GB VRAM, ~7x speed)")
    print("3. small (~2GB VRAM, ~4x speed)")
    print("4. medium (~5GB VRAM, ~2x speed)")
    print("5. large (~10GB VRAM, 1x speed)")
    print("6. turbo (~6GB VRAM, ~8x speed)")
    choice = input("Enter the number of the model you want to use: ")
    model_map = {
        "1": "tiny",
        "2": "base",
        "3": "small",
        "4": "medium",
        "5": "large",
        "6": "turbo"
    }
    model_size = model_map.get(choice, "small")  # default to 'small' if invalid input
    print(f"Using model: {model_size}")

    # Find newest mp3 in Downloads
    downloads_folder = os.path.expanduser('~/Downloads')
    mp3_files = glob.glob(os.path.join(downloads_folder, '*.mp3'))
    if not mp3_files:
        print(f"No mp3 files found in {downloads_folder}.")
        sys.exit(1)
    newest_mp3 = max(mp3_files, key=os.path.getmtime)
    print(f"Newest mp3 found: {newest_mp3}")

    # Copy to Web_App with original name
    web_app_folder = os.path.join(os.path.dirname(__file__), "Web_App")
    if not os.path.exists(web_app_folder):
        os.makedirs(web_app_folder)
    base_name = get_title_from_mp3(newest_mp3)
    target_mp3 = os.path.join(web_app_folder, f"{base_name}.mp3")
    shutil.copy2(newest_mp3, target_mp3)
    print(f"Copied to: {target_mp3}")

    # Transcribe and write SRT with original name
    srt_path = os.path.join(web_app_folder, f"{base_name}.srt")
    transcribe_and_write_srt(target_mp3, srt_path, language="fr", model_size=model_size)

    # Start HTTP server in Web_App folder
    print("Starting local web server in Web_App folder...")
    server_proc = subprocess.Popen([
        sys.executable, "-m", "http.server", "--directory", web_app_folder
    ], cwd=web_app_folder)
    print("Opening browser to http://localhost:8000/index.html ...")
    webbrowser.open("http://localhost:8000/")
    print("Press Ctrl+C to stop the server.")
    server_proc.wait()


