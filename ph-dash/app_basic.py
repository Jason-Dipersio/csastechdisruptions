import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

from pages import gaming

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.LITERA],
    suppress_callback_exceptions=True,
)

server = app.server

# Register callbacks for each page module
gaming.register_callbacks(app)


# ── Hub (landing) page ────────────────────────────────────────────────────────

hub_layout = html.Div([
    html.H1("Technological Disruptions", className="hub-title"),
    html.P(
        "Explore how major technological shifts transformed the Music, Gaming, and Film "
        "industries — and how AI continues to reshape them all today.",
        className="hub-subtitle",
    ),

    html.Div([
        dcc.Link(html.Div("Music",  className="topic-card"), href="/music",  className="topic-link"),
        dcc.Link(html.Div("Gaming", className="topic-card"), href="/gaming", className="topic-link"),
        dcc.Link(html.Div("Film",   className="topic-card"), href="/film",   className="topic-link"),
    ], className="topic-row"),

    dcc.Link(html.Div("AI", className="ai-card"), href="/ai", className="ai-link"),

], className="hub-container")


# ── Placeholder sub-pages ─────────────────────────────────────────────────────

def placeholder_page(title):
    return html.Div([
        html.H1(title),
        html.P("Charts and analysis coming soon."),
        dcc.Link("← Back to Hub", href="/", className="back-link"),
    ], className="page-container")

music_layout = placeholder_page("Music Industry Disruptions")
film_layout  = placeholder_page("Film Industry Disruptions")
ai_layout    = placeholder_page("How AI Affects These Industries")


# ── App shell ─────────────────────────────────────────────────────────────────

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content"),
])


@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/music":
        return music_layout
    if pathname == "/gaming":
        return gaming.layout()
    if pathname == "/film":
        return film_layout
    if pathname == "/ai":
        return ai_layout
    return hub_layout


if __name__ == "__main__":
    app.run(debug=True)
