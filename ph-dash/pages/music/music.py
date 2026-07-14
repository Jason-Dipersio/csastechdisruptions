
# Install Dash and Dash Bootstrap Components
import requests
import pandas as pd
from io import StringIO
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objs as go
import matplotlib.pyplot as plt

DATA_DIR = Path("csastechdisruptions/ph-dash/pages/music/music_assets")

# set up dataframes

CD_YearlyCount = pd.read_csv(DATA_DIR / "CD_yearlycount.csv")
CD_YearlySent = pd.read_csv(DATA_DIR / "CD_yearlysent.csv")
LP_YearlyCount = pd.read_csv(DATA_DIR / "LP_yearlycount.csv")
LP_YearlySent = pd.read_csv(DATA_DIR / "LP_yearlysent.csv")
df = pd.read_csv(DATA_DIR / "musicdata.csv")

# Set up subframes for sales

cdFrame = df[(df['format'].isin(['CD', 'CD Single', 'SACD'])) & (df['metric'] == 'Value (Adjusted)')].groupby('year')['value_actual'].sum().reset_index()
vyFrame = df[(df['format'].isin(['LP/EP', 'Vinyl Single'])) & (df['metric'] == 'Value (Adjusted)')].groupby('year')['value_actual'].sum().reset_index()
dgFrame = df[(df['format'].isin(['Download Album', 'Other Digital', 'Download Music Video', 'Download Single', 'Ringtones & Ringbacks'])) & (df['metric'] == 'Value (Adjusted)')].groupby('year')['value_actual'].sum().reset_index()
stFrame = df[(df['format'].isin(['Limited Tier Paid Subscription', 'On-Demand Streaming (Ad-Supported)', 'Other Ad-Supported Streaming', 'Paid Subscription', 'Paid Subscriptions'])) & (df['metric'] == 'Value (Adjusted)')].groupby('year')['value_actual'].sum().reset_index()
cassFrame = df[(df['format'].isin(['8 - Track', 'Cassette', 'Cassette Single', 'Other Tapes'])) & (df['metric'] == 'Value (Adjusted)')].groupby('year')['value_actual'].sum().reset_index()
dvdFrame = df[(df['format'].isin(['DVD Audio', 'Music Video (Physical)'])) & (df['metric'] == 'Value (Adjusted)')].groupby('year')['value_actual'].sum().reset_index()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA])
server = app.server

# Set up all initial figures

sentcomp_fig = go.Figure(data=[go.Scatter(x=CD_YearlySent['year'], y=CD_YearlySent['sentiment_score'], mode='lines', name='CD'),
                             go.Scatter(x=LP_YearlySent['year'], y=LP_YearlySent['sentiment_score'], mode='lines', name='Vinyl')])
sentcomp_fig.update_layout(title='CD vs Vinyl Sentiment Score (1982-2019)',
                         xaxis_title='Year',
                         yaxis_title='Sentiment Score')


cd_vinyl_sales_fig = go.Figure(data=[go.Scatter(x=cdFrame['year'], y=cdFrame['value_actual'], mode='lines', name='CD'),
                              go.Scatter(x=vyFrame['year'], y=vyFrame['value_actual'], mode='lines', name='Vinyl')])
cd_vinyl_sales_fig.update_layout(title='CD Sales vs Vinyl Sales (1973-2019)',
                          xaxis_title='Year',
                          yaxis_title='Estimated Units (In Millions)')


cd_article_count_fig = go.Figure(data=[go.Bar(x=CD_YearlyCount['year'], y=CD_YearlyCount['count'], name='CD')])
cd_article_count_fig.update_layout(title='CD Article Count (NYT 1982-2019)',
                          xaxis_title='Year',
                          yaxis_title='Article Count')


cd_sent_fig = go.Figure(data=[go.Bar(x=CD_YearlyCount['year'], y=CD_YearlyCount['count'], name='Article Count', marker_color='royalblue', opacity=0.8, yaxis='y'),
                              go.Scatter(x=CD_YearlySent['year'], y=CD_YearlySent['sentiment_score'], mode='lines', name='Sentiment Score', marker_color='black', yaxis='y2')])
cd_sent_fig.update_layout(title='CD Article Count vs Sentiment Score (1973-2019)',
                          xaxis_title='Year',
                          yaxis=dict(title='Article Count'),
                          yaxis2=dict(title='Sentiment Score', side='right', overlaying='y'),
                          legend=dict(x=1.1, y=1))


