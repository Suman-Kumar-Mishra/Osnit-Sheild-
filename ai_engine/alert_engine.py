from sqlalchemy import text
from database import SessionLocal
from models import RawOSINT


RISK_THRESHOLD = 2.5
CLUSTER_THRESHOLD = 3


def generate_alerts():
    db = SessionLocal()

    try:
        # ----------------------------
        # 1️⃣ High Risk Alerts
        # ----------------------------
        high_risk_records = db.query(RawOSINT).filter(
            RawOSINT.risk_score >= RISK_THRESHOLD
        ).all()

        for record in high_risk_records:
            db.execute(
                text("""
                    INSERT INTO alerts (cluster_id, incident_type, alert_level, message)
                    VALUES (:cluster_id, :incident_type, :alert_level, :message)
                """),
                {
                    "cluster_id": record.cluster_id,
                    "incident_type": record.incident_type,
                    "alert_level": "HIGH",
                    "message": f"High risk incident detected (Score: {record.risk_score})"
                }
            )

        # ----------------------------
        # 2️⃣ Cluster Growth Alerts
        # ----------------------------
        cluster_counts = db.execute(
            text("""
                SELECT cluster_id, COUNT(*) as cnt
                FROM raw_osint
                GROUP BY cluster_id
                HAVING COUNT(*) >= :threshold
            """),
            {"threshold": CLUSTER_THRESHOLD}
        )

        for cluster in cluster_counts:
            db.execute(
                text("""
                    INSERT INTO alerts (cluster_id, incident_type, alert_level, message)
                    VALUES (:cluster_id, :incident_type, :alert_level, :message)
                """),
                {
                    "cluster_id": cluster.cluster_id,
                    "incident_type": "cluster",
                    "alert_level": "MEDIUM",
                    "message": f"Cluster {cluster.cluster_id} has grown to {cluster.cnt} incidents."
                }
            )

        db.commit()

    except Exception as e:
        db.rollback()
        print("Alert Engine Error:", e)

    finally:
        db.close()
