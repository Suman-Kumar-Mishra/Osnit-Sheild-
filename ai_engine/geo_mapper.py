"""
ai_engine/geo_mapper.py
------------------------
Extracts geographic signals from a RawOSINT record by ID.
Writes country, state, geo_lat, geo_lon back to the DB row.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session
from database import SessionLocal
from models import RawOSINT
from ai_engine.preprocessor import get_cleaned_content

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Geography Reference Data
# (add entries here to extend coverage — no logic changes needed)
# ──────────────────────────────────────────────

# State → (lat, lon) approximate centroid
# All 28 States + 8 Union Territories of India
INDIAN_STATES: dict[str, tuple[float, float]] = {

    # ── Northern States ──
    "Jammu and Kashmir":  (33.7782, 76.5762),
    "Jammu":              (32.7266, 74.8570),
    "Kashmir":            (34.0837, 74.7973),
    "Himachal Pradesh":   (31.1048, 77.1734),
    "Punjab":             (31.1471, 75.3412),
    "Uttarakhand":        (30.0668, 79.0193),
    "Haryana":            (29.0588, 76.0856),
    "Delhi":              (28.6139, 77.2090),
    "Uttar Pradesh":      (26.8467, 80.9462),

    # ── Western States ──
    "Rajasthan":          (27.0238, 74.2179),
    "Gujarat":            (22.2587, 71.1924),
    "Maharashtra":        (19.7515, 75.7139),
    "Goa":                (15.2993, 74.1240),

    # ── Central States ──
    "Madhya Pradesh":     (22.9734, 78.6569),
    "Chhattisgarh":       (21.2787, 81.8661),

    # ── Eastern States ──
    "Bihar":              (25.0961, 85.3131),
    "Jharkhand":          (23.6102, 85.2799),
    "West Bengal":        (22.9868, 87.8550),
    "Odisha":             (20.9517, 85.0985),

    # ── Northeastern States ──
    "Assam":              (26.2006, 92.9376),
    "Arunachal Pradesh":  (28.2180, 94.7278),
    "Nagaland":           (26.1584, 94.5624),
    "Manipur":            (24.6637, 93.9063),
    "Mizoram":            (23.1645, 92.9376),
    "Tripura":            (23.9408, 91.9882),
    "Meghalaya":          (25.4670, 91.3662),
    "Sikkim":             (27.5330, 88.5122),

    # ── Southern States ──
    "Karnataka":          (15.3173, 75.7139),
    "Kerala":             (10.8505, 76.2711),
    "Tamil Nadu":         (11.1271, 78.6569),
    "Andhra Pradesh":     (15.9129, 79.7400),
    "Telangana":          (18.1124, 79.0193),

    # ── Union Territories ──
    "Ladakh":             (34.2268, 77.5619),
    "Chandigarh":         (30.7333, 76.7794),
    "Dadra and Nagar Haveli": (20.1809, 73.0169),
    "Daman and Diu":      (20.3974, 72.8328),
    "Lakshadweep":        (10.5667, 72.6417),
    "Puducherry":         (11.9416, 79.8083),
    "Andaman and Nicobar Islands": (11.7401, 92.6586),
}

# Neighbour country → (lat, lon) approximate centroid
NEIGHBOR_COUNTRIES: dict[str, tuple[float, float]] = {
    "Pakistan":          (30.3753, 69.3451),
    "China":             (35.8617, 104.1954),
    "Bangladesh":        (23.6850, 90.3563),
    "Nepal":             (28.3949, 84.1240),
    "Sri Lanka":         (7.8731, 80.7718),
    "Myanmar":           (21.9162, 95.9560),
    "Bhutan":            (27.5142, 90.4336),
    "Afghanistan":       (33.9391, 67.7100),
}

# Default fallback
DEFAULT_COUNTRY = "India"
DEFAULT_COORDS: tuple[float, float] = (20.5937, 78.9629)   # India centroid


# ──────────────────────────────────────────────
# Detection helpers
# ──────────────────────────────────────────────

def _detect_country(text: str) -> tuple[str, float, float]:
    """Returns (country_name, lat, lon). Defaults to India."""
    lower = text.lower()
    for country, coords in NEIGHBOR_COUNTRIES.items():
        if country.lower() in lower:
            return country, coords[0], coords[1]
    return DEFAULT_COUNTRY, DEFAULT_COORDS[0], DEFAULT_COORDS[1]


def _detect_state(text: str) -> tuple[Optional[str], Optional[float], Optional[float]]:
    """Returns (state_name, lat, lon) or (None, None, None) if not found."""
    lower = text.lower()
    for state, coords in INDIAN_STATES.items():
        if state.lower() in lower:
            return state, coords[0], coords[1]
    return None, None, None


# ──────────────────────────────────────────────
# Single Record
# ──────────────────────────────────────────────

def geomap_record(record_id: int, db: Optional[Session] = None) -> dict:
    """
    Detect geographic signals for a RawOSINT record.
    Writes country, state, geo_lat, geo_lon back to the DB row.

    Args:
        record_id: PK of the RawOSINT row.
        db:        Optional shared session.

    Returns:
        Dict with keys: country, state, geo_lat, geo_lon.
    """
    _own_session = db is None
    if _own_session:
        db = SessionLocal()

    result = {}

    try:
        record: Optional[RawOSINT] = db.query(RawOSINT).filter(RawOSINT.id == record_id).first()

        if not record:
            logger.warning(f"[GeoMapper] Record ID {record_id} not found.")
            return result

        text = get_cleaned_content(record_id, db) or record.content

        # State takes priority for lat/lon (more precise)
        state, s_lat, s_lon = _detect_state(text)
        country, c_lat, c_lon = _detect_country(text)

        record.state   = state
        record.country = country
        record.geo_lat = s_lat if s_lat is not None else c_lat
        record.geo_lon = s_lon if s_lon is not None else c_lon

        result = {
            "country": country,
            "state":   state,
            "geo_lat": record.geo_lat,
            "geo_lon": record.geo_lon,
        }

        if _own_session:
            db.commit()

        logger.info(f"[GeoMapper] ID {record_id} → {country} / {state} ({record.geo_lat}, {record.geo_lon})")
        return result

    except Exception as e:
        logger.error(f"[GeoMapper] Failed on ID {record_id}: {e}")
        if _own_session:
            db.rollback()
        raise
    finally:
        if _own_session:
            db.close()


# ──────────────────────────────────────────────
# Batch Processing
# ──────────────────────────────────────────────

def geomap_unmapped(batch_size: int = 100) -> list[int]:
    """
    Map all records where country is NULL.

    Returns:
        List of processed record IDs.
    """
    db = SessionLocal()
    processed_ids = []

    try:
        records = (
            db.query(RawOSINT)
            .filter(RawOSINT.country == None)  # noqa: E711
            .limit(batch_size)
            .all()
        )

        for record in records:
            text = (record.extra_metadata or {}).get("cleaned_content") or record.content
            state, s_lat, s_lon = _detect_state(text)
            country, c_lat, c_lon = _detect_country(text)

            record.state   = state
            record.country = country
            record.geo_lat = s_lat if s_lat is not None else c_lat
            record.geo_lon = s_lon if s_lon is not None else c_lon

        db.commit()
        processed_ids = [r.id for r in records]
        logger.info(f"[GeoMapper] Batch mapped {len(processed_ids)} records.")

    except Exception as e:
        logger.error(f"[GeoMapper] Batch failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

    return processed_ids