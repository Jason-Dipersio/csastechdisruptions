import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

from pages.film import film
from pages.music import music
# We'll import the other pages here in the page directory when they're ready if you want.

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.LITERA],
    suppress_callback_exceptions=True,
)

server = app.server

# Register callbacks
film.register_callbacks(app)
music.register_callbacks(app)


# Home page
# We can change this stuff later if you want, it's just placeholders
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

# Placeholder page for those that aren't done yet
def placeholder_page(title):
    return html.Div([
        html.H1(title),
        html.P("Nothing yet"),
        dcc.Link("← Back to Hub", href="/", className="back-link"),
    ], className="page-container")

gaming_layout = placeholder_page("Gaming Industry Disruptions")
ai_layout    = placeholder_page("How AI Affects These Industries")

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content"),
])

@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/music":
        return music.layout()
    if pathname == "/gaming":
        return gaming_layout # placeholder
    if pathname == "/film":
        return film.layout()
    if pathname == "/ai":
        return ai_layout # placeholder
    return hub_layout


if __name__ == "__main__":
    app.run(debug=True)
