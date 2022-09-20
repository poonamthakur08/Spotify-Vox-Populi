import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

from pymongo import MongoClient
from plotly.express import data
import pandas as pd
import plotly.express as px

import time
from APIs.count_tweets import count_tweets
from APIs.latest_tweets_pro import disconnect
from APIs.latest_tweets_pro import produce_tweets
import redis
import json
import numpy as np
from musixmatch import Musixmatch
from wordcloud import WordCloud, STOPWORDS


artist_name = "Harry Styles"
track_name = "As It Was"
ongoing_query = "Harry Styles"
sentiment_val = [0, 0, 0]
sentiment_label = ["Positive", "Neutral", "Negative"]


musixmatch = Musixmatch("")

r = redis.StrictRedis(host="localhost", port=6379, db=0)


client = MongoClient("mongodb://localhost:27017/")
db = client["test"]
collection = db["top_spotify"]

data = pd.DataFrame(list(collection.find()))

artists_names = data.Artist.unique()
track_names = []

external_stylesheets = [
    dbc.themes.CYBORG,
    "/assets/style.css",
]

app = dash.Dash(external_stylesheets=[dbc.themes.CYBORG])

n_intervals = 1

colors = {
    "background": "#111111",
    "text": "#7FDBFF",
    "contrast": "#FFFFFF",
    "mild": "#808080",
    "dark-grey": "#2a2a2a",
}


last_tweets_list = None

map_content = dbc.Card(
    dbc.CardBody([], id="map-graph"),
    className="mt-3",
)


stream_content = dbc.Card(
    dbc.CardBody([], id="stream-graph"),
    className="mt-3",
)

tweet_content = dbc.Card(
    html.Div(
        children=[
            dbc.CardBody([], id="tweet-graph"),
            dcc.Interval(id="interval"),
        ]
    ),
    className="mt-3",
)


lyrics_content = dbc.Card(
    dbc.CardBody([], id="lyrics-text"),
    className="mt-3",
)


tab_plot = dbc.Card(
    [
        dbc.CardHeader(
            dbc.Tabs(
                [
                    dbc.Tab(map_content, label="Map", tab_id="tab-1"),
                    dbc.Tab(stream_content, label="Stream over time", tab_id="tab-2"),
                    dbc.Tab(tweet_content, label="Number of tweets", tab_id="tab-3"),
                    dbc.Tab(lyrics_content, label="Lyrics", tab_id="tab-4"),
                ],
                id="card-tabs",
                active_tab="tab-1",
            )
        ),
        dbc.CardBody(html.P(id="card-content", className="card-text")),
    ]
)
style_numbers = {"display": "block", "font-size": "40px", "font-weight": "700"}
style_dis = {"display": "block", "margin-top": "-10px"}
style_col = {"text-align": "center", "display": "inline"}
energy_bar_1 = {
    "width": "24%",
    "height": "32px",
    "background": "#2a9fd6",
    "border-radius": "3px 0px 0px 3px",
}

energy_bar_2 = {
    "width": "76%",
    "height": "32px",
    "background": "#D6D6D6",
    "border-radius": "0px 3px 3px 0px",
}

dance_bar_1 = {
    "width": "60%",
    "height": "32px",
    "background": "#2a9fd6",
    "border-radius": "3px 0px 0px 3px",
}
dance_bar_2 = {
    "width": "40%",
    "height": "32px",
    "background": "#D6D6D6",
    "border-radius": "0px 3px 3px 0px",
}

valence_bar_1 = {
    "width": "40%",
    "height": "32px",
    "background": "#2a9fd6",
    "border-radius": "3px 0px 0px 3px",
}
valence_bar_2 = {
    "width": "60%",
    "height": "32px",
    "background": "#D6D6D6",
    "border-radius": "0px 3px 3px 0px",
}

bar_ = {
    "display": "inline-flex",
    "margin-top": "18px",
    "margin-bottom": "13px",
    "width": "100%",
}


