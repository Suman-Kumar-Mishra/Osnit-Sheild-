from fastapi import APIRouter, HTTPException
from ingestion.runner import run_ingestion
from ai_engine.pipeline import process_unprocessed_records
from ingestion.scheduler import scheduler
from database import get_db
from models import RawOSINT
from sqlalchemy.orm import Session

router = APIRouter(prefix="/operations", tags=["Operations"])


# ------------------------------
# Run Ingestion
# ------------------------------
@router.post("/run-ingestion")
def run_ingestion_endpoint():
    try:
        stats = run_ingestion()
        return {
            "status": "success",
            "message": "Ingestion completed",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------
# Run AI Processing
# ------------------------------
@router.post("/run-ai")
def run_ai_endpoint():
    try:
        processed = process_unprocessed_records()
        return {
            "status": "success",
            "message": "AI processing completed",
            "records_processed": processed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------
# Scheduler Status
# ------------------------------
@router.get("/scheduler-status")
def scheduler_status():
    return {
        "running": scheduler.running,
        "jobs": [job.id for job in scheduler.get_jobs()]
    }


# ------------------------------
# Start Scheduler
# ------------------------------
@router.post("/start-scheduler")
def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        return {"status": "Scheduler started"}
    return {"status": "Scheduler already running"}


# ------------------------------
# Stop Scheduler
# ------------------------------
@router.post("/stop-scheduler")
def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        return {"status": "Scheduler stopped"}
    return {"status": "Scheduler already stopped"}


# ------------------------------
# Database Stats (Quick Check)
# ------------------------------
@router.get("/db-stats")
def db_stats():
    db: Session = next(get_db())
    total = db.query(RawOSINT).count()
    processed = db.query(RawOSINT).filter(RawOSINT.processed == True).count()
    unprocessed = db.query(RawOSINT).filter(RawOSINT.processed == False).count()

    return {
        "total_records": total,
        "processed_records": processed,
        "unprocessed_records": unprocessed
    }
