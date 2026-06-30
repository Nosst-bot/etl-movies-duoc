"""Data extraction from CSV files and OMDb API."""

from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from etl.config import (
    DATA_RAW_DIR,
    IMDB_SAMPLE_SIZE,
    KAGGLE_IMDB_DATASET,
    KAGGLE_TMDB_DATASET,
    OMDB_API_KEY,
    OMDB_BASE_URL,
    OMDB_MAX_REQUESTS,
    TMDB_SAMPLE_SIZE,
)
from etl.logging_config import setup_logging

logger = setup_logging("extract")


def _find_csv_in_directory(directory: Path) -> Optional[Path]:
    """Find the first CSV file in a directory."""
    csv_files = list(directory.glob("*.csv"))
    if not csv_files:
        return None
    return max(csv_files, key=lambda p: p.stat().st_size)


def download_kaggle_dataset(dataset_slug: str) -> Path:
    """
    Download a Kaggle dataset using kagglehub.

    Args:
        dataset_slug: Kaggle dataset identifier.

    Returns:
        Path to the downloaded dataset directory.

    Raises:
        RuntimeError: If download fails.
    """
    try:
        import kagglehub

        path = kagglehub.dataset_download(dataset_slug)
        dataset_path = Path(path)
        logger.info("Downloaded Kaggle dataset '%s' to %s", dataset_slug, dataset_path)
        return dataset_path
    except Exception as exc:
        logger.error("Failed to download Kaggle dataset '%s': %s", dataset_slug, exc)
        raise RuntimeError(f"Kaggle download failed for {dataset_slug}") from exc


def read_csv_file(
    path: Path,
    sample_size: int = 0,
    source_name: str = "csv",
) -> pd.DataFrame:
    """
    Read a CSV file into a pandas DataFrame.

    Args:
        path: Path to CSV file.
        sample_size: Optional row limit (0 = all rows).
        source_name: Name for logging.

    Returns:
        DataFrame with raw data.
    """
    logger.info("Reading %s from %s", source_name, path)
    try:
        df = pd.read_csv(path, low_memory=False)
        if sample_size > 0 and len(df) > sample_size:
            df = df.head(sample_size)
            logger.info("Sampled %d rows from %s", sample_size, source_name)
        logger.info("Loaded %d rows from %s", len(df), source_name)
        return df
    except Exception as exc:
        logger.error("Error reading %s: %s", path, exc)
        raise


def extract_imdb_data(
    local_path: Optional[Path] = None,
    use_kaggle: bool = True,
) -> pd.DataFrame:
    """
    Extract IMDB top movies dataset from Kaggle or local CSV.

    Args:
        local_path: Optional path to local CSV override.
        use_kaggle: Whether to download from Kaggle when no local path given.

    Returns:
        Raw IMDB dataframe.
    """
    csv_path: Optional[Path] = local_path

    if csv_path is None and use_kaggle:
        try:
            dataset_dir = download_kaggle_dataset(KAGGLE_IMDB_DATASET)
            csv_path = _find_csv_in_directory(dataset_dir)
            if csv_path:
                dest = DATA_RAW_DIR / "imdb_movies.csv"
                DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
                df_temp = pd.read_csv(csv_path, low_memory=False)
                df_temp.to_csv(dest, index=False)
                csv_path = dest
        except RuntimeError:
            logger.warning("Kaggle IMDB download failed, checking local raw data")

    if csv_path is None:
        local_imdb = DATA_RAW_DIR / "imdb_movies.csv"
        if local_imdb.exists():
            csv_path = local_imdb
        else:
            csv_path = _find_csv_in_directory(DATA_RAW_DIR)

    if csv_path is None or not csv_path.exists():
        raise FileNotFoundError(
            "IMDB dataset not found. Download via Kaggle or place CSV in data/raw/"
        )

    return read_csv_file(csv_path, IMDB_SAMPLE_SIZE, "IMDB")


def extract_tmdb_data(
    local_path: Optional[Path] = None,
    use_kaggle: bool = True,
) -> pd.DataFrame:
    """
    Extract TMDB movies dataset from Kaggle or local CSV.

    Args:
        local_path: Optional path to local CSV override.
        use_kaggle: Whether to download from Kaggle when no local path given.

    Returns:
        Raw TMDB dataframe.
    """
    csv_path: Optional[Path] = local_path

    if csv_path is None and use_kaggle:
        try:
            dataset_dir = download_kaggle_dataset(KAGGLE_TMDB_DATASET)
            csv_path = _find_csv_in_directory(dataset_dir)
            if csv_path:
                dest = DATA_RAW_DIR / "tmdb_movies.csv"
                DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
                nrows = TMDB_SAMPLE_SIZE if TMDB_SAMPLE_SIZE > 0 else None
                df_temp = pd.read_csv(csv_path, low_memory=False, nrows=nrows)
                df_temp.to_csv(dest, index=False)
                csv_path = dest
        except RuntimeError:
            logger.warning("Kaggle TMDB download failed, checking local raw data")

    if csv_path is None:
        local_tmdb = DATA_RAW_DIR / "tmdb_movies.csv"
        if local_tmdb.exists():
            csv_path = local_tmdb
        else:
            csv_path = _find_csv_in_directory(DATA_RAW_DIR)

    if csv_path is None or not csv_path.exists():
        raise FileNotFoundError(
            "TMDB dataset not found. Download via Kaggle or place CSV in data/raw/"
        )

    sample = TMDB_SAMPLE_SIZE if TMDB_SAMPLE_SIZE > 0 else 0
    return read_csv_file(csv_path, sample, "TMDB")


def fetch_omdb_movie(title: str, year: Optional[int] = None) -> Optional[dict]:
    """
    Fetch movie metadata from OMDb API.

    Args:
        title: Movie title to search.
        year: Optional release year for disambiguation.

    Returns:
        API response dict or None on failure.
    """
    params: dict[str, str] = {
        "apikey": OMDB_API_KEY,
        "t": title.replace(" ", "_"),
    }
    if year is not None:
        params["y"] = str(year)

    try:
        response = requests.get(OMDB_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("Response") == "True":
            return data
        logger.warning("OMDb no result for '%s': %s", title, data.get("Error"))
        return None
    except requests.RequestException as exc:
        logger.error("OMDb API error for '%s': %s", title, exc)
        return None


def extract_omdb_data(titles: list[str], years: Optional[list[Optional[int]]] = None) -> pd.DataFrame:
    """
    Extract enrichment data from OMDb for a list of movie titles.

    Args:
        titles: List of movie titles.
        years: Optional parallel list of release years.

    Returns:
        DataFrame with OMDb fields.
    """
    records: list[dict] = []
    max_requests = min(len(titles), OMDB_MAX_REQUESTS)
    logger.info("Fetching OMDb data for %d titles (max %d)", len(titles), max_requests)

    for idx in range(max_requests):
        title = titles[idx]
        year = years[idx] if years and idx < len(years) else None
        data = fetch_omdb_movie(title, year)
        if data:
            records.append(
                {
                    "title": data.get("Title", title),
                    "year": data.get("Year"),
                    "genre": data.get("Genre"),
                    "director": data.get("Director"),
                    "actors": data.get("Actors"),
                    "runtime": data.get("Runtime"),
                    "imdb_rating": data.get("imdbRating"),
                    "metascore": data.get("Metascore"),
                    "source_rating": data.get("imdbRating"),
                    "omdb_plot": data.get("Plot"),
                }
            )

    logger.info("OMDb extraction complete: %d records retrieved", len(records))
    return pd.DataFrame(records)
