import argparse
import config
from scrapers.sportsbookreview import (
    NFLOddsScraper,
    NBAOddsScraper,
    NHLOddsScraper,
    MLBOddsScraper,
)

parser = argparse.ArgumentParser()
parser.add_argument("--sport", type=str, required=True)
# start and end years
parser.add_argument("--start", type=int, required=True)
parser.add_argument("--end", type=int, required=True)
# filename for output
parser.add_argument("--filename", type=str, required=True)
# output format (csv or json), default is json
parser.add_argument("--format", type=str, default="json")

args = parser.parse_args()

if __name__ == "__main__":
    if args.start < config.MIN_YEAR or args.end > config.MAX_YEAR:
        raise ValueError(
            f"Invalid year range. Must be between {config.MIN_YEAR} and {config.MAX_YEAR}."
        )
    if args.start > args.end:
        raise ValueError("Invalid year range. Start year must be before end year.")

    list_yrs = list(range(args.start, args.end + 1))
    scrapers = {
        "nfl": NFLOddsScraper,
        "nba": NBAOddsScraper,
        "nhl": NHLOddsScraper,
        "mlb": MLBOddsScraper,
    }
    scraper = scrapers[args.sport.lower()](list_yrs)
    data = scraper.driver()

    if args.format.lower() == "csv":
        data.to_csv(f"data/{args.filename}.csv", index=False)
    elif args.format.lower() == "json":
        data.to_json(f"data/{args.filename}.json", orient="records")
    else:
        raise ValueError("Invalid output format. Must be csv or json.")