visualize_song = html.Div(
    [
        dbc.Row(
            [
                dbc.Row(
                    html.Div(id="global-rank", children=["#25"]), style=style_numbers
                ),
                dbc.Row(html.Div("Global "), style=style_dis),
            ],
            align="center",
            style={"margin-top": "-10px"},
        ),
        dbc.Row(
            [
                html.Div(
                    id="follower-count", children=["2435523"], style=style_numbers
                ),
                html.Div("Number of followers", style=style_dis),
            ]
        ),
        dbc.Row(
            [
                html.Div(
                    [
                        html.Div(id="energy-bar-1", children="", style=energy_bar_1),
                        html.Div(id="energy-bar-2", children="", style=energy_bar_2),
                    ],
                    style=bar_,
                ),
                html.Div("Energy", style=style_dis),
            ]
        ),
        dbc.Row(
            [
                html.Div(
                    [
                        html.Div(id="dance-bar-1", children="", style=dance_bar_1),
                        html.Div(id="dance-bar-2", children="", style=dance_bar_2),
                    ],
                    style=bar_,
                ),
                html.Div("Danceability", style=style_dis),
            ]
        ),
        dbc.Row(
            [
                html.Div(
                    [
                        html.Div(id="valence-bar-1", children="", style=valence_bar_1),
                        html.Div(id="valence-bar-2", children="", style=valence_bar_2),
                    ],
                    style=bar_,
                ),
                html.Div("Valence", style=style_dis),
            ]
        ),
    ]
)

song_info = dbc.Card(
    [
        dbc.CardHeader("Track Info", style={"color": "#C6C6C6"}),
        dbc.CardBody([visualize_song], style={"color": "white"}),
    ],
)

sentiment_style = {
    "width": "185px",
    "height": "185px",
    "border-radius": "50%",
    "background": "conic-gradient(red 0deg 80deg,green 80deg 190deg,#6c6c6c 190deg 360deg)",
    "display": "flex",
    "align-items": "center",
    "justify-content": "center",
}

sentiment_plot = dbc.Card(
    [
        dbc.CardHeader("Sentiment Analysis", style={"color": "#C6C6C6"}),
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.Div(
                            [],
                            style={
                                "width": "120px",
                                "height": "120px",
                                "border-radius": "50%",
                                "background": "#282828",
                            },
                        )
                    ],
                    id="sentiment-plot",
                    style=sentiment_style,
                ),
            ],
        ),
    ]
)

tweets = dbc.Card(
    [
        dbc.CardHeader("Last tweets", style={"color": "#C6C6C6"}),
        dbc.CardBody(
            [last_tweets_list],
            id="tweet-stream",
            style={
                "display": "-webkit-inline-box",
                "overflow-x": "auto",
                "width": "100%",
            },
        ),
    ]
)

html_code = '<iframe style="border-radius:3px" src="https://open.spotify.com/embed/track/2ICMOgpboUzD1EcxkUS9qz?si=cf6309a474ec4c43" width="100%" height="100" margin="0px" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>'


app.layout = html.Div(
    style={"backgroundColor": colors["background"]},
    children=[
        dbc.Row(
            html.H1(
                children="Spotify Vox Populi",
                style={"textAlign": "center", "color": colors["contrast"]},
            ),
            style={"height": "150px", "align-content": "center"},
        ),
        dbc.Row(
            [
                dbc.Col(html.Div(), width=1),
                dbc.Col(
                    html.Div(
                        dcc.Dropdown(
                            artists_names,
                            artists_names[0],
                            id="artistdropdown",
                            placeholder="Select Artist",
                        )
                    ),
                    width=4,
                ),
                dbc.Col(
                    html.Div(
                        dcc.Dropdown(
                            value=track_name,
                            id="songsdropdown",
                            placeholder="Select Track",
                        )
                    ),
                    width=4,
                ),
                dbc.Col(
                    html.Div(
                        dbc.Button("Submit", id="submit-btn", color="primary"),
                        className="d-grid gap-2",
                    ),
                    width=2,
                ),
                dbc.Col(html.Div(), width=1),
            ],
            style={
                "padding-top": "10px",
                "margin-bottom": "30px",
                "padding-bottom": "10px",
            },
        ),
        dbc.Row(
            [
                dbc.Col(html.Div(), width=1),
                dbc.Col(
                    html.Div(
                        html.Iframe(srcDoc=html_code, height="100%", width="100%"),
                        id="spotify-player",
                        style={"margin-left": "-9px", "margin-right": "-9px"},
                    ),
                    width=10,
                ),
                dbc.Col(html.Div(), width=1),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.Div(), width=1),
                dbc.Col(html.Div(tab_plot), width=7),
                dbc.Col(html.Div(song_info), width=3),
                dbc.Col(html.Div(), width=1),
            ],
            style={"margin-top": "-44px"},
        ),
        dbc.Row(
            [
                dbc.Col(html.Div(), width=1),
                dbc.Col(html.Div(sentiment_plot), width=2),
                dbc.Col(html.Div(tweets), width=8),
                dbc.Col(html.Div(), width=1),
            ],
            style={"margin-top": "25px"},
        ),
    ],
)


