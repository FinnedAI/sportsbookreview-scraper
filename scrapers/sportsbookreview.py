import requests
import pandas as pd
from itertools import tee
import json
import io
import logging


class OddsScraper:
    def __init__(self, sport, years):
        self.sport = sport
        self.translator = json.load(open("config/translated.json", "r"))
        self.seasons = years

    def _translate(self, name):
        return self.translator[self.sport].get(name, name)

    @staticmethod
    def _make_season(season):
        season = str(season)
        yr = season[2:]
        next_yr = str(int(yr) + 1)
        return f"{season}-{next_yr}"

    @staticmethod
    def _make_datestr(date, season, start=8, yr_end=12):
        date = str(date)
        if len(date) == 3:
            date = f"0{date}"
        month = date[:2]

        if int(month) in range(start, yr_end + 1):
            return f"{date}{season}"

        return f"{date}{int(season) + 1}"

    @staticmethod
    def _pairwise(iterable):
        a, b = tee(iterable)
        next(b, None)
        return zip(a, b)

    def driver(self):
        df = pd.DataFrame()
        for season in self.seasons:
            season_str = self._make_season(season)
            url = self.base + season_str

            # Sportsbookreview has scraper protection, so we need to set a user agent
            # to get around this.
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers)

            dfs = pd.read_html(r.text)
            df = pd.concat([df, self._reformat_data(dfs[0][1:], season)], axis=0)
        return self._to_schema(df)


class NFLOddsScraper(OddsScraper):
    def __init__(self, years):
        super().__init__("nfl", years)
        self.base = (
            "https://www.sportsbookreviewsonline.com/scoresoddsarchives/nfl-odds-"
        )
        self.schema = {
            "season": [],
            "date": [],
            "home_team": [],
            "away_team": [],
            "home_1stQtr": [],
            "away_1stQtr": [],
            "home_2ndQtr": [],
            "away_2ndQtr": [],
            "home_3rdQtr": [],
            "away_3rdQtr": [],
            "home_4thQtr": [],
            "away_4thQtr": [],
            "home_final": [],
            "away_final": [],
            "home_close_ml": [],
            "away_close_ml": [],
            "home_open_spread": [],
            "away_open_spread": [],
            "home_close_spread": [],
            "away_close_spread": [],
            "home_2H_spread": [],
            "away_2H_spread": [],
            "2H_total": [],
            "open_over_under": [],
            "close_over_under": [],
        }

    def _reformat_data(self, df, season):
        new_df = pd.DataFrame()
        new_df["season"] = [season] * len(df)
        new_df["date"] = df[0].apply(lambda x: self._make_datestr(x, season))
        new_df["name"] = df[3]
        new_df["1stQtr"] = df[4]
        new_df["2ndQtr"] = df[5]
        new_df["3rdQtr"] = df[6]
        new_df["4thQtr"] = df[7]
        new_df["final"] = df[8]
        _open = df[9].apply(lambda x: 0 if str(x).lower() == "pk" else x)
        new_df["open_odds"] = _open
        close = df[10].apply(lambda x: 0 if str(x).lower() == "pk" else x)
        new_df["close_odds"] = close
        new_df["close_ml"] = df[11]
        h2 = df[12].apply(lambda x: 0 if str(x).lower() == "pk" else x)
        new_df["2H_odds"] = h2
        return new_df

    def _to_schema(self, df):
        df = df.dropna(how="any").reset_index(drop=True)
        df = df[df["2H_odds"] != "NL"].reset_index(drop=True)
        new_df = self.schema.copy()
        progress = df.iterrows()
        for (i1, row), (i2, next_row) in self._pairwise(progress):
            try:
                home_ml = int(next_row["close_ml"])
                away_ml = int(row["close_ml"])

                odds1 = float(row["open_odds"])
                odds2 = float(next_row["open_odds"])
                if odds1 < odds2:
                    open_spread = odds1
                    close_spread = float(row["close_odds"])
                    h2_spread = float(row["2H_odds"])

                    h2_total = float(next_row["2H_odds"])
                    open_ou = odds2
                    close_ou = float(next_row["close_odds"])
                else:
                    open_spread = odds2
                    close_spread = float(next_row["close_odds"])
                    h2_spread = float(next_row["2H_odds"])

                    h2_total = float(row["2H_odds"])
                    open_ou = odds1
                    close_ou = float(row["close_odds"])

                home_open_spread = -open_spread if home_ml < away_ml else open_spread
                away_open_spread = -home_open_spread
                home_close_spread = -close_spread if home_ml < away_ml else close_spread
                away_close_spread = -home_close_spread
                h2_home_spread = -h2_spread if home_ml < away_ml else h2_spread
                h2_away_spread = -h2_home_spread
            except Exception as e:
                logging.error(
                    f"Encountered error: {e} when reformatting data, params {row['season']}"
                )
                continue

            new_df["season"].append(row["season"])
            new_df["date"].append(row["date"])
            new_df["home_team"].append(self._translate(next_row["name"]))
            new_df["away_team"].append(self._translate(row["name"]))
            new_df["home_1stQtr"].append(next_row["1stQtr"])
            new_df["away_1stQtr"].append(row["1stQtr"])
            new_df["home_2ndQtr"].append(next_row["2ndQtr"])
            new_df["away_2ndQtr"].append(row["2ndQtr"])
            new_df["home_3rdQtr"].append(next_row["3rdQtr"])
            new_df["away_3rdQtr"].append(row["3rdQtr"])
            new_df["home_4thQtr"].append(next_row["4thQtr"])
            new_df["away_4thQtr"].append(row["4thQtr"])
            new_df["home_final"].append(next_row["final"])
            new_df["away_final"].append(row["final"])
            new_df["home_close_ml"].append(home_ml)
            new_df["away_close_ml"].append(away_ml)
            new_df["home_open_spread"].append(home_open_spread)
            new_df["away_open_spread"].append(away_open_spread)
            new_df["home_close_spread"].append(home_close_spread)
            new_df["away_close_spread"].append(away_close_spread)
            new_df["home_2H_spread"].append(h2_home_spread)
            new_df["away_2H_spread"].append(h2_away_spread)
            new_df["2H_total"].append(h2_total)
            new_df["open_over_under"].append(open_ou)
            new_df["close_over_under"].append(close_ou)

        return pd.DataFrame(new_df)


