"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import vocabulary, user, generate, import_export, starter_words, podcast
from api.services.languages import get_all_languages

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
app.include_router(podcast.router)


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
