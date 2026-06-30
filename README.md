# Movies ETL & Analytics Dashboard

Academic Data Engineering project that integrates multiple movie data sources (IMDB, TMDB, OMDb), applies ETL transformations and validations, stores consolidated data in SQLite, and visualizes insights through an interactive Streamlit dashboard.

## Description

This project demonstrates a complete data pipeline for movie analytics:

- **Extract**: CSV datasets from Kaggle (IMDB Top 1000, TMDB 930K+) and enrichment via OMDb API
- **Transform**: Clean, standardize, merge on movie title, validate, and derive metrics
- **Load**: Persist to SQLite with a repository layer for queries
- **Visualize**: Streamlit dashboard with Plotly charts and filters

Data sources are joined using **normalized movie title** as the primary key.

## Architecture

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ IMDB CSV    │  │ TMDB CSV    │  │ OMDb API    │
│ (Kaggle)    │  │ (Kaggle)    │  │ (REST)      │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        ▼
              ┌─────────────────┐
              │   extract.py    │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │  transform.py   │
              │  validators.py  │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │    load.py      │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │  SQLite DB      │
              │  movies.db      │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ movie_repository│
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ dashboard/app.py│
              │ (Streamlit)     │
              └─────────────────┘
```

### Project Structure

```
movies-etl-dashboard/
├── data/
│   ├── raw/                 # Downloaded CSV files
│   └── processed/           # Consolidated output CSV
├── database/
│   └── movies.db            # SQLite database (generated)
├── etl/
│   ├── extract.py           # Data extraction
│   ├── transform.py         # Transformation & merging
│   ├── load.py              # SQLite load
│   ├── validators.py        # Data quality rules
│   ├── config.py            # Configuration
│   └── logging_config.py    # Logging setup
├── dashboard/
│   └── app.py               # Streamlit dashboard
├── repository/
│   └── movie_repository.py  # Data access layer
├── tests/                   # Pytest suite
├── logs/                    # ETL logs
├── run_pipeline.py          # Pipeline entry point
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Installation

### Prerequisites

- Python 3.11+
- pip
- (Optional) Docker & Docker Compose
- (Optional) Kaggle credentials for automatic dataset download
- OMDb API key (free at [omdbapi.com](https://www.omdbapi.com/apikey.aspx))

### Local Setup

```bash
# Clone or navigate to project
cd movies-etl-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate          # Linux/macOS
# venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your OMDB_API_KEY
```

## Usage

### Run ETL Pipeline

```bash
python run_pipeline.py
```

This will:

1. Download IMDB and TMDB datasets from Kaggle (or use local CSVs in `data/raw/`)
2. Fetch enrichment data from OMDb API (limited by `OMDB_MAX_REQUESTS`)
3. Transform, validate, and merge datasets
4. Save processed CSV to `data/processed/movies_consolidated.csv`
5. Load data into `database/movies.db`

### Run Dashboard

```bash
streamlit run dashboard/app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### Without Kaggle (local CSV)

Place CSV files in `data/raw/`:

- `imdb_movies.csv` — IMDB dataset
- `tmdb_movies.csv` — TMDB dataset

Or use the test fixtures as samples:

```bash
cp tests/fixtures/imdb_sample.csv data/raw/imdb_movies.csv
cp tests/fixtures/tmdb_sample.csv data/raw/tmdb_movies.csv
python run_pipeline.py
```

## Docker

Run the full stack (ETL + Dashboard):

```bash
docker compose up --build
```

- ETL runs first and populates the database
- Dashboard starts on [http://localhost:8501](http://localhost:8501)

Environment variables can be set in `.env` or passed via `docker-compose.yml`.

## Dashboard

The Streamlit dashboard includes:

| Feature | Description |
|---------|-------------|
| Total Movies | Count of records in database |
| Average Rating | Mean combined rating |
| Movies by Genre | Interactive bar chart (Plotly) |
| Top 10 Rated | Horizontal bar chart of best movies |
| Distribution by Year | Line chart of releases per year |
| Filters | Genre and year dropdown filters |
| Data Table | Filtered results with ratings |

## Testing

Run the full test suite:

```bash
pytest tests/ -v
```

Tests cover:

- CSV data reading (`test_extract.py`)
- Transformations and merging (`test_transform.py`)
- Validation rules (`test_validators.py`)
- SQLite load and repository (`test_load.py`)

Fixtures in `tests/fixtures/` provide sample data without external dependencies.

## Data Sources

| Source | Type | Description |
|--------|------|-------------|
| IMDB Top 1000 | Kaggle CSV | `harshitshankhdhar/imdb-dataset-of-top-1000-movies-and-tv-shows` |
| TMDB 930K+ | Kaggle CSV | `asaniczka/tmdb-movies-dataset-2023-930k-movies` |
| OMDb | REST API | `https://www.omdbapi.com/` |

## Validations

Implemented in `etl/validators.py` with logging to `logs/etl.log`:

- Empty titles
- Ratings out of range (IMDB: 0–10, Metascore: 0–100)
- Invalid release years
- Duplicate records (title + year)
- Critical null values

## Database Schema

**Table: `movies`**

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| title | TEXT | Movie title |
| year | INTEGER | Release year |
| genre | TEXT | Genre(s) |
| director | TEXT | Director name |
| actors | TEXT | Cast |
| runtime | INTEGER | Duration in minutes |
| imdb_rating | REAL | IMDB rating |
| metascore | REAL | Metascore |
| source_rating | REAL | Primary source rating |
| tmdb_rating | REAL | TMDB vote average |
| combined_rating | REAL | Derived average rating |
| rating_tier | TEXT | excellent/good/average/poor |
| decade | TEXT | Release decade |
| sources | TEXT | Contributing data sources |

## License

Academic project — for educational purposes.
