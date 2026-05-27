from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Proyecto 2 Big Data - Visualización",
    page_icon="📍",
    layout="wide"
)

st.title("📍 Proyecto 2 Big Data - Lugares de interés en Medellín")

st.write(
    "Aplicación de visualización para explorar resultados analíticos sobre lugares de interés "
    "en Medellín. La aplicación usa archivos CSV de la zona trusted del proyecto y permite "
    "analizar barrios, tipos de lugar, ratings, reseñas, niveles de precio y disponibilidad en fin de semana."
)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "api" / "sample_data"

PLACES_PATH = DATA_DIR / "trusted_places_clean.csv"
TYPES_PATH = DATA_DIR / "trusted_place_types_clean.csv"
HOURS_PATH = DATA_DIR / "trusted_place_hours_clean.csv"


@st.cache_data
def load_data():
    places = pd.read_csv(PLACES_PATH)
    place_types = pd.read_csv(TYPES_PATH)
    place_hours = pd.read_csv(HOURS_PATH)

    places["rating"] = pd.to_numeric(places["rating"], errors="coerce")
    places["review_count"] = pd.to_numeric(places["review_count"], errors="coerce").fillna(0).astype(int)
    places["price_level"] = pd.to_numeric(places["price_level"], errors="coerce").fillna(0).astype(int)

    place_hours["is_open"] = (
        place_hours["is_open"]
        .astype(str)
        .str.lower()
        .isin(["true", "1", "yes", "si", "sí"])
    )

    primary_types = (
        place_types
        .dropna(subset=["place_id", "type"])
        .groupby("place_id", as_index=False)
        .agg(
            primary_type=("type", "first"),
            types_count=("type", "count")
        )
    )

    weekend_open = (
        place_hours[
            place_hours["day_en"].isin(["Saturday", "Sunday"]) &
            (place_hours["is_open"])
        ]
        .groupby("place_id", as_index=False)
        .agg(weekend_open_days=("day_en", "count"))
    )

    df = places.merge(primary_types, on="place_id", how="left")
    df = df.merge(weekend_open, on="place_id", how="left")

    df["primary_type"] = df["primary_type"].fillna("Sin categoría")
    df["types_count"] = df["types_count"].fillna(0).astype(int)
    df["weekend_open_days"] = df["weekend_open_days"].fillna(0).astype(int)
    df["opens_on_weekend"] = df["weekend_open_days"] > 0

    return df, place_types, place_hours


df, place_types, place_hours = load_data()

st.sidebar.header("Filtros")

all_neighborhoods = sorted(df["neighborhood"].dropna().unique())
all_types = sorted(df["primary_type"].dropna().unique())

top_limit = st.sidebar.slider(
    "Cantidad de elementos en rankings",
    min_value=5,
    max_value=30,
    value=15,
    step=5
)

neighborhoods = st.sidebar.multiselect(
    "Barrio",
    options=all_neighborhoods,
    default=[]
)

types = st.sidebar.multiselect(
    "Tipo de lugar principal",
    options=all_types,
    default=[]
)

min_rating = st.sidebar.slider(
    "Rating mínimo",
    min_value=0.0,
    max_value=5.0,
    value=0.0,
    step=0.1
)

only_weekend = st.sidebar.checkbox("Solo lugares abiertos en fin de semana")

filtered = df.copy()

if neighborhoods:
    filtered = filtered[filtered["neighborhood"].isin(neighborhoods)]

if types:
    filtered = filtered[filtered["primary_type"].isin(types)]

filtered = filtered[filtered["rating"].fillna(0) >= min_rating]

if only_weekend:
    filtered = filtered[filtered["opens_on_weekend"]]

total_places = len(filtered)
average_rating = filtered["rating"].dropna().mean() if total_places else 0
total_reviews = filtered["review_count"].sum() if total_places else 0
weekend_places = filtered["opens_on_weekend"].sum() if total_places else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("Lugares filtrados", f"{total_places:,}")
col2.metric("Rating promedio", f"{average_rating:.2f}" if total_places else "0")
col3.metric("Total reseñas", f"{total_reviews:,}")
col4.metric("Abren fin de semana", f"{weekend_places:,}")

