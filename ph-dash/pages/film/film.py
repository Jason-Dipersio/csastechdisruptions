import pandas as pd
from io import StringIO
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

from .film_data.tmdb_fetcher import fetch_cgi_movies, fetch_tmdb_reviews


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

def layout():
    return dbc.Container([
        dcc.Store(id="film-tmdb-store"),
        dcc.Store(id="film-sentiment-store"),

        # Header
        dbc.Row(dbc.Col([
            dcc.Link("← Back to Hub", href="/", className="back-link"),
            html.H1("CGI in Film: Rise & Public Perception", className="mt-3 mb-1"),
            html.P(
                "Tracking the growth of computer-generated imagery in cinema (1993–2026) "
                "and how audiences on Letterboxd responded to these films over time.",
                className="text-muted mb-4",
            ),
        ])),

        # API setup down here
        dbc.Accordion([
            dbc.AccordionItem([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("TMDB API Key"),
                        dbc.Input(
                            id="tmdb-key",
                            type="password",
                            placeholder="Paste your TMDB API key (v3 auth) here",
                        ),
                    ], width=5),
                ], className="mb-3"),
                dbc.Button(
                    "Fetch CGI Movie Data", id="fetch-tmdb-btn",
                    color="primary", className="me-2",
                ),
                html.Span(id="fetch-tmdb-status", className="text-muted small align-middle"),
            ], title="API Configuration"),
        ], start_collapsed=False, className="mb-4"),

        html.H4("CGI Prevalence in Cinema", className="mb-1"),
        html.P(
            "Movies tagged with CGI-related keywords on TMDB, filtered to titles with "
            "at least 50 audience votes. Volume (left) indicates how many notable CGI "
            "films were released each year; average rating (right) tracks overall reception.",
            className="text-muted small mb-3",
        ),

        dbc.Row([
            dbc.Col([
                html.H5("Notable CGI Films per Year", className="mb-2"),
                dcc.Loading(
                    dcc.Graph(
                        id="cgi-volume-chart",
                        config={"displayModeBar": False},
                    ),
                    type="circle",
                ),
            ], width=6),
            dbc.Col([
                html.H5("Average TMDB Rating of CGI Films", className="mb-2"),
                dcc.Loading(
                    dcc.Graph(
                        id="cgi-rating-chart",
                        config={"displayModeBar": False},
                    ),
                    type="circle",
                ),
            ], width=6),
        ], className="mb-5"),

        # Sentiment 
        html.Hr(),
        html.H4("Audience Sentiment", className="mt-4 mb-1"),
        html.P(
            "Select detected notable CGI films from the list below after running the API, "
            "then fetch their TMDB member reviews. VADER sentiment scores range from "
            "−1 (very negative) to +1 (very positive). ",
            className="text-muted small mb-3",
        ),

        dbc.Row([
            dbc.Col([
                dbc.Label("Films to Analyze"),
                dcc.Dropdown(
                    id="film-movie-select",
                    multi=True,
                    placeholder="Fetch TMDB data first, then select films here…",
                ),
            ], width=7),
            dbc.Col([
                dbc.Label("Filter by Release Year"),
                dcc.RangeSlider(
                    id="film-year-slider",
                    min=1993, max=2026, step=1,
                    value=[1993, 2026],
                    marks={y: str(y) for y in range(1993, 2027, 5)},
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
            ], width=5, className="align-self-end pb-2"),
        ], className="mb-3"),

        dbc.Row(dbc.Col([
            dbc.Button(
                "Fetch TMDB Reviews", id="fetch-sentiment-film-btn",
                color="secondary", className="me-3",
            ),
            html.Span(id="fetch-sentiment-film-status", className="text-muted small align-middle"),
        ])),

        dcc.Loading(
            dcc.Graph(
                id="film-sentiment-chart",
                className="mt-4",
                config={"displayModeBar": False},
            ),
            type="circle",
        ),

        dcc.Loading(
            dcc.Graph(
                id="film-stars-chart",
                className="mt-3",
                config={"displayModeBar": False},
            ),
            type="circle",
        ),

    ], fluid=True, className="page-container py-4")

