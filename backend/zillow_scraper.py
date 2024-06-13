import os
import re
import time
from typing import List
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

from setup import MySQLConnection, clean_monetary_string, proxied_request, log, retry

def save_html(content, file_name):
    file_path = os.path.join('html', file_name)
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
    except Exception as e:
        pass

@retry(max_retry_count=2, interval_sec=5)
def get_zestimate(address: str):
    url = f'https://www.zillow.com/homes/{address.replace(" ", "-").replace("/", "-")}_rb'
    log.info(f'Scraping Zestimate for address : {address}  Requesting URL: {url}')
    
    response = proxied_request(url)
    if response.status_code != 200:
        log.error(f'Failed to retrieve the page. Status code: {response.status_code}')
        raise Exception()

    soup = BeautifulSoup(response.text, 'html.parser')
    prices: List[BeautifulSoup] = soup.find_all(string="Zestimate")
    if not prices:
        prices = soup.find_all(string='Est. ')

    if not prices:
        log.error('Neither "Zestimate" nor "Est. " found in the HTML content')
        save_html(response.text, f"""{address.replace(" ", "-").replace("/", "-")}.html""")
        raise Exception()

    for price in prices:
        parent = price
        for i in range(3):
            parent = parent.find_parent()
            parent_text = parent.__str__()
            match = re.search(r'\$\d[\d,]*', parent_text)
            if match:
                zestimate = match.group()
                log.info(f'Found Zestimate: {zestimate} for address : {address}')
                return zestimate

    log.warning('Zestimate not found after checking potential parent elements')
    save_html(response.text, f"""{address.replace(" ", "-").replace("/", "-")}.html""")
    raise Exception()


def update_database(row):
    try:
        with MySQLConnection() as cursor:
            update_query = """
            UPDATE auction_data
            SET zestimate = %s, v_o = %s
            WHERE auction_id = %s;
            """
            cursor.execute(update_query, (row["zestimate"], row["v_o"], row["auction_id"]))
    except Exception as e:
        log.error(f"Error updating database: {e}")


def zillow_crawler(df):
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