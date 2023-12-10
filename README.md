# Sportsbookreview.com Scraper
> Scrape 10+ years of sportsbookreview.com data. Currently supports NFL, NBA, MLB, NHL, but can be easily extended to other sports.

Keywords: ``sportsbookreview.com``, ``sportsbookreview``, ``sportsbook``, ``scraper``, ``sports``, ``sports betting``, ``sportsbookreview.com scraper``, ``sportsbookreview scraper``, ``odds``, ``odds scraper``

## What is this?
This is a scraper for sportsbookreview.com. It scrapes the data from the website and saves it to a file. This is useful for data analysis, machine learning, and other applications, where you need a large amount of data, particularly odds. For many betting hobbyists and analysts, it is hard to acquire odds data going past the current season for free. This scraper solves that problem by allowing you to scrape 10+ years of data from sportsbookreview.com. Additionally, a pre-scraped dataset is provided in the ``data`` folder for each sport, ranging from 2011 to 2021.

## Installation

```sh
1. git clone https://github.com/finned-tech/sportsbookreview-scraper.git
2. cd sportsbookreview-scraper
3. pip install -r requirements.txt
```

## Usage example

```sh
python cli.py --sport nfl --start 2011 --end 2021 --filename nfl_10Y.json
```

Currently, we support the following arguments:
- **--sport: nfl, nba, mlb, nhl**\
Description: The sport to scrape data for.

- **--start <2011 - 2021>**\
Description: The year to start scraping data from.

- **--end <2011 - 2021>**\
Description: The year to stop scraping data at.

- **--filename < filename >**\
Description: The filename to save the scraped data to.

- **--format (optional) < json, csv >**\
Description: The format to save the scraped data in.

## License
Copyright © 2023 Finn Lancaster

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.