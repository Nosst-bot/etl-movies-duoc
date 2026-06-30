"""Load consolidated movie data into SQLite."""

import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

from etl.config import DATABASE_DIR, DATABASE_PATH, MOVIES_COLUMNS, MOVIES_TABLE
from etl.logging_config import setup_logging

logger = setup_logging("load")

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {MOVIES_TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    year INTEGER,
    genre TEXT,
    director TEXT,
    actors TEXT,
    runtime INTEGER,
    imdb_rating REAL,
    metascore REAL,
    source_rating REAL,
    tmdb_rating REAL,
    combined_rating REAL,
    rating_tier TEXT,
    decade TEXT,
    sources TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Create a SQLite connection with row factory.

    Args:
        db_path: Optional database path override.

    Returns:
        SQLite connection.
    """
    path = db_path or DATABASE_PATH
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(conn: Optional[sqlite3.Connection] = None) -> None:
    """
    Create the movies table if it does not exist.

    Args:
        conn: Optional existing connection.
    """
    close_conn = conn is None
    connection = conn or get_connection()
    try:
        connection.execute(CREATE_TABLE_SQL)
        connection.commit()
        logger.info("Database initialized at %s", DATABASE_PATH)
    finally:
        if close_conn:
            connection.close()


def prepare_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Select and order columns for database insertion.

    Args:
        df: Consolidated dataframe.

    Returns:
        Dataframe ready for load.
    """
    load_df = df.copy()
    for col in MOVIES_COLUMNS:
        if col == "id":
            continue
        if col not in load_df.columns:
            load_df[col] = None

    return load_df[[c for c in MOVIES_COLUMNS if c != "id"]]


def load_to_sqlite(
    df: pd.DataFrame,
    db_path: Optional[Path] = None,
    replace: bool = True,
) -> int:
    """
    Load consolidated movie records into SQLite.

    Args:
        df: Processed dataframe.
        db_path: Optional database path override.
        replace: If True, replace existing table data.

    Returns:
        Number of rows inserted.
    """
    path = db_path or DATABASE_PATH
    conn = get_connection(path)
    try:
        initialize_database(conn)
        load_df = prepare_records(df)

        if replace:
            conn.execute(f"DELETE FROM {MOVIES_TABLE}")
            logger.info("Existing records cleared from %s", MOVIES_TABLE)

        columns = [c for c in MOVIES_COLUMNS if c != "id"]
        placeholders = ", ".join(["?"] * len(columns))
        col_names = ", ".join(columns)
        insert_sql = f"INSERT INTO {MOVIES_TABLE} ({col_names}) VALUES ({placeholders})"

        records = [
            tuple(None if pd.isna(val) else val for val in row)
            for row in load_df[columns].itertuples(index=False, name=None)
        ]

        conn.executemany(insert_sql, records)
        conn.commit()
        logger.info("Loaded %d records into %s", len(records), path)
        return len(records)
    except sqlite3.Error as exc:
        logger.error("SQLite load error: %s", exc)
        raise
    finally:
        conn.close()
