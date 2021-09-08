from datetime import datetime
from typing import List, Dict, Tuple
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


def get_update_date(path):
    session = HTMLSession()
    r = session.get(path)
    text_block = r.html.find(".mol_textblock")
    date_list = list()
    for num in range(len(text_block)):
        date_list.append(kyoto_text_to_date(text_block, num))
    date_list = [d for d in date_list if d]
    seshu_date = date_list[0]
    forecast_date = date_list[1]
    return seshu_date, forecast_date


def latest_csv(path: str) -> Tuple[datetime, pd.DataFrame]:
    """
    Desc:
        保有するCSVの日付とデータフレームを返す
    Params:
        path: str
        csvのpath
    Returns:
        date_max: datetime
        保有csvの最新の日付
        df: pd.Dataframe
        保有csvのデータフレーム
    """

    df = pd.read_csv(path, parse_dates=["date"])
    date_max = df["date"].max()
    return date_max, df


def vac_num_df_prepro(
    data: List, num: int, latest_date: datetime, seshu_dict: Dict = None
) -> pd.DataFrame:
    """
    desc:
        pathにある目的のデータを取得するための関数

    Params:
        data: str
        ページにあるデータフレームのリスト
        num: int
        ワクチン接種数のテーブルの掲載されている番号
        現在:
            0: 総数
            1: 年代別
        latest_date: datetime
        データ取得日
    Returns:
        df: pd.DataFrame
        取得されたデータフレーム
    """

    df = data[num]
    df["date"] = latest_date
    df = df.rename({"Unnamed: 0": "年代"}, axis=1)
    if seshu_dict:
        df = df.rename(seshu_dict, axis=1)
    return df


if __name__ == "__main__":
    data_url = "https://www.city.kyoto.lg.jp/hokenfukushi/page/0000280084.html"
    data = pd.read_html(data_url)

    seshu_date, forecast_date = get_update_date(data_url)

    seshu = {"接種率": "1回目接種率", "接種率.1": "2回目接種率"}

    # 自分の持つデータを読み込み、データ更新の最新日を取得
    vac_num_path = "./data/vaccined_num.csv"
    vac_forecast_path = "./data/vac_forecast.csv"

    old_num_date, old_num_df = latest_csv(vac_num_path)
    old_for_date, old_for_df = latest_csv(vac_forecast_path)

    # まずは数値データ分を作成する

    data = pd.read_html(data_url)

    if old_num_date != seshu_date:
        total_df = vac_num_df_prepro(data, 0, seshu_date, seshu)
        aged_df = vac_num_df_prepro(data, 1, seshu_date, seshu)
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
    else:
        print("接種者数は更新されていませんでした")

    new_num_df = pd.concat([old_num_df, vaccine_num_df])

    if old_for_date != forecast_date:
        forecast_df = vac_num_df_prepro(data, 2, forecast_date)
        forecast_df["配送数（予定を含む）"] = forecast_df["配送数（予定を含む）"].map(
            lambda x: int(x.replace("\u3000回分", "").replace(",", "").replace("約", ""))
        )

    else:
        print("配送数は更新されていませんでした")

    new_for_df = pd.concat([old_for_df, forecast_df])

    new_num_df.to_csv("./data/vaccined_num.csv", index=None)
    new_for_df.to_csv("./data/vac_forecast.csv", index=None)
