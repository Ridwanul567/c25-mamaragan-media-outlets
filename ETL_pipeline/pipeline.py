"""Main ETL pipeline entrypoint linking ingestion, enrichment, and storage."""

import logging
from dotenv import load_dotenv
from collect_data import get_all_articles
from write_data import get_boto3_session, filter_new_articles, save_articles_to_dynamodb
from enrich_data import enrich_articles

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()


def run_pipeline():
    """Execute end-to-end serverless ETL flow in-memory."""
    logging.info("Starting article collection step...")
    raw_articles = get_all_articles()
    logging.info("Collected %d raw articles from feeds.", len(raw_articles))

    boto3_session = get_boto3_session()
    unprocessed_articles = filter_new_articles(
        raw_articles, session=boto3_session)
    logging.info("Found %d new articles to process.",
                 len(unprocessed_articles))

    if not unprocessed_articles:
        logging.info("No new articles to enrich. Exiting.")
        return

    logging.info("Starting article enrichment step...")
    enriched_articles = enrich_articles(unprocessed_articles)

    logging.info("Starting DynamoDB loading step...")
    save_articles_to_dynamodb(enriched_articles, session=boto3_session)
    logging.info("Pipeline execution completed successfully.")


def handler(event=None, context=None):
    run_pipeline()


if __name__ == "__main__":
    run_pipeline()
