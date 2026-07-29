from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

DATA_PATH = Path(__file__).parent / "cgiRevenu.xlsx"

LINE_COLOR = "#2a78d6"
FILL_COLOR = "rgba(42, 120, 214, 0.1)"
GRID_COLOR = "#e1e0d9"


def load_cgi_revenue_df() -> pd.DataFrame:
    raw = pd.read_excel(DATA_PATH, sheet_name="Data", header=None)
    data = raw.iloc[:, 1:3].dropna()
    data.columns = ["year", "revenue_million"]
    data = data[pd.to_numeric(data["year"], errors="coerce").notna()]
    data["year"] = data["year"].astype(int)
    data["revenue_billion"] = data["revenue_million"].astype(float) / 1000
    return data[["year", "revenue_billion"]].sort_values("year").reset_index(drop=True)


def build_cgi_revenue_chart() -> go.Figure:
    df = load_cgi_revenue_df()

    fig = go.Figure(go.Scatter(
        x=df["year"],
        y=df["revenue_billion"],
        mode="lines+markers",
        line=dict(color=LINE_COLOR, width=2),
        marker=dict(size=8, color=LINE_COLOR, line=dict(width=2, color="#ffffff")),
        fill="tozeroy",
        fillcolor=FILL_COLOR,
        hovertemplate="<b>%{x}</b><br>$%{y:.2f}B<extra></extra>",
    ))

    last = df.iloc[-1]
    fig.add_annotation(
        x=last["year"], y=last["revenue_billion"],
        text=f"${last['revenue_billion']:.1f}B",
        showarrow=False, xanchor="left", xshift=10,
        font=dict(size=12, color="#0b0b0b"),
    )

    fig.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        xaxis=dict(
            title="Year", dtick=1,
            showgrid=False, zeroline=False,
            linecolor="#c3c2b7",
        ),
        yaxis=dict(
            title="Box Office Revenue ($B)",
            tickprefix="$", ticksuffix="B",
            gridcolor=GRID_COLOR, zeroline=False,
        ),
        margin=dict(t=20, b=10, l=10, r=60),
    )
    return fig
