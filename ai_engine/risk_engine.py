"""
ai_engine/risk_engine.py
-------------------------
Calculates severity + risk score for a RawOSINT record by ID.
Writes severity and risk_score back to the DB row.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session
from database import SessionLocal
from models import RawOSINT

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Severity & Risk Configuration
# (edit values here to tune scoring — no logic changes needed)
# ──────────────────────────────────────────────

SEVERITY_MAPPING: dict[str, int] = {
    "terrorism":          5,
    "cyber_attack":       4,
    "border_tension":     4,
    "military_activity":  3,
    "civil_unrest":       2,
    "natural_disaster":   2,
    "other":              1,
}

# Text label for each severity int
SEVERITY_LABELS: dict[int, str] = {
    5: "critical",
    4: "high",
    3: "medium",
    2: "low",
    1: "minimal",
}

# Risk formula weights
SEVERITY_WEIGHT  = 0.35   # contribution from incident type
GEO_WEIGHT       = 0.05   # per detected location (capped)
GEO_CAP          = 0.20   # max geo contribution
SOURCE_WEIGHT    = 0.02   # per corroborating source (capped)
SOURCE_CAP       = 0.10   # max source contribution
CONFIDENCE_FLOOR = 0.50   # minimum confidence to trust classification


# ──────────────────────────────────────────────
# Pure calculation helpers
# ──────────────────────────────────────────────

def _get_severity_level(incident_type: Optional[str]) -> int:
    return SEVERITY_MAPPING.get(incident_type or "other", 1)


def _get_severity_label(level: int) -> str:
    return SEVERITY_LABELS.get(level, "minimal")


def _calculate_risk_score(
    severity_level: int,
    location_count: int = 1,
    source_count: int = 1,
    confidence: float = 1.0,
) -> float:
    """
    Composite risk score in [0.0, 1.0].

    Formula:
        risk = (severity_weight * severity_level/5)
               + min(location_count * geo_weight, geo_cap)
               + min(source_count * source_weight, source_cap)
               * confidence_multiplier
    """
    severity_component = SEVERITY_WEIGHT * (severity_level / 5)
    geo_component      = min(location_count * GEO_WEIGHT, GEO_CAP)
    source_component   = min(source_count * SOURCE_WEIGHT, SOURCE_CAP)

    # Penalise low-confidence classifications
    confidence_multiplier = max(confidence, CONFIDENCE_FLOOR)

    raw = (severity_component + geo_component + source_component) * confidence_multiplier
    return round(min(raw, 1.0), 4)


# ──────────────────────────────────────────────
# Single Record
# ──────────────────────────────────────────────

def score_record(record_id: int, db: Optional[Session] = None) -> Optional[dict]:
    """
    Calculate and persist severity + risk_score for a RawOSINT record.

    Reads:   incident_type, confidence, extra_metadata (location_count, source_count)
    Writes:  severity, risk_score

    Args:
        record_id: PK of the RawOSINT row.
        db:        Optional shared session.

    Returns:
        Dict {severity, severity_level, risk_score} or None if not found.
    """
    _own_session = db is None
    if _own_session:
        db = SessionLocal()

    try:
        record: Optional[RawOSINT] = db.query(RawOSINT).filter(RawOSINT.id == record_id).first()

        if not record:
            logger.warning(f"[RiskEngine] Record ID {record_id} not found.")
            return None

        metadata = record.extra_metadata or {}

        severity_level = _get_severity_level(record.incident_type)
        location_count = metadata.get("location_count", 1)
        source_count   = metadata.get("source_count", 1)
        confidence     = record.confidence or 1.0

        risk_score     = _calculate_risk_score(severity_level, location_count, source_count, confidence)
        severity_label = _get_severity_label(severity_level)

        record.severity   = severity_label
        record.risk_score = risk_score

        if _own_session:
            db.commit()

        result = {
            "severity":       severity_label,
            "severity_level": severity_level,
            "risk_score":     risk_score,
        }

        logger.info(f"[RiskEngine] ID {record_id} → severity={severity_label}, risk={risk_score}")
        return result

    except Exception as e:
        logger.error(f"[RiskEngine] Failed on ID {record_id}: {e}")
        if _own_session:
            db.rollback()
        raise
    finally:
        if _own_session:
            db.close()


# ──────────────────────────────────────────────
# Batch Processing
# ──────────────────────────────────────────────

def score_unscored(batch_size: int = 100) -> dict[int, float]:
    """
    Score all records where risk_score is NULL.

    Returns:
        Dict of {record_id: risk_score}.
    """
    db = SessionLocal()
    results: dict[int, float] = {}

    try:
        records = (
            db.query(RawOSINT)
            .filter(RawOSINT.risk_score == None)  # noqa: E711
            .limit(batch_size)
            .all()
        )

        for record in records:
            metadata       = record.extra_metadata or {}
            severity_level = _get_severity_level(record.incident_type)
            location_count = metadata.get("location_count", 1)
            source_count   = metadata.get("source_count", 1)
            confidence     = record.confidence or 1.0

            risk_score     = _calculate_risk_score(severity_level, location_count, source_count, confidence)
            severity_label = _get_severity_label(severity_level)

            record.severity   = severity_label
            record.risk_score = risk_score
            results[record.id] = risk_score

        db.commit()
        logger.info(f"[RiskEngine] Batch scored {len(results)} records.")

    except Exception as e:
        logger.error(f"[RiskEngine] Batch failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

    return results