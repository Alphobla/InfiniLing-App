"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import vocabulary, user, generate, import_export, starter_words
from src.shared.languages import get_all_languages

app = FastAPI(
    title="InfiniLing API",
    description="Language learning API with spaced repetition",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(vocabulary.router)
app.include_router(user.router)
app.include_router(generate.router)
app.include_router(import_export.router)
app.include_router(starter_words.router)


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/languages")
def get_languages():
    """Get list of all supported languages (public endpoint)."""
    return {
        "languages": [
            {"code": code, "name": name}
            for name, code in get_all_languages()
        ]
    }


@app.get("/api/debug/tatoeba")
def debug_tatoeba(word: str = "Hund", lang_from: str = "de", lang_to: str = "en"):
    """Debug endpoint to test Tatoeba integration."""
    from api.services.tatoeba_service import get_example_sentence
    import time

    start = time.time()
    try:
        result = get_example_sentence(word, lang_from, lang_to)
        elapsed = time.time() - start
        return {
            "word": word,
            "lang_from": lang_from,
            "lang_to": lang_to,
            "result": result,
            "elapsed_seconds": round(elapsed, 2)
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "elapsed_seconds": round(elapsed, 2)
        }


@app.get("/api/debug/tatoeba-with-lemma")
def debug_tatoeba_with_lemma(word: str = "der Hund", lang_from: str = "de", lang_to: str = "en"):
    """Debug: test Tatoeba with a lemma (like after GPT enhancement)."""
    from api.services.tatoeba_service import get_example_sentence
    import time

    start = time.time()
    try:
        # This is exactly what happens in the enhance endpoint
        result = get_example_sentence(word, lang_from, lang_to)
        elapsed = time.time() - start

        example_original = None
        example_translation = None
        if result:
            example_original = result.get("original")
            example_translation = result.get("translation")

        return {
            "input_word": word,
            "lang_from": lang_from,
            "lang_to": lang_to,
            "raw_result": result,
            "example_original": example_original,
            "example_translation": example_translation,
            "elapsed_seconds": round(elapsed, 2)
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "elapsed_seconds": round(elapsed, 2)
        }
