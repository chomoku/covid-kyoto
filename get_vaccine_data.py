from datetime import datetime
from typing import List
from requests_html import HTMLSession
import pandas as pd


def _wareki_to_datetime(date_str: str) -> datetime:
    if date_str[:2] == "令和":
        dt_str = date_str[2:]
        dt_str = dt_str.split("年")
        dt_year = int(dt_str[0])
        dt_year = 2018 + dt_year
        dt_str = dt_str[1].split("月")
        dt_month = int(dt_str[0])
        dt_str = dt_str[1].split("日")
        dt_day = int(dt_str[0])
        the_datetime = datetime(dt_year, dt_month, dt_day)
        return the_datetime


def kyoto_text_to_date(text_block: List, text_num: int) -> str:
    vac_str = text_block[text_num].text
    vac_str = vac_str.split("\u3000")[0].replace("（", "")
    vac_str = _wareki_to_datetime(vac_str)
    return vac_str


"""
もう少し使いやすくする必要性
問題: 日付の位置が動いてしまう
どうやって探すか？
総当たりして、リストに格納、Noneをはじくとか？
作業を並列に行うと、修正などが難しい。
1つの作業は一つの塊で扱う。
"""

if __name__ == "__main__":
    data = pd.read_html(
        "https://www.city.kyoto.lg.jp/hokenfukushi/page/0000280084.html"
    )
    session = HTMLSession()
    r = session.get("https://www.city.kyoto.lg.jp/hokenfukushi/page/0000280084.html")
    text_block = r.html.find(".mol_textblock")

    # データの日付作成

    date_list = list()

    for num in range(len(text_block)):
        date_list.append(kyoto_text_to_date(text_block, num))

    date_list = [d for d in date_list if d]
    seshu_date = date_list[0]
    forecast_date = date_list[1]

    seshu = {"接種率": "1回目接種率", "接種率.1": "2回目接種率"}

    # データフレーム作成

    total_df = data[0]
    total_df["date"] = seshu_date
    total_df = total_df.rename({"Unnamed: 0": "年代"}, axis=1)
    total_df = total_df.rename(seshu, axis=1)

    aged_df = data[1]
    aged_df["date"] = seshu_date
    aged_df = aged_df.rename(seshu, axis=1)
    vaccine_num_df = pd.concat([total_df, aged_df]).reset_index(drop=True)

    for num, col in enumerate(vaccine_num_df.columns[1:-1]):
        if num % 2 == 0:
            vaccine_num_df[col] = vaccine_num_df[col].map(
                lambda x: int(
                    x.replace("\u3000回", "").replace("\u3000％", "").replace(",", "")
                )
            )
        else:
            vaccine_num_df[col] = vaccine_num_df[col].map(
                lambda x: float(
                    x.replace("\u3000回", "").replace("\u3000％", "").replace(",", "")
                )
            )

    forecast_df = data[2]
    forecast_df["date"] = forecast_date

    forecast_df["配送数（予定を含む）"] = forecast_df["配送数（予定を含む）"].map(
        lambda x: int(x.replace("\u3000回分", "").replace(",", "").replace("約", ""))
    )

    old_num_df = pd.read_csv("./data/vaccined_num.csv")
    old_for_df = pd.read_csv("./data/vac_forecast.csv")

    old_num_df = old_num_df.rename(seshu, axis=1)
    old_for_df = old_for_df.rename(seshu, axis=1)

    new_num_df = pd.concat([old_num_df, vaccine_num_df])
    new_for_df = pd.concat([old_for_df, forecast_df])

    new_num_df.to_csv("./data/vaccined_num.csv", index=None)
    new_for_df.to_csv("./data/vac_forecast.csv", index=None)