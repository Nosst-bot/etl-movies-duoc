"""Data transformation, standardization, and merging."""

import re
from typing import Optional

import pandas as pd

from etl.config import DATA_PROCESSED_DIR
from etl.logging_config import setup_logging
from etl.validators import run_all_validations

logger = setup_logging("transform")

MAX_YEAR = 2026

COLUMN_ALIASES: dict[str, list[str]] = {
    "title": [
        "Series_Title",
        "series_title",
        "title",
        "original_title",
        "movie_title",
        "name",
    ],
    "year": [
        "Released_Year",
        "released_year",
        "release_year",
        "Year",
        "year",
    ],
    "genre": ["Genre", "genre", "genres"],
    "director": ["Director", "director"],
    "actors": ["Actors", "actors", "Star1", "cast"],
    "runtime": ["Runtime", "runtime", "running_time"],
    "imdb_rating": [
        "IMDB_Rating",
        "imdb_rating",
        "imdbRating",
        "vote_average",
    ],
    "metascore": ["Meta_score", "meta_score", "metascore", "Metascore"],
    "tmdb_rating": ["vote_average", "tmdb_rating"],
    "release_date": ["release_date", "Release_Date"],
}


def normalize_title(title: Optional[str]) -> str:
    """
    Normalize a movie title for matching across sources.

    Args:
        title: Raw title string.

    Returns:
        Normalized lowercase title without special characters.
    """
    if title is None or (isinstance(title, float) and pd.isna(title)):
        return ""
    cleaned = re.sub(r"[^\w\s]", "", str(title).lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _resolve_column(df: pd.DataFrame, canonical: str) -> Optional[str]:
    """Find the first matching column alias in the dataframe."""
    lower_map = {c.lower(): c for c in df.columns}
    for alias in COLUMN_ALIASES.get(canonical, [canonical]):
        if alias in df.columns:
            return alias
        if alias.lower() in lower_map:
            return lower_map[alias.lower()]
    return None


def standardize_columns(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """
    Rename columns to canonical names and add source tag.

    Args:
        df: Raw dataframe.
        source: Data source identifier (imdb, tmdb, omdb).

    Returns:
        Standardized dataframe.
    """
    rename_map: dict[str, str] = {}
    for canonical in COLUMN_ALIASES:
        col = _resolve_column(df, canonical)
        if col and col != canonical:
            rename_map[col] = canonical

    result = df.rename(columns=rename_map).copy()
    result["data_source"] = source

    # Ensure canonical columns exist
    for col in COLUMN_ALIASES:
        if col not in result.columns:
            result[col] = None

    return result


def parse_runtime_minutes(runtime_value: Optional[str | float | int]) -> Optional[int]:
    """
    Parse runtime string (e.g. '142 min') to integer minutes.

    Args:
        runtime_value: Runtime in various formats.

    Returns:
        Runtime in minutes or None.
    """
    if runtime_value is None or (isinstance(runtime_value, float) and pd.isna(runtime_value)):
        return None
    if isinstance(runtime_value, (int, float)):
        return int(runtime_value)

    match = re.search(r"(\d+)", str(runtime_value))
    return int(match.group(1)) if match else None


def extract_year(value: Optional[str | int | float]) -> Optional[int]:
    """
    Extract a four-digit year from mixed date/year strings.

    Args:
        value: Year or date string.

    Returns:
        Integer year or None.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, int):
        return value if 1888 <= value <= MAX_YEAR else None

    text = str(value).strip()
    if text.isdigit() and len(text) == 4:
        year = int(text)
        return year if 1888 <= year <= MAX_YEAR else None

    match = re.search(r"(19|20)\d{2}", text)
    return int(match.group()) if match and 1888 <= int(match.group()) <= MAX_YEAR else None


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean nulls, convert types, and normalize text fields.

    Args:
        df: Standardized dataframe.

    Returns:
        Cleaned dataframe.
    """
    df = df.copy()
    df["title"] = df["title"].astype(str).str.strip()
    df["title_key"] = df["title"].apply(normalize_title)

    if "release_date" in df.columns:
        df["year"] = df.apply(
            lambda row: extract_year(row.get("year")) or extract_year(row.get("release_date")),
            axis=1,
        )
    else:
        df["year"] = df["year"].apply(extract_year)

    year_median = df["year"].median()
    if pd.notna(year_median):
        df["year"] = df["year"].fillna(int(year_median))
    df["year"] = df["year"].astype(int)

    df["runtime"] = df["runtime"].apply(parse_runtime_minutes)

    for col in ["imdb_rating", "metascore", "tmdb_rating", "source_rating"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    text_cols = ["genre", "director", "actors"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).replace({"nan": None, "None": None})

    df = df[df["title_key"] != ""].copy()
    return df


def create_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create derived columns: combined rating, tier, decade, sources.

    Args:
        df: Cleaned consolidated dataframe.

    Returns:
        Dataframe with derived metrics.
    """
    df = df.copy()

    rating_cols = [c for c in ["imdb_rating", "tmdb_rating", "source_rating"] if c in df.columns]
    if rating_cols:
        df["combined_rating"] = df[rating_cols].mean(axis=1, skipna=True)
    else:
        df["combined_rating"] = None

    def rating_tier(score: Optional[float]) -> str:
        if score is None or pd.isna(score):
            return "unknown"
        if score >= 8.0:
            return "excellent"
        if score >= 7.0:
            return "good"
        if score >= 5.0:
            return "average"
        return "poor"

    df["rating_tier"] = df["combined_rating"].apply(rating_tier)
    df["decade"] = df["year"].apply(
        lambda y: f"{int(y // 10) * 10}s" if y is not None and not pd.isna(y) else None
    )

    if "data_source" in df.columns:
        df["sources"] = df["data_source"]
    else:
        df["sources"] = "merged"

    return df


def _aggregate_merged_group(group: pd.DataFrame) -> pd.Series:
    """Aggregate duplicate title keys using first non-null value."""
    result: dict = {}
    for col in group.columns:
        non_null = group[col].dropna()
        if len(non_null) > 0:
            if col == "data_source":
                result[col] = ",".join(sorted(set(group[col].astype(str))))
            else:
                result[col] = non_null.iloc[0]
        else:
            result[col] = None
    return pd.Series(result)


def merge_sources(
    imdb_df: pd.DataFrame,
    tmdb_df: pd.DataFrame,
    omdb_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Merge IMDB, TMDB, and OMDb data on normalized title key.

    Args:
        imdb_df: Standardized IMDB data.
        tmdb_df: Standardized TMDB data.
        omdb_df: Optional standardized OMDb enrichment data.

    Returns:
        Consolidated dataframe.
    """
    imdb = clean_dataframe(standardize_columns(imdb_df, "imdb")).drop_duplicates(subset=["title_key"]).copy()
    tmdb = clean_dataframe(standardize_columns(tmdb_df, "tmdb")).drop_duplicates(subset=["title_key"]).copy()

    allowed_title_keys = set(imdb["title_key"].dropna().astype(str))
    tmdb = tmdb[tmdb["title_key"].isin(allowed_title_keys)].copy()

    merged = pd.merge(
        imdb,
        tmdb,
        on="title_key",
        how="left",
        suffixes=("_imdb", "_tmdb"),
    )

    def coalesce(row: pd.Series, col: str) -> Optional[object]:
        imdb_val = row.get(f"{col}_imdb")
        tmdb_val = row.get(f"{col}_tmdb")
        if imdb_val is not None and not (isinstance(imdb_val, float) and pd.isna(imdb_val)):
            return imdb_val
        if tmdb_val is not None and not (isinstance(tmdb_val, float) and pd.isna(tmdb_val)):
            return tmdb_val
        return row.get(col)

    consolidated = pd.DataFrame()
    consolidated["title_key"] = merged["title_key"]
    for col in ["title", "year", "genre", "director", "actors", "runtime",
                "imdb_rating", "metascore", "tmdb_rating"]:
        consolidated[col] = merged.apply(lambda r, c=col: coalesce(r, c), axis=1)

    sources_imdb = merged.get("data_source_imdb", pd.Series(dtype=str))
    sources_tmdb = merged.get("data_source_tmdb", pd.Series(dtype=str))
    consolidated["data_source"] = sources_imdb.fillna("") + "," + sources_tmdb.fillna("")
    consolidated["data_source"] = consolidated["data_source"].str.strip(",")

    if omdb_df is not None and not omdb_df.empty:
        omdb = clean_dataframe(standardize_columns(omdb_df, "omdb"))
        omdb["title_key"] = omdb["title"].apply(normalize_title)
        for col in ["genre", "director", "actors", "runtime", "imdb_rating",
                    "metascore", "source_rating"]:
            if col in omdb.columns:
                consolidated = consolidated.merge(
                    omdb[["title_key", col]].drop_duplicates("title_key"),
                    on="title_key",
                    how="left",
                    suffixes=("", "_omdb"),
                )
                omdb_col = f"{col}_omdb"
                if omdb_col in consolidated.columns:
                    consolidated[col] = consolidated[col].fillna(consolidated[omdb_col])
                    consolidated.drop(columns=[omdb_col], inplace=True)

        consolidated["data_source"] = consolidated["data_source"].fillna("") + ",omdb"
        consolidated["data_source"] = consolidated["data_source"].str.strip(",")

    consolidated["source_rating"] = consolidated.get("imdb_rating")
    consolidated = create_derived_metrics(consolidated)
    consolidated = run_all_validations(consolidated)

    consolidated.drop(columns=["title_key"], inplace=True, errors="ignore")
    return consolidated


def transform_and_save(
    imdb_df: pd.DataFrame,
    tmdb_df: pd.DataFrame,
    omdb_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Run full transformation pipeline and save processed CSV.

    Args:
        imdb_df: Raw IMDB dataframe.
        tmdb_df: Raw TMDB dataframe.
        omdb_df: Optional OMDb dataframe.

    Returns:
        Processed consolidated dataframe.
    """
    logger.info("Starting transformation pipeline")
    result = merge_sources(imdb_df, tmdb_df, omdb_df)

    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DATA_PROCESSED_DIR / "movies_consolidated.csv"
    result.to_csv(output_path, index=False)
    logger.info("Saved processed data to %s (%d rows)", output_path, len(result))

    return result
