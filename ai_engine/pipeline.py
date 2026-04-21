"""
ai_engine/pipeline.py
----------------------
Processes unprocessed RawOSINT records from the database.

Changes from original:
  1. Per-record try/except  — one bad record won't rollback the entire batch
  2. Per-record commit       — progress is saved incrementally
  3. finally db.close()     — no DB connection leaks on exceptions
  4. batch_size limit        — prevents memory overflow on large tables
  5. geo_lat / geo_lon       — coordinates now saved alongside country/state
  All original logic (confidence formula, keyword_vector, severity labels) preserved.
"""

import logging
from database import SessionLocal
from models import RawOSINT
from ai_engine.preprocessor import _clean_text as clean_text
from ai_engine.ner import extract_entities
from ai_engine.geo_mapper import _detect_country as detect_country, _detect_state as detect_state, INDIAN_STATES, NEIGHBOR_COUNTRIES, DEFAULT_COORDS
from ai_engine.classifier import _classify_text as classify_incident
from ai_engine.risk_engine import _get_severity_level as calculate_severity, _calculate_risk_score as calculate_risk_score
from ai_engine.summarizer import _generate_summary as generate_summary

logger = logging.getLogger(__name__)

SEVERITY_LABELS = ["low", "medium", "high"]


def process_unprocessed_records(batch_size: int = 100) -> dict:
    """
    Fetch unprocessed RawOSINT records and run the full AI pipeline on each.

    Args:
        batch_size: Max records to process per call (prevents memory overflow).

    Returns:
        Dict with processed_count and failed_count.
    """
    db = SessionLocal()
    processed_count = 0
    failed_count = 0

    try:
        records = (
            db.query(RawOSINT)
            .filter(RawOSINT.processed == False)  # noqa: E712
            .limit(batch_size)
            .all()
        )

        logger.info(f"[Pipeline] Found {len(records)} unprocessed records.")

        for record in records:
            try:
                # ── Step 1: Clean text ──
                cleaned = clean_text(record.content)

                # ── Step 2: NLP — extract entities ──
                entities  = extract_entities(cleaned)
                locations = entities.get("locations", [])

                # ── Step 3: Geo detection ──
                country = detect_country(" ".join(locations))
                state   = detect_state(" ".join(locations))

                # ── Step 4: Classify ──
                incident_type = classify_incident(cleaned)

                # ── Step 5: Risk scoring ──
                severity_level = calculate_severity(incident_type)
                risk_score     = calculate_risk_score(severity_level, len(locations), 1, 1.0)

                # ── Step 6: Summary ──
                summary = generate_summary(incident_type, state, country, SEVERITY_LABELS[min(severity_level - 1, 2)], record.source)

                # ── Step 7: Write back to DB ──
                record.country        = country
                record.state          = state
                record.incident_type  = incident_type
                record.severity       = SEVERITY_LABELS[min(severity_level - 1, 2)]
                record.risk_score     = risk_score
                record.confidence     = round(0.6 + risk_score * 0.3, 2)
                record.keyword_vector = entities
                record.processed      = True

                # Coordinates from geo_mapper reference dicts
                if state and state in INDIAN_STATES:
                    record.geo_lat, record.geo_lon = INDIAN_STATES[state]
                elif country and country in NEIGHBOR_COUNTRIES:
                    record.geo_lat, record.geo_lon = NEIGHBOR_COUNTRIES[country]
                else:
                    record.geo_lat, record.geo_lon = DEFAULT_COORDS

                # Save summary + cleaned text into metadata
                metadata                    = record.extra_metadata or {}
                metadata["summary"]         = summary
                metadata["cleaned_content"] = cleaned
                record.extra_metadata       = metadata

                # Per-record commit — saves progress even if later records fail
                db.commit()
                processed_count += 1
                logger.info(
                    f"[Pipeline] ✓ ID {record.id} | {incident_type} | "
                    f"{country}/{state} | risk={risk_score}"
                )

            except Exception as e:
                # Rollback only this record, continue with the rest
                db.rollback()
                failed_count += 1
                logger.error(f"[Pipeline] ✗ ID {record.id} failed: {e}")

    finally:
        db.close()

    logger.info(
        f"[Pipeline] Done — {processed_count} processed, {failed_count} failed."
    )
    return {
        "processed_count": processed_count,
        "failed_count":    failed_count,
    }
