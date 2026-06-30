"""Pytest configuration and shared fixtures."""

from pathlib import Path

import pandas as pd
import pytest

from etl.load import get_connection, initialize_database, load_to_sqlite

FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_DB_PATH = Path(__file__).parent / "test_movies.db"


@pytest.fixture
def imdb_sample_df() -> pd.DataFrame:
    """Load IMDB sample CSV fixture."""
    return pd.read_csv(FIXTURES_DIR / "imdb_sample.csv")


@pytest.fixture
def tmdb_sample_df() -> pd.DataFrame:
    """Load TMDB sample CSV fixture."""
    return pd.read_csv(FIXTURES_DIR / "tmdb_sample.csv")


@pytest.fixture
def test_db_path() -> Path:
    """Provide test database path and clean up after test."""
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    yield TEST_DB_PATH
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture
def populated_db(test_db_path: Path, imdb_sample_df: pd.DataFrame, tmdb_sample_df: pd.DataFrame) -> Path:
    """Create a test database with sample merged data."""
    from etl.transform import merge_sources

    merged = merge_sources(imdb_sample_df, tmdb_sample_df)
    load_to_sqlite(merged, db_path=test_db_path)
    return test_db_path