cd_sales_sent_fig = go.Figure(data=[go.Scatter(x=cdFrame['year'], y=cdFrame['value_actual'], name='Units Sold (In Millions)', marker_color='royalblue', opacity=0.8, yaxis='y'),
                              go.Scatter(x=CD_YearlySent['year'], y=CD_YearlySent['sentiment_score'], mode='lines', name='Sentiment Score', marker_color='black', yaxis='y2')])
cd_sales_sent_fig.update_layout(title='CD Sales vs Sentiment Score (1973-2019)',
                          xaxis_title='Year',
                          yaxis=dict(title='Article Count'),
                          yaxis2=dict(title='Sentiment Score', side='right', overlaying='y'),
                          legend=dict(x=1.1, y=1))
# Set up app data
app.layout = dbc.Container(
    [
        dbc.Row([
            dbc.Col(html.H1("Music Data (The Compact Disc)"), className="text-center mt-3 mb-1")
        ]),
        dbc.Row([
            dbc.Col(html.P("This page displays data about the compact disc, viewing it as a technological disruption."), className="mt-3 mb-1")
        ]),
        dbc.Row([
            dbc.Col(html.Br())
        ]),
        dbc.Row([
            dbc.Col(html.H3("Sales Data"), className="mt-3 mb-1")
        ]),
        dbc.Row([
            dbc.Col(html.P("One of the easiest indicators to understanding the effect a new technology has on any landscape is sales data. Using the following charts below it is evident that the compact disc did have a major amount of influence in the space."))
        ]),
        dbc.Row([
            dbc.Col(html.Br())
        ]),
        dbc.Row([
            dbc.Col(html.Div([
              # The button that will trigger the switch
              html.Button('Switch Graph Complexity', id='btn-switch1', n_clicks=0),
              dcc.Store(id='graph-state1', data=True)
          ]))
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id='display-graph1', figure=cd_vinyl_sales_fig), width=12)
        ]),
        dbc.Row([
            dbc.Col(html.Br())
        ]),
        dbc.Row([
            dbc.Col(html.H3("Sentiment Analysis"), className="mt-3 mb-1")
        ]),
        dbc.Row([
            dbc.Col(html.P("By using sentiment analysis, we can roughly determine the level of positive or negative reception in a given source. By pulling articles fron the New York Times using its dedicated API, we can judge the relative feelings on a certain topic for a particular year."))
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=sentcomp_fig)) # Use the pre-defined static_fig here
        ]),
        dbc.Row([
            dbc.Col(html.Br())
        ]),
        dbc.Row([
            dbc.Col(html.H3("Article Count"), className="mt-3 mb-1")
        ]),
        dbc.Row([
            dbc.Col(html.P("By seeing the number of articles of a given topic, we can judge how big said topic is that year. Since each page of an API pull is, at most, ten articles, a cap of 100 articles per year is a solid cut off to determine how covered the topic is just in the NYT alone."))
        ]),
        dbc.Row([
            dbc.Col(html.Br())
        ]),
         dbc.Row([
            dbc.Col(html.Div([
              # The button that will trigger the switch
              html.Button('Switch Graph', id='btn-switch2', n_clicks=0),
              dcc.Store(id='graph-state2', data=True)
          ]))
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id='display-graph2', figure=cd_article_count_fig), width=12)
        ]),
        dbc.Row([
            dbc.Col(html.Br())
        ]),
        dbc.Row([
            dbc.Col(html.H3("Article Count vs Sentiment Score"), className="mt-3 mb-1")
        ]),
        dbc.Row([
            dbc.Col(html.P("Using comparison frames, we can see if there is any correlation between two bits of data. In these charts, we determine if there is anything to be gleamed from article count and sentiment score. Oddly enough the charts seem to show a negative correlation in CDs (The more articles, the less the sentiment score) and a positive one for vinyls (The more articles, the higher the sentiment score)."))
        ]),
        dbc.Row([
            dbc.Col(html.Br())
        ]),
        dbc.Row([
            dbc.Col(html.Div([
              # The button that will trigger the switch
              html.Button('Switch Graph', id='btn-switch3', n_clicks=0),
              dcc.Store(id='graph-state3', data=True)
          ]))
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id='display-graph3', figure=cd_sent_fig), width=12)
        ]),
        dbc.Row([
            dbc.Col(html.Br())
        ]),
        dbc.Row([
            dbc.Col(html.H3("Sales vs Sentiment Score"), className="mt-3 mb-1")
        ]),
        dbc.Row([
            dbc.Col(html.P("This combination graph examines the relationship between sales and sentiment. For CDs, there seems to be a slight positive correlation, signified by the center of the graph following a similar trend but not the rest. For vinyl, there appears to be little to no correlation."))
        ]),
        dbc.Row([
            dbc.Col(html.Br())
        ]),
        dbc.Row([
            dbc.Col(html.Div([
              # The button that will trigger the switch
              html.Button('Switch Graph', id='btn-switch4', n_clicks=0),
              dcc.Store(id='graph-state4', data=True)
          ]))
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id='display-graph4', figure=cd_sales_sent_fig), width=12)
        ]),
        dbc.Row([
            dbc.Col(html.Br())
        ]),
    ]
)

