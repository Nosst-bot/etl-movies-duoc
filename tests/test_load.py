"""Tests for SQLite load module."""

from pathlib import Path

import pandas as pd

from etl.load import get_connection, initialize_database, load_to_sqlite, prepare_records
from repository.movie_repository import MovieRepository


def test_initialize_database_creates_table(test_db_path: Path) -> None:
    """Database initialization should create movies table."""
    conn = get_connection(test_db_path)
    initialize_database(conn)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='movies'"
    ).fetchall()
    conn.close()
    assert len(tables) == 1


def test_load_to_sqlite_inserts_records(test_db_path: Path, imdb_sample_df, tmdb_sample_df) -> None:
    """Load should insert merged records into SQLite."""
    from etl.transform import merge_sources

    merged = merge_sources(imdb_sample_df, tmdb_sample_df)
    count = load_to_sqlite(merged, db_path=test_db_path)
    assert count > 0

    repo = MovieRepository(test_db_path)
    assert repo.get_total_count() == count


def test_prepare_records_adds_missing_columns() -> None:
    """Prepare records should fill missing schema columns."""
    df = pd.DataFrame({"title": ["Test Movie"], "year": [2000]})
    result = prepare_records(df)
    assert "genre" in result.columns
    assert "combined_rating" in result.columns


def test_repository_queries(populated_db: Path) -> None:
    """Repository should return analytics from populated database."""
    repo = MovieRepository(populated_db)
    assert repo.get_total_count() > 0
    assert repo.get_average_rating() > 0

    top = repo.get_top_rated(3)
    assert len(top) <= 3

    genres = repo.get_movies_by_genre()
    assert not genres.empty

    years = repo.get_distribution_by_year()
    assert not years.empty

    filtered = repo.get_filtered_movies(genre="Drama")
    assert not filtered.empty
