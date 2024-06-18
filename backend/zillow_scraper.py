from datetime import datetime, timedelta
from decimal import Decimal
import os
import re
import time
from typing import List
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd

from setup import MySQLConnection, clean_monetary_string, proxied_request, log, retry

def save_html(content, file_name):
    file_path = os.path.join('html_pages', file_name)
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
    except Exception as e:
        pass

def fetch_crawlable_data():
    log.info("Fetching crawlable data from the database.")
    with MySQLConnection() as cursor:
        time_24_hours_ago = datetime.now() - timedelta(days=1)
        select_query = """
            SELECT * FROM auction_data
            WHERE (zestimate IS NULL OR zestimate = '')
            AND created_at >= %s;
        """
        
        try:
            cursor.execute(select_query, (time_24_hours_ago,))
            results = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(results, columns=column_names)
            for col in df.columns:
                if df[col].dtype == 'object' and isinstance(df[col].iloc[0], Decimal):
                    df[col] = df[col].astype(float)
            
            log.info(f"Found {len(df)} entries")
            return df
        except Exception as e:
            log.error(f"Error fetching data: {e}")
            return pd.DataFrame()

@retry(max_retry_count=2, interval_sec=5)
def get_zestimate(address: str):
    status, i = 500, 0
    while status != 200:
        i += 1
        url = f'https://www.zillow.com/homes/{address.replace(" ", "-").replace("/", "-")}_rb'
        log.info(f'Scraping Zestimate for address : {address}  Requesting URL: {url}')
        
        response = proxied_request(url)
        if response.status_code != 200:
            log.error(f'{i} times. || Failed to retrieve the page. Status code: {response.status_code}. Retrying in 30 seconds.')
            time.sleep(30)
        else:
            status = 200

    soup = BeautifulSoup(response.text, 'html.parser')
    price_element = soup.find('span', {'data-testid': 'price'})
    if price_element:
        log.info(f"Found direct zestimate: {price_element.text}")
        price = clean_monetary_string(price_element.text)
        if price:
            return price_element.text
    prices: List[BeautifulSoup] = soup.find_all(string="Zestimate")
    if not prices:
        prices = soup.find_all(string='Est. ')

    if not prices:
        log.error('Neither "Zestimate" nor "Est. " found in the HTML content')
        raise Exception()

    for price in prices:
        parent = price
        for i in range(3):
            parent = parent.find_parent()
            parent_text = parent.__str__()
            log.info(parent_text)
            if 'rent' in parent_text.lower():
                return None
            match = re.search(r'\$\d[\d,]*', parent_text)
            if match:
                zestimate = match.group()
                log.info(f'Found Zestimate: {zestimate} for address : {address}')
                return zestimate

    log.warning('Zestimate not found after checking potential parent elements')
    raise Exception()


def update_database(row):
    try:
        with MySQLConnection() as cursor:
            update_query = """
            UPDATE auction_data
            SET 
                zestimate = IF(zestimate IS NULL, %s, zestimate), 
                v_o = IF(v_o IS NULL, %s, v_o)
            WHERE auction_id = %s;
            """
            cursor.execute(update_query, (row["zestimate"], row["v_o"], row["auction_id"]))
    except Exception as e:
        log.error(f"Error updating database: {e}")


def zillow_crawler():
    df = fetch_crawlable_data()
    for _, row in df.iterrows():
        zestimate = get_zestimate(row['address'])
        zestimate = clean_monetary_string(zestimate)
        if row["debt"] and zestimate:
            v_o = zestimate/row["debt"]
        else:
            v_o = None
        row["zestimate"] = zestimate
        row["v_o"] = v_o
        update_database(row)