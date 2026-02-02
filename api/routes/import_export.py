"""Import and export vocabulary endpoints."""

import csv
import json
from io import StringIO
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from supabase import Client
from api.dependencies import get_supabase, get_current_user_id

router = APIRouter(prefix="/api", tags=["import_export"])


class ImportResult(BaseModel):
    """Schema for import result."""
    total_rows: int
    imported: int
    skipped: int
    errors: List[str]


@router.get("/export")
def export_vocabulary(
    format: str = Query(default="csv", pattern="^(csv|json)$"),
    language_from: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Export vocabulary as CSV or JSON."""
    query = db.table("vocabulary").select("*").eq("user_id", user_id)

    if language_from:
        query = query.eq("language_from", language_from)

    result = query.order("created_at", desc=True).execute()
    words = result.data

    if format == "json":
        # Return JSON
        content = json.dumps(words, indent=2, default=str)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=vocabulary.json"}
        )
    else:
        # Return CSV
        output = StringIO()
        if words:
            fieldnames = ["word", "lemma", "translation", "secondary_translation",
                         "language_from", "language_to", "frequency_rank",
                         "frequency_level", "example_sentence_original",
                         "example_sentence_translation", "created_at"]
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(words)

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=vocabulary.csv"}
        )


@router.post("/import", response_model=ImportResult)
async def import_vocabulary(
    file: UploadFile = File(...),
    language_from: str = Query(...),
    language_to: str = Query(...),
    conflict_resolution: str = Query(default="skip", pattern="^(skip|merge|replace)$"),
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """
    Import vocabulary from CSV or JSON file.

    Conflict resolution:
    - skip: Skip words that already exist
    - merge: Update existing words with new data
    - replace: Delete existing and add new
    """
    content = await file.read()
    content_str = content.decode("utf-8")

    # Detect format
    filename = file.filename or ""
    if filename.endswith(".json") or content_str.strip().startswith("["):
        words = json.loads(content_str)
    else:
        # Assume CSV
        reader = csv.DictReader(StringIO(content_str))
        words = list(reader)

    result = ImportResult(total_rows=len(words), imported=0, skipped=0, errors=[])

    for i, word_data in enumerate(words):
        try:
            # Get word and translation from various possible column names
            word = word_data.get("word") or word_data.get("source") or word_data.get("term")
            translation = word_data.get("translation") or word_data.get("target") or word_data.get("meaning")

            if not word or not translation:
                result.errors.append(f"Row {i+1}: Missing word or translation")
                result.skipped += 1
                continue

            # Check if exists
            existing = db.table("vocabulary").select("id").eq("user_id", user_id).eq("word", word).eq("language_from", language_from).execute()

            if existing.data:
                if conflict_resolution == "skip":
                    result.skipped += 1
                    continue
                elif conflict_resolution == "merge":
                    # Update existing
                    update_data = {
                        "translation": translation,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    # Add optional fields if present
                    for field in ["lemma", "secondary_translation", "frequency_rank"]:
                        if word_data.get(field):
                            update_data[field] = word_data[field]

                    db.table("vocabulary").update(update_data).eq("id", existing.data[0]["id"]).execute()
                    result.imported += 1
                    continue
                elif conflict_resolution == "replace":
                    # Delete existing
                    db.table("vocabulary").delete().eq("id", existing.data[0]["id"]).execute()

            # Insert new
            new_word = {
                "user_id": user_id,
                "word": word,
                "lemma": word_data.get("lemma") or word,
                "translation": translation,
                "language_from": language_from,
                "language_to": language_to,
                "secondary_translation": word_data.get("secondary_translation"),
                "frequency_rank": word_data.get("frequency_rank"),
                "frequency_level": word_data.get("frequency_level"),
                "example_sentence_original": word_data.get("example_sentence_original"),
                "example_sentence_translation": word_data.get("example_sentence_translation")
            }

            db.table("vocabulary").insert(new_word).execute()
            result.imported += 1

        except Exception as e:
            result.errors.append(f"Row {i+1}: {str(e)}")
            result.skipped += 1

    return result
