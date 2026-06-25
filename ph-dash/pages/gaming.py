import pandas as pd
from io import StringIO
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

from data.rawg_fetcher import fetch_rawg_games
from data.steam_fetcher import fetch_game_sentiments

# Platform names exactly as RAWG returns them
PLATFORM_OPTIONS = [
    {"label": "PC",              "value": "PC"},
    {"label": "PlayStation 1",   "value": "PlayStation"},
    {"label": "Nintendo 64",     "value": "Nintendo 64"},
    {"label": "SNES",            "value": "SNES"},
    {"label": "Sega Genesis",    "value": "Sega Mega Drive/Genesis"},
    {"label": "Sega Saturn",     "value": "Sega Saturn"},
]
ALL_PLATFORMS = [p["value"] for p in PLATFORM_OPTIONS]


def _empty_fig(message: str) -> go.Figure:
    return go.Figure().update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=20),
        annotations=[{
            "text": message,
            "showarrow": False,
            "font": {"size": 13, "color": "#999"},
            "xref": "paper", "yref": "paper",
            "x": 0.5, "y": 0.5,
        }],
    )


# ── Layout ────────────────────────────────────────────────────────────────────

def layout():
    return dbc.Container([
        dcc.Store(id="gaming-rawg-store"),
        dcc.Store(id="gaming-sentiment-store"),

        # Header
        dbc.Row(dbc.Col([
            dcc.Link("← Back to Hub", href="/", className="back-link"),
            html.H1("Gaming's Jump to 3D", className="mt-3 mb-1"),
            html.P(
                "How Metacritic scores and community sentiment shifted as the industry "
                "moved from 2D to 3D (1994–2000).",
                className="text-muted mb-4",
            ),
        ])),

        # API Config
        dbc.Accordion([
            dbc.AccordionItem([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("RAWG API Key"),
                        dbc.Input(
                            id="rawg-key",
                            type="password",
                            placeholder="Paste your RAWG API key here",
                        ),
                    ], width=5),
                ], className="mb-3"),
                dbc.Button(
                    "Fetch Game Data", id="fetch-games-btn",
                    color="primary", className="me-2",
                ),
                html.Span(id="fetch-games-status", className="text-muted small align-middle"),
            ], title="API Configuration"),
        ], start_collapsed=False, className="mb-4"),

        # Platform filter
        html.Div([
            html.Strong("Filter by Platform:  "),
            dcc.Checklist(
                id="platform-filter",
                options=PLATFORM_OPTIONS,
                value=ALL_PLATFORMS,
                inline=True,
                inputStyle={"margin-right": "5px"},
                labelStyle={"margin-right": "20px", "user-select": "none"},
            ),
        ], className="mb-4 p-3 bg-light rounded"),

        # Charts row
        dbc.Row([
            dbc.Col([
                html.H5("Metacritic Scores: 2D vs 3D", className="mb-2"),
                dcc.Loading(
                    dcc.Graph(
                        id="metacritic-compare-chart",
                        config={"displayModeBar": False},
                    ),
                    type="circle",
                ),
            ], width=6),
            dbc.Col([
                html.H5("3D Adoption by Platform Over Time", className="mb-2"),
                dcc.Loading(
                    dcc.Graph(
                        id="adoption-timeline-chart",
                        config={"displayModeBar": False},
                    ),
                    type="circle",
                ),
            ], width=6),
        ], className="mb-5"),

        # Sentiment section
        html.Hr(),
        html.H4("Community Sentiment via Steam Reviews", className="mt-4 mb-1"),
        html.P(
            "Select games from the list below (populated after fetching data), "
            "then run the sentiment fetch. Reviews are sourced from Steam — "
            "no API key required.",
            className="text-muted small mb-3",
        ),
        dbc.Row([
            dbc.Col([
                dbc.Label("Games to Analyze"),
                dcc.Dropdown(
                    id="sentiment-game-select",
                    multi=True,
                    placeholder="Fetch game data first, then select games here…",
                ),
            ], width=7),
            dbc.Col([
                dbc.Label("Filter by Release Year"),
                dcc.RangeSlider(
                    id="sentiment-year-slider",
                    min=1994, max=2000, step=1,
                    value=[1994, 2000],
                    marks={y: str(y) for y in range(1994, 2001)},
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
            ], width=5, className="align-self-end pb-2"),
        ], className="mb-3"),

        dbc.Row(dbc.Col([
            dbc.Button(
                "Fetch Steam Sentiment", id="fetch-sentiment-btn",
                color="secondary", className="me-3",
            ),
            html.Span(id="fetch-sentiment-status", className="text-muted small align-middle"),
        ])),

        dcc.Loading(
            dcc.Graph(
                id="sentiment-chart",
                className="mt-4",
                config={"displayModeBar": False},
            ),
            type="circle",
        ),

    ], fluid=True, className="page-container py-4")


