"""Data validation rules for the movies ETL pipeline."""

from typing import Any

import pandas as pd

from etl.logging_config import setup_logging

logger = setup_logging("validators")

MIN_IMDB_RATING = 0.0
MAX_IMDB_RATING = 10.0
MIN_METASCORE = 0.0
MAX_METASCORE = 100.0
MIN_YEAR = 1888
MAX_YEAR = 2026


def validate_empty_titles(df: pd.DataFrame, title_col: str = "title") -> pd.DataFrame:
    """
    Remove rows with empty or whitespace-only titles.

    Args:
        df: Input dataframe.
        title_col: Column name for titles.

    Returns:
        Filtered dataframe.
    """
    if title_col not in df.columns:
        logger.warning("Title column '%s' not found for empty title validation", title_col)
        return df

    mask = df[title_col].astype(str).str.strip().eq("") | df[title_col].isna()
    invalid_count = mask.sum()
    if invalid_count > 0:
        logger.error("Validation: %d records with empty titles removed", invalid_count)
        df = df.loc[~mask].copy()
    return df


def validate_rating_range(
    df: pd.DataFrame,
    column: str,
    min_val: float,
    max_val: float,
) -> pd.DataFrame:
    """
    Nullify ratings outside the allowed range and log errors.

    Args:
        df: Input dataframe.
        column: Rating column name.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.

    Returns:
        Dataframe with invalid ratings set to NaN.
    """
    if column not in df.columns:
        return df

    numeric = pd.to_numeric(df[column], errors="coerce")
    invalid_mask = numeric.notna() & ((numeric < min_val) | (numeric > max_val))
    invalid_count = invalid_mask.sum()
    if invalid_count > 0:
        logger.error(
            "Validation: %d records with %s out of range [%.1f, %.1f]",
            invalid_count,
            column,
            min_val,
            max_val,
        )
        df = df.copy()
        df.loc[invalid_mask, column] = None
    return df


def validate_year(df: pd.DataFrame, year_col: str = "year") -> pd.DataFrame:
    """
    Remove rows with invalid release years.

    Args:
        df: Input dataframe.
        year_col: Year column name.

    Returns:
        Filtered dataframe.
    """
    if year_col not in df.columns:
        return df

    years = pd.to_numeric(df[year_col], errors="coerce")
    invalid_mask = years.notna() & ((years < MIN_YEAR) | (years > MAX_YEAR))
    invalid_count = invalid_mask.sum()
    if invalid_count > 0:
        logger.error("Validation: %d records with invalid year removed", invalid_count)
        df = df.loc[~invalid_mask].copy()
    return df


def validate_critical_nulls(
    df: pd.DataFrame,
    critical_columns: list[str],
) -> pd.DataFrame:
    """
    Remove rows where all critical columns are null.

    Args:
        df: Input dataframe.
        critical_columns: Columns that must have at least one non-null value.

    Returns:
        Filtered dataframe.
    """
    existing = [c for c in critical_columns if c in df.columns]
    if not existing:
        return df

    all_null_mask = df[existing].isna().all(axis=1)
    invalid_count = all_null_mask.sum()
    if invalid_count > 0:
        logger.error(
            "Validation: %d records with all critical fields null removed",
            invalid_count,
        )
        df = df.loc[~all_null_mask].copy()
    return df


def validate_and_remove_duplicates(
    df: pd.DataFrame,
    subset: list[str],
) -> pd.DataFrame:
    """
    Remove duplicate records based on subset columns.

    Args:
        df: Input dataframe.
        subset: Columns defining uniqueness.

    Returns:
        Deduplicated dataframe.
    """
    existing = [c for c in subset if c in df.columns]
    if not existing:
        return df

    before = len(df)
    df = df.drop_duplicates(subset=existing, keep="first")
    removed = before - len(df)
    if removed > 0:
        logger.error("Validation: %d duplicate records removed", removed)
    return df


def run_all_validations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all validation rules to the consolidated movies dataframe.

    Args:
        df: Consolidated dataframe.

    Returns:
        Validated dataframe.
    """
    logger.info("Running validations on %d records", len(df))
    df = validate_empty_titles(df)
    df = validate_rating_range(df, "imdb_rating", MIN_IMDB_RATING, MAX_IMDB_RATING)
    df = validate_rating_range(df, "metascore", MIN_METASCORE, MAX_METASCORE)
    df = validate_rating_range(df, "tmdb_rating", MIN_IMDB_RATING, MAX_IMDB_RATING)
    df = validate_rating_range(df, "source_rating", MIN_IMDB_RATING, MAX_IMDB_RATING)
    df = validate_year(df)
    df = validate_critical_nulls(df, ["title", "imdb_rating", "tmdb_rating"])
    df = validate_and_remove_duplicates(df, ["title", "year"])
    logger.info("Validations complete: %d records remaining", len(df))
    return df
