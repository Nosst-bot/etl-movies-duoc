"""Tests for data extraction module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from etl.extract import (
    extract_imdb_data,
    extract_tmdb_data,
    fetch_omdb_movie,
    read_csv_file,
)
from tests.conftest import FIXTURES_DIR


def test_read_csv_file_loads_rows() -> None:
    """CSV reader should load all rows from fixture file."""
    path = FIXTURES_DIR / "imdb_sample.csv"
    df = read_csv_file(path, source_name="test_imdb")
    assert len(df) == 5
    assert "Series_Title" in df.columns


def test_read_csv_file_with_sample_size() -> None:
    """CSV reader should respect sample size limit."""
    path = FIXTURES_DIR / "tmdb_sample.csv"
    df = read_csv_file(path, sample_size=2, source_name="test_tmdb")
    assert len(df) == 2


def test_extract_imdb_from_local_fixture() -> None:
    """IMDB extraction should work with local CSV path."""
    path = FIXTURES_DIR / "imdb_sample.csv"
    df = extract_imdb_data(local_path=path, use_kaggle=False)
    assert not df.empty
    assert "Series_Title" in df.columns


def test_extract_tmdb_from_local_fixture() -> None:
    """TMDB extraction should work with local CSV path."""
    path = FIXTURES_DIR / "tmdb_sample.csv"
    df = extract_tmdb_data(local_path=path, use_kaggle=False)
    assert not df.empty
    assert "title" in df.columns


@patch("etl.extract.requests.get")
def test_fetch_omdb_movie_success(mock_get: MagicMock) -> None:
    """OMDb fetch should return parsed JSON on success."""
    mock_get.return_value.json.return_value = {
        "Response": "True",
        "Title": "The Godfather",
        "Year": "1972",
        "imdbRating": "9.2",
    }
    mock_get.return_value.raise_for_status = MagicMock()

    result = fetch_omdb_movie("The Godfather", 1972)
    assert result is not None
    assert result["Title"] == "The Godfather"


@patch("etl.extract.requests.get")
def test_fetch_omdb_movie_not_found(mock_get: MagicMock) -> None:
    """OMDb fetch should return None when movie not found."""
    mock_get.return_value.json.return_value = {
        "Response": "False",
        "Error": "Movie not found!",
    }
    mock_get.return_value.raise_for_status = MagicMock()

    result = fetch_omdb_movie("Nonexistent Movie XYZ")
    assert result is None


def test_extract_imdb_missing_file_raises() -> None:
    """IMDB extraction should raise when no data source available."""
    with patch("etl.extract.DATA_RAW_DIR", Path("/nonexistent/path")):
        with pytest.raises(FileNotFoundError):
            extract_imdb_data(use_kaggle=False)
