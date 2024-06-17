from logging import config
import logging
import re
import traceback
from selenium import webdriver
from contextlib import contextmanager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import warnings
import pymysql

from credentials import CONFIG, DOWNLOAD_PATH, SCRAPEOPS
import requests

def proxied_request(url, render_js=False):
        PROXY_URL = 'https://proxy.scrapeops.io/v1/'
        API_KEY = SCRAPEOPS
        return requests.get(
            url=PROXY_URL,
            params={
                'api_key': API_KEY,
                'url': url, 
                # 'residential': 'true', 
                'country': 'us',
                'render_js': render_js
            },
        )


@contextmanager
def get_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    # chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    # chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration (useful for headless mode)
    # chrome_options.add_argument("--no-sandbox")  # Bypass OS security model (useful for Docker)
    # chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    chrome_options.add_experimental_option("prefs", {
    "download.default_directory": DOWNLOAD_PATH,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

    driver = webdriver.Chrome(options=chrome_options)
    try:
        yield driver
    finally:
        driver.quit()


class MySQLConnection:
    def __init__(self):
        self.config = CONFIG

    def __enter__(self):
        self.connection = pymysql.connect(
            host=self.config['host'],
            user=self.config['user'],
            password=self.config['password'],
            database=self.config['database'],
            port=self.config['port']
        )
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_tb is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.cursor.close()
        self.connection.close()


def retry(max_retry_count, interval_sec):
    def decorator(func):
        def wrapper(*args, **kwargs):
            retry_count = 0
            while retry_count < max_retry_count:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retry_count += 1
                    log.error(f'{func.__name__} failed on attempt {retry_count}: {str(e)}')
                    log.error(traceback.format_exc())  # Log the traceback
                    if retry_count < max_retry_count:
                        log.info(f'Retrying {func.__name__} in {interval_sec} seconds...')
                        time.sleep(interval_sec)
            log.warning(f'{func.__name__} reached maximum retry count of {max_retry_count}.')
            return None
        return wrapper
    return decorator

def configure_get_log():
    warnings.filterwarnings("ignore")

    config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"
                },
                "slack_format": {
                    "format": "`[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]` %(message)s"
                },
            },
            "handlers": {
                "file": {
                    "class": "logging.FileHandler",
                    "formatter": "default",
                    "filename": "logs.log",
                },
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
            },
            
            "loggers": {
                "root": {
                    "level": logging.INFO,
                    "handlers": ["file", "console"],
                    "propagate": False,
                },
            },
        }
    )
    log = logging.getLogger("root")
    return log


log = configure_get_log()

def clean_monetary_string(value_str):
    try:
        # Updated regex pattern to correctly extract the number after the dollar sign
        match = re.search(r'\$([\d,]+\.?\d*)', value_str)
        if match:
            # Remove commas and convert to float
            cleaned_str = match.group(1).replace(',', '')
            return float(cleaned_str)
        else:
            return None
    except Exception as e:
        log.error(f"Error cleaning monetary string: {e}. value = {value_str}")
        return None
    

def url_to_county(url):
    return {
        "https://www.bid4assets.com/chestercopasheriffsales": 'Chester',
        "https://www.bid4assets.com/MontcoPASheriff": 'Montgomery',
        "https://www.bid4assets.com/berkscountysheriffsales": "Berks",
        "https://www.bid4assets.com/philataxsales": 'Philadelphia',
        "https://www.bid4assets.com/philaforeclosures": 'Philadelphia'
    }[url]

def url_to_col_name(url):
    return {
        "https://www.bid4assets.com/chestercopasheriffsales": {'Auction ID': "id", 
                                                       'Minimum Bid': 'bid', 
                                                       'Bidding Open Date/Time': 'bid_open_date', 
                                                       'Bidding Closing Date/Time': 'bid_closing_date', 
                                                       'Debt Amount': 'debt', 
                                                       'Address': 'address'},
        "https://www.bid4assets.com/MontcoPASheriff": {'Auction ID': "id", 
                                                       'Minimum Bid': 'bid', 
                                                       'Bidding Open Date/Time': 'bid_open_date', 
                                                       'Bidding Closing Date/Time': 'bid_closing_date', 
                                                       'Debt Amount': 'debt', 
                                                       'Address': 'address'},
        "https://www.bid4assets.com/berkscountysheriffsales": {'Auction ID': "id", 
                                                       'Minimum Bid': 'bid', 
                                                       'Bidding Open Date/Time': 'bid_open_date', 
                                                       'Bidding Closing Date/Time': 'bid_closing_date', 
                                                       'Debt Amount': 'debt', 
                                                       'Address': 'address'},
        "https://www.bid4assets.com/philataxsales": {'Auction ID': "id", 
                                                       'Minimum Bid': 'bid', 
                                                       'Bidding Open Date/Time': 'bid_open_date', 
                                                       'Bidding Close Date/Time': 'bid_closing_date', 
                                                       'Address': 'address'},
        "https://www.bid4assets.com/philaforeclosures": {'Auction ID': "id", 
                                                       'Minimum Bid': 'bid', 
                                                       'Bidding Open Date/Time.1': 'bid_open_date', 
                                                       'Bidding Open Date/Time': 'bid_closing_date', 
                                                       'Debt Amount': 'debt', 
                                                       'Address': 'address'},
    }[url]

def get_remark(url):
    return {
        "https://www.bid4assets.com/chestercopasheriffsales": '',
        "https://www.bid4assets.com/MontcoPASheriff": '',
        "https://www.bid4assets.com/berkscountysheriffsales": "",
        "https://www.bid4assets.com/philataxsales": 'Phila tax',
        "https://www.bid4assets.com/philaforeclosures": 'Phila foreclosure'
    }[url]