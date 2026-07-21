import os

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import html, dcc
import dash_bootstrap_components as dbc

# ── Placeholder data ──────────────────────────────────────────────────────
# Easy to swap out later for real Google Trends / Guardian API results —
# just replace the values below, the layout and charts don't need to change.
#
# The AI Applications and Challenges ratings below are qualitative literature-
# analysis judgments (how strongly a theme appears across the three reviewed
# sources), NOT measured statistics, survey results, or percentages.

# Small shared palette so KPI accents, chart series, and the timeline all
# read as one page instead of unrelated colors.
PRIMARY_DARK = "#0a3d62"
SERIES_BLUE = "#2a78d6"
SERIES_ORANGE = "#eb6834"

CATEGORY_ORDER = ["Low", "Moderate", "High", "Very High"]
CATEGORY_RANK = {name: i + 1 for i, name in enumerate(CATEGORY_ORDER)}

AI_APPLICATIONS = [
    ("Generative AI", "Very High"),
    ("Procedural Content Generation", "High"),
    ("AI-Assisted Game Design", "High"),
    ("Machine Learning", "Moderate"),
    ("NPC Behavior", "Moderate"),
    ("Player Modeling", "Low"),
]

AI_APPLICATIONS_GLOSSARY = [
    ("NPC Behavior", "AI controls how non-player characters react and make decisions."),
    ("Procedural Content Generation", "Algorithms automatically create levels, maps, items, or worlds."),
    ("Player Modeling", "Systems estimate player preferences, skill, or behavior."),
    ("Machine Learning", "Models learn patterns from game or player data."),
    ("AI-Assisted Game Design", "AI helps developers generate, evaluate, or improve design ideas."),
    ("Generative AI", "Models create dialogue, images, code, audio, or other game assets."),
]

CURRENT_CHALLENGES = [
    ("Copyright and Ownership", "Very High"),
    ("Limited or Proprietary Data", "High"),
    ("Human Creativity and Employment", "High"),
    ("Playability and Balance", "Moderate"),
    ("Coordinating Game Systems", "Moderate"),
]

CHALLENGES_GLOSSARY = [
    ("Playability and Balance", "Generated content may be impossible, unfair, or not enjoyable."),
    ("Limited or Proprietary Data", "Game datasets are smaller and less standardized than text or image datasets."),
    ("Copyright and Ownership", "Training data and generated assets may create legal questions."),
    ("Human Creativity and Employment", "AI may change the work of artists, writers, designers, and programmers."),
    ("Coordinating Game Systems", "AI-generated visuals, rules, narrative, and sound may not form one coherent game."),
]

TIMELINE_STEPS = [
    ("1980s – early 1990s", "Dominance of 2D gaming"),
    ("Mid-1990s", "Mainstream transition to real-time 3D graphics"),
    ("Late 1990s – 2000s", "Expansion of online multiplayer"),
    ("2010s", "Growth of machine learning and player modeling"),
    ("2020s", "Rise of generative AI in game development"),
]

# Topic | Current Coverage | Main Source Support | Additional Research Needed
LITERATURE_COVERAGE = [
    ("AI in Games", "High", "Artificial Intelligence and Games", "More recent industry adoption data"),
    ("Procedural Content Generation", "High", "PCG via Machine Learning", "Commercial case studies"),
    ("AI-Assisted Design", "High", "Artificial Intelligence for Designing Games", "Developer survey data"),
    ("Machine Learning", "Moderate", "AI and Games; PCGML", "More current generative AI research"),
    ("AI Ethics", "Moderate", "Artificial Intelligence and Games", "Copyright and labor research"),
    ("2D to 3D Transition", "Low", "Limited current source support", "Historical graphics sources"),
    ("Graphics Hardware", "Low", "Limited current source support", "GPU and rendering research"),
    ("Industry Impact", "Low", "Limited current source support", "Revenue, employment, and production data"),
]

COVERAGE_COLORS = {
    "High": "success",
    "Moderate": "warning",
    "Low": "danger",
}

SOURCES = [
    ("Artificial Intelligence and Games", "Georgios N. Yannakakis and Julian Togelius"),
    ("Procedural Content Generation via Machine Learning", "Adam Summerville et al."),
    ("Artificial Intelligence for Designing Games", "Antonio Liapis"),
]

