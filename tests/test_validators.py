"""Tests for data validation module."""

import pandas as pd

from etl.validators import (
    validate_and_remove_duplicates,
    validate_critical_nulls,
    validate_empty_titles,
    validate_rating_range,
    validate_year,
    run_all_validations,
)


def test_validate_empty_titles_removes_blank() -> None:
    """Empty title validation should remove blank rows."""
    df = pd.DataFrame({"title": ["Valid", "", "  ", None], "imdb_rating": [8.0, 7.0, 6.0, 5.0]})
    result = validate_empty_titles(df)
    assert len(result) == 1
    assert result["title"].iloc[0] == "Valid"


def test_validate_rating_range_nullifies_invalid() -> None:
    """Out-of-range ratings should be set to null."""
    df = pd.DataFrame({"imdb_rating": [8.5, 15.0, -1.0, None]})
    result = validate_rating_range(df, "imdb_rating", 0.0, 10.0)
    assert result["imdb_rating"].iloc[0] == 8.5
    assert pd.isna(result["imdb_rating"].iloc[1])
    assert pd.isna(result["imdb_rating"].iloc[2])


def test_validate_year_removes_invalid() -> None:
    """Invalid years should be removed."""
    df = pd.DataFrame({"year": [1994, 1800, 2200, None], "title": ["A", "B", "C", "D"]})
    result = validate_year(df)
    assert len(result) == 2


def test_validate_critical_nulls() -> None:
    """Rows with all critical nulls should be removed."""
    df = pd.DataFrame(
        {
            "title": ["A", None],
            "imdb_rating": [8.0, None],
            "tmdb_rating": [None, None],
        }
    )
    result = validate_critical_nulls(df, ["title", "imdb_rating", "tmdb_rating"])
    assert len(result) == 1


def test_validate_duplicates() -> None:
    """Duplicate title+year pairs should be removed."""
    df = pd.DataFrame({"title": ["A", "A", "B"], "year": [2000, 2000, 2001]})
    result = validate_and_remove_duplicates(df, ["title", "year"])
    assert len(result) == 2


def test_run_all_validations_pipeline() -> None:
    """Full validation pipeline should produce clean dataset."""
    df = pd.DataFrame(
        {
            "title": ["Good Movie", "", "Bad Rating", "Good Movie"],
            "year": [1994, 1994, 1994, 1994],
            "imdb_rating": [8.5, 7.0, 99.0, 8.5],
            "tmdb_rating": [8.0, None, 7.0, 8.0],
            "metascore": [80, None, None, 80],
            "source_rating": [8.5, None, 99.0, 8.5],
        }
    )
    result = run_all_validations(df)
    assert len(result) <= 2
    assert "" not in result["title"].astype(str).tolist()
