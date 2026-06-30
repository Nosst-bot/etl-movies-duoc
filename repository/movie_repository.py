"""Data access layer for movies SQLite database."""

from pathlib import Path
from typing import Any, Optional

import pandas as pd

from etl.config import DATABASE_PATH, MOVIES_TABLE
from etl.load import get_connection


class MovieRepository:
    """Repository for querying consolidated movie data from SQLite."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """
        Initialize repository with database path.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path or DATABASE_PATH

    def _query(self, sql: str, params: tuple = ()) -> pd.DataFrame:
        """Execute a read query and return results as DataFrame."""
        conn = get_connection(self.db_path)
        try:
            return pd.read_sql_query(sql, conn, params=params)
        finally:
            conn.close()

    def get_all_movies(self) -> pd.DataFrame:
        """Return all movies from the database."""
        return self._query(f"SELECT * FROM {MOVIES_TABLE} ORDER BY combined_rating DESC")

    def get_total_count(self) -> int:
        """Return total number of movies."""
        df = self._query(f"SELECT COUNT(*) as count FROM {MOVIES_TABLE}")
        return int(df["count"].iloc[0])

    def get_average_rating(self) -> float:
        """Return average combined rating."""
        df = self._query(
            f"SELECT AVG(combined_rating) as avg_rating FROM {MOVIES_TABLE} "
            "WHERE combined_rating IS NOT NULL"
        )
        value = df["avg_rating"].iloc[0]
        return float(value) if value is not None else 0.0

    def get_average_runtime(self) -> float:
        """Return average runtime in minutes."""
        df = self._query(
            f"SELECT AVG(runtime) as avg_runtime FROM {MOVIES_TABLE} "
            "WHERE runtime IS NOT NULL"
        )
        value = df["avg_runtime"].iloc[0]
        return float(value) if value is not None else 0.0

    def get_movies_by_genre(self) -> pd.DataFrame:
        """Return movie counts grouped by primary genre."""
        sql = f"""
            SELECT
                LOWER(TRIM(SUBSTR(genre, 1, CASE WHEN INSTR(genre, ',') > 0
                    THEN INSTR(genre, ',') - 1 ELSE LENGTH(genre) END))) as genre,
                COUNT(*) as count
            FROM {MOVIES_TABLE}
            WHERE genre IS NOT NULL AND genre != ''
            GROUP BY LOWER(TRIM(SUBSTR(genre, 1, CASE WHEN INSTR(genre, ',') > 0
                THEN INSTR(genre, ',') - 1 ELSE LENGTH(genre) END)))
            ORDER BY count DESC
        """
        return self._query(sql)

    def get_rating_tier_distribution(self) -> pd.DataFrame:
        """Return movie count by rating tier in Spanish labels."""
        sql = f"""
            SELECT
                CASE
                    WHEN rating_tier = 'excellent' THEN 'Excelente'
                    WHEN rating_tier = 'good' THEN 'Buena'
                    WHEN rating_tier = 'average' THEN 'Promedio'
                    WHEN rating_tier = 'poor' THEN 'Baja'
                    ELSE 'Sin clasificar'
                END as nivel,
                COUNT(*) as count
            FROM {MOVIES_TABLE}
            WHERE rating_tier IS NOT NULL AND rating_tier != ''
            GROUP BY rating_tier
            ORDER BY count DESC
        """
        return self._query(sql)

    def get_source_coverage(self) -> pd.DataFrame:
        """Return count of movies by contributing data source."""
        sql = f"""
            SELECT
                CASE
                    WHEN sources LIKE '%omdb%' AND sources LIKE '%tmdb%' AND sources LIKE '%imdb%' THEN 'IMDB + TMDB + OMDb'
                    WHEN sources LIKE '%tmdb%' AND sources LIKE '%omdb%' THEN 'TMDB + OMDb'
                    WHEN sources LIKE '%imdb%' AND sources LIKE '%tmdb%' THEN 'IMDB + TMDB'
                    WHEN sources LIKE '%imdb%' AND sources LIKE '%omdb%' THEN 'IMDB + OMDb'
                    WHEN sources LIKE '%tmdb%' THEN 'TMDB'
                    WHEN sources LIKE '%imdb%' THEN 'IMDB'
                    WHEN sources LIKE '%omdb%' THEN 'OMDb'
                    ELSE sources
                END as source,
                COUNT(*) as count
            FROM {MOVIES_TABLE}
            WHERE sources IS NOT NULL AND sources != ''
            GROUP BY source
            ORDER BY count DESC
        """
        return self._query(sql)

    def get_top_directors(self, limit: int = 10) -> pd.DataFrame:
        """Return top directors by number of movies."""
        sql = f"""
            SELECT director, COUNT(*) as count
            FROM {MOVIES_TABLE}
            WHERE director IS NOT NULL AND director != ''
            GROUP BY director
            ORDER BY count DESC
            LIMIT ?
        """
        return self._query(sql, (limit,))

    def get_decade_distribution(self) -> pd.DataFrame:
        """Return movie count by decade."""
        sql = f"""
            SELECT decade, COUNT(*) as count
            FROM {MOVIES_TABLE}
            WHERE decade IS NOT NULL AND decade != ''
            GROUP BY decade
            ORDER BY decade
        """
        return self._query(sql)

    def get_average_rating_by_year(self) -> pd.DataFrame:
        """Return average rating by release year."""
        sql = f"""
            SELECT year, AVG(combined_rating) as avg_rating
            FROM {MOVIES_TABLE}
            WHERE year IS NOT NULL AND combined_rating IS NOT NULL
            GROUP BY year
            ORDER BY year
        """
        return self._query(sql)

    def get_runtime_distribution(self) -> pd.DataFrame:
        """Return runtime bucket counts for quick analysis."""
        sql = f"""
            SELECT
                CASE
                    WHEN runtime < 90 THEN 'Menos de 90 min'
                    WHEN runtime < 120 THEN '90-119 min'
                    WHEN runtime < 150 THEN '120-149 min'
                    ELSE '150+ min'
                END as rango,
                COUNT(*) as count
            FROM {MOVIES_TABLE}
            WHERE runtime IS NOT NULL
            GROUP BY rango
            ORDER BY count DESC
        """
        return self._query(sql)

    def get_top_rated(self, limit: int = 10) -> pd.DataFrame:
        """Return top rated movies by combined rating."""
        sql = f"""
            SELECT title, year, genre, director, combined_rating, imdb_rating, tmdb_rating
            FROM {MOVIES_TABLE}
            WHERE combined_rating IS NOT NULL
            ORDER BY combined_rating DESC
            LIMIT ?
        """
        return self._query(sql, (limit,))

    def get_distribution_by_year(self) -> pd.DataFrame:
        """Return movie count distribution by release year."""
        sql = f"""
            SELECT year, COUNT(*) as count
            FROM {MOVIES_TABLE}
            WHERE year IS NOT NULL
            GROUP BY year
            ORDER BY year
        """
        return self._query(sql)

    def get_filtered_movies(
        self,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        rating_tier: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Return movies filtered by genre, year, and/or rating tier.

        Args:
            genre: Primary genre filter.
            year: Exact year filter.
            rating_tier: Exact rating tier filter.

        Returns:
            Filtered movies dataframe.
        """
        conditions: list[str] = []
        params: list[Any] = []

        if genre and genre != "All":
            conditions.append("LOWER(TRIM(SUBSTR(genre, 1, CASE WHEN INSTR(genre, ',') > 0 THEN INSTR(genre, ',') - 1 ELSE LENGTH(genre) END))) = ?")
            params.append(genre.lower())
        if year is not None:
            conditions.append("year = ?")
            params.append(year)
        if rating_tier:
            conditions.append("rating_tier = ?")
            params.append(rating_tier.lower())

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
            SELECT title, year, genre, director, combined_rating, runtime, rating_tier, sources
            FROM {MOVIES_TABLE}
            {where_clause}
            ORDER BY combined_rating DESC
        """
        return self._query(sql, tuple(params))

    def get_available_genres(self) -> list[str]:
        """Return list of distinct primary genres for filter dropdown."""
        df = self.get_movies_by_genre()
        if df.empty:
            return []
        return sorted(
            {
                str(genre).strip().title()
                for genre in df["genre"].tolist()
                if genre
            }
        )

    def get_available_years(self) -> list[int]:
        """Return sorted list of available release years."""
        sql = f"""
            SELECT DISTINCT year FROM {MOVIES_TABLE}
            WHERE year IS NOT NULL
            ORDER BY year DESC
        """
        df = self._query(sql)
        return [int(y) for y in df["year"].tolist()]

    def get_available_rating_tiers(self) -> list[str]:
        """Return list of available rating tiers in Spanish labels."""
        sql = f"""
            SELECT DISTINCT
                CASE
                    WHEN rating_tier = 'excellent' THEN 'Excelente'
                    WHEN rating_tier = 'good' THEN 'Buena'
                    WHEN rating_tier = 'average' THEN 'Promedio'
                    WHEN rating_tier = 'poor' THEN 'Baja'
                    ELSE rating_tier
                END as rating_tier
            FROM {MOVIES_TABLE}
            WHERE rating_tier IS NOT NULL AND rating_tier != ''
            ORDER BY rating_tier
        """
        df = self._query(sql)
        return [str(t) for t in df["rating_tier"].tolist()]
