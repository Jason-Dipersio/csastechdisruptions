from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

DATA_PATH = Path(__file__).parent / "userAiAcceptanceInFilm.xlsx"

COMFORTABLE_COLOR = "#2a78d6"
INDIFFERENT_COLOR = "#898781"
NOT_COMFORTABLE_COLOR = "#e34948"
GRID_COLOR = "#e1e0d9"

COLUMNS = {
    "comfortable": "Comfortable with AI being used",
    "indifferent": "Indifferent",
    "not_comfortable": "Not comfortable with AI being used",
}


def load_ai_acceptance_df() -> pd.DataFrame:
    raw = pd.read_excel(DATA_PATH, sheet_name="Data", header=None)
    data = raw.iloc[:, 1:5].dropna(how="all")
    data.columns = ["aspect", "comfortable", "indifferent", "not_comfortable"]
    data = data[pd.to_numeric(data["comfortable"], errors="coerce").notna()]
    for col in ("comfortable", "indifferent", "not_comfortable"):
        data[col] = data[col].astype(float)
    return data.sort_values("comfortable").reset_index(drop=True)


def build_ai_acceptance_chart() -> go.Figure:
    df = load_ai_acceptance_df()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=COLUMNS["comfortable"],
        x=df["comfortable"], y=df["aspect"], orientation="h",
        marker_color=COMFORTABLE_COLOR,
        text=df["comfortable"].map(lambda v: f"{v:.0f}%"),
        textposition="inside", insidetextanchor="middle",
        textfont=dict(color="#ffffff"),
        hovertemplate="<b>%{y}</b><br>Comfortable: %{x:.0f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name=COLUMNS["indifferent"],
        x=df["indifferent"], y=df["aspect"], orientation="h",
        marker_color=INDIFFERENT_COLOR,
        text=df["indifferent"].map(lambda v: f"{v:.0f}%"),
        textposition="inside", insidetextanchor="middle",
        textfont=dict(color="#ffffff"),
        hovertemplate="<b>%{y}</b><br>Indifferent: %{x:.0f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name=COLUMNS["not_comfortable"],
        x=df["not_comfortable"], y=df["aspect"], orientation="h",
        marker_color=NOT_COMFORTABLE_COLOR,
        text=df["not_comfortable"].map(lambda v: f"{v:.0f}%"),
        textposition="inside", insidetextanchor="middle",
        textfont=dict(color="#ffffff"),
        hovertemplate="<b>%{y}</b><br>Not comfortable: %{x:.0f}%<extra></extra>",
    ))

    fig.update_layout(
        barmode="stack",
        plot_bgcolor="#ffffff",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            title="Share of Respondents",
            ticksuffix="%", range=[0, 100],
            gridcolor=GRID_COLOR, zeroline=False,
        ),
        yaxis=dict(title="", automargin=True),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            traceorder="normal",
        ),
        margin=dict(t=40, b=10, l=10, r=10),
        height=max(320, len(df) * 45),
    )
    return fig