@app.callback(
    dash.dependencies.Output("songsdropdown", "options"),
    [dash.dependencies.Input("artistdropdown", "value")],
)
def display_tracks_by_artist(value):
    track_names = data[data["Artist"] == value]["Track Name"]
    return track_names.unique()


@app.callback(
    Output("sentiment-plot", "style"),
    Output("tweet-stream", "children"),
    Input("interval", "n_intervals"),
)
def update_data(n_intervals):
    global last_tweets_list
    global ongoing_query
    global sentiment_val
    global sentiment_style
    global streams

    message = r.spop(ongoing_query)
    if message is None:
        return sentiment_style, last_tweets_list
    message = message.decode("utf-8")
    q = message.split("**%**")
    tmp = json.loads(q[0])
    user_name = tmp["user_name"]
    user_id = tmp["user_id"]
    img_url = tmp["user_pic"]
    text = tmp["text"]

    tweet_vis = html.Div(
        [
            html.Img(src=img_url, style={"margin": "10px", "border-radius": "3px"}),
            html.Div(
                user_name,
                style={
                    "display": "inline-block",
                    "float": "revert",
                    "margin-left": "10px",
                    "font-weight": "1000",
                    "color": "white",
                },
            ),
            html.Div(
                "@" + user_id,
                style={
                    "display": "inline-block",
                    "float": "revert",
                    "margin-left": "10px",
                },
            ),
            html.Div(
                text,
                style={
                    "padding-left": "10px",
                    "padding-right": "10px",
                    "color": "#e0e0e0",
                },
            ),
        ],
        style={
            "background": "#2F2F2F",
            "width": "400px",
            "height": "185px",
            "border-radius": "3px",
            "margin-right": "12px",
        },
    )

    last_tweets_list.insert(0, tweet_vis)

    tmp = float(q[1])
    if tmp > 0:
        sentiment_val[0] += 1
    elif tmp == 0:
        sentiment_val[1] += 1
    else:
        sentiment_val[2] += 1

    sum_sent = np.sum(sentiment_val)
    neg = (sentiment_val[2] / sum_sent) * 360
    pos = neg + (sentiment_val[0] / sum_sent) * 360
    sentiment_style["background"] = (
        "conic-gradient(red "
        + str(0)
        + "deg "
        + str(neg)
        + "deg,green "
        + str(neg)
        + "deg "
        + str(pos)
        + "deg,#6c6c6c "
        + str(pos)
        + "deg +"
        + str(360)
        + "deg)"
    )

    return sentiment_style, last_tweets_list


streams = []