# GRAPH SWITCHING BUTTON 1
# Callback to update state and graph upon clicking
@app.callback(
    [Output('display-graph1', 'figure'),
     Output('graph-state1', 'data')],
    [Input('btn-switch1', 'n_clicks')],
    [State('graph-state1', 'data')]
)
def switch_graph1(n_clicks, current_state):
    # Default to Graph 1 if button hasn't been clicked or state is True
    if n_clicks == 0 or current_state:
        # Generate Graph 1
        fig = go.Figure(data=[go.Scatter(x=cdFrame['year'], y=cdFrame['value_actual'], mode='lines', name='CD'),
                              go.Scatter(x=vyFrame['year'], y=vyFrame['value_actual'], mode='lines', name='Vinyl')])
        fig.update_layout(title='CD Sales vs Vinyl Sales (1973-2019)',
                          xaxis_title='Year',
                          yaxis_title='Estimated Units (In Millions)')
        new_state = False # Next click will show Graph 2
    else:
        # Generate Graph 2
        fig = go.Figure(data=[go.Scatter(x=cdFrame['year'], y=cdFrame['value_actual'], mode='lines', name='CD'),
                              go.Scatter(x=vyFrame['year'], y=vyFrame['value_actual'], mode='lines', name='Vinyl'),
                              go.Scatter(x=dgFrame['year'], y=dgFrame['value_actual'], mode= 'lines', name='Digital'),
                              go.Scatter(x=stFrame['year'], y=stFrame['value_actual'], mode= 'lines', name='Streaming'),
                              go.Scatter(x=cassFrame['year'], y=cassFrame['value_actual'], mode= 'lines', name='Cassette'),
                              go.Scatter(x=dvdFrame['year'], y=dvdFrame['value_actual'], mode= 'lines', name='DVD'),])
        fig.update_layout(title= 'Music Medium Sales (1973-2019)',
                          xaxis_title='Year',
                          yaxis_title='Estimated Units (In Millions)')
        new_state = True  # Next click will show Graph 1

    return fig, new_state

# GRAPH SWITCHING BUTTON 2
# Callback to update state and graph upon clicking
@app.callback(
    [Output('display-graph2', 'figure'),
     Output('graph-state2', 'data')],
    [Input('btn-switch2', 'n_clicks')],
    [State('graph-state2', 'data')]
)
def switch_graph2(n_clicks, current_state):
    # Default to Graph 1 if button hasn't been clicked or state is True
    if n_clicks == 0 or current_state:
        # Generate Graph 1
        fig = go.Figure(data=[go.Bar(x=CD_YearlyCount['year'], y=CD_YearlyCount['count'], name='CD')])
        fig.update_layout(title='CD Article Count (NYT 1982-2019)',
                          xaxis_title='Year',
                          yaxis_title='Article Count')
        new_state = False # Next click will show Graph 2
    else:
        # Generate Graph 2
        fig = go.Figure(data=[go.Bar(x=LP_YearlyCount['year'], y=LP_YearlyCount['count'], name='Vinyl', marker_color='red')])
        fig.update_layout(title= 'Vinyl Article Count (NYT 1982-2019)',
                          xaxis_title='Year',
                          yaxis_title='Article Count')
        new_state = True  # Next click will show Graph 1

    return fig, new_state

