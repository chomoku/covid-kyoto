import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dash.dependencies import Input, Output, State

from datetime import date
from datetime import datetime

# データを京都府のサイトからとっていた際のコード
# age_dict = {
#     "10未満": "10代未満",
#     "10": "10代",
#     "20": "20代",
#     "30": "30代",
#     "40": "40代",
#     "50": "50代",
#     "60": "60代",
#     "70": "70代",
#     "80": "80代",
#     "90": "90代",
#     "90以上": "90代以上",
#     "-": "不明",
# }

# df = pd.read_html("https://www.pref.kyoto.jp/kentai/corona/hassei1-50.html")[1]
# today = df["発表日"][0]

# df_new = df[df["発表日"] == today]
# df_count = pd.DataFrame(df_new["年代"].value_counts())
# df_count.columns = ["人数"]
# df_count = df_count.reset_index()
# df_count["年代"] = df_count["index"].map(age_dict)

# total = df_count["人数"].sum()


def draw_circle(df: pd.DataFrame, total: int, today: str) -> go.Figure:
    """
    年代別患者数の円グラフを作成する関数
    """
    fig = go.Figure()
    circle_size = 300 + total / 1.5 
    fig.add_trace(
        go.Pie(
            labels=df["age"], values=df["counts"], textinfo="label+percent", hole=0.7
        )
    )
    fig.update_layout(
        width=circle_size,
        height=circle_size,
        title={"text": f"{today}", "x": 0.47, "xanchor": "center"},
        annotations=[
            {"text": f"感染者数: {str(total)}", "showarrow": False, "font_size": 25}
        ],
        showlegend=False
    )
    return fig


def cal_counts(df: pd.DataFrame, selected_date: datetime) -> pd.DataFrame:
    """
    選択された日付のデータを集計したものを出力
    その日の感染者数の合計も返す
    """
    selected_df = df[df["date"] == selected_date]
    counts = pd.DataFrame(selected_df["age"].value_counts())
    counts.columns = ["counts"]
    counts = counts.reset_index()
    counts = counts.rename({"index": "age"}, axis=1)

    total = len(selected_df)
    return counts, total


df = pd.read_csv("data/kyoto_patients.csv", parse_dates=['date'])
new_date = df["date"].max()
min_date = df["date"].min()
new_counts, new_total = cal_counts(df, new_date)

## データ全てを年齢と日付で分けたもの
aged_df = pd.DataFrame(df[['date', 'age']].value_counts())
aged_df.columns = ['counts']
aged_df = aged_df.reset_index()

aged_fig = px.bar(aged_df, x='date', y='counts', color='age')
aged_fig.update_layout(
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1,
                     label="1m",
                     step="month",
                     stepmode="backward"),
                dict(count=3,
                     label="3m",
                     step="month",
                     stepmode="backward",),
                dict(count=6,
                     label="6m",
                     step="month",
                     stepmode="backward"),
                # dict(count=1,
                #      label="1y",
                #      step="year",
                #      stepmode="backward"),
                # dict(step="all")
            ])
        ),
        rangeslider=dict(
            visible=True
        ),
        type="date"
    )
)

test_fig = draw_circle(new_counts, new_total, new_date)

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)

app.layout = html.Div(
    [
        html.Div(
            [html.H1("京都コロナウィルス感染者数"), html.H2("年代別割合")],
            className="container pt-3 my-3 bg-primary text-white",
            style={"textAlign": "center"},
        ),
        html.Div(
            [
                dcc.Graph(
                    id="latest_graph",
                    figure=test_fig,
                    style={"margin": "auto", "display": "inline-block", "width": "50%"},
                ),
                html.Div(
                    [
                        html.Div([
                        html.P('日付選択: ', style={'display': 'inline-block', 'marginRight': '2%', 'fontSize': "1.2rem"}),
                        dcc.DatePickerSingle(
                            id="datepicker",
                            min_date_allowed=min_date,
                            max_date_allowed=new_date,
                            initial_visible_month=date(2021, 7, 1),
                            date=date(2021, 1, 5),
                            display_format="YYYY/M/D",
                            style={'display': 'inline-block', 'verticalAlign': 'middle'}
                        )
                        ], style={'margin': '5% auto'}),
                        dcc.Graph(id="second_graph", style={'margin': 'auto'}),
                    ],
                    style={
                        "display": "inline-block",
                        "width": "50%",

                        "textAlign": 'center',
                        "verticalAlign": "top",
                    },
                ),
            ]
        ),
        html.Div([
            html.H3('年齢別感染者数（時系列）'),
            dcc.Graph(figure=aged_fig, style={'height': 500})
        ])
    ]
)


@app.callback(
    Output('second_graph', 'figure'),

    Input('datepicker', 'date')
)
def update_circle(selected_date):
    selected_datetime = datetime(int(selected_date.split('-')[0]), int(selected_date.split('-')[1]), int(selected_date.split('-')[2]))
    selected_df, sel_total = cal_counts(df, selected_datetime)
    fig = draw_circle(selected_df, sel_total, selected_datetime)
    return fig

if __name__ == "__main__":
    app.run_server(debug=True)