@app.callback(
    Output("lyrics-text", "children"),
    Output("tweet-graph", "children"),
    Output("map-graph", "children"),
    Output("stream-graph", "children"),
    Output("spotify-player", "children"),
    Output("follower-count", "children"),
    Output("global-rank", "children"),
    Output("energy-bar-1", "style"),
    Output("energy-bar-2", "style"),
    Output("dance-bar-1", "style"),
    Output("dance-bar-2", "style"),
    Output("valence-bar-1", "style"),
    Output("valence-bar-2", "style"),
    Input("submit-btn", "n_clicks"),
    State("artistdropdown", "value"),
    State("songsdropdown", "value"),
)
def update_info(n_clicks, artist_name, track_name):

    global ongoing_query
    global last_tweets_list
    global sentiment_val
    global streams

    sentiment_val = [0, 0, 0]

    r.delete(ongoing_query)

    if artist_name is None:
        artist_name = "Harry Styles"

    if track_name is None:
        track_name = "As It Was"
    if streams is not None:
        for stream in streams:
            if stream[1] != artist_name:
                stream[0].disconnect()
                streams.remove(stream)

    ongoing_query = artist_name
    disconnect(artist_name)

    last_tweets_list = []
    collection = db["artist_info"]

    agg_result = collection.aggregate(
        [{"$match": {"Artist": artist_name, "Track Name": track_name}}]
    )

    data = pd.DataFrame(agg_result)
    for index, row in data.iterrows():
        url = row["Track URL"]
        id_ = url.split("/")[-1]
        url = "https://open.spotify.com/embed/track/" + id_
        html_code_org = (
            '<iframe style="border-radius:3px" src="'
            + url
            + '" width="100%" height="100" margin="0px" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>'
        )
        followers_num = row["Followers"]
        rank = "#" + row["Rank"]
        energy_bar_1["width"] = str(float(row["Energy"]) * 100) + "%"
        energy_bar_2["width"] = str((1 - float(row["Energy"])) * 100) + "%"
        dance_bar_1["width"] = str((float(row["Danceability"])) * 100) + "%"
        dance_bar_2["width"] = str((1 - float(row["Danceability"])) * 100) + "%"
        valence_bar_1["width"] = str((float(row["Valence"])) * 100) + "%"
        valence_bar_2["width"] = str((1 - float(row["Valence"])) * 100) + "%"

    player = html.Iframe(srcDoc=html_code_org, height="100%", width="100%")

    collection = db["top_spotify"]
    agg_result = collection.aggregate(
        [{"$match": {"Artist": artist_name, "Track Name": track_name}}]
    )
    data = pd.DataFrame(agg_result)
    data_stream = data[data.Country != "Global"]
    data_stream["Date"] = pd.to_datetime(data_stream["Date"])
    data_stream = data_stream.sort_values(["Date"])
    data_stream = data_stream.groupby("Date").sum().reset_index()

    fig_stream = px.line(data_stream, x="Date", y="Streams", template="plotly_dark")

    fig_stream.update_xaxes(rangeslider_visible=True)

    fig_stream = dcc.Graph(figure=fig_stream)

    data_map = data[data.Country != "Global"]
    data_map["Date"] = pd.to_datetime(
        data_map["Date"]
    )  # data['Streams'].astype('int')#streams
    data_map = data_map.sort_values(["Date"])
    data_map["Date"] = data_map["Date"].astype("str")

    fig_map = px.choropleth(
        data_map,
        locations="Country",
        color="Streams",
        locationmode="country names",
        hover_name="Country",
        animation_frame="Date",
        template="plotly_dark",
        color_continuous_scale="Viridis",
        height=400,
    )
    fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    fig_map = dcc.Graph(figure=fig_map)

    data_tweet = count_tweets(artist_name + " " + track_name)

    fig_tweet = px.line(data_tweet, x="Date", y="Count", template="plotly_dark")

    fig_tweet.update_xaxes(rangeslider_visible=True)

    fig_tweet = dcc.Graph(figure=fig_tweet)

    lyrics = musixmatch.matcher_lyrics_get(track_name, artist_name)
    tmp = lyrics["message"]["body"]["lyrics"]["lyrics_body"]
    lyrics = tmp.split("*******")[0]

    streams.append([produce_tweets(artist_name), artist_name])

    return (
        lyrics,
        fig_tweet,
        fig_map,
        fig_stream,
        player,
        followers_num,
        rank,
        energy_bar_1,
        energy_bar_2,
        dance_bar_1,
        dance_bar_2,
        valence_bar_1,
        valence_bar_2,
    )


if __name__ == "__main__":
    app.run_server(debug=False, host="0.0.0.0", port=7234)
