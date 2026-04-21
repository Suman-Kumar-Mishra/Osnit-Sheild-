import logging
from typing import Optional
from sqlalchemy.orm import Session
from database import SessionLocal
from models import RawOSINT

logger = logging.getLogger(__name__)

# 1. Templates Update: Defense-related logic yahan hai
SUMMARY_TEMPLATES: dict[str, str] = {
    "cyber_attack": "A cyber-related incident has been detected in {location}. Risk level: {severity}.",
    "border_tension": "Border tension activity has been reported near {location}. Risk level: {severity}.",
    "military_activity": "Increased military presence observed in {location}. Risk level: {severity}.",
    "civil_unrest": "Civil unrest signals emerging from {location}. Risk level: {severity}.",
    "terrorism": "A potential terrorism-related incident flagged in {location}. Risk level: {severity}.",
    "natural_disaster": "A natural disaster event has been detected in {location}. Risk level: {severity}.",
    "other": (
        "General activity detected in {location}. Based on current analysis, "
        "this incident does not appear to be directly related or connected to defense or national security. "
        "Risk level: {severity}."
    ),
}

def _build_location(state: Optional[str], country: Optional[str]) -> str:
    if state and country: return f"{state}, {country}"
    return state or country or "an unidentified location"

def _generate_summary(incident_type, state, country, severity, source=None) -> str:
    template = SUMMARY_TEMPLATES.get(incident_type or "other", SUMMARY_TEMPLATES["other"])
    location = _build_location(state, country)
    summary = template.format(location=location, severity=severity or "unknown")
    if source: summary += f" Source: {source}."
    return summary

def summarize_record(record_id: int, db: Optional[Session] = None) -> Optional[str]:
    _own_session = db is None
    if _own_session: db = SessionLocal()
    try:
        record = db.query(RawOSINT).filter(RawOSINT.id == record_id).first()
        if not record: return None

        summary = _generate_summary(record.incident_type, record.state, record.country, record.severity, record.source)

        # FIX: Direct main summary column mein data save hoga
        record.summary = summary 
        
        if _own_session: db.commit()
        return summary
    except Exception as e:
        if _own_session: db.rollback()
        raise
    finally:
        if _own_session: db.close()

def summarize_unsummarized(batch_size: int = 100) -> list[int]:
    db = SessionLocal()
    processed_ids = []
    try:
        # Unprocessed records fetch karein
        records = db.query(RawOSINT).filter(RawOSINT.summary == None, RawOSINT.incident_type != None).limit(batch_size).all()
        for record in records:
            record.summary = _generate_summary(record.incident_type, record.state, record.country, record.severity, record.source)
            processed_ids.append(record.id)
        db.commit()
        return processed_ids
    finally:
        db.close()