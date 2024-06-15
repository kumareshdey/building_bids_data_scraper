from datetime import datetime, timedelta
import re
import time

from bs4 import BeautifulSoup
from setup import MySQLConnection, clean_monetary_string, get_driver, log, proxied_request, retry
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
import pandas as pd
import numpy as np


def extract_city_state(address):
    # Regular expression to match the city and state at the end of the address
    pattern = r'([^,]+),?\s+([A-Za-z\s]+)\s+([A-Z]{2})\s+\d{5}$'
    
    match = re.search(pattern, address.strip())
    if match:
        city = match.group(2).strip().title()
        state = match.group(3)
        return city, state
    else:
        return None, None

def fetch_existing_auction_ids():
    log.info("Fetching existing auction IDs from the database.")
    with MySQLConnection() as cursor:
        query = "SELECT auction_id FROM auction_data"
        cursor.execute(query)
        
        result = cursor.fetchall()
        log.info(f"Fetched {len(result)} auction IDs.")
        return {row[0] for row in result}

@retry(max_retry_count=1, interval_sec=5)
def fetch_other_values(auction_id):
    url = f"https://www.bid4assets.com/auction/index/{auction_id}"
    log.info(f"Fetching debt value from {url}")
    response = proxied_request(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    item_specifics_table = soup.find('div', class_='item-specifics-table')
    right_table = item_specifics_table.find('table', class_='pull-right')
    debt_amount = ""
    rows = right_table.find_all('tr')
    ret = [None, None]
    for row in rows:
        cells = row.find_all('td')
        if len(cells) > 1:
            key = cells[0].get_text(strip=True).lower()
            value = cells[1].get_text(strip=True)
            if key == 'debt amount':
                ret[0] = value
            elif key == 'county':
                ret[1] = value
    return ret

@retry(max_retry_count=2, interval_sec=10)
def fetch_bids_data(url):
    log.info(f"Starting to scrape data from {url}.")
    existing_auction_ids = fetch_existing_auction_ids()
    log.info(f"Existing auction_ids {existing_auction_ids}")
    stop_scraping = False
    data = []
    with get_driver() as driver:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        header_row = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'thead.k-table-thead tr')))
        time.sleep(3)
        header_row = driver.find_element(By.CSS_SELECTOR, 'thead.k-table-thead tr')
        headers = header_row.find_elements(By.TAG_NAME, 'th')
        id_index = None
        address_index = None
        curremt_bid_index = None

        for i, header in enumerate(headers):
            header_text = header.text.strip().lower()
            if 'id' == header_text:
                id_index = i
            elif 'address' == header_text:
                address_index = i
            elif 'current bid' == header_text:
                curremt_bid_index = i

        if id_index is None or address_index is None or curremt_bid_index is None:
            raise ValueError("ID or Address column not found in table headers")

        while not stop_scraping:
            rows = driver.find_elements(By.CSS_SELECTOR, 'tbody.k-table-tbody tr')
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, 'td')
                auction_id = cols[id_index].text.strip()
                if int(auction_id) in existing_auction_ids:
                    log.info(f"Auction ID {auction_id} already exists in the database. Stopping scrape.")
                    stop_scraping = True
                    break
                address = cols[address_index].text.strip()
                current_bid = cols[curremt_bid_index].text.strip()
                debt, county = fetch_other_values(auction_id)
                current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                city, state = extract_city_state(address)
                data.append([auction_id, address, clean_monetary_string(current_bid), clean_monetary_string(debt), county, city, state, current_date])
            log.info(f"Rows length after this page {len(data)}")
            if stop_scraping:
                break
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                next_button = driver.find_element(By.CSS_SELECTOR, 'button[title="Go to the next page"]')
                if next_button.get_attribute("aria-disabled") == "true":
                    log.info("Reached the last page of the table.")
                    break
                next_button.click()
                log.info("Moved to the next page.")
                time.sleep(2)
            except (NoSuchElementException, ElementClickInterceptedException):
                log.warning("Next button not found or click intercepted.")
                break
    
    page_data = pd.DataFrame(data, columns=['auction_id', 'address', 'current_bid', 'debt', 'county', 'city', 'state', 'date'])
    page_data = page_data.replace({np.nan: None})
    log.info(f"Scraped {len(data)} rows of data.")
    return page_data

