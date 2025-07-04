def load_audio_file(file_path):
    """Load an audio file and return its path."""
    if os.path.exists(file_path):
        return file_path
    raise FileNotFoundError(f"Audio file not found: {file_path}")

def format_transcription_result(transcription):
    """Format the transcription result for display."""
    return transcription.strip()

def validate_file_extension(file_path, valid_extensions):
    """Check if the file has a valid extension."""
    return any(file_path.endswith(ext) for ext in valid_extensions)

def get_latest_file(folder_path, valid_extensions):
    """Get the latest file in a folder with specified extensions."""
    files = [f for f in glob.glob(os.path.join(folder_path, '*')) if validate_file_extension(f, valid_extensions)]
    if not files:
        raise FileNotFoundError("No valid files found in the specified folder.")
    return max(files, key=os.path.getmtime)

def save_transcription_to_file(transcription, output_path):
    """Save the transcription result to a text file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(transcription)