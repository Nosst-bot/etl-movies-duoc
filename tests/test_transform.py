"""Tests for data transformation module."""

import pandas as pd

from etl.transform import (
    clean_dataframe,
    create_derived_metrics,
    extract_year,
    merge_sources,
    normalize_title,
    parse_runtime_minutes,
    standardize_columns,
)


def test_normalize_title_removes_special_chars() -> None:
    """Title normalization should lowercase and strip punctuation."""
    assert normalize_title("The Godfather: Part II") == "the godfather part ii"
    assert normalize_title("  Inception  ") == "inception"


def test_parse_runtime_minutes_from_string() -> None:
    """Runtime parser should extract minutes from string format."""
    assert parse_runtime_minutes("142 min") == 142
    assert parse_runtime_minutes(175) == 175
    assert parse_runtime_minutes(None) is None


def test_extract_year_from_various_formats() -> None:
    """Year extractor should handle int and date strings."""
    assert extract_year(1994) == 1994
    assert extract_year("1994-09-23") == 1994
    assert extract_year("2026-09-23") == 2026
    assert extract_year("2099") is None
    assert extract_year("N/A") is None


def test_standardize_columns_imdb() -> None:
    """IMDB columns should map to canonical names."""
    df = pd.DataFrame({"Series_Title": ["Test"], "IMDB_Rating": [8.5]})
    result = standardize_columns(df, "imdb")
    assert "title" in result.columns
    assert "imdb_rating" in result.columns
    assert result["data_source"].iloc[0] == "imdb"


def test_clean_dataframe_creates_title_key() -> None:
    """Cleaning should add normalized title key."""
    df = pd.DataFrame({"title": ["The Godfather"], "year": [1972], "runtime": ["175 min"]})
    result = clean_dataframe(df)
    assert "title_key" in result.columns
    assert result["runtime"].iloc[0] == 175


def test_create_derived_metrics() -> None:
    """Derived metrics should include combined rating and tier."""
    df = pd.DataFrame(
        {
            "title": ["Movie A"],
            "year": [2010],
            "imdb_rating": [8.5],
            "tmdb_rating": [8.0],
            "data_source": "imdb,tmdb",
        }
    )
    result = create_derived_metrics(df)
    assert result["combined_rating"].iloc[0] == 8.25
    assert result["rating_tier"].iloc[0] == "excellent"
    assert result["decade"].iloc[0] == "2010s"


def test_merge_sources_combines_imdb_and_tmdb(imdb_sample_df, tmdb_sample_df) -> None:
    """Merge should combine records sharing normalized titles."""
    result = merge_sources(imdb_sample_df, tmdb_sample_df)
    assert not result.empty
    assert "title" in result.columns
    assert "combined_rating" in result.columns

    godfather = result[result["title"].str.contains("Godfather", na=False)]
    assert len(godfather) >= 1


def test_merge_removes_duplicate_titles(imdb_sample_df, tmdb_sample_df) -> None:
    """Merge and validation should deduplicate Shawshank entries."""
    result = merge_sources(imdb_sample_df, tmdb_sample_df)
    shawshank = result[result["title"].str.contains("Shawshank", na=False)]
    assert len(shawshank) == 1


def test_merge_filters_tmdb_to_imdb_top_titles() -> None:
    """Merge should keep only TMDB titles validated against the IMDB top list."""
    imdb_df = pd.DataFrame(
        {
            "Series_Title": ["The Godfather", "The Shawshank Redemption"],
            "IMDB_Rating": [9.2, 9.3],
            "Released_Year": [1972, 1994],
        }
    )
    tmdb_df = pd.DataFrame(
        {
            "title": ["The Godfather", "XXX Movie 123", "The Shawshank Redemption"],
            "vote_average": [8.7, 1.1, 9.0],
            "release_date": ["1972-03-24", "2099-01-01", "1994-09-23"],
        }
    )

    result = merge_sources(imdb_df, tmdb_df)

    assert "XXX Movie 123" not in result["title"].tolist()
    assert "The Godfather" in result["title"].tolist()
    assert "The Shawshank Redemption" in result["title"].tolist()
