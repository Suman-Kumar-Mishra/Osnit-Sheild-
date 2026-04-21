"""
test_pipeline.py
-----------------
Run this file to check the entire AI pipeline in one command.
Usage:
    python test_pipeline.py
"""

import sys
import traceback

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

passed = 0
failed = 0

def ok(label, detail=""):
    global passed
    passed += 1
    suffix = f"  {YELLOW}({detail}){RESET}" if detail else ""
    print(f"  {GREEN}✓ PASS{RESET}  {label}{suffix}")

def fail(label, error=""):
    global failed
    failed += 1
    print(f"  {RED}✗ FAIL{RESET}  {label}")
    if error:
        print(f"         {RED}{error}{RESET}")

def section(title):
    print(f"\n{BOLD}{CYAN}── {title} ──{RESET}")


# ══════════════════════════════════════════════
# 1. DB CONNECTION
# ══════════════════════════════════════════════
section("1. Database Connection")
try:
    from database import SessionLocal, engine
    db = SessionLocal()
    db.execute(__import__("sqlalchemy").text("SELECT 1"))
    db.close()
    ok("Database connection")
except Exception as e:
    fail("Database connection", str(e))
    print(f"\n{RED}Cannot continue without DB. Fix your .env / database.py first.{RESET}")
    sys.exit(1)


# ══════════════════════════════════════════════
# 2. TABLES EXIST
# ══════════════════════════════════════════════
section("2. Tables Exist")
try:
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    for table in ["raw_osint", "ingestion_logs", "alerts"]:
        if table in tables:
            ok(f"Table '{table}' exists")
        else:
            fail(f"Table '{table}' missing — did you run migrations?")
except Exception as e:
    fail("Table inspection", str(e))


# ══════════════════════════════════════════════
# 3. PREPROCESSOR
# ══════════════════════════════════════════════
section("3. Preprocessor")
try:
    from ai_engine.preprocessor import _clean_text
    result = _clean_text("Hello WORLD! Visit https://example.com for more info!!!")
    assert "http" not in result,     "URL not removed"
    assert result == result.lower(), "Not lowercased"
    assert "!!!" not in result,      "Special chars not removed"
    assert result.strip() == result, "Leading/trailing whitespace"
    ok("clean_text()", f'"{result}"')
except AssertionError as e:
    fail("clean_text()", str(e))
except Exception as e:
    fail("Preprocessor import/run", str(e))


# ══════════════════════════════════════════════
# 4. CLASSIFIER
# ══════════════════════════════════════════════
section("4. Classifier")
try:
    from ai_engine.classifier import _classify_text
    tests = {
        "cyber attack on government servers breach detected": "cyber_attack",
        "border tension near line of control infiltration":   "border_tension",
        "military troops deployed near the border":           "military_activity",
        "protest and riot violence in the city":              "civil_unrest",
        "terrorist bomb blast casualties reported":           "terrorism",
        "massive flood relief camp set up":                   "natural_disaster",
        "some random news with no keywords":                  "other",
    }
    for text, expected in tests.items():
        result = _classify_text(text)
        if result == expected:
            ok(f'"{text[:45]}..."', f"-> {result}")
        else:
            fail(f'"{text[:45]}..."', f"Expected '{expected}', got '{result}'")
except Exception as e:
    fail("Classifier import/run", str(e))


