# InfiniLing Project Reorganization Plan

## Current Assessment (Completed)
✅ **Dependencies**: All required packages installed and working  
✅ **Virtual Environment**: Using Windows venv via WSL successfully (`./venv/Scripts/python.exe`)  
✅ **Application**: Launches and runs without errors  
✅ **Cleanup**: Removed unnecessary files, clean requirements.txt  

## Project Structure Migration

### Current Structure
```
src/
├── main.py
├── ui/
│   ├── main_menu.py
│   ├── vocabulary_interface.py
│   └── whisper_interface.py
├── vocabulary/
│   ├── audio_generator.py
│   ├── git_database_manager.py
│   ├── main_orchestrator.py
│   ├── review_interface.py
│   ├── text_generator_clean.py
│   └── vocabulary_selector.py
└── whisper_mode/
    └── transcriber.py
```

### Target Structure (Simple & Beginner-Friendly)
```
src/
├── main.py                 # App entry point
├── config.py              # All settings in one place
│
├── transcriber/           # Audio-to-text module (rename from whisper_mode)
│   ├── __init__.py
│   ├── transcriber.py     # Core transcription logic
│   └── ui.py             # Transcription interface (from whisper_interface.py)
│
├── gentexter/            # Text generation module (rename from vocabulary)
│   ├── __init__.py
│   ├── orchestrator.py   # Main logic (from main_orchestrator.py)
│   ├── selector.py       # Word selection (from vocabulary_selector.py)
│   ├── text_generator.py # Text generation (from text_generator_clean.py)
│   ├── audio_generator.py # Keep as is
│   ├── database.py       # Database management (from git_database_manager.py)
│   ├── reviewer.py       # Review logic (from review_interface.py)
│   └── ui.py            # Gentexter interface (from vocabulary_interface.py)
│
├── shared/               # Common utilities
│   ├── __init__.py
│   └── menu.py          # Main menu (from ui/main_menu.py)
│
├── data/                # Keep as is
└── requirements.txt     # Keep as is
```

## Migration Steps

### Step 1: Create New Directory Structure
```bash
cd src/
mkdir -p transcriber gentexter shared
touch transcriber/__init__.py gentexter/__init__.py shared/__init__.py
```

### Step 2: Move and Rename Files
```bash
# Transcriber module
mv whisper_mode/transcriber.py transcriber/transcriber.py
mv ui/whisper_interface.py transcriber/ui.py

# Gentexter module  
mv vocabulary/main_orchestrator.py gentexter/orchestrator.py
mv vocabulary/vocabulary_selector.py gentexter/selector.py
mv vocabulary/text_generator_clean.py gentexter/text_generator.py
mv vocabulary/audio_generator.py gentexter/audio_generator.py
mv vocabulary/git_database_manager.py gentexter/database.py
mv vocabulary/review_interface.py gentexter/reviewer.py
mv ui/vocabulary_interface.py gentexter/ui.py

# Shared utilities
mv ui/main_menu.py shared/menu.py

# Clean up empty directories
rmdir ui/ vocabulary/ whisper_mode/
```

### Step 3: Update Import Statements

#### In main.py:
Change: `from ui.main_menu import MainMenu`
To: `from shared.menu import MainMenu`

#### In shared/menu.py:
Change: `from ui.whisper_interface import WhisperInterface`
To: `from transcriber.ui import WhisperInterface`

Change: `from ui.vocabulary_interface import VocabularyInterface`  
To: `from gentexter.ui import VocabularyInterface`

#### In transcriber/ui.py:
Change: `from whisper_mode.transcriber import Transcriber`
To: `from .transcriber import Transcriber`

#### In gentexter/ui.py:
Update all relative imports from vocabulary/* to use relative imports:
- `from vocabulary.main_orchestrator import MainOrchestrator` → `from .orchestrator import MainOrchestrator`
- `from vocabulary.vocabulary_selector import VocabularySelector` → `from .selector import VocabularySelector`
- etc.

### Step 4: Create Unified Config
Create `src/config.py` with all configuration settings consolidated.

### Step 5: Test Application
```bash
cd src/
../venv/Scripts/python.exe main.py
```

## Key Benefits of New Structure

1. **Clear Module Names**: `transcriber` and `gentexter` - immediately obvious
2. **Flat Organization**: Only 3 directories, not overwhelming for beginners  
3. **Logical Grouping**: Each module contains its logic + UI together
4. **Simple Imports**: Easy to remember where things are
5. **Room to Grow**: Can add features without restructuring

## Status
- [x] Analysis completed
- [x] Structure designed  
- [x] Migration plan created
- [ ] **NEXT**: Execute migration in IDE session
- [ ] Update all import statements
- [ ] Test functionality
- [ ] Create unified config.py

## Notes for IDE Session
- Use Windows Python: `./venv/Scripts/python.exe`
- All dependencies already installed
- App currently works, just needs restructuring
- Focus on updating imports after file moves