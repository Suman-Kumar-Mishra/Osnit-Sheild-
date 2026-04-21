from apscheduler.schedulers.blocking import BlockingScheduler
import logging

from ingestion.collectors.news import collect_news
from ai_engine.pipeline import process_unprocessed_records
from ingestion.runner import run_ingestion


logging.basicConfig(level=logging.INFO)

scheduler = BlockingScheduler()



def ingestion_job():
    print("Running ingestion pipeline...")
    run_ingestion()

def ai_processing_job():
    logging.info("Running AI processing job...")
    process_unprocessed_records()


# Run every 15 minutes
scheduler.add_job(ingestion_job, 'interval', minutes=15)
scheduler.add_job(ai_processing_job, 'interval', minutes=15)


if __name__ == "__main__":
    logging.info("🚀 OSNIT Full Pipeline Scheduler Started...")
    scheduler.start()