# NBA is the same as NFL, so we can subclass the NFL scraper
class NBAOddsScraper(NFLOddsScraper):
    def __init__(self, years):
        super().__init__(years)
        self.sport = "nba"
        self.base = (
            "https://www.sportsbookreviewsonline.com/scoresoddsarchives/nba-odds-"
        )
        self.schema = {
            "season": [],
            "date": [],
            "home_team": [],
            "away_team": [],
            "home_1stQtr": [],
            "away_1stQtr": [],
            "home_2ndQtr": [],
            "away_2ndQtr": [],
            "home_3rdQtr": [],
            "away_3rdQtr": [],
            "home_4thQtr": [],
            "away_4thQtr": [],
            "home_final": [],
            "away_final": [],
            "home_close_ml": [],
            "away_close_ml": [],
            "home_open_spread": [],
            "away_open_spread": [],
            "home_close_spread": [],
            "away_close_spread": [],
            "home_2H_spread": [],
            "away_2H_spread": [],
            "2H_total": [],
            "open_over_under": [],
            "close_over_under": [],
        }


# NHL is the same as NFL, so we can subclass the NFL scraper
class NHLOddsScraper(OddsScraper):
    def __init__(self, years):
        super().__init__("nhl", years)
        self.base = (
            "https://www.sportsbookreviewsonline.com/scoresoddsarchives/nhl-odds-"
        )
        self.schema = {
            "season": [],
            "date": [],
            "home_team": [],
            "away_team": [],
            "home_1stPeriod": [],
            "away_1stPeriod": [],
            "home_2ndPeriod": [],
            "away_2ndPeriod": [],
            "home_3rdPeriod": [],
            "away_3rdPeriod": [],
            "home_final": [],
            "away_final": [],
            "home_open_ml": [],
            "away_open_ml": [],
            "home_close_ml": [],
            "away_close_ml": [],
            "home_close_spread": [],
            "away_close_spread": [],
            "home_close_spread_odds": [],
            "away_close_spread_odds": [],
            "home_open_over_under": [],
            "away_open_over_under": [],
            "home_open_over_under_odds": [],
            "away_open_over_under_odds": [],
            "home_close_over_under": [],
            "away_close_over_under": [],
            "home_close_over_under_odds": [],
            "away_close_over_under_odds": [],
        }

    def _reformat_data(self, df, season, covid=False):
        new_df = pd.DataFrame()
        new_df["season"] = [season] * len(df)
        new_df["date"] = df[0].apply(
            lambda x: self._make_datestr(x, season)
            if not covid
            else self._make_datestr(x, season, start=1, yr_end=3)
        )
        new_df["name"] = df[3]
        new_df["1stPeriod"] = df[4]
        new_df["2ndPeriod"] = df[5]
        new_df["3rdPeriod"] = df[6]
        new_df["final"] = df[7]
        new_df["open_ml"] = df[8]
        new_df["close_ml"] = df[9]
        new_df["close_spread"] = df[10] if season > 2013 else 0
        new_df["close_spread_odds"] = df[11] if season > 2013 else 0
        new_df["open_over_under"] = df[12] if season > 2013 else df[10]
        new_df["open_over_under_odds"] = df[13] if season > 2013 else df[11]
        new_df["close_over_under"] = df[14] if season > 2013 else df[12]
        new_df["close_over_under_odds"] = df[15] if season > 2013 else df[13]

        return new_df

    def _to_schema(self, df):
        df = df.dropna(how="any").reset_index(drop=True)
        new_df = self.schema.copy()
        progress = df.iterrows()
        for (i1, row), (i2, next_row) in self._pairwise(progress):
            new_df["season"].append(row["season"])
            new_df["date"].append(row["date"])
            new_df["home_team"].append(self._translate(next_row["name"]))
            new_df["away_team"].append(self._translate(row["name"]))
            new_df["home_1stPeriod"].append(next_row["1stPeriod"])
            new_df["away_1stPeriod"].append(row["1stPeriod"])
            new_df["home_2ndPeriod"].append(next_row["2ndPeriod"])
            new_df["away_2ndPeriod"].append(row["2ndPeriod"])
            new_df["home_3rdPeriod"].append(next_row["3rdPeriod"])
            new_df["away_3rdPeriod"].append(row["3rdPeriod"])
            new_df["home_final"].append(next_row["final"])
            new_df["away_final"].append(row["final"])
            new_df["home_open_ml"].append(next_row["open_ml"])
            new_df["away_open_ml"].append(row["open_ml"])
            new_df["home_close_ml"].append(next_row["close_ml"])
            new_df["away_close_ml"].append(row["close_ml"])
            new_df["home_close_spread"].append(next_row["close_spread"])
            new_df["away_close_spread"].append(row["close_spread"])
            new_df["home_close_spread_odds"].append(next_row["close_spread_odds"])
            new_df["away_close_spread_odds"].append(row["close_spread_odds"])
            new_df["home_open_over_under"].append(next_row["open_over_under"])
            new_df["away_open_over_under"].append(row["open_over_under"])
            new_df["home_open_over_under_odds"].append(next_row["open_over_under_odds"])
            new_df["away_open_over_under_odds"].append(row["open_over_under_odds"])
            new_df["home_close_over_under"].append(next_row["close_over_under"])
            new_df["away_close_over_under"].append(row["close_over_under"])
            new_df["home_close_over_under_odds"].append(
                next_row["close_over_under_odds"]
            )
            new_df["away_close_over_under_odds"].append(row["close_over_under_odds"])

        return pd.DataFrame(new_df)

    def driver(self):
        dfs = pd.DataFrame()
        for season in self.seasons:
            # compensate for the COVID shortened season in 2021
            season_str = self._make_season(season) if season != 2020 else "2021"
            is_cov = True if season == 2020 else False
            url = self.base + season_str

            # Sportsbookreview has scraper protection, so we need to set a user agent
            # to get around this.
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers)

            dfs = pd.concat(
                [dfs, self._reformat_data(pd.read_html(r.text)[0][1:], season, is_cov)],
                axis=0,
            )

        return self._to_schema(dfs)


