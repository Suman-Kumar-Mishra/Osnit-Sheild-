from ingestion.collectors.news import collect_news
from ingestion.collectors.regional_rss import collect_regional_rss
from ingestion.collectors.youtube import collect_youtube
from ingestion.collectors.telegram import collect_telegram

from ingestion.utils import insert_records, log_ingestion


def run_ingestion():

    sources = {
        "newsapi": collect_news,
        "regional_rss": collect_regional_rss,
        "youtube": collect_youtube,
        "telegram": collect_telegram
    }

    total_inserted = 0

    for name, func in sources.items():

        try:
            records = func()
            inserted = insert_records(records)

            log_ingestion(
                source=name,
                fetched=len(records),
                inserted=inserted,
                status="success",
                error_message=None
            )

            total_inserted += inserted

        except Exception as e:
            log_ingestion(
                source=name,
                fetched=0,
                inserted=0,
                status="failed",
                error_message=str(e)
            )

    return total_inserted