# Callback section

def register_callbacks(app):

# Fetch TMDB CGI movie data 
    @app.callback(
        Output("film-tmdb-store", "data"),
        Output("fetch-tmdb-status", "children"),
        Output("film-movie-select", "options"),
        Input("fetch-tmdb-btn", "n_clicks"),
        State("tmdb-key", "value"),
        prevent_initial_call=True,
    )

    def fetch_tmdb(_, api_key):
        if not api_key:
            return None, "Please enter a TMDB API key first.", []
        df = fetch_cgi_movies(api_key)
        if df.empty:
            return None, "No data found. Please check your API key or try again.", []
        options = [
            {"label": f"{row['title']} ({int(row['year'])})", "value": row["title"]}
            for _, row in df.sort_values(["year", "title"]).iterrows()
        ]
        msg = f"Loaded {len(df)} CGI-tagged films across {df['year'].nunique()} years."
        return df.to_json(orient="records", date_format="iso"), msg, options

# Major CGI volume/use chart
    @app.callback(
        Output("cgi-volume-chart", "figure"),
        Output("cgi-rating-chart", "figure"),
        Input("film-tmdb-store", "data"),
    )
    def update_cgi_charts(json_data):
        waiting = _empty_fig("Please fetch CGI movie data first to see this chart")
        if not json_data:
            return waiting, waiting

        df = pd.read_json(StringIO(json_data), orient="records")
        df["year"] = df["year"].astype(int)

        by_year = (
            df.groupby("year")
            .agg(count=("id", "count"), avg_rating=("vote_average", "mean"))
            .reset_index()
        )

        # Volume bar chart
        fig_vol = go.Figure(go.Bar(
            x=by_year["year"],
            y=by_year["count"],
            marker_color="#3498db",
            hovertemplate="<b>%{x}</b><br>Films: %{y}<extra></extra>",
        ))
        fig_vol.update_layout(
            plot_bgcolor="#ffffff",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="Year", dtick=3),
            yaxis=dict(title="Number of Films"),
            margin=dict(t=10, b=10),
        )

        # Average review score line chart
        fig_rat = go.Figure(go.Scatter(
            x=by_year["year"],
            y=by_year["avg_rating"].round(2),
            mode="lines+markers",
            line=dict(color="#e74c3c", width=2),
            marker=dict(size=6),
            hovertemplate="<b>%{x}</b><br>Avg Rating: %{y:.2f}<extra></extra>",
        ))
        fig_rat.update_layout(
            plot_bgcolor="#ffffff",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="Year", dtick=3),
            yaxis=dict(title="Avg TMDB Rating", range=[4, 10]),
            margin=dict(t=10, b=10),
        )

        return fig_vol, fig_rat

