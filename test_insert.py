from database import SessionLocal
from models import RawOSINT


def insert_test_record():
    """
    Inserts a test OSINT record into the raw_osint table
    """

    db = SessionLocal()

    try:
        new_record = RawOSINT(
            source="python_test",
            content="Cyber fraud detected in Mumbai targeting banking servers.",
            url="https://example.com/test-incident",
            extra_metadata={
                "location": "Mumbai",
                "severity_hint": "medium",
                "author": "System Test",
                "tags": ["cybercrime", "banking"]
            }
        )

        db.add(new_record)
        db.commit()
        db.refresh(new_record)

        print("✅ Data inserted successfully!")
        print(f"Inserted ID: {new_record.id}")

    except Exception as e:
        db.rollback()
        print("❌ Error inserting data:", e)

    finally:
        db.close()


if __name__ == "__main__":
    insert_test_record()

