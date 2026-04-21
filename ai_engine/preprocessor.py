"""
ai_engine/preprocessor.py
--------------------------
Cleans raw OSINT text directly from the database by record ID.
Writes cleaned content back to the record and marks it ready for pipeline.
"""

import re
import logging
from typing import Optional
from sqlalchemy.orm import Session
from database import SessionLocal
from models import RawOSINT

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Core Text Cleaning
# ──────────────────────────────────────────────

def _clean_text(text: str) -> str:
    """Pure cleaning logic (no DB dependency — can be unit-tested standalone)."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"http\S+", "", text)           # strip URLs
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)   # remove special chars
    text = re.sub(r"\s+", " ", text)              # collapse whitespace
    return text.strip()


# ──────────────────────────────────────────────
# Single Record
# ──────────────────────────────────────────────

def preprocess_record(record_id: int, db: Optional[Session] = None) -> Optional[str]:
    """
    Fetch RawOSINT by ID, clean its content, persist cleaned text
    into extra_metadata['cleaned_content'], return cleaned string.

    Args:
        record_id: Primary key of the RawOSINT row.
        db:        Optional existing session (useful for pipeline chaining).
                   If None, a new session is opened and closed automatically.

    Returns:
        Cleaned text string, or None if record not found.
    """
    _own_session = db is None
    if _own_session:
        db = SessionLocal()

    try:
        record: Optional[RawOSINT] = db.query(RawOSINT).filter(RawOSINT.id == record_id).first()

        if not record:
            logger.warning(f"[Preprocessor] Record ID {record_id} not found.")
            return None

        cleaned = _clean_text(record.content)

        # Persist into metadata so downstream steps can read cleaned_content
        metadata = record.extra_metadata or {}
        metadata["cleaned_content"] = cleaned
        record.extra_metadata = metadata

        if _own_session:
            db.commit()

        logger.info(f"[Preprocessor] ID {record_id} cleaned ({len(cleaned)} chars).")
        return cleaned

    except Exception as e:
        logger.error(f"[Preprocessor] Failed on ID {record_id}: {e}")
        if _own_session:
            db.rollback()
        raise
    finally:
        if _own_session:
            db.close()


# ──────────────────────────────────────────────
# Batch Processing
# ──────────────────────────────────────────────

def preprocess_unprocessed(batch_size: int = 100) -> list[int]:
    """
    Fetch all unprocessed RawOSINT records (processed=False),
    clean them, and return list of successfully processed IDs.

    Args:
        batch_size: Max records to process in one call.

    Returns:
        List of record IDs that were successfully cleaned.
    """
    db = SessionLocal()
    processed_ids = []

    try:
        records = (
            db.query(RawOSINT)
            .filter(RawOSINT.processed == False)  # noqa: E712
            .limit(batch_size)
            .all()
        )

        for record in records:
            cleaned = _clean_text(record.content)
            metadata = record.extra_metadata or {}
            metadata["cleaned_content"] = cleaned
            record.extra_metadata = metadata

        db.commit()
        processed_ids = [r.id for r in records]
        logger.info(f"[Preprocessor] Batch cleaned {len(processed_ids)} records.")

    except Exception as e:
        logger.error(f"[Preprocessor] Batch failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

    return processed_ids


# ──────────────────────────────────────────────
# Convenience helper used by the pipeline
# ──────────────────────────────────────────────

def get_cleaned_content(record_id: int, db: Session) -> Optional[str]:
    """
    Returns already-cleaned content from metadata if available,
    otherwise runs preprocessing on the fly.
    Designed to be called from within a shared pipeline session.
    """
    record: Optional[RawOSINT] = db.query(RawOSINT).filter(RawOSINT.id == record_id).first()
    if not record:
        return None
    metadata = record.extra_metadata or {}
    if "cleaned_content" in metadata:
        return metadata["cleaned_content"]
    # Fallback: clean on the fly without committing (pipeline will commit)
    return _clean_text(record.content)