#Fetch TMDB reviews
    @app.callback(
        Output("film-sentiment-store", "data"),
        Output("fetch-sentiment-film-status", "children"),
        Input("fetch-sentiment-film-btn", "n_clicks"),
        State("film-movie-select", "value"),
        State("film-tmdb-store", "data"),
        State("tmdb-key", "value"),
        prevent_initial_call=True,
    )
    def fetch_sentiment(_, selected_titles, tmdb_json, api_key):
        if not selected_titles:
            return None, "Please select at least one film first."
        if not api_key:
            return None, "Please enter your TMDB API key above."
        if not tmdb_json:
            return None, "Please fetch CGI movie data first."

        df_tmdb = pd.read_json(StringIO(tmdb_json), orient="records")
        pairs = []
        for title in selected_titles:
            row = df_tmdb[df_tmdb["title"] == title]
            if not row.empty:
                pairs.append((title, int(row.iloc[0]["id"]), int(row.iloc[0]["year"])))

        if not pairs:
            return None, "Could not match selected titles to TMDB IDs."

        df = fetch_tmdb_reviews(api_key, pairs)
        if df.empty:
            return None, "No reviews found for the selected films."
        msg = f"Analyzed {len(df)} reviews across {df['title'].nunique()} film(s)."
        return df.to_json(orient="records", date_format="iso"), msg

    # Sentiment analysis charts
    @app.callback(
        Output("film-sentiment-chart", "figure"),
        Output("film-stars-chart", "figure"),
        Input("film-sentiment-store", "data"),
        Input("film-movie-select", "value"),
        Input("film-year-slider", "value"),
        Input("film-tmdb-store", "data"),
    )
    def update_sentiment_charts(sentiment_json, selected_titles, year_range, tmdb_json):
        waiting = _empty_fig("Please select films and fetch TMDB reviews to see this chart")
        if not sentiment_json:
            return waiting, waiting

        df = pd.read_json(StringIO(sentiment_json), orient="records")

        # Apply year filter using TMDB release year
        if tmdb_json and year_range:
            df_tmdb = pd.read_json(StringIO(tmdb_json), orient="records")
            in_range = df_tmdb[
                df_tmdb["year"].between(year_range[0], year_range[1])
            ]["title"].unique()
            df = df[df["title"].isin(in_range)]

        if selected_titles:
            df = df[df["title"].isin(selected_titles)]

        if df.empty:
            return (
                _empty_fig("No data for the current filters"),
                _empty_fig("No data for the current filters"),
            )

        # Aggregate per film
        agg = (
            df.groupby("title")
            .agg(
                avg_compound=("compound", "mean"),
                review_count=("compound", "count"),
                avg_tmdb_rating=("tmdb_rating", "mean"),
            )
            .reset_index()
            .sort_values("avg_compound")
        )

        agg["bar_color"] = agg["avg_compound"].apply(
            lambda s: "#27ae60" if s >= 0.05 else ("#e74c3c" if s <= -0.05 else "#f39c12")
        )
        agg["hover_text"] = agg.apply(
            lambda r: (
                f"Reviews: {r['review_count']}<br>"
                f"Avg TMDB rating: {r['avg_tmdb_rating']:.1f} / 10"
                if pd.notna(r["avg_tmdb_rating"])
                else f"Reviews: {r['review_count']}<br>Avg TMDB rating: N/A"
            ),
            axis=1,
        )

        # VADER sentiment bar chart
        fig_sent = go.Figure(go.Bar(
            x=agg["avg_compound"].round(3),
            y=agg["title"],
            orientation="h",
            marker_color=agg["bar_color"],
            hovertext=agg["hover_text"],
            hoverinfo="text+x",
            text=agg["avg_compound"].round(2),
            textposition="outside",
        ))
        fig_sent.add_vline(x=0, line_width=1, line_dash="dot", line_color="#777")
        fig_sent.update_layout(
            title="VADER Sentiment Score by Film",
            xaxis=dict(
                title="Avg VADER Compound Score  (−1 = Very Negative → +1 = Very Positive)",
                range=[-1, 1],
                zeroline=False,
            ),
            yaxis_title="",
            plot_bgcolor="#ffffff",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=70, t=40, b=40),
            height=max(300, len(agg) * 50),
        )

        # TMDB author rating bar chart
        agg_rated = agg[agg["avg_tmdb_rating"].notna()].sort_values("avg_tmdb_rating")
        if agg_rated.empty:
            fig_stars = _empty_fig("No numeric ratings attached to the fetched TMDB reviews")
        else:
            fig_stars = go.Figure(go.Bar(
                x=agg_rated["avg_tmdb_rating"].round(2),
                y=agg_rated["title"],
                orientation="h",
                marker_color="#9b59b6",
                hovertemplate="%{y}: %{x:.1f} / 10<extra></extra>",
                text=agg_rated["avg_tmdb_rating"].round(1),
                textposition="outside",
            ))
            fig_stars.update_layout(
                title="Average TMDB User Rating by Film",
                xaxis=dict(title="Avg Rating (out of 10)", range=[0, 11]),
                yaxis_title="",
                plot_bgcolor="#ffffff",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=70, t=40, b=40),
                height=max(300, len(agg_rated) * 50),
            )

        return fig_sent, fig_stars