# ══════════════════════════════════════════════
# 5. GEO MAPPER
# ══════════════════════════════════════════════
section("5. Geo Mapper")
try:
    from ai_engine.geo_mapper import _detect_country, _detect_state, INDIAN_STATES, NEIGHBOR_COUNTRIES

    expected_states = [
        "Jammu and Kashmir", "Himachal Pradesh", "Punjab", "Uttarakhand",
        "Haryana", "Delhi", "Uttar Pradesh", "Rajasthan", "Gujarat",
        "Maharashtra", "Goa", "Madhya Pradesh", "Chhattisgarh", "Bihar",
        "Jharkhand", "West Bengal", "Odisha", "Assam", "Arunachal Pradesh",
        "Nagaland", "Manipur", "Mizoram", "Tripura", "Meghalaya", "Sikkim",
        "Karnataka", "Kerala", "Tamil Nadu", "Andhra Pradesh", "Telangana",
        "Ladakh", "Chandigarh", "Puducherry", "Andaman and Nicobar Islands", "Lakshadweep",
    ]
    missing = [s for s in expected_states if s not in INDIAN_STATES]
    if not missing:
        ok(f"All states/UTs present ({len(INDIAN_STATES)} entries)")
    else:
        fail("Missing states", ", ".join(missing))

    # detect_country returns (country, lat, lon)
    country, lat, lon = _detect_country("tension along Pakistan border")
    assert country == "Pakistan", f"Expected Pakistan, got {country}"
    ok("detect_country()", f"Pakistan -> ({lat}, {lon})")

    state, lat, lon = _detect_state("floods reported in Kerala")
    assert state == "Kerala", f"Expected Kerala, got {state}"
    ok("detect_state()", f"Kerala -> ({lat}, {lon})")

    bad_coords = [s for s, (la, lo) in INDIAN_STATES.items()
                  if not (-90 <= la <= 90) or not (-180 <= lo <= 180)]
    if not bad_coords:
        ok("All coordinates valid")
    else:
        fail("Invalid coordinates", ", ".join(bad_coords))

except Exception as e:
    fail("Geo Mapper import/run", str(e))


# ══════════════════════════════════════════════
# 6. RISK ENGINE
# ══════════════════════════════════════════════
section("6. Risk Engine")
try:
    from ai_engine.risk_engine import _get_severity_level, _calculate_risk_score, _get_severity_label

    assert _get_severity_level("terrorism")         == 5
    assert _get_severity_level("cyber_attack")      == 4
    assert _get_severity_level("border_tension")    == 4
    assert _get_severity_level("military_activity") == 3
    assert _get_severity_level("civil_unrest")      == 2
    assert _get_severity_level("other")             == 1
    ok("Severity levels correct")

    score = _calculate_risk_score(5, 3, 2, 1.0)
    assert 0.0 <= score <= 1.0, f"Score out of bounds: {score}"
    ok("Risk score in [0.0, 1.0]", f"sample score={score}")

    assert _get_severity_label(5) == "critical"
    assert _get_severity_label(1) == "minimal"
    ok("Severity labels correct")

except AssertionError as e:
    fail("Risk Engine assertion", str(e))
except Exception as e:
    fail("Risk Engine import/run", str(e))


# ══════════════════════════════════════════════
# 7. SUMMARIZER
# ══════════════════════════════════════════════
section("7. Summarizer")
try:
    from ai_engine.summarizer import _generate_summary

    for incident in ["cyber_attack", "border_tension", "military_activity",
                     "civil_unrest", "terrorism", "natural_disaster", "other"]:
        summary = _generate_summary(incident, "Punjab", "India", "high")
        assert isinstance(summary, str) and len(summary) > 10
        ok(f"Summary for '{incident}'", summary[:60] + "...")

except AssertionError as e:
    fail("Summarizer assertion", str(e))
except Exception as e:
    fail("Summarizer import/run", str(e))