# ── Real quantitative data ────────────────────────────────────────────────
# Unlike the literature-based ratings above, everything in this section is
# real, sourced, external data — not qualitative judgment.

# Google Trends has no official public API. Live scraping via the unofficial
# "pytrends" library is rate-limited (HTTP 429) from most cloud/shared IPs,
# which makes it unreliable to fetch live during a presentation. Instead this
# reads a CSV exported directly from trends.google.com. See the "How to add
# Google Trends data" instructions on the page for the exact export steps.
GOOGLE_TRENDS_CSV = os.path.join(os.path.dirname(__file__), "gaming_data", "google_trends.csv")

# The Guardian Open Platform API counts below ARE real API results (not
# invented), fetched with the public "test" API key on 2026-07-17. Fully
# paginated per query, so every number is a complete count, not a sample.
# Reproduce with: https://content.guardianapis.com/search?api-key=test&
#   from-date=2015-01-01&to-date=2026-07-17&order-by=newest&page-size=50
# plus the parameters below for each series (all restricted to section=games
# except "Procedural generation", which is rare/specific enough to search
# across all sections without picking up unrelated noise):
#   AI in gaming            -> q="artificial intelligence"      section=games
#   Video game AI           -> q=AI                             section=games
#   Procedural generation   -> q="procedural generation"        (no section filter)
#   Generative AI games     -> q="generative AI"                section=games
# 2026 is a partial year (data through July 17, 2026).
GUARDIAN_YEARS = list(range(2015, 2027))
GUARDIAN_COVERAGE = {
    "AI in gaming":          [14, 7, 7, 1, 3, 1, 4, 2, 8, 4, 4, 2],
    "Video game AI":         [54, 40, 29, 12, 20, 16, 20, 16, 30, 31, 44, 30],
    "Procedural generation": [3, 3, 2, 1, 0, 0, 1, 0, 1, 0, 1, 1],
    "Generative AI games":   [0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 8, 3],
}
# Categorical palette (CVD-safe ordering), reused for both real-data charts.
REAL_DATA_PALETTE = [SERIES_BLUE, "#1baf7a", "#eda100", "#4a3aa7", "#e34948"]


def _kpi_card(value, label):
    return dbc.Card(
        dbc.CardBody([
            html.H3(str(value), className="mb-1 fw-bold", style={"color": PRIMARY_DARK}),
            html.P(label, className="text-muted mb-0 small text-uppercase"),
        ]),
        className="text-center shadow-sm h-100",
    )


def _horizontal_bar(data, color):
    """Horizontal bar chart for qualitative (Low/Moderate/High/Very High) ratings.

    Bar length encodes rank order only — the axis and hover text always show
    the category label, never a number, so the chart can't be misread as a
    measured statistic.
    """
    labels = [d[0] for d in data]
    categories = [d[1] for d in data]
    values = [CATEGORY_RANK[c] for c in categories]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=color,
        text=categories,
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>",
    ))
    fig.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=110, t=10, b=10),
        xaxis=dict(
            title="Qualitative emphasis in reviewed literature",
            range=[0, len(CATEGORY_ORDER) + 0.5],
            tickmode="array",
            tickvals=list(CATEGORY_RANK.values()),
            ticktext=CATEGORY_ORDER,
        ),
        yaxis=dict(autorange="reversed"),
        height=max(280, len(data) * 55),
        font=dict(color="#0b0b0b"),
    )
    return fig


def _chart_note(text):
    return html.P(text, className="text-muted small fst-italic mt-2 mb-0")


def _section_badge(text, color):
    return dbc.Badge(text, color=color, className="ms-2 align-middle")


def _empty_trends_figure(message):
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(t=20, b=20),
        height=320,
        annotations=[{
            "text": message,
            "showarrow": False,
            "font": {"size": 13, "color": "#999"},
            "xref": "paper", "yref": "paper",
            "x": 0.5, "y": 0.5,
        }],
    )
    return fig


