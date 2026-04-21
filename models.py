# models.py

from sqlalchemy import (
    Column,
    Integer,
    Text,
    Float,
    Boolean,
    TIMESTAMP,
    JSON
)
from sqlalchemy.sql import func
from database import Base


# -----------------------------------------------------
# RAW OSINT TABLE
# -----------------------------------------------------

class RawOSINT(Base):
    __tablename__ = "raw_osint"

    id = Column(Integer, primary_key=True, index=True)

    source = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    url = Column(Text)

    country = Column(Text)
    state = Column(Text)

    geo_lat = Column(Float)
    geo_lon = Column(Float)

    content_hash = Column(Text, unique=True)

    # models.py mein ye line add karein
    summary = Column(Text, nullable=True)

    # 🔥 FIXED HERE
    extra_metadata = Column("metadata", JSON)

    keyword_vector = Column(JSON)

    incident_type = Column(Text)
    severity = Column(Text)
    risk_score = Column(Float)
    confidence = Column(Float)

    processed = Column(Boolean, default=False)

    collected_at = Column(TIMESTAMP, server_default=func.now())


# -----------------------------------------------------
# INGESTION LOGS TABLE
# -----------------------------------------------------

class IngestionLog(Base):
    __tablename__ = "ingestion_logs"

    id = Column(Integer, primary_key=True, index=True)

    source = Column(Text)
    records_fetched = Column(Integer)
    records_inserted = Column(Integer)
    status = Column(Text)
    error_message = Column(Text)

    run_time = Column(TIMESTAMP, server_default=func.now())


# -----------------------------------------------------
# ALERTS TABLE
# -----------------------------------------------------

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    keyword = Column(Text)
    state = Column(Text)
    country = Column(Text)

    spike_ratio = Column(Float)
    threat_probability = Column(Float)
    confidence = Column(Float)

    source_count = Column(Integer)
    alert_type = Column(Text)

    created_at = Column(TIMESTAMP, server_default=func.now())