# GRAPH SWITCHING BUTTON 3
# Callback to update state and graph upon clicking
@app.callback(
    [Output('display-graph3', 'figure'),
     Output('graph-state3', 'data')],
    [Input('btn-switch3', 'n_clicks')],
    [State('graph-state3', 'data')]
)
def switch_graph3(n_clicks, current_state):
    # Default to Graph 1 if button hasn't been clicked or state is True
    if n_clicks == 0 or current_state:
        # Generate Graph 1
        fig = go.Figure(data=[go.Bar(x=CD_YearlyCount['year'], y=CD_YearlyCount['count'], name='Article Count', marker_color='royalblue', opacity=0.8, yaxis='y'),
                              go.Scatter(x=CD_YearlySent['year'], y=CD_YearlySent['sentiment_score'], mode='lines', name='Sentiment Score', marker_color='black', yaxis='y2')])
        fig.update_layout(title='CD Article Count vs Sentiment Score (1973-2019)',
                          xaxis_title='Year',
                          yaxis=dict(title='Article Count'),
                          yaxis2=dict(title='Sentiment Score', side='right', overlaying='y'),
                          legend=dict(x=1.1, y=1))
        new_state = False # Next click will show Graph 2
    else:
        # Generate Graph 2
        fig = go.Figure(data=[go.Bar(x=LP_YearlyCount['year'], y=LP_YearlyCount['count'], name='Article Count', marker_color='red', opacity=0.8, yaxis='y'),
                              go.Scatter(x=LP_YearlySent['year'], y=LP_YearlySent['sentiment_score'], mode='lines', name='Sentiment Score', marker_color='black', yaxis='y2')])
        fig.update_layout(title='Vinyl Article Count vs Sentiment Score (1973-2019)',
                          xaxis_title='Year',
                          yaxis=dict(title='Article Count'),
                          yaxis2=dict(title='Sentiment Score', side='right', overlaying='y'),
                          legend=dict(x=1.1, y=1))
        new_state = True  # Next click will show Graph 1

    return fig, new_state

# GRAPH SWITCHING BUTTON 4
# Callback to update state and graph upon clicking
@app.callback(
    [Output('display-graph4', 'figure'),
     Output('graph-state4', 'data')],
    [Input('btn-switch4', 'n_clicks')],
    [State('graph-state4', 'data')]
)
def switch_graph4(n_clicks, current_state):
    # Default to Graph 1 if button hasn't been clicked or state is True
    if n_clicks == 0 or current_state:
        # Generate Graph 1
        fig = go.Figure(data=[go.Scatter(x=cdFrame['year'], y=cdFrame['value_actual'], name='Units Sold (In Millions)', marker_color='royalblue', opacity=0.8, yaxis='y'),
                              go.Scatter(x=CD_YearlySent['year'], y=CD_YearlySent['sentiment_score'], mode='lines', name='Sentiment Score', marker_color='black', yaxis='y2')])
        fig.update_layout(title='CD Sales vs Sentiment Score (1973-2019)',
                          xaxis_title='Year',
                          yaxis=dict(title='Units Sold (in Millions)'),
                          yaxis2=dict(title='Sentiment Score', side='right', overlaying='y'),
                          legend=dict(x=1.1, y=1))
        new_state = False # Next click will show Graph 2
    else:
        # Generate Graph 2
        fig = go.Figure(data=[go.Scatter(x=vyFrame['year'], y=vyFrame['value_actual'], name='Units Sold (In Millions)', marker_color='red', opacity=0.8, yaxis='y'),
                              go.Scatter(x=LP_YearlySent['year'], y=LP_YearlySent['sentiment_score'], mode='lines', name='Sentiment Score', marker_color='black', yaxis='y2')])
        fig.update_layout(title='Vinyl Sales vs Sentiment Score (1973-2019)',
                          xaxis_title='Year',
                          yaxis=dict(title='Units Sold (in Millions)'),
                          yaxis2=dict(title='Sentiment Score', side='right', overlaying='y'),
                          legend=dict(x=1.1, y=1))
        new_state = True  # Next click will show Graph 1

    return fig, new_state

# This block here is necessary to be able to run this file individually,
# without the app_tech_disruptions hub page.
# If you'd like to be able to run your files without needing the hub page,
# you can just copy and paste this block exactly how it is into your code.
if __name__ == "__main__":
    import os
    import dash

    # Point at the shared assets/ folder at the project root so standalone
    # runs still pick up the same CSS as the hub app.
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.LITERA],
        assets_folder=os.path.join(os.path.dirname(__file__), "..", "..", "assets"),
    )
    app.layout = layout()
    register_callbacks(app)
    app.run(debug=True)
