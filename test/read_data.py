import pandas as pd

if __name__ == "__main__":
    vac_num = pd.read_csv("../data/vaccined_num.csv")
    vac_for = pd.read_csv("../data/vac_forecast.csv")

    print(vac_for)
