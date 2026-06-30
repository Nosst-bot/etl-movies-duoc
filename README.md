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


---

I’m checking the container setup and environment requirements first, then I’ll tighten the compose file so the ETL and dashboard can run consistently on another machine.

Read [](file:///c%3A/Users/kevin/movies-etl-dashboard/Dockerfile)

Read [](file:///c%3A/Users/kevin/movies-etl-dashboard/requirements.txt)

Read [](file:///c%3A/Users/kevin/movies-etl-dashboard/.env)

I found one important container issue: the compose file was defaulting TMDB to 5,000 rows, which would reintroduce the old cap in Docker. I’m correcting that before I draft the deployment guide.

Replacing 31 lines with 37 lines in [](file:///c%3A/Users/kevin/movies-etl-dashboard/docker-compose.yml)


```

```


Ran terminal command:  cd /c/Users/kevin/movies-etl-dashboard && docker compose config

Ran terminal command:  cd /c/Users/kevin/movies-etl-dashboard && mkdir -p cache/kagglehub && docker compose up --build -d
Completed with input:  cd /c/Users/kevin/movies-etl-dashboard && mkdir -p cache/kagglehub && docker compose up --build -d

## Configuración lista para contenedores ✅

Ya dejé docker-compose.yml preparado para que el flujo funcione de forma consistente en otra máquina:

- ETL con `TMDB_SAMPLE_SIZE=0` para que no vuelva a capear el dataset en 5,000.
- Montaje persistente de:
  - data
  - database
  - logs
- Caché de Kaggle en kagglehub para evitar re-descargas innecesarias.
- Dashboard expuesto en `http://localhost:8501`

> Verificación hecha: `docker compose config` sí pasó correctamente, así que la sintaxis del compose está bien.  
> No pude lanzar el contenedor aquí porque este entorno no tiene un motor Docker disponible, así que la validación final de arranque se deja para el otro PC.

---

## Mini guía para inicializar el proyecto en otro PC

### 1) Requisitos previos

Instala en el otro equipo:

- Docker Desktop
- Docker Compose v2
- Git

Si usas Windows, lo ideal es tener Docker Desktop con WSL2 activado.

---

### 2) Clona el repositorio

```bash
git clone <URL-del-repo>
cd movies-etl-dashboard
```

---

### 3) Ajusta el archivo .env

Asegúrate de que exista \.env con algo como esto:

```env
OMDB_API_KEY=5f53a744
OMDB_MAX_REQUESTS=50
IMDB_SAMPLE_SIZE=0
TMDB_SAMPLE_SIZE=0
LOG_LEVEL=INFO
```

Si quieres descargar TMDB desde Kaggle, agrega también tus credenciales de Kaggle:

```env
KAGGLE_USERNAME=tu_usuario
KAGGLE_KEY=tu_api_key
```

> Si no tienes Kaggle creds, puedes dejar el proyecto con los CSV ya descargados en raw, y el pipeline usará esos archivos locales.

---

### 4) Prepara carpetas necesarias

```bash
mkdir -p data/raw data/processed database logs cache/kagglehub
```

---

### 5) Asegura que los datasets estén disponibles

Opciones:

- Opción A (recomendada): deja los CSV listos en raw
  - `imdb_movies.csv`
  - `tmdb_movies.csv`

- Opción B: deja que el ETL descargue desde Kaggle, pero entonces necesitas:
  - internet
  - credenciales de Kaggle válidas

---

### 6) Construye y levanta todo

Desde la raíz del proyecto:

```bash
docker compose build
docker compose up -d
```

Si quieres ver el progreso del ETL:

```bash
docker compose logs -f etl
```

---

### 7) Abre el dashboard

Una vez que el ETL termine:

```text
http://localhost:8501
```

---

### 8) Si quieres reiniciar solo el pipeline

```bash
docker compose run --rm etl python run_pipeline.py
```

---

### 9) Si quieres apagar todo

```bash
docker compose down
```

---

## Recomendación clave para que funcione “tal cual”

Para que el comportamiento sea lo más parecido al tuyo:

1. Mantén `TMDB_SAMPLE_SIZE=0` en .env
2. Asegura que raw tenga los CSV correctos
3. Si usas Kaggle, configura `KAGGLE_USERNAME` y `KAGGLE_KEY`
4. Usa `docker compose up -d` desde la raíz del proyecto

---
