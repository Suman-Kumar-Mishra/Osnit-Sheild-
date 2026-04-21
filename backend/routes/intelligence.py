from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from database import get_db
from models import RawOSINT, Alert

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])


# =====================================================
# DASHBOARD SUMMARY
# =====================================================
@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):

    total_incidents = db.query(RawOSINT).count()

    severity_breakdown = dict(
        db.query(RawOSINT.severity, func.count())
        .group_by(RawOSINT.severity)
        .all()
    )

    top_states = db.query(
        RawOSINT.state,
        func.count().label("count")
    ).filter(RawOSINT.state != None) \
     .group_by(RawOSINT.state) \
     .order_by(func.count().desc()) \
     .limit(5).all()

    top_types = db.query(
        RawOSINT.incident_type,
        func.count().label("count")
    ).filter(RawOSINT.incident_type != None) \
     .group_by(RawOSINT.incident_type) \
     .order_by(func.count().desc()) \
     .limit(5).all()

    avg_risk = db.query(func.avg(RawOSINT.risk_score)).scalar()

    incidents_last_24h = db.query(RawOSINT) \
        .filter(text("collected_at >= NOW() - INTERVAL '24 HOURS'")) \
        .count()

    total_alerts = db.query(Alert).count()

    return {
        "total_incidents": total_incidents,
        "severity_breakdown": severity_breakdown,
        "top_states": [{"state": s, "count": c} for s, c in top_states],
        "top_incident_types": [{"type": t, "count": c} for t, c in top_types],
        "average_risk_score": round(avg_risk, 3) if avg_risk else 0,
        "incidents_last_24h": incidents_last_24h,
        "total_alerts": total_alerts
    }


# =====================================================
# LIST ALL COUNTRIES
# =====================================================
@router.get("/countries")
def list_countries(db: Session = Depends(get_db)):

    countries = db.query(
        RawOSINT.country,
        func.count().label("count")
    ).filter(RawOSINT.country != None) \
     .group_by(RawOSINT.country) \
     .order_by(func.count().desc()) \
     .all()

    return [{"country": c, "count": cnt} for c, cnt in countries]


# =====================================================
# LIST ALL STATES
# =====================================================
@router.get("/states")
def list_states(db: Session = Depends(get_db)):

    states = db.query(
        RawOSINT.state,
        func.count().label("count")
    ).filter(RawOSINT.state != None) \
     .group_by(RawOSINT.state) \
     .order_by(func.count().desc()) \
     .all()

    return [{"state": s, "count": cnt} for s, cnt in states]


# =====================================================
# COUNTRY SUMMARY
# =====================================================
@router.get("/country/{country_name}")
def country_summary(country_name: str, db: Session = Depends(get_db)):

    total = db.query(RawOSINT) \
        .filter(RawOSINT.country.ilike(f"%{country_name}%")) \
        .count()

    high_risk = db.query(RawOSINT) \
        .filter(
            RawOSINT.country.ilike(f"%{country_name}%"),
            RawOSINT.risk_score >= 0.75
        ).count()

    avg_risk = db.query(func.avg(RawOSINT.risk_score)) \
        .filter(RawOSINT.country.ilike(f"%{country_name}%")) \
        .scalar()

    severity_breakdown = dict(
        db.query(RawOSINT.severity, func.count())
        .filter(RawOSINT.country.ilike(f"%{country_name}%"))
        .group_by(RawOSINT.severity)
        .all()
    )

    return {
        "country": country_name,
        "total_incidents": total,
        "high_risk_incidents": high_risk,
        "average_risk_score": round(avg_risk, 3) if avg_risk else 0,
        "severity_breakdown": severity_breakdown
    }


# =====================================================
# STATE SUMMARY
# =====================================================
@router.get("/state/{state_name}")
def state_summary(state_name: str, db: Session = Depends(get_db)):

    total = db.query(RawOSINT) \
        .filter(RawOSINT.state.ilike(f"%{state_name}%")) \
        .count()

    high_risk = db.query(RawOSINT) \
        .filter(
            RawOSINT.state.ilike(f"%{state_name}%"),
            RawOSINT.risk_score >= 0.75
        ).count()

    dominant_type = db.query(
        RawOSINT.incident_type,
        func.count()
    ).filter(
        RawOSINT.state.ilike(f"%{state_name}%")
    ).group_by(
        RawOSINT.incident_type
    ).order_by(
        func.count().desc()
    ).first()

    return {
        "state": state_name,
        "total_incidents": total,
        "high_risk_incidents": high_risk,
        "dominant_incident_type": dominant_type[0] if dominant_type else None
    }


# =====================================================
# TREND (Last 7 Days)
# =====================================================
@router.get("/trend")
def get_trend(db: Session = Depends(get_db)):

    trend = db.query(
        func.date(RawOSINT.collected_at),
        func.count()
    ).filter(
        text("collected_at >= NOW() - INTERVAL '7 DAYS'")
    ).group_by(
        func.date(RawOSINT.collected_at)
    ).order_by(
        func.date(RawOSINT.collected_at)
    ).all()

    return [{"date": str(d), "count": c} for d, c in trend]


# =====================================================
# ALERTS
# =====================================================
@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db)):

    alerts = db.query(Alert) \
        .order_by(Alert.created_at.desc()) \
        .limit(50) \
        .all()

    return [
        {
            "id": a.id,
            "keyword": a.keyword,
            "state": a.state,
            "country": a.country,
            "alert_type": a.alert_type,
            "threat_probability": a.threat_probability,
            "confidence": a.confidence,
            "created_at": str(a.created_at)
        } for a in alerts
    ]
@router.get("/countries")
def list_countries(db: Session = Depends(get_db)):
    results = db.query(RawOSINT.country)\
        .filter(RawOSINT.country != None)\
        .distinct().all()
    return [r.country for r in results if r.country]

@router.get("/states")
def list_states(db: Session = Depends(get_db)):
    results = db.query(RawOSINT.state)\
        .filter(RawOSINT.state != None)\
        .distinct().all()
    return [r.state for r in results if r.state]

@router.get("/risk-scores")
def get_risk_scores(db: Session = Depends(get_db)):
    results = db.query(
        RawOSINT.state,
        func.avg(RawOSINT.risk_score).label("avg_risk"),
        func.max(RawOSINT.risk_score).label("max_risk"),
        func.count().label("total")
    ).filter(RawOSINT.state != None)\
     .group_by(RawOSINT.state)\
     .order_by(func.avg(RawOSINT.risk_score).desc()).all()
    return [{"state":r.state,"avg_risk":round(r.avg_risk,3),"max_risk":round(r.max_risk,3),"total_incidents":r.total} for r in results]

@router.get("/severity")
def get_severity(db: Session = Depends(get_db)):
    results = db.query(RawOSINT.severity, func.count().label("count"))\
        .group_by(RawOSINT.severity).all()
    return [{"severity":s,"count":c} for s,c in results]

@router.get("/countries")
def list_countries(db: Session = Depends(get_db)):
    results = db.query(RawOSINT.country)\
        .filter(RawOSINT.country != None).distinct().all()
    return [r.country for r in results if r.country]

@router.get("/states")
def list_states(db: Session = Depends(get_db)):
    results = db.query(RawOSINT.state)\
        .filter(RawOSINT.state != None).distinct().all()
    return [r.state for r in results if r.state]