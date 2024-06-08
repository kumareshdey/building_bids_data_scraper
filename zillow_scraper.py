import re
import time
from typing import List
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

from setup import proxied_request, log, retry

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
    raise Exception()