def _load_google_trends():
    """Read a Google Trends 'compare terms' CSV export, if one has been added.

    Returns a DataFrame with a date column and one numeric column per search
    term, or None if the file hasn't been placed at GOOGLE_TRENDS_CSV yet.
    """
    if not os.path.exists(GOOGLE_TRENDS_CSV):
        return None

    with open(GOOGLE_TRENDS_CSV, encoding="utf-8") as f:
        lines = f.readlines()

    header_idx = next(
        (i for i, line in enumerate(lines) if line.split(",")[0].strip() in ("Month", "Week", "Day")),
        None,
    )
    if header_idx is None:
        return None

    df = pd.read_csv(GOOGLE_TRENDS_CSV, skiprows=header_idx)
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])

    term_cols = list(df.columns[1:])
    for col in term_cols:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace("<1", "0", regex=False), errors="coerce"
        ).fillna(0)
    df = df.rename(columns={c: c.split(":")[0].strip() for c in term_cols})

    if df.empty:
        return None
    return df


def _google_trends_figure():
    df = _load_google_trends()
    if df is None:
        return _empty_trends_figure(
            "Awaiting Google Trends export — see \"How to add Google Trends data\" below"
        )

    date_col = df.columns[0]
    fig = go.Figure()
    for i, term in enumerate(df.columns[1:]):
        fig.add_trace(go.Scatter(
            x=df[date_col], y=df[term], mode="lines", name=term,
            line=dict(color=REAL_DATA_PALETTE[i % len(REAL_DATA_PALETTE)], width=2),
            hovertemplate=f"<b>{term}</b><br>%{{x|%b %Y}}: %{{y}}<extra></extra>",
        ))
    fig.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(title="Date"),
        yaxis=dict(title="Search interest (Google Trends index, 0-100)"),
        legend=dict(orientation="h", yanchor="top", y=-0.18),
        height=380,
        font=dict(color="#0b0b0b"),
    )
    return fig


def _guardian_coverage_figure():
    terms = list(GUARDIAN_COVERAGE.keys())
    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=terms,
        vertical_spacing=0.22,
        horizontal_spacing=0.08,
    )
    for (row, col), term, color in zip(positions, terms, REAL_DATA_PALETTE):
        fig.add_trace(
            go.Scatter(
                x=GUARDIAN_YEARS,
                y=GUARDIAN_COVERAGE[term],
                mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=5),
                showlegend=False,
                hovertemplate="%{x}: %{y} articles<extra></extra>",
            ),
            row=row, col=col,
        )
    fig.update_xaxes(dtick=3)
    fig.update_yaxes(rangemode="tozero")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        margin=dict(l=10, r=10, t=40, b=10),
        height=460,
        font=dict(color="#0b0b0b", size=11),
    )
    return fig


def _definition_list(items):
    """Compact term/definition list, reused for both the AI and challenges glossaries."""
    return dbc.ListGroup([
        dbc.ListGroupItem([
            html.Span(f"{term}: ", className="fw-bold"),
            html.Span(definition),
        ], className="small")
        for term, definition in items
    ], flush=True)


def _timeline():
    items = []
    for i, (era, description) in enumerate(TIMELINE_STEPS):
        items.append(
            html.Div([
                html.Div(era, className="fw-bold"),
                html.Div(description),
            ], className="gaming-timeline-node")
        )
        if i < len(TIMELINE_STEPS) - 1:
            items.append(html.Div("↓", className="gaming-timeline-arrow"))
    return html.Div(items, className="gaming-timeline")


def _coverage_table():
    header = html.Thead(html.Tr([
        html.Th("Topic"),
        html.Th("Current Coverage"),
        html.Th("Main Source Support"),
        html.Th("Additional Research Needed"),
    ]))
    rows = []
    for topic, coverage, main_source, research_needed in LITERATURE_COVERAGE:
        rows.append(html.Tr([
            html.Td(topic),
            html.Td(dbc.Badge(coverage, color=COVERAGE_COLORS.get(coverage, "secondary"), pill=True)),
            html.Td(main_source),
            html.Td(research_needed),
        ]))
    return dbc.Table(
        [header, html.Tbody(rows)],
        bordered=False,
        hover=True,
        responsive=True,
        className="align-middle",
    )


def _sources_list():
    return html.Ol([
        html.Li([
            html.Span(title, className="fw-bold"),
            html.Span(f" — {authors}", className="text-muted"),
        ])
        for title, authors in SOURCES
    ])


