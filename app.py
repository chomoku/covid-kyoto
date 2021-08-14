import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

age_dict = {
    "10未満": "10代未満",
    "10": "10代",
    "20": "20代",
    "30": "30代",
    "40": "40代",
    "50": "50代",
    "60": "60代",
    "70": "70代",
    "80": "80代",
    "90": "90代",
    "90以上": "90代以上",
    "-": "不明",
}

df = pd.read_html("https://www.pref.kyoto.jp/kentai/corona/hassei1-50.html")[1]

today = df["発表日"][0]

df_new = df[df["発表日"] == today]
df_count = pd.DataFrame(df_new["年代"].value_counts())
df_count.columns = ["人数"]
df_count = df_count.reset_index()
df_count["年代"] = df_count["index"].map(age_dict)

total = df_count["人数"].sum()

fig = go.Figure()
fig.add_trace(go.Pie(labels=df_count["年代"], values=df_count["人数"], textinfo='label+percent', hole=0.7))
fig.update_layout(
    width=800, height=800,
    title={"text": f"{today}", "x": 0.47, "xanchor": "center"},
    annotations=[{"text": f"感染者数: {str(total)}", "showarrow": False, "font_size": 25}],
)

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)

app.layout = html.Div(
    [
        html.Div([
        html.H1("京都コロナウィルス感染者数"),
        html.H2("年代別割合")
        ], className="container pt-3 my-3 bg-primary text-white", style={'textAlign': 'center'}),
        dcc.Graph(figure=fig, style={'margin': 'auto'}),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)
