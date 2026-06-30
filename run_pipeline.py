"""ETL pipeline orchestrator."""

from dotenv import load_dotenv

load_dotenv()

import pandas as pd

from etl.extract import extract_imdb_data, extract_omdb_data, extract_tmdb_data
from etl.load import load_to_sqlite
from etl.logging_config import setup_logging
from etl.transform import transform_and_save

logger = setup_logging("pipeline")


def run_etl_pipeline(use_kaggle: bool = True) -> int:
    """
    Execute the full Extract-Transform-Load pipeline.

    Args:
        use_kaggle: Whether to attempt Kaggle downloads for CSV sources.

    Returns:
        Number of records loaded into SQLite.
    """
    logger.info("=== Starting Movies ETL Pipeline ===")

    imdb_df = extract_imdb_data(use_kaggle=use_kaggle)
    tmdb_df = extract_tmdb_data(use_kaggle=use_kaggle)

    titles = imdb_df.get("Series_Title", imdb_df.get("title", pd.Series())).dropna().tolist()
    years_raw = imdb_df.get("Released_Year", imdb_df.get("year", pd.Series()))
    years = [int(y) if str(y).isdigit() else None for y in years_raw.tolist()]

    omdb_df = extract_omdb_data(titles[:50], years[:50])

    processed = transform_and_save(imdb_df, tmdb_df, omdb_df)
    row_count = load_to_sqlite(processed)

    logger.info("=== ETL Pipeline Complete: %d records loaded ===", row_count)
    return row_count


if __name__ == "__main__":
    run_etl_pipeline()
