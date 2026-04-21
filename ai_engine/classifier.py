"""
ai_engine/classifier.py
------------------------
Classifies a RawOSINT record by ID using keyword rules.
Writes the incident_type back to the DB row.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session
from database import SessionLocal
from models import RawOSINT
from ai_engine.preprocessor import get_cleaned_content

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Classification Rules
# (extend this dict to add new categories — no code changes needed elsewhere)
# ──────────────────────────────────────────────

CLASSIFICATION_RULES: dict[str, list[str]] = {
    "cyber_attack": [
        "cyber", "hack", "malware", "ransomware", "phishing",
        "ddos", "breach", "exploit", "zero-day", "intrusion",
    ],
    "border_tension": [
        "infiltration", "ceasefire", "line of control",
        "loc", "surgical strike", "cross-border", "incursion",
        "border tension", "border dispute", "border standoff",
    ],
    "military_activity": [
        "military", "army", "airstrike", "missile", "troops",
        "deployment", "naval", "warship", "fighter jet", "artillery",
        "border patrol", "near the border", "border security",
    ],
    "civil_unrest": [
        "protest", "riot", "violence", "demonstration", "mob",
        "curfew", "bandh", "agitation", "clashes", "pellet",
    ],
    "terrorism": [
        "terrorist", "bomb", "explosion", "ied", "suicide bomber",
        "attack", "casualties", "blast", "fidayeen",
    ],
    "natural_disaster": [
        "flood", "earthquake", "cyclone", "landslide", "tsunami",
        "drought", "wildfire", "relief camp",
    ],
}


def _classify_text(text: str) -> str:
    """
    Keyword-based classifier. Returns the first matched category
    or 'other' if nothing matches.
    """
    if not text:
        return "other"

    lower = text.lower()
    for incident_type, keywords in CLASSIFICATION_RULES.items():
        for kw in keywords:
            if kw in lower:
                return incident_type
    return "other"


# ──────────────────────────────────────────────
# Single Record
# ──────────────────────────────────────────────

def classify_record(record_id: int, db: Optional[Session] = None) -> Optional[str]:
    """
    Classify a single RawOSINT record by ID.
    Reads cleaned content from metadata (or falls back to raw content),
    writes incident_type back to the DB row.

    Args:
        record_id: PK of the RawOSINT row.
        db:        Optional shared session.

    Returns:
        incident_type string, or None if record not found.
    """
    _own_session = db is None
    if _own_session:
        db = SessionLocal()

    try:
        record: Optional[RawOSINT] = db.query(RawOSINT).filter(RawOSINT.id == record_id).first()

        if not record:
            logger.warning(f"[Classifier] Record ID {record_id} not found.")
            return None

        text = get_cleaned_content(record_id, db) or record.content
        incident_type = _classify_text(text)

        record.incident_type = incident_type

        if _own_session:
            db.commit()

        logger.info(f"[Classifier] ID {record_id} → {incident_type}")
        return incident_type

    except Exception as e:
        logger.error(f"[Classifier] Failed on ID {record_id}: {e}")
        if _own_session:
            db.rollback()
        raise
    finally:
        if _own_session:
            db.close()


# ──────────────────────────────────────────────
# Batch Processing
# ──────────────────────────────────────────────

def classify_unclassified(batch_size: int = 100) -> dict[int, str]:
    """
    Classify all records where incident_type is NULL.

    Returns:
        Dict of {record_id: incident_type} for all processed records.
    """
    db = SessionLocal()
    results: dict[int, str] = {}

    try:
        records = (
            db.query(RawOSINT)
            .filter(RawOSINT.incident_type == None)  # noqa: E711
            .limit(batch_size)
            .all()
        )

        for record in records:
            text = (record.extra_metadata or {}).get("cleaned_content") or record.content
            incident_type = _classify_text(text)
            record.incident_type = incident_type
            results[record.id] = incident_type

        db.commit()
        logger.info(f"[Classifier] Batch classified {len(results)} records.")

    except Exception as e:
        logger.error(f"[Classifier] Batch failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

    return results