st.divider()

places_by_neighborhood = (
    filtered
    .groupby("neighborhood", as_index=False)
    .agg(
        places_count=("place_id", "count"),
        average_rating=("rating", "mean"),
        total_reviews=("review_count", "sum")
    )
    .sort_values("places_count", ascending=False)
    .head(top_limit)
)

places_by_type = (
    filtered
    .groupby("primary_type", as_index=False)
    .agg(
        places_count=("place_id", "count"),
        average_rating=("rating", "mean"),
        total_reviews=("review_count", "sum")
    )
    .sort_values("places_count", ascending=False)
    .head(top_limit)
)

left, right = st.columns([1.35, 1])

with left:
    st.subheader("Top barrios por cantidad de lugares")

    fig_neighborhood = px.bar(
        places_by_neighborhood,
        x="places_count",
        y="neighborhood",
        orientation="h",
        title="Cantidad de lugares por barrio",
        text="places_count",
        hover_data=["average_rating", "total_reviews"]
    )

    fig_neighborhood.update_layout(
        height=520,
        yaxis={"categoryorder": "total ascending"}
    )

    st.plotly_chart(fig_neighborhood, use_container_width=True)

with right:
    st.subheader("Tipos de lugar más frecuentes")

    fig_type = px.bar(
        places_by_type,
        x="places_count",
        y="primary_type",
        orientation="h",
        title="Cantidad de lugares por tipo principal",
        text="places_count",
        hover_data=["average_rating", "total_reviews"]
    )

    fig_type.update_layout(
        height=520,
        yaxis={"categoryorder": "total ascending"}
    )

    st.plotly_chart(fig_type, use_container_width=True)

st.subheader("Rating promedio por nivel de precio")

price_rating = (
    filtered[filtered["price_level"] > 0]
    .groupby("price_level", as_index=False)
    .agg(
        average_rating=("rating", "mean"),
        places_count=("place_id", "count")
    )
    .sort_values("price_level")
)

fig_price = px.bar(
    price_rating,
    x="price_level",
    y="average_rating",
    color="places_count",
    title="Rating promedio según nivel de precio",
    text_auto=".2f",
    hover_data=["places_count"]
)

fig_price.update_layout(height=420)

st.plotly_chart(fig_price, use_container_width=True)

st.subheader("Top lugares por rating y reseñas")

top_places = (
    filtered
    .sort_values(["rating", "review_count"], ascending=False)
    .head(25)
)

columns_to_show = [
    "name",
    "neighborhood",
    "primary_type",
    "rating",
    "price_level",
    "review_count",
    "opens_on_weekend",
    "address",
]

st.dataframe(
    top_places[columns_to_show],
    use_container_width=True,
    height=430
)

st.subheader("Conclusión descriptiva")

if not filtered.empty and not places_by_neighborhood.empty and not places_by_type.empty:
    top_neighborhood = places_by_neighborhood.iloc[0]["neighborhood"]
    top_type = places_by_type.iloc[0]["primary_type"]
    top_reviews_type = places_by_type.sort_values("total_reviews", ascending=False).iloc[0]["primary_type"]

    st.success(
        f"En los datos filtrados, el barrio con mayor cantidad de lugares es **{top_neighborhood}** "
        f"y el tipo principal más frecuente es **{top_type}**. "
        f"El tipo con mayor volumen de reseñas dentro del filtro es **{top_reviews_type}**. "
        f"El rating promedio del conjunto filtrado es **{average_rating:.2f}**."
    )
else:
    st.warning("No hay datos para los filtros seleccionados.")

st.caption(
    "Nota: los archivos utilizados representan la estructura trusted esperada del proyecto. "
    "En la integración final pueden ser reemplazados por los outputs definitivos del pipeline raw → trusted."
)