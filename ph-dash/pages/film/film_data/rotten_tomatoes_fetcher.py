import hashlib
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

DATA_PATH = Path(__file__).parent / "rotten_tomatoes_yearly_fresh.csv"

CATEGORICAL_COLORS = [
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
]
GRID_COLOR = "#e1e0d9"
AXIS_COLOR = "#c3c2b7"
MUTED_TEXT = "#898781"

MAX_SELECTED_FILMS = len(CATEGORICAL_COLORS)

_df_cache = None


def load_rt_yearly_df() -> pd.DataFrame:
    global _df_cache
    if _df_cache is None:
        df = pd.read_csv(DATA_PATH)
        df["release_year"] = df["release_year"].astype("Int64")
        _df_cache = df
    return _df_cache


def get_movie_options() -> list[dict]:
    df = load_rt_yearly_df()
    movies = df[["rotten_tomatoes_link", "movie_title", "release_year"]].drop_duplicates()
    movies = movies.sort_values(["movie_title", "release_year"])
    options = []
    for _, row in movies.iterrows():
        year = row["release_year"]
        label = f"{row['movie_title']} ({int(year)})" if pd.notna(year) else row["movie_title"]
        options.append({"label": label, "value": row["rotten_tomatoes_link"]})
    return options


def _color_for_link(link: str) -> str:
    idx = int(hashlib.sha256(link.encode()).hexdigest(), 16) % len(CATEGORICAL_COLORS)
    return CATEGORICAL_COLORS[idx]


def _empty_fig(message: str) -> go.Figure:
    return go.Figure().update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=20),
        annotations=[{
            "text": message,
            "showarrow": False,
            "font": {"size": 13, "color": MUTED_TEXT},
            "xref": "paper", "yref": "paper",
            "x": 0.5, "y": 0.5,
        }],
    )


def build_freshness_chart(selected_links: list[str]) -> go.Figure:
    if not selected_links:
        return _empty_fig("Select one or more films above to see their %Fresh trend over time")

    if len(selected_links) > MAX_SELECTED_FILMS:
        selected_links = selected_links[:MAX_SELECTED_FILMS]

    df = load_rt_yearly_df()
    df = df[df["rotten_tomatoes_link"].isin(selected_links)]
    if df.empty:
        return _empty_fig("No review data...")

    fig = go.Figure()
    for link in selected_links:
        movie_df = df[df["rotten_tomatoes_link"] == link].sort_values("year")
        if movie_df.empty:
            continue
        title = movie_df.iloc[0]["movie_title"]
        color = _color_for_link(link)

        # Marker size signals review volume for that year
        sizes = movie_df["total_count"].clip(upper=30) * 0.6 + 8

        fig.add_trace(go.Scatter(
            x=movie_df["year"],
            y=movie_df["pct_fresh"],
            mode="lines+markers",
            name=title,
            line=dict(color=color, width=2),
            marker=dict(size=sizes, color=color, line=dict(width=2, color="#ffffff")),
            customdata=movie_df["total_count"],
            hovertemplate=(
                f"<b>{title}</b><br>%{{x}}: %{{y:.1f}}% Fresh"
                "<br>%{customdata} review(s)<extra></extra>"
            ),
        ))

        last = movie_df.iloc[-1]
        fig.add_annotation(
            x=last["year"], y=last["pct_fresh"],
            text=f"{last['pct_fresh']:.0f}%",
            showarrow=False, xanchor="left", xshift=10,
            font=dict(size=11, color="#0b0b0b"),
        )

    show_legend = len(selected_links) > 1
    fig.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=show_legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(
            title="Year", dtick=2,
            showgrid=False, zeroline=False,
            linecolor=AXIS_COLOR,
        ),
        yaxis=dict(
            title="% Fresh Reviews", range=[-5, 105],
            ticksuffix="%",
            gridcolor=GRID_COLOR, zeroline=False,
        ),
        margin=dict(t=40 if show_legend else 20, b=10, l=10, r=70),
    )
    return fig
