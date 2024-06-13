
import pandas as pd
from bids_scraper import fetch_bids_data
from zillow_scraper import zillow_crawler
from setup import MySQLConnection, log

urls = ["https://www.bid4assets.com/chestercopasheriffsales",
        "https://www.bid4assets.com/MontcoPASheriff"
]


def save_bids_data(df):
    log.info("Saving data to the database.")
    with MySQLConnection() as cursor:
        insert_query = """
            INSERT INTO auction_data (auction_id, address, current_bid, debt, county, city, state, date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """

        for _, row in df.iterrows():
            try:
                cursor.execute(insert_query, tuple(row))
            except Exception as e:
                log.error(f"Error inserting data: {e}")

    log.info("Data saving complete.")
    return True
if __name__ == "__main__":
    for url in urls:
        try:
            df = fetch_bids_data(url)
            if not df.empty:
                save_bids_data(df)
            zillow_crawler(df)
        except Exception as e:
            log.error(f"An error occurred while processing {url}: {e}")