# ══════════════════════════════════════════════
# 8. FULL PIPELINE — end to end
# ══════════════════════════════════════════════
section("8. Full Pipeline (End-to-End)")
dummy_id = None
try:
    from models import RawOSINT
    import hashlib, time

    db = SessionLocal()

    # Insert dummy record
    dummy_content = "Cyber attack detected on Indian Army servers near Kashmir border. Military troops on high alert."
    dummy_hash    = hashlib.md5(f"test_{time.time()}".encode()).hexdigest()
    dummy = RawOSINT(
        source       = "test_script",
        content      = dummy_content,
        content_hash = dummy_hash,
        processed    = False,
    )
    db.add(dummy)
    db.commit()
    db.refresh(dummy)
    dummy_id = dummy.id

    verify = db.query(RawOSINT).filter(RawOSINT.id == dummy_id).first()
    assert verify is not None, "Insert failed"
    ok(f"Dummy record inserted (ID={dummy_id})")
    db.close()

    # Run all pipeline steps directly on this record
    from ai_engine.preprocessor import _clean_text
    from ai_engine.ner          import extract_entities
    from ai_engine.geo_mapper   import _detect_country, _detect_state, INDIAN_STATES, NEIGHBOR_COUNTRIES, DEFAULT_COORDS
    from ai_engine.classifier   import _classify_text
    from ai_engine.risk_engine  import _get_severity_level, _calculate_risk_score
    from ai_engine.summarizer   import _generate_summary

    SLABELS = ["low", "medium", "high"]

    db = SessionLocal()
    rec = db.query(RawOSINT).filter(RawOSINT.id == dummy_id).first()

    cleaned       = _clean_text(rec.content)
    entities      = extract_entities(cleaned)
    locations     = entities.get("locations", [])
    country, c_lat, c_lon = _detect_country(cleaned)
    state,   s_lat, s_lon = _detect_state(cleaned)
    incident_type = _classify_text(cleaned)
    sev_level     = _get_severity_level(incident_type)
    risk_score    = _calculate_risk_score(sev_level, len(locations), 1, 1.0)
    sev_label     = SLABELS[min(sev_level - 1, 2)]
    summary       = _generate_summary(incident_type, state, country, sev_label, rec.source)

    rec.country        = country
    rec.state          = state
    rec.incident_type  = incident_type
    rec.severity       = sev_label
    rec.risk_score     = risk_score
    rec.confidence     = round(0.6 + risk_score * 0.3, 2)
    rec.keyword_vector = entities
    rec.processed      = True
    rec.geo_lat        = s_lat if s_lat is not None else c_lat
    rec.geo_lon        = s_lon if s_lon is not None else c_lon

    metadata                    = rec.extra_metadata or {}
    metadata["summary"]         = summary
    metadata["cleaned_content"] = cleaned
    rec.extra_metadata          = metadata

    db.commit()
    db.refresh(rec)
    ok("Pipeline steps ran without crash", f"incident={incident_type}, risk={risk_score}")

    # Verify all fields
    checks = {
        "processed = True":   rec.processed == True,
        "incident_type set":  rec.incident_type is not None,
        "severity set":       rec.severity is not None,
        "risk_score set":     rec.risk_score is not None,
        "confidence set":     rec.confidence is not None,
        "country set":        rec.country is not None,
        "keyword_vector set": rec.keyword_vector is not None,
        "summary in metadata":(rec.extra_metadata or {}).get("summary") is not None,
    }
    for check, result in checks.items():
        if result:
            ok(f"DB field: {check}")
        else:
            fail(f"DB field: {check}", "Value is None or False after pipeline")

    db.close()

except Exception as e:
    fail("Full pipeline test", traceback.format_exc())

finally:
    if dummy_id:
        try:
            db = SessionLocal()
            db.query(RawOSINT).filter(RawOSINT.id == dummy_id).delete()
            db.commit()
            db.close()
            print(f"  {YELLOW}↳ Dummy record ID={dummy_id} cleaned up{RESET}")
        except Exception:
            pass


# ══════════════════════════════════════════════
# FINAL REPORT
# ══════════════════════════════════════════════
total = passed + failed
print(f"\n{BOLD}{'═'*45}{RESET}")
print(f"{BOLD}  RESULTS:  {GREEN}{passed} passed{RESET}  |  {RED}{failed} failed{RESET}  |  {total} total{RESET}")
print(f"{BOLD}{'═'*45}{RESET}\n")

if failed > 0:
    sys.exit(1)
else:
    print(f"{GREEN}{BOLD}  ✓ All checks passed. Pipeline is healthy!{RESET}\n")
    sys.exit(0)