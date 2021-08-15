import requests
import pandas as pd


"""
    データの持つ属性
    No: int  通し番号
    リリース日: str 発表日
    居住地: str 住んでる場所
    年代と性別: str 
    退院: str 〇とNone 
    date: datetime　発表日
    age: str 年代
    sex: str 性別
"""


def _get_data_from_kyoto_covid(url):
    r = requests.get(url)
    print(r.status_code)
    res = r.json()
    df = pd.DataFrame(res["data"])
    df["date"] = df["リリース日"].map(lambda x: x.split("T")[0])
    df["date"] = pd.to_datetime(df["date"])
    return df


"""
男性を不明男性、女性を不明女性に置き換えるのをどうするか分からない。
ひとまず放置して進める
"""


def _data_prepro(df, replace_dict):
    for k, v in replace_dict.items():
        df["年代と性別"] = df["年代と性別"].str.replace(k, v)

    df["age"] = df["年代と性別"].map(lambda x: x[:-2])
    df["sex"] = df["年代と性別"].map(lambda x: x[-2:])
    return df


if __name__ == "__main__":
    url = "https://raw.githubusercontent.com/stop-covid19-kyoto/covid19-kyoto/development/data/patients.json"
    replace_dict = {
        "2代": "20代",
        " ": "",
        "―": "不明",
        "－代": "不明",
        "園児": "10代未満不明",
        "10未満男性": "10代未満男性",
        "10未満女性": "10代未満女性",
        "調査中代": "不明",
        "不明代": "不明",
        "調査中代": "不明",
        "6代": "60代",
    }
    df = _get_data_from_kyoto_covid(url)
    df = _data_prepro(df, replace_dict)
    df.to_csv("data/kyoto_patients.csv", index=None)
    print(df)
