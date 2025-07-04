# Unified Language Application

This project combines audio transcription and vocabulary learning features into a unified application. Users can choose between two modes: **Whisper-mode** for audio-to-text transcription using OpenAI's Whisper model, and **Wordstory-mode** for vocabulary review and learning.

## Features

- **Whisper-mode**: 
  - Transcribe audio files to text using the Whisper model.
  - Supports multiple audio formats (e.g., MP3, WAV).
  - Displays transcription results in a user-friendly interface.

- **Wordstory-mode**: 
  - Load vocabulary files and review vocabulary through interactive sessions.
  - Generate contextual stories using vocabulary words.
  - Track word usage and manage spaced repetition for effective learning.

## Project Structure

```
unified-language-app
├── src
│   ├── main.py                     # Entry point of the application
│   ├── ui                          # User interface components
│   │   ├── __init__.py             # Marks the ui directory as a package
│   │   ├── main_menu.py             # Main menu interface for mode selection
│   │   ├── whisper_interface.py      # UI for Whisper audio transcription
│   │   └── vocabulary_interface.py    # UI for vocabulary review
│   ├── whisper                      # Whisper transcription logic
│   │   ├── __init__.py             # Marks the whisper directory as a package
│   │   ├── transcriber.py           # Logic for transcribing audio files
│   │   └── audio_processor.py       # Handles audio file operations
│   ├── vocabulary                   # Vocabulary management features
│   │   ├── __init__.py             # Marks the vocabulary directory as a package
│   │   ├── file_manager.py          # Manages vocabulary file operations
│   │   ├── vocabulary_loader.py     # Loads vocabulary data from files
│   │   ├── word_tracker.py          # Tracks word usage statistics
│   │   ├── text_generator.py        # Generates contextual stories
│   │   └── reviewer.py              # Functionality for reviewing vocabulary
│   ├── shared                       # Shared utilities and configurations
│   │   ├── __init__.py             # Marks the shared directory as a package
│   │   ├── config.py                # Configuration settings
│   │   └── utils.py                 # Utility functions
│   └── web_assets                   # Web interface assets
│       ├── index.html               # Main HTML file for the web interface
│       ├── style.css                # Styles for the web interface
│       └── script.js                # JavaScript for dynamic content
├── data                             # Data files
│   ├── word_tracking.json           # Stores word tracking data
│   └── app_settings.json            # Stores application settings
├── requirements.txt                 # Project dependencies
├── .env.example                     # Example environment variables
├── setup.py                         # Packaging information
└── # 🌍 Unified Language App

A comprehensive language learning application that combines audio transcription and vocabulary review in one unified interface.

## Features

### 🎤 Whisper Mode (Audio-to-Text)
- AI-powered audio transcription using OpenAI Whisper
- Support for multiple audio formats (MP3, WAV, M4A, FLAC, AAC, OGG)
- Real-time transcription with progress feedback
- Save transcriptions to text files
- Modern, intuitive interface

### 📚 Wordstory Mode (Vocabulary Review)
- Load vocabulary from CSV/Excel files
- Intelligent spaced repetition system
- Track difficult words automatically
- Multiple review modes:
  - Full review session
  - Quick review (5 words)
  - Difficult words only
- Modern UI with progress tracking

## Quick Start

### Option 1: Using the Batch File (Recommended)
1. Double-click `launch_app.bat`
2. The application will automatically:
   - Create a virtual environment
   - Install required packages
   - Launch the app

### Option 2: Manual Setup
1. Install Python 3.7 or later
2. Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   cd src
   python main.py
   ```

## Usage

### Whisper Mode
1. Click "🎤 Whisper Mode" from the main menu
2. Browse and select an audio file
3. Click "🎯 Start Transcription"
4. Wait for the AI to process your audio
5. Save the transcription as a text file

### Wordstory Mode
1. Click "📚 Wordstory Mode" from the main menu
2. Load a vocabulary file (CSV or Excel format)
3. Choose your review mode:
   - **Full Review**: Review all vocabulary
   - **Quick Review**: Review 5 random words
   - **Difficult Words**: Focus on challenging words
4. Follow the interactive review session

## File Formats

### Vocabulary Files
- **CSV**: Columns should be: word, translation, context
- **Excel**: Same structure as CSV
- **Example**:
  ```
  word,translation,context
  bonjour,hello,greeting
  au revoir,goodbye,farewell
  ```

### Audio Files
Supported formats: MP3, WAV, M4A, FLAC, AAC, OGG

## System Requirements

- Windows 10/11
- Python 3.7+
- Minimum 4GB RAM (8GB recommended for large audio files)
- Internet connection for initial setup

## Troubleshooting

### Common Issues
1. **"Python not found"**: Install Python from python.org
2. **Import errors**: Run `pip install -r requirements.txt`
3. **Audio not loading**: Check file format and path
4. **Slow transcription**: Large audio files take time to process

### Getting Help
- Check the console output for detailed error messages
- Ensure all requirements are installed
- Try restarting the application

## File Structure
```
unified-language-app/
├── launch_app.bat          # Easy launcher
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── src/
│   ├── main.py            # Application entry point
│   ├── ui/                # User interface modules
│   ├── whisper/           # Audio transcription
│   ├── vocabulary/        # Vocabulary management
│   └── shared/            # Shared utilities
└── data/                  # Application data
```

## License

This project is for educational and personal use.

---

**Happy learning! 🎓**                        # Project documentation
```

## Installation

1. Clone the repository:
   ```sh
   git clone <repository-url>
   cd unified-language-app
   ```

2. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Set up environment variables as needed by copying `.env.example` to `.env` and filling in the required values.

## Usage

To run the application, execute the following command:

```sh
python src/main.py
```

Follow the on-screen instructions to choose between Whisper-mode and Wordstory-mode.

## Testing

Unit tests can be run using Python's `unittest` framework. To execute tests, navigate to the `src` directory and run:

```sh
python -m unittest discover
```

## License

This project is licensed under the MIT License.

## Author

Valentin Maissen