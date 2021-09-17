from os import replace
from requests_html import HTMLSession
import pandas as pd
from typing import List, Tuple
from datetime import datetime
from datetime import timedelta
import re
import time

# 年齢行の置き換えよう辞書
replace_dict = {
    "2": "20代",
    " ": "不明",
    "-": "不明",
    "―": "不明",
    "－": "不明",
    "園児": "10代未満",
    "10未満": "10代未満",
    "10未満": "10代未満",
    "調査中": "不明",
    "不明": "不明",
    "6": "60代",
    "10未満": "10代未満",
    "100以上": "90代以上",
    "90以上": "90代以上",
    "10": "10代",
    "20": "20代",
    "30": "30代",
    "40": "40代",
    "50": "50代",
    "60": "60代",
    "70": "70代",
    "80": "80代",
    "90": "90代",
}


def _wareki_to_datetime(date_str: str) -> datetime:
    """
    令和の和暦を西暦に変更し、datetime型で返す
    Params:
        date_str: 令和の日付（令和〇年〇月〇日）
    Returns:
        the_datetime: 西暦の日付
    
    """
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
    else:
        pass


def _latest_data_desc(page_url: str) -> Tuple[datetime, int]:
    """
        京都府のサイトから最新データの日付、感染者数を取得する
        Params:
            page_url : サイトのURL
        Returns:
            latest_date: datetime
    
    """
    session = HTMLSession()
    r = session.get(page_url)
    top_content = r.html.find("h3")  # 日付の取得
    date_cont = top_content[0].text.split("日")[0].split("月")
    data_day = int(date_cont[1])
    data_month = int(date_cont[0])
    date_year = (datetime.now() - timedelta(1)).year
    master_date = datetime(date_year, data_month, data_day)  # 資料の日付の取得完了

    # 感染者数のデータの取得
    df = pd.read_html(page_url)[0]
    master_count = int(df.iloc[0, 1].split("名")[0])

    return master_date, master_count

# リンクの数値を取得する関数

def _get_hassei_url(select_num: int) -> List:
    '''
     京都の感染バックナンバーのURLを取得する
     Params:
        select_num: 取得するバックナンバーURLの数
     Returns:
        link_list: select_numで指定された数のURLのリスト
    '''
    hassei_bn_url = 'https://www.pref.kyoto.jp/kentai/corona/hassei-bn.html'
    session = HTMLSession()
    r = session.get(hassei_bn_url)
    links = r.html.absolute_links
    link_list = [link for link in links if re.search('hassei', link)] #バックナンバーのURLを格納
    link_list = [link.split('hassei')[1].split('.')[0] for link in link_list] # バックナンバーの番号部分をリストに格納
    r = re.compile('^[0-9]+$')
    num_list = [int(num) for num in filter(r.match, link_list)]
    num_list = sorted(num_list)
    num_list = num_list[-select_num:]
    link_list = [f'https://www.pref.kyoto.jp/kentai/corona/hassei{i}.html' for i in num_list]
    return link_list


def get_data(selected_num: int) -> pd.DataFrame:
    '''
     バックナンバーをselected_numで指定した分と、1-50にあるデータを取得する
     関数。
     Params:
        selected_num: バックナンバーの数を指定する
     Returns:
        data: バックナンバー＋最新のデータを持つ
    '''
    link_list = _get_hassei_url(selected_num)
    data = pd.DataFrame()
    for link in link_list:
        df = pd.read_html(link)[0]
        df = df[df['発表日'] != "（欠番）"]
        df = _rename_data(df)
        data = pd.concat([data, df])
        time.sleep(2)
    df = pd.read_html('https://www.pref.kyoto.jp/kentai/corona/hassei1-50.html')[1]
    df = _rename_data(df)
    df = df[df['発表日'] != "（欠番）"]
    data = pd.concat([data, df])
    data = data.reset_index(drop=True)
    data = data.sort_values("date")
    return data


def _rename_data(df):
    df = df.rename({"Unnamed: 0": "事例"}, axis=1)
    df["date"] = df["発表日"].map(_wareki_to_datetime)
    df["age"] = df["年代"].map(replace_dict)
    return df

def update_data(data_path: str, page_url: str, selected_num: int) -> None:
    """
        京都府のコロナ感染者数のテーブルが最新のものに更新されるかチェックして、
        最新であればCSVファイルを更新、保存する

        Params:
            data_path: csvfileへのパス
            page_url: 感染者数ページへのURL
            selected_num: バックナンバーの取得数

    """
    page_df = get_data(selected_num)
    page_latest_date = max(page_df["date"].dropna())
    latest_data_num = len(page_df[page_df["date"] == page_latest_date])

    base_data = pd.read_csv(data_path, index_col=0, parse_dates=["date"])  # 保有するデータ
    base_data_latest_date = max(base_data["date"])
    master_date, master_count = _latest_data_desc(page_url)
    print(f'{master_date} / {master_count}/ {page_latest_date} / {latest_data_num}')
    if (
        master_date == page_latest_date
        and latest_data_num == master_count
        and master_date != base_data_latest_date
    ):
        new_data = page_df.merge(base_data, on=list(base_data.columns), how='outer')
        new_data = new_data.sort_values('date')
        new_data = new_data.reset_index(drop=True)
        new_data.to_csv("./data/kyoto_covid_patient.csv", index=None)
        new_data[['date', 'age']].to_csv('./data/kyoto_covid2.csv', index=None)
        print("done!")
    else:
        print("Not Yet!")


if __name__ == "__main__":
    data_path = "./data/kyoto_covid_patient.csv"
    page_url = "https://www.pref.kyoto.jp/kentai/corona/hassei1-50.html"
    update_data(data_path, page_url, 5)