def layout():
    return dbc.Container([

        # Header
        dbc.Row(dbc.Col([
            dcc.Link("← Back to Hub", href="/", className="back-link"),
            html.H1("Gaming Technological Disruptions", className="mt-3 mb-1"),
            html.P(
                "The Evolution from 2D Graphics to AI-Assisted Game Development",
                className="text-muted mb-2",
            ),
            html.P(
                "Research suggests that AI is expanding across game design and production, "
                "while concerns about playability, creative control, data, and copyright "
                "remain unresolved.",
                className="text-muted mb-4",
            ),
        ])),

        # KPI cards
        dbc.Row([
            dbc.Col(_kpi_card(3, "Sources Reviewed"), width=6, md=3, className="mb-4"),
            dbc.Col(_kpi_card("AI in Games", "Primary Focus"), width=6, md=3, className="mb-4"),
            dbc.Col(_kpi_card(6, "Research Themes"), width=6, md=3, className="mb-4"),
            dbc.Col(_kpi_card(5, "Current Research Challenges"), width=6, md=3, className="mb-4"),
        ], className="mb-4"),

        html.Hr(),

        # Technology timeline (moved directly below the KPI cards)
        html.H4("Major Technology Shifts in Gaming", className="mb-1 mt-3"),
        _chart_note("This timeline provides historical context rather than measuring the number of games released."),
        dbc.Card(
            dbc.CardBody(_timeline()),
            className="shadow-sm mb-4 mt-2",
        ),

        html.Hr(),

        # Real-world evidence: public interest (Google Trends) and media
        # coverage (Guardian API) over time — quantitative, sourced data,
        # distinct from the literature-based ratings further down the page.
        html.H4([
            "Public Interest Over Time",
            _section_badge("Quantitative — Real Data", "primary"),
        ], className="mb-1 mt-3"),
        html.P(
            "Worldwide Google Trends search interest for AI-and-gaming-related terms.",
            className="text-muted small mb-3",
        ),
        dbc.Card(
            dbc.CardBody([
                dcc.Graph(
                    id="gaming-trends-chart",
                    figure=_google_trends_figure(),
                    config={"displayModeBar": False},
                ),
                _chart_note(
                    "Source: Google Trends (trends.google.com). Index is relative search "
                    "interest, 0-100, worldwide."
                ),
            ]),
            className="shadow-sm mb-2",
        ),
        dbc.Accordion([
            dbc.AccordionItem([
                html.P("Google Trends has no official API, so this chart reads a CSV you export yourself:", className="small mb-2"),
                html.Ol([
                    html.Li("Go to trends.google.com/trends/explore."),
                    html.Li(
                        "Add all 5 terms as a comparison: \"AI in gaming\", \"Generative AI\", "
                        "\"Procedural generation\", \"Machine learning games\", \"Video game AI\" "
                        "(Google Trends allows up to 5 terms per comparison)."
                    ),
                    html.Li("Set the date range (2015-present matches the Guardian chart below)."),
                    html.Li("On the \"Interest over time\" chart, click the download icon to get the CSV."),
                    html.Li(
                        html.Span([
                            "Save it as ",
                            html.Code("ph-dash/pages/gaming/gaming_data/google_trends.csv"),
                            " and reload the page.",
                        ])
                    ),
                ], className="small mb-0"),
            ], title="How to add Google Trends data"),
        ], start_collapsed=True, className="mb-4"),

        html.H4([
            "Media Coverage Over Time",
            _section_badge("Quantitative — Real Data", "primary"),
        ], className="mb-1 mt-3"),
        html.P(
            "Guardian articles matching each search term, by year (2015 – Jul 17, 2026; "
            "2026 is a partial year).",
            className="text-muted small mb-3",
        ),
        dbc.Card(
            dbc.CardBody([
                dcc.Graph(
                    id="gaming-guardian-chart",
                    figure=_guardian_coverage_figure(),
                    config={"displayModeBar": False},
                ),
                _chart_note(
                    "Source: The Guardian Open Platform API (content.guardianapis.com). Full, "
                    "non-sampled article counts for each query, fetched July 17, 2026. \"AI in "
                    "gaming\", \"Video game AI\", and \"Generative AI games\" are restricted to "
                    "the Games section; \"Procedural generation\" is specific enough to search "
                    "across all sections without adding unrelated noise."
                ),
            ]),
            className="shadow-sm mb-4",
        ),

        html.Hr(),

        # AI Applications & Current Challenges charts
        dbc.Row([
            dbc.Col([
                html.H4([
                    "AI Applications in Game Development",
                    _section_badge("Qualitative — Literature Review", "secondary"),
                ], className="mb-1"),
                html.P(
                    "Where AI techniques are being applied across the development pipeline.",
                    className="text-muted small mb-3",
                ),
                dbc.Card(
                    dbc.CardBody([
                        dcc.Graph(
                            id="gaming-ai-applications-chart",
                            figure=_horizontal_bar(AI_APPLICATIONS, SERIES_BLUE),
                            config={"displayModeBar": False},
                        ),
                        _chart_note(
                            "Qualitative summary of the reviewed literature, not measured data: "
                            "ratings reflect how strongly each theme appears across the three "
                            "reviewed sources, not survey or usage statistics."
                        ),
                    ]),
                    className="shadow-sm h-100",
                ),
                dbc.Card(
                    dbc.CardBody([
                        html.H6("Key Terms", className="mb-2"),
                        _definition_list(AI_APPLICATIONS_GLOSSARY),
                    ]),
                    className="shadow-sm mt-3",
                ),
            ], md=6, className="mb-4"),
            dbc.Col([
                html.H4([
                    "Current Research Challenges",
                    _section_badge("Qualitative — Literature Review", "secondary"),
                ], className="mb-1"),
                html.P(
                    "Open problems raised across the reviewed literature.",
                    className="text-muted small mb-3",
                ),
                dbc.Card(
                    dbc.CardBody([
                        dcc.Graph(
                            id="gaming-challenges-chart",
                            figure=_horizontal_bar(CURRENT_CHALLENGES, SERIES_ORANGE),
                            config={"displayModeBar": False},
                        ),
                        _chart_note(
                            "Qualitative summary of the reviewed literature, not measured data: "
                            "ratings reflect how strongly each theme appears across the three "
                            "reviewed sources, not survey or usage statistics."
                        ),
                    ]),
                    className="shadow-sm h-100",
                ),
                dbc.Card(
                    dbc.CardBody([
                        html.H6("Key Terms", className="mb-2"),
                        _definition_list(CHALLENGES_GLOSSARY),
                    ]),
                    className="shadow-sm mt-3",
                ),
            ], md=6, className="mb-4"),
        ]),

        html.Hr(),

        # Literature coverage table
        html.H4([
            "Literature Coverage",
            _section_badge("Qualitative — Literature Review", "secondary"),
        ], className="mb-1 mt-3"),
        html.P(
            "Depth of coverage found across reviewed sources, by topic.",
            className="text-muted small mb-3",
        ),
        dbc.Card(
            dbc.CardBody(_coverage_table()),
            className="shadow-sm mb-4",
        ),

        html.Hr(),

        # Sources reviewed
        html.H4("Sources Reviewed", className="mb-1 mt-3"),
        dbc.Card(
            dbc.CardBody([
                _sources_list(),
                html.P(
                    "This dashboard summarizes themes from the reviewed literature. It does not "
                    "claim that qualitative rankings represent industry-wide statistics.",
                    className="text-muted small fst-italic mt-2 mb-0",
                ),
            ]),
            className="shadow-sm mb-4",
        ),

        # Conclusion
        dbc.Card(
            dbc.CardBody([
                html.H5("Conclusion", className="mb-2"),
                html.P(
                    "The reviewed literature shows that AI can support game development through "
                    "content generation, player modeling, and design assistance. However, AI still "
                    "struggles with reliability, creative control, legal uncertainty, and coordination "
                    "across complete game systems. Additional historical and industry data is needed "
                    "to compare the rise of AI with the earlier transition from 2D to 3D gaming.",
                    className="mb-0",
                ),
            ]),
            className="shadow-sm mb-4 border-start border-4",
            style={"borderColor": f"{PRIMARY_DARK} !important"},
        ),

    ], fluid=True, className="page-container py-4")


def register_callbacks(app):
    # Reserved for future interactivity (e.g. filters once Google Trends /
    # Guardian API data replaces the placeholder values above).
    pass


# This block here is necessary to be able to run this file individually,
# without the app_tech_disruptions hub page.
if __name__ == "__main__":
    import os
    import dash

    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.LITERA],
        assets_folder=os.path.join(os.path.dirname(__file__), "..", "..", "assets"),
    )

    app.layout = layout()
    register_callbacks(app)
    app.run(debug=True)