# ── Callbacks ─────────────────────────────────────────────────────────────────

def register_callbacks(app):

    # ── 1. Fetch RAWG game data ──────────────────────────────────────────────
    @app.callback(
        Output("gaming-rawg-store", "data"),
        Output("fetch-games-status", "children"),
        Output("sentiment-game-select", "options"),
        Input("fetch-games-btn", "n_clicks"),
        State("rawg-key", "value"),
        prevent_initial_call=True,
    )
    def fetch_rawg(_, api_key):
        if not api_key:
            return None, "Enter a RAWG API key first.", []
        df = fetch_rawg_games(api_key)
        if df.empty:
            return None, "No data returned — check your API key.", []
        options = [{"label": n, "value": n} for n in sorted(df["name"].unique())]
        msg = f"✓ Loaded {len(df)} games."
        return df.to_json(orient="records", date_format="iso"), msg, options

    # ── 2. Update Metacritic + adoption charts ───────────────────────────────
    @app.callback(
        Output("metacritic-compare-chart", "figure"),
        Output("adoption-timeline-chart", "figure"),
        Input("gaming-rawg-store", "data"),
        Input("platform-filter", "value"),
    )
    def update_main_charts(json_data, selected_platforms):
        waiting = _empty_fig("Fetch game data to see this chart")
        if not json_data or not selected_platforms:
            return waiting, waiting

        df = pd.read_json(StringIO(json_data), orient="records")

        # Filter rows to games available on at least one selected platform
        def on_selected_platform(plats):
            if not isinstance(plats, list):
                return False
            return any(sel in plat for sel in selected_platforms for plat in plats)

        df = df[df["platforms"].apply(on_selected_platform)]

        # ── Chart 1: 2D vs 3D Metacritic box plot ───────────────────────────
        df_known = df[df["dimension"].isin(["2D", "3D"])].copy()
        if df_known.empty:
            fig_meta = _empty_fig("No 2D/3D classification data for selected platforms")
        else:
            unknown_count = (df["dimension"] == "Unknown").sum()
            fig_meta = px.box(
                df_known,
                x="dimension",
                y="metacritic",
                color="dimension",
                color_discrete_map={"2D": "#3498db", "3D": "#e74c3c"},
                labels={"dimension": "Game Type", "metacritic": "Metacritic Score"},
                hover_data=["name", "year"],
                points="all",
            )
            fig_meta.update_layout(
                showlegend=False,
                plot_bgcolor="#ffffff",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(range=[40, 100], title="Metacritic Score"),
                xaxis_title="",
                margin=dict(t=10, b=10),
            )
            if unknown_count:
                fig_meta.add_annotation(
                    text=f"({unknown_count} games couldn't be classified as 2D/3D and are excluded)",
                    xref="paper", yref="paper", x=0.5, y=-0.08,
                    showarrow=False, font={"size": 10, "color": "#aaa"},
                )

        # ── Chart 2: % 3D releases per platform per year ─────────────────────
        records = []
        for _, row in df.iterrows():
            plats = row["platforms"] if isinstance(row["platforms"], list) else []
            for plat in plats:
                if any(sel in plat for sel in selected_platforms):
                    records.append({
                        "year": row.get("year"),
                        "platform": plat,
                        "dimension": row.get("dimension"),
                    })

        df_exp = pd.DataFrame(records).dropna(subset=["year"])
        if df_exp.empty:
            fig_adopt = _empty_fig("No platform data for selected filters")
        else:
            df_exp["year"] = df_exp["year"].astype(int)
            totals = df_exp.groupby(["year", "platform"]).size().reset_index(name="total")
            threes = (
                df_exp[df_exp["dimension"] == "3D"]
                .groupby(["year", "platform"])
                .size()
                .reset_index(name="count_3d")
            )
            adopt = totals.merge(threes, on=["year", "platform"], how="left").fillna(0)
            adopt["pct_3d"] = (adopt["count_3d"] / adopt["total"] * 100).round(1)

            fig_adopt = px.line(
                adopt,
                x="year",
                y="pct_3d",
                color="platform",
                markers=True,
                labels={
                    "pct_3d": "% of Releases That Are 3D",
                    "year": "Year",
                    "platform": "Platform",
                },
                hover_data={"count_3d": True, "total": True},
            )
            fig_adopt.update_layout(
                plot_bgcolor="#ffffff",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(range=[0, 105], ticksuffix="%"),
                xaxis=dict(dtick=1, title="Year"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(t=40, b=10),
            )

        return fig_meta, fig_adopt

    # ── 3. Fetch Steam sentiment ─────────────────────────────────────────────
    @app.callback(
        Output("gaming-sentiment-store", "data"),
        Output("fetch-sentiment-status", "children"),
        Input("fetch-sentiment-btn", "n_clicks"),
        State("sentiment-game-select", "value"),
        State("gaming-rawg-store", "data"),
        prevent_initial_call=True,
    )
    def fetch_sentiment(_, selected_games, rawg_json):
        if not selected_games:
            return None, "⚠ Select at least one game first."

        # Apply release-year filter so only games in the slider range are fetched
        if rawg_json:
            df_rawg = pd.read_json(StringIO(rawg_json), orient="records")
            valid = set(df_rawg["name"].unique())
            selected_games = [g for g in selected_games if g in valid]

        if not selected_games:
            return None, "⚠ No valid games after filtering."

        df = fetch_game_sentiments(selected_games)
        if df.empty:
            return None, "No Steam reviews found for selected games."

        msg = f"✓ Analyzed {len(df)} reviews across {df['game'].nunique()} game(s)."
        return df.to_json(orient="records", date_format="iso"), msg

    # ── 4. Update sentiment chart ────────────────────────────────────────────
    @app.callback(
        Output("sentiment-chart", "figure"),
        Input("gaming-sentiment-store", "data"),
        Input("sentiment-game-select", "value"),
        Input("sentiment-year-slider", "value"),
        Input("gaming-rawg-store", "data"),
    )
    def update_sentiment_chart(sentiment_json, selected_games, year_range, rawg_json):
        waiting = _empty_fig("Select games and fetch Steam sentiment to see this chart")
        if not sentiment_json:
            return waiting

        df = pd.read_json(StringIO(sentiment_json), orient="records")

        # Filter to games whose RAWG release year is within the slider range
        if rawg_json and year_range:
            df_rawg = pd.read_json(StringIO(rawg_json), orient="records")
            in_range = df_rawg[
                df_rawg["year"].between(year_range[0], year_range[1])
            ]["name"].unique()
            df = df[df["game"].isin(in_range)]

        if selected_games:
            df = df[df["game"].isin(selected_games)]

        if df.empty:
            return _empty_fig("No sentiment data for the current filters")

        # Aggregate to one row per game
        agg = (
            df.groupby("game")
            .agg(
                avg_sentiment=("compound", "mean"),
                review_count=("compound", "count"),
                pct_positive=("voted_up", lambda x: round(x.mean() * 100, 1)),
            )
            .reset_index()
            .sort_values("avg_sentiment")
        )

        # Join Metacritic for tooltip context
        if rawg_json:
            df_rawg = pd.read_json(StringIO(rawg_json), orient="records")
            meta_map = df_rawg.drop_duplicates("name").set_index("name")["metacritic"]
            agg["metacritic"] = agg["game"].map(meta_map)

        agg["bar_color"] = agg["avg_sentiment"].apply(
            lambda s: "#27ae60" if s >= 0.05 else ("#e74c3c" if s <= -0.05 else "#f39c12")
        )
        agg["hover"] = agg.apply(
            lambda r: (
                f"Reviews analyzed: {r['review_count']}<br>"
                f"Steam thumbs-up: {r.get('pct_positive', '?')}%<br>"
                f"Metacritic: {int(r['metacritic']) if pd.notna(r.get('metacritic')) else 'N/A'}"
            ),
            axis=1,
        )

        fig = go.Figure(go.Bar(
            x=agg["avg_sentiment"].round(3),
            y=agg["game"],
            orientation="h",
            marker_color=agg["bar_color"],
            hovertext=agg["hover"],
            hoverinfo="text+x",
            text=agg["avg_sentiment"].round(2),
            textposition="outside",
        ))
        fig.add_vline(x=0, line_width=1, line_dash="dot", line_color="#777")
        fig.update_layout(
            xaxis=dict(
                title="Avg. VADER Compound Score  (−1 = Very Negative → +1 = Very Positive)",
                range=[-1, 1],
                zeroline=False,
            ),
            yaxis_title="",
            plot_bgcolor="#ffffff",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=60, t=20, b=40),
            height=max(300, len(agg) * 45),
        )
        return fig
