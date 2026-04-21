from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
from models import RawOSINT

router = APIRouter(prefix="/incidents", tags=["Incidents"])


# -----------------------------------
# Get All Incidents (with filters)
# -----------------------------------
@router.get("/")
def get_incidents(
    state: Optional[str] = None,
    country: Optional[str] = None,
    severity: Optional[str] = None,
    incident_type: Optional[str] = None,
    min_risk: Optional[float] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(RawOSINT)

    if state:
        query = query.filter(RawOSINT.state.ilike(f"%{state}%"))

    if country:
        query = query.filter(RawOSINT.country.ilike(f"%{country}%"))

    if severity:
        query = query.filter(RawOSINT.severity == severity)

    if incident_type:
        query = query.filter(RawOSINT.incident_type == incident_type)

    if min_risk is not None:
        query = query.filter(RawOSINT.risk_score >= min_risk)

    incidents = query.order_by(RawOSINT.collected_at.desc()) \
                     .offset(offset) \
                     .limit(limit) \
                     .all()

    return incidents


# -----------------------------------
# Get Single Incident
# -----------------------------------
@router.get("/{incident_id}")
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(RawOSINT).filter(RawOSINT.id == incident_id).first()
    if not incident:
        return {"error": "Incident not found"}
    return incident


# -----------------------------------
# Get High Risk Incidents
# -----------------------------------
@router.get("/high-risk/")
def get_high_risk(db: Session = Depends(get_db)):
    incidents = db.query(RawOSINT) \
                  .filter(RawOSINT.risk_score >= 0.75) \
                  .order_by(RawOSINT.risk_score.desc()) \
                  .limit(100) \
                  .all()

    return incidents


# -----------------------------------
# Get Recent Incidents (24h)
# -----------------------------------
@router.get("/recent/")
def get_recent(db: Session = Depends(get_db)):
    from sqlalchemy import text

    incidents = db.query(RawOSINT) \
                  .filter(text("collected_at >= NOW() - INTERVAL '24 HOURS'")) \
                  .order_by(RawOSINT.collected_at.desc()) \
                  .all()

    return incidents
