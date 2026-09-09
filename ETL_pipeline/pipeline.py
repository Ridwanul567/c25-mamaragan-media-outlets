"""Main ETL pipeline entrypoint linking ingestion, enrichment, and storage."""

import logging
from collect_data import get_all_articles
from enrich_data import enrich_articles
from write_data import save_articles_to_dynamodb

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


def run_pipeline():
    """Execute end-to-end serverless ETL flow in-memory."""
    logging.info("Starting article collection step...")
    raw_articles = get_all_articles()
    logging.info("Collected %d raw articles from feeds.", len(raw_articles))

    if not raw_articles:
        logging.warning("No articles fetched. Pipeline exiting.")
        return

    logging.info("Starting article enrichment step...")
    enriched_articles = enrich_articles(raw_articles)

    logging.info("Starting DynamoDB loading step...")
    save_articles_to_dynamodb(enriched_articles)
    logging.info("Pipeline execution completed successfully.")


if __name__ == "__main__":
    run_pipeline()
