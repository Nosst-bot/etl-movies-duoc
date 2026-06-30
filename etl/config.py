"""Project configuration and path constants."""

from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "movies.db"
LOGS_DIR = PROJECT_ROOT / "logs"

KAGGLE_IMDB_DATASET = (
    "harshitshankhdhar/imdb-dataset-of-top-1000-movies-and-tv-shows"
)
KAGGLE_TMDB_DATASET = "asaniczka/tmdb-movies-dataset-2023-930k-movies"

OMDB_API_KEY = os.getenv("OMDB_API_KEY", "5f53a744")
OMDB_BASE_URL = "https://www.omdbapi.com/"
OMDB_MAX_REQUESTS = int(os.getenv("OMDB_MAX_REQUESTS", "50"))
IMDB_SAMPLE_SIZE = int(os.getenv("IMDB_SAMPLE_SIZE", "0"))
TMDB_SAMPLE_SIZE = int(os.getenv("TMDB_SAMPLE_SIZE", "0"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# SQLite schema
MOVIES_TABLE = "movies"
MOVIES_COLUMNS = [
    "id",
    "title",
    "year",
    "genre",
    "director",
    "actors",
    "runtime",
    "imdb_rating",
    "metascore",
    "source_rating",
    "tmdb_rating",
    "combined_rating",
    "rating_tier",
    "decade",
    "sources",
]
