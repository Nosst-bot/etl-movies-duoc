"""Streamlit dashboard for movies analytics."""

import sys
from pathlib import Path

# Streamlit runs this file directly; ensure project root is on sys.path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from etl.config import DATABASE_PATH
from repository.movie_repository import MovieRepository

st.set_page_config(
    page_title="Movies Analytics Dashboard",
    page_icon="🎬",
    layout="wide",
)


@st.cache_resource
def get_repository() -> MovieRepository:
    """Create cached repository instance."""
    return MovieRepository(DATABASE_PATH)


def render_dashboard() -> None:
    """Render the main dashboard layout."""
    repo = get_repository()

    if not DATABASE_PATH.exists():
        st.error(
            "No se encontró la base de datos. Ejecuta primero el pipeline ETL: `python run_pipeline.py`"
        )
        st.stop()

    total = repo.get_total_count()
    if total == 0:
        st.warning("No hay películas en la base de datos. Ejecuta el pipeline ETL para cargar datos.")
        st.stop()

    st.title("🎬 Panel de análisis de películas")
    st.markdown("Exploración interactiva de datos consolidados de IMDB, TMDB y OMDb.")

    avg_rating = repo.get_average_rating()
    avg_runtime = repo.get_average_runtime()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de películas", f"{total:,}")
    col2.metric("Calificación promedio", f"{avg_rating:.2f}")
    col3.metric("Duración promedio", f"{avg_runtime:.0f} min")
    col4.metric("Fuentes de datos", "IMDB + TMDB + OMDb")

    st.divider()

    genres = repo.get_available_genres()
    years = repo.get_available_years()
    rating_tiers = repo.get_available_rating_tiers()

    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        selected_genre = st.selectbox("Filtrar por género", ["Todos"] + genres)
    with filter_col2:
        selected_year = st.selectbox("Filtrar por año", ["Todos"] + [str(y) for y in years])
    with filter_col3:
        selected_tier = st.selectbox("Filtrar por categoría de calificación", ["Todas"] + rating_tiers)

    year_filter = int(selected_year) if selected_year != "Todos" else None
    genre_filter = selected_genre if selected_genre != "Todos" else None
    tier_filter = selected_tier if selected_tier != "Todas" else None
    filtered = repo.get_filtered_movies(genre=genre_filter, year=year_filter, rating_tier=tier_filter)

    st.subheader("Resumen visual")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        genre_df = repo.get_movies_by_genre().head(15)
        if not genre_df.empty:
            fig_genre = px.bar(
                genre_df,
                x="genre",
                y="count",
                color="count",
                color_continuous_scale="Viridis",
                labels={"genre": "Género", "count": "Cantidad"},
            )
            fig_genre.update_layout(showlegend=False, xaxis_tickangle=-45, title="Películas por género")
            st.plotly_chart(fig_genre, use_container_width=True)

    with chart_col2:
        year_df = repo.get_distribution_by_year()
        if not year_df.empty:
            fig_year = px.line(
                year_df,
                x="year",
                y="count",
                markers=True,
                labels={"year": "Año", "count": "Películas"},
            )
            fig_year.update_layout(title="Distribución por año")
            st.plotly_chart(fig_year, use_container_width=True)

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        tier_df = repo.get_rating_tier_distribution()
        if not tier_df.empty:
            fig_tier = px.pie(
                tier_df,
                names="nivel",
                values="count",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            fig_tier.update_layout(title="Distribución por categoría de calificación")
            st.plotly_chart(fig_tier, use_container_width=True)

    with chart_col4:
        source_df = repo.get_source_coverage()
        if not source_df.empty:
            fig_sources = px.bar(
                source_df,
                x="source",
                y="count",
                color="count",
                color_continuous_scale="Blues",
                labels={"source": "Fuente", "count": "Películas"},
            )
            fig_sources.update_layout(title="Cobertura por fuente", xaxis_tickangle=-30)
            st.plotly_chart(fig_sources, use_container_width=True)

    chart_col5, chart_col6 = st.columns(2)

    with chart_col5:
        decade_df = repo.get_decade_distribution()
        if not decade_df.empty:
            fig_decade = px.bar(
                decade_df,
                x="decade",
                y="count",
                color="count",
                color_continuous_scale="Cividis",
                labels={"decade": "Década", "count": "Películas"},
            )
            fig_decade.update_layout(title="Películas por década")
            st.plotly_chart(fig_decade, use_container_width=True)

    with chart_col6:
        runtime_df = repo.get_runtime_distribution()
        if not runtime_df.empty:
            fig_runtime = px.bar(
                runtime_df,
                x="rango",
                y="count",
                color="count",
                color_continuous_scale="Sunsetdark",
                labels={"rango": "Rango de duración", "count": "Películas"},
            )
            fig_runtime.update_layout(title="Duración de películas")
            st.plotly_chart(fig_runtime, use_container_width=True)

    st.subheader("Tendencia de calificación por año")
    rating_year_df = repo.get_average_rating_by_year()
    if not rating_year_df.empty:
        fig_rating_year = px.line(
            rating_year_df,
            x="year",
            y="avg_rating",
            markers=True,
            labels={"year": "Año", "avg_rating": "Calificación promedio"},
        )
        fig_rating_year.update_layout(title="Calificación promedio por año")
        st.plotly_chart(fig_rating_year, use_container_width=True)

    st.subheader("Directores más prolíficos")
    directors_df = repo.get_top_directors(10)
    if not directors_df.empty:
        fig_directors = px.bar(
            directors_df,
            x="director",
            y="count",
            color="count",
            color_continuous_scale="Magma",
            labels={"director": "Director", "count": "Películas"},
        )
        fig_directors.update_layout(title="Top 10 directores", xaxis_tickangle=-30)
        st.plotly_chart(fig_directors, use_container_width=True)

    st.subheader("Top 10 mejores películas por calificación")
    top_df = repo.get_top_rated(10)
    if not top_df.empty:
        fig_top = px.bar(
            top_df,
            x="combined_rating",
            y="title",
            orientation="h",
            color="combined_rating",
            color_continuous_scale="Plasma",
            labels={"combined_rating": "Calificación", "title": "Título"},
        )
        fig_top.update_layout(yaxis={"categoryorder": "total ascending"}, title="Top 10")
        st.plotly_chart(fig_top, use_container_width=True)

        st.dataframe(top_df.rename(columns={
            "title": "Título",
            "year": "Año",
            "genre": "Género",
            "director": "Director",
            "combined_rating": "Calificación combinada",
            "imdb_rating": "IMDB",
            "tmdb_rating": "TMDB",
        }), use_container_width=True, hide_index=True)

    st.subheader("Resultados filtrados")
    if not filtered.empty:
        filtered_display = filtered.rename(columns={
            "title": "Título",
            "year": "Año",
            "genre": "Género",
            "director": "Director",
            "combined_rating": "Calificación combinada",
            "runtime": "Duración (min)",
            "rating_tier": "Categoría de calificación",
            "sources": "Fuentes",
        })
        st.dataframe(filtered_display, use_container_width=True, hide_index=True)
    else:
        st.info("No hay películas que coincidan con los filtros seleccionados.")
    st.caption(f"Mostrando {len(filtered)} películas")


if __name__ == "__main__":
    render_dashboard()
