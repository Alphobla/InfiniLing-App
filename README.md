# InfiniLing 🌐

InfiniLing is a smart language learning application that leverages AI to generate personalized vocabulary practice and immersive stories. By using OpenAI's powerful language models, it creates a unique learning experience tailored to your database of vocabulary words.

## ✨ Features

- **AI-Powered Story Generation**: Generates contextual stories using your target vocabulary.
- **Natural Text-to-Speech**: High-quality audio generation for listening practice.
- **Spaced Repetition System (SRS)**: Optimized learning intervals to help you remember words longer.
- **Cross-Platform**: Designed to run on both Windows and macOS.
- **Customizable**: Tweak generation parameters, voices, and window sizes via `config.json`.

## 📦 Professional Distribution

For the best experience, users can download the latest version of InfiniLing directly from the **[Releases](https://github.com/yourusername/InfiniLing/releases)** page.

- **Windows**: Download `InfiniLing-Windows.exe` and run it directly.
- **macOS**: Download `InfiniLing-macOS.zip`, extract it, and run the `InfiniLing.app`.

> [!NOTE]  
> VLC Media Player must still be installed on your system for audio playback to function in the standalone app.

## 🚀 Getting Started (Developers)

### Prerequisites

- **Python 3.10+**
- **VLC Media Player**: Required for audio playback.
  - **Windows**: [Download VLC](https://www.videolan.org/vlc/download-windows.html)
  - **macOS**: `brew install --cask vlc` or [Download VLC](https://www.videolan.org/vlc/download-macosx.html)
- **OpenAI API Key**: Required for text and audio generation.

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/InfiniLing.git
   cd InfiniLing
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   - Copy `.env.example` to `.env`.
   - Add your [OpenAI API Key](https://platform.openai.com/api-keys) to the `.env` file.

   ```bash
   cp .env.example .env  # macOS/Linux
   copy .env.example .env # Windows
   ```

### Running the App

```bash
python main.py
```

## 🛠 Configuration

The application behavior can be customized in `config.json`. You can adjust:
- Language pairs (e.g., French to German).
- Audio voices and models.
- UI dimensions and colors.
- Spaced repetition parameters.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an issue.

---
*Created with ❤️ for language learners.*