# MLB has a different format, so we need to subclass the OddsScraper
class MLBOddsScraper(OddsScraper):
    def __init__(self, years):
        super().__init__("mlb", years)
        self.base = "https://www.sportsbookreviewsonline.com/wp-content/uploads/sportsbookreviewsonline_com_737/mlb-odds-"
        self.ext = ".xlsx"
        self.schema = {
            "season": [],
            "date": [],
            "home_team": [],
            "away_team": [],
            "home_1stInn": [],
            "away_1stInn": [],
            "home_2ndInn": [],
            "away_2ndInn": [],
            "home_3rdInn": [],
            "away_3rdInn": [],
            "home_4thInn": [],
            "away_4thInn": [],
            "home_5thInn": [],
            "away_5thInn": [],
            "home_6thInn": [],
            "away_6thInn": [],
            "home_7thInn": [],
            "away_7thInn": [],
            "home_8thInn": [],
            "away_8thInn": [],
            "home_9thInn": [],
            "away_9thInn": [],
            "home_final": [],
            "away_final": [],
            "open_ml": [],
            "close_ml": [],
            "close_spread": [],
            "close_spread_odds": [],
            "open_over_under": [],
            "open_over_under_odds": [],
            "close_over_under": [],
            "close_over_under_odds": [],
        }

    def _reformat_data(self, df, season):
        new_df = pd.DataFrame()
        new_df["season"] = [season] * len(df)
        new_df["date"] = df[0].apply(
            lambda x: self._make_datestr(x, season, start=3, yr_end=10)
        )
        new_df["name"] = df[3]
        new_df["1stInn"] = df[5]
        new_df["2ndInn"] = df[6]
        new_df["3rdInn"] = df[7]
        new_df["4thInn"] = df[8]
        new_df["5thInn"] = df[9]
        new_df["6thInn"] = df[10]
        new_df["7thInn"] = df[11]
        new_df["8thInn"] = df[12]
        new_df["9thInn"] = df[13]
        new_df["final"] = df[14]
        new_df["open_ml"] = df[17]
        new_df["close_ml"] = df[16]
        new_df["close_spread"] = df[17] if season > 2013 else 0
        new_df["close_spread_odds"] = df[18] if season > 2013 else 0
        new_df["open_over_under"] = df[19] if season > 2013 else df[17]
        new_df["open_over_under_odds"] = df[20] if season > 2013 else df[18]
        new_df["close_over_under"] = df[21] if season > 2013 else df[19]
        new_df["close_over_under_odds"] = df[22] if season > 2013 else df[20]

        return new_df

    def _to_schema(self, df):
        df = df.dropna(how="any").reset_index(drop=True)
        new_df = self.schema.copy()
        progress = df.iterrows()
        for (i1, row), (i2, next_row) in self._pairwise(progress):
            new_df["season"].append(row["season"])
            new_df["date"].append(row["date"])
            new_df["home_team"].append(self._translate(next_row["name"]))
            new_df["away_team"].append(self._translate(row["name"]))
            new_df["home_1stInn"].append(next_row["1stInn"])
            new_df["away_1stInn"].append(row["1stInn"])
            new_df["home_2ndInn"].append(next_row["2ndInn"])
            new_df["away_2ndInn"].append(row["2ndInn"])
            new_df["home_3rdInn"].append(next_row["3rdInn"])
            new_df["away_3rdInn"].append(row["3rdInn"])
            new_df["home_4thInn"].append(next_row["4thInn"])
            new_df["away_4thInn"].append(row["4thInn"])
            new_df["home_5thInn"].append(next_row["5thInn"])
            new_df["away_5thInn"].append(row["5thInn"])
            new_df["home_6thInn"].append(next_row["6thInn"])
            new_df["away_6thInn"].append(row["6thInn"])
            new_df["home_7thInn"].append(next_row["7thInn"])
            new_df["away_7thInn"].append(row["7thInn"])
            new_df["home_8thInn"].append(next_row["8thInn"])
            new_df["away_8thInn"].append(row["8thInn"])
            new_df["home_9thInn"].append(next_row["9thInn"])
            new_df["away_9thInn"].append(row["9thInn"])
            new_df["home_final"].append(next_row["final"])
            new_df["away_final"].append(row["final"])
            new_df["open_ml"].append(next_row["open_ml"])
            new_df["close_ml"].append(next_row["close_ml"])
            new_df["close_spread"].append(next_row["close_spread"])
            new_df["close_spread_odds"].append(next_row["close_spread_odds"])
            new_df["open_over_under"].append(next_row["open_over_under"])
            new_df["open_over_under_odds"].append(next_row["open_over_under_odds"])
            new_df["close_over_under"].append(next_row["close_over_under"])
            new_df["close_over_under_odds"].append(next_row["close_over_under_odds"])

        return pd.DataFrame(new_df)

    def driver(self):
        dfs = pd.DataFrame()
        for season in self.seasons:
            url = self.base + str(season) + self.ext
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers)

            with io.BytesIO(r.content) as fh:
                df = pd.read_excel(fh, header=None, sheet_name=None)
            dfs = pd.concat(
                [dfs, self._reformat_data(df["Sheet1"][1:], season)], axis=0
            )

        return self._to_schema(dfs)
