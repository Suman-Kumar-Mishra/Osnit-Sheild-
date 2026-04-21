# ingestion/utils.py

import hashlib
from database import SessionLocal
from models import RawOSINT, IngestionLog


# -----------------------------------------------------
# HASH GENERATOR
# -----------------------------------------------------

def generate_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# -----------------------------------------------------
# INSERT RECORDS SAFELY (DUPLICATE-PROOF)
# -----------------------------------------------------

def insert_records(records):

    db = SessionLocal()
    inserted = 0

    for record in records:

        content = record.get("content")
        if not content:
            continue

        content_hash = generate_hash(content)

        # Check if already exists
        exists = db.query(RawOSINT.id).filter(
            RawOSINT.content_hash == content_hash
        ).first()

        if exists:
            continue

        try:
            obj = RawOSINT(
                source=record.get("source"),
                content=content,
                url=record.get("url"),
                country=record.get("country"),
                state=record.get("state"),
                geo_lat=record.get("geo_lat"),
                geo_lon=record.get("geo_lon"),
                extra_metadata=record.get("metadata"),
                content_hash=content_hash,
                processed=False
            )

            db.add(obj)
            db.commit()   # commit per record
            inserted += 1

        except Exception:
            db.rollback()
            continue

    db.close()
    return inserted


# -----------------------------------------------------
# INGESTION LOGGING
# -----------------------------------------------------

def log_ingestion(source, fetched, inserted, status, error_message):

    db = SessionLocal()

    try:
        log = IngestionLog(
            source=source,
            records_fetched=fetched,
            records_inserted=inserted,
            status=status,
            error_message=error_message
        )

        db.add(log)
        db.commit()

    except Exception:
        db.rollback()

    finally:
        db.close()
