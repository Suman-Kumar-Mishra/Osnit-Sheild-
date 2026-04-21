"""
ai_engine/ner.py
-----------------
Named Entity Recognition without spaCy.
Uses keyword matching against known entities for Python 3.12 compatibility.
spaCy conflicts with pydantic on Python 3.12 — this avoids that entirely.
"""

import re
from ai_engine.geo_mapper import INDIAN_STATES, NEIGHBOR_COUNTRIES

# ── Known Organizations ──
KNOWN_ORGS = [
    "indian army", "indian navy", "indian air force", "bsf", "crpf", "itbp",
    "nsg", "raw", "ib", "nia", "cbi", "isro", "drdo", "ministry of defence",
    "ministry of home", "un", "nato", "who", "interpol", "fbi", "cia",
    "isi", "pla", "taliban", "isis", "al qaeda", "lashkar", "jaish",
    "government of india", "parliament", "supreme court",
]

# ── Known Persons (expandable) ──
KNOWN_PERSONS = [
    "modi", "shah", "rajnath", "jaishankar", "doval",
    "xi jinping", "imran", "shehbaz", "biden", "putin",
]


def extract_entities(text: str) -> dict:
    """
    Extract named entities from text using keyword matching.

    Returns:
        Dict with keys: persons, organizations, locations
    """
    if not text:
        return {"persons": [], "organizations": [], "locations": []}

    lower = text.lower()

    # ── Locations — match Indian states + neighbour countries ──
    locations = []
    for state in INDIAN_STATES:
        if state.lower() in lower:
            locations.append(state)
    for country in NEIGHBOR_COUNTRIES:
        if country.lower() in lower:
            locations.append(country)
    # Also catch "India" itself
    if "india" in lower:
        locations.append("India")

    # ── Organizations ──
    organizations = []
    for org in KNOWN_ORGS:
        if org in lower:
            organizations.append(org.title())

    # ── Persons ──
    persons = []
    for person in KNOWN_PERSONS:
        if person in lower:
            persons.append(person.title())

    return {
        "persons":       list(set(persons)),
        "organizations": list(set(organizations)),
        "locations":     list(set(locations)),
    }