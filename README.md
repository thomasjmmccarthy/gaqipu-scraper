# Gaqipu Scraper
Bespoke web scraper developed for a study by EuroFIR AISBL (https://www.eurofir.org)

Python 3 with Headless Chrome scraper designed to find data availability statements in research articles. It has been configured to work on 2021-dated articles for 28 journals from 4 publishers: Taylor & Francis, Wiley, Elsevier, & Springer Open.


### Install & Run:
1. Download all files from the Gaqipu repository: https://github.com/thomasjmmccarthy/gaqipu-scraper
2. Download the version of Chromedriver that matches your version of Google Chrome from https://googlechromelabs.github.io/chrome-for-testing/. Make sure chromedriver.exe is located in the same directory as Gaqipu.py
3. Run launcher.py using Python 3. This will install all required packages and libraries for you, as well as establish a new virtual environment
4. Gaqipu should run automatically once launcher.py is complete

### Runtime Notes:
1. URLs to articles should be stored in the urls.csv file, in the format: ```journal name, link to article``` - any journal listed in this file should have at least one configuration in config.csv to help prevent program crashes
2. Sometimes unexpected errors occur due to websites being down and/or the connection timing out. In these cases, re-run the scraper
3. Collected data is written to output.csv whenever a change in journal is detected. Some minor encoding errors may occur when processing special